# Trinity Score: 90.0 (Established by Chancellor)
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from AFO.julie_cpa.config import julie_config


class FinancialTransaction(BaseModel):
    """[The Prince #25: Feared > Loved]
    Strict Model for Financial Transactions.
    Immutability and rigorous validation are enforced.
    """

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    transaction_id: str = Field(
        ..., min_length=julie_config.MIN_TX_ID_LENGTH, description="Unique ID"
    )
    timestamp: datetime = Field(default_factory=datetime.now)
    amount: Decimal = Field(..., description="Transaction Amount")
    currency: Literal["USD", "KRW"] = Field("KRW", description="Currency Code")
    category: str = Field(..., min_length=2, description="Expense Category")
    description: str = Field(
        ..., min_length=julie_config.MIN_DESC_LENGTH, description="Transaction Details"
    )
    status: Literal["PENDING", "CLEARED", "REJECTED"] = "PENDING"

    # Audit Trail (The Prince #09: Use of Spies)
    audit_hash: str | None = Field(None, description="Cryptographic Checksum")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v == 0:
            raise ValueError("Transaction amount cannot be zero (Fog of War detected).")
        return v


class BudgetPlan(BaseModel):
    """[Sun Tzu #1: Laying Plans]
    Budget Plan Model.
    """

    month: str = Field(..., pattern=r"^\d{4}-\d{2}$")  # YYYY-MM
    limit_amount: Decimal = Field(..., gt=0)
    current_usage: Decimal = Field(default=Decimal("0.0"))

    @property
    def utilization_rate(self) -> float:
        if self.limit_amount == 0:
            return 0.0
        return float(self.current_usage / self.limit_amount) * 100
