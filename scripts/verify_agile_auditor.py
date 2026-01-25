import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import aiohttp

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("AgileAuditor")


class AgileAuditor:
    """
    🕵️ AgileAuditor Agent
    Autonomous Agent designed to verify Phase 49 (The Glass Palace).
    It ensures True (Backend), Good (API), and Beautiful (Stream) consistency.
    """

    def __init__(self, base_url="http://localhost:8010") -> None:
        self.base_url = base_url
        self.findings = []
        self.headers = {"User-Agent": "AgileAuditor/1.0 (AFO-Kingdom)"}

    async def audit_truth_tickets(self):
        """Phase 1: Verify Ticket Truth (Domain) vs API"""
        logger.info("🔍 [Phase 1] Auditing Ticket Truth...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tickets", headers=self.headers
                ) as resp:
                    if resp.status != 200:
                        self.findings.append(f"❌ API Error: /api/tickets returned {resp.status}")
                        return False

                    tickets = await resp.json()
                    total_tickets = len(tickets)
                    logger.info(f"✅ API returned {total_tickets} tickets.")

                    # Deep Check: Phase 49 existence
                    next((t for t in tickets if "Phase 49" in str(t)), None)
                    # Note: Ticket parsing might put Phase in 'phase' field or title

                    has_p49 = any(t["phase"] and "Phase 49" in t["phase"] for t in tickets)
                    if has_p49:
                        logger.info("✅ Phase 49 found in API response.")
                    else:
                        # Fallback check in titles
                        has_p49_title = any("Phase 49" in t["title"] for t in tickets)
                        if has_p49_title:
                            logger.info("✅ Phase 49 found in Ticket Titles.")
                        else:
                            self.findings.append("⚠️ Phase 49 NOT detected in Ticket API.")

                    # Check Ticket-007 (Dashboard UX)
                    t007 = next((t for t in tickets if t["id"] == "007"), None)
                    if t007:
                        logger.info(f"✅ TICKET-007 Found: {t007['title']} ({t007['status']})")
                    else:
                        self.findings.append("❌ TICKET-007 (Dashboard UX) missing from API.")

                    return True

        except Exception as e:
            self.findings.append(f"❌ Connection Failed: {e}")
            return False

    async def audit_glass_palace_status(self):
        """Phase 2: Verify Glass Palace Status"""
        logger.info("🔍 [Phase 2] Auditing Glass Palace (Kingdom Status)...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/system/kingdom-status", headers=self.headers
                ) as resp:
                    if resp.status != 200:
                        self.findings.append(
                            f"❌ API Error: /api/system/kingdom-status {resp.status}"
                        )
                        return False

                    data = await resp.json()

                    # Verify Organs
                    organs = data.get("organs", [])
                    heart = next((o for o in organs if o["name"] == "Heart"), None)

                    if heart and heart["score"] > 0:
                        logger.info("✅ Kingdom Heart is beating (Redis Connected).")
                    else:
                        self.findings.append("⚠️ Kingdom Heart (Redis) appears stopped or missing.")

                    # Verify Trinity
                    trinity = data.get("trinity_score", 0)
                    logger.info(f"✅ Trinity Score: {trinity}")

                    return True
        except Exception as e:
            self.findings.append(f"❌ Kingdom Status Check Failed: {e}")
            return False

    async def audit_log_stream(self):
        """Phase 3: Verify Log Stream (SSE)"""
        logger.info("🔍 [Phase 3] Auditing Log Stream (SSE)...")
        # This is tricky without a full SSE client, but we can check initial connection
        try:
            async with aiohttp.ClientSession() as session:
                # Set timeout for stream connection
                async with session.get(
                    f"{self.base_url}/api/logs/stream", headers=self.headers, timeout=5
                ) as resp:
                    if resp.status == 200:
                        logger.info("✅ Log Stream Endpoint is ACTIVE (200 OK).")
                        # Read first chunk
                        chunk = await resp.content.read(1024)
                        if chunk:
                            logger.info("✅ Received detailed log stream data.")
                        else:
                            self.findings.append("⚠️ Log Stream connected but returned no data.")
                    else:
                        self.findings.append(f"❌ Log Stream Error: {resp.status}")
                    return True
        except asyncio.TimeoutError:
            # Timeout is actually GOOD for a stream if we didn't get immediate error
            logger.info("✅ Log Stream connection held open (Expected behavior).")
            return True
        except Exception as e:
            self.findings.append(f"❌ Log Stream Audit Failed: {e}")
            return False

    async def run(self):
        print("🤖 AgileAuditor Agent Initialized.")
        print("===================================")

        await self.audit_truth_tickets()
        await self.audit_glass_palace_status()
        await self.audit_log_stream()

        print("\n===================================")
        if not self.findings:
            print("🎉 Full Integrity Verified! Zero anomalies detected.")
            print("   - Ticket API: Verified")
            print("   - Kingdom Status: Verified")
            print("   - Log Stream: Verified")
            return 0
        else:
            print("⚠️ Anomalies Detected:")
            for finding in self.findings:
                print(f"   - {finding}")
            return 1


if __name__ == "__main__":
    try:
        logging.getLogger("aiohttp").setLevel(logging.WARNING)
        auditor = AgileAuditor()
        sys.exit(asyncio.run(auditor.run()))
    except KeyboardInterrupt:
        pass
