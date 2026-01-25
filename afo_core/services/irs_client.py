"""
IRS A2A Client (Application-to-Application)
Handles secure communication with the IRS API for Transcripts and E-Filing.
Supports 'Simulation Mode' when Certificate is missing.
"""

import asyncio
import logging
import os
import ssl
from typing import Any

import httpx

from AFO.services.irs_mock_data import MOCK_STATUS_RESPONSE, MOCK_TRANSCRIPT_2024
from AFO.utils.resilience import retry_with_backoff

logger = logging.getLogger(__name__)

# IRS OAuth2 Configuration (Phase 79 - TODO-001)
IRS_TOKEN_URL = os.getenv("IRS_TOKEN_URL", "https://api.irs.gov/oauth2/token")
IRS_CLIENT_SECRET = os.getenv("IRS_CLIENT_SECRET")


class IRSClient:
    def __init__(self) -> None:
        self.cert_path = os.getenv("IRS_CERT_PATH")
        self.client_id = os.getenv("IRS_CLIENT_ID")
        self.base_url = "https://api.irs.gov/a2a/v1"
        self.access_token = None
        self.ssl_context = None

        # Simulation Mode Detection
        # Cert path must exist for Real Mode
        self.simulation_mode = not (self.cert_path and os.path.exists(self.cert_path))

        if self.simulation_mode:
            logger.warning("⚠️ IRS Client running in SIMULATION MODE (No Certificate found)")
        else:
            self._load_ssl_context()

    def _load_ssl_context(self) -> None:
        """Loads the SSL context with the client certificate."""
        try:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.ssl_context.load_cert_chain(certfile=self.cert_path)  # type: ignore
            logger.info(f"✅ Loaded IRS Client Certificate from {self.cert_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load IRS Certificate: {e}")
            self.simulation_mode = True  # Fallback to simulation

    @retry_with_backoff(retries=3, initial_delay=2.0, backoff_factor=1.5)
    async def connect(self) -> bool:
        """Authenticates with IRS via Mutual TLS (OAuth2 Client flow)."""
        logger.info("Connecting to IRS A2A Gateway...")

        if self.simulation_mode:
            # Simulate Auth Delay
            await asyncio.sleep(1)
            self.access_token = "mock-access-token-777"  # noqa: S105 (mock password for testing)
            logger.info("✅ Authenticated (Simulated)")
            return True

        try:
            # Phase 79 - TODO-001: Full OAuth2 Client Credentials flow with mTLS
            if not self.ssl_context or not self.client_id:
                logger.warning("🔐 Missing SSL context or client_id for OAuth2 flow")
                return False

            # Prepare OAuth2 token request
            token_data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "scope": "transcript.read filing.status",
            }

            # Add client secret if available (some flows use it)
            if IRS_CLIENT_SECRET:
                token_data["client_secret"] = IRS_CLIENT_SECRET

            # Create httpx client with mTLS certificate
            async with httpx.AsyncClient(
                cert=self.cert_path,
                verify=True,
                timeout=30.0,
            ) as client:
                logger.info(f"🔐 Requesting OAuth2 token from {IRS_TOKEN_URL}")

                response = await client.post(
                    IRS_TOKEN_URL,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code == 200:
                    token_response = response.json()
                    self.access_token = token_response.get("access_token")
                    expires_in = token_response.get("expires_in", 3600)
                    logger.info(f"✅ OAuth2 authenticated (expires in {expires_in}s)")
                    return True
                else:
                    logger.error(f"❌ OAuth2 failed: {response.status_code} - {response.text}")
                    return False

        except httpx.ConnectError as e:
            logger.error(f"Connection error to IRS: {e}")
            return False
        except Exception as e:
            logger.error(f"OAuth2 flow failed: {e}")
            return False

    async def get_transcript(self, year: int, transcript_type: str = "return") -> dict[str, Any]:
        """Fetches a tax transcript."""
        if not self.access_token and not await self.connect():
            return {"error": "Authentication Failed"}

        logger.info(f"Fetching {transcript_type} transcript for {year}...")

        if self.simulation_mode:
            await asyncio.sleep(1.5)  # Network latency
            if year == 2024:
                return MOCK_TRANSCRIPT_2024
            return {"error": "No mock data for this year"}

        # Real Request Placeholder
        return {"error": "Real API call not fully implemented (OAuth Pending)"}

    async def check_filing_status(self, submission_id: str) -> dict[str, Any]:
        """Checks the status of an e-filed return."""
        if not self.access_token and not await self.connect():
            return {"error": "Authentication Failed"}

        logger.info(f"Checking status for {submission_id}...")

        if self.simulation_mode:
            await asyncio.sleep(0.5)
            # Make it dynamic for fun
            resp = MOCK_STATUS_RESPONSE.copy()
            resp["submissionId"] = submission_id
            return resp

        return {"error": "Real API call not implemented"}


irs_client = IRSClient()
