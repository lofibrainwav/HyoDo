# Trinity Score: 90.0 (Established by Chancellor)
"""Cache Metrics Router
Phase 6B: Expose cache performance metrics to the dashboard
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from AFO.cache import get_cache_metrics
from AFO.utils.standard_shield import shield

router = APIRouter(prefix="/api/cache", tags=["Cache Metrics"])


@shield(pillar="善")
@router.get("/metrics", response_model=dict[str, Any])
async def get_metrics():
    """Get current cache performance metrics"""
    try:
        metrics = get_cache_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
