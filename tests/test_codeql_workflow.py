"""Keep the CodeQL workflow a small, pinned Python SAST evidence lane."""

from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "codeql.yml"
PINNED_ACTION = re.compile(r"uses:\s+[^\s@]+@[0-9a-f]{40}(?:\s+#.*)?$")


def test_codeql_workflow_is_pinned_python_sast() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "pull_request:" in text
    assert "branches: [main]" in text
    assert "schedule:" in text
    assert "workflow_dispatch:" in text
    assert "languages: python" in text
    assert "security-events: write" in text
    assert "contents: read" in text
    assert "github/codeql-action/init@" in text
    assert "github/codeql-action/analyze@" in text

    action_lines = [line.strip() for line in text.splitlines() if "uses:" in line]
    assert action_lines, "CodeQL workflow must declare pinned actions"
    assert all(PINNED_ACTION.fullmatch(line) for line in action_lines)
