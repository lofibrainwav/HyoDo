import asyncio
import os
import pathlib
import sys
from decimal import Decimal

# Ensure pythonpath includes afo-core
sys.path.append(os.path.join(pathlib.Path.cwd(), "packages/afo-core"))

from AFO.julie_cpa.services.julie_service import JulieService


async def verify_julie_royal():
    print("🔹 Initializing Julie CPA (Royal Edition) Verification...")
    service = JulieService()

    # Scenario 1: Happy Path (Dry Run)
    print("\n🔹 [Scenario 1] Happy Path (Dry Run)")
    valid_data = {
        "transaction_id": "TX-1234567890",
        "amount": Decimal(50000),
        "currency": "KRW",
        "category": "Food",
        "description": "Family Dinner",
    }
    # [Refactor] Passing dynamic account_id
    res1 = await service.process_transaction(valid_data, account_id="ACC-ROYAL-001", dry_run=True)
    if res1["success"] and res1["mode"] == "DRY_RUN":
        print("✅ Scenario 1 PASS")
    else:
        print(f"❌ Scenario 1 FAIL: {res1}")

    # Scenario 2: Fog of War (Missing Data)
    print("\n🔹 [Scenario 2] Fog of War (Empty Data)")
    foggy_data = {}
    res2 = await service.process_transaction(foggy_data, account_id="ACC-ROYAL-001")
    if not res2["success"] and "Fog" in res2["reason"]:
        print("✅ Scenario 2 PASS (Blocked by Friction Manager)")
    else:
        print(f"❌ Scenario 2 FAIL: {res2}")

    # Scenario 3: The Prince (Strict Validation)
    print("\n🔹 [Scenario 3] Strict Validation (Zero Amount)")
    bad_data = valid_data.copy()
    bad_data["amount"] = Decimal(0)  # Invalid
    res3 = await service.process_transaction(bad_data, account_id="ACC-ROYAL-001")
    if not res3["success"] and "cannot be zero" in res3["reason"]:
        print("✅ Scenario 3 PASS (Blocked by Pydantic Validator)")
    else:
        print(f"❌ Scenario 3 FAIL: {res3}")

    # Scenario 4: Three Kingdoms (Live Connect)
    print("\n🔹 [Scenario 4] Live Execution & Resilience")
    # Using valid data in live mode
    res4 = await service.process_transaction(valid_data, account_id="ACC-ROYAL-001", dry_run=False)
    if res4["success"] and res4["bank_sync"]:
        print("✅ Scenario 4 PASS (Connected to Bank)")
    else:
        print(f"❌ Scenario 4 FAIL: {res4}")

    print("\n✨ Julie CPA Royal Verification Complete.")


if __name__ == "__main__":
    asyncio.run(verify_julie_royal())
