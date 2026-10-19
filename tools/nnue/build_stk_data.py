#!/usr/bin/env python3
"""Prepare resumable, checked STK-HalfKA shards from labelled FEN positions."""
from __future__ import annotations

from pathlib import Path

if __name__ == "__main__" and not __package__:
    import runpy
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "_entrypoint.py"),
                    init_globals={"MODULE": "tools.nnue.build_stk_data", "ARGV0": __file__}, run_name="__main__")

import argparse
import hashlib
import io
import json
import math
import os
import sqlite3
from collections import Counter
from typing import Any

import numpy as np

from . import halfka_features as hk
from .contracts import DATA_FORMAT, FEATURES, sha256, validate_dataset, write_json

MAX_FEATURES = 32
MATE_CP = 8000.0


def iter_lines(path: Path):
    if path.suffix.lower() == ".zst":
        import zstandard as zstd
        with path.open("rb") as stream:
            with zstd.ZstdDecompressor().stream_reader(stream) as reader:
                yield from io.TextIOWrapper(reader, encoding="utf-8")
    else:
        with path.open(encoding="utf-8") as stream:
            yield from stream


def extract_cp(rec: dict, min_depth: int, min_knodes: int = 0) -> float | None:
    evals = rec.get("evals")
    if not isinstance(evals, list):
        if int(rec.get("depth", 0)) < min_depth or int(rec.get("knodes", 0)) < min_knodes:
            return None
        return float(rec["cp"]) if rec.get("cp") is not None else None
    best_depth = -1
    best_cp: float | None = None
    for entry in evals:
        if not isinstance(entry, dict):
            continue
        depth = int(entry.get("depth", 0))
        if depth < min_depth or depth <= best_depth or int(entry.get("knodes", 0)) < min_knodes:
            continue
        pvs = entry.get("pvs")
        pv = pvs[0] if isinstance(pvs, list) and pvs else entry
        if not isinstance(pv, dict):
            continue
        if pv.get("cp") is not None:
            best_cp, best_depth = float(pv["cp"]), depth
        elif pv.get("mate") is not None:
            best_cp = MATE_CP if float(pv["mate"]) > 0 else -MATE_CP
            best_depth = depth
    return best_cp


def blend_cp(eval_white: float, wdl: float, lam: float) -> float:
    if not all(math.isfinite(v) for v in (eval_white, wdl, lam)) or not 0 <= wdl <= 1 or not 0 <= lam <= 1:
        raise ValueError("invalid WDL blend")
    probability = 1.0 / (1.0 + math.exp(-max(-4000.0, min(4000.0, eval_white)) / 400.0))
    probability = min(max((1 - lam) * probability + lam * wdl, 1e-4), 1 - 1e-4)
    return 400.0 * math.log(probability / (1 - probability))


def parse_line(line: str, min_depth: int, wdl_lambda: float = 0.5,
               min_knodes: int = 0) -> tuple[str, float] | None:
    line = line.strip()
    if not line:
        return None
    if line.startswith("{"):
        rec = json.loads(line)
        if not isinstance(rec, dict) or not isinstance(rec.get("fen"), str):
            return None
        cp = extract_cp(rec, min_depth, min_knodes)
        return (rec["fen"], cp) if cp is not None else None
    fields = [field.strip() for field in line.split("|")]
    if len(fields) == 3:
        return fields[0], blend_cp(float(fields[1]), float(fields[2]), wdl_lambda)
    if len(fields) == 2:
        return fields[0], float(fields[1])
    return None


def encode(fen: str, max_features: int = MAX_FEATURES) -> tuple[np.ndarray, np.ndarray, int]:
    pieces, stm = hk.parse_fen_pieces(fen)
    white, black = (hk.features_for(pieces, side) for side in (hk.WHITE, hk.BLACK))
    if max(len(white), len(black)) > max_features:
        raise ValueError("feature overflow")
    w = np.full(max_features, -1, dtype=np.int32)
    b = np.full(max_features, -1, dtype=np.int32)
    w[:len(white)], b[:len(black)] = white, black
    return w, b, stm


def source_files(source: str) -> list[Path]:
    path = Path(source)
    files = sorted(path.glob("*.txt")) if path.is_dir() else [path]
    if not files or any(not file.is_file() for file in files):
        raise ValueError(f"input files not found: {source}")
    return files


def source_identity(source: str) -> Any:
    if source.startswith("hf://"):
        return source
    return [{"path": str(p.resolve()), "size": p.stat().st_size, "mtime_ns": p.stat().st_mtime_ns}
            for p in source_files(source)]


def input_lines(source: str):
    if source.startswith("hf://"):
        from datasets import load_dataset
        dataset = source[5:] or "Lichess/chess-position-evaluations"
        for row in load_dataset(dataset, split="train", streaming=True):
            yield json.dumps(row)
    else:
        for path in source_files(source):
            yield from iter_lines(path)


def prepare(args: argparse.Namespace, out_dir: Path) -> Path:
    if args.shard_size <= 0 or args.max_features < 31 or args.max_samples < 0:
        raise ValueError("shard-size must be positive, max-features >=31 and max-samples >=0")
    if not math.isfinite(args.max_abs_cp) or args.max_abs_cp <= 0 or min(args.min_depth, args.min_knodes) < 0:
        raise ValueError("invalid label filters")
    if not 0 <= args.wdl_lambda <= 1 or not args.prefix or Path(args.prefix).name != args.prefix:
        raise ValueError("invalid WDL lambda or shard prefix")
    config = {key: getattr(args, key) for key in (
        "shard_size", "max_features", "max_samples", "min_depth", "min_knodes", "max_abs_cp",
        "cp_source", "dedup_scope", "prefix", "uncompressed", "wdl_lambda")}
    config["source"] = source_identity(args.input)
    manifest_path = out_dir / "manifest.json"
    if manifest_path.exists():
        manifest = validate_dataset(manifest_path)
        if manifest.get("prep_config") != config:
            raise ValueError("preparation inputs/settings changed; use a different output directory")
        print(f"[prep] checked {manifest['total_samples']} existing samples")
        return out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    progress = out_dir / "progress.json"
    state: dict[str, Any] = {"prep_config": config, "lines": 0, "shards": [], "stats": {}, "kept": 0}
    if progress.exists():
        state = json.loads(progress.read_text(encoding="utf-8"))
        if state["prep_config"] != config:
            raise ValueError("resume inputs/settings changed; use a different output directory")
        for shard in state["shards"]:
            if sha256(out_dir / shard["file"]) != shard["sha256"]:
                raise ValueError("resume shard SHA256 mismatch")
    elif list(out_dir.glob("*.npz")):
        raise ValueError("unregistered shards in output directory; use a new directory")
    shards = state["shards"]
    stats: Counter[str] = Counter(state["stats"])
    kept, lines_done = state["kept"], state["lines"]
    write_json(progress, state)
    rows: list[tuple[np.ndarray, np.ndarray, int, float]] = []
    seen: set[bytes] = set()
    connection = None
    if args.dedup_scope == "global":
        db = Path(args.dedup_db) if args.dedup_db else out_dir / "dedup_seen.sqlite"
        if shards and not db.exists():
            raise ValueError("resume dedup database missing; use a new output directory")
        db.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db)
        connection.execute("CREATE TABLE IF NOT EXISTS stk_owner (directory TEXT PRIMARY KEY)")
        owners = connection.execute("SELECT directory FROM stk_owner").fetchall()
        if owners and owners != [(str(out_dir.resolve()),)]:
            connection.close()
            raise ValueError("dedup database belongs to another preparation directory")
        connection.execute("INSERT OR IGNORE INTO stk_owner VALUES (?)", (str(out_dir.resolve()),))
        connection.execute("CREATE TABLE IF NOT EXISTS stk_seen (h BLOB PRIMARY KEY, shard INTEGER)")
        # Dedup may commit before progress; unregistered rows must be replayed.
        connection.execute("DELETE FROM stk_seen WHERE shard >= ?", (len(shards),))
        connection.commit()
    line_no = lines_done

    def flush() -> None:
        if not rows:
            return
        name = f"{args.prefix}_{len(shards):05d}.npz"
        target = out_dir / name
        temporary = target.with_suffix(".npz.tmp")
        with temporary.open("wb") as stream:
            writer = np.savez if args.uncompressed else np.savez_compressed
            writer(stream, white_indices=np.stack([row[0] for row in rows]),
                   black_indices=np.stack([row[1] for row in rows]),
                   stm=np.asarray([row[2] for row in rows], dtype=np.int8),
                   eval_cp=np.asarray([row[3] for row in rows], dtype=np.float32))
        os.replace(temporary, target)
        labels = np.asarray([row[3] for row in rows], dtype=np.float64)
        shards.append({"file": name, "samples": len(rows), "sha256": sha256(target),
                       "cp_min": float(labels.min()), "cp_max": float(labels.max()),
                       "cp_mean": float(labels.mean()), "cp_std": float(labels.std())})
        if connection is not None:
            connection.commit()
        write_json(progress, {"prep_config": config, "lines": line_no, "shards": shards,
                              "stats": dict(stats), "kept": kept})
        rows.clear()
        seen.clear()

    try:
        for line_no, line in enumerate(input_lines(args.input), 1):
            if line_no <= lines_done:
                continue
            if args.max_samples and kept >= args.max_samples:
                break
            stats["lines"] += 1
            try:
                parsed = parse_line(line, args.min_depth, args.wdl_lambda, args.min_knodes)
                if parsed is None:
                    stats["unlabelled"] += 1
                    continue
                fen, cp = parsed
                if not math.isfinite(cp):
                    stats["non_finite"] += 1
                    continue
                w, b, stm = encode(fen, args.max_features)
            except (ValueError, KeyError, TypeError, IndexError, StopIteration, OverflowError):
                stats["invalid"] += 1
                continue
            if args.cp_source == "stm" and stm == hk.BLACK:
                cp = -cp
            if abs(cp) > args.max_abs_cp:
                stats["extreme"] += 1
                continue
            key = hashlib.blake2b(" ".join(fen.split()[:4]).encode(), digest_size=16).digest()
            if args.dedup_scope == "shard":
                duplicate = key in seen
                seen.add(key)
            elif connection is not None:
                duplicate = connection.execute("INSERT OR IGNORE INTO stk_seen VALUES (?, ?)",
                                               (key, len(shards))).rowcount == 0
            else:
                duplicate = False
            if duplicate:
                stats["duplicate"] += 1
                continue
            rows.append((w, b, stm, cp))
            kept += 1
            if len(rows) >= args.shard_size:
                flush()
        flush()
        if not shards:
            raise ValueError(f"no usable training positions: {dict(stats)}")
        write_json(manifest_path, {"format": DATA_FORMAT, "version": 1, "features": FEATURES,
                                  "target_perspective": "white", "max_features": args.max_features,
                                  "total_samples": kept, "shards": shards,
                                  "prep_config": config, "stats": dict(stats)})
        progress.unlink(missing_ok=True)
    finally:
        if connection is not None:
            connection.rollback()
            connection.close()
    print(f"[prep] kept {kept} samples in {len(shards)} shards: {dict(stats)}")
    return out_dir


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--shard-size", type=int, default=1_000_000)
    parser.add_argument("--max-features", type=int, default=MAX_FEATURES)
    parser.add_argument("--min-depth", type=int, default=0)
    parser.add_argument("--min-knodes", type=int, default=0)
    parser.add_argument("--max-abs-cp", type=float, default=6000.0)
    parser.add_argument("--max-samples", "--max-positions", type=int, default=0)
    parser.add_argument("--cp-source", choices=("white", "stm"), default="white")
    parser.add_argument("--wdl-lambda", type=float, default=0.5)
    parser.add_argument("--dedup-scope", choices=("none", "shard", "global"), default="global")
    parser.add_argument("--dedup-db", default=None)
    parser.add_argument("--prefix", default="stk_shard")
    parser.add_argument("--uncompressed", action="store_true")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out-dir", required=True)
    add_arguments(parser)
    args = parser.parse_args(argv)
    prepare(args, Path(args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
