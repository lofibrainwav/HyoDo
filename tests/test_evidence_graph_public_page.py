"""Public /evidence-graph/ is a demo fixture, not a live ledger."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PAGE = REPO_ROOT / "site" / "src" / "pages" / "evidence-graph.astro"
SITE_DOC = REPO_ROOT / "site" / "src" / "content" / "docs" / "docs" / "evidence-graph.md"


def test_public_evidence_graph_page_names_demo_fixture_and_local_dashboard() -> None:
    text = PAGE.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "demo fixture" in lowered
    assert "hyodo dashboard" in lowered
    assert "/graph" in text
    assert "nothing is uploaded" in lowered or "nothing here is uploaded" in lowered
    assert "remote ledger" not in lowered or "no remote" in lowered or "not a remote" in lowered


def test_site_evidence_graph_doc_keeps_fixture_release_boundary() -> None:
    text = SITE_DOC.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "demo fixture" in lowered
    assert "does not read a real ledger" in lowered
    assert "hyodo.evidence-graph/v1" in lowered
