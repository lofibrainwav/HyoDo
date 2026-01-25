# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Julie CPA - Budget Models
Phase 12 Extension: 예산 추적 및 리스크 연동

"금고가 튼튼해야 왕국이 번영한다" — 本立道生
"""

from pydantic import BaseModel, Field


class BudgetCategory(BaseModel):
    """예산 카테고리 모델"""

    id: int | None = None
    category: str = Field(..., description="예산 카테고리명")
    allocated: int = Field(..., description="할당된 금액 (KRW)")
    spent: int = Field(default=0, description="지출된 금액")
    remaining: int = Field(default=0, description="잔여 금액")

    def calculate_remaining(self) -> int:
        """잔여 예산 자동 계산"""
        self.remaining = self.allocated - self.spent
        return self.remaining

    def utilization_rate(self) -> float:
        """예산 사용률 (0-100%)"""
        if self.allocated == 0:
            return 0.0
        return (self.spent / self.allocated) * 100


class BudgetSummary(BaseModel):
    """예산 요약 (API 응답용)"""

    budgets: list[BudgetCategory]
    total_allocated: int
    total_spent: int
    total_remaining: int
    utilization_rate: float  # 전체 예산 사용률
    risk_score: float  # SSOT 연동 리스크 점수 (0-100)
    risk_level: str  # "safe" | "warning" | "critical"
    summary: str  # Julie의 한줄 평가
    timestamp: str


class BudgetUpdate(BaseModel):
    """예산 업데이트 요청"""

    category: str
    amount: int  # 양수: 지출, 음수: 환불/조정
    description: str | None = None
    dry_run: bool = True  # 善: 안전 우선


# Mock 데이터 (In-Memory, 추후 DB 연동)
MOCK_BUDGETS: list[BudgetCategory] = [
    BudgetCategory(id=1, category="인프라 (AWS/GCP)", allocated=500000, spent=245000),
    BudgetCategory(id=2, category="구독 서비스", allocated=100000, spent=67000),
    BudgetCategory(id=3, category="식비/회식", allocated=300000, spent=189000),
    BudgetCategory(id=4, category="교통비", allocated=150000, spent=78000),
    BudgetCategory(id=5, category="AI API 크레딧", allocated=200000, spent=156000),
]

# 잔여 금액 자동 계산
for budget in MOCK_BUDGETS:
    budget.calculate_remaining()
