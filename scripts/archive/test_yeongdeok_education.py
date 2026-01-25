import asyncio
import sys

# Set PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent / "packages" / "afo-core"))

from AFO.scholars.yeongdeok import yeongdeok


async def verify_education():
    print("🎓 Verifying Yeongdeok's Education (The Scholar's Oath)...\n")

    # Question designed to trigger Identity & Rules
    prompt = "자네의 임무와 지켜야 할 원칙이 무엇인가? 짧게 대답하게."

    # We consult Samahwi (Truth) via Yeongdeok to see if the System Prompt (which applies to the session) holds.
    # Note: In the current architecture, Yeongdeok's SYSTEM_PROMPT might be passed only if the core logic supports it.
    # Let's check if `consult_samahwi` uses the Yeongdeok class's SYSTEM_PROMPT.
    # Actually, `yeongdeok.py` defines `SYSTEM_PROMPT` but it's not explicitly passed in `consult_samahwi`'s `_samahwi_mlx_logic`.
    # Wait, the code I modified:
    # `SYSTEM_PROMPT` is a class constant.
    # But `consult_samahwi` passes a hardcoded `system` string in `_samahwi_mlx_logic`.
    # The `_call_ollama` method accepts a `system` arg.

    # TEST STRATEGY:
    # I need to see if Yeongdeok ITSELF has a chat method, or if I should test his influence on the Sages.
    # Looking at the code: `yeongdeok` acts as a gateway.
    # The `SYSTEM_PROMPT` I updated is a class attribute, but is it USED?
    # Let's check `_call_ollama` implementation in the file content I viewed earlier.
    # It seems `SYSTEM_PROMPT` isn't actively injected into `_call_ollama` unless passed.
    #
    # Ah, I see. I might have updated a constant that needs to be WIRED IN.
    # Let's run a test where I explicitly ask him to "recite his oath" using a method that might use it,
    # OR acknowledge that I need to wire it into the `_consult_sage_core` or `_call_ollama` defaults.

    # Let's try finding out via a direct prompt first.

    # Using `consult_samahwi` which has its OWN system prompt in the code.
    # I should probably have updated the `consult_samahwi` system prompt string too
    # OR better, made `consult_samahwi` use `Yeongdeok .SYSTEM_PROMPT + specific instruction`.

    # Let's just ask basic identifying questions to see what he "thinks".

    response = await yeongdeok.consult_samahwi(prompt)
    print(f"🗣️ Response:\n{response}\n")


if __name__ == "__main__":
    asyncio.run(verify_education())
