"""
Financial Metrics Service for Royal Treasury (Phase 60)
Provides income/expense analytics, category breakdowns, and trend data.
"""

import random
from datetime import datetime, timedelta
from typing import Any


class TreasuryService:
    """Provides financial metrics and analytics for the Julie CPA Dashboard."""

    def __init__(self) -> None:
        # Mock data - in production, this would come from QuickBooks/database
        self._generate_mock_data()

    def _generate_mock_data(self) -> None:
        """Generate realistic mock financial data."""
        self.transactions = []
        categories_income = ["Consulting", "Product Sales", "Royalties", "Investments"]
        categories_expense = ["Office", "Software", "Marketing", "Payroll", "Utilities", "Travel"]

        # Generate 6 months of data
        for month_offset in range(6):
            month_date = datetime.now() - timedelta(days=30 * month_offset)

            # Income transactions
            for _ in range(random.randint(3, 8)):
                self.transactions.append(
                    {
                        "id": f"TXN-{len(self.transactions):04d}",
                        "date": month_date.strftime("%Y-%m-%d"),
                        "type": "income",
                        "category": random.choice(categories_income),
                        "amount": round(random.uniform(5000, 50000), 2),
                        "description": f"Revenue - {random.choice(categories_income)}",
                    }
                )

            # Expense transactions
            for _ in range(random.randint(5, 12)):
                self.transactions.append(
                    {
                        "id": f"TXN-{len(self.transactions):04d}",
                        "date": month_date.strftime("%Y-%m-%d"),
                        "type": "expense",
                        "category": random.choice(categories_expense),
                        "amount": round(random.uniform(500, 15000), 2),
                        "description": f"Expense - {random.choice(categories_expense)}",
                    }
                )

    def get_summary(self) -> dict[str, Any]:
        """Get overall financial summary."""
        total_income = sum(t["amount"] for t in self.transactions if t["type"] == "income")
        total_expense = sum(t["amount"] for t in self.transactions if t["type"] == "expense")
        net_income = total_income - total_expense

        return {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "net_income": round(net_income, 2),
            "profit_margin": round((net_income / total_income * 100) if total_income > 0 else 0, 1),
            "transaction_count": len(self.transactions),
            "period": "Last 6 Months",
        }

    def get_category_breakdown(self) -> dict[str, Any]:
        """Get income and expense breakdown by category."""
        income_by_cat: dict[str, float] = {}
        expense_by_cat: dict[str, float] = {}

        for t in self.transactions:
            if t["type"] == "income":
                income_by_cat[t["category"]] = income_by_cat.get(t["category"], 0) + t["amount"]
            else:
                expense_by_cat[t["category"]] = expense_by_cat.get(t["category"], 0) + t["amount"]

        return {
            "income_categories": [
                {"category": k, "amount": round(v, 2)}
                for k, v in sorted(income_by_cat.items(), key=lambda x: -x[1])
            ],
            "expense_categories": [
                {"category": k, "amount": round(v, 2)}
                for k, v in sorted(expense_by_cat.items(), key=lambda x: -x[1])
            ],
        }

    def get_monthly_trend(self) -> dict[str, Any]:
        """Get monthly income/expense trend data for charting."""
        monthly_data: dict[str, dict[str, float]] = {}

        for t in self.transactions:
            month_key = t["date"][:7]  # YYYY-MM
            if month_key not in monthly_data:
                monthly_data[month_key] = {"income": 0, "expense": 0}

            if t["type"] == "income":
                monthly_data[month_key]["income"] += t["amount"]
            else:
                monthly_data[month_key]["expense"] += t["amount"]

        # Sort by month
        sorted_months = sorted(monthly_data.keys())

        return {
            "labels": sorted_months,
            "income": [round(monthly_data[m]["income"], 2) for m in sorted_months],
            "expense": [round(monthly_data[m]["expense"], 2) for m in sorted_months],
            "net": [
                round(monthly_data[m]["income"] - monthly_data[m]["expense"], 2)
                for m in sorted_months
            ],
        }

    def get_tax_forecast(self, annual_income: float | None = None) -> dict[str, Any]:
        """Calculate tax forecast based on current trend."""
        summary = self.get_summary()
        self.get_monthly_trend()

        # Project annual income based on 6-month data
        if annual_income is None:
            monthly_avg_income = summary["total_income"] / 6
            projected_annual = monthly_avg_income * 12
        else:
            projected_annual = annual_income

        monthly_avg_expense = summary["total_expense"] / 6
        projected_expenses = monthly_avg_expense * 12

        # Tax calculation (simplified)
        taxable_income = projected_annual - projected_expenses

        # Federal tax brackets (2026 estimate)
        federal_tax = self._calculate_federal_tax(taxable_income)
        state_tax = taxable_income * 0.0725  # CA flat estimate

        return {
            "projected_annual_income": round(projected_annual, 2),
            "projected_annual_expenses": round(projected_expenses, 2),
            "taxable_income": round(max(taxable_income, 0), 2),
            "estimated_federal_tax": round(federal_tax, 2),
            "estimated_state_tax": round(state_tax, 2),
            "total_estimated_tax": round(federal_tax + state_tax, 2),
            "effective_rate": round(
                (federal_tax + state_tax) / taxable_income * 100 if taxable_income > 0 else 0, 1
            ),
            "quarterly_estimate": round((federal_tax + state_tax) / 4, 2),
        }

    def _calculate_federal_tax(self, income: float) -> float:
        """Calculate federal tax using 2026 brackets (simplified)."""
        if income <= 0:
            return 0

        brackets = [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            (191950, 0.24),
            (243725, 0.32),
            (609350, 0.35),
            (float("inf"), 0.37),
        ]

        tax = 0
        prev_limit = 0

        for limit, rate in brackets:
            if income <= prev_limit:
                break
            taxable_in_bracket = min(income, limit) - prev_limit
            tax += taxable_in_bracket * rate
            prev_limit = limit

        return tax


# Singleton instance
_treasury_service: TreasuryService | None = None


def get_treasury_service() -> TreasuryService:
    """Get or create the treasury service singleton."""
    global _treasury_service
    if _treasury_service is None:
        _treasury_service = TreasuryService()
    return _treasury_service
