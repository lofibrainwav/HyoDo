from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from AFO.api_wallet import APIWallet

# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""
Wallet Keys Router - API 키 CRUD 관리
"""


# Import APIWallet

# Create router - prefix will be handled by main wallet router
keys_router = APIRouter(prefix="", tags=["Wallet Keys"])


# Models
class KeyResponse(BaseModel):
    name: str
    service: str
    key_type: str
    read_only: bool
    created_at: str | None = None
    access_count: int = 0
    # Security: Never return the actual key


class AddKeyRequest(BaseModel):
    name: str
    key: str
    service: str = "unknown"
    description: str = ""


@keys_router.get("/keys", response_model=list[KeyResponse])
async def list_keys() -> list[KeyResponse]:
    """List all stored API keys (metadata only)"""
    try:
        wallet = APIWallet()

        # Force reload to ensure fresh data
        if hasattr(wallet, "_load_storage"):
            # This is internal but useful given our script context
            pass

        keys = wallet.list_keys()

        return [
            KeyResponse(
                name=k["name"],
                service=k.get("service", "unknown"),
                key_type=k.get("key_type", "api"),
                read_only=k.get("read_only", False),
                created_at=k.get("created_at"),
                access_count=k.get("access_count", 0),
            )
            for k in keys
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@keys_router.post("/keys")
async def add_key(request: AddKeyRequest) -> dict[str, Any]:
    """Add a new API key"""
    try:
        wallet = APIWallet()

        # Check if exists
        if wallet.get(request.name):
            raise HTTPException(status_code=400, detail=f"Key '{request.name}' already exists")

        key_id = wallet.add(
            name=request.name,
            api_key=request.key,
            service=request.service,
            description=request.description,
        )

        return {
            "status": "success",
            "id": key_id,
            "message": f"Key '{request.name}' added successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add key: {e}") from e


@keys_router.delete("/keys/{name}")
async def delete_key(name: str) -> dict[str, Any]:
    """Delete an API key"""
    try:
        wallet = APIWallet()

        success = wallet.delete(name)

        if not success:
            raise HTTPException(status_code=404, detail=f"Key '{name}' not found")

        return {"status": "success", "message": f"Key '{name}' deleted"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete key: {e}") from e
