"""RED/GREEN guard: every ``run:`` step in ci.yml that uses a shell pipe (``|``)
also enables ``pipefail``.

Without ``set -o pipefail`` (or ``set -euo pipefail``), bash only reports the
exit status of the last command in a pipeline. A pattern like
``cat file | jq . > /dev/null`` silently ignores a missing or unreadable
file — ``jq`` sees empty stdin and the step can still exit 0. Requiring
``pipefail`` alongside every pipe keeps upstream failures from being
swallowed.
"""

from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "ci.yml"


def _run_blocks() -> list[tuple[str, str, str]]:
    """Return (job_name, step_name, run_script) for every step with a run: key."""
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    out: list[tuple[str, str, str]] = []
    for job_name, job in data["jobs"].items():
        for step in job.get("steps", []):
            if "run" in step:
                out.append((job_name, step.get("name", "<unnamed>"), step["run"]))
    return out


def test_ci_workflow_is_valid_yaml():
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert data["jobs"]


def test_every_pipe_run_block_enables_pipefail():
    offenders = [
        (job_name, step_name)
        for job_name, step_name, script in _run_blocks()
        if "|" in script and "pipefail" not in script
    ]
    assert offenders == [], f"run: blocks with a pipe but no pipefail: {offenders}"
