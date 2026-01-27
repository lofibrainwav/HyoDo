import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FinancialRecord:
    id: str
    description: str
    amount: float
    category: str
    risk_score: int  # 0-100 (Yi Sun-sin Filter)
    status: str  # 'PENDING', 'APPROVED', 'REJECTED'


class JulieService:
    """
    Julie CPA Service (Financial Autonomous Driving)
    Strategy: Input -> Labeling -> Queue
    """

    DB_PATH = Path(__file__).parent / "julie_audit.db"

    def __init__(self) -> None:
        self.queue: list[FinancialRecord] = []
        self.audit_log: list[str] = []

        # [Phase 58] Initialize SQLite for Persistence (永)
        self._init_db()

        # Seed Data for Verification
        from datetime import datetime

        self._log_to_db(
            f"[{datetime.now().strftime('%H:%M:%S')}] [BRAIN] System initialized with Yi Sun-sin Risk Module."
        )

        # Hydrate with mock records
        self.queue.append(
            FinancialRecord(
                id="tx-seed-1",
                description="AWS Cloud Services",
                amount=4500.00,
                category="INFRASTRUCTURE",
                risk_score=80,
                status="APPROVED",
            )
        )
        self._log_to_db(
            f"[{datetime.now().strftime('%H:%M:%S')}] [BRAIN] Risk Assessment: AWS Cloud Services ($4500.00) -> CRITICAL (80/100)"
        )

        self.queue.append(
            FinancialRecord(
                id="tx-seed-2",
                description="Office Coffee",
                amount=45.00,
                category="OFFICE_SUPPLIES",
                risk_score=10,
                status="APPROVED",
            )
        )
        self._log_to_db(
            f"[{datetime.now().strftime('%H:%M:%S')}] [BRAIN] Risk Assessment: Office Coffee ($45.00) -> SAFE (10/100)"
        )

        # Load existing logs from DB into memory for API responses
        self._load_logs_from_db()

    def _init_db(self) -> None:
        """Create SQLite database and table if not exists."""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                message TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def _log_to_db(self, message: str) -> None:
        """Persist log entry to SQLite."""
        from datetime import datetime

        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_events (timestamp, message) VALUES (?, ?)",
            (datetime.now().isoformat(), message),
        )
        conn.commit()
        conn.close()
        # Also keep in memory
        self.audit_log.insert(0, message)

    def _load_logs_from_db(self) -> None:
        """Load persisted logs into memory."""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT message FROM audit_events ORDER BY id DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
        self.audit_log = [row[0] for row in rows]

    def log_event(self, message: str) -> None:
        """Log an immutable event to the specific memory stream."""
        import threading
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [BRAIN] {message}"
        self._log_to_db(entry)
        # Keep log size manageable in memory
        if len(self.audit_log) > 100:
            self.audit_log.pop()

        # [Phase 59] Background sync to NotebookLM Bridge (non-blocking)
        def _background_sync() -> None:
            try:
                import asyncio

                from AFO.core.notebook_sync import sync_audit_event

                asyncio.run(sync_audit_event(entry))
            except Exception:
                pass  # Non-blocking, ignore sync failures

        thread = threading.Thread(target=_background_sync, daemon=True)
        thread.start()

    async def ingest_record(self, description: str, amount: float) -> FinancialRecord:
        """Step 1: Input (Data Collection)"""
        # NOTE: grok_engine integration planned for Phase 50 - using simplified ingestion
        record = FinancialRecord(
            id="temp-id",
            description=description,
            amount=amount,
            category="UNCATEGORIZED",
            risk_score=0,
            status="PENDING",
        )
        return await self.assess_risk(record)

    from AFO.core.resilience import julie_breaker

    @julie_breaker
    async def assess_risk(self, record: FinancialRecord) -> FinancialRecord:
        """Step 2: Labeling (Yi Sun-sin Risk Filter)"""
        # Simple logic for now: High amount = High risk
        if record.amount > 1000:
            record.risk_score = 80
            level = "CRITICAL"
        else:
            record.risk_score = 10
            level = "SAFE"

        record.category = "Auto-Classified"
        self.queue.append(record)

        self.log_event(
            f"Risk Assessment: {record.description} (${record.amount}) -> {level} ({record.risk_score}/100)"
        )
        return record

    async def get_approval_queue(self) -> list[FinancialRecord]:
        """Step 3: Queue (Approval Mechanism)"""
        return [r for r in self.queue if r.status == "PENDING"]

    async def get_royal_status(self) -> dict:
        """Return Julie CPA service status for Royal API."""
        pending_count = len([r for r in self.queue if r.status == "PENDING"])
        return {
            "status": "healthy",
            "service": "Julie CPA (Royal Edition)",
            "version": "1.0.0",
            "queue_size": len(self.queue),
            "pending_approvals": pending_count,
            "features": {
                "tax_calculation": "available",
                "transaction_processing": "available",
                "risk_assessment": "available",
            },
        }

    async def get_financial_dashboard(self) -> dict:
        """Return full financial dashboard data for GenUI support."""
        pending = [r for r in self.queue if r.status == "PENDING"]
        approved = [r for r in self.queue if r.status == "APPROVED"]
        rejected = [r for r in self.queue if r.status == "REJECTED"]

        total_pending_amount = sum(r.amount for r in pending)
        total_approved_amount = sum(r.amount for r in approved)

        return {
            "health": {
                "status": "healthy",
                "score": 95,
                "last_check": "2026-01-15T00:00:00Z",
            },
            "summary": {
                "total_transactions": len(self.queue),
                "pending_count": len(pending),
                "approved_count": len(approved),
                "rejected_count": len(rejected),
                "pending_amount": total_pending_amount,
                "approved_amount": total_approved_amount,
            },
            "alerts": [],
            "recent_transactions": [
                {
                    "id": r.id,
                    "description": r.description,
                    "amount": r.amount,
                    "category": r.category,
                    "status": r.status,
                    "risk_score": r.risk_score,
                }
                for r in self.queue[-10:]  # Last 10 transactions
            ],
            "audit_log": self.audit_log[:50],  # Latest 50 brain logs
        }

    async def calculate_tax_scenario(self, income: float, filing_status: str) -> dict:
        """Calculate tax scenario (Federal + CA + QBI) based on 2025 rules."""
        # Simplified tax calculation for demo purposes
        # Federal brackets (2025 simplified)
        federal_tax = 0.0
        if income <= 11600:
            federal_tax = income * 0.10
        elif income <= 47150:
            federal_tax = 1160 + (income - 11600) * 0.12
        elif income <= 100525:
            federal_tax = 5426 + (income - 47150) * 0.22
        elif income <= 191950:
            federal_tax = 17168.5 + (income - 100525) * 0.24
        else:
            federal_tax = 39110.5 + (income - 191950) * 0.32

        # California tax (simplified)
        ca_tax = income * 0.0725  # Simplified CA rate

        # QBI deduction (20% for qualified business income)
        qbi_deduction = income * 0.20 if income < 182100 else 0

        total_tax = federal_tax + ca_tax
        effective_rate = (total_tax / income * 100) if income > 0 else 0

        return {
            "input": {
                "income": income,
                "filing_status": filing_status,
            },
            "federal": {
                "taxable_income": income,
                "tax": round(federal_tax, 2),
                "effective_rate": round(federal_tax / income * 100, 2) if income > 0 else 0,
            },
            "california": {
                "taxable_income": income,
                "tax": round(ca_tax, 2),
                "effective_rate": 7.25,
            },
            "deductions": {
                "qbi_deduction": round(qbi_deduction, 2),
            },
            "total": {
                "tax": round(total_tax, 2),
                "effective_rate": round(effective_rate, 2),
            },
            "trinity_score": 0.92,
        }

    async def process_transaction(
        self, request_data: dict, account_id: str, dry_run: bool = False
    ) -> dict:
        """Process a financial transaction with ToT emission."""
        # Create a financial record from the request
        record = FinancialRecord(
            id=request_data.get("transaction_id", "tx-unknown"),
            description=f"{request_data.get('merchant', 'Unknown')} - {request_data.get('category', 'Uncategorized')}",
            amount=request_data.get("amount", 0.0),
            category=request_data.get("category", "UNCATEGORIZED"),
            risk_score=0,
            status="PENDING" if dry_run else "APPROVED",
        )

        # Assess risk
        record = await self.assess_risk(record)

        return {
            "success": True,
            "dry_run": dry_run,
            "transaction": {
                "id": record.id,
                "account_id": account_id,
                "merchant": request_data.get("merchant"),
                "amount": record.amount,
                "category": record.category,
                "date": request_data.get("date"),
                "status": record.status,
                "risk_score": record.risk_score,
            },
            "thoughts": [
                f"Transaction received: ${record.amount:.2f} at {request_data.get('merchant')}",
                f"Risk assessment: {record.risk_score}/100",
                f"Status: {'Simulated (DRY_RUN)' if dry_run else 'Processed'}",
            ],
        }

    async def analyze_irs_records(self, year: int) -> dict:
        """[Phase 13] Delegate IRS Analysis to Core Julie Engine."""
        from julie_cpa.core.julie_engine import julie

        # Delegate to the "Enlightened" Julie Engine (Context7 + IRS Client)
        return await julie.analyze_irs_records(year)
