import os
from pathlib import Path

import pytest
import yaml

CONFIG_PATH = Path(__file__).parent.parent / "config" / "slo.yml"


def test_slo_config_exists() -> None:
    assert CONFIG_PATH.exists(), f"SLO config not found at {CONFIG_PATH}"


def test_slo_config_valid_yaml() -> None:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data is not None
    assert "version" in data
    assert "slos" in data
    assert isinstance(data["slos"], list)


def test_slo_targets_and_windows() -> None:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for slo in data["slos"]:
        # Name and Service are required
        assert "name" in slo
        assert "service" in slo

        # Target must be between 0 and 1
        target = slo.get("target")
        assert target is not None
        assert 0 < target <= 1.0

        # Window must be defined
        assert "window" in slo

        # SLI PromQL must exist
        assert "sli" in slo
        assert "promql" in slo["sli"]


def test_slo_pillars() -> None:
    valid_pillars = ["眞", "善", "美", "孝", "永"]
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for slo in data["slos"]:
        pillar = slo.get("pillar")
        assert pillar in valid_pillars, f"Invalid pillar '{pillar}' in SLO '{slo.get('name')}'"
