"""docs/MISREAD.md exists and names the remaining honesty-gap surfaces."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MISREAD = REPO_ROOT / "docs" / "MISREAD.md"


def test_misread_doc_exists_and_names_shadow_allowlist_and_policy_trust() -> None:
    assert MISREAD.is_file()
    text = MISREAD.read_text(encoding="utf-8").lower()
    assert "shadow" in text
    assert "allowlist" in text
    assert "policy-trust" in text
