"""OCR Document Extractor.

이미지 기반 문서에서 텍스트를 추출하는 OCR 엔진.
"""

from __future__ import annotations

import os


def perform_ocr_extraction(image_path: str) -> str:
    """이미지 파일에서 텍스트를 추출합니다."""
    # 실제 구현에서는 Tesseract, AWS Textract, Google Vision API 등을 호출
    # 현재는 파일 확장자 기반 모의 텍스트 반환
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".tiff"]:
        return ""

    return f"OCR로부터 추출된 텍스트 내용 ({image_path})...\n총 소득(Total Income): $150,000\n원천징수(Withholding): $25,000"
