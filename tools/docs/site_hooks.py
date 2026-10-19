"""Render canonical repository documents on the site with source-relative links."""
from __future__ import annotations

import posixpath
import re
from pathlib import Path
from urllib.parse import quote, urlsplit

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
CANONICAL = {
    "changelog.md": "CHANGELOG.md",
    "contributing.md": "CONTRIBUTING.md",
    "limitations.md": "LIMITATIONS.md",
    "stability.md": "STABILITY.md",
    "benchmark.md": "BENCHMARK.md",
    "releasing.md": "RELEASING.md",
    "roadmap.md": "ROADMAP.md",
    "support.md": "SUPPORT.md",
    "security.md": "SECURITY.md",
    "third-party-notices.md": "THIRD_PARTY_NOTICES.md",
    "model-card.md": "nets/model-card.md",
    "bullet.md": "tools/bullet/README.md",
    "syzygy.md": "src/syzygy/README.md",
    "examples.md": "examples/README.md",
}
SOURCE_TO_PAGE = {(ROOT / source).resolve(): page for page, source in CANONICAL.items()}
SOURCE_TO_PAGE[ROOT / "README.md"] = "index.md"
LINK = re.compile(r"(?P<label>!?\[[^\]\n]*\])\((?P<target>[^)\s]+)\)")


def on_page_markdown(markdown: str, page: Page, config: MkDocsConfig, files: Files) -> str:
    source_name = CANONICAL.get(page.file.src_uri)
    if source_name is None:
        return markdown
    source = ROOT / source_name
    page.edit_url = f"https://github.com/fcmv/Vector-64/edit/main/{source_name}"
    content = source.read_text(encoding="utf-8")

    def retarget(match: re.Match[str]) -> str:
        target = match["target"]
        parsed = urlsplit(target)
        if parsed.scheme or target.startswith(("#", "//")):
            return match[0]
        actual = (source.parent / parsed.path).resolve()
        destination = SOURCE_TO_PAGE.get(actual)
        if destination is None and actual.is_relative_to(DOCS) and actual.suffix == ".md":
            destination = actual.relative_to(DOCS).as_posix()
        if destination is not None:
            result = posixpath.relpath(destination, posixpath.dirname(page.file.src_uri) or ".")
        else:
            relative = actual.relative_to(ROOT).as_posix()
            kind = "tree" if actual.is_dir() else "blob"
            result = f"https://github.com/fcmv/Vector-64/{kind}/main/{quote(relative)}"
        if parsed.fragment:
            result += "#" + parsed.fragment
        return f"{match['label']}({result})"

    return LINK.sub(retarget, content)
