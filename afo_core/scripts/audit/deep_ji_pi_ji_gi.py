"""
Deep Ji-Pi-Ji-Gi (眞 - Palantir-style Audit)
왕국의 모든 장기를 정밀 타격하여 순수성을 검증합니다.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add package root
script_dir = os.path.dirname(os.path.abspath(__file__))
package_root = os.path.abspath(os.path.join(script_dir, "../../"))
if package_root not in sys.path:
    sys.path.append(package_root)

from AFO.serenity.evolution_loop import EvolutionLoop
from AFO.serenity.self_diagnostics import SelfDiagnostics

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def run_deep_audit():
    """심층 지피지기 감사 및 자아 진화 실행"""
    logger.info("⚔️ Starting Deep Ji-Pi-Ji-Gi Audit...")

    # 1. 진단 (Diagnostics)
    diag = SelfDiagnostics()
    initial_report = await diag.run_full_diagnosis()

    # 2. 진화 및 치유 (Evolution)
    loop = EvolutionLoop()
    final_report = await loop.evolve()

    # 3. 결과 비교 및 보고
    initial_score = initial_report["trinity"]["trinity_score"] * 100
    final_score = final_report["trinity"]["trinity_score"] * 100

    logger.info("=" * 50)
    logger.info("🏆 AUDIT COMPLETE")
    logger.info(f"📈 Initial Health: {initial_score:.1f}%")
    logger.info(f"📊 Final Health:   {final_score:.1f}%")
    logger.info(f"⚖️ Balance Status: {final_report['status']}")
    logger.info("=" * 50)

    if final_score < 70:
        logger.error("❌ Kingdom is in critical condition. Manual intervention required.")
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(run_deep_audit())
    sys.exit(0 if success else 1)
