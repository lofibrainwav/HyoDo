"""docs/FULL_BODY.md exists and names the digest-only default, operator consent, and no rotation/redaction."""

import inspect
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


def test_mcp_serve_has_no_allow_full_body_flag() -> None:
    from hyodo.cli.main import mcp_serve
    from hyodo.mcp_server import _create_http_app, create_server

    serve_src = inspect.getsource(mcp_serve)
    http_src = inspect.getsource(_create_http_app)
    assert "--allow-full-body" not in serve_src
    assert "allow_full_body" not in serve_src
    assert "allow_full_body" not in http_src
    assert inspect.signature(create_server).parameters["allow_full_body"].default is False
