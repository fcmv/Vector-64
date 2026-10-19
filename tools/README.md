# Development tools

| Directory | Purpose |
|---|---|
| `bench/` | Resumable benchmark collectors, shell build comparisons and profiling. |
| `nnue/` | Shared STK-HalfKA preparation, training, export, validation and match tools. |
| `bullet/` | External Bullet trainer integration and transfer checks. |
| `experiments/` | SPRT experiment drivers, including historical reproductions. |
| `docs/` | Documentation checks, site hooks and recording overlays. |
| `release/` | Exact-commit check gates, binary staging, notices, checksums and verified draft publication. |

The root keeps supported launchers such as `run_benchmarks.ps1`,
`run_training.ps1`, `run_pipeline.py`, `benchmark.py` and the existing Bash/SPRT
command names. Implementations live in the directories above. Package commands
such as `python -m tools.nnue.make_net --help` also work from the repository root.

Search fingerprints remain in `bench_signature.txt`, checked by
`bench_signature.sh` and deliberately regenerated with
`update_bench_signature.sh` only for an accepted search/network change.

Read the [repository layout](../docs/repository-layout.md),
[benchmark methodology](../BENCHMARK.md), [training guide](../docs/nnue-training.md)
and [contribution checks](../CONTRIBUTING.md) before running experiments.
