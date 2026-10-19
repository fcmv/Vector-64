"""Map the older command names onto the single STK-HalfKA pipeline."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import make_net


def training_main(argv: list[str] | None = None, stage: str = "all", workdir: str = "runs/pipeline") -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--workdir", default=workdir)
    parser.add_argument("--skip-batching", action="store_true")
    parser.add_argument("--skip-training", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    options, rest = parser.parse_known_args(sys.argv[1:] if argv is None else argv)
    command = ["--workdir", options.workdir]
    if "--stage" not in rest:
        command += ["--stage", "all" if options.skip_training or options.verify else stage]
    if options.dataset:
        dataset = Path(options.dataset)
        if dataset.suffix in (".npz", ".json") or dataset.is_dir() and (dataset / "manifest.json").exists():
            directory = dataset if dataset.is_dir() else dataset.parent
            command += ["--data-dir", str(directory)]
            if dataset.suffix == ".json":
                command += ["--dataset-manifest", str(dataset)]
            elif dataset.suffix == ".npz":
                parser.error("use the dataset manifest or directory so shard identity and counts can be checked")
        else:
            command += ["--input", options.dataset]
    if options.skip_batching:
        command += ["--data-dir", str(Path(options.workdir) / "data")]
    if options.skip_training and "--checkpoint" not in rest and "--export-only" not in rest:
        command += ["--checkpoint", str(Path(options.workdir) / "model_float.pt")]
    return make_net.main(command + rest)
