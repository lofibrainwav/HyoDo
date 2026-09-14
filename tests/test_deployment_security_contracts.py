"""Regression contracts for the hardened optional deployment surfaces."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_compose_keeps_redis_private_and_postgres_secret_required() -> None:
    compose = (REPO_ROOT / "docker-compose.minimal.yml").read_text(encoding="utf-8")

    assert "container_name:" not in compose
    redis_block = compose.split("  redis:\n", 1)[1].split("  postgres:\n", 1)[0]
    assert "ports:" not in redis_block
    assert '"127.0.0.1:15432:5432"' in compose
    assert "${HYODO_POSTGRES_PASSWORD:?" in compose
    assert "POSTGRES_PASSWORD: hyodo_dev" not in compose


def test_dockerfile_builds_a_non_editable_runtime_image_without_dev_tools() -> None:
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")

    base_images = re.findall(
        r"^FROM (python:3\.12-slim@sha256:[0-9a-f]{64})", dockerfile, re.MULTILINE
    )
    assert len(base_images) == 2
    assert base_images[0] == base_images[1]
    assert "pip wheel --no-cache-dir --no-deps" in dockerfile
    assert "pip install --no-cache-dir --no-compile --no-deps /app/hyodo-*.whl" in dockerfile
    assert "pip install -e" not in dockerfile
    assert "USER hyodo" in dockerfile
    assert "pip install ruff" not in dockerfile
    assert "pip install pyright" not in dockerfile
    assert "pip install pytest" not in dockerfile


def test_security_workflow_keeps_all_external_actions_sha_pinned() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "security.yml").read_text(encoding="utf-8")

    uses = [line.strip() for line in workflow.splitlines() if line.strip().startswith("uses:")]
    assert uses
    assert all("@" in line and len(line.rsplit("@", 1)[1].split()[0]) == 40 for line in uses)
    assert "dependency-review-action" in workflow
