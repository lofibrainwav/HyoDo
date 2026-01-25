# Trinity Score: 90.0 (Established by Chancellor)
import random
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Transaction:
    id: str
    date: datetime
    amount: Decimal
    merchant: str
    category: str = "Uncategorized"

    @staticmethod
    def mock() -> "Transaction":
        """Generate a mock transaction for DRY_RUN"""
        amounts = [
            Decimal("10.50"),
            Decimal("4.25"),
            Decimal("100.00"),
            Decimal("42.99"),
        ]
        merchants = ["Starbucks", "Uber", "Amazon", "K-Town Market"]
        return Transaction(
            id=f"txn_{random.randint(1000, 9999)}",
            date=datetime.now(),
            amount=random.choice(amounts),
            merchant=random.choice(merchants),
        )
