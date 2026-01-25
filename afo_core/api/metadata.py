# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Kingdom API Metadata Configuration

Provides OpenAPI metadata and tags for the FastAPI application.
"""

from typing import Any


def get_api_metadata() -> dict[str, Any]:
    """Get FastAPI application metadata for OpenAPI documentation."""
    return {
        "title": "AFO Kingdom Soul Engine API",
        "description": """
## 🏰 AFO (A-Philosophy-First Operating System) Ultimate API

**Philosophy**: 眞善美孝 (Truth, Goodness, Beauty, Serenity)

### Overview

The AFO Soul Engine is a multi-agent RAG system with advanced monitoring and workflow automation.

### Key Features

* **🧠 Multi-Agent Orchestration** - LangGraph-based command execution with Redis checkpointing
* **📚 5 RAG Systems** - Ultimate RAG, Trinity Loop, Query Expansion, Recursive RAG, Ragas Evaluation
* **🏥 11-Organ Health Monitoring** - Real-time system health tracking (100% = all healthy)
* **🗄️ Triple Memory** - ChromaDB (vectors), PostgreSQL+pgvector (hybrid), Redis (checkpoints)
* **🔔 Alertmanager Integration** - 30-second Slack notifications for critical events
* **⚡ High Performance** - <50ms API response, 80%+ cache hit rate

### Documentation

* **GitHub**: [lofibrainwav/AFO](https://github.com/lofibrainwav/AFO)
* **Comprehensive Guide**: See CLAUDE.md and DEPLOYMENT_GUIDE.md
* **Philosophy**: See AFO_KINGDOM_CONSTITUTION.md

### Recent Achievements (Nov 2025)

* ✅ **Phase 6.2**: Redis optimization (80%+ cache hit rate via AsyncRedisSaver)
* ✅ **Phase 6.3**: Alertmanager + Grafana integration (30s Slack alerts)
* 🎯 **System Health**: 100% (11/11 organs operational)
""",
        "version": "6.3.0",
        "contact": {
            "name": "AFO Kingdom",
            "url": "https://github.com/lofibrainwav/AFO",
        },
        "license_info": {
            "name": "MIT License",
            "url": "https://github.com/lofibrainwav/AFO/blob/main/LICENSE",
        },
        "openapi_tags": get_api_tags(),
    }


def get_api_tags() -> list[dict[str, Any]]:
    """Get OpenAPI tags for endpoint grouping."""
    return [
        {
            "name": "Health",
            "description": "System health monitoring endpoints. Check 11-organ status and n8n connectivity.",
        },
        {
            "name": "RAG",
            "description": "Retrieval-Augmented Generation endpoints. 5 RAG systems: CRAG, Hybrid, Ultimate, Trinity Loop, Query Expansion.",
        },
        {
            "name": "Ragas",
            "description": "Ragas RAG evaluation system. 4 metrics: Faithfulness, Answer Relevancy, Context Precision, Context Recall.",
        },
        {
            "name": "Strategy",
            "description": "LangGraph-based command execution with Redis checkpointing. Multi-turn conversations with state persistence.",
        },
        {
            "name": "n8n Integration",
            "description": "n8n workflow automation integration. Monitor workflows, check health, execute actions.",
        },
        {
            "name": "API Wallet",
            "description": "Secure API key management with encryption. Store and retrieve API keys for multiple services.",
        },
        {
            "name": "Yeongdeok Memory",
            "description": "Advanced memory system with RAG integration. Named after 제갈량's strategic wisdom.",
        },
        {
            "name": "Skills Registry",
            "description": "AFO skill execution system. Register, discover, and execute modular skills.",
        },
        {
            "name": "GenUI",
            "description": "Phase 9: Self-Expanding Kingdom. Autonomous UI generation via Samahwi.",
        },
    ]
