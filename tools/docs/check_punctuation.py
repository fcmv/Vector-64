"""Reject em and en dashes in repository documentation."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    paths = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    ).decode("utf-8").split("\0")
    failures = 0
    count = 0
    for name in sorted(set(paths)):
        path = ROOT / name
        if path.suffix.lower() not in {".md", ".markdown", ".rst", ".adoc"} or not path.is_file():
            continue
        count += 1
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "\u2013" in line or "\u2014" in line:
                print(f"{name}:{number}: replace em/en dashes with ASCII punctuation")
                failures += 1
    print(f"Checked {count} documentation files; {failures} punctuation violations.")
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
