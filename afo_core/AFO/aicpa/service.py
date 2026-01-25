# Trinity Score: 90.0 (Established by Chancellor)
"""
AICPA Service Layer - 에이전트 군단 서비스

총사령관 역할: 모든 AICPA 에이전트를 조율

眞 (Truth): 정확한 세금 계산
善 (Goodness): 최적의 절세 전략
美 (Beauty): 깔끔한 보고서 생성
孝 (Serenity): Zero Friction 자동화
永 (Eternity): 모든 작업 영구 기록
"""

import logging
import tempfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from AFO.aicpa.report_generator import (
    generate_email_draft,
    generate_quickbooks_csv,
    generate_strategy_report,
    generate_turbotax_csv,
)
from AFO.aicpa.tax_engine import (
    FilingStatus,
    TaxInput,
    calculate_tax,
    simulate_roth_ladder,
)

logger = logging.getLogger(__name__)


class AICPAService:
    """
    AICPA 에이전트 군단 총사령관

    형님의 명령을 받아 4명의 에이전트를 지휘:
    - Data Scouter: 고객 데이터 수집
    - Tax Calculator: 세금 계산
    - Strategy Advisor: 전략 수립
    - Form Filler: 보고서 및 파일 생성
    """

    def __init__(self) -> None:
        self.mission_log = []
        logger.info("[AICPAService] 에이전트 군단 소집 완료")

    def log_mission(self, action: str, result: str) -> None:
        """미션 로그 기록 (永 - Eternity)"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "result": result,
        }
        self.mission_log.append(entry)
        logger.info(f"[AICPAService] {action}: {result}")

    # =========================================================================
    # Agent 1: Data Scouter (데이터 수집)
    # =========================================================================

    def get_client_data(self, client_name: str) -> dict:
        """
        고객 데이터 조회

        현재: Mock 데이터 반환
        추후: Google Sheets API 연동
        """
        # Mock 클라이언트 데이터베이스
        # Mock 클라이언트 데이터베이스
        mock_clients = {
            "justin mason": {
                "name": "Justin Mason",
                "filing_status": "mfj",
                "gross_income": 180000,
                "traditional_ira_balance": 600000,
                "state": "CA",
                "goal": "Tax-Free Legacy",
            },
            "julie kim": {
                "name": "Julie Kim",
                "filing_status": "mfj",
                "gross_income": 250000,
                "traditional_ira_balance": 0,
                "state": "CA",
                "goal": "Backdoor Roth",
            },
            "jayden lee": {
                "name": "Jayden Lee",
                "filing_status": "single",
                "gross_income": 85000,
                "traditional_ira_balance": 20000,
                "state": "CA",
                "goal": "FIRE Movement",
            },
        }

        client_key = client_name.lower()
        mock_clients.get(client_name.lower())

        if client_key in mock_clients:
            self.log_mission("Data Scouter", f"Found client: {client_name}")
            return mock_clients[client_key]

        # 기본 데이터 반환
        self.log_mission("Data Scouter", f"Client not found, using default: {client_name}")
        return {
            "name": client_name,
            "filing_status": "single",
            "gross_income": 100000,
            "traditional_ira_balance": 50000,
            "state": "CA",
            "goal": "General Optimization",
        }

    # =========================================================================
    # Agent 2: Tax Calculator (세금 계산)
    # =========================================================================

    def calculate_tax_scenario(
        self,
        filing_status: str,
        gross_income: int,
        ira_balance: int = 0,
        roth_conversion: int = 0,
        state: str = "CA",
    ) -> dict:
        """
        세금 시나리오 계산

        眞 (Truth): 2025 OBBBA 세법 기반 정밀 계산

        Args:
            filing_status: 신고 상태 (single, mfj, mfs, hoh).
            gross_income: 총 소득 ($).
            ira_balance: 기존 Traditional IRA 잔액 ($).
            roth_conversion: Roth로 전환할 금액 ($).
            state: 거주 주 (기본 CA).

        Returns:
            dict: 세금 계산 결과 (federal_tax, state_tax, total_tax 등).
        """
        # FilingStatus 변환
        status_map = {
            "single": FilingStatus.SINGLE,
            "mfj": FilingStatus.MFJ,
            "mfs": FilingStatus.MFS,
            "hoh": FilingStatus.HOH,
        }

        filing = status_map.get(filing_status.lower(), FilingStatus.SINGLE)

        input_data = TaxInput(
            filing_status=filing,
            gross_income=gross_income,
            traditional_ira_balance=ira_balance,
            roth_conversion_amount=roth_conversion,
            state=state,
        )

        result = calculate_tax(input_data)

        self.log_mission("Tax Calculator", f"Computed for income ${gross_income:,}")

        return asdict(result)

    # =========================================================================
    # Agent 3: Strategy Advisor (전략 수립)
    # =========================================================================

    def generate_roth_strategy(
        self, ira_balance: int, filing_status: str, current_income: int, years: int = 4
    ) -> dict:
        """
        Roth Ladder 전략 시뮬레이션

        永 (Eternity): 장기 부의 증식 전략

        Args:
            ira_balance: 현재 Traditional IRA 잔액.
            filing_status: 신고 상태.
            current_income: 현재 연소득.
            years: 시뮬레이션 기간 (년).

        Returns:
            dict: 연도별 Roth 전환 전략 및 예상 절세액.
        """
        status_map = {
            "single": FilingStatus.SINGLE,
            "mfj": FilingStatus.MFJ,
            "mfs": FilingStatus.MFS,
            "hoh": FilingStatus.HOH,
        }

        filing = status_map.get(filing_status.lower(), FilingStatus.SINGLE)

        result = simulate_roth_ladder(
            ira_balance=ira_balance,
            filing_status=filing,
            current_income=current_income,
            years=years,
        )

        self.log_mission("Strategy Advisor", f"Roth Ladder for ${ira_balance:,} over {years} years")

        return result

    # =========================================================================
    # Agent 4: Form Filler (문서 생성)
    # =========================================================================

    def generate_all_documents(
        self,
        client_name: str,
        tax_result: dict,
        roth_simulation: dict | None = None,
        output_dir: str | None = None,
    ) -> dict:
        """
        모든 문서 일괄 생성

        孝 (Serenity): 버튼 하나로 모든 파일 생성
        """
        # Use tempfile if output_dir not provided
        if output_dir is None:
            output_dir = tempfile.gettempdir()

        safe_name = client_name.replace(" ", "_")
        files = {}

        # 1. Word 보고서
        try:
            word_path = str(Path(output_dir) / f"{safe_name}_Strategy_Report.docx")
            files["word_report"] = generate_strategy_report(
                client_name, tax_result, roth_simulation, word_path
            )
        except Exception as e:
            files["word_report"] = f"Error: {e!s}"

        # 2. TurboTax CSV
        try:
            tt_path = str(Path(output_dir) / f"{safe_name}_TurboTax.csv")
            files["turbotax_csv"] = generate_turbotax_csv(client_name, tax_result, tt_path)
        except Exception as e:
            files["turbotax_csv"] = f"Error: {e!s}"

        # 3. QuickBooks CSV
        try:
            qb_path = str(Path(output_dir) / f"{safe_name}_QuickBooks.csv")
            files["quickbooks_csv"] = generate_quickbooks_csv(client_name, tax_result, qb_path)
        except Exception as e:
            files["quickbooks_csv"] = f"Error: {e!s}"

        # 4. Email Draft
        try:
            files["email_draft"] = generate_email_draft(client_name, asdict(tax_result))
        except Exception as e:
            files["email_draft"] = f"Error: {e!s}"

        self.log_mission("Form Filler", f"Generated {len(files)} documents for {client_name}")

        return files

    # =========================================================================
    # 통합 미션 실행
    # =========================================================================

    def execute_full_mission(self, client_name: str) -> dict:
        """
        전체 AICPA 미션 실행

        1. 데이터 수집 (Data Scouter)
        2. 세금 계산 (Tax Calculator)
        3. 전략 수립 (Strategy Advisor)
        4. 문서 생성 (Form Filler)

        Args:
            client_name: 고객 이름 (Case insensitive).

        Returns:
            dict: 전체 미션 결과 (세금 분석, 전략, 생성된 파일 경로 등).
        """
        self.log_mission("Commander", f"Full mission started for: {client_name}")

        # 1. 데이터 수집
        client_data = self.get_client_data(client_name)

        # 2. 세금 계산
        tax_result = self.calculate_tax_scenario(
            filing_status=client_data.get("filing_status", "single"),
            gross_income=client_data.get("gross_income", 100000),
            ira_balance=client_data.get("traditional_ira_balance", 0),
        )

        # 3. Roth Ladder 시뮬레이션 (IRA 잔액이 있는 경우)
        roth_simulation = None
        if client_data.get("traditional_ira_balance", 0) > 0:
            roth_simulation = self.generate_roth_strategy(
                ira_balance=client_data.get("traditional_ira_balance", 0),
                filing_status=client_data.get("filing_status", "single"),
                current_income=client_data.get("gross_income", 100000),
            )

        # 4. 문서 생성
        documents = self.generate_all_documents(
            client_name=client_data.get("name", client_name),
            tax_result=tax_result,
            roth_simulation=roth_simulation,
        )

        self.log_mission("Commander", f"Mission complete for: {client_name}")

        return {
            "client": client_data,
            "tax_analysis": tax_result,
            "roth_strategy": roth_simulation,
            "generated_files": documents,
            "mission_log": self.mission_log,
            "summary": (
                f"Julie CPA 분석 완료: {client_name}\n"
                f"총 세금: ${tax_result.get('total_tax', 0):,}\n"
                f"절세 기회: ${tax_result.get('roth_conversion_recommendation', 0):,}\n"
                f"생성된 파일: {len(documents)}개"
            ),
        }


# 싱글톤 인스턴스
_service_instance = None


def get_aicpa_service() -> AICPAService:
    """AICPA 서비스 싱글톤 획득"""
    global _service_instance
    if _service_instance is None:
        _service_instance = AICPAService()
    return _service_instance
