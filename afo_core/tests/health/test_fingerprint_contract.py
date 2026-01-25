# Trinity Score: 90.0 (Established by Chancellor)
"""
Fingerprint Contract Tests for AFO Kingdom API.

Ensures critical API endpoints always return expected schema fields,
preventing "Ghost Code" and maintaining Eternity (永).
"""

import os
import sys

import pytest

# Add AFO to path for direct module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


@pytest.mark.asyncio
async def test_health_response_contains_fingerprint():
    """
    Contract Test: Ensure the health report always exposes a BUILD_VERSION fingerprint.
    This prevents 'Ghost Code' by ensuring we can always identify the running code version.
    """
    from AFO.services.health_service import get_comprehensive_health

    health = await get_comprehensive_health()

    # build_version must exist and not be null in the comprehensive report
    assert "build_version" in health, "build_version missing from health report"
    print(f"Detected Build Fingerprint: {health.get('build_version')}")


@pytest.mark.asyncio
async def test_health_response_contains_trinity_score():
    """
    Contract Test: Ensure the health report always includes the Trinity score breakdown.
    """
    from AFO.services.health_service import get_comprehensive_health

    health = await get_comprehensive_health()

    # Trinity fields must exist
    assert "trinity" in health, "trinity object missing from health report"
    trinity = health["trinity"]

    # Each pillar must have a score
    for pillar in ["truth", "goodness", "beauty", "filial_serenity", "eternity"]:
        assert pillar in trinity, f"Pillar '{pillar}' missing from trinity breakdown"

    # Trinity score must be a valid percentage
    assert "trinity_score" in trinity, "trinity_score missing from trinity breakdown"
    assert 0 <= trinity["trinity_score"] <= 1, f"Invalid trinity_score: {trinity['trinity_score']}"

    print(f"Trinity Score: {trinity['trinity_score']}")


@pytest.mark.asyncio
async def test_health_response_contains_organs_v2():
    """
    Contract Test: Ensure the health report uses the v2 organs schema with 11 expected organs.
    """
    from AFO.services.health_service import get_comprehensive_health

    health = await get_comprehensive_health()

    # organs_v2 must exist
    assert "organs_v2" in health, "organs_v2 object missing from health report"
    organs = health["organs_v2"]

    # Check for expected organ count (11 as per contract)
    assert len(organs) == 11, f"Expected 11 organs in v2, got {len(organs)}"

    # Each organ must have required fields
    for organ_name, organ_data in organs.items():
        assert "status" in organ_data, f"Organ '{organ_name}' missing 'status'"
        assert "score" in organ_data, f"Organ '{organ_name}' missing 'score'"

    print(f"Organs V2 verified: {list(organs.keys())}")


@pytest.mark.asyncio
async def test_health_response_decision_field():
    """
    Contract Test: Ensure the health report always includes a decision (AUTO_RUN or ASK).
    """
    from AFO.services.health_service import get_comprehensive_health

    health = await get_comprehensive_health()

    # decision field must exist
    assert "decision" in health, "decision field missing from health report"
    assert health["decision"] in [
        "AUTO_RUN",
        "ASK_COMMANDER",
        "TRY_AGAIN",
    ], f"Invalid decision: {health['decision']}"

    print(f"Decision: {health['decision']}")
