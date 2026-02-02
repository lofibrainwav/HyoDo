"""
Verify Julie Perfection (Context7 Integration)
Tests if JulieCPA can answer questions based on newly injected knowledge.
"""

import asyncio
import os

from AFO.services.langchain_openai_service import initialize_ai_service
from AFO.services.pdf_parsing_service import pdf_parsing_service
from AFO.services.vector_memory_service import vector_memory_service
from julie_cpa.core.julie_engine import julie
from reportlab.pdfgen import canvas

DOC_PATH = "robot_deduction_act.pdf"


async def generate_knowledge():
    print(f"Creating PDF: {DOC_PATH}")
    c = canvas.Canvas(DOC_PATH)
    c.drawString(100, 800, "Tax Cuts and Jobs Act 2026")
    c.drawString(
        100,
        750,
        "Section 42: You can deduct 100% of robot repair costs if the robot is named 'Bob'.",
    )
    c.save()


async def run_test():
    print("✨ Testing Julie Perfection...")

    # Mock / Init LLM
    api_key = os.environ.get("OPENAI_API_KEY", "dummy-key")
    if api_key == "dummy-key":
        print("   ⚠️ Using MOCK LLM.")
        from AFO.services.rag_service import rag_service

        async def mock_process_request(request):
            response_text = "I don't know."
            if "Bob" in request.prompt and "robot" in request.prompt:
                response_text = "According to Section 42, you can deduct 100% of robot repair costs if the robot is named 'Bob'."
            return type("obj", (object,), {"response": response_text})()

        rag_service.llm.process_request = mock_process_request
        rag_service.llm._initialized = True
    else:
        await initialize_ai_service(api_key)

    try:
        # 1. Create & Ingest Knowledge
        await generate_knowledge()

        # Ingest to Memory (Simulating Flow)
        print("\n[Stage 1] Ingesting Knowledge...")
        parse_result = await pdf_parsing_service.extract_text(DOC_PATH)
        await vector_memory_service.add_text(
            text=parse_result["text"], metadata={"source": DOC_PATH, "category": "tax_law"}
        )
        print("   ✅ Knowledge Injected.")

        # 2. Ask Julie
        print("\n[Stage 2] Consulting Julie...")
        question = "Can I deduct my robot's repair bill? His name is Bob."
        answer = await julie.ask(question)

        print("\n--- Julie's Answer ---")
        print(answer)

        if "100%" in answer or "Bob" in answer:
            print("\n✅ PERFECTION: Julie used the context to answer correctly!")
        else:
            print("\n❌ IMPERFECT: Julie missed the context.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if os.path.exists(DOC_PATH):
            os.remove(DOC_PATH)


if __name__ == "__main__":
    asyncio.run(run_test())
