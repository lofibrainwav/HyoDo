# Trinity Score: 90.0 (Established by Chancellor)
# packages/afo-core/domain/transaction.py
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class Transaction(BaseModel):
    id: str
    amount: float
    description: str
    date: datetime
    category: str | None = None
    source: str = "manual"

    @classmethod
    def mock(cls) -> "Transaction":
        """Create a mock transaction for testing."""
        return cls(
            id="mock-tx-1",
            amount=15000.0,
            description="점심 식사 (Mock)",
            date=datetime.now(),
            category="식비",
            source="dry_run",
        )

    @classmethod
    def from_raw(cls, data: dict[str, Any]) -> "Transaction":
        """Create a transaction from raw dictionary data."""
        try:
            return cls(**data)
        except Exception as e:
            print(f"[ERROR] Transaction.from_raw failed: {e}")
            raise
