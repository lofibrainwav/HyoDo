"""The published description must carry links a reader off GitHub can open.

Two independent contracts live here, and they are deliberately not merged. A
single "no relative links remain" assertion would pass even if the rewriter
destroyed every absolute URL in the file, so the transformed targets and the
preserved ones are checked separately.

The first layer drives the metadata hook directly. The second layer reads the
real built artifacts when they exist; when they do not, the result is reported
as UNOBSERVED rather than silently skipped, because "no artifact" is not
evidence that the artifact is correct.
"""

from __future__ import annotations

import os
import re
import sys
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import hatch_build  # noqa: E402  (repo-root build hook, not an installed module)

LINK = re.compile(r"\]\((?P<target>[^)]*)\)")
ABSOLUTE = ("http://", "https://", "#", "mailto:")


def _targets(markdown: str) -> list[str]:
    """Return every inline-link target outside fenced code blocks, in order."""
    found: list[str] = []
    in_fence = False
    for line in markdown.split("\n"):
        if hatch_build._FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        found.extend(match.group("target") for match in LINK.finditer(line))
    return found


@pytest.fixture(scope="module")
def version() -> str:
    return hatch_build.read_version(REPO_ROOT)


@pytest.fixture(scope="module")
def source_readme() -> str:
    return (REPO_ROOT / "README.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def published(version: str, source_readme: str) -> str:
    return hatch_build.rewrite_relative_links(source_readme, version)


# --- Contract 1: the links that must be transformed --------------------------


def test_every_relative_link_becomes_the_pinned_url_for_its_own_path(
    source_readme: str, published: str, version: str
) -> None:
    """Each relative target maps to this version's tag and keeps its own path."""
    source = _targets(source_readme)
    result = _targets(published)
    assert len(source) == len(result), "link count changed; a link was dropped or added"

    relative = [(index, t) for index, t in enumerate(source) if not t.startswith(ABSOLUTE)]
    assert relative, "README has no relative links; this contract would be vacuous"

    for index, target in relative:
        path, _, fragment = target.partition("#")
        normalized = path[2:] if path.startswith("./") else path
        view = "tree" if normalized.endswith("/") else "blob"
        expected = f"https://github.com/lofibrainwav/HyoDo/{view}/v{version}/{normalized}"
        if fragment:
            expected = f"{expected}#{fragment}"
        assert result[index] == expected, f"{target!r} was published as {result[index]!r}"


def test_every_rewritten_target_exists_in_the_checkout(source_readme: str, version: str) -> None:
    """A pinned link is only useful if the path it names is really there."""
    for target in _targets(source_readme):
        if target.startswith(ABSOLUTE):
            continue
        path = target.partition("#")[0]
        normalized = path[2:] if path.startswith("./") else path
        resolved = REPO_ROOT / normalized
        assert resolved.exists(), f"README links to {normalized}, which does not exist"
        if normalized.endswith("/"):
            assert resolved.is_dir(), f"{normalized} ends in / but is not a directory"
        else:
            assert resolved.is_file(), f"{normalized} is not a file; add a trailing /"


def test_no_relative_link_survives_publication(published: str) -> None:
    for target in _targets(published):
        assert target.startswith(ABSOLUTE), f"relative link survived: {target!r}"


# --- Contract 2: the links and text that must be preserved ------------------


def test_absolute_urls_are_carried_through_verbatim(source_readme: str, published: str) -> None:
    """The rewriter must not touch a link that already works off GitHub."""
    source_absolute = [t for t in _targets(source_readme) if t.startswith(ABSOLUTE)]
    published_absolute = [t for t in _targets(published) if t in source_absolute]
    assert published_absolute == source_absolute


def test_a_fragment_is_kept_attached_to_its_path(published: str, version: str) -> None:
    """An in-page anchor must survive, not be swallowed into the path."""
    expected = (
        f"https://github.com/lofibrainwav/HyoDo/blob/v{version}/docs/CONNECT.md#what-to-commit"
    )
    assert expected in published


def test_fenced_code_blocks_are_left_alone(source_readme: str, published: str) -> None:
    """Template markers such as ``vX.Y.Z`` are examples, not links to pin."""
    assert "vX.Y.Z" in source_readme, "the template marker moved; update this contract"
    assert published.count("vX.Y.Z") == source_readme.count("vX.Y.Z")

    def fenced_lines(markdown: str) -> list[str]:
        lines, in_fence = [], False
        for line in markdown.split("\n"):
            if hatch_build._FENCE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                lines.append(line)
        return lines

    assert fenced_lines(published) == fenced_lines(source_readme)


def test_readme_on_disk_stays_relative_for_github_readers(source_readme: str) -> None:
    """The rewrite is for published metadata only; the file must not change."""
    assert any(not t.startswith(ABSOLUTE) for t in _targets(source_readme))


# --- Contract 3: the artifacts that actually ship ---------------------------


def _description(archive: Path) -> tuple[str, str | None]:
    if archive.name.endswith(".tar.gz"):
        with tarfile.open(archive, "r:gz") as tar:
            name = next(n for n in tar.getnames() if n.endswith("/PKG-INFO"))
            member = tar.extractfile(name)
            assert member is not None
            raw = member.read().decode("utf-8")
    else:
        with zipfile.ZipFile(archive) as wheel:
            name = next(n for n in wheel.namelist() if n.endswith(".dist-info/METADATA"))
            raw = wheel.read(name).decode("utf-8")
    message = Parser().parsestr(raw)
    payload = message.get_payload()
    assert isinstance(payload, str)
    return payload, message.get("Description-Content-Type")


def _built_artifacts() -> list[Path]:
    outdir = Path(os.environ.get("HYODO_DIST_DIR", REPO_ROOT / "dist"))
    if not outdir.is_dir():
        return []
    return sorted([*outdir.glob("hyodo-*.tar.gz"), *outdir.glob("hyodo-*.whl")])


def _artifacts_required() -> bool:
    # A source-only run may honestly lack artifacts and reports UNOBSERVED. A
    # lane that has just built them sets this so that absence becomes a failure:
    # otherwise the one check of what users actually download never runs.
    return os.environ.get("HYODO_REQUIRE_BUILT_ARTIFACTS") == "1"


def test_built_artifacts_publish_the_rewritten_description(published: str) -> None:
    """Check the real artifacts, or report UNOBSERVED -- never a silent skip."""
    artifacts = _built_artifacts()
    if _artifacts_required():
        kinds = {"sdist" if a.name.endswith(".tar.gz") else "wheel" for a in artifacts}
        assert kinds == {"sdist", "wheel"}, (
            "HYODO_REQUIRE_BUILT_ARTIFACTS=1 but HYODO_DIST_DIR does not hold both a "
            f"wheel and an sdist: {[a.name for a in artifacts]}"
        )
    if not artifacts:
        pytest.skip(
            "UNOBSERVED: no built artifacts found. Run `python -m build --outdir <dir>` "
            "and set HYODO_DIST_DIR to that directory. Absence of an artifact is not "
            "evidence that the artifact is correct."
        )

    descriptions = {}
    for artifact in artifacts:
        payload, content_type = _description(artifact)
        assert content_type == "text/markdown", f"{artifact.name} lost its content type"
        for target in _targets(payload):
            assert target.startswith(ABSOLUTE), f"{artifact.name} ships a relative link: {target!r}"
        descriptions[artifact.name] = payload.strip()

    assert len(set(descriptions.values())) == 1, (
        f"sdist and wheel ship different descriptions: {sorted(descriptions)}"
    )
    assert next(iter(descriptions.values())) == published.strip()


def test_required_lane_fails_instead_of_skipping_when_artifacts_are_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Guard the guard: the canonical lane must not be able to report a skip here.
    monkeypatch.setenv("HYODO_DIST_DIR", str(tmp_path))
    monkeypatch.setenv("HYODO_REQUIRE_BUILT_ARTIFACTS", "1")
    with pytest.raises(AssertionError, match="both a wheel and an sdist"):
        test_built_artifacts_publish_the_rewritten_description("")

    (tmp_path / "hyodo-0.0.0-py3-none-any.whl").write_bytes(b"")
    with pytest.raises(AssertionError, match="both a wheel and an sdist"):
        test_built_artifacts_publish_the_rewritten_description("")


def test_source_only_run_still_reports_unobserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HYODO_DIST_DIR", str(tmp_path))
    monkeypatch.delenv("HYODO_REQUIRE_BUILT_ARTIFACTS", raising=False)
    with pytest.raises(pytest.skip.Exception, match="UNOBSERVED"):
        test_built_artifacts_publish_the_rewritten_description("")
