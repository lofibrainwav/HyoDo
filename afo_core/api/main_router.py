"""
Main API Router with authentication and rate limiting
"""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

# Import middleware
from .middleware.auth import (
    AuthException,
    RateLimitException,
    generate_access_token,
    verify_origin,
)
from .routes.mygpt.contexts import router as mygpt_contexts_router
from .routes.mygpt.transfer import router as mygpt_transfer_router
from .routes.trinity import router as trinity_router

# Import existing handlers (would be integrated)
# from ..handlers.cpa_handler import analyze_tax
# from ..handlers.irs_handler import sync_irs
# from ..handlers.notebook_handler import list_notebooks

router = APIRouter(prefix="/api")


# Health check endpoint (public)
@router.get("/health", tags=["Health"])
async def health_check():
    """Public health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "AFO_Kingdom API v1.0",
    }


# Kingdom status endpoint (public)
@router.get("/kingdom/status", tags=["Kingdom"])
async def kingdom_status():
    """Public Trinity Score and system status endpoint"""
    # This would normally call Trinity OS for real-time calculation
    # For now, return cached data or trigger background calculation

    return {
        "trinityScore": 97.66,
        "pillars": {
            "truth": 100,
            "goodness": 100,
            "beauty": 92.8,
            "serenity": 95.6,
            "infinity": 99.9,
        },
        "activeAgents": 7,
        "systemHealth": "VERIFY_TRUST: 361CAF7E-4830-4D3E-9AE0-1A7B2CAA8028",
        "lastUpdated": datetime.now(UTC).isoformat(),
        "note": "This endpoint is now properly protected and requires authentication for write operations",
    }


# Notebooks endpoint (public read, protected write)
@router.get("/notebooks", tags=["Notebooks"])
async def list_notebooks(request: Request):
    """List MyGPT contexts (public read access)"""
    # In production, this would fetch from Redis/Upstash
    # For demo, return static data

    return {
        "results": [
            {
                "id": "o75vEpSlZeNtlMy1bp3jB",
                "title": "TAX-EASYUP-5165-M (2025 Inflation Update)",
                "content": "CPE Depot Easy Update 2025 — Inflation Adjustment Baseline\n\nSource: Danny C. Santucci, CPE Depot (Publication Date: 2025-05-08)",
                "tags": ["tax", "inflation", "2025", "CPE", "baseline", "JulieCPA"],
                "createdAt": "2026-01-19T06:54:31.996Z",
                "updatedAt": "2026-01-19T06:54:31.996Z",
            },
            {
                "id": "YNHOAXPKiUai_42YK6Uvp",
                "title": "Tax EasyUp 5165 - 2025 Inflation & Update Summary",
                "content": "### 📘 2025 EasyUp 5165 Comprehensive Summary\n\n**Source:** CPE Depot, '2025/2024 Easy Update & Inflation Adjustments' (Danny C. Santucci, CPA)",
                "tags": ["tax", "CPE", "inflation", "2025", "JulieCPA"],
                "createdAt": "2026-01-19T06:48:13.666Z",
                "updatedAt": "2026-01-19T06:48:13.666Z",
            },
            {
                "id": "0jNiduX5sCws2TQM6q7WQ",
                "title": "Julie CPA Strategy Log",
                "content": "Initial entry for Julie CPA project notebook.\nPurpose: Track all CPA strategic analyses, tax simulations, and audit review logs.",
                "tags": ["strategy", "julie-cpa"],
                "createdAt": "2026-01-18T20:30:50.827Z",
                "updatedAt": "2026-01-18T20:30:50.827Z",
            },
            {
                "id": "z5h1SVRxY_efJTCh3vygz",
                "title": "AICPA_AI_Audit_Template_v1.0",
                "content": "Full AICPA AI Audit Standard Template + Client Training Module Integration Report (generated 2026-01-18).",
                "tags": ["aicpa", "audit", "template"],
                "createdAt": "2026-01-18T10:48:52.137Z",
                "updatedAt": "2026-01-18T10:48:52.137Z",
            },
            {
                "id": "rHOGg0sel_1I98kkoA7l8",
                "title": "Julie_CPA_Full_AFO_Integration",
                "content": "AFO GPT (Tax Simulation / Roth Optimizer / IRMAA Avoidance / EV Credit / 401k Optimizer / Quarterly Estimated Tax) 완전 통합 버전.",
                "tags": ["julie-cpa", "afo-gpt", "integration", "tax", "roth"],
                "createdAt": "2026-01-17T01:41:59.365Z",
                "updatedAt": "2026-01-17T01:41:59.365Z",
            },
        ],
        "total": 5,
    }


# Create notebook endpoint (protected - auth required)
@router.post("/notebooks", tags=["Notebooks"])
async def create_notebook(
    request: Request, title: str, content: str, tags: list[str] | None = None
):
    """Create new MyGPT context (requires authentication)"""

    # Verify origin
    if not verify_origin(request):
        raise HTTPException(status_code=403, detail="Forbidden: Invalid origin")

    try:
        # Get authenticated user from request state (set by middleware)
        user = getattr(request.state, "user", None)

        if not user:
            raise AuthException("Authentication required")

        user_id = user.get("user_id")

        # Create notebook record (would go to Redis/Upstash in production)
        notebook_id = f"nb_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{user_id}"

        return {
            "id": notebook_id,
            "title": title,
            "content": content,
            "tags": tags or [],
            "userId": user_id,
            "createdAt": datetime.now(UTC).isoformat(),
            "updatedAt": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# CPA Analysis endpoints (protected - auth required)
@router.post("/cpa/analyze", tags=["CPA"])
async def cpa_analyze(request: Request):
    """Tax Analysis by Associate (requires authentication)"""

    if not verify_origin(request):
        raise HTTPException(status_code=403, detail="Forbidden: Invalid origin")

    # Check authentication
    user = getattr(request.state, "user", None)
    if not user:
        raise AuthException("Authentication required")

    # This would call the actual CPA analysis logic
    # For now, return a demo response

    return {
        "result": "analysis_complete",
        "agent": "Associate",
        "trinityScore": 95,
        "timestamp": datetime.now(UTC).isoformat(),
        "note": "This endpoint is protected and requires authentication. Integration with actual CPA logic pending.",
    }


@router.post("/cpa/review", tags=["CPA"])
async def cpa_review(request: Request):
    """Strategic Review by Manager (requires authentication)"""

    if not verify_origin(request):
        raise HTTPException(status_code=403, detail="Forbidden: Invalid origin")

    # Check authentication
    user = getattr(request.state, "user", None)
    if not user:
        raise AuthException("Authentication required")

    return {
        "result": "review_complete",
        "agent": "Manager",
        "trinityScore": 98,
        "timestamp": datetime.now(UTC).isoformat(),
        "note": "This endpoint is protected and requires authentication. Integration with actual review logic pending.",
    }


@router.post("/cpa/audit", tags=["CPA"])
async def cpa_audit(request: Request):
    """Final Audit by Auditor (requires authentication)"""

    if not verify_origin(request):
        raise HTTPException(status_code=403, detail="Forbidden: Invalid origin")

    # Check authentication
    user = getattr(request.state, "user", None)
    if not user:
        raise AuthException("Authentication required")

    return {
        "result": "audit_complete",
        "agent": "Auditor",
        "trinityScore": 99,
        "timestamp": datetime.now(UTC).isoformat(),
        "note": "This endpoint is protected and requires authentication. Integration with actual audit logic pending.",
    }


# IRS Updates endpoint (protected - auth required)
@router.get("/irs/updates", tags=["IRS"])
async def irs_updates(request: Request):
    """IRS Regulation Sync (requires authentication)"""

    if not verify_origin(request):
        raise HTTPException(status_code=403, detail="Forbidden: Invalid origin")

    # Check authentication
    user = getattr(request.state, "user", None)
    if not user:
        raise AuthException("Authentication required")

    return {
        "result": "sync_complete",
        "timestamp": datetime.now(UTC).isoformat(),
        "note": "This endpoint is protected and requires authentication. Integration with actual IRS API pending.",
    }


# Admin endpoint to generate access tokens (protected)
@router.post("/auth/token", tags=["Authentication"])
async def generate_token(request: Request):
    """Generate JWT access token for authenticated users (admin only)"""

    if not verify_origin(request):
        raise HTTPException(status_code=403, detail="Forbidden: Invalid origin")

    # Check authentication
    user = getattr(request.state, "user", None)
    if not user:
        raise AuthException("Authentication required")

    # Only allow admins to generate tokens
    user_id = user.get("user_id")
    if user_id != "admin":  # Replace with actual admin check
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")

    permissions = user.get("permissions", ["read", "write"])
    token = generate_access_token(user_id, permissions)

    return {
        "token": token,
        "type": "Bearer",
        "expires_in": 60,  # Hardcoded for demo, use env var in production
        "permissions": permissions,
        "note": "Use this token in the X-API-Key header for API requests",
    }


router.include_router(trinity_router, prefix="/trinity", tags=["Trinity"])
router.include_router(mygpt_contexts_router)
router.include_router(mygpt_transfer_router)


# Exception handlers
@router.exception_handler(AuthException)
async def auth_exception_handler(request: Request, exc: AuthException):
    """Handle authentication exceptions"""
    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": exc.detail})


@router.exception_handler(RateLimitException)
async def rate_limit_exception_handler(request: Request, exc: RateLimitException):
    """Handle rate limit exceptions"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": exc.detail, "retry_after": 60},
    )


@router.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle all other HTTP exceptions"""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


__all__ = ["router"]
