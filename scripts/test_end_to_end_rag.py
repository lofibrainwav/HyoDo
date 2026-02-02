"""
End-to-End RAG Verification
Tests the full lifecycle: PDF Creation -> Parsing -> Memory -> Retrieval -> Generating Answer.
"""

import asyncio
import os

from AFO.services.langchain_openai_service import initialize_ai_service
from AFO.services.pdf_parsing_service import pdf_parsing_service
from AFO.services.rag_service import rag_service
from AFO.services.vector_memory_service import vector_memory_service
from reportlab.pdfgen import canvas

PDF_PATH = "protocol_99.pdf"


async def generate_pdf():
    print(f"Creating PDF: {PDF_PATH}")
    c = canvas.Canvas(PDF_PATH)
    c.drawString(100, 800, "AFO Kingdom Official Protocols")
    c.drawString(
        100, 750, "Protocol 99: When entering the throne room, one must always wear a purple hat."
    )
    c.save()


async def run_pipeline():
    print("🚀 Starting End-to-End RAG Test...")

    # 0. Mock LLM Setup (same as stage 2)
    api_key = os.environ.get("OPENAI_API_KEY", "dummy-key")
    if api_key == "dummy-key":
        print("   ⚠️ Using MOCK LLM for generation verification.")

        async def mock_process_request(request):
            # Check if context was injected
            response_text = "I don't know."
            if "Protocol 99" in request.prompt and "purple hat" in request.prompt:
                response_text = (
                    "According to the context, Protocol 99 requires wearing a purple hat."
                )
            return type("obj", (object,), {"response": response_text})()

        rag_service.llm.process_request = mock_process_request
        rag_service.llm._initialized = True
    else:
        await initialize_ai_service(api_key)

    try:
        # 1. Generate
        await generate_pdf()

        # 2. Ingest (Simulating the Classifier's job)
        print("\n[Step 1] Ingesting PDF...")
        parse_result = await pdf_parsing_service.extract_text(PDF_PATH)
        if not parse_result["success"]:
            raise Exception(f"PDF Parse Failed: {parse_result['error']}")

        print(f"   - Extracted {len(parse_result['text'])} chars.")

        # Save to memory (The Classifier usually does this, we do it manually here to test the flow)
        await vector_memory_service.add_text(
            text=parse_result["text"],
            metadata={"source": PDF_PATH, "filename": PDF_PATH, "category": "protocol"},
        )
        print("   - Saved to Vector Memory.")

        # 3. Query
        query = "What does Protocol 99 say about hats?"
        print(f"\n[Step 2] Asking: '{query}'")

        result = await rag_service.ask(query)

        print("\n--- Final Answer ---")
        print(result["answer"])

        if "purple hat" in result["answer"]:
            print("\n✅ E2E SUCCESS: Julie read the PDF and answered correctly!")
        else:
            print("\n❌ E2E FAILED: Answer did not contain the expected info.")

    except Exception as e:
        print(f"\n❌ Pipeline Error: {e}")
    finally:
        if os.path.exists(PDF_PATH):
            os.remove(PDF_PATH)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
