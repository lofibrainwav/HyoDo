"""
Mathematical Tools for CPA Enhancement
수학적 도구들로 CPA들의 friction을 날카롭게 하고 총명을 높인다.

Science Skill Rules Integration:
- Rule 3.1: Symbolic mathematics with sympy
- Rule 3.2: Linear algebra operations
- Rule 3.3: Statistical analysis for scientific data
- Rule 7.1: Use Map/Set for frequent lookups
- Rule 7.2: Avoid creating functions in loops
"""

from typing import Any

# Python 3.9 compatibility - use traditional typing
import numpy as np


class CPAMathematicalTools:
    """
    CPA들을 위한 수학적 도구 모음
    과학적 정확성과 계산 효율성으로 friction을 날카롭게 한다.
    """

    @staticmethod
    def calculate_depreciation_schedule(
        cost_basis: float, salvage_value: float, useful_life: int, method: str = "straight_line"
    ) -> dict[str, Any]:
        """
        감가상각 스케줄 계산 (CPA 필수 계산)
        Rule 3.2: Linear algebra operations 적용

        Args:
            cost_basis: 취득원가
            salvage_value: 잔존가치
            useful_life: 내용연수
            method: 감가상각 방법

        Returns:
            감가상각 스케줄 및 관련 메트릭
        """
        if method == "straight_line":
            # 직선법: (취득원가 - 잔존가치) / 내용연수
            annual_depr = (cost_basis - salvage_value) / useful_life
            accumulated_depr = 0
            book_value = cost_basis
            schedule = []

            for year in range(1, useful_life + 1):
                accumulated_depr += annual_depr
                book_value -= annual_depr
                schedule.append(
                    {
                        "year": year,
                        "depreciation": annual_depr,
                        "accumulated": accumulated_depr,
                        "book_value": max(book_value, salvage_value),
                    }
                )

            return {
                "method": "straight_line",
                "schedule": schedule,
                "total_depreciation": accumulated_depr,
                "final_book_value": max(book_value, salvage_value),
            }

        elif method == "declining_balance":
            # 정률법 (double declining balance)
            rate = 2.0 / useful_life  # 200% 정률법
            accumulated_depr = 0
            book_value = cost_basis
            schedule = []

            for year in range(1, useful_life + 1):
                annual_depr = book_value * rate
                # 마지막 연도: 잔존가치를 초과하지 않도록 조정
                if book_value - annual_depr < salvage_value:
                    annual_depr = book_value - salvage_value

                accumulated_depr += annual_depr
                book_value -= annual_depr

                schedule.append(
                    {
                        "year": year,
                        "depreciation": annual_depr,
                        "accumulated": accumulated_depr,
                        "book_value": max(book_value, salvage_value),
                    }
                )

            return {
                "method": "declining_balance",
                "schedule": schedule,
                "total_depreciation": accumulated_depr,
                "final_book_value": max(book_value, salvage_value),
            }

        else:
            raise ValueError(f"Unsupported depreciation method: {method}")

    @staticmethod
    def optimize_tax_strategy(
        income: float, deductions: list[float], tax_brackets: list[tuple[float, float]]
    ) -> dict[str, float | list[dict]]:
        """
        세금 최적화 전략 계산 (CPA 고급 분석)
        Rule 3.3: Statistical analysis 적용

        Args:
            income: 총소득
            deductions: 공제 항목들
            tax_brackets: 세율 구간 [(하한, 세율), ...]

        Returns:
            세금 최적화 분석 결과
        """
        # 총 공제액 계산
        total_deductions = sum(deductions)
        taxable_income = max(0, income - total_deductions)

        # 세금 계산 함수
        def calculate_tax(income_amt: float) -> float:
            tax = 0.0
            remaining = income_amt
            num_brackets = len(tax_brackets)

            for i in range(num_brackets):
                if remaining <= 0:
                    break

                current_bracket = tax_brackets[i]
                bracket_min, rate = current_bracket

                # Get next bracket's minimum or infinity for last bracket
                if i + 1 < num_brackets:
                    next_bracket = tax_brackets[i + 1]
                    next_bracket_min = next_bracket[0]
                else:
                    next_bracket_min = float("inf")

                taxable_in_bracket = min(remaining, next_bracket_min - bracket_min)
                tax += taxable_in_bracket * rate
                remaining -= taxable_in_bracket

            return tax

        # 현재 세금
        current_tax = calculate_tax(taxable_income)

        # 최적화 분석: 추가 공제의 효용성
        optimization_scenarios = []
        for additional_deduction in [1000, 5000, 10000, 25000]:
            new_taxable = max(0, taxable_income - additional_deduction)
            new_tax = calculate_tax(new_taxable)
            savings = current_tax - new_tax
            efficiency = savings / additional_deduction if additional_deduction > 0 else 0

            optimization_scenarios.append(
                {
                    "additional_deduction": additional_deduction,
                    "new_tax": new_tax,
                    "savings": savings,
                    "efficiency": efficiency,
                    "marginal_rate": efficiency,
                }
            )

        return {
            "current_income": income,
            "total_deductions": total_deductions,
            "taxable_income": taxable_income,
            "current_tax": current_tax,
            "effective_rate": current_tax / income if income > 0 else 0,
            "optimization_scenarios": optimization_scenarios,
        }

    @staticmethod
    def calculate_financial_ratios(
        balance_sheet: dict[str, float], income_statement: dict[str, float]
    ) -> dict[str, float]:
        """
        재무 비율 분석 (CPA 핵심 역량)
        Rule 7.1: Use Map/Set for frequent lookups 적용

        Args:
            balance_sheet: 대차대조표 데이터
            income_statement: 손익계산서 데이터

        Returns:
            재무 비율 분석 결과
        """
        # 빠른 조회를 위한 맵 생성 (Rule 7.1)
        bs_map = {k.lower(): v for k, v in balance_sheet.items()}
        is_map = {k.lower(): v for k, v in income_statement.items()}

        ratios = {}

        # 유동성 비율
        current_assets = bs_map.get("current assets", 0)
        current_liabilities = bs_map.get("current liabilities", 0)
        if current_liabilities > 0:
            ratios["current_ratio"] = current_assets / current_liabilities

        # 부채 비율
        total_liabilities = bs_map.get("total liabilities", 0)
        total_assets = bs_map.get("total assets", 0)
        if total_assets > 0:
            ratios["debt_ratio"] = total_liabilities / total_assets

        # 수익성 비율
        net_income = is_map.get("net income", 0)
        total_revenue = is_map.get("total revenue", is_map.get("sales", 0))
        if total_revenue > 0:
            ratios["profit_margin"] = net_income / total_revenue

        # 투자 수익률
        shareholders_equity = bs_map.get("shareholders equity", bs_map.get("owners equity", 0))
        if shareholders_equity > 0:
            ratios["return_on_equity"] = net_income / shareholders_equity

        return ratios

    @staticmethod
    def forecast_financial_performance(
        historical_data: list[dict[str, float]], periods: int = 5
    ) -> dict[str, list[float]]:
        """
        재무 성과 예측 (CPA 미래 예측)
        Rule 3.3: Statistical analysis 적용

        Args:
            historical_data: 과거 재무 데이터
            periods: 예측 기간

        Returns:
            예측 결과
        """
        if len(historical_data) < 3:
            raise ValueError("Need at least 3 periods of historical data")

        # 데이터 추출
        revenues = [d.get("revenue", d.get("sales", 0)) for d in historical_data]
        net_incomes = [d.get("net_income", 0) for d in historical_data]

        # 선형 회귀 예측
        x = np.arange(len(revenues))
        revenue_slope, revenue_intercept = np.polyfit(x, revenues, 1)
        income_slope, income_intercept = np.polyfit(x, net_incomes, 1)

        # 예측 생성
        forecast_revenues = []
        forecast_incomes = []

        for i in range(1, periods + 1):
            future_x = len(revenues) + i - 1
            forecast_revenues.append(revenue_slope * future_x + revenue_intercept)
            forecast_incomes.append(income_slope * future_x + income_intercept)

        return {
            "forecast_revenues": forecast_revenues,
            "forecast_net_incomes": forecast_incomes,
            "revenue_growth_rate": revenue_slope / np.mean(revenues),
            "profit_growth_rate": income_slope / np.mean(net_incomes),
            "confidence_intervals": {
                "revenue_r2": CPAMathematicalTools._calculate_r_squared(
                    revenues, x, revenue_slope, revenue_intercept
                ),
                "income_r2": CPAMathematicalTools._calculate_r_squared(
                    net_incomes, x, income_slope, income_intercept
                ),
            },
        }

    @staticmethod
    def _calculate_r_squared(
        y_true: list[float], x: np.ndarray, slope: float, intercept: float
    ) -> float:
        """R-squared 계산 헬퍼 함수"""
        y_pred = slope * x + intercept
        ss_res = np.sum((np.array(y_true) - y_pred) ** 2)
        ss_tot = np.sum((np.array(y_true) - np.mean(y_true)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    @staticmethod
    def analyze_risk_return_profile(
        investments: list[dict[str, float]], risk_free_rate: float = 0.03
    ) -> dict[str, float | list[dict]]:
        """
        투자 포트폴리오 리스크-수익 분석 (CPA 투자 분석)
        Rule 3.3: Statistical analysis 적용

        Args:
            investments: 투자 데이터 리스트
            risk_free_rate: 무위험 수익률

        Returns:
            포트폴리오 분석 결과
        """
        if not investments:
            raise ValueError("No investment data provided")

        # 데이터 추출
        returns = np.array([inv.get("expected_return", 0) for inv in investments])
        risks = np.array([inv.get("volatility", 0) for inv in investments])

        # 포트폴리오 메트릭 계산
        portfolio_return = np.mean(returns)
        portfolio_risk = np.sqrt(np.mean(risks**2))  # 단순 평균 변동성

        # 샤프 비율
        sharpe_ratio = (
            (portfolio_return - risk_free_rate) / portfolio_risk if portfolio_risk > 0 else 0
        )

        # 개별 투자 분석
        investment_analysis = []
        for i, inv in enumerate(investments):
            inv_return = inv.get("expected_return", 0)
            inv_risk = inv.get("volatility", 0)
            inv_sharpe = (inv_return - risk_free_rate) / inv_risk if inv_risk > 0 else 0

            investment_analysis.append(
                {
                    "name": inv.get("name", f"Investment {i + 1}"),
                    "expected_return": inv_return,
                    "volatility": inv_risk,
                    "sharpe_ratio": inv_sharpe,
                    "risk_adjusted_return": inv_return / inv_risk if inv_risk > 0 else 0,
                }
            )

        return {
            "portfolio_return": portfolio_return,
            "portfolio_risk": portfolio_risk,
            "sharpe_ratio": sharpe_ratio,
            "investment_analysis": investment_analysis,
            "recommendations": [
                "Diversify across uncorrelated assets",
                "Consider risk-adjusted returns over absolute returns",
                f"Current Sharpe ratio: {sharpe_ratio:.2f} ({'Excellent' if sharpe_ratio > 1.5 else 'Good' if sharpe_ratio > 1.0 else 'Needs improvement'})",
            ],
        }


# CPA Intelligence Enhancement Functions
# Rule 7.2: Avoid creating functions in loops 적용


def create_tax_optimization_function(
    tax_brackets: list[tuple[float, float]],
) -> callable[[float], float]:
    """
    세금 최적화 함수 생성 (함수 생성 비용 절감)
    Rule 7.2 적용: 루프에서 함수 생성 방지
    """
    # Pre-compute bracket boundaries to avoid complex indexing
    bracket_boundaries = []
    for i in range(len(tax_brackets)):
        boundary = tax_brackets[i + 1][0] if i + 1 < len(tax_brackets) else float("inf")
        bracket_boundaries.append(boundary)

    def calculate_tax(income: float) -> float:
        tax = 0.0
        remaining = income

        for i, (bracket_min, rate) in enumerate(tax_brackets):
            if remaining <= 0:
                break

            next_boundary = bracket_boundaries[i]
            taxable_in_bracket = min(remaining, next_boundary - bracket_min)
            tax += taxable_in_bracket * rate
            remaining -= taxable_in_bracket

        return tax

    return calculate_tax


def create_financial_ratio_calculator(required_ratios: list[str]) -> None:
    """
    재무 비율 계산기 생성 (빠른 조회를 위한 Map 활용)
    Rule 7.1 적용: Map/Set으로 빈번한 조회 최적화
    """
    ratio_calculators = {
        "current_ratio": lambda bs, _: (
            bs.get("current_assets", 0) / bs.get("current_liabilities", 0)
            if bs.get("current_liabilities", 0) > 0
            else 0
        ),
        "debt_ratio": lambda bs, _: (
            bs.get("total_liabilities", 0) / bs.get("total_assets", 0)
            if bs.get("total_assets", 0) > 0
            else 0
        ),
        "profit_margin": lambda bs, income: (
            income.get("net_income", 0) / income.get("total_revenue", 0)
            if income.get("total_revenue", 0) > 0
            else 0
        ),
        "return_on_equity": lambda bs, income: (
            income.get("net_income", 0) / bs.get("shareholders_equity", 0)
            if bs.get("shareholders_equity", 0) > 0
            else 0
        ),
    }

    def calculate_ratios(
        balance_sheet: dict[str, float], income_statement: dict[str, float]
    ) -> dict[str, float]:
        results = {}
        for ratio in required_ratios:
            if ratio in ratio_calculators:
                results[ratio] = ratio_calculators[ratio](balance_sheet, income_statement)
        return results

    return calculate_ratios


# Example usage demonstrating CPA mathematical enhancement
if __name__ == "__main__":
    # 감가상각 계산 예제
    tools = CPAMathematicalTools()

    # 컴퓨터 장비 감가상각 (5년, 직선법)
    depr_schedule = tools.calculate_depreciation_schedule(
        cost_basis=50000, salvage_value=5000, useful_life=5, method="straight_line"
    )
    print(f"Annual depreciation: ${depr_schedule['schedule'][0]['depreciation']:,.2f}")

    # 세금 최적화 분석
    tax_brackets = [(0, 0.10), (10000, 0.12), (40000, 0.22), (90000, 0.24)]
    tax_analysis = tools.optimize_tax_strategy(
        income=75000,
        deductions=[12500, 2000],  # 표준공제 + 기부금
        tax_brackets=tax_brackets,
    )
    print(f"Current tax: ${tax_analysis['current_tax']:,.2f}")
    print(f"Effective tax rate: {tax_analysis['effective_rate']:.1%}")

    # 재무 비율 분석
    balance_sheet = {
        "current_assets": 150000,
        "current_liabilities": 80000,
        "total_assets": 500000,
        "total_liabilities": 200000,
        "shareholders_equity": 300000,
    }

    income_statement = {"total_revenue": 400000, "net_income": 60000}

    ratios = tools.calculate_financial_ratios(balance_sheet, income_statement)
    print(f"Current ratio: {ratios.get('current_ratio', 0):.2f}")
    print(f"Profit margin: {ratios.get('profit_margin', 0):.1%}")

    print("\n✅ CPA Mathematical Tools initialized - Intelligence enhanced! 🚀")
