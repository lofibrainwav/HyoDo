import pytest
from config.antigravity import antigravity


def test_afo_silent_civilization_mode() -> None:
    """Test that AFO is in silent civilization mode (孝 protection)"""
    assert antigravity.EXTERNAL_EXPOSURE_ENABLED is False
    assert antigravity.EXTERNAL_API_ENABLED is False
    assert antigravity.PUBLIC_ENDPOINTS_ENABLED is False
    assert antigravity.SILENT_CIVILIZATION_MODE is True


def test_afo_dry_run_default() -> None:
    """Test that DRY_RUN is enabled by default (善 protection)"""
    assert antigravity.DRY_RUN_DEFAULT is True


def test_afo_philosophy_weights() -> None:
    """Test Trinity Score weights are properly configured (眞善美孝永)"""
    weights = antigravity.trinity_weights
    assert weights["truth"] == 0.35
    assert weights["goodness"] == 0.35
    assert weights["beauty"] == 0.20
    assert weights["serenity"] == 0.08
    assert weights["eternity"] == 0.02
