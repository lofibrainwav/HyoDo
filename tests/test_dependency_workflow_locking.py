"""Keep CI dependency installation and vulnerability scans bound to locks."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_python_ci_workflows_sync_locked_dependencies() -> None:
    workflows = (
        "ci.yml",
        "discoverability-smoke.yml",
        "mutation.yml",
        "publish.yml",
        "release-evidence.yml",
        "security.yml",
        "smoke.yml",
    )
    for name in workflows:
        content = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert "uv sync --locked" in content, f"{name} does not consume uv.lock"


def test_setup_uv_version_comes_from_the_project_ssot() -> None:
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.uv]" in project
    assert 'required-version = "==0.12.13"' in project
    for path in (ROOT / ".github" / "workflows").glob("*.yml"):
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        for job in workflow.get("jobs", {}).values():
            for step in job.get("steps", []):
                if str(step.get("uses", "")).startswith("astral-sh/setup-uv@"):
                    assert "version" not in step.get("with", {}), (
                        f"{path.name} duplicates the uv version outside pyproject.toml"
                    )


def test_security_workflow_audits_every_lock_profile() -> None:
    content = (ROOT / ".github" / "workflows" / "security.yml").read_text(encoding="utf-8")
    assert "uv sync --locked --all-extras --all-groups --no-editable" in content
    assert "inputs: ci/mcp-v1/requirements.txt" in content
    assert "require-hashes: true" in content
    assert "python -m pip install -r requirements.runtime.txt" not in content


def test_site_workflow_audits_the_locked_npm_tree() -> None:
    content = (ROOT / ".github" / "workflows" / "site.yml").read_text(encoding="utf-8")
    assert "run: npm ci" in content
    assert "run: npm audit --audit-level=low" in content


def test_wheel_smoke_install_is_constrained_by_the_runtime_lock() -> None:
    content = (ROOT / ".github" / "workflows" / "smoke.yml").read_text(encoding="utf-8")
    assert "uv pip install --constraint requirements.runtime.txt dist/*.whl" in content


def test_mcp_v1_lane_uses_an_audited_hash_lock() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    requirements = (ROOT / "ci" / "mcp-v1" / "requirements.txt").read_text(encoding="utf-8")
    assert "--require-hashes -r ci/mcp-v1/requirements.txt" in workflow
    assert "--hash=sha256:" in requirements
    assert re.search(r"^mcp==1\.", requirements, re.MULTILINE)


def test_ci_precommit_is_private_dependency_group() -> None:
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "discoverability-smoke.yml").read_text(
        encoding="utf-8"
    )
    assert "[dependency-groups]" in project
    assert '"pre-commit==4.3.0"' in project
    assert "uv sync --locked --group ci --no-default-groups" in workflow


def test_dependabot_keeps_mcp_v1_lock_on_compatible_major() -> None:
    config = yaml.load(
        (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    entries = [
        entry
        for entry in config["updates"]
        if entry.get("package-ecosystem") == "pip" and entry.get("directory") == "/ci/mcp-v1"
    ]
    assert len(entries) == 1
    assert entries[0]["ignore"][0]["dependency-name"] == "mcp"
    assert ">=2" in entries[0]["ignore"][0]["versions"]


def test_workflow_checkouts_do_not_persist_github_credentials() -> None:
    for path in (ROOT / ".github" / "workflows").glob("*.yml"):
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        for job_name, job in workflow.get("jobs", {}).items():
            for step in job.get("steps", []):
                if str(step.get("uses", "")).startswith("actions/checkout@"):
                    assert step.get("with", {}).get("persist-credentials") is False, (
                        f"{path.name}:{job_name}:{step.get('name', '<unnamed>')}"
                    )
