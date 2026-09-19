"""Publish a README whose links work outside the repository.

PyPI renders the project description with no repository around it, so a
relative link like ``](./docs/GATES_SYNTAX.md)`` resolves under
``https://pypi.org/project/hyodo/`` and returns 404. GitHub needs the opposite:
relative links keep following whatever ref the reader is on. Both are served by
rewriting links for the published metadata only -- ``README.md`` stays relative
on disk, and the published copy is pinned to the tag that carries this VERSION,
so a reader of version N sees version N's documents.

The rewrite is deliberately narrow. It touches link targets that are relative,
outside fenced code blocks, and nothing else: absolute URLs, fragment-only
anchors, fenced examples such as the ``vX.Y.Z`` template markers, and anchors
attached to a path are all preserved verbatim.
"""

from __future__ import annotations

import re
from pathlib import Path

try:
    from hatchling.metadata.plugin.interface import MetadataHookInterface
except ModuleNotFoundError:  # pragma: no cover - the build backend is not a test dependency
    # The renderer below is pure text handling and is imported directly by
    # tests/test_pypi_readme_links.py, which runs in an environment that has no
    # build backend installed. Only the hook class needs hatchling.
    MetadataHookInterface = object  # type: ignore[assignment,misc]

REPO_URL = "https://github.com/lofibrainwav/HyoDo"

# A markdown inline-link target: the "(...)" that follows "](" . Targets that
# contain parentheses or whitespace are rejected rather than guessed at, so a
# future README cannot be silently mangled.
_LINK = re.compile(r"\]\((?P<target>[^)]*)\)")
_FENCE = re.compile(r"^\s*(?:```|~~~)")
_ABSOLUTE_PREFIXES = ("http://", "https://", "#", "mailto:")


def read_version(root: Path) -> str:
    """Return the VERSION file's content, the single version source of truth."""
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def rewrite_target(target: str, version: str) -> str:
    """Return the published form of one relative link target.

    A target ending in ``/`` is a directory and needs GitHub's ``tree`` view;
    ``blob`` is for files. Any ``#fragment`` is carried through untouched so an
    in-page anchor keeps working.
    """
    path, separator, fragment = target.partition("#")
    if not path:
        return target
    normalized = path[2:] if path.startswith("./") else path
    view = "tree" if normalized.endswith("/") else "blob"
    return f"{REPO_URL}/{view}/v{version}/{normalized}{separator}{fragment}"


def rewrite_relative_links(markdown: str, version: str) -> str:
    """Rewrite relative link targets outside fenced code blocks."""
    lines = markdown.split("\n")
    in_fence = False
    for index, line in enumerate(lines):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        def replace(match: re.Match[str]) -> str:
            target = match.group("target")
            if target.startswith(_ABSOLUTE_PREFIXES):
                return match.group(0)
            if not target or any(character.isspace() for character in target):
                raise ValueError(
                    f"README link target is empty or contains whitespace: {target!r}. "
                    "Link titles and unencoded spaces are not supported; encode or "
                    "make the link absolute."
                )
            return f"]({rewrite_target(target, version)})"

        lines[index] = _LINK.sub(replace, line)

    if in_fence:
        raise ValueError("README has an unclosed fenced code block")
    return "\n".join(lines)


def render_pypi_readme(root: Path) -> str:
    """Return README.md with its relative links pinned to this version's tag."""
    version = read_version(root)
    return rewrite_relative_links((root / "README.md").read_text(encoding="utf-8"), version)


class CustomMetadataHook(MetadataHookInterface):  # type: ignore[misc]
    """Supply ``project.readme`` so the published links are absolute."""

    PLUGIN_NAME = "custom"

    def update(self, metadata: dict) -> None:
        metadata["readme"] = {
            "content-type": "text/markdown",
            "text": render_pypi_readme(Path(self.root)),
        }
