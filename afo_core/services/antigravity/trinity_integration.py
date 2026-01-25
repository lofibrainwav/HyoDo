# Trinity Score: 90.0 (Established by Chancellor)
"""
Trinity Integration - Antigravity ↔ Trinity Evidence 연결
모듈식 Antigravity 엔진을 Trinity Evidence 시스템에 통합
"""

import logging
from datetime import datetime
from typing import Any, cast

from .modular_engine import ModularAntigravityEngine, create_simple_engine

logger = logging.getLogger(__name__)


class TrinityAntigravityIntegration:
    """
    Trinity Evidence와 Antigravity의 통합 인터페이스

    주요 기능:
    1. Trinity Evidence의 점수를 Antigravity 품질 게이트에 연결
    2. Antigravity 결과를 Trinity Evidence에 피드백
    3. 자동화된 품질 게이트 워크플로우
    """

    def __init__(self, engine: ModularAntigravityEngine | None = None) -> None:
        """
        통합 인터페이스 초기화

        Args:
            engine: 사용할 Antigravity 엔진 (기본: simple_engine)
        """
        self.engine = engine or create_simple_engine()
        self.last_evaluation: dict[str, Any] | None = None
        self.evaluation_history: list[dict[str, Any]] = []

        logger.info("✅ Trinity-Antigravity 통합 초기화 완료")
        logger.info(f"사용 엔진: {self.engine._get_active_modules()}")

    async def evaluate_from_trinity_evidence(
        self, trinity_evidence_path: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Trinity Evidence 파일에서 직접 품질 게이트 평가

        Args:
            trinity_evidence_path: Trinity Evidence JSON 파일 경로
            context: 추가 맥락 정보

        Returns:
            평가 결과
        """
        try:
            # Trinity Evidence 로드
            evidence_data = self._load_trinity_evidence(trinity_evidence_path)

            # 점수 추출
            trinity_score = evidence_data.get("calculation", {}).get("total", 0.0)

            # Risk Score 계산 (Trinity Score 기반)
            risk_score = self._calculate_risk_from_evidence(evidence_data)

            # 맥락 정보 구성
            evaluation_context = self._build_evaluation_context(evidence_data, context or {})

            # 품질 게이트 평가
            result = await self.engine.evaluate_quality_gate(
                trinity_score, risk_score, evaluation_context
            )

            # 결과 기록
            self.last_evaluation = result
            self.evaluation_history.append(
                {
                    "timestamp": datetime.now(),
                    "evidence_path": trinity_evidence_path,
                    "trinity_score": trinity_score,
                    "risk_score": risk_score,
                    "decision": result["decision"],
                    "confidence": result.get("confidence", 0.0),
                }
            )

            # Trinity Evidence에 피드백
            await self._feedback_to_trinity_evidence(trinity_evidence_path, result)

            logger.info(f"✅ Trinity Evidence 기반 평가 완료: {result['decision']}")
            return result

        except Exception as e:
            logger.error(f"Trinity Evidence 평가 실패: {e}")
            raise

    def _load_trinity_evidence(self, evidence_path: str) -> dict[str, Any]:
        """
        Trinity Evidence 파일 로드

        Args:
            evidence_path: JSON 파일 경로

        Returns:
            파싱된 Evidence 데이터
        """
        import json
        from pathlib import Path

        evidence_file = Path(evidence_path)
        if not evidence_file.exists():
            raise FileNotFoundError(f"Trinity Evidence 파일 없음: {evidence_path}")

        with open(evidence_file, encoding="utf-8") as f:
            return cast("dict[str, Any]", json.load(f))

    def _calculate_risk_from_evidence(self, evidence_data: dict[str, Any]) -> float:
        """
        Trinity Evidence에서 Risk Score 계산

        Risk Score 계산 기준:
        - 테스트 실패율
        - 린트 위반 수
        - 보안 취약점 수
        - 코드 복잡도

        Args:
            evidence_data: Evidence 데이터

        Returns:
            계산된 Risk Score (0-100)
        """
        risk_factors = []

        # 테스트 실패율 기반 리스크
        test_results = evidence_data.get("test_results", {})
        if test_results:
            total_tests = test_results.get("total", 0)
            failed_tests = test_results.get("failed", 0)
            if total_tests > 0:
                failure_rate = failed_tests / total_tests
                risk_factors.append(failure_rate * 30)  # 최대 30점

        # 린트 위반 기반 리스크
        lint_results = evidence_data.get("lint_results", {})
        if lint_results:
            violations = lint_results.get("violations", 0)
            risk_factors.append(min(violations * 2, 20))  # 최대 20점

        # 보안 취약점 기반 리스크
        security_results = evidence_data.get("security_results", {})
        if security_results:
            vulnerabilities = security_results.get("vulnerabilities", 0)
            risk_factors.append(min(vulnerabilities * 10, 30))  # 최대 30점

        # 코드 복잡도 기반 리스크
        complexity = evidence_data.get("complexity_score", 0)
        if complexity > 50:  # 복잡도가 높으면 리스크 증가
            risk_factors.append(min((complexity - 50) * 0.5, 20))

        # 종합 리스크 계산
        total_risk = sum(risk_factors)
        return float(min(total_risk, 100.0))  # 최대 100점

    def _build_evaluation_context(
        self, evidence_data: dict[str, Any], additional_context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        평가 맥락 정보 구성

        Args:
            evidence_data: Evidence 데이터
            additional_context: 추가 맥락

        Returns:
            완성된 평가 맥락
        """
        context = {
            "evidence_type": "trinity_evidence",
            "timestamp": evidence_data.get("generated_at"),
            "project_info": evidence_data.get("project_info", {}),
            "test_coverage": evidence_data.get("test_coverage", 80.0),
            "ci_status": evidence_data.get("ci_status", "unknown"),
            "change_scope": self._infer_change_scope(evidence_data),
            "team_experience": additional_context.get("team_experience", "intermediate"),
            "time_pressure": additional_context.get("time_pressure", "normal"),
        }

        # 추가 맥락 병합
        context.update(additional_context)
        return context

    def _infer_change_scope(self, evidence_data: dict[str, Any]) -> str:
        """
        Evidence 데이터에서 변경 범위 추론

        Args:
            evidence_data: Evidence 데이터

        Returns:
            추론된 변경 범위 ("small", "medium", "large", "breaking")
        """
        # 변경된 파일 수 기반 추론
        changed_files = evidence_data.get("changed_files", [])
        if len(changed_files) <= 3:
            return "small"
        elif len(changed_files) <= 10:
            return "medium"
        elif len(changed_files) <= 50:
            return "large"
        else:
            return "breaking"

    async def _feedback_to_trinity_evidence(
        self, evidence_path: str, evaluation_result: dict[str, Any]
    ) -> None:
        """
        평가 결과를 Trinity Evidence에 피드백

        Args:
            evidence_path: Evidence 파일 경로
            evaluation_result: 평가 결과
        """
        try:
            # Evidence 파일에 평가 결과 추가
            import json
            from pathlib import Path

            evidence_file = Path(evidence_path)
            if not evidence_file.exists():
                return

            # 기존 데이터 로드
            with open(evidence_file, encoding="utf-8") as f:
                data = json.load(f)

            # 평가 결과 추가
            data["antigravity_evaluation"] = {
                "timestamp": datetime.now().isoformat(),
                "decision": evaluation_result["decision"],
                "confidence": evaluation_result.get("confidence", 0.0),
                "active_modules": evaluation_result.get("active_modules", []),
                "trinity_score_used": evaluation_result["trinity_score"],
                "risk_score_calculated": evaluation_result["risk_score"],
            }

            # 파일 저장
            with open(evidence_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Trinity Evidence에 평가 결과 피드백: {evidence_path}")

        except Exception as e:
            logger.warning(f"Trinity Evidence 피드백 실패: {e}")

    async def run_automated_workflow(
        self, evidence_path: str, auto_apply: bool = False
    ) -> dict[str, Any]:
        """
        자동화된 품질 게이트 워크플로우

        Args:
            evidence_path: Trinity Evidence 파일 경로
            auto_apply: AUTO_RUN 시 자동 적용 여부

        Returns:
            워크플로우 결과
        """
        logger.info(f"🚀 자동 품질 게이트 워크플로우 시작: {evidence_path}")

        # 1. 평가 실행
        evaluation = await self.evaluate_from_trinity_evidence(evidence_path)

        # 2. 결정에 따른 액션
        decision = evaluation["decision"]
        actions_taken = []

        if decision == "AUTO_RUN":
            if auto_apply:
                actions_taken.append("자동 배포 실행")
                # 실제 배포 로직은 여기서 호출
                logger.info("✅ AUTO_RUN: 자동 배포 진행")
            else:
                actions_taken.append("자동 배포 준비됨")
                logger.info("✅ AUTO_RUN: 수동 확인 대기")

        elif decision == "ASK_COMMANDER":
            actions_taken.append("형님 판단 요청")
            # 알림 시스템 호출
            logger.info("⚠️ ASK_COMMANDER: 형님 판단 요청")

        else:  # BLOCK
            actions_taken.append("배포 차단")
            # 차단 조치 실행
            logger.warning("🛑 BLOCK: 배포 차단")

        # 3. 보고서 생성 (활성화된 경우)
        report_path = None
        if self.engine.config.get("use_reporting", False):
            try:
                report = await self.engine.generate_report(
                    "analysis",
                    {
                        "title": f"품질 게이트 평가 - {decision}",
                        "evidence_path": evidence_path,
                    },
                    {
                        "decision": decision,
                        "confidence": evaluation.get("confidence", 0.0),
                    },
                    {"evaluation": evaluation},
                    actions_taken,
                )

                if report:
                    report_path = self.engine.save_report(
                        report,
                        f"quality_gate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    )
                    actions_taken.append(f"보고서 생성: {report_path}")

            except Exception as e:
                logger.warning(f"보고서 생성 실패: {e}")

        result = {
            "evaluation": evaluation,
            "decision": decision,
            "actions_taken": actions_taken,
            "report_path": report_path,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"✅ 자동 워크플로우 완료: {decision}")
        return result

    def get_evaluation_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        평가 히스토리 조회

        Args:
            limit: 최대 조회 개수

        Returns:
            최근 평가 히스토리
        """
        return self.evaluation_history[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        """
        평가 통계 조회

        Returns:
            평가 통계
        """
        if not self.evaluation_history:
            return {"total_evaluations": 0}

        decisions = [h["decision"] for h in self.evaluation_history]
        total = len(decisions)

        return {
            "total_evaluations": total,
            "auto_run_rate": decisions.count("AUTO_RUN") / total * 100,
            "ask_commander_rate": decisions.count("ASK_COMMANDER") / total * 100,
            "block_rate": (decisions.count("BLOCK") if "BLOCK" in decisions else 0) / total * 100,
            "average_confidence": sum(h.get("confidence", 0.0) for h in self.evaluation_history)
            / total,
        }


# 싱글톤 인스턴스
trinity_integration = TrinityAntigravityIntegration()
