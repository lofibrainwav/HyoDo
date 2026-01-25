# Trinity Score: 90.0 (Established by Chancellor)
"""Heal Router - System Recovery Operations
眞 (Truth): Validates recovery commands
善 (Goodness): Safe execution of system repairs
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class HealResponse(BaseModel):
    success: bool
    message: str
    action: str


@router.post("/heal", response_model=HealResponse)
async def heal_kingdom() -> HealResponse:
    """Triggers system recovery protocols.
    Currently attempts to restart core Docker services.
    """
    logger.info("🚑 Heal Protocol Initiated by Commander")

    try:
        # Command to restart redis and postgres
        # Note: This assumes the backend has permissions to run docker commands
        # In a real production env, this might be handled by an orchestrator or specialized agent
        cmd = "docker-compose up -d redis postgres"

        process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        _stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info("✅ Heal Protocol Successful: Services Restarted")
            return HealResponse(
                success=True,
                message="Core services restart initiated successfully.",
                action="docker_restart",
            )
        else:
            error_msg = stderr.decode().strip()
            logger.error(f"❌ Heal Protocol Failed: {error_msg}")
            # Try alternative command for macOS Docker Desktop
            if "docker daemon" in error_msg.lower():
                return HealResponse(
                    success=False,
                    message="Docker Daemon is down. Please start Docker Desktop manually.",
                    action="manual_intervention_required",
                )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Recovery failed: {error_msg}",
            )

    except Exception as e:
        logger.error(f"❌ Heal Protocol Critical Error: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Critical system failure during heal: {e!s}",
        ) from e
