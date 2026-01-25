"""
Notebook Handler Package
Manages MyGPT context storage and retrieval
Integrates with Redis/Upstash for persistence
"""

import os
from datetime import UTC, datetime
from typing import Any

from AFO.utils.standard_shield import shield

# Import Upstash Redis client (would install: pip install upstash-redis)
# For demo purposes, we use in-memory storage
# from upstash_redis import Redis

# Configuration
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL", "")
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN", "")

# Demo storage (in-memory)
demo_notebooks = [
    {
        "id": "o75vEpSlZeNtlMy1bp3jB",
        "title": "TAX-EASYUP-5165-M (2025 Inflation Update)",
        "content": "CPE Depot Easy Update 2025 — Inflation Adjustment Baseline\n\nSource: Danny C. Santucci, CPE Depot (Publication Date: 2025-05-08)",
        "tags": ["tax", "inflation", "2025", "CPE", "baseline", "JulieCPA"],
        "createdAt": "2026-01-19T06:54:31.996Z",
        "updatedAt": "2026-01-19T06:54:31.996Z",
    },
    {
        "id": "YNHOAXPKiUai_42YK6Uvp",
        "title": "Tax EasyUp 5165 - 2025 Inflation & Update Summary",
        "content": "### 📘 2025 EasyUp 5165 Comprehensive Summary\n\n**Source:** CPE Depot, '2025/2024 Easy Update & Inflation Adjustments' (Danny C. Santucci, CPA)",
        "tags": ["tax", "CPE", "inflation", "2025", "JulieCPA"],
        "createdAt": "2026-01-19T06:48:13.666Z",
        "updatedAt": "2026-01-19T06:48:13.666Z",
    },
    {
        "id": "0jNiduX5sCws2TQM6q7WQ",
        "title": "Julie CPA Strategy Log",
        "content": "Initial entry for Julie CPA project notebook.\nPurpose: Track all CPA strategic analyses, tax simulations, and audit review logs.",
        "tags": ["strategy", "julie-cpa"],
        "createdAt": "2026-01-18T20:30:50.827Z",
        "updatedAt": "2026-01-18T20:30:50.827Z",
    },
    {
        "id": "z5h1SVRxY_efJTCh3vygz",
        "title": "AICPA_AI_Audit_Template_v1.0",
        "content": "Full AICPA AI Audit Standard Template + Client Training Module Integration Report (generated 2026-01-18).",
        "tags": ["aicpa", "audit", "template"],
        "createdAt": "2026-01-18T10:48:52.137Z",
        "updatedAt": "2026-01-18T10:48:52.137Z",
    },
    {
        "id": "rHOGg0sel_1I98kkoA7l8",
        "title": "Julie_CPA_Full_AFO_Integration",
        "content": 'AFO GPT (Tax Simulation / Roth Optimizer / IRMAA Avoidance / EV Credit / 401k Optimizer / Quarterly Estimated Tax) 완전 통합 버전.\n\n### 🔧 Integration Summary\n- Link: ABC CPAs Workspace ↔ AFO GPT\n- Mode: AUTO LINK (Project별 자동 핸드오프)\n- Components: Tax Simulation, Roth Ladder, IRMAA Avoidance, EV Credit, 401(k) Deferral, QET Calculator\n- Security: Vault Encryption, Partner-Level Review Required\n- Memory Scope: Project-level Isolation (per Client)\n- API Paths: /api/julie/tax-simulation, /api/julie/roth, /api/julie/irmaa, /api/julie/ev, /api/julie/401k, /api/julie/qet\n- Governance: Trinity Score System (Truth / Goodness / Beauty)\n- IRS Rev. Proc. 2024-40, OBBB Act 2025 compliance\n- Audit-ready: Logging + Partner verification\n- Status: AUTO LINK DEPLOYMENT completed\n- All Widgets functional\n- Dashboard: "AI Tax Engine ACTIVE" banner enabled',
        "tags": ["julie-cpa", "afo-gpt", "integration", "tax", "roth"],
        "createdAt": "2026-01-17T01:41:59.365Z",
        "updatedAt": "2026-01-17T01:41:59.365Z",
    },
]


class NotebookManager:
    """Manages MyGPT context storage"""

    def __init__(self) -> None:
        self.storage = demo_notebooks

    def _generate_id(self) -> str:
        """Generate unique notebook ID"""
        return f"nb_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{len(self.storage)}"

    @shield(default_return=[], pillar="善")
    def list_notebooks(self, limit: int = 5, tags: list[str] | None = None) -> list[dict[str, Any]]:
        """List all notebooks with optional filtering"""
        results = self.storage

        # Filter by tags if provided
        if tags:
            results = [nb for nb in results if any(tag in nb.get("tags", []) for tag in tags)]

        # Limit results
        if limit and len(results) > limit:
            results = results[:limit]

        return results

    @shield(default_return=None, pillar="善")
    def get_notebook(self, notebook_id: str) -> dict[str, Any] | None:
        """Get a specific notebook by ID"""
        for nb in self.storage:
            if nb.get("id") == notebook_id:
                return nb
        return None

    @shield(default_return={}, pillar="善")
    def create_notebook(
        self, title: str, content: str, tags: list[str] | None = None, user_id: str = "default"
    ) -> dict[str, Any]:
        """Create a new notebook entry"""
        notebook_id = self._generate_id()

        notebook = {
            "id": notebook_id,
            "title": title,
            "content": content,
            "tags": tags or [],
            "userId": user_id,
            "createdAt": datetime.now(UTC).isoformat(),
            "updatedAt": datetime.now(UTC).isoformat(),
        }

        self.storage.append(notebook)
        return notebook

    @shield(default_return=None, pillar="善")
    def update_notebook(
        self, notebook_id: str, title: str | None = None, content: str | None = None
    ) -> dict[str, Any] | None:
        """Update an existing notebook"""
        for nb in self.storage:
            if nb.get("id") == notebook_id:
                if title:
                    nb["title"] = title
                if content:
                    nb["content"] = content
                nb["updatedAt"] = datetime.now(UTC).isoformat()
                return nb
        return None

    @shield(default_return=False, pillar="善")
    def delete_notebook(self, notebook_id: str) -> bool:
        """Delete a notebook by ID"""
        for i, nb in enumerate(self.storage):
            if nb.get("id") == notebook_id:
                del self.storage[i]
                return True
        return False


# Note: This is a demo implementation
# In production, this would use Upstash Redis with async operations
# Example:
# from upstash_redis import Redis
# redis = Redis(url=UPSTASH_REDIS_URL, token=UPSTASH_REDIS_TOKEN)
#
# async def list_notebooks_async(self):
#     keys = await redis.keys("nb:*")
#     notebooks = await redis.mget(keys)
#     return [json.loads(nb) for nb in notebooks]
