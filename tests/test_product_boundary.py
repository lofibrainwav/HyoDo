"""Keep the HyoDo/Kingdom product boundary explicit and regression-tested."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = REPO_ROOT / "docs" / "PRODUCT_BOUNDARY.md"


def test_product_boundary_is_the_explicit_ownership_contract() -> None:
    text = BOUNDARY.read_text(encoding="utf-8")

    required_phrases = (
        "HyoDo is a verification and evidence plane",
        "Kingdom is an execution plane",
        "does not plan tasks, execute",
        "execution authority and worker lifecycle",
        "are not HyoDo state",
        "HyoDo closeout and Kingdom closeout are separate decisions",
        "UNATTRIBUTED",
    )
    for phrase in required_phrases:
        assert phrase in text


def test_public_docs_point_to_the_boundary_contract() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    current_state = (REPO_ROOT / "docs" / "CURRENT_STATE.md").read_text(encoding="utf-8")

    assert "docs/PRODUCT_BOUNDARY.md" in readme
    assert "PRODUCT_BOUNDARY.md" in current_state
