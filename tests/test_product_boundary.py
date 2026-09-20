"""Keep HyoDo's standalone public product boundary explicit and regression-tested."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = REPO_ROOT / "docs" / "PRODUCT_BOUNDARY.md"


def test_product_boundary_is_the_explicit_ownership_contract() -> None:
    text = BOUNDARY.read_text(encoding="utf-8")

    required_phrases = (
        "HyoDo is a local verification and evidence layer",
        "## HyoDo owns",
        "## HyoDo does not own",
        "Execution is not evidence",
        "Evidence is not authority",
        "Missing evidence is not a pass",
        "Recorded history is not current runtime truth",
        "does not execute the observed work",
        "UNATTRIBUTED",
    )
    for phrase in required_phrases:
        assert phrase in text


def test_public_docs_point_to_the_boundary_contract() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    current_state = (REPO_ROOT / "docs" / "CURRENT_STATE.md").read_text(encoding="utf-8")
    site_boundary = (
        REPO_ROOT / "site" / "src" / "content" / "docs" / "docs" / "product-boundary.md"
    ).read_text(encoding="utf-8")

    assert "docs/PRODUCT_BOUNDARY.md" in readme
    assert "PRODUCT_BOUNDARY.md" in current_state
    assert "## HyoDo owns" in site_boundary
    assert "## HyoDo does not own" in site_boundary
    assert "Evidence is not authority" in site_boundary
