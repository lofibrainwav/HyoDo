import asyncio
import logging
from AFO.utils.resilience_decorator import shield

# Setup logging to see the shield output
logging.basicConfig(level=logging.INFO)


@shield(fallback="Sync Fallback Success", pillar="TEST")
def test_sync_fail():
    print("Testing sync failure...")
    raise ValueError("Original Sync Error")


@shield(fallback="Async Fallback Success", pillar="TEST")
async def test_async_fail():
    print("Testing async failure...")
    raise ValueError("Original Async Error")


@shield(fallback="Should not trigger", pillar="TEST")
def test_sync_pass():
    return "Sync Pass"


@shield(fallback="Should not trigger", pillar="TEST")
async def test_async_pass():
    return "Async Pass"


async def main():
    print("--- Starting Shield Verification ---")

    # 1. Sync Fail
    res1 = test_sync_fail()
    print(f"Result 1 (Sync Fail): {res1}")
    assert res1 == "Sync Fallback Success"

    # 2. Async Fail
    res2 = await test_async_fail()
    print(f"Result 2 (Async Fail): {res2}")
    assert res2 == "Async Fallback Success"

    # 3. Sync Pass
    res3 = test_sync_pass()
    print(f"Result 3 (Sync Pass): {res3}")
    assert res3 == "Sync Pass"

    # 4. Async Pass
    res4 = await test_async_pass()
    print(f"Result 4 (Async Pass): {res4}")
    assert res4 == "Async Pass"

    print("--- Shield Verification Complete: ALL PASSED ---")


if __name__ == "__main__":
    asyncio.run(main())
