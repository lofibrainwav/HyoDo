# Trinity Score: 90.0 (Established by Chancellor)
import asyncio
import random
from typing import Any

from AFO.julie_cpa.config import julie_config


class FinancialConnector:
    """[Three Kingdoms #14 & #21]
    Resilient Connector for External Financial APIs (Mocked).
    Implements Retry (Three Visits) and Circuit Breaker (Bitter Meat).
    """

    def __init__(self) -> None:
        self._circuit_open = False
        self._failure_count = 0
        self._threshold = julie_config.MAX_RETRIES

    async def fetch_bank_data(self, account_id: str) -> dict[str, Any]:
        """[Three Kingdoms #14: Three Visits]
        Retries up to 3 times before giving up.
        """
        if self._circuit_open:
            print("⚡ [Circuit Breaker] Open! Skipping request to protect system.")
            return {"error": "Circuit Open"}

        for attempt in range(1, julie_config.MAX_RETRIES + 1):
            try:
                print(
                    f"🔄 [Attempt {attempt}/{julie_config.MAX_RETRIES}] Connecting to Bank for {account_id}..."
                )
                data = await self._mock_api_call(account_id)
                self._success()
                return data
            except Exception as e:
                print(f"⚠️ Connection Failed: {e}")
                await asyncio.sleep(
                    julie_config.RETRY_BACKOFF_FACTOR * attempt
                )  # Exponential Backoff

        self._record_failure()
        return {"error": "Max Retries Exceeded"}

    async def _mock_api_call(self, account_id: str) -> dict[str, Any]:
        # Simulate Network Flakiness (Fog of War) - Reduced failure rate for stability
        if random.random() < 0.05:  # Reduced from 30% to 5% for better stability
            raise ConnectionError("Network Glitch")

        # Add small delay to simulate network latency
        await asyncio.sleep(0.1)

        return {
            "account_id": account_id,
            "balance": 1000000,
            "currency": "KRW",
            "status": "ACTIVE",
        }

    async def fetch_dashboard_data(self, account_id: str) -> dict[str, Any]:
        """[Dynamic Simulation Layer]
        Fetches consolidated dashboard data.
        In Phase 2, this simulates a real aggregator response.
        """
        # Fetch basic bank status first
        bank_status = await self.fetch_bank_data(account_id)
        if "error" in bank_status:
            return bank_status

        # Simulate dynamic dashboard metrics
        return self._simulate_financial_data(account_id)

    def _simulate_financial_data(self, account_id: str) -> dict[str, Any]:
        """Generates realistic-looking financial data for the dashboard.
        Simulates:
        - Monthly Spending (Randomized around base)
        - Budget Remaining
        - Recent Transactions (Random mix)
        """
        # Base figures (Simulated volatility)
        base_spending = 2450000
        volatility = random.uniform(0.9, 1.1)
        monthly_spending = int(base_spending * volatility)

        total_budget = 3000000
        budget_remaining = max(0, total_budget - monthly_spending)

        # Generate random recent transactions
        transactions = []
        merchants = [
            ("Netflix", 17000, "Subscription"),
            ("Starbucks", 9800, "Food"),
            ("AWS", 45000, "Infrastructure"),
            ("Coupang", 28500, "Shopping"),
            ("Uber", 15200, "Transport"),
            ("Spotify", 11900, "Subscription"),
        ]

        # Pick 3-4 random transactions
        daily_sample = random.sample(merchants, k=random.randint(3, 5))
        for _i, (name, amount, cat) in enumerate(daily_sample):
            transactions.append(
                {
                    "id": f"tx-{random.randint(1000, 9999)}",
                    "merchant": name,
                    "amount": amount,
                    "date": "2024-12-26",  # Fixed for demo, or use datetime.now()
                    "category": cat,
                }
            )

        return {
            "account_id": account_id,
            "monthly_spending": monthly_spending,
            "budget_remaining": budget_remaining,
            "recent_transactions": transactions,
            "risk_alerts": self._generate_dynamic_alerts(monthly_spending, total_budget),
        }

    def _generate_dynamic_alerts(self, spending: int, budget: int) -> list[dict[str, str]]:
        alerts = []
        utilization = (spending / budget) * 100

        if utilization > 90:
            alerts.append({"level": "critical", "message": "Budget Critical (>90%)"})
        elif utilization > 80:
            alerts.append({"level": "warning", "message": "Budget Utilization > 80%"})
        else:
            alerts.append({"level": "info", "message": "Spending on track"})

        if random.random() < 0.3:
            alerts.append({"level": "warning", "message": "Unusual subscription detected"})

        return alerts

    def _record_failure(self) -> None:
        self._failure_count += 1
        if self._failure_count >= self._threshold:
            self._circuit_open = True
            print("💥 [Circuit Breaker] Threshold reached. Opening Circuit.")

    def _success(self) -> None:
        self._failure_count = 0
        self._circuit_open = False
