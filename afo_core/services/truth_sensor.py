import asyncio
import datetime
import logging
import shutil
from pathlib import Path

from AFO.domain.metrics.trinity import TrinityInputs
from AFO.domain.metrics.trinity_manager import trinity_manager

logger = logging.getLogger(__name__)

# x = undefined_variable_for_testing  # 주석 처리하여 임포트 오류 방지


class PhysicalTruthSensor:
    """
    [PhysicalTruthSensor]
    眞 (Truth)의 물리적 무결성을 감시하는 보초병.
    Ruff, MyPy 등을 직접 실행하여 코드의 실질적 품질을 측정합니다.
    """

    def __init__(self, check_interval: int = 15):
        self.check_interval = check_interval
        self.is_running = False
        # Improved path resolution: Find 'AFO' directory relative to this file
        current_file = Path(__file__).resolve()
        self._afo_dir = current_file.parent.parent  # AFO/
        self._project_root = self._afo_dir.parent  # packages/afo-core/

    async def start(self):
        """센서 가동"""
        print(f"🛡️ !!! PHYSICAL TRUTH SENSOR STARTING !!! (眞) Path: {self._afo_dir}")
        if self.is_running:
            return
        self.is_running = True
        logger.info("🛡️ Physical Truth Sensor activated (眞)")
        asyncio.create_task(self._monitoring_loop())

    async def _monitoring_loop(self):
        while self.is_running:
            try:
                await self.perform_audit()
            except Exception as e:
                logger.error(f"❌ Truth Sensor audit failed: {e}")
            await asyncio.sleep(self.check_interval)

    async def perform_audit(self):
        """물리적 감서 수행 (Ruff + MyPy)"""
        # 1. Ruff Audit
        ruff_score = 1.0
        try:
            ruff_path = shutil.which("ruff")
            if not ruff_path:
                raise FileNotFoundError("ruff executable not found in PATH")

            # AFO 패키지 내의 최소한의 규칙 검사
            process = await asyncio.create_subprocess_exec(
                ruff_path,
                "check",
                ".",
                "--select",
                "E,F",
                "--ignore",
                "E501",
                cwd=str(self._afo_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            if process.returncode != 0:
                # 위반 사항 개수에 따라 감점 (최소 0.5)
                violation_count = len(stdout.decode().splitlines())
                ruff_score = max(0.5, 1.0 - (violation_count * 0.05))
                logger.warning(f"⚠️ Ruff violations detected: {violation_count}")
        except Exception as e:
            error_msg = f"Ruff check error: {e}"
            logger.error(error_msg)
            with open("/tmp/afo_truth_sensor.log", "a") as f:
                f.write(f"ERROR: {error_msg}\n")
            ruff_score = 0.5

        # 2. MyPy Audit (Targeted)
        mypy_score = 1.0
        try:
            mypy_path = shutil.which("mypy")
            if not mypy_path:
                raise FileNotFoundError("mypy executable not found in PATH")

            # api_server.py를 대표 지표로 타입 검사
            process = await asyncio.create_subprocess_exec(
                mypy_path,
                "api_server.py",
                "--ignore-missing-imports",
                cwd=str(self._afo_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            if process.returncode != 0:
                mypy_score = 0.7  # 타입 불일치 시 감점
                logger.warning("⚠️ MyPy type safety violations detected in core")
        except Exception as e:
            logger.error(f"MyPy check error: {e}")
            mypy_score = 0.6

        # 3. Trinity Score 반영
        # 眞 (Truth) = (Ruff + MyPy) / 2
        final_truth = (ruff_score + mypy_score) / 2.0

        # TrinityManager의 base_inputs 업데이트 (실질적 반영)
        current_inputs = trinity_manager.base_inputs
        new_inputs = TrinityInputs(
            truth=final_truth,
            goodness=current_inputs.goodness,
            beauty=current_inputs.beauty,
            filial_serenity=current_inputs.filial_serenity,
        )
        trinity_manager.base_inputs = new_inputs

        # Debug Log to File
        with open("/tmp/afo_truth_sensor.log", "a") as f:
            f.write(
                f"{datetime.datetime.now()} - Truth: {final_truth:.3f} (Ruff: {ruff_score}, MyPy: {mypy_score})\n"
            )

        logger.info(f"📊 Physical Truth Updated: {final_truth * 100:.1f}% (Measured via Ruff/MyPy)")


# Singleton Sensor
truth_sensor = PhysicalTruthSensor()
