"""docs/FULL_BODY.md exists and names the digest-only default, operator consent, and no rotation/redaction."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FULL_BODY = REPO_ROOT / "docs" / "FULL_BODY.md"
FDE_README = REPO_ROOT / "examples" / "fde-evidence-spine" / "README.md"


def test_full_body_doc_names_digest_only_operator_consent_and_no_redaction() -> None:
    assert FULL_BODY.is_file()
    text = FULL_BODY.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "digest-only" in lowered
    assert "--allow-full-body" in text
    assert "does not rotate" in lowered
    assert "redact" in lowered


def test_fde_example_points_at_full_body_doc() -> None:
    text = FDE_README.read_text(encoding="utf-8")
    assert "--full-body" in text
    assert "FULL_BODY.md" in text


def test_docs_index_points_at_full_body_doc() -> None:
    text = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "FULL_BODY.md" in text
