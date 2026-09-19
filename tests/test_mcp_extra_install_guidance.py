"""The optional MCP extra must be installable by whoever reads the advice.

HyoDo's own install command is `pipx install hyodo`, and pipx keeps the package
in an isolated environment. Advice that says only `pip install 'hyodo[mcp]'`
therefore sends a pipx user to a different interpreter, where the install
succeeds and `hyodo mcp` still reports the SDK as missing. HyoDo has no evidence
of how it was installed, so it names both paths rather than guessing one.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hyodo.cli import main as cli

REPO_ROOT = Path(__file__).resolve().parents[1]

PIP_COMMAND = "pip install 'hyodo[mcp]'"
PIPX_COMMAND = "pipx install --force 'hyodo[mcp]'"

DOCUMENTS = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "QUICK_START.md",
    REPO_ROOT / "site/src/content/docs/docs/quickstart.md",
)


def test_cli_names_both_install_paths(capsys: pytest.CaptureFixture[str]) -> None:
    cli._print_mcp_missing()
    output = capsys.readouterr().out
    assert "not installed" in output
    assert PIP_COMMAND in output
    assert PIPX_COMMAND in output
    assert "same environment" in output


def test_cli_message_keeps_the_literal_the_smoke_workflow_greps_for() -> None:
    """.github/workflows/smoke.yml asserts on this exact substring."""
    workflow = (REPO_ROOT / ".github/workflows/smoke.yml").read_text(encoding="utf-8")
    assert 'grep -Fq "hyodo[mcp]"' in workflow, "the smoke assertion moved; update this test"
    assert "hyodo[mcp]" in cli.MCP_EXTRA_PIP
    assert "hyodo[mcp]" in cli.MCP_EXTRA_PIPX


def test_doctor_label_offers_both_paths() -> None:
    assert PIP_COMMAND in cli.MCP_EXTRA_INLINE
    assert PIPX_COMMAND in cli.MCP_EXTRA_INLINE


@pytest.mark.parametrize("document", DOCUMENTS, ids=lambda p: p.name)
def test_documents_that_mention_the_extra_name_both_paths(document: Path) -> None:
    """A document may skip the extra entirely, but must not name only pip."""
    text = document.read_text(encoding="utf-8")
    if "hyodo[mcp]" not in text:
        pytest.skip(f"UNOBSERVED: {document.name} does not mention the extra")
    assert PIPX_COMMAND in text, (
        f"{document.name} names the pip install path without the pipx one; a reader "
        "who installed with pipx would install into the wrong environment"
    )


def test_web_quickstart_says_where_to_run_the_commands() -> None:
    """Every command in the quickstart is relative to the project directory."""
    text = (REPO_ROOT / "site/src/content/docs/docs/quickstart.md").read_text(encoding="utf-8")
    assert "cd your-project" in text
    install_index = text.index("pipx install hyodo")
    assert text.index("cd your-project") < install_index, (
        "the working-directory step must come before the first command"
    )
