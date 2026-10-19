"""Stage all release capabilities and record the exact downloadable bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGETS = ("ChessEngine", "ChessEngine-nnue", "ChessEngine-all", "ChessEngine-variants",
           "ChessEngine-validator", "ChessEngine-viz")


def validate_name(name: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
        raise ValueError("asset must be a plain filename starting with a letter or number")


def binary_names(asset: str) -> set[str]:
    validate_name(asset)
    extension = ".exe" if asset.endswith(".exe") else ""
    return {asset.removesuffix(".exe") + target.removeprefix("ChessEngine") + extension for target in TARGETS}


def release_files(output: Path) -> list[Path]:
    paths = sorted(output.iterdir())
    if any(path.is_symlink() or not path.is_file() or path.stat().st_size == 0 for path in paths):
        raise ValueError("release output must contain only nonempty regular files")
    for path in paths:
        validate_name(path.name)
    return paths


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def stage(build: Path, output: Path, asset: str, commit: str, ref: str) -> None:
    validate_name(asset)
    extension = ".exe" if asset.endswith(".exe") else ""
    binaries = build / "bin"
    if (binaries / "Release").is_dir():
        binaries /= "Release"
    missing = [target for target in TARGETS if not (binaries / (target + extension)).is_file()
               or (binaries / (target + extension)).is_symlink()
               or (binaries / (target + extension)).stat().st_size == 0]
    if missing:
        raise ValueError("Required release binaries missing: " + ", ".join(missing))
    if output.exists() and any(output.iterdir()):
        raise ValueError("release output must be empty")
    cache = (build / "CMakeCache.txt").read_text(encoding="utf-8")
    compiler_files = sorted((build / "CMakeFiles").glob("*/CMakeCXXCompiler.cmake"))
    if len(compiler_files) != 1:
        raise ValueError("one configured C++ compiler identity is required")
    output.mkdir(parents=True, exist_ok=True)
    files = {}
    base = asset.removesuffix(".exe")
    for target in TARGETS:
        name = base + target.removeprefix("ChessEngine") + extension
        destination = output / name
        shutil.copy2(binaries / (target + extension), destination)
        files[name] = sha256(destination)
    record = {
        "asset": asset, "commit": commit, "ref": ref,
        "source": f"https://github.com/fcmv/Vector-64/tree/{commit}",
        "compiler": compiler_files[0].read_text(encoding="utf-8"),
        "cmake_cache": cache,
        "network_sha256": sha256(ROOT / "nets/stk-vector-64.nnue"),
        "ui_bundle_sha256": sha256(ROOT / "ui/dist/index.html"),
        "ui_lock_sha256": sha256(ROOT / "ui/package-lock.json"),
        "search_signatures": (ROOT / "tools/bench_signature.txt").read_text(encoding="utf-8"),
        "files": files,
    }
    write_json(output / (base + ".build.json"), record)


def notices(output: Path, commit: str) -> None:
    lock = json.loads((ROOT / "ui/package-lock.json").read_text(encoding="utf-8"))
    files = {name: ROOT / name for name in (
        "LICENSE", "THIRD_PARTY_NOTICES.md", "nets/model-card.md", "ui/package.json", "ui/package-lock.json",
        "third_party/fathom/LICENSE", "third_party/licenses/README.md",
    )}
    for path in sorted((ROOT / "third_party/licenses").glob("*.txt")):
        files[path.relative_to(ROOT).as_posix()] = path
    inventory = []
    for name, package in sorted(lock["packages"].items()):
        if not name or package.get("dev"):
            continue
        directory = ROOT / "ui" / name
        texts = [path for path in directory.iterdir()
                 if path.is_file() and path.name.lower().startswith(("license", "licence", "copying", "notice"))]
        if not texts and name == "node_modules/@pixi/colord" and package["version"] == "2.9.6":
            texts = [ROOT / "third_party/licenses/colord.txt"]
        if not texts:
            raise ValueError(f"Missing license text for {name}@{package['version']}")
        for text in texts:
            files[f"ui-dependencies/{name}/{text.name}"] = text
        inventory.append({"package": name, "version": package["version"], "license": package.get("license"),
                          "resolved": package.get("resolved"), "integrity": package.get("integrity")})
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, path in sorted(files.items()):
            archive.write(path, name)
        archive.writestr("ui-dependencies.json", json.dumps(inventory, indent=2) + "\n")
        archive.writestr("SOURCE.txt", f"Source commit: {commit}\n"
                         f"https://github.com/fcmv/Vector-64/tree/{commit}\n"
                         f"https://github.com/fcmv/Vector-64/archive/{commit}.tar.gz\n"
                         "Build records and SHA256SUMS accompany these notices in the release.\n"
                         "Model provenance and distribution terms remain as recorded in nets/model-card.md.\n")


def finalize(output: Path, commit: str, expected_assets: list[str]) -> None:
    if not expected_assets or len(expected_assets) != len(set(expected_assets)):
        raise ValueError("expected platforms must be nonempty and unique")
    paths = release_files(output)
    records = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(output.glob("*.build.json"))]
    if sorted(record["asset"] for record in records) != sorted(expected_assets):
        raise ValueError("release matrix is incomplete or contains duplicate/unexpected platforms")
    expected = {"release-notices.zip", "release-source.tar.gz"}
    identity = {"network_sha256": sha256(ROOT / "nets/stk-vector-64.nnue"),
                "ui_bundle_sha256": sha256(ROOT / "ui/dist/index.html"),
                "ui_lock_sha256": sha256(ROOT / "ui/package-lock.json"),
                "search_signatures": (ROOT / "tools/bench_signature.txt").read_text(encoding="utf-8")}
    for record in records:
        if record["commit"] != commit or set(record["files"]) != binary_names(record["asset"]):
            raise ValueError("release build identity or capability count mismatch")
        if any(record.get(key) != value for key, value in identity.items()):
            raise ValueError("release builds disagree with the source network, UI or search signatures")
        expected.add(record["asset"].removesuffix(".exe") + ".build.json")
        for name, digest in record["files"].items():
            if Path(name).name != name or name in expected or sha256(output / name) != digest:
                raise ValueError(f"release asset is duplicated or changed after staging: {name}")
            expected.add(name)
    actual = {path.name for path in paths}
    if actual != expected:
        raise ValueError("release files differ from the build records")
    write_json(output / "release-builds.json", {"commit": commit, "builds": records})
    assets = sorted(path for path in output.iterdir() if path.is_file())
    (output / "SHA256SUMS").write_text("".join(f"{sha256(path)}  {path.name}\n" for path in assets),
                                       encoding="utf-8", newline="\n")


def verify(output: Path) -> dict[str, str]:
    paths = release_files(output)
    names = {path.name for path in paths}
    hashes = {}
    for line in (output / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if not match:
            raise ValueError("invalid SHA256SUMS entry")
        digest, name = match.groups()
        if name == "SHA256SUMS" or name in hashes or name not in names or sha256(output / name) != digest:
            raise ValueError(f"duplicated or changed release file: {name}")
        hashes[name] = digest
    if set(hashes) != names - {"SHA256SUMS"}:
        raise ValueError("SHA256SUMS does not cover the complete release")
    return hashes | {"SHA256SUMS": sha256(output / "SHA256SUMS")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    stage_parser = commands.add_parser("stage")
    stage_parser.add_argument("--build", type=Path, required=True)
    stage_parser.add_argument("--asset", required=True)
    stage_parser.add_argument("--ref", required=True)
    commands.add_parser("notices")
    final_parser = commands.add_parser("finalize")
    final_parser.add_argument("--assets", nargs="+", required=True)
    for command in commands.choices.values():
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--commit", required=True)
    args = parser.parse_args()
    if args.command == "stage":
        stage(args.build, args.output, args.asset, args.commit, args.ref)
    elif args.command == "notices":
        notices(args.output, args.commit)
    else:
        finalize(args.output, args.commit, args.assets)


if __name__ == "__main__":
    main()
