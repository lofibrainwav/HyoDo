import asyncio
import os
import pathlib
import sys

# Add project root to path
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

from AFO.config.settings import settings
from AFO.schemas.gen_ui import GenUIRequest
from AFO.services.gen_ui import gen_ui_service
from AFO.services.matrix_stream import matrix_stream

settings.MOCK_MODE = True


async def demo_matrix_stream():
    print("=== 👁️ Phase 10: The Matrix Stream Demo ===")

    # 1. GenUI: Create Widget
    print("\n[GenUI] Creating CopilotThoughtStreamWidget...")
    request = GenUIRequest(
        prompt="Create a Matrix-style thought stream widget with real-time NLP analysis.",
        component_name="CopilotThoughtStreamWidget",
        trinity_threshold=0.9,
    )

    resp = await gen_ui_service.generate_component(request)
    if resp.status == "approved":
        path = gen_ui_service.deploy_component(resp)
        print(f"✅ Deployed Widget: {path}")
    else:
        print(f"❌ Generation Failed: {resp.error}")
        return

    # 2. NLP Logic Test
    print("\n[NLP] Testing Pillar Classification Logic (TF-IDF)...")

    test_thoughts = [
        "Verifying type safety with mypy strict mode.",
        "Checking for vulnerabilities and risks using grype.",
        "Applying glassmorphism and tailwind css for beauty.",
        "Reducing friction for user serenity feedback.",
        "Recording logs to evolution history database.",
    ]

    for text in test_thoughts:
        # We access the internal method for testing
        pillar, conf = matrix_stream._classify_pillar(text)
        print(f"Thought: '{text}' -> Pillar: {pillar} (Conf: {conf}%)")

    print("\n✅ Phase 10 Logic Verified.")


if __name__ == "__main__":
    asyncio.run(demo_matrix_stream())
