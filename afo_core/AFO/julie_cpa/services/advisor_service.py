"""
Julie AI Advisor - Tax Question Answering Service (Phase 61)
Provides intelligent responses to tax and financial questions.
"""

from datetime import datetime
from typing import Any


class JulieAdvisorService:
    """AI-powered tax and financial advisor for Julie CPA Portal."""

    def __init__(self) -> None:
        self.conversation_history: list[dict[str, str]] = []
        self._load_knowledge_base()

    def _load_knowledge_base(self) -> None:
        """Load tax knowledge base for Q&A."""
        self.knowledge_base = {
            # Federal Tax Questions
            "standard_deduction": {
                "keywords": ["standard deduction", "deduction amount", "itemized"],
                "answer": "For 2026, the standard deduction is $14,600 for Single filers, $29,200 for Married Filing Jointly, and $21,900 for Head of Household. You should itemize only if your deductions exceed these amounts.",
            },
            "tax_brackets": {
                "keywords": ["tax bracket", "tax rate", "how much tax"],
                "answer": "2026 Federal Tax Brackets for Single: 10% ($0-11,600), 12% ($11,601-47,150), 22% ($47,151-100,525), 24% ($100,526-191,950), 32% ($191,951-243,725), 35% ($243,726-609,350), 37% (over $609,350).",
            },
            "qbi_deduction": {
                "keywords": ["qbi", "qualified business income", "self-employed", "199a"],
                "answer": "The QBI (Qualified Business Income) deduction under Section 199A allows eligible self-employed taxpayers to deduct up to 20% of their qualified business income. Subject to income limitations: $182,100 for Single, $364,200 for MFJ.",
            },
            "estimated_taxes": {
                "keywords": ["estimated tax", "quarterly", "self-employment"],
                "answer": "Self-employed individuals must pay estimated taxes quarterly (Apr 15, Jun 15, Sep 15, Jan 15). Pay at least 90% of current year tax or 100% of prior year tax (110% if AGI > $150k) to avoid penalties.",
            },
            "capital_gains": {
                "keywords": ["capital gains", "stock sale", "investment tax"],
                "answer": "Long-term capital gains (assets held >1 year) are taxed at 0%, 15%, or 20% depending on income. Short-term gains are taxed as ordinary income. The NIIT (3.8%) applies to investment income for high earners.",
            },
            "home_office": {
                "keywords": ["home office", "work from home", "home deduction"],
                "answer": "Home office deduction: Simplified method is $5/sq ft up to 300 sq ft ($1,500 max). Regular method calculates actual expenses proportionally. Space must be used regularly and exclusively for business.",
            },
            # California Tax Questions
            "california_tax": {
                "keywords": ["california", "state tax", "ca tax"],
                "answer": "California has progressive tax rates from 1% to 13.3%. There's no capital gains preference - all gains taxed as ordinary income. Mental Health Services Tax adds 1% on income over $1M. SDI (State Disability Insurance) is 1.1% on first $153,164.",
            },
            # IRS Questions
            "irs_audit": {
                "keywords": ["audit", "irs letter", "notice"],
                "answer": "If you receive an IRS notice: 1) Don't panic - most are routine, 2) Read carefully and note response deadline, 3) Keep copies of everything, 4) Respond promptly with requested documentation, 5) Consider consulting a CPA for complex issues.",
            },
            "extension": {
                "keywords": ["extension", "file late", "more time"],
                "answer": "Form 4868 gives an automatic 6-month extension to file (Oct 15). IMPORTANT: This extends filing time only, NOT payment time. You must still pay 90% of tax owed by April 15 to avoid penalties.",
            },
            "retirement": {
                "keywords": ["401k", "ira", "retirement", "roth"],
                "answer": "2026 Contribution Limits: 401(k) $23,000 ($30,500 if 50+), Traditional/Roth IRA $7,000 ($8,000 if 50+). Traditional IRA may be tax-deductible; Roth IRA contributions aren't deductible but qualified withdrawals are tax-free.",
            },
        }

    def ask(self, question: str) -> dict[str, Any]:
        """Process a tax/financial question and return an answer."""
        question_lower = question.lower()
        timestamp = datetime.now().isoformat()

        # Find best matching answer
        best_match = None
        max_score = 0

        for topic, data in self.knowledge_base.items():
            score = sum(1 for kw in data["keywords"] if kw in question_lower)
            if score > max_score:
                max_score = score
                best_match = data

        if best_match and max_score > 0:
            answer = best_match["answer"]
            confidence = min(0.95, 0.5 + (max_score * 0.15))
        else:
            answer = self._generate_fallback_response(question)
            confidence = 0.3

        # Add to conversation history
        self.conversation_history.append(
            {"role": "user", "content": question, "timestamp": timestamp}
        )
        self.conversation_history.append(
            {"role": "assistant", "content": answer, "timestamp": timestamp}
        )

        # Keep last 20 messages
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        return {
            "question": question,
            "answer": answer,
            "confidence": round(confidence, 2),
            "sources": ["IRS Publication 17", "California FTB", "Julie CPA Knowledge Base"],
            "disclaimer": "This is general tax guidance. Consult a licensed CPA for advice specific to your situation.",
            "timestamp": timestamp,
        }

    def _generate_fallback_response(self, question: str) -> str:
        """Generate a fallback response for unknown questions."""
        return (
            "I don't have specific information about that tax topic in my knowledge base. "
            "For personalized advice, I recommend: 1) Checking IRS.gov for official guidance, "
            "2) Using IRS Publication 17 for general tax information, or "
            "3) Consulting with a licensed CPA for complex situations. "
            "Is there a related topic I can help you with?"
        )

    def get_insights(self, income: float, filing_status: str = "single") -> dict[str, Any]:
        """Generate personalized financial insights based on income."""
        insights = []

        # QBI Insight
        qbi_limit = 182100 if filing_status.lower() == "single" else 364200
        if income < qbi_limit:
            insights.append(
                {
                    "type": "deduction",
                    "title": "QBI Deduction Available",
                    "description": f"Your income (${income:,.0f}) qualifies for the full 20% QBI deduction. Potential savings: ${income * 0.20 * 0.24:,.0f}",
                    "priority": "high",
                }
            )

        # Retirement Contribution Insight
        if income > 100000:
            insights.append(
                {
                    "type": "planning",
                    "title": "Max Out Retirement Contributions",
                    "description": "Consider maxing your 401(k) contributions ($23,000) to reduce taxable income and save for retirement.",
                    "priority": "high",
                }
            )

        # Estimated Tax Insight
        if income > 50000:
            quarterly_estimate = income * 0.25 / 4
            insights.append(
                {
                    "type": "compliance",
                    "title": "Estimated Tax Reminder",
                    "description": f"If self-employed, pay quarterly estimates of ~${quarterly_estimate:,.0f} to avoid penalties.",
                    "priority": "medium",
                }
            )

        # California Mental Health Tax
        if income > 1000000:
            insights.append(
                {
                    "type": "planning",
                    "title": "California Mental Health Tax",
                    "description": "Income over $1M is subject to additional 1% Mental Health Services Tax. Consider timing of income recognition.",
                    "priority": "medium",
                }
            )

        # Standard vs Itemized
        if 15000 < income < 150000:
            insights.append(
                {
                    "type": "deduction",
                    "title": "Deduction Strategy",
                    "description": "Review whether itemizing (mortgage interest, SALT up to $10k, charitable) exceeds the standard deduction.",
                    "priority": "medium",
                }
            )

        return {
            "income": income,
            "filing_status": filing_status,
            "insights": insights,
            "insight_count": len(insights),
            "generated_at": datetime.now().isoformat(),
        }

    def get_conversation_history(self) -> list[dict[str, str]]:
        """Return conversation history for context."""
        return self.conversation_history


# Singleton instance
_advisor_service: JulieAdvisorService | None = None


def get_advisor_service() -> JulieAdvisorService:
    """Get or create the advisor service singleton."""
    global _advisor_service
    if _advisor_service is None:
        _advisor_service = JulieAdvisorService()
    return _advisor_service
