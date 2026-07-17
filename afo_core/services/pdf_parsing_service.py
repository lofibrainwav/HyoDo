"""
PDF Parsing Service
Provides robust PDF text extraction capabilities for the Tax Document Classifier.
Utilizes pypdf for local extraction and handles common PDF edge cases.
"""

from pathlib import Path
from typing import Any

import anyio

try:
    from pypdf import PdfReader

    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


def _extract_pdf_text_sync(file_path: str) -> dict[str, Any]:
    """Extract PDF contents synchronously for execution in a worker thread."""
    reader = PdfReader(file_path)

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            return {
                "success": False,
                "error": "PDF is encrypted/password protected.",
                "text": "",
                "is_scanned": False,
            }

    full_text = []
    page_count = len(reader.pages)
    for page in reader.pages:
        try:
            page_text = page.extract_text()
            if page_text:
                full_text.append(page_text)
        except Exception:
            continue

    combined_text = "\n".join(full_text)
    is_scanned = page_count > 0 and len(combined_text.strip()) < (page_count * 20)
    return {
        "success": True,
        "text": combined_text,
        "meta": {"pages": page_count, "info": reader.metadata},
        "is_scanned": is_scanned,
        "error": None,
    }


class PDFParsingService:
    """Service for extracting text and metadata from PDF documents."""

    def __init__(self) -> None:
        self.chunk_size = 1000  # Characters (for future chunking usage)

    async def extract_text(self, file_path: str) -> dict[str, Any]:
        """
        Extracts text from a PDF file.

        Returns:
            Dict containing:
            - text: The full extracted text
            - meta: Metadata (pages, author, etc.)
            - success: Boolean status
            - error: Error message if failed
            - is_scanned: Boolean hint if text extraction yielded little result
        """
        if not PYPDF_AVAILABLE:
            return {
                "success": False,
                "error": "pypdf library not installed. Please install 'pypdf'.",
                "text": "",
                "is_scanned": False,
            }

        path = Path(file_path)
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "text": "",
                "is_scanned": False,
            }

        try:
            return await anyio.to_thread.run_sync(_extract_pdf_text_sync, file_path)
        except Exception as e:
            return {"success": False, "error": str(e), "text": "", "is_scanned": False}


# Singleton instance
pdf_parsing_service = PDFParsingService()
