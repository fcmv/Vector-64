"""Require successful main-branch push checks for an exact source commit."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess


def require_success(runs: list[dict], commit: str, workflow: str) -> None:
    matching = [run for run in runs if run["head_sha"] == commit
                and run["event"] == "push" and run["head_branch"] == "main"]
    if not matching:
        raise ValueError(f"{workflow}: no main push run exists for {commit}")
    latest = max(matching, key=lambda run: (run["run_number"], run.get("run_attempt", 1)))
    if latest["status"] != "completed" or latest["conclusion"] != "success":
        raise ValueError(f"{workflow}: latest run for {commit} must complete successfully: {latest['html_url']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit) or not args.repo:
        parser.error("a full commit SHA and repository are required")
    for workflow in ("ci.yml", "docs.yml"):
        endpoint = (f"repos/{args.repo}/actions/workflows/{workflow}/runs"
                    f"?head_sha={args.commit}&event=push&branch=main&per_page=100")
        output = subprocess.check_output(["gh", "api", "--paginate", "--slurp", endpoint], text=True)
        runs = [run for page in json.loads(output) for run in page["workflow_runs"]]
        require_success(runs, args.commit, workflow)
        print(f"{workflow}: successful main push checks for {args.commit}")


if __name__ == "__main__":
    main()
