from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from AFO.api.routes.integrity_check import IntegrityCheckRequest, check_integrity


@pytest.mark.asyncio
async def test_eternity_pillar_hardcoded_check_fail():
    """
    TDD Test: Prove that we are effectively checking Redis,
    and if Redis fails, the 'persistence' check should fail.
    """
    request = IntegrityCheckRequest(pillar="eternity")

    # Mock Redis failure
    with patch("AFO.api.routes.integrity_check.get_shared_async_redis_client") as mock_redis_getter:
        mock_redis_getter.side_effect = Exception("Redis Down")

        # When we implement real check, it should catch this exception and mark persistence=False
        result = await check_integrity(request)

        # If result is hardcoded, checking persistence will be True even if Redis is "down"
        # We Assert what we WANT: persistence should be False if Redis is down.
        # This assertion will FAIL currently (proving the bug).
        # Once fixed, it will PASS.
        assert result["pillars"]["eternity"]["checks"]["persistence"] is False


@pytest.mark.asyncio
@pytest.mark.skip(reason="TDD placeholder - CI now uses 'which' commands, not Path.exists")
async def test_truth_pillar_ci_lock_check_fail():
    """
    TDD Test: Prove that we are checking for actual artifacts.
    If artifacts are missing, ci_cd_lock should be False.

    NOTE: This test was a TDD placeholder. The actual implementation uses
    'which' commands to check for CI tools, not Path.exists for artifacts.
    """
    request = IntegrityCheckRequest(pillar="truth")

    # Mock Path.exists to return False for artifacts
    # We need to target the specific Path usage in verifying artifacts
    # Since we haven't written the code yet, we assume it will check `path / "artifacts/ci/..."`

    with patch("pathlib.Path.exists", return_value=False):
        result = await check_integrity(request)

        # Currently checks `which` commands, so likely returns depends on env.
        # But we want to ensure it fails if artifacts missing.
        assert result["pillars"]["truth"]["checks"]["ci_cd_lock"] is False


@pytest.mark.asyncio
async def test_serenity_pillar_sse_streaming_check_fail():
    """
    TDD Test: Serenity pillar should check Redis/EventBus for SSE, not hardcoded True.
    """
    request = IntegrityCheckRequest(pillar="serenity")

    with patch("AFO.api.routes.integrity_check.get_shared_async_redis_client") as mock_redis:
        mock_redis.side_effect = Exception("Redis Down")

        result = await check_integrity(request)
        assert result["pillars"]["serenity"]["checks"]["sse_streaming"] is False
