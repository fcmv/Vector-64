"""File contracts shared by the STK-HalfKA training tools."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
from pathlib import Path
from typing import Any

import numpy as np

FEATURES = 22528
BUCKETS = 8
MAGIC = b"STKHALFKA"
HEADER = struct.Struct("<9sIIII")
DATA_FORMAT = "STK-HalfKA"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def copy_file(source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    shutil.copyfile(source, temporary)
    os.replace(temporary, destination)


def net_layout(hidden: int) -> tuple[dict[str, dict[str, int]], int]:
    if hidden not in (128, 1024):
        raise ValueError("STK-HalfKA supports hidden widths 128 and 1024")
    sections: dict[str, dict[str, int]] = {}
    offset = HEADER.size
    sizes = {"ft_weights": FEATURES * hidden * 2, "ft_bias": hidden * 2,
             "ft_psqt": FEATURES * BUCKETS * 4}
    for bucket in range(BUCKETS):
        sizes.update({f"bucket{bucket}.{name}": size for name, size in (
            ("l1w", 16 * hidden), ("l1b", 16 * 4), ("l2w", 32 * 16),
            ("l2b", 32 * 4), ("outw", 32), ("outb", 4))})
    for name, size in sizes.items():
        sections[name] = {"offset": offset, "size": size}
        offset += size
    return sections, offset


def check_net(path: Path, allow_trailing: bool = False) -> dict[str, Any]:
    with path.open("rb") as stream:
        raw = stream.read(HEADER.size)
    if len(raw) != HEADER.size:
        raise ValueError("truncated STK-HalfKA header")
    magic, version, features, hidden, buckets = HEADER.unpack(raw)
    if (magic, version, features, buckets) != (MAGIC, 1, FEATURES, BUCKETS):
        raise ValueError("not a supported STK-HalfKA network; legacy VECTOR64_NNUE must be retrained")
    sections, expected = net_layout(hidden)
    size = path.stat().st_size
    if size < expected or (size != expected and not allow_trailing):
        raise ValueError(f"network size {size} differs from expected {expected}")
    return {"format": DATA_FORMAT, "hidden": hidden, "size": size, "sections": sections}


def load_shard(path: Path) -> dict[str, np.ndarray]:
    keys = ("white_indices", "black_indices", "stm", "eval_cp")
    with np.load(path, allow_pickle=False) as archive:
        missing = set(keys) - set(archive.files)
        if missing:
            raise ValueError(f"{path}: missing arrays {sorted(missing)}")
        data = {key: archive[key] for key in keys}
    w, b, stm, cp = (data[key] for key in keys)
    if w.ndim != 2 or b.shape != w.shape or w.shape[1] < 31:
        raise ValueError(f"{path}: invalid feature shapes")
    rows = w.shape[0]
    if rows == 0 or stm.shape != (rows,) or cp.shape != (rows,):
        raise ValueError(f"{path}: inconsistent or empty row arrays")
    for key in ("white_indices", "black_indices"):
        values = data[key]
        if not np.issubdtype(values.dtype, np.integer) or np.any(values < -1) or np.any(values >= FEATURES):
            raise ValueError(f"{path}: invalid STK-HalfKA indices in {key}; rebuild legacy shards from FEN")
        counts = (values >= 0).sum(axis=1)
        if np.any(counts < 1) or np.any(counts > 31):
            raise ValueError(f"{path}: invalid active feature count")
        ordered = np.sort(values, axis=1)
        if np.any((ordered[:, 1:] == ordered[:, :-1]) & (ordered[:, 1:] >= 0)):
            raise ValueError(f"{path}: duplicate features")
    if np.any((w >= 0).sum(axis=1) != (b >= 0).sum(axis=1)):
        raise ValueError(f"{path}: perspectives disagree on piece count")
    if not np.issubdtype(stm.dtype, np.integer) or not np.isin(stm, (0, 1)).all():
        raise ValueError(f"{path}: stm must be integer 0 or 1")
    if not (np.issubdtype(cp.dtype, np.floating) or np.issubdtype(cp.dtype, np.integer)) or not np.isfinite(cp).all():
        raise ValueError(f"{path}: non-finite or non-numeric labels")
    return data


def load_manifest(path: Path, allow_untagged: bool = False) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"{path}: manifest must be an object")
    format_name = manifest.get("format")
    if format_name is None and allow_untagged:
        pass
    elif (format_name, manifest.get("version"), manifest.get("features"), manifest.get("target_perspective")) != (
        DATA_FORMAT, 1, FEATURES, "white"
    ):
        raise ValueError(f"{path}: incompatible or untagged dataset; rebuild from FEN or explicitly use "
                         "--allow-untagged-shards for known STK-HalfKA data")
    shards = manifest.get("shards")
    if not isinstance(shards, list) or not shards:
        raise ValueError(f"{path}: no shards")
    seen: set[str] = set()
    total = 0
    for shard in shards:
        if not isinstance(shard, dict):
            raise ValueError(f"{path}: invalid shard entry")
        name = shard.get("file")
        if not isinstance(name, str) or Path(name).name != name or name in seen:
            raise ValueError(f"{path}: invalid or duplicate shard name")
        if not isinstance(shard.get("samples"), int) or shard["samples"] <= 0:
            raise ValueError(f"{path}: invalid shard count")
        seen.add(name)
        total += shard["samples"]
    if total != manifest.get("total_samples"):
        raise ValueError(f"{path}: total_samples disagrees with shards")
    return manifest


def validate_dataset(path: Path, allow_untagged: bool = False) -> dict[str, Any]:
    manifest = load_manifest(path, allow_untagged)
    for shard in manifest["shards"]:
        file_path = path.parent / shard["file"]
        if shard.get("sha256") and sha256(file_path) != shard["sha256"]:
            raise ValueError(f"{file_path}: SHA256 mismatch")
        data = load_shard(file_path)
        if len(data["stm"]) != shard["samples"]:
            raise ValueError(f"{file_path}: sample count differs from manifest")
    return manifest
