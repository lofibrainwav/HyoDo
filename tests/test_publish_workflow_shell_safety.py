"""RED/GREEN guard: no unbound ``${{ }}`` expression interpolation inside a
``run:`` shell block of publish.yml.

Interpolating a GitHub Actions expression (e.g. a git tag name) directly into
a ``run:`` bash script lets an attacker-controlled string (tags allow shell
metacharacters like ``;``, ``$()``, backticks, ``&&``, ``|``) execute
arbitrary shell code before the glob-based tag-format check ever runs.
The safe pattern is: bind the value via ``env:`` and reference it as
``"$ENV_VAR"`` inside the script — never ``${{ ... }}`` inside ``run:``.
"""

from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "publish.yml"


def _run_blocks() -> list[tuple[str, str, str]]:
    """Return (job_name, step_name, run_script) for every step with a run: key."""
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    out: list[tuple[str, str, str]] = []
    for job_name, job in data["jobs"].items():
        for step in job.get("steps", []):
            if "run" in step:
                out.append((job_name, step.get("name", "<unnamed>"), step["run"]))
    return out


def test_publish_workflow_is_valid_yaml():
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert data["jobs"]


def test_no_expression_interpolation_inside_run_blocks():
    """Guards against the shell-injection pattern fixed in H1d.

    ``${{ ... }}`` expressions must never appear directly inside a ``run:``
    script — values must be passed through ``env:`` and referenced as
    ``"$VAR"`` so shell metacharacters in the value cannot be interpreted.
    """
    offenders = [
        (job_name, step_name)
        for job_name, step_name, script in _run_blocks()
        if "${{" in script
    ]
    assert offenders == [], f"run: blocks with unbound ${{{{ }}}} interpolation: {offenders}"
