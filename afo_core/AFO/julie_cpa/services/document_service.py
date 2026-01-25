"""
Document Library Service (Phase 63)
Manages document templates, generated reports, and tax forms.
"""

import hashlib
import json
from datetime import datetime
from typing import Any


class DocumentLibraryService:
    """Manages documents, templates, and generated reports."""

    def __init__(self) -> None:
        self._documents: dict[str, dict[str, Any]] = {}
        self._templates: dict[str, dict[str, Any]] = {}
        self._load_templates()
        self._generate_sample_documents()

    def _load_templates(self) -> None:
        """Load document templates."""
        self.templates = {
            "tax_summary": {
                "id": "TPL-001",
                "name": "Annual Tax Summary",
                "description": "Comprehensive tax summary for the fiscal year",
                "category": "tax",
                "fields": ["year", "income", "deductions", "tax_liability"],
            },
            "quarterly_estimate": {
                "id": "TPL-002",
                "name": "Quarterly Tax Estimate",
                "description": "Estimated tax payment calculation",
                "category": "tax",
                "fields": ["quarter", "estimated_income", "estimated_tax"],
            },
            "audit_report": {
                "id": "TPL-003",
                "name": "Audit Trail Report",
                "description": "Complete audit log for specified period",
                "category": "compliance",
                "fields": ["start_date", "end_date", "events"],
            },
            "financial_statement": {
                "id": "TPL-004",
                "name": "Financial Statement",
                "description": "Income and expense summary statement",
                "category": "financial",
                "fields": ["period", "income_categories", "expense_categories"],
            },
            "1099_summary": {
                "id": "TPL-005",
                "name": "1099 Income Summary",
                "description": "Summary of 1099 income for tax filing",
                "category": "tax",
                "fields": ["year", "payers", "total_income"],
            },
        }

    def _generate_sample_documents(self) -> None:
        """Generate sample documents for demo."""
        samples = [
            {
                "template": "tax_summary",
                "title": "2025 Annual Tax Summary",
                "data": {
                    "year": 2025,
                    "income": 285000,
                    "deductions": 45000,
                    "tax_liability": 67200,
                },
                "status": "final",
            },
            {
                "template": "quarterly_estimate",
                "title": "Q4 2025 Tax Estimate",
                "data": {"quarter": "Q4 2025", "estimated_income": 75000, "estimated_tax": 18750},
                "status": "final",
            },
            {
                "template": "quarterly_estimate",
                "title": "Q1 2026 Tax Estimate",
                "data": {"quarter": "Q1 2026", "estimated_income": 80000, "estimated_tax": 20000},
                "status": "draft",
            },
            {
                "template": "audit_report",
                "title": "January 2026 Audit Report",
                "data": {"start_date": "2026-01-01", "end_date": "2026-01-31", "events": 156},
                "status": "pending",
            },
        ]

        for sample in samples:
            self.create_document(
                template_id=sample["template"],
                title=sample["title"],
                data=sample["data"],
                status=sample["status"],
            )

    def create_document(
        self, template_id: str, title: str, data: dict[str, Any], status: str = "draft"
    ) -> dict[str, Any]:
        """Create a new document from template."""
        doc_id = f"DOC-{len(self._documents) + 1:04d}"
        timestamp = datetime.now().isoformat()

        # Generate content hash for integrity
        content_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]

        template = self.templates.get(template_id, {})

        document = {
            "id": doc_id,
            "template_id": template_id,
            "template_name": template.get("name", "Unknown"),
            "category": template.get("category", "general"),
            "title": title,
            "data": data,
            "status": status,
            "created_at": timestamp,
            "updated_at": timestamp,
            "content_hash": content_hash,
            "version": 1,
        }

        self._documents[doc_id] = document
        return document

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """Get a document by ID."""
        return self._documents.get(doc_id)

    def list_documents(
        self, category: str | None = None, status: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """List documents with optional filters."""
        docs = list(self._documents.values())

        if category:
            docs = [d for d in docs if d.get("category") == category]

        if status:
            docs = [d for d in docs if d.get("status") == status]

        # Sort by created_at descending
        docs.sort(key=lambda x: x["created_at"], reverse=True)

        return docs[:limit]

    def update_document_status(self, doc_id: str, status: str) -> dict[str, Any] | None:
        """Update document status."""
        doc = self._documents.get(doc_id)
        if doc:
            doc["status"] = status
            doc["updated_at"] = datetime.now().isoformat()
            return doc
        return None

    def get_templates(self) -> list[dict[str, Any]]:
        """Get all available templates."""
        return list(self.templates.values())

    def generate_pdf_content(self, doc_id: str) -> dict[str, Any]:
        """Generate PDF-ready content for a document."""
        doc = self._documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        template = self.templates.get(doc["template_id"], {})

        # Generate structured content for PDF
        content = {
            "title": doc["title"],
            "subtitle": template.get("description", ""),
            "category": doc["category"].upper(),
            "status": doc["status"].upper(),
            "generated_at": datetime.now().isoformat(),
            "document_id": doc_id,
            "content_hash": doc["content_hash"],
            "sections": [],
        }

        # Add data fields as sections
        for key, value in doc["data"].items():
            content["sections"].append(
                {
                    "label": key.replace("_", " ").title(),
                    "value": str(value)
                    if not isinstance(value, (int, float))
                    else f"${value:,.2f}"
                    if "income" in key.lower() or "tax" in key.lower()
                    else str(value),
                }
            )

        content["footer"] = (
            f"Generated by Julie CPA Portal | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        return content

    def get_document_stats(self) -> dict[str, Any]:
        """Get document statistics."""
        docs = list(self._documents.values())

        by_status = {}
        by_category = {}

        for doc in docs:
            status = doc["status"]
            category = doc["category"]

            by_status[status] = by_status.get(status, 0) + 1
            by_category[category] = by_category.get(category, 0) + 1

        return {
            "total_documents": len(docs),
            "by_status": by_status,
            "by_category": by_category,
            "templates_available": len(self.templates),
        }


# Singleton instance
_doc_service: DocumentLibraryService | None = None


def get_document_service() -> DocumentLibraryService:
    """Get or create the document service singleton."""
    global _doc_service
    if _doc_service is None:
        _doc_service = DocumentLibraryService()
    return _doc_service
