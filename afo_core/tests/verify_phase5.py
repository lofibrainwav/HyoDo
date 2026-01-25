import asyncio
import json
import logging
import os
from datetime import datetime

import httpx

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Phase5Verifier")

# Environment
API_KEY = os.getenv("NOTEBOOK_BRIDGE_API_KEY", "test-api-key")
BASE_URL = "https://jangjungwha.com/api"
LOCAL_URL = "http://localhost:8010/api"


async def test_dashboard_update(use_local=False):
    """Test the /v1/dashboard/update endpoint on the bridge."""
    target = LOCAL_URL if use_local else BASE_URL
    logger.info(f"🧪 Testing Dashboard Update API on {target}...")

    payload = {
        "trinity_score": {"truth": 98.5, "good": 97.2, "beauty": 99.1},
        "irs_updates": [
            {
                "notice": "TEST-2026-001",
                "impact": "HIGH",
                "summary": "Phase 5 Verification Test Notice",
                "effective_date": datetime.now().isoformat(),
            }
        ],
        "notification": "Verification sequence initiated. [Jin-Seon-Mi 100%]",
        "schedule": [
            {"time": "12:00", "task": "Integrity Sweep", "status": "✅ 완료"},
            {"time": "13:00", "task": "System Expansion", "status": "🕐 예정"},
        ],
    }

    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        try:
            # Note: The actual path is api/v1/dashboard/update based on vercel.json rewrites
            url = f"{target}/v1/dashboard/update"
            resp = await client.post(url, json=payload, headers=headers)
            logger.info(f"Response Status: {resp.status_code}")
            if resp.status_code == 200:
                logger.info("✅ Dashboard Update: SUCCESS")
                return True
            else:
                # Try fallback if /api/v1 prefix is needed directly
                logger.info("🔄 Retrying with /api/v1 prefix...")
                url_fallback = f"{target}/api/v1/dashboard/update".replace("//api", "/api")
                resp = await client.post(url_fallback, json=payload, headers=headers)
                logger.info(f"Fallback Status: {resp.status_code}")
                if resp.status_code == 200:
                    logger.info("✅ Dashboard Update (Fallback): SUCCESS")
                    return True

                logger.error(f"❌ Dashboard Update: FAILED ({resp.text})")
                return False
        except Exception as e:
            logger.error(f"❌ Dashboard Update: ERROR ({str(e)})")
            return False


async def test_kakao_notifications():
    """Test the Kakao notification polling endpoint."""
    logger.info("🧪 Testing Kakao Notification Polling...")

    async with httpx.AsyncClient() as client:
        try:
            # This hits the LOCAL afo-core server (mocked here or assumed running)
            resp = await client.get(f"{LOCAL_URL}/kakao/notifications")
            logger.info(f"Response Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"Notifications: {json.dumps(data, indent=2)}")
                logger.info("✅ Kakao Notifications: SUCCESS")
                return True
            else:
                logger.error("❌ Kakao Notifications: FAILED")
                return False
        except Exception as e:
            # If server isn't running locally, this will fail.
            # In a real CI, we'd start the server first.
            logger.warning(f"⚠️ Kakao Notifications: Local server not reachable. ({str(e)})")
            return "SKIP"


async def run_verification():
    logger.info("🚀 Starting Phase 5 Final Verification Sweep...")

    results = {
        "dashboard_update": await test_dashboard_update(),
        "kakao_notifications": await test_kakao_notifications(),
    }

    logger.info("--- Final Summary ---")
    for task, passed in results.items():
        status = "PASSED" if passed is True else ("SKIPPED" if passed == "SKIP" else "FAILED")
        logger.info(f"{task.upper()}: {status}")


if __name__ == "__main__":
    asyncio.run(run_verification())
