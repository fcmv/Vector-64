"""Publish a complete verified draft without modifying an existing public release."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

from tools.release.package import verify

VERSION = re.compile(r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?")


def gh(*arguments: str, timeout: int = 60) -> str:
    return subprocess.check_output(["gh", *arguments], text=True, timeout=timeout)


def get_release(repo: str, tag: str) -> dict | None:
    result = subprocess.run(["gh", "api", f"repos/{repo}/releases/tags/{tag}"],
                            text=True, capture_output=True, timeout=60)
    if result.returncode:
        if "HTTP 404" in result.stderr:
            return None
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def check_release(release: dict | None, commit: str) -> None:
    if release is not None:
        if not release["draft"]:
            raise ValueError("Release is already public; publish a new version instead of replacing its assets")
        if release["target_commitish"] != commit:
            raise ValueError("Existing draft belongs to a different source identity")


def check_tag(repo: str, tag: str, commit: str) -> None:
    obj = json.loads(gh("api", f"repos/{repo}/git/ref/tags/{tag}"))["object"]
    for _ in range(8):
        if obj["type"] != "tag":
            break
        obj = json.loads(gh("api", f"repos/{repo}/git/tags/{obj['sha']}"))["object"]
    if obj["type"] != "commit" or obj["sha"] != commit:
        raise ValueError("Remote tag no longer identifies the tested commit")


def asset_hashes(repo: str, release_id: int) -> dict[str, str]:
    pages = json.loads(gh("api", "--paginate", "--slurp", f"repos/{repo}/releases/{release_id}/assets?per_page=100"))
    assets = [asset for page in pages for asset in page]
    if len({asset["name"] for asset in assets}) != len(assets):
        raise ValueError("Remote draft contains duplicate filenames")
    if any(asset["state"] != "uploaded" or not re.fullmatch(r"sha256:[0-9a-f]{64}", asset.get("digest") or "")
           for asset in assets):
        raise ValueError("Remote draft contains an incomplete upload or lacks a SHA256 digest")
    return {asset["name"]: asset["digest"].removeprefix("sha256:") for asset in assets}


def publish(output: Path, repo: str, tag: str, commit: str, notes: Path) -> None:
    hashes = verify(output)
    if json.loads((output / "release-builds.json").read_text(encoding="utf-8"))["commit"] != commit:
        raise ValueError("Release artifacts belong to another commit")
    check_tag(repo, tag, commit)
    release = get_release(repo, tag)
    check_release(release, commit)
    if release is None:
        arguments = ["release", "create", tag, "--repo", repo, "--verify-tag", "--target", commit,
                     "--draft", "--title", tag, "--notes-file", str(notes), "--generate-notes"]
        if "-" in tag:
            arguments.append("--prerelease")
        gh(*arguments)
        release = get_release(repo, tag)
        if release is None:
            raise ValueError("Created draft could not be read back")
        check_release(release, commit)
    existing = asset_hashes(repo, release["id"])
    if any(name not in hashes or hashes[name] != digest for name, digest in existing.items()):
        raise ValueError("Existing draft assets differ; inspect the draft before retrying")
    missing = [str(output / name) for name in sorted(hashes.keys() - existing.keys())]
    if missing:
        gh("release", "upload", tag, "--repo", repo, *missing, timeout=900)
    if asset_hashes(repo, release["id"]) != hashes:
        raise ValueError("Uploaded draft does not match the complete verified manifest")
    check_tag(repo, tag, commit)
    current = get_release(repo, tag)
    check_release(current, commit)
    if current is None or current["id"] != release["id"]:
        raise ValueError("Draft identity changed during upload")
    gh("api", "--method", "PATCH", f"repos/{repo}/releases/{release['id']}", "-F", "draft=false",
       "-f", "make_latest=false" if "-" in tag else "make_latest=legacy")
    print(f"Published {repo} {tag} with {len(hashes)} verified files")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("dist"))
    parser.add_argument("--notes", type=Path, default=Path(".github/release-notes.md"))
    args = parser.parse_args()
    if (not args.repo or not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repo)
            or not VERSION.fullmatch(args.tag) or not re.fullmatch(r"[0-9a-f]{40}", args.commit)):
        parser.error("repository, full commit SHA and version tag are required")
    if args.check_only:
        check_tag(args.repo, args.tag, args.commit)
        check_release(get_release(args.repo, args.tag), args.commit)
    else:
        publish(args.output, args.repo, args.tag, args.commit, args.notes)


if __name__ == "__main__":
    main()
