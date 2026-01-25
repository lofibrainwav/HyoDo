# Trinity Score: 90.0 (Established by Chancellor)
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from AFO.julie_cpa.services.julie_service import JulieService
from AFO.utils.standard_shield import shield

# [Legacy Merger]
# This router exposes same endpoints as legacy 'julie.py'
# but powers them with new 'JulieService' (Royal Edition).

router = APIRouter(prefix="/api/julie", tags=["Julie CPA (Royal)"])
julie_service = JulieService()


from starlette.requests import Request

from AFO.core.limiter import limiter


@router.get("/status")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_status(request: Request) -> dict[str, Any]:
    """Legacy-compatible Status Endpoint.
    Used by: AICPA Julie Frontend (Port 3000)
    """
    return await julie_service.get_royal_status()


@router.get("/dashboard")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_dashboard(request: Request) -> dict[str, Any]:
    """[GenUI Support]
    Full Financial Dashboard Data (Health, Alerts, Tx).
    """
    return await julie_service.get_financial_dashboard()


class TaxCalcRequest(BaseModel):
    income: float
    filing_status: str = "single"


class TransactionRequest(BaseModel):
    merchant: str
    amount: float
    category: str = "general"
    date: str = ""
    account_id: str = "default"
    dry_run: bool = True


@router.post("/calculate-tax")
@limiter.limit("20/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def calculate_tax(request: Request, body: TaxCalcRequest) -> dict[str, Any]:
    """[Operation Gwanggaeto]
    Performs real-time tax simulation (Federal + CA + QBI).
    Source: JuliePerplexity Report (2025 Rules).
    """
    return await julie_service.calculate_tax_scenario(body.income, body.filing_status)


@router.post("/transaction")
@limiter.limit("30/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def process_transaction(request: Request, body: TransactionRequest) -> dict[str, Any]:
    """[Action Endpoint]
    Trigger a financial transaction (or simulation).
    Emits thoughts to Neural Stream (ToT).
    """
    return await julie_service.process_transaction(
        request_data={
            "transaction_id": f"tx-{body.merchant.lower()}-001",
            "merchant": body.merchant,
            "amount": body.amount,
            "category": body.category,
            "date": body.date,
        },
        account_id=body.account_id,
        dry_run=body.dry_run,
    )


@router.post("/transaction/approve")
@limiter.limit("30/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def approve_transaction(request: Request, tx_id: str) -> dict[str, Any]:
    """[T26] Transaction Approval Action"""
    # In Phase 2, this would trigger actual bank transfer or DB update.
    # For now, we simulate approval.
    return {
        "success": True,
        "message": f"Transaction {tx_id} approved",
        "tx_id": tx_id,
        "status": "APPROVED",
    }


@router.get("/history")
@limiter.limit("30/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_history(request: Request, limit: int = 50) -> dict[str, Any]:
    """[Phase 58] Query persisted audit log history from SQLite."""
    import sqlite3
    from pathlib import Path

    db_path = Path(__file__).parent.parent.parent / "julie_cpa" / "services" / "julie_audit.db"

    if not db_path.exists():
        return {"logs": [], "count": 0, "source": "memory"}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, timestamp, message FROM audit_events ORDER BY id DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    conn.close()

    return {
        "logs": [{"id": r[0], "timestamp": r[1], "message": r[2]} for r in rows],
        "count": len(rows),
        "source": "sqlite",
    }


# ============================================
# Phase 60: Royal Treasury Analytics Endpoints
# ============================================


@router.get("/treasury/summary")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_treasury_summary(request: Request) -> dict[str, Any]:
    """[Phase 60] Get overall financial summary (income, expense, net)."""
    from AFO.julie_cpa.services.treasury_service import get_treasury_service

    return get_treasury_service().get_summary()


@router.get("/treasury/categories")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_treasury_categories(request: Request) -> dict[str, Any]:
    """[Phase 60] Get income/expense breakdown by category."""
    from AFO.julie_cpa.services.treasury_service import get_treasury_service

    return get_treasury_service().get_category_breakdown()


@router.get("/treasury/trend")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_treasury_trend(request: Request) -> dict[str, Any]:
    """[Phase 60] Get monthly income/expense trend data for charts."""
    from AFO.julie_cpa.services.treasury_service import get_treasury_service

    return get_treasury_service().get_monthly_trend()


@router.get("/treasury/forecast")
@limiter.limit("30/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_tax_forecast(request: Request) -> dict[str, Any]:
    """[Phase 60] Get projected annual tax estimate."""
    from AFO.julie_cpa.services.treasury_service import get_treasury_service

    return get_treasury_service().get_tax_forecast()


# ============================================
# Phase 61: Julie AI Advisor Endpoints
# ============================================


class AdvisorQuestionRequest(BaseModel):
    question: str


class AdvisorInsightsRequest(BaseModel):
    income: float
    filing_status: str = "single"


@router.post("/advisor/ask")
@limiter.limit("30/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def ask_advisor(request: Request, body: AdvisorQuestionRequest) -> dict[str, Any]:
    """[Phase 61] Ask Julie AI Advisor a tax/financial question."""
    from AFO.julie_cpa.services.advisor_service import get_advisor_service

    return get_advisor_service().ask(body.question)


@router.post("/advisor/insights")
@limiter.limit("30/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_insights(request: Request, body: AdvisorInsightsRequest) -> dict[str, Any]:
    """[Phase 61] Get personalized financial insights based on income."""
    from AFO.julie_cpa.services.advisor_service import get_advisor_service

    return get_advisor_service().get_insights(body.income, body.filing_status)


@router.get("/advisor/history")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_advisor_history(request: Request) -> dict[str, Any]:
    """[Phase 61] Get conversation history with AI advisor."""
    from AFO.julie_cpa.services.advisor_service import get_advisor_service

    return {
        "history": get_advisor_service().get_conversation_history(),
        "count": len(get_advisor_service().get_conversation_history()),
    }


# ============================================
# Phase 62: System Health Monitoring Endpoints
# ============================================


@router.get("/health/metrics")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_health_metrics(request: Request) -> dict[str, Any]:
    """[Phase 62] Get current system health metrics (CPU, Memory, Disk)."""
    from AFO.core.health_service import get_health_service

    return get_health_service().get_current_metrics()


@router.get("/health/summary")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_health_summary(request: Request) -> dict[str, Any]:
    """[Phase 62] Get overall system health summary."""
    from AFO.core.health_service import get_health_service

    return get_health_service().get_health_summary()


@router.get("/health/alerts")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_health_alerts(request: Request, limit: int = 20) -> dict[str, Any]:
    """[Phase 62] Get recent system alerts."""
    from AFO.core.health_service import get_health_service

    alerts = get_health_service().get_alerts(limit=limit)
    return {"alerts": alerts, "count": len(alerts)}


@router.post("/health/alerts/{alert_id}/ack")
@limiter.limit("30/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def acknowledge_alert(request: Request, alert_id: str) -> dict[str, Any]:
    """[Phase 62] Acknowledge a system alert."""
    from AFO.core.health_service import get_health_service

    success = get_health_service().acknowledge_alert(alert_id)
    return {"success": success, "alert_id": alert_id}


@router.get("/health/performance")
@limiter.limit("30/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_performance_metrics(request: Request) -> dict[str, Any]:
    """[Phase 62] Get aggregated performance metrics."""
    from AFO.core.health_service import get_health_service

    return get_health_service().get_performance_metrics()


# ============================================
# Phase 63: Document Library Endpoints
# ============================================


@router.get("/documents")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def list_documents(
    request: Request, category: str | None = None, status: str | None = None, limit: int = 20
) -> dict[str, Any]:
    """[Phase 63] List documents with optional filters."""
    from AFO.julie_cpa.services.document_service import get_document_service

    docs = get_document_service().list_documents(category=category, status=status, limit=limit)
    return {"documents": docs, "count": len(docs)}


@router.get("/documents/templates")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_templates(request: Request) -> dict[str, Any]:
    """[Phase 63] Get available document templates."""
    from AFO.julie_cpa.services.document_service import get_document_service

    return {"templates": get_document_service().get_templates()}


@router.get("/documents/stats")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_document_stats(request: Request) -> dict[str, Any]:
    """[Phase 63] Get document statistics."""
    from AFO.julie_cpa.services.document_service import get_document_service

    return get_document_service().get_document_stats()


@router.get("/documents/{doc_id}")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_document(request: Request, doc_id: str) -> dict[str, Any]:
    """[Phase 63] Get a specific document by ID."""
    from AFO.julie_cpa.services.document_service import get_document_service

    doc = get_document_service().get_document(doc_id)
    if doc:
        return doc
    return {"error": "Document not found"}


@router.get("/documents/{doc_id}/pdf")
@limiter.limit("30/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_document_pdf(request: Request, doc_id: str) -> dict[str, Any]:
    """[Phase 63] Get PDF-ready content for a document."""
    from AFO.julie_cpa.services.document_service import get_document_service

    return get_document_service().generate_pdf_content(doc_id)


@router.post("/documents/{doc_id}/status")
@limiter.limit("30/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def update_document_status(request: Request, doc_id: str, status: str) -> dict[str, Any]:
    """[Phase 63] Update document status."""
    from AFO.julie_cpa.services.document_service import get_document_service

    doc = get_document_service().update_document_status(doc_id, status)
    if doc:
        return {"success": True, "document": doc}
    return {"success": False, "error": "Document not found"}


# ============================================
# Phase 64: User Settings Endpoints
# ============================================


@router.get("/settings")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_all_settings(request: Request) -> dict[str, Any]:
    """[Phase 64] Get all user settings."""
    from AFO.julie_cpa.services.settings_service import get_settings_service

    return get_settings_service().get_all_settings()


@router.get("/settings/summary")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_settings_summary(request: Request) -> dict[str, Any]:
    """[Phase 64] Get settings summary."""
    from AFO.julie_cpa.services.settings_service import get_settings_service

    return get_settings_service().get_settings_summary()


@router.get("/settings/{section}")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_settings_section(request: Request, section: str) -> dict[str, Any]:
    """[Phase 64] Get a specific settings section."""
    from AFO.julie_cpa.services.settings_service import get_settings_service

    result = get_settings_service().get_section(section)
    if result:
        return {"section": section, "settings": result}
    return {"error": f"Unknown section: {section}"}


class SettingUpdate(BaseModel):
    key: str
    value: Any


@router.post("/settings/{section}")
@limiter.limit("30/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def update_setting(request: Request, section: str, body: SettingUpdate) -> dict[str, Any]:
    """[Phase 64] Update a single setting."""
    from AFO.julie_cpa.services.settings_service import get_settings_service

    return get_settings_service().update_setting(section, body.key, body.value)


@router.get("/settings/notifications/config")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_notification_config(request: Request) -> dict[str, Any]:
    """[Phase 64] Get notification settings configuration."""
    from AFO.julie_cpa.services.settings_service import get_settings_service

    return get_settings_service().get_notification_settings()


@router.get("/settings/theme/config")
@limiter.limit("60/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def get_theme_config(request: Request) -> dict[str, Any]:
    """[Phase 64] Get theme settings configuration."""
    from AFO.julie_cpa.services.settings_service import get_settings_service


# ============================================
# Phase 66: Socratic Synaptic Stream (Event Sourcing)
# ============================================

import asyncio
import datetime

from sse_starlette.sse import EventSourceResponse


@router.get("/stream/{channel}")
async def stream_synaptic_thoughts(request: Request, channel: str):
    """[Socratic Architecture] Real-time Synaptic Stream.
    Proxies thoughts from the Soul Engine to the NeuroLink (Client).
    Replaces HTTP Polling with Event Sourcing.
    """

    async def event_generator():
        # Initial Handshake
        yield {
            "event": "connected",
            "data": f'{{"message": "🧠 Synaptic Stream Connected ({channel})", "timestamp": "{datetime.datetime.now(datetime.UTC).isoformat()}"}}',
        }

        # Simulation: In a real Event Sourcing setup, this would subscribe to Redis Streams
        # For now, we simulate a "Thinking" heartbeat.
        counter = 0
        while True:
            if await request.is_disconnected():
                break

            # Heartbeat / Thought every 10 seconds
            await asyncio.sleep(10)
            counter += 1
            yield {
                "event": "thought",
                "data": f'{{"type": "thought", "payload": {{"id": {counter}, "content": "Analyzing ecosystem state...", "channel": "{channel}"}}}}',
            }

    return EventSourceResponse(event_generator())


# ============================================
# Phase 13: IRS & CPA Perfection Endpoints
# ============================================


class IRSAnalysisRequest(BaseModel):
    year: int = 2025


@router.post("/irs/analyze")
@limiter.limit("5/minute")
@shield(pillar="善", log_error=True, reraise=False)
async def analyze_irs(request: Request, body: IRSAnalysisRequest) -> dict[str, Any]:
    """[Phase 13] Analyze IRS records for a specific tax year.
    Connects to the Enlightened Julie Engine (Context7 + IRS Client).
    """
    return await julie_service.analyze_irs_records(body.year)
