# Trinity Score: 90.0 (Established by Chancellor)
from unittest.mock import AsyncMock, patch

import pytest

# We need to test the lifespan context manager in api_server.py
# The lifespan function depends on global variables in api_server.py
# that are imported at module level.
# To test the "Component Not Available" branches, we need to ensure those globals are None.


@pytest.mark.asyncio
@pytest.mark.integration
async def test_lifespan_manager_calls_init_cleanup():
    """Test that lifespan manager calls initialize and cleanup systems."""
    from fastapi import FastAPI

    from AFO.api.config import get_lifespan_manager

    app = FastAPI()

    # We patch import inside the function to avoid strict dependency issues if modules are missing
    # But since we are testing flow, we just patch the imported functions in AFO.api.config

    # We need to patch where they are USED in AFO.api.config
    # The functions are imported at module level, so we must patch the config module's reference

    with patch("AFO.api.config.initialize_system", new_callable=AsyncMock) as mock_init:
        with patch("AFO.api.config.cleanup_system", new_callable=AsyncMock) as mock_cleanup:
            async with get_lifespan_manager(app):
                mock_init.assert_awaited_once()
                mock_cleanup.assert_not_awaited()

            mock_cleanup.assert_awaited_once()
