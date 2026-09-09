"""Regression guards for the public ACL / friction research surface."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX = REPO_ROOT / "site" / "src" / "pages" / "index.astro"
EVIDENCE_GRAPH = REPO_ROOT / "site" / "src" / "pages" / "evidence-graph.astro"
TOKENS = REPO_ROOT / "site" / "src" / "styles" / "tokens.css"
ACL = REPO_ROOT / "site" / "src" / "content" / "docs" / "docs" / "acl.md"
RESEARCH = REPO_ROOT / "site" / "src" / "content" / "docs" / "docs" / "research.md"
FRICTION = REPO_ROOT / "site" / "src" / "content" / "docs" / "docs" / "friction-contribution.md"


def _assert_docs_acl_research_order(text: str) -> None:
    docs = text.index('href="/docs/quickstart/">Docs')
    acl = text.index('href="/docs/acl/">ACL')
    research = text.index('href="/docs/research/">Research')
    assert docs < acl < research


def test_public_nav_keeps_acl_next_to_docs_everywhere() -> None:
    _assert_docs_acl_research_order(INDEX.read_text(encoding="utf-8"))
    _assert_docs_acl_research_order(EVIDENCE_GRAPH.read_text(encoding="utf-8"))


def test_public_nav_has_narrow_screen_fallback() -> None:
    css = TOKENS.read_text(encoding="utf-8")
    assert "@media (max-width: 560px)" in css
    assert "body .navbar .nav-links" in css
    assert "a[href^='https://']" in css
    assert "display: none" in css


def test_friction_docs_state_the_cli_version_boundary() -> None:
    text = FRICTION.read_text(encoding="utf-8")
    assert "introduced in **HyoDo 4.17.0**" in text
    assert "4.16.x and earlier do not expose this command" in text
    assert '"hyodo_version": "4.17.0"' in text


def test_acl_does_not_claim_friction_taxonomy_is_automatically_classified() -> None:
    text = ACL.read_text(encoding="utf-8")
    assert "research labeling target" in text
    assert "not a shipped HyoDo classifier" in text
    assert "Baselines designed to disprove the Wisdom Reflex" in text
    assert "Threats to validity" in text


def test_acl_and_research_explain_their_distinct_roles() -> None:
    acl = ACL.read_text(encoding="utf-8")
    research = RESEARCH.read_text(encoding="utf-8")
    assert "Reader map." in acl
    assert "Reader map." in research
    assert "Wisdom Reflex" in acl
    assert "broader empirical program" in acl
    assert "benchmark status" in research
