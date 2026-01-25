"""
PDF Parsing Service
Provides robust PDF text extraction capabilities for the Tax Document Classifier.
Utilizes pypdf for local extraction and handles common PDF edge cases.
"""

from pathlib import Path
from typing import Any

try:
    from pypdf import PdfReader

    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


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
            reader = PdfReader(file_path)

            # check encryption
            if reader.is_encrypted:
                try:
                    reader.decrypt("")  # Try empty password
                except Exception:
                    # If still encrypted, we can't do much without password management
                    return {
                        "success": False,
                        "error": "PDF is encrypted/password protected.",
                        "text": "",
                        "is_scanned": False,
                    }

            full_text = []
            page_count = len(reader.pages)

            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        full_text.append(page_text)
                except Exception:
                    # Individual page failure shouldn't kill whole process
                    continue

            combined_text = "\n".join(full_text)

            # Simple heuristic for scanned documents:
            # If we have many pages but very little text, it's likely an image scan
            is_scanned = False
            if page_count > 0 and len(combined_text.strip()) < (page_count * 20):
                # Less than 20 chars per page on average? Suspicious.
                is_scanned = True

            return {
                "success": True,
                "text": combined_text,
                "meta": {"pages": page_count, "info": reader.metadata},
                "is_scanned": is_scanned,
                "error": None,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "text": "", "is_scanned": False}


# Singleton instance
pdf_parsing_service = PDFParsingService()
