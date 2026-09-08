"""docs/CLAIMS.md exists and forbids implying a large installed base."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAIMS = REPO_ROOT / "docs" / "CLAIMS.md"
WHY_HYODO = REPO_ROOT / "site" / "src" / "content" / "docs" / "docs" / "why-hyodo.md"


def test_claims_doc_exists_and_forbids_implied_installed_base() -> None:
    assert CLAIMS.is_file()
    text = CLAIMS.read_text(encoding="utf-8")
    lower = re.sub(r"\s+", " ", text.lower())
    assert "## What we do not claim" in text
    assert "installed base" in lower
    assert "star count" in lower
    assert "teams/companies using hyodo" in lower
    assert "dated public source" in lower
    assert "pypi" in lower
    assert "version" in lower
    assert "integrity score" in lower
    assert "social proof" in lower
    for phrase in (
        "thousands of users",
        "widely used",
        "trusted by",
        "used by companies",
    ):
        assert phrase not in lower


def test_why_hyodo_points_at_claims_doc() -> None:
    text = WHY_HYODO.read_text(encoding="utf-8")
    assert "CLAIMS.md" in text


def test_docs_index_points_at_claims_doc() -> None:
    text = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "CLAIMS.md" in text
