#!/usr/bin/env python3
"""
AFO 왕국 Cybernetic Loop 검증 스크립트
Phase 43: The Cybernetic Loop (자율 진화의 고리)

로그 분석 시스템과 Self-Evolution Loop의 통합을 검증합니다.
Critical 로그 주입 시 Truth Score가 자동으로 하락하는지 확인합니다.
"""

import asyncio
import json
import logging
import tempfile
import time
from pathlib import Path

from AFO.serenity.self_diagnostics import SelfDiagnostics
from AFO.services.log_analysis import LogAnalysisService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CyberneticLoopVerifier:
    """Cybernetic Loop 검증기"""

    def __init__(self) -> None:
        self.diagnostics = SelfDiagnostics()
        self.log_service = LogAnalysisService(output_dir="cybernetic_test_results")
        self.test_results = {}

    async def run_full_verification(self) -> dict:
        """완전한 Cybernetic Loop 검증 실행"""
        logger.info("🚀 Starting Cybernetic Loop Verification (Phase 43)")

        # Phase 1: 초기 상태 확인
        logger.info("📊 Phase 1: Initial State Assessment")
        initial_report = await self.diagnostics.run_full_diagnosis()
        initial_truth_score = initial_report["trinity"]["truth"]
        logger.info(f"Initial Truth Score: {initial_truth_score:.3f}")

        # Phase 2: Critical 로그 주입
        logger.info("💉 Phase 2: Injecting Critical Logs")
        critical_log_path = await self._inject_critical_logs()

        # Phase 3: 로그 분석 실행
        logger.info("🔍 Phase 3: Log Analysis Execution")
        analysis_result = await self._run_log_analysis(critical_log_path)

        # Phase 4: 진단 재실행 (Truth Score 변화 확인)
        logger.info("🩺 Phase 4: Post-Analysis Diagnostics")
        final_report = await self.diagnostics.run_full_diagnosis()
        final_truth_score = final_report["trinity"]["truth"]
        logger.info(f"Final Truth Score: {final_truth_score:.3f}")

        # Phase 5: Cybernetic Loop 효과 검증
        logger.info("🔄 Phase 5: Cybernetic Loop Effectiveness")
        loop_effectiveness = self._verify_cybernetic_effectiveness(
            initial_truth_score, final_truth_score, analysis_result
        )

        # 결과 정리
        verification_result = {
            "phase": "Phase 43: The Cybernetic Loop",
            "timestamp": time.time(),
            "initial_state": {
                "truth_score": initial_truth_score,
                "overall_health": initial_report["status"],
            },
            "critical_injection": {
                "log_file": str(critical_log_path),
                "injected_errors": 5,  # CRITICAL 레벨 로그 5개
                "analysis_completed": analysis_result["pipeline_status"] == "SUCCESS",
            },
            "final_state": {
                "truth_score": final_truth_score,
                "overall_health": final_report["status"],
            },
            "cybernetic_effectiveness": loop_effectiveness,
            "verification_status": (
                "SUCCESS" if loop_effectiveness["pain_detection"] else "FAILED"
            ),
        }

        self.test_results = verification_result
        return verification_result

    async def _inject_critical_logs(self) -> Path:
        """Critical 레벨 로그를 주입하여 시스템 고통 유발"""
        # 임시 로그 파일 생성
        temp_dir = Path("cybernetic_test_results")
        temp_dir.mkdir(exist_ok=True)
        log_file = temp_dir / "critical_test.log"

        # CRITICAL 레벨 로그 패턴들
        critical_logs = [
            "[CRITICAL] Database connection failed: Connection timeout after 30 seconds",
            "[CRITICAL] Memory allocation failed: Out of memory (requested 1GB)",
            "[CRITICAL] Authentication service down: Unable to verify user credentials",
            "[CRITICAL] File system corruption detected: Data integrity compromised",
            "[CRITICAL] Network partition detected: Cluster split-brain condition",
        ]

        # 일반 로그와 섞어서 현실성 높임
        normal_logs = [
            "[INFO] Application started successfully",
            "[INFO] Database connection established",
            "[WARNING] High memory usage detected: 85%",
            "[INFO] User authentication successful",
            "[WARNING] Network latency increased: 150ms",
        ]

        # 로그 파일 작성
        with open(log_file, "w") as f:
            # 일반 로그 먼저
            for log in normal_logs:
                f.write(f"{log}\n")

            # CRITICAL 로그 주입 (시스템 고통 유발)
            for log in critical_logs:
                f.write(f"{log}\n")
                await asyncio.sleep(0.1)  # 시간 간격 두기

            # 추가 일반 로그
            for i in range(10):
                f.write(f"[INFO] Routine operation {i + 1} completed\n")

        logger.info(f"Injected {len(critical_logs)} critical logs into {log_file}")
        return log_file

    async def _run_log_analysis(self, log_file: Path) -> dict:
        """로그 분석 실행"""
        try:
            result = self.log_service.run_pipeline(str(log_file))

            if result["pipeline_status"] == "SUCCESS":
                logger.info("✅ Log analysis completed successfully")
                logger.info(f"📊 Chunks created: {result['chunking']['chunks_created']}")
                logger.info(f"🔍 Analysis status: {result['sequential']['status']}")
            else:
                logger.error(f"❌ Log analysis failed: {result.get('error', 'Unknown error')}")

            return result

        except Exception as e:
            logger.error(f"💥 Log analysis execution failed: {e}")
            return {"pipeline_status": "FAILED", "error": str(e)}

    def _verify_cybernetic_effectiveness(
        self, initial_score: float, final_score: float, analysis_result: dict
    ) -> dict:
        """Cybernetic Loop 효과 검증"""

        # Truth Score 변화 계산
        score_change = initial_score - final_score
        score_drop_percentage = (score_change / initial_score) * 100 if initial_score > 0 else 0

        # 고통 감지 여부 (Truth Score 10% 이상 하락)
        pain_detection = score_drop_percentage >= 10.0

        # 분석 성공 여부
        analysis_success = analysis_result.get("pipeline_status") == "SUCCESS"

        # Cybernetic Loop 완전성
        loop_integrity = pain_detection and analysis_success

        effectiveness = {
            "score_change": score_change,
            "score_drop_percentage": score_drop_percentage,
            "pain_detection": pain_detection,
            "analysis_success": analysis_success,
            "loop_integrity": loop_integrity,
            "assessment": (
                "PERFECT" if loop_integrity else "IMPAIRED" if pain_detection else "BROKEN"
            ),
        }

        logger.info(f"🎯 Cybernetic Effectiveness: {effectiveness['assessment']}")
        logger.info(f"📉 Truth Score Drop: {score_drop_percentage:.1f}%")
        logger.info(f"🩺 Pain Detection: {'✅' if pain_detection else '❌'}")
        logger.info(f"🔄 Loop Integrity: {'✅' if loop_integrity else '❌'}")

        return effectiveness

    def generate_report(self) -> str:
        """검증 보고서 생성"""
        if not self.test_results:
            return "No verification results available"

        r = self.test_results

        report = f"""
# AFO 왕국 Cybernetic Loop 검증 보고서
## Phase 43: The Cybernetic Loop (자율 진화의 고리)

**검증 시간**: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r["timestamp"]))}

### 📊 검증 결과

#### 초기 상태
- Truth Score: {r["initial_state"]["truth_score"]:.3f}
- 전반적 건강: {r["initial_state"]["overall_health"]}

#### Critical 로그 주입
- 로그 파일: {r["critical_injection"]["log_file"]}
- 주입된 오류 수: {r["critical_injection"]["injected_errors"]}
- 분석 완료: {"✅" if r["critical_injection"]["analysis_completed"] else "❌"}

#### 최종 상태
- Truth Score: {r["final_state"]["truth_score"]:.3f}
- 전반적 건강: {r["final_state"]["overall_health"]}

### 🔄 Cybernetic Loop 효과

#### 수치 변화
- Score 변화: {r["cybernetic_effectiveness"]["score_change"]:.3f}
- Score 하락률: {r["cybernetic_effectiveness"]["score_drop_percentage"]:.1f}%

#### 기능 검증
- 고통 감지: {"✅" if r["cybernetic_effectiveness"]["pain_detection"] else "❌"}
- 분석 성공: {"✅" if r["cybernetic_effectiveness"]["analysis_success"] else "❌"}
- Loop 완전성: {"✅" if r["cybernetic_effectiveness"]["loop_integrity"] else "❌"}

### 🎯 종합 평가

**검증 상태**: {r["verification_status"]}
**Loop 효과**: {r["cybernetic_effectiveness"]["assessment"]}

### 💡 해석

"""

        effectiveness = r["cybernetic_effectiveness"]

        if effectiveness["loop_integrity"]:
            report += """
**🎉 PERFECT**: Cybernetic Loop가 완벽하게 작동합니다.
- Critical 로그 주입 시 Truth Score가 적절히 하락
- 로그 분석이 성공적으로 수행됨
- 시스템이 고통을 인지하고 분석을 통해 진단 가능
"""
        elif effectiveness["pain_detection"]:
            report += """
**⚠️ IMPAIRED**: 부분적 기능. 고통 감지는 작동하지만 분석에 문제가 있음.
- Truth Score 하락은 감지되나 분석 파이프라인에 개선 필요
"""
        else:
            report += """
**💔 BROKEN**: Cybernetic Loop에 결함이 있습니다.
- Truth Score 변화 미감지 또는 분석 실패
- 즉시 진단 및 수리 필요
"""

        report += f"""

### 📁 생성된 파일들
- 로그 파일: {r["critical_injection"]["log_file"]}
- 분석 결과: cybernetic_test_results/

### 🔧 권고사항

1. **시스템 모니터링**: Truth Score 변화를 지속적으로 모니터링
2. **로그 품질**: Critical 로그 패턴을 정기적으로 검증
3. **분석 정확도**: 로그 분석 결과의 정확성을 주기적으로 검증
4. **자동화**: 이 검증을 CI/CD 파이프라인에 통합

---

*AFO 왕국 Cybernetic Loop 검증 스크립트에 의해 생성됨*
"""

        return report


async def main():
    """메인 실행 함수"""
    print("🧬 AFO 왕국 Cybernetic Loop 검증 시작")
    print("=" * 50)

    verifier = CyberneticLoopVerifier()

    try:
        # 검증 실행
        result = await verifier.run_full_verification()

        # 보고서 생성 및 출력
        report = verifier.generate_report()
        print(report)

        # 파일로 저장
        report_file = Path("cybernetic_test_results/cybernetic_verification_report.md")
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"📄 보고서 저장됨: {report_file}")

        # 최종 상태 출력
        status = "✅ SUCCESS" if result["verification_status"] == "SUCCESS" else "❌ FAILED"
        print(f"\n🏁 최종 검증 상태: {status}")

    except Exception as e:
        print(f"💥 검증 실행 실패: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
