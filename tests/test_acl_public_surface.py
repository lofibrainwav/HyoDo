"""Regression guards for research-boundary and friction public surfaces."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX = REPO_ROOT / "site" / "src" / "pages" / "index.astro"
EVIDENCE_GRAPH = REPO_ROOT / "site" / "src" / "pages" / "evidence-graph.astro"
ASTRO_CONFIG = REPO_ROOT / "site" / "astro.config.mjs"
TOKENS = REPO_ROOT / "site" / "src" / "styles" / "tokens.css"
ACL = REPO_ROOT / "site" / "src" / "content" / "docs" / "docs" / "acl.md"
RESEARCH = REPO_ROOT / "site" / "src" / "content" / "docs" / "docs" / "research.md"
FRICTION = REPO_ROOT / "site" / "src" / "content" / "docs" / "docs" / "friction-contribution.md"


def _assert_docs_research_navigation(text: str) -> None:
    docs = text.index('href="/docs/quickstart/">Docs')
    research = text.index('href="/docs/research/">Research')
    assert docs < research
    assert 'href="/docs/acl/">ACL' not in text


def test_public_nav_keeps_research_boundaries_explicit() -> None:
    _assert_docs_research_navigation(INDEX.read_text(encoding="utf-8"))
    _assert_docs_research_navigation(EVIDENCE_GRAPH.read_text(encoding="utf-8"))
    assert "docs/acl" not in ASTRO_CONFIG.read_text(encoding="utf-8")


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
    assert "research-only field note" in text
    assert "not a shipped HyoDo capability" in text
    assert "research labeling target" in text
    assert "not a shipped HyoDo classifier" in text
    assert "Baselines designed to disprove the Wisdom Reflex" in text
    assert "Threats to validity" in text


def test_acl_and_research_explain_their_distinct_roles() -> None:
    acl = ACL.read_text(encoding="utf-8")
    research = RESEARCH.read_text(encoding="utf-8")
    assert "Reader map." in acl
    assert "Reader map." in research
    assert "focused field note" in acl
    assert "](/docs/research/)" in acl
    assert "broader empirical program" in research
    assert "benchmark status" in research
    assert "](/docs/acl/)" in research
