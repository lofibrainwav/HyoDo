# Trinity Score: 90.0 (Established by Chancellor)
import asyncio
import sys
from pathlib import Path

# Add root directory to sys.path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from AFO.scholars.yeongdeok import yeongdeok


async def verify_yeongdeok():
    print("🛡️ Yeongdeok Scholar Live Verification")
    print(f"Base URL: {yeongdeok.base_url}")
    print(f"Model: {yeongdeok.model}")

    # Simple docgen test
    code_snippet = "def add(a, b): return a + b"
    print(f"\n[Input Code]: {code_snippet}")

    response = await yeongdeok.document_code(code_snippet)

    print(f"\n[Response]:\n{response}")

    if "Ollama 호출 실패" in response or "처리 실패" in response:
        print("\n❌ Yeongdeok verification failed (Ollama connection issue?)")
    else:
        print("\n✅ Yeongdeok verification successful")


if __name__ == "__main__":
    asyncio.run(verify_yeongdeok())
