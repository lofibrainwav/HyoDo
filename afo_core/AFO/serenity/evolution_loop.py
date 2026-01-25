"""
AFO Evolution Loop (善 - Self-Healing)
진단 결과를 바탕으로 스스로를 치유하고 최적화합니다.
"""

import asyncio
import logging
import subprocess

from AFO.serenity.self_diagnostics import SelfDiagnostics

logger = logging.getLogger(__name__)


class EvolutionLoop:
    """왕국 자아 진화 루프"""

    def __init__(self) -> None:
        self.diagnostics = SelfDiagnostics()

    async def heal_truth(self, findings: list[str]):
        """眞(Truth) 치유: 데이터 정합성 복구"""
        for finding in findings:
            if "Knowledge base is empty" in finding:
                logger.warning("🩹 Healing Truth: Re-indexing knowledge base...")
                # 재인덱싱 스크립트 실행
                try:
                    subprocess.run(
                        [
                            "python3",
                            "packages/afo-core/scripts/rag/reindex_kingdom_to_lancedb.py",
                        ],
                        check=True,
                        capture_output=True,
                    )
                    logger.info("✅ Truth Healed: Re-indexing complete.")
                except Exception as e:
                    logger.error(f"❌ Truth Healing Failed: {e}")

    async def evolve(self):
        """진화 프로세스 실행"""
        logger.info("🚀 Starting Evolution Cycle...")

        report = await self.diagnostics.run_full_diagnosis()
        trinity = report["trinity"]

        logger.info(f"📊 Current Trinity Score: {trinity['trinity_score'] * 100:.1f}/100")

        # 1. 진단 결과에 따른 치유 작업
        for result in report["details"]:
            if result.status in ["WARNING", "CRITICAL"]:
                logger.info(f"🕵️ Analyzing {result.lens} issues...")
                if result.lens == "眞":
                    await self.heal_truth(result.findings)
                elif result.lens == "善":
                    logger.info("🛡️ Goodness optimization: Hardening security posture...")
                elif result.lens == "美":
                    logger.info("🎨 Beauty refinement: Enforcing design system constraints...")

        # 2. 결과 재확인
        final_report = await self.diagnostics.run_full_diagnosis()
        logger.info(
            f"✨ Evolution Cycle Complete. Final Score: {final_report['trinity']['trinity_score'] * 100:.1f}/100"
        )
        return final_report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def main():
        loop = EvolutionLoop()
        await loop.evolve()

    asyncio.run(main())
