"""Document Analysis AI Package.

멀티모달 문서 분석 시스템.
OCR, AI 분석, 수학적 검증을 결합하여 고도의 정확성을 제공.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional

from .ai_engine import DocumentAIEngine
from .extractors.ocr import perform_ocr_extraction
from .extractors.pdf import perform_pdf_extraction
from .validator import calculate_document_trinity_score, validate_mathematically


class DocumentAnalysisAI:
    """AI 기반 문서 분석 및 추출 시스템 (Facade)."""

    def __init__(self) -> None:
        self.ai_engine = DocumentAIEngine()

    async def analyze_document_with_ai(
        self,
        document_path: str,
        analysis_type: str = "comprehensive",
        claude_client=None,
    ) -> dict[str, Any]:
        """AI 기반 문서 종합 분석 수행."""

        # 1. 문서 내용 추출
        content = self._extract_content(document_path)

        # 2. AI 스타일 분석
        metadata = {"filename": os.path.basename(document_path), "size": 0}
        ai_result = await self.ai_engine.analyze_content(
            content, metadata, analysis_type, claude_client
        )

        # 3. 수학적 검증
        math_valid = validate_mathematically(ai_result, content)

        # 4. Trinity Score 계산
        scores = calculate_document_trinity_score(ai_result, math_valid)

        return {
            "success": True,
            "document_path": document_path,
            "analysis_timestamp": datetime.now().isoformat(),
            "document_type": ai_result.get("document_type"),
            "extracted_data": ai_result.get("extracted_data"),
            "summary": ai_result.get("summary"),
            "validation": math_valid,
            "trinity_scores": scores,
        }

    def _extract_content(self, path: str) -> str:
        """파일 형식에 따른 텍스트 추출 분기."""
        ext = os.path.splitext(path)[1].lower()
        if ext in [".png", ".jpg", ".jpeg"]:
            return perform_ocr_extraction(path)
        elif ext == ".pdf":
            return perform_pdf_extraction(path)
        else:
            return "일반 텍스트 문서 내용..."


# 편의 함수
async def analyze_tax_document_with_ai(
    document_path: str,
    analysis_type: str = "comprehensive",
) -> dict[str, Any]:
    """세금 문서 AI 분석 편의 함수."""
    analyzer = DocumentAnalysisAI()
    return await analyzer.analyze_document_with_ai(document_path, analysis_type)


__all__ = ["DocumentAnalysisAI", "analyze_tax_document_with_ai"]
