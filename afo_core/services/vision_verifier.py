# Trinity Score: 90.0 (Established by Chancellor)
"""
Vision Verifier Service (The Eyes)
Phase 9: Self-Expanding Kingdom

Autonomous visual inspection of generated UI components.
"""

import logging
from pathlib import Path
from typing import Any

from AFO.config.settings import settings
from AFO.utils.playwright_bridge import bridge

logger = logging.getLogger("afo.services.vision_verifier")


class VisionVerifier:
    """
    Autonomous visual verification service.
    Uses Playwright to "see" the generated component.
    """

    def __init__(self) -> None:
        # Ultimate Resolution: 1080p (美: Beauty & clarity)
        self.viewport = {"width": 1920, "height": 1080}
        self.screenshot_dir = Path("packages/dashboard/public/artifacts/verification")

        if not self.screenshot_dir.exists():
            try:
                self.screenshot_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"⚠️ [Vision] Could not create screenshot dir: {e}")

    async def verify_ui(self, url: str, screenshot_path: str) -> dict[str, Any]:
        """
        [Ultimate Vision] Performs exhaustive visual inspection.
        """
        logger.info(f"👁️ [Vision] Verifying {url}...")

        try:
            # Using the bridge for implementation stability
            # We enforce the resolution via bridge if possible, or directly in bridge
            result = await bridge.verify_ui(
                url=url, screenshot_path=screenshot_path, enable_tracing=True
            )

            if result.get("status") == "PASS":
                logger.info(f"✅ [Vision] Captured 1080p snapshot: {screenshot_path}")
                return {
                    "success": True,
                    "screenshot_path": screenshot_path,
                    "details": result,
                    "resolution": "1920x1080",
                }
            else:
                logger.warning(f"⚠️ [Vision] Verification failed: {result}")
                return {
                    "success": False,
                    "error": "Visual anomalies detected",
                    "details": result,
                }

        except Exception as e:
            logger.error(f"❌ [Vision] Critical verification error: {e}")
            return {"success": False, "error": str(e)}

    async def verify_component(self, component_name: str) -> dict[str, Any]:
        """
        Visits the Sandbox Preview URL (convenience wrapper).
        """
        # Note: Sandbox routes are usually under /sandbox or /gen-ui/preview
        target_url = f"{settings.DASHBOARD_URL}/sandbox/{component_name}"
        filename = f"{component_name}_v2025.png"
        path = str(self.screenshot_dir / filename)

        return await self.verify_ui(target_url, path)


vision_verifier = VisionVerifier()
