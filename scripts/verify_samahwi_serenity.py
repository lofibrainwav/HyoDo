import asyncio
import logging
import sys

# Setup Path
sys.path.append("/Users/brnestrm/AFO_Kingdom/packages/afo-core")

# Configure Logging to stdout
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from AFO.scholars.yeongdeok import yeongdeok


async def verify_serenity():
    print("🧘 Verifying Samahwi's Serenity (No Warnings expected)...")

    # This call used to trigger a WARNING if MLX model was missing
    response = await yeongdeok.consult_samahwi("Hello, are you serene?")

    print(f"\nResponse received: {response[:50]}...")
    print("✅ Call completed.")


if __name__ == "__main__":
    asyncio.run(verify_serenity())
