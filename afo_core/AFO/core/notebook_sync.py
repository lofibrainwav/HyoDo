"""
Audit Trail to NotebookLM Sync Service (Phase 59 - TICKET-090)
Automatically syncs Julie Portal audit events to NotebookLM Bridge.
"""

import asyncio
import logging
import os
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

NOTEBOOK_BRIDGE_URL = "https://jangjungwha.com/api"
NOTEBOOK_BRIDGE_API_KEY = os.getenv("NOTEBOOK_BRIDGE_API_KEY", "")

# Cache for the audit notebook ID
_audit_notebook_id: str | None = None


async def get_or_create_audit_notebook() -> str:
    """Get existing audit notebook or create one."""
    global _audit_notebook_id

    if _audit_notebook_id:
        return _audit_notebook_id

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Search for existing audit notebook
        headers = {"x-api-key": NOTEBOOK_BRIDGE_API_KEY}
        res = await client.get(
            f"{NOTEBOOK_BRIDGE_URL}/notebooks",
            params={"q": "Julie CPA Audit Trail", "limit": 1},
            headers=headers,
        )

        if res.status_code == 200:
            data = res.json()
            if data.get("results") and len(data["results"]) > 0:
                _audit_notebook_id = data["results"][0]["id"]
                logger.info(f"Found existing audit notebook: {_audit_notebook_id}")
                return _audit_notebook_id

        # Create new audit notebook
        notebook_data = {
            "title": "Julie CPA Audit Trail",
            "content": f"# Julie CPA Audit Trail\n\nAutomated audit log sync from Julie CPA Portal.\nCreated: {datetime.now().isoformat()}\n\n---\n\n",
            "tags": ["JulieCPA", "AuditTrail", "Automated"],
        }

        res = await client.post(
            f"{NOTEBOOK_BRIDGE_URL}/notebooks", json=notebook_data, headers=headers
        )

        if res.status_code == 201:
            data = res.json()
            _audit_notebook_id = data["id"]
            logger.info(f"Created new audit notebook: {_audit_notebook_id}")
            return _audit_notebook_id
        else:
            raise Exception(f"Failed to create notebook: {res.status_code}")


async def sync_audit_event(event_message: str) -> bool:
    """Append an audit event to the NotebookLM audit notebook."""
    try:
        notebook_id = await get_or_create_audit_notebook()

        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"x-api-key": NOTEBOOK_BRIDGE_API_KEY}

            # Format the event with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            append_text = f"[{timestamp}] {event_message}"

            res = await client.post(
                f"{NOTEBOOK_BRIDGE_URL}/notebooks/{notebook_id}/append",
                json={"appendText": append_text, "delimiter": "\n"},
                headers=headers,
            )

            if res.status_code == 200:
                logger.info(f"Synced audit event to NotebookLM: {event_message[:50]}...")
                return True
            else:
                logger.warning(f"Failed to sync: {res.status_code}")
                return False

    except Exception as e:
        logger.error(f"Audit sync error: {e}")
        return False


async def sync_batch_events(events: list[str]) -> int:
    """Sync multiple audit events at once."""
    success_count = 0
    for event in events:
        if await sync_audit_event(event):
            success_count += 1
        await asyncio.sleep(0.1)  # Rate limiting
    return success_count


# Convenience function for synchronous code
def sync_event_sync(event_message: str) -> bool:
    """Synchronous wrapper for sync_audit_event."""
    try:
        return asyncio.get_event_loop().run_until_complete(sync_audit_event(event_message))
    except RuntimeError:
        # No event loop, create new one
        return asyncio.run(sync_audit_event(event_message))
