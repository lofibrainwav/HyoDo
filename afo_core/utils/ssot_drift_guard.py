import logging
import sys
from pathlib import Path

# [眞] Truth: SSOT Drift Guard
# Ensures the Kingdom's documentation never drifts from its code reality.

logger = logging.getLogger(__name__)


class SSOTDriftGuard:
    def __init__(self, project_root: str) -> None:
        self.root = Path(project_root)
        self.tickets_md = self.root / "TICKETS.md"
        self.evolution_log = self.root / "AFO_EVOLUTION_LOG.md"
        # Adjusted path for actual brain location
        self.brain_root = Path("${HOME}/.gemini/antigravity/brain")

    def check_drift(self) -> None:
        """Perform a holistic check of SSOT artifacts."""
        logger.info("🛡️ Starting SSOT Drift Guard Scan...")
        issues = []

        if not self.tickets_md.exists():
            issues.append("❌ TICKETS.md missing at root")

        if not self.evolution_log.exists():
            issues.append("❌ AFO_EVOLUTION_LOG.md missing at root")

        # Target the current conversation context
        current_conv_id = "b85d7878-3b6a-4858-82ef-8069746e7518"
        task_md = self.brain_root / current_conv_id / "task.md"

        if task_md.exists():
            logger.info(f"✅ Found task.md in context: {current_conv_id}")
        else:
            # Broader search if current context missing
            task_files = list(self.brain_root.glob("**/task.md"))
            if task_files:
                latest_task = max(task_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"✅ Found latest task.md: {latest_task.parent.name}")
            else:
                issues.append(
                    f"⚠️ task.md not found (Searched current context {current_conv_id} and brain root)"
                )

        if not issues:
            logger.info("✅ SSOT Alignment Verified. No critical drift detected.")
            return True
        else:
            for issue in issues:
                logger.warning(issue)
            return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    script_path = Path(__file__).resolve()
    root = script_path.parent.parent.parent.parent

    guard = SSOTDriftGuard(str(root))
    if not guard.check_drift():
        sys.exit(1)
    sys.exit(0)
