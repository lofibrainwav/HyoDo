"""E2E Simulation - Refactored Wrapper.

Original code moved to: AFO/irs/e2e/
"""

import asyncio

from .e2e import E2ESimulator


async def main():
    simulator = E2ESimulator()
    summary = await simulator.run_all_tests()
    print(f"Simulation summary: {summary['passed_tests']}/{summary['total_tests']} passed.")
    return 0 if summary["failed_tests"] == 0 else 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
