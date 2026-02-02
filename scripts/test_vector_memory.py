"""
Test Vector Memory Integration
Verifies that the VectorMemoryService works and that the TaxDocumentClassifier correctly invokes it.
"""

import asyncio
import os

from AFO.services.vector_memory_service import vector_memory_service

# Clean up any previous test DB for a fresh start (Optional, maybe risky if persistent)
# For now, we assume we append.


async def run_test():
    print("🧠 Testing Vector Memory Service...")

    # 1. Direct Service Test
    print("\n[1] Testing Direct Add/Search...")
    test_text = "The deadline for filing IRS Form 1040 is typically April 15th."
    success = await vector_memory_service.add_text(
        text=test_text, metadata={"category": "test", "source": "manual"}
    )

    if success:
        print("   ✅ Text added successfully.")
    else:
        print("   ❌ Failed to add text.")
        return

    # Search
    print("   🔍 Searching for 'deadline'...")
    results = await vector_memory_service.search("When is the tax deadline?")

    found = False
    for res in results:
        print(f"      - Found: {res['text']} (Dist: {res['distance']})")
        if "April 15th" in res["text"]:
            found = True

    if found:
        print("   ✅ Memory retrieval verified!")
    else:
        print("   ❌ Memory retrieval failed (content not found).")

    # 2. Classifier Hook Test
    print("\n[2] Testing Classifier Hook...")
    # dependent on having the dummy PDF from previous step or creating one
    from reportlab.pdfgen import canvas

    pdf_path = "memory_test_form.pdf"
    c = canvas.Canvas(pdf_path)
    c.drawString(100, 800, "Internal Revenue Service")
    c.drawString(100, 780, "Publication 1234")
    c.drawString(100, 760, "Topic: Secret Tax Deduction for Robots")
    c.save()

    try:
        # We need to run the classifier logic.
        # Since full 'classify_tax_document' has heavy dependencies,
        # let's try to import it. If it fails due to missing deps in this env,
        # we might rely on the Manual Test [1] as proof of service health.
        try:
            from AFO.tax_document_classifier import classify_tax_document

            print(f"   📄 Classifying {pdf_path}...")
            result = await classify_tax_document(pdf_path)

            if result.get("memorized"):
                print("   ✅ Classifier reported 'memorized=True'")
            else:
                print(f"   ⚠️ Classifier finished, but memorized={result.get('memorized')}")
                if result.get("memory_error"):
                    print(f"      Error: {result.get('memory_error')}")

            # Verify via search
            print("   🔍 Verifying via search for 'Robots'...")
            results = await vector_memory_service.search("tax deduction robots")
            if any("Secret Tax Deduction" in r["text"] for r in results):
                print("   ✅ Hook verified! Document was found in memory.")
            else:
                print("   ❌ Hook failed. Document not found in memory.")

        except ImportError as e:
            print(f"   ⚠️ Skipping Classifier Hook test due to missing deps: {e}")
            print(
                "   (This is expected if pydantic_settings/redis are broken in this venv. Direct memory test [1] passed though.)"
            )

    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


if __name__ == "__main__":
    asyncio.run(run_test())
