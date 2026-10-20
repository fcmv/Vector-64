from __future__ import annotations

import subprocess

import pytest

from tools.bench.benchmark import InvalidResult, require_clean_sources


@pytest.mark.parametrize("path", ["cmake/CompilerOptions.cmake", "cmake/Variants.cmake",
                                  "CMakePresets.json", "CMakeUserPresets.json", "src/untracked.cpp"])
def test_build_sources_reject_untracked_staged_and_dirty_files(tmp_path, path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init")
    (tmp_path / "README.md").write_text("fixture")
    git("add", "README.md")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-m", "fixture")
    require_clean_sources(tmp_path)
    source = tmp_path / path
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("original")
    with pytest.raises(InvalidResult, match="commit build/search"):
        require_clean_sources(tmp_path)
    git("add", path)
    with pytest.raises(InvalidResult, match="commit build/search"):
        require_clean_sources(tmp_path)
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-m", "source")
    require_clean_sources(tmp_path)
    source.write_text("modified")
    with pytest.raises(InvalidResult, match="commit build/search"):
        require_clean_sources(tmp_path)


def test_ignored_user_preset_is_not_a_clean_build(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text("CMakeUserPresets.json\n")
    (tmp_path / "CMakeUserPresets.json").write_text("{}")
    with pytest.raises(InvalidResult, match="outside the recorded"):
        require_clean_sources(tmp_path)
