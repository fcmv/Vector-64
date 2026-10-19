"""Run legacy file commands as package modules without changing cwd or sys.path."""
from __future__ import annotations

import importlib.util
import runpy
import sys
from pathlib import Path

module = globals().get("MODULE")
if not isinstance(module, str) or not module.startswith("tools."):
    raise SystemExit("Use a tool command or python -m tools.<module>.")

if "tools" not in sys.modules:
    spec = importlib.util.spec_from_file_location("tools", Path(__file__).with_name("__init__.py"))
    assert spec is not None and spec.loader is not None
    package = importlib.util.module_from_spec(spec)
    sys.modules["tools"] = package
    spec.loader.exec_module(package)

sys.argv[0] = str(globals().get("ARGV0", module))
runpy.run_module(module, run_name="__main__")
raise SystemExit(0)
