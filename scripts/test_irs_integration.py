"""
Verify Julie IRS Capabilities
Tests if JulieCPA can connect to the IRS Client, fetch a transcript, and analyze it.
"""

import asyncio

from julie_cpa.core.julie_engine import julie


async def run_test():
    print("🏦 Testing Julie's IRS Connection...")

    # 1. Analyze 2024 Records
    # This should trigger the Mock Client, fetch the Mock Transcript, and return the Good News.

    year = 2024
    result = await julie.analyze_irs_records(year)

    print("\n--- Analysis Result ---")
    print(result)

    if "Transaction 846" in result and "GOOD NEWS" in result:
        print("\n✅ SUCCESS: Julie successfully pulled and analyzed IRS records.")
    else:
        print("\n❌ FAILED: Analysis did not match expectations.")


if __name__ == "__main__":
    asyncio.run(run_test())
