# Trinity Score: 90.0 (Established by Chancellor)
import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from AFO.api_wallet import APIWallet
except ImportError:
    APIWallet = None  # type: ignore

router = APIRouter(prefix="/browser", tags=["Browser Bridge"])


class BrowserTokenRequest(BaseModel):
    service: str
    token: str
    email: str | None = None
    user_agent: str | None = None


@router.post("/save-token")
async def save_browser_token(request: BrowserTokenRequest) -> dict[str, Any]:
    """
    Save a browser session token to the API Wallet.
    """
    try:
        wallet = APIWallet()

        # Determine key name based on service and email/timestamp
        key_name = f"{request.service}_session_{os.urandom(2).hex()}"
        if request.email:
            clean_email = request.email.split("@")[0]
            key_name = f"{request.service}_{clean_email}"

        # Setup key type
        description = f"Imported via Browser Bridge from {request.user_agent or 'Web'}"

        # Check if exists and delete if so (overwrite logic for sessions)
        existing = wallet.get(key_name, decrypt=False)
        if existing:
            wallet.delete(key_name)

        # Add to wallet
        wallet.add(
            name=key_name,
            api_key=request.token,
            key_type="session_token",
            service=request.service,
            description=description,
            read_only=False,
        )

        return {
            "status": "success",
            "message": f"Session token for {request.service} saved securely.",
            "key_name": key_name,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/extraction-script")
async def get_extraction_script() -> dict[str, str]:
    """
    Returns the JS script for the user to run in their browser console.
    """
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "get_browser_token.js",
    )

    # Fallback if file setup is different in Docker
    if not os.path.exists(script_path):
        # Try relative to AFO root
        script_path = "/app/AFO/get_browser_token.js"

    try:
        if os.path.exists(script_path):
            with open(script_path) as f:
                return {"script": f.read()}
        else:
            # Fallback content if file missing
            return {
                "script": "console.log('Script not found on server. Please use manual entry.');"
            }
    except Exception as e:
        return {"script": f"// Error reading script: {e!s}"}
