#!/usr/bin/env python3
"""Resumable STK-HalfKA preparation, training, export and engine-parity checks.

Targets and model output are side-to-move relative. Training uses normalized
activations; export scales FT by 127, dense weights by 64, dense biases by 8128
and PSQT by 16. Pairwise scaling makes eval_cp = 508 * float_out + psqt_cp.
Integer-reference parity is exact; float quantization drift is informational.
CUDA batches halve on OOM. Re-running the command resumes saved prep/training state.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_stk_data as prep  # noqa: E402
import halfka_features as hk  # noqa: E402
from contracts import check_net, copy_file, load_shard, sha256, validate_dataset, write_json  # noqa: E402

FEATURES = 22528
# Set from --hidden in main(): 1024 = primary net, 128 = dual-net small net.
HIDDEN = 1024
PAIR = HIDDEN // 2
L1 = 16
L2 = 32
BUCKETS = 8

QA = 127.0
QB = 64.0
WMAX = QA / QB
OUT_CP = QA * QB / 16.0
CP_SCALE = 400.0  # tanh() sharpness of the WDL loss
PAIR_FACTOR = QA / 128.0

BENCH_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
    "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
    "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
    "r1bq1rk1/pp2bppp/2n2n2/2pp4/4P3/2NP1N2/PPP1BPPP/R1BQ1RK1 w - - 0 8",
    "8/8/1p1k4/p1p2p2/P1P2P2/1P1K4/8/8 w - - 0 1",
]

def mirror_fen(fen: str) -> str:
    """The same position with the colours swapped, top to bottom.

    Pure string surgery on the six FEN fields -- no chess library, per the
    house rule that only the engine encodes chess rules. Ranks are reversed
    and piece letters change case; castling letters swap case; the en-passant
    square flips rank. Clocks are untouched.
    """
    board, stm, castling, ep, halfmove, fullmove = fen.split()

    ranks = board.split("/")[::-1]
    flipped = "/".join(r.swapcase() for r in ranks)

    stm = "b" if stm == "w" else "w"
    if castling != "-":
        # Swapping case also swaps which side owns each right, so the letters
        # have to be put back into canonical KQkq order.
        swapped = castling.swapcase()
        castling = "".join(c for c in "KQkq" if c in swapped) or "-"
    if ep != "-":
        ep = ep[0] + str(9 - int(ep[1]))

    return " ".join([flipped, stm, castling, ep, halfmove, fullmove])

class STKNet(nn.Module):
    """Normalized-domain model of src/nnue/network.{h,cpp}."""

    def __init__(self, hidden: int = 0) -> None:
        super().__init__()
        # Width captured per-instance so a 1024-wide teacher and a 128-wide
        # student can coexist (distillation) regardless of the global HIDDEN.
        h = hidden or HIDDEN
        self.hidden = h
        self.pair = h // 2
        # Row 0 is a frozen zero row for -1 padding (indices are shifted +1).
        self.ft = nn.EmbeddingBag(FEATURES + 1, h, mode="sum", padding_idx=0)
        self.ft_bias = nn.Parameter(torch.zeros(h))
        self.psqt = nn.EmbeddingBag(FEATURES + 1, BUCKETS, mode="sum", padding_idx=0)
        self.l1w = nn.Parameter(torch.empty(BUCKETS, L1, h))
        self.l1b = nn.Parameter(torch.zeros(BUCKETS, L1))
        self.l2w = nn.Parameter(torch.empty(BUCKETS, L2, L1))
        self.l2b = nn.Parameter(torch.zeros(BUCKETS, L2))
        self.outw = nn.Parameter(torch.empty(BUCKETS, L2))
        self.outb = nn.Parameter(torch.zeros(BUCKETS))
        nn.init.uniform_(self.ft.weight, -0.05, 0.05)
        nn.init.uniform_(self.psqt.weight, -1.0, 1.0)
        for w in (self.l1w, self.l2w, self.outw):
            nn.init.uniform_(w, -0.5, 0.5)
        with torch.no_grad():
            self.ft.weight[0].zero_()
            self.psqt.weight[0].zero_()

    def clip_weights(self) -> None:
        with torch.no_grad():
            for w in (self.l1w, self.l2w, self.outw):
                w.clamp_(-WMAX, WMAX)

    def forward(
        self,
        white_idx: torch.Tensor,
        black_idx: torch.Tensor,
        stm: torch.Tensor,
        bucket: torch.Tensor,
    ) -> torch.Tensor:
        wi, bi = white_idx + 1, black_idx + 1
        acc_w = self.ft(wi) + self.ft_bias
        acc_b = self.ft(bi) + self.ft_bias
        psq_w, psq_b = self.psqt(wi), self.psqt(bi)

        white_stm = (stm == 0).unsqueeze(1)
        us = torch.where(white_stm, acc_w, acc_b)
        them = torch.where(white_stm, acc_b, acc_w)
        psq_us = torch.where(white_stm, psq_w, psq_b)
        psq_them = torch.where(white_stm, psq_b, psq_w)

        def pairwise(a: torch.Tensor) -> torch.Tensor:
            c = torch.clamp(a, 0.0, 1.0)
            return c[:, : self.pair] * c[:, self.pair :] * PAIR_FACTOR

        x = torch.cat([pairwise(us), pairwise(them)], dim=1)
        l1 = torch.clamp(torch.einsum("bi,koi->bko", x, self.l1w) + self.l1b, 0.0, 1.0)
        l2 = torch.clamp(torch.einsum("bko,klo->bkl", l1, self.l2w) + self.l2b, 0.0, 1.0)
        out = torch.einsum("bkl,kl->bk", l2, self.outw) + self.outb

        rows = torch.arange(bucket.shape[0], device=bucket.device)
        positional = out[rows, bucket] * OUT_CP
        psqt_cp = psq_us[rows, bucket] - psq_them[rows, bucket]
        return positional + psqt_cp

def stage_prep(args: argparse.Namespace, work: Path) -> Path:
    if not args.input:
        raise ValueError("--input is required for preparation; use --data-dir to reuse checked shards")
    return prep.prepare(args, work / "data")


def training_config(args: argparse.Namespace, manifest_path: Path) -> dict[str, Any]:
    return {"manifest_sha256": sha256(manifest_path), "hidden": HIDDEN,
            "init_sha256": sha256(Path(args.init)) if args.init else None,
            "teacher_sha256": sha256(Path(args.teacher)) if args.teacher else None,
            **{key: getattr(args, key) for key in (
                "epochs", "batch_size", "lr", "mix_shards", "teacher", "shard_slice", "seed")}}


def stage_train(args: argparse.Namespace, work: Path, data_dir: Path) -> Path:
    ckpt_path = work / "ckpt_latest.pt"
    done_path = work / "train_done.json"
    float_path = work / "model_float.pt"
    manifest_path = Path(args.dataset_manifest) if args.dataset_manifest else data_dir / "manifest.json"
    manifest = validate_dataset(manifest_path, args.allow_untagged_shards)
    config = training_config(args, manifest_path)
    if done_path.exists():
        if json.loads(done_path.read_text()) != config or not float_path.exists():
            raise ValueError("completed training settings changed or model missing; use a new workdir")
        print("[train] checked complete run, skipping")
        return float_path
    shard_files = [manifest_path.parent / entry["file"] for entry in manifest["shards"]]
    if args.shard_slice:
        fields = args.shard_slice.split(":")
        if len(fields) != 2:
            raise ValueError("--shard-slice must be start:stop")
        begin, end = (int(value) if value else None for value in fields)
        shard_files = shard_files[slice(begin, end)]
    if not shard_files:
        raise SystemExit("[train] no shards")

    device = torch.device(args.device)
    model = STKNet().to(device)

    # Warm-start (RL fine-tuning): load weights from a previous model_float.pt
    # but keep a fresh optimizer/schedule so the new data drives a clean LR run.
    # A workdir checkpoint (resume) still wins over this if present.
    if args.init and not ckpt_path.exists():
        ick = torch.load(args.init, map_location=device, weights_only=False)
        model.load_state_dict(ick["state_dict"] if "state_dict" in ick else ick["model"])
        print(f"[train] warm-started weights from {args.init}")

    # Distillation: when --teacher is a 1024-wide float checkpoint, the small
    # student is trained to match the teacher's own eval instead of the
    # dataset label. Both outputs are side-to-move relative, so the teacher
    # value is used directly as the target (no white-perspective flip). This
    # makes the small net AGREE with the big net -- the requirement for the
    # dual-net gate to help rather than hurt.
    teacher = None
    if args.teacher:
        teacher = STKNet(hidden=1024).to(device)
        tck = torch.load(args.teacher, map_location=device, weights_only=False)
        teacher.load_state_dict(tck["state_dict"])
        teacher.eval()
        for pp in teacher.parameters():
            pp.requires_grad_(False)
        print(f"[train] distilling from teacher {args.teacher} (1024-wide)")
    # bullet's canonical recipe (examples/simple.rs): AdamW (decay 0.01, weight
    # clipping +/-1.98 == our +/-127/64), lr 1e-3 dropping x0.1 at 45% and 90%
    # of the run (their step 18 of 40 superbatches), batch 16384.
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.StepLR(opt, step_size=max(1, round(0.45 * args.epochs)), gamma=0.1)

    epoch0, shard0, batch = 1, 0, args.batch_size
    resume_path = ckpt_path if ckpt_path.exists() else Path(args.resume) if args.resume else None
    if resume_path is not None:
        ck = torch.load(resume_path, map_location=device, weights_only=False)
        if ck.get("config") != config:
            raise ValueError("resume architecture/dataset/settings changed; use --init for a fresh warm-start")
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["opt"])
        sched.load_state_dict(ck["sched"])
        epoch0, shard0, batch = ck["epoch"], ck["next_shard"], ck["batch"]
        torch.set_rng_state(ck["rng"].cpu())
        if device.type == "cuda" and ck.get("cuda_rng") is not None:
            torch.cuda.set_rng_state_all(ck["cuda_rng"])
        print(f"[train] resuming at epoch {epoch0}, shard {shard0}, batch {batch}")

    def save_ckpt(epoch: int, next_shard: int) -> None:
        tmp = ckpt_path.with_suffix(".tmp")
        torch.save(
            {
                "model": model.state_dict(),
                "opt": opt.state_dict(),
                "sched": sched.state_dict(),
                "epoch": epoch,
                "next_shard": next_shard,
                "batch": batch,
                "config": config,
                "rng": torch.get_rng_state(),
                "cuda_rng": torch.cuda.get_rng_state_all() if device.type == "cuda" else None,
            },
            tmp,
        )
        os.replace(tmp, ckpt_path)

    print(f"[train] device={device} shards={len(shard_files)} epochs={args.epochs} batch={batch}")
    for epoch in range(epoch0, args.epochs + 1):
        order = np.random.default_rng(args.seed + epoch).permutation(len(shard_files))
        model.train()
        loss_sum, seen, t0 = 0.0, 0, time.time()
        si = shard0
        while si < len(shard_files):
            # Load a group of --mix-shards shards and shuffle across their
            # union: the Lichess DB is not randomly ordered, so single-shard
            # batches are thematically correlated. mix=1 == original behavior.
            group_end = min(si + args.mix_shards, len(shard_files))
            loaded = [load_shard(shard_files[order[j]]) for j in range(si, group_end)]
            d = {k: np.concatenate([x[k] for x in loaded]) for k in loaded[0]}
            del loaded
            n = d["stm"].shape[0]
            perm = np.random.default_rng(args.seed + epoch * 100_003 + si).permutation(n)
            pos = 0
            while pos < n:
                sel = perm[pos : pos + batch]
                try:
                    w = torch.from_numpy(d["white_indices"][sel]).long().to(device)
                    b = torch.from_numpy(d["black_indices"][sel]).long().to(device)
                    stm = torch.from_numpy(d["stm"][sel]).long().to(device)
                    cp = torch.from_numpy(d["eval_cp"][sel]).float().to(device)
                    pieces = (w >= 0).sum(dim=1) + 1
                    bucket = torch.clamp((pieces - 1) // 4, 0, BUCKETS - 1)
                    if teacher is not None:
                        with torch.no_grad():
                            target = teacher(w, b, stm, bucket)
                    else:
                        # eval_cp is white-perspective; the model output is
                        # side-to-move relative, so flip black-to-move targets.
                        target = torch.where(stm == 0, cp, -cp)
                    opt.zero_grad(set_to_none=True)
                    pred = model(w, b, stm, bucket)
                    loss = torch.mean((torch.sigmoid(pred / CP_SCALE) - torch.sigmoid(target / CP_SCALE)) ** 2)
                    if not torch.isfinite(loss):
                        raise ValueError("non-finite training loss")
                    loss.backward()
                    opt.step()
                    model.clip_weights()
                except torch.cuda.OutOfMemoryError:
                    torch.cuda.empty_cache()
                    if batch <= 1:
                        raise
                    batch = max(1, batch // 2)
                    print(f"[train] CUDA OOM -> batch {batch}")
                    continue
                pos += len(sel)
                loss_sum += float(loss.detach()) * len(sel)
                seen += len(sel)
            save_ckpt(epoch, group_end)
            si = group_end
        sched.step()
        shard0 = 0
        save_ckpt(epoch + 1, 0)
        rate = seen / max(time.time() - t0, 1e-9)
        print(
            f"[train] epoch {epoch:3d}/{args.epochs}  loss {loss_sum / max(seen, 1):.6f}  "
            f"{rate:.0f} pos/s  lr {sched.get_last_lr()[0]:.2e}"
        )

    temporary = float_path.with_suffix(".tmp")
    torch.save({"state_dict": model.state_dict(), "format": "STK-HalfKA", "hidden": HIDDEN}, temporary)
    os.replace(temporary, float_path)
    write_json(done_path, config)
    print(f"[train] done -> {float_path}")
    return float_path

def quant(t: torch.Tensor, scale: float, lo: int, hi: int, dtype: str) -> np.ndarray:
    if not torch.isfinite(t).all():
        raise ValueError("cannot export non-finite weights")
    q = torch.round(t.detach().cpu().float() * scale).clamp(lo, hi)
    return q.numpy().astype(dtype)

def quantize_model(model: STKNet) -> dict[str, np.ndarray]:
    """The exact integer tensors written to the .nnue (padding row dropped)."""
    i32 = (-(2**31) + 1, 2**31 - 1)
    q: dict[str, np.ndarray] = {
        "ft_w": quant(model.ft.weight[1:], QA, -32767, 32767, "<i2"),
        "ft_b": quant(model.ft_bias, QA, -32767, 32767, "<i2"),
        "ft_p": quant(model.psqt.weight[1:], 16.0, *i32, "<i4"),
        "l1w": quant(model.l1w, QB, -127, 127, "i1"),
        "l1b": quant(model.l1b, QA * QB, *i32, "<i4"),
        "l2w": quant(model.l2w, QB, -127, 127, "i1"),
        "l2b": quant(model.l2b, QA * QB, *i32, "<i4"),
        "outw": quant(model.outw, QB, -127, 127, "i1"),
        "outb": quant(model.outb, QA * QB, *i32, "<i4"),
    }
    return q

def load_float_model(float_path: Path) -> STKNet:
    checkpoint = torch.load(float_path, map_location="cpu", weights_only=False)
    state = checkpoint.get("state_dict", checkpoint.get("model", checkpoint))
    if "ft.weight" not in state or state["ft.weight"].shape[0] != FEATURES + 1:
        raise ValueError("legacy HalfKP checkpoints cannot become STK-HalfKA weights; retrain from FEN")
    hidden = state["ft.weight"].shape[1]
    if hidden not in (128, 1024):
        raise ValueError("unsupported STK-HalfKA checkpoint width")
    model = STKNet(hidden=hidden)
    model.load_state_dict(state)
    model.eval()
    return model


def stage_export(work: Path, float_path: Path) -> Path:
    model = load_float_model(float_path)
    out = work / f"stk_halfka_{model.hidden}.nnue"
    q = quantize_model(model)
    temporary = out.with_suffix(".nnue.tmp")
    with temporary.open("wb") as stream:
        stream.write(struct.pack("<9sIIII", b"STKHALFKA", 1, FEATURES, model.hidden, BUCKETS))
        for name in ("ft_w", "ft_b", "ft_p"):
            stream.write(q[name].tobytes())
        for bucket in range(BUCKETS):
            for name in ("l1w", "l1b", "l2w", "l2b", "outw", "outb"):
                stream.write(q[name][bucket].tobytes())
    check_net(temporary)
    os.replace(temporary, out)
    write_json(out.with_suffix(".nnue.meta.json"), {"format": "STK-HalfKA", "hidden": model.hidden,
               "sha256": sha256(out), "checkpoint_sha256": sha256(float_path)})

    # Worst-case accumulator estimate: ~32 active features of the largest
    # magnitude plus the bias must stay far inside int16.
    reach = 33 * int(np.abs(q["ft_w"]).max()) + int(np.abs(q["ft_b"]).max())
    print(f"[export] {out} ({out.stat().st_size / 1e6:.1f} MB), max |ft int16| {np.abs(q['ft_w']).max()}")
    if reach > 30000:
        print(f"[export] WARNING: accumulator may overflow int16 (worst-case reach {reach})")
    return out

def python_eval(model: STKNet, fen: str) -> int:
    pieces, stm = hk.parse_fen_pieces(fen)
    wf = hk.features_for(pieces, hk.WHITE)
    bf = hk.features_for(pieces, hk.BLACK)
    pad = 40
    w = torch.full((1, pad), -1, dtype=torch.long)
    b = torch.full((1, pad), -1, dtype=torch.long)
    w[0, : len(wf)] = torch.tensor(wf)
    b[0, : len(bf)] = torch.tensor(bf)
    bucket = torch.tensor([min(max((len(pieces) - 1) // 4, 0), BUCKETS - 1)])
    with torch.no_grad():
        cp = model(w, b, torch.tensor([stm]), bucket)
    return int(round(float(cp[0])))

def python_eval_int(q: dict[str, np.ndarray], fen: str) -> int:
    """Mirror of the engine's integer forward over the exported tensors."""
    pieces, stm = hk.parse_fen_pieces(fen)
    feats = [hk.features_for(pieces, hk.WHITE), hk.features_for(pieces, hk.BLACK)]
    acc = [q["ft_b"].astype(np.int32) + q["ft_w"][f].astype(np.int32).sum(axis=0) for f in feats]
    psq = [q["ft_p"][f].astype(np.int64).sum(axis=0) for f in feats]
    bucket = min(max((len(pieces) - 1) // 4, 0), BUCKETS - 1)

    us, them = (0, 1) if stm == hk.WHITE else (1, 0)

    def pairwise(a: np.ndarray) -> np.ndarray:
        c = np.clip(a, 0, 127)
        return (c[:len(c) // 2] * c[len(c) // 2:]) >> 7

    x = np.concatenate([pairwise(acc[us]), pairwise(acc[them])])
    l1 = np.clip((q["l1b"][bucket] + q["l1w"][bucket].astype(np.int32) @ x) >> 6, 0, 127)
    l2 = np.clip((q["l2b"][bucket] + q["l2w"][bucket].astype(np.int32) @ l1) >> 6, 0, 127)
    raw = int(q["outb"][bucket]) + int(q["outw"][bucket].astype(np.int32) @ l2)
    positional = raw >> 4
    psqt_term = int(psq[us][bucket] - psq[them][bucket]) >> 4
    return positional + psqt_term

def find_engine(cli: str | None) -> Path | None:
    if cli:
        return Path(cli).resolve() if Path(cli).is_file() else None
    for c in ("build-bench/bin/ChessEngine.exe", "build/bin/ChessEngine.exe", "build/bin/ChessEngine"):
        p = Path(c)
        if p.exists():
            return p.resolve()
    return None

def stage_verify(args: argparse.Namespace, float_path: Path, net_path: Path) -> None:
    engine = find_engine(args.engine)
    if engine is None:
        raise ValueError("engine binary required for parity; build it and pass --engine")
    model = load_float_model(float_path)
    q = quantize_model(model)

    # Each position is evaluated as-is and colour-mirrored. STK-HalfKA is
    # colour-symmetric by construction (the mover's features are identical in
    # the mirrored position), so the two evals must be exactly equal -- this
    # catches any side-to-move sign bug in training or inference.
    mirrored = [mirror_fen(fen) for fen in BENCH_FENS]
    option = "EvalFile" if model.hidden == 1024 else "EvalFileSmall"
    lines = [f"setoption name {option} value {net_path}"]
    for fen, mfen in zip(BENCH_FENS, mirrored, strict=True):
        lines += [f"position fen {fen}", "eval", f"position fen {mfen}", "eval"]
    lines.append("quit")
    res = subprocess.run(
        [str(engine)], input="\n".join(lines) + "\n", capture_output=True, text=True, timeout=120, check=False
    )
    scores = [int(tok.split("score:")[1].split("cp")[0]) for tok in res.stdout.splitlines() if "score:" in tok]
    if res.returncode != 0 or f"{option} loaded" not in res.stdout or len(scores) != 2 * len(BENCH_FENS):
        raise SystemExit(f"[verify] FAIL: engine did not load/evaluate the net\n{res.stdout[-800:]}")

    # Engine must match the integer reference exactly (same math, same ints);
    # the float column is informational (quantization drift).
    worst = mirror_worst = 0
    for i, fen in enumerate(BENCH_FENS):
        engine_cp, mirror_cp = scores[2 * i], scores[2 * i + 1]
        int_cp = python_eval_int(q, fen)
        float_cp = python_eval(model, fen)
        worst = max(worst, abs(int_cp - engine_cp))
        mirror_worst = max(mirror_worst, abs(engine_cp - mirror_cp))
        print(
            f"[verify] engine {engine_cp:6d}  py-int {int_cp:6d}  mirror {mirror_cp:6d}   "
            f"(float {float_cp:6d})  {fen.split()[0][:20]}"
        )
    if worst > args.tolerance_cp:
        raise SystemExit(f"[verify] FAIL: engine != quantized reference (max diff {worst} cp)")
    if mirror_worst > 0:
        raise SystemExit(f"[verify] FAIL: colour-mirror asymmetry ({mirror_worst} cp) -- stm sign bug")
    print(f"[verify] PASS: engine == quantized reference (max diff {worst} cp), mirror-symmetric")

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="STK-HalfKA NNUE pipeline (prep/train/export/verify, resumable).")
    p.add_argument("--input", "--data", "--dataset", default=None,
                   help=".jsonl(.zst) lichess evals, a '<fen> | <cp>' .txt file, "
                        "or a directory of such .txt shards (datagen_bulk output)")
    p.add_argument("--workdir", required=True)
    p.add_argument("--stage", choices=("all", "prep", "train", "export", "verify"), default="all")
    p.add_argument("--output", default=None, help="copy the verified network to this path")
    p.add_argument("--float-output", "--out-checkpoint", default=None)
    p.add_argument("--checkpoint", "--export-only", default=None)
    p.add_argument("--net", default=None, help="existing network for --stage verify")
    p.add_argument("--resume", default=None)
    p.add_argument("--dataset-manifest", default=None)
    p.add_argument("--allow-untagged-shards", action="store_true", help="only for known older STK-HalfKA shards")
    p.add_argument("--shard-slice", default=None)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=20, help="20 x 200M ~= bullet's canonical 4B visits")
    p.add_argument("--hidden", type=int, default=1024, choices=(1024, 128), help="net width (128 = small net)")
    p.add_argument("--init", default=None,
                   help="warm-start weights from a model_float.pt (RL fine-tune)")
    p.add_argument("--teacher", default=None,
                   help="distill the (128-wide) student from this 1024-wide model_float.pt")
    p.add_argument("--data-dir", default=None,
                   help="reuse an existing prepared shard dir (skips prep; e.g. runs/v2/data)")
    p.add_argument("--mix-shards", type=int, default=1, help="shards shuffled together per group (8 recommended)")
    p.add_argument("--batch-size", type=int, default=16384)
    p.add_argument("--lr", type=float, default=1e-3)
    prep.add_arguments(p)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--engine", default=None, help="ChessEngine binary for the parity check")
    p.add_argument("--tolerance-cp", type=int, default=1)
    args = p.parse_args(argv)
    if min(args.epochs, args.batch_size, args.mix_shards) < 1 or not math.isfinite(args.lr) or args.lr <= 0:
        p.error("epochs, batch-size, mix-shards and lr must be positive")
    if args.tolerance_cp < 0:
        p.error("tolerance-cp must be nonnegative")
    if args.stage in ("all", "verify") and find_engine(args.engine) is None:
        p.error("--engine is required for engine parity")

    global HIDDEN, PAIR
    HIDDEN = args.hidden
    PAIR = HIDDEN // 2

    work = Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(args.seed)

    float_path = Path(args.checkpoint) if args.checkpoint else work / "model_float.pt"
    if args.stage in ("all", "prep", "train") and not args.checkpoint:
        data_dir = Path(args.data_dir) if args.data_dir else stage_prep(args, work)
        if args.stage == "prep":
            return 0
        float_path = stage_train(args, work, data_dir)
        if args.float_output:
            destination = Path(args.float_output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.resolve() != float_path.resolve():
                copy_file(float_path, destination)
        if args.stage == "train":
            return 0
    if args.stage == "verify":
        model = load_float_model(float_path)
        net_path = Path(args.net) if args.net else work / f"stk_halfka_{model.hidden}.nnue"
        check_net(net_path)
    else:
        net_path = stage_export(work, float_path)
    if args.stage in ("all", "verify"):
        stage_verify(args, float_path, net_path)
    if args.output and args.stage != "verify":
        destination = Path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.resolve() != net_path.resolve():
            copy_file(net_path, destination)
    print(f"\nStages complete. Net: {net_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
