# Trinity Score: 90.0 (Established by Chancellor)
# packages/afo-core/julie_cpa/core/julie_engine.py
# Julie CPA AutoMate 메인 엔진 (Precision Upgrade)
# AntiGravity: 비용 최적화(Truth), 권한 검증(Goodness), 지속 아키텍처(Eternity)

from abc import ABC, abstractmethod
from decimal import Decimal, getcontext

from AFO.security.vault_manager import vault as vault_manager
from services.trinity_calculator import trinity_calculator

# Set Decimal Precision
getcontext().prec = 28

# Assuming llm_router import logic remains similar or we mock it
try:
    from services.llm_router import llm_router
except ImportError:

    class MockRouter:
        async def ask(self, prompt, context=None, model_priority=None):
            return "Mock LLM Response"

    llm_router = MockRouter()


# ==========================================
# Command Pattern for Financial Operations
# ==========================================


class FinancialCommand(ABC):
    @abstractmethod
    def execute(self) -> bool:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass


class AdjustBudgetCommand(FinancialCommand):
    def __init__(self, cpa: "JulieCPA", amount: Decimal) -> None:
        self.cpa = cpa
        self.amount = amount
        self.previous_limit = Decimal("0.00")

    def execute(self) -> bool:
        self.previous_limit = self.cpa.budget_limit
        self.cpa.budget_limit = self.amount
        print(f"💰 [Julie] Budget Adjusted: ${self.previous_limit} -> ${self.amount}")
        return True

    def undo(self) -> None:
        print(f"↩️ [Julie] Undo Budget Adjustment. Reverting to ${self.previous_limit}")
        self.cpa.budget_limit = self.previous_limit


# ==========================================
# Julie CPA Engine (Precision)
# ==========================================


class JulieCPA:
    """Julie CPA AutoMate - 의(義)의 기술
    재정적 자유와 절대적 정확성을 위한 자동 회계·세무 엔진
    """

    def __init__(self) -> None:
        # Vault 동적 조회
        self.openai_key = vault_manager.get_secret("OPENAI_API_KEY", "mock-key")

        # Financial State (Decimal for Precision)
        self.monthly_spending = Decimal("4200.00")
        self.budget_limit = Decimal("3500.00")
        self.tax_risk_score = 85

        self.command_history: list[FinancialCommand] = []

    async def execute_command(self, command: FinancialCommand) -> bool:
        """Trinity Gated Execution"""
        # 1. Calculate Trinity Score to approve action
        # Mocking raw scores for this action context - ideally dynamic
        raw_scores = [1.0, 1.0, 1.0, 1.0, 1.0]
        # Check Risk Gate (Goodness)
        if self.tax_risk_score > 90:
            # If too risky, Goodness pillar might fail
            raw_scores[1] = 0.0

        trinity_score = trinity_calculator.calculate_trinity_score(raw_scores)

        if trinity_score < 70.0:
            print(f"⛔ [Julie] Trinity Score Too Low ({trinity_score}). Action Blocked.")
            return False

        # 2. Execute
        success = command.execute()
        if success:
            self.command_history.append(command)
            return True
        return False

    async def undo_last_command(self):
        if self.command_history:
            cmd = self.command_history.pop()
            cmd.undo()
        else:
            print("⚠️ [Julie] No commands to undo.")

    async def risk_alert(self) -> list[str]:
        """초과 지출·세금 위험 실시간 알림"""
        alerts = []
        if self.monthly_spending > self.budget_limit * Decimal("1.2"):
            alerts.append("⚠️ Monthly burn rate > 20% over budget (LA Life)")
        if self.tax_risk_score > 80:
            alerts.append("🔴 IRS Audit Risk High - Check 1099s immediately")
        return alerts

    async def ask(self, question: str) -> str:
        """Consult Julie with a question (Context-Aware).

        Uses Context7 to retrieve relevant Kingdom knowledge (PDFs, docs)
        and provides a grounded answer.
        """
        print(f"🤔 [Julie] Thinking about: '{question}'...")

        # 1. Retrieve Context via Context7
        from AFO.context7 import Context7Manager

        context_mgr = Context7Manager()
        context_items = await context_mgr.get_relevant_context(question)

        if context_items:
            print(f"📚 [Julie] Found {len(context_items)} relevant records.")

            print(f"📚 [Julie] Found {len(context_items)} relevant records.")
            for i, item in enumerate(context_items):
                print(
                    f"[Record {i + 1}: {item['source']}]\n{item['content'][:100]}..."
                )  # Log preview instead of full string
        else:
            print("🤷‍♀️ [Julie] No internal records found. Using general knowledge.")

        # 2. Consult LLM (using simple RAG construction for now, typically LLMRouter)
        # We can reuse RAGService logic or the LLM Router.
        # Since RAGService already does Retrieval+Gen, arguably Julie could just delegate to RAGService.
        # BUT, the plan was "Enlighten Julie". Let's stick to the architecture where Julie uses Context7.
        # Ideally Julie uses LLMRouter with the context.

        from AFO.services.rag_service import rag_service
        # Actually RAGService.ask() does exactly what we want (Search + Answer).
        # Context7 was just the "Search" part.
        # Julie is the "Agent".
        # So Julie can use RAGService.ask() which internally uses VectorMemory.
        # OR Julie constructs the prompt herself.
        # Let's use RAGService for the heavy lifting to keep Julie clean.

        result = await rag_service.ask(question)
        answer = result["answer"]

        print(f"🗣️ [Julie] Answer: {answer[:100]}...")
        return answer

    async def analyze_irs_records(self, year: int) -> str:
        """Fetches and analyzes IRS transcripts for the given year."""
        print(f"📡 [Julie] Connecting to IRS for Tax Year {year}...")

        from AFO.services.irs_client import irs_client

        transcript = await irs_client.get_transcript(year)

        if "error" in transcript:
            return f"❌ Could not access IRS records: {transcript['error']}"

        # Analysis Logic
        print("🧐 [Julie] Analyzing Transcript Data...")

        # We can use RAG here too!
        # "What does IRS Code 846 mean?" -> RAG -> "Refund Issued"
        # For now, let's do a structured summary + RAG insight if possible.

        # 1. Structure Summary
        summary = (
            f"**Tax Year {year} Transcript Analysis**\n"
            f"- Filing Status: {transcript.get('filingStatus')}\n"
            f"- AGI: ${transcript.get('adjustedGrossIncome', 0):,}\n"
            f"- Total Tax: ${transcript.get('totalTax', 0):,}\n"
            f"- Refunds/Credits: Noted.\n\n"
        )

        transactions = transcript.get("transactions", [])
        refund = next((t for t in transactions if t["code"] == "846"), None)

        if refund:
            summary += f"✅ **GOOD NEWS**: I found Transaction 846 (Refund Issued) for ${abs(refund['amount']):,}. Date: {refund['date']}\n"
        else:
            summary += "ℹ️ No refund issued yet.\n"

        return summary


# Singleton Instance
julie = JulieCPA()
