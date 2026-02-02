"""
Verify PDF Capabilities
Generates a dummy tax PDF and runs the TaxDocumentClassifier on it.
"""

import asyncio
import os

# Bypassing the heavy TaxDocumentClassifier for unit testing the service
from AFO.services.pdf_parsing_service import pdf_parsing_service
from reportlab.pdfgen import canvas

TEST_PDF_PATH = "test_tax_form.pdf"


def generate_dummy_pdf() -> None:
    print(f"Creating dummy PDF: {TEST_PDF_PATH}")
    c = canvas.Canvas(TEST_PDF_PATH)
    c.drawString(100, 800, "Internal Revenue Service")
    c.drawString(100, 780, "Form 1040 (2025)")
    c.drawString(100, 760, "Department of the Treasury")
    c.drawString(100, 740, "Individual Income Tax Return")
    c.drawString(100, 700, "Your first name and initial: Julie")
    c.drawString(100, 680, "Last name: Bot")
    c.drawString(100, 660, "Home address: AFO Kingdom, Virtual Space")
    c.save()


async def run_verification():
    try:
        generate_dummy_pdf()

        print(f"\nrunning basic PDF Service on {TEST_PDF_PATH}...")
        result = await pdf_parsing_service.extract_text(TEST_PDF_PATH)

        print("\n--- Result ---")
        if result.get("success"):
            print("✅ Success!")
            print(f"Text Length: {len(result.get('text'))} chars")
            print(f"Content Preview: {result.get('text')[:100]}...")
            print(f"Is Scanned? {result.get('is_scanned')}")
        else:
            print(f"❌ Failed: {result.get('error')}")
            print(result)

    finally:
        if os.path.exists(TEST_PDF_PATH):
            os.remove(TEST_PDF_PATH)
            print(f"\nCleaned up {TEST_PDF_PATH}")


if __name__ == "__main__":
    asyncio.run(run_verification())
