import pytest

from AFO.domain.metrics.trinity import calculate_trinity
from AFO.domain.metrics.trinity_ssot import (
    WEIGHT_BEAUTY,
    WEIGHT_ETERNITY,
    WEIGHT_GOODNESS,
    WEIGHT_SERENITY,
    WEIGHT_TRUTH,
)


def test_trinity_weight_sum() -> None:
    """Ensure the sum of all weights is exactly 1.0"""
    total = WEIGHT_TRUTH + WEIGHT_GOODNESS + WEIGHT_BEAUTY + WEIGHT_SERENITY + WEIGHT_ETERNITY
    assert abs(total - 1.0) < 1e-9


def test_trinity_calculation_logic() -> None:
    """Ensure calculation uses the unified weights"""
    metrics = calculate_trinity(
        truth=1.0, goodness=1.0, beauty=1.0, filial_serenity=1.0, eternity=1.0
    )
    assert metrics.truth == 1.0
    assert metrics.trinity_score == pytest.approx(1.0)


def test_anatomy_mapping_in_code() -> None:
    """Check if the mapping in comprehensive_health matches the standard"""
    pytest.importorskip("openai", reason="openai package required for dspy import chain")
    from api.routes.comprehensive_health import _extract_services_status

    # Mock health data
    health_data = {
        "organs": {
            "心_Redis": {"status": "healthy"},
            "肝_PostgreSQL": {"status": "healthy"},
            "脾_Ollama": {"status": "healthy"},
            "肺_LanceDB": {"status": "healthy"},
            "腎_MCP": {"status": "healthy"},
            "腦_Soul_Engine": {"status": "healthy"},
        }
    }

    status = _extract_services_status(health_data)
    assert status["redis"] is True
    assert status["postgres"] is True
    assert status["ollama"] is True
    assert status["api_server"] is True
