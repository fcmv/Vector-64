"""Compatibility launcher for tools.bench.benchmark."""
from pathlib import Path

if __name__ == "__main__" and not __package__:
    import runpy
    runpy.run_path(str(Path(__file__).resolve().parent / "_entrypoint.py"),
                    init_globals={"MODULE": "tools.benchmark", "ARGV0": __file__}, run_name="__main__")

from .bench.benchmark import main

if __name__ == "__main__":
    raise SystemExit(main())
