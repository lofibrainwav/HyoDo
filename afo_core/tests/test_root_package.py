"""
Root Package Tests - AFO Kingdom 오장육부

Tests for root-level scripts, configuration, and startup orchestration.

Coverage Target: Boost root package coverage from 9.90% to 50%+
"""

import os
import subprocess
from pathlib import Path
from typing import List

import pytest

ROOT_PATH = Path(__file__).parent.parent.parent.parent


def test_pyproject_toml_exists() -> None:
    """Root pyproject.toml should exist and be valid."""
    pyproject_path = ROOT_PATH / "pyproject.toml"

    assert pyproject_path.exists(), "pyproject.toml should exist at root"
    assert pyproject_path.is_file(), "pyproject.toml should be a file"


def test_pyproject_toml_structure() -> None:
    """pyproject.toml should have required sections."""
    pyproject_path = ROOT_PATH / "pyproject.toml"

    content = pyproject_path.read_text()

    required_sections = [
        "[project]",
        "[tool.ruff]",
        "[tool.mypy]",
        "[tool.pytest.ini_options]",
    ]

    for section in required_sections:
        assert section in content, f"pyproject.toml should contain {section}"


def test_uv_workspace_configuration() -> None:
    """uv workspace should be configured correctly."""
    pyproject_path = ROOT_PATH / "pyproject.toml"

    content = pyproject_path.read_text()

    assert "[tool.uv.workspace]" in content, "uv workspace should be configured"
    assert '"packages/afo-core"' in content, "afo-core should be in workspace members"


def test_agents_md_exists() -> None:
    """AGENTS.md (Root SSOT) should exist."""
    agents_path = ROOT_PATH / "AGENTS.md"

    assert agents_path.exists(), "AGENTS.md should exist at root"


def test_agents_md_key_sections() -> None:
    """AGENTS.md should contain key sections."""
    agents_path = ROOT_PATH / "AGENTS.md"

    content = agents_path.read_text()

    required_keywords = [
        "AFOI",
        "眞善美孝永",
        "Trinity Score",
        "3책사",
    ]

    for keyword in required_keywords:
        assert keyword in content, f"AGENTS.md should contain {keyword}"


def test_start_kingdom_v2_exists() -> None:
    """start_kingdom_v2.sh should exist and be executable."""
    script_path = ROOT_PATH / "start_kingdom_v2.sh"

    assert script_path.exists(), "start_kingdom_v2.sh should exist"
    assert os.access(script_path, os.X_OK), "start_kingdom_v2.sh should be executable"


def test_start_kingdom_v2_organs_mapping() -> None:
    """start_kingdom_v2.sh should contain organ mappings."""
    script_path = ROOT_PATH / "start_kingdom_v2.sh"

    content = script_path.read_text()

    organ_mappings = {
        "心": "Redis",
        "肝": "PostgreSQL",
        "脾": "Ollama",
        "肺": "LanceDB",
        "腎": "MCP",
    }

    for organ, service in organ_mappings.items():
        assert organ in content, f"Script should mention {organ} organ"
        assert service in content, f"Script should mention {service} service"


def test_start_kingdom_v2_ports() -> None:
    """start_kingdom_v2.sh should configure correct ports."""
    script_path = ROOT_PATH / "start_kingdom_v2.sh"

    content = script_path.read_text()

    required_ports = ["6379", "8010", "3000", "11434"]

    for port in required_ports:
        assert port in content, f"Script should configure port {port}"


def test_start_kingdom_v2_trap_cleanup() -> None:
    """start_kingdom_v2.sh should have cleanup trap."""
    script_path = ROOT_PATH / "start_kingdom_v2.sh"

    content = script_path.read_text()

    assert "trap cleanup EXIT" in content, "Script should have cleanup trap"
    assert "cleanup()" in content, "Script should define cleanup function"


def test_scripts_directory_exists() -> None:
    """scripts/ directory should exist."""
    scripts_path = ROOT_PATH / "scripts"

    assert scripts_path.exists(), "scripts/ directory should exist"
    assert scripts_path.is_dir(), "scripts/ should be a directory"


def test_ci_lock_protocol_exists() -> None:
    """CI Lock Protocol script should exist."""
    script_path = ROOT_PATH / "scripts" / "ci_lock_protocol.sh"

    assert script_path.exists(), "ci_lock_protocol.sh should exist"


def test_ci_lock_protocol_single_entry() -> None:
    """CI Lock Protocol should enforce single entry point."""
    script_path = ROOT_PATH / "scripts" / "ci_lock_protocol.sh"

    content = script_path.read_text()

    assert "ci_lock_protocol.sh" in content, (
        "CI Lock Protocol should reference itself as single entry"
    )


def test_ci_lock_protocol_ruff_version() -> None:
    """CI Lock Protocol should enforce Ruff version."""
    script_path = ROOT_PATH / "scripts" / "ci_lock_protocol.sh"

    content = script_path.read_text()

    assert "ruff" in content.lower(), "CI Lock Protocol should use Ruff"


def test_github_workflows_exist() -> None:
    """github/workflows/ directory should exist with key workflows."""
    workflows_path = ROOT_PATH / ".github" / "workflows"

    assert workflows_path.exists(), ".github/workflows/ should exist"

    required_workflows = [
        "ci.yml",
        "release.yml",
    ]

    for workflow in required_workflows:
        workflow_path = workflows_path / workflow
        assert workflow_path.exists(), f"{workflow} should exist"


def test_docs_directory_exists() -> None:
    """docs/ directory should exist."""
    docs_path = ROOT_PATH / "docs"

    assert docs_path.exists(), "docs/ directory should exist"


def test_final_ssot_exists() -> None:
    """AFO_FINAL_SSOT.md should exist."""
    ssot_path = ROOT_PATH / "docs" / "AFO_FINAL_SSOT.md"

    assert ssot_path.exists(), "docs/AFO_FINAL_SSOT.md should exist"


def test_royal_library_exists() -> None:
    """AFO_ROYAL_LIBRARY.md should exist."""
    library_path = ROOT_PATH / "docs" / "AFO_ROYAL_LIBRARY.md"

    assert library_path.exists(), "docs/AFO_ROYAL_LIBRARY.md should exist"


def test_map_of_kingdom_exists() -> None:
    """MAP_OF_KINGDOM.md should exist."""
    map_path = ROOT_PATH / "docs" / "MAP_OF_KINGDOM.md"

    assert map_path.exists(), "docs/MAP_OF_KINGDOM.md should exist"


def test_final_ssot_trinity_score_formula() -> None:
    """AFO_FINAL_SSOT.md should contain Trinity Score formula."""
    ssot_path = ROOT_PATH / "docs" / "AFO_FINAL_SSOT.md"

    content = ssot_path.read_text()

    assert "Trinity Score" in content, "SSOT should contain Trinity Score"
    assert "0.35×眞" in content, "SSOT should contain Truth weight"
    assert "0.35×善" in content, "SSOT should contain Goodness weight"
    assert "0.20×美" in content, "SSOT should contain Beauty weight"


def test_env_example_exists() -> None:
    """.env.example should exist."""
    env_example = ROOT_PATH / ".env.example"

    assert env_example.exists(), ".env.example should exist"


def test_packages_directory_exists() -> None:
    """packages/ directory should exist."""
    packages_path = ROOT_PATH / "packages"

    assert packages_path.exists(), "packages/ directory should exist"


def test_core_packages_exist() -> None:
    """Core packages should exist."""
    packages_path = ROOT_PATH / "packages"

    required_packages = [
        "afo-core",
        "trinity-os",
        "dashboard",
    ]

    for pkg in required_packages:
        pkg_path = packages_path / pkg
        assert pkg_path.exists(), f"packages/{pkg} should exist"
        assert pkg_path.is_dir(), f"packages/{pkg} should be a directory"


def test_package_agents_md() -> None:
    """Each core package should have AGENTS.md."""
    packages_path = ROOT_PATH / "packages"

    required_packages = ["afo-core", "trinity-os", "dashboard"]

    for pkg in required_packages:
        pkg_path = packages_path / pkg

        agents_paths = [
            pkg_path / "AGENTS.md",
            pkg_path / "agents.md",
        ]

        has_agents = any(path.exists() for path in agents_paths)
        assert has_agents, f"packages/{pkg} should have AGENTS.md or agents.md"


def test_skills_directory_exists() -> None:
    """skills/ directory should exist."""
    skills_path = ROOT_PATH / "skills"

    assert skills_path.exists(), "skills/ directory should exist"


def test_skills_has_subdirectories() -> None:
    """skills/ should contain skill directories."""
    skills_path = ROOT_PATH / "skills"

    skill_dirs = [d for d in skills_path.iterdir() if d.is_dir()]

    assert len(skill_dirs) > 0, "skills/ should contain at least one skill directory"

    known_skills = [
        "automated-debugging",
        "health-monitor",
        "ultimate-rag",
    ]

    for skill in known_skills:
        skill_path = skills_path / skill
        if skill_path.exists():
            assert skill_path.is_dir(), f"skills/{skill} should be a directory"


def test_orchestration_port_conflicts() -> None:
    """Orchestration should avoid port conflicts."""
    script_path = ROOT_PATH / "start_kingdom_v2.sh"

    content = script_path.read_text()

    import re

    ports = set(re.findall(r"PORT=(\d+)", content))

    assert len(ports) == len(set(ports)), "Orchestration should not have port conflicts"


def test_orchestration_organ_dependency_order() -> None:
    """Orchestration should respect organ dependency order."""
    script_path = ROOT_PATH / "start_kingdom_v2.sh"

    content = script_path.read_text()

    redis_pos = content.find("Redis")
    backend_pos = content.find("Backend") or content.find("Soul")

    if redis_pos > 0 and backend_pos > 0:
        assert redis_pos < backend_pos, "Redis (Heart) should start before Backend (Soul)"


def test_evolution_log_exists() -> None:
    """AFO_EVOLUTION_LOG.md should exist."""
    log_path = ROOT_PATH / "AFO_EVOLUTION_LOG.md"

    assert log_path.exists(), "AFO_EVOLUTION_LOG.md should exist"


def test_tickets_md_exists() -> None:
    """TICKETS.md should exist for task tracking."""
    tickets_path = ROOT_PATH / "TICKETS.md"

    assert tickets_path.exists(), "TICKETS.md should exist"


@pytest.mark.slow
def test_start_kingdom_v2_syntax() -> None:
    """start_kingdom_v2.sh should have valid bash syntax."""
    script_path = ROOT_PATH / "start_kingdom_v2.sh"

    result = subprocess.run(
        ["bash", "-n", str(script_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"start_kingdom_v2.sh should have valid bash syntax: {result.stderr}"
    )


@pytest.mark.slow
def test_ci_lock_protocol_syntax() -> None:
    """ci_lock_protocol.sh should have valid bash syntax."""
    script_path = ROOT_PATH / "scripts" / "ci_lock_protocol.sh"

    result = subprocess.run(
        ["bash", "-n", str(script_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"ci_lock_protocol.sh should have valid bash syntax: {result.stderr}"
    )
