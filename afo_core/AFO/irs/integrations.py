"""
IRS Integrations

RAG 및 Context7 통합 로직
"""

import logging
import os
import sys
from typing import Any

logger = logging.getLogger(__name__)


class IRSIntegrations:
    """IRS 외부 시스템 통합"""

    def __init__(self, multimodal_rag: Any = None) -> None:
        self.multimodal_rag = multimodal_rag

    async def add_to_multimodal_rag(self, documents: list[dict[str, Any]]) -> None:
        """Multimodal RAG 엔진에 문서 추가"""
        if not self.multimodal_rag:
            logger.warning("Multimodal RAG engine not initialized")
            return

        for doc in documents:
            try:
                content = f"""
# {doc["title"]}

**Source**: {doc["source"]}
**Type**: {doc["document_type"]}
**URL**: {doc["url"]}

## Preview
{doc["preview"]}

---
*Collected at: {doc["collected_at"]}*
*Document ID: {doc["id"]}*
"""
                metadata = {
                    "source": "irs_registry",
                    "document_type": doc["document_type"],
                    "category": doc["category"],
                    "subcategory": doc["subcategory"],
                    "url": doc["url"],
                    "collected_at": doc["collected_at"],
                }

                success = self.multimodal_rag.add_document(
                    content=content, content_type="text", metadata=metadata
                )

                if success:
                    logger.info(f"Added to RAG: {doc['title'][:50]}...")
                else:
                    logger.warning(f"Failed to add to RAG: {doc['title'][:50]}...")

            except Exception as e:
                logger.error(f"RAG addition failed for {doc.get('title', 'Unknown')}: {e}")

    async def register_to_context7(self, documents: list[dict[str, Any]]) -> None:
        """Context7에 문서 메타데이터 등록"""
        try:
            trinity_os_path = os.path.join(os.getcwd(), "packages", "trinity-os")
            if trinity_os_path not in sys.path:
                sys.path.insert(0, trinity_os_path)

            from trinity_os.servers.context7_mcp import Context7MCP

            context7 = Context7MCP()

            for doc in documents:
                try:
                    knowledge_item = {
                        "id": f"irs_{doc['id']}",
                        "type": "irs_document",
                        "title": f"IRS {doc['document_type'].replace('_', ' ').title()}: {doc['title']}",
                        "content": self._build_context7_content(doc),
                        "keywords": [
                            "irs",
                            "tax",
                            doc["document_type"],
                            doc["category"],
                            doc["subcategory"],
                            doc["source"],
                        ],
                    }

                    item_id = context7.add_knowledge(knowledge_item)

                    if item_id:
                        logger.info(f"Registered to Context7: {doc['title'][:50]}...")
                    else:
                        logger.warning(f"Context7 registration failed: {doc['title'][:50]}...")

                except Exception as e:
                    logger.error(
                        f"Context7 registration failed for {doc.get('title', 'Unknown')}: {e}"
                    )

        except Exception as e:
            logger.error(f"Context7 integration failed: {e}")

    @staticmethod
    def _build_context7_content(doc: dict[str, Any]) -> str:
        """Context7용 콘텐츠 생성"""
        return f"""
IRS {doc["document_type"].replace("_", " ").title()}

**Title**: {doc["title"]}
**Source**: {doc["source"]}
**URL**: {doc["url"]}
**Category**: {doc["category"]}
**Subcategory**: {doc["subcategory"]}

**Preview**:
{doc["preview"]}

This document has been automatically collected and indexed by the IRS Source Registry system.
For full content, visit: {doc["url"]}
"""

    async def classify_with_tax_classifier(self, documents: list[dict[str, Any]]) -> None:
        """수집된 문서를 Tax Classifier로 분류"""
        try:
            from AFO.tax_document_classifier import tax_document_classifier

            for doc in documents:
                temp_content = f"{doc['title']}\n\n{doc['preview']}"
                temp_filename = f"irs_temp_{doc['id']}.txt"

                with open(temp_filename, "w", encoding="utf-8") as f:
                    f.write(temp_content)

                classification = await tax_document_classifier.classify_document(temp_filename)

                if classification.get("success"):
                    logger.info(
                        f"Classified: {doc['title'][:30]}... -> "
                        f"{classification.get('primary_category')}"
                    )

                try:
                    os.remove(temp_filename)
                except OSError:
                    pass

        except Exception as e:
            logger.error(f"Classification error: {e}")
