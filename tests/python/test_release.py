from __future__ import annotations

import json
import subprocess
import zipfile

import pytest

from tools.release import package, publish
from tools.release.require_checks import require_success

COMMIT = "a" * 40


def run(number=1, conclusion="success", **overrides):
    return {"head_sha": COMMIT, "event": "push", "head_branch": "main", "run_number": number,
            "status": "completed", "conclusion": conclusion, "html_url": "https://example.com/run",
            **overrides}


def test_release_checks_use_latest_exact_main_push():
    require_success([run(), run(2, "failure", head_branch="other"), run(3, "failure", event="pull_request")],
                    COMMIT, "ci.yml")
    with pytest.raises(ValueError, match="must complete successfully"):
        require_success([run(), run(2, "failure")], COMMIT, "ci.yml")
    with pytest.raises(ValueError, match="must complete successfully"):
        require_success([run(), run(run_attempt=2, status="in_progress", conclusion=None)], COMMIT, "ci.yml")


def test_release_checks_reject_other_revisions_and_events():
    for candidate in (run(head_sha="b" * 40), run(event="workflow_dispatch"), run(head_branch="other")):
        with pytest.raises(ValueError, match="no main push run"):
            require_success([candidate], COMMIT, "ci.yml")


@pytest.fixture
def source(tmp_path, monkeypatch):
    root = tmp_path / "source"
    for name in ("nets/stk-vector-64.nnue", "ui/dist/index.html", "tools/bench_signature.txt",
                 "LICENSE", "THIRD_PARTY_NOTICES.md", "nets/model-card.md", "ui/package.json",
                 "third_party/fathom/LICENSE", "third_party/licenses/README.md"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name, encoding="utf-8")
    (root / "ui/package-lock.json").write_text(json.dumps({"packages": {
        "": {}, "node_modules/chessground": {"version": "9.2.1", "license": "GPL-3.0-or-later"},
    }}), encoding="utf-8")
    dependency = root / "ui/node_modules/chessground"
    dependency.mkdir(parents=True)
    (dependency / "LICENSE").write_text("GPL text", encoding="utf-8")
    monkeypatch.setattr(package, "ROOT", root)
    return root


def build_fixture(tmp_path, extension=""):
    build = tmp_path / "build"
    binaries = build / "bin"
    if extension:
        binaries /= "Release"
    binaries.mkdir(parents=True)
    for target in package.TARGETS:
        (binaries / (target + extension)).write_bytes(target.encode("ascii"))
    (build / "CMakeCache.txt").write_text("ENGINE_NATIVE:BOOL=OFF\n", encoding="utf-8")
    compiler = build / "CMakeFiles/3.31/CMakeCXXCompiler.cmake"
    compiler.parent.mkdir(parents=True)
    compiler.write_text('set(CMAKE_CXX_COMPILER_ID "GNU")\n', encoding="utf-8")
    return build


@pytest.mark.parametrize("extension", ["", ".exe"])
def test_release_final_checksums_cover_every_download(source, tmp_path, extension):
    asset = "Vector-test" + extension
    output = tmp_path / "dist"
    package.stage(build_fixture(tmp_path, extension), output, asset, COMMIT, "refs/tags/v1.1.0")
    package.notices(output / "release-notices.zip", COMMIT)
    (output / "release-source.tar.gz").write_bytes(b"source archive")
    package.finalize(output, COMMIT, [asset])
    assert set(package.verify(output)) == {path.name for path in output.iterdir()}
    manifest = (output / "SHA256SUMS").read_text().splitlines()
    assert len(manifest) == len(list(output.iterdir())) - 1
    for line in manifest:
        digest, name = line.split("  ")
        assert package.sha256(output / name) == digest
    with zipfile.ZipFile(output / "release-notices.zip") as archive:
        assert archive.read("ui-dependencies/node_modules/chessground/LICENSE") == b"GPL text"
        assert COMMIT in archive.read("SOURCE.txt").decode()


def test_release_rejects_missing_capability_before_staging(source, tmp_path):
    build = build_fixture(tmp_path)
    (build / "bin/ChessEngine-viz").unlink()
    output = tmp_path / "dist"
    with pytest.raises(ValueError, match="ChessEngine-viz"):
        package.stage(build, output, "Vector-test", COMMIT, "refs/tags/v1.1.0")
    assert not output.exists()


@pytest.mark.parametrize("damage", ["binary", "platform", "commit", "extra-file", "source"])
def test_release_rejects_damaged_or_incomplete_downloads(source, tmp_path, damage):
    output = tmp_path / "dist"
    package.stage(build_fixture(tmp_path), output, "Vector-test", COMMIT, "refs/tags/v1.1.0")
    package.notices(output / "release-notices.zip", COMMIT)
    (output / "release-source.tar.gz").write_bytes(b"source archive")
    assets, commit = ["Vector-test"], COMMIT
    if damage == "binary":
        (output / "Vector-test-nnue").write_bytes(b"changed after staging")
    elif damage == "platform":
        assets.append("missing-platform")
    elif damage == "commit":
        commit = "b" * 40
    elif damage == "source":
        (output / "release-source.tar.gz").unlink()
    else:
        (output / "unexpected.exe").write_bytes(b"unrecorded")
    with pytest.raises(ValueError):
        package.finalize(output, commit, assets)
    assert not (output / "SHA256SUMS").exists()


def test_release_notices_reject_missing_dependency_license(source, tmp_path):
    (source / "ui/node_modules/chessground/LICENSE").unlink()
    with pytest.raises(ValueError, match="Missing license text"):
        package.notices(tmp_path / "notices.zip", COMMIT)


@pytest.mark.parametrize("damage", ["empty", "directory", "network", "ui", "capability", "record-name"])
def test_release_rejects_invalid_content_and_mixed_build_identity(source, tmp_path, damage):
    output = tmp_path / "dist"
    package.stage(build_fixture(tmp_path), output, "Vector-test", COMMIT, "refs/tags/v1.1.0")
    package.notices(output / "release-notices.zip", COMMIT)
    (output / "release-source.tar.gz").write_bytes(b"source archive")
    record_path = output / "Vector-test.build.json"
    record = json.loads(record_path.read_text())
    if damage == "empty":
        (output / "Vector-test").write_bytes(b"")
    elif damage == "directory":
        (output / "nested").mkdir()
    elif damage in {"network", "ui"}:
        record["network_sha256" if damage == "network" else "ui_bundle_sha256"] = "f" * 64
        package.write_json(record_path, record)
    elif damage == "record-name":
        record_path.rename(output / "wrong.build.json")
    else:
        (output / "Vector-test-viz").rename(output / "unrelated")
        record["files"]["unrelated"] = record["files"].pop("Vector-test-viz")
        package.write_json(record_path, record)
    with pytest.raises(ValueError):
        package.finalize(output, COMMIT, ["Vector-test"])


def test_release_staging_rejects_empty_binary(source, tmp_path):
    build = build_fixture(tmp_path)
    (build / "bin/ChessEngine-nnue").write_bytes(b"")
    with pytest.raises(ValueError, match="Required release binaries missing"):
        package.stage(build, tmp_path / "dist", "Vector-test", COMMIT, "refs/tags/v1.1.0")


@pytest.mark.parametrize("entry", ["../outside", "-option", "two words", "Vector-test\nextra"])
def test_release_manifest_rejects_unsafe_filenames(tmp_path, entry):
    (tmp_path / "SHA256SUMS").write_text(f"{'0' * 64}  {entry}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        package.verify(tmp_path)


def test_release_verification_rejects_unrecorded_files(tmp_path):
    (tmp_path / "expected").write_bytes(b"data")
    (tmp_path / "extra").write_bytes(b"unexpected")
    (tmp_path / "SHA256SUMS").write_text(f"{package.sha256(tmp_path / 'expected')}  expected\n", encoding="utf-8")
    with pytest.raises(ValueError, match="complete release"):
        package.verify(tmp_path)


def test_public_release_and_other_source_drafts_are_never_reused():
    with pytest.raises(ValueError, match="already public"):
        publish.check_release({"draft": False}, COMMIT)
    with pytest.raises(ValueError, match="different source"):
        publish.check_release({"draft": True, "target_commitish": "b" * 40}, COMMIT)


def test_release_api_errors_are_not_treated_as_absent(monkeypatch):
    monkeypatch.setattr(publish.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 1, "", "HTTP 403"))
    with pytest.raises(RuntimeError, match="403"):
        publish.get_release("owner/repo", "v1.1.0")


def test_public_release_lookup_uses_tag_endpoint(monkeypatch):
    release = {"id": 1, "tag_name": "v1.1.1", "draft": False}
    monkeypatch.setattr(publish.subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(a, 0, json.dumps(release), ""))
    calls = []
    monkeypatch.setattr(publish, "gh", lambda *a: calls.append(a))
    assert publish.get_release("owner/repo", "v1.1.1") == release
    assert not calls


@pytest.mark.parametrize("matching", [False, True])
def test_release_lookup_finds_draft_in_paginated_listing(monkeypatch, matching):
    draft = {"id": 2, "tag_name": "v1.1.1", "draft": True, "target_commitish": COMMIT}
    monkeypatch.setattr(publish.subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(a, 1, "", "HTTP 404"))
    calls = []

    def gh(*arguments):
        calls.append(arguments)
        return json.dumps([[{"tag_name": "v1.1.0"}], [draft] if matching else []])

    monkeypatch.setattr(publish, "gh", gh)
    assert publish.get_release("owner/repo", "v1.1.1") == (draft if matching else None)
    assert calls == [("api", "--paginate", "--slurp", "repos/owner/repo/releases?per_page=100")]


def test_release_lookup_rejects_duplicate_tag_drafts(monkeypatch):
    monkeypatch.setattr(publish.subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(a, 1, "", "HTTP 404"))
    monkeypatch.setattr(publish, "gh", lambda *a: json.dumps([[{"tag_name": "v1.1.1"}] * 2]))
    with pytest.raises(ValueError, match="Multiple releases"):
        publish.get_release("owner/repo", "v1.1.1")


def test_release_lookup_listing_failure_is_not_treated_as_absent(monkeypatch):
    monkeypatch.setattr(publish.subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(a, 1, "", "HTTP 404"))

    def gh(*arguments):
        raise subprocess.CalledProcessError(1, arguments)

    monkeypatch.setattr(publish, "gh", gh)
    with pytest.raises(subprocess.CalledProcessError):
        publish.get_release("owner/repo", "v1.1.1")


@pytest.mark.parametrize("digest", [None, "sha256:short", "sha1:" + "a" * 40])
def test_release_remote_assets_require_complete_sha256(monkeypatch, digest):
    monkeypatch.setattr(publish, "gh", lambda *a, **k: json.dumps([[{"name": "asset", "state": "uploaded",
                                                                  "digest": digest}]]))
    with pytest.raises(ValueError, match="SHA256"):
        publish.asset_hashes("owner/repo", 1)


@pytest.mark.parametrize("damage", [None, "upload", "draft", "tag"])
def test_release_publishes_only_an_exact_complete_draft(monkeypatch, tmp_path, damage):
    package.write_json(tmp_path / "release-builds.json", {"commit": COMMIT})
    hashes = {"asset": "a" * 64, "SHA256SUMS": "b" * 64}
    monkeypatch.setattr(publish, "verify", lambda path: hashes)
    draft = {"id": 1, "draft": True, "target_commitish": COMMIT}
    reads = iter([draft, {**draft, "draft": False} if damage == "draft" else draft])
    monkeypatch.setattr(publish, "get_release", lambda *a: next(reads))
    uploaded = iter([{ "asset": "a" * 64}, {**hashes, "unexpected": "c" * 64} if damage == "upload" else hashes])
    monkeypatch.setattr(publish, "asset_hashes", lambda *a: next(uploaded))
    tags = []

    def check_tag(*args):
        tags.append(args)
        if damage == "tag" and len(tags) == 2:
            raise ValueError("Remote tag moved")

    monkeypatch.setattr(publish, "check_tag", check_tag)
    calls = []
    monkeypatch.setattr(publish, "gh", lambda *a, **k: calls.append(a))
    if damage:
        with pytest.raises(ValueError):
            publish.publish(tmp_path, "owner/repo", "v1.1.0", COMMIT, tmp_path / "notes.md")
        assert not any("PATCH" in call for call in calls)
    else:
        publish.publish(tmp_path, "owner/repo", "v1.1.0", COMMIT, tmp_path / "notes.md")
        assert calls[0] == ("release", "upload", "v1.1.0", "--repo", "owner/repo", str(tmp_path / "SHA256SUMS"))
        assert "PATCH" in calls[-1] and "draft=false" in calls[-1]


def test_new_release_is_created_as_draft_and_stays_private_on_upload_failure(monkeypatch, tmp_path):
    package.write_json(tmp_path / "release-builds.json", {"commit": COMMIT})
    monkeypatch.setattr(publish, "verify", lambda path: {"asset": "a" * 64})
    monkeypatch.setattr(publish, "check_tag", lambda *a: None)
    releases = iter([None, {"id": 1, "draft": True, "target_commitish": COMMIT}])
    monkeypatch.setattr(publish, "get_release", lambda *a: next(releases))
    monkeypatch.setattr(publish, "asset_hashes", lambda *a: {})
    calls = []

    def gh(*arguments, **kwargs):
        calls.append(arguments)
        if arguments[:2] == ("release", "upload"):
            raise subprocess.CalledProcessError(1, arguments)

    monkeypatch.setattr(publish, "gh", gh)
    with pytest.raises(subprocess.CalledProcessError):
        publish.publish(tmp_path, "owner/repo", "v1.1.0-rc.1", COMMIT, tmp_path / "notes.md")
    assert calls[0][:2] == ("release", "create")
    assert "--draft" in calls[0] and "--prerelease" in calls[0]
    assert not any("PATCH" in call for call in calls)
