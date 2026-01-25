# scripts/verify_frontend_integration.py
"""
Browser Integration Test for AFO Kingdom Dashboard.
Verifies Trinity UI elements render correctly using Playwright.
"""

import asyncio
import os
import pathlib
import sys

# Ensure AFO package is importable
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)


async def verify_dashboard():
    """Verify Dashboard UI using Playwright."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright && playwright install")
        return False

    print("=== Browser Integration Test ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Dashboard URL (Next.js default port)
        dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:3000")

        try:
            print(f"[Action] Navigating to {dashboard_url}...")
            await page.goto(dashboard_url, timeout=10000)

            # Wait for page to load
            await page.wait_for_load_state("domcontentloaded")

            # Check for Trinity UI elements
            checks = []

            # 1. Check for main container
            main = await page.query_selector("main")
            checks.append(("Main Container", main is not None))

            # 2. Check for Trinity-related text (e.g., "Trinity", "Score", "Health")
            content = await page.content()
            has_trinity_text = "trinity" in content.lower() or "score" in content.lower()
            checks.append(("Trinity Text Present", has_trinity_text))

            # 3. Check for status indicator
            status = await page.query_selector('[class*="status"], [data-testid="status"]')
            checks.append(("Status Indicator", status is not None))

            # Print Results
            print("\n[Results]")
            all_passed = True
            for name, passed in checks:
                status = "✅" if passed else "❌"
                print(f"  {status} {name}: {'PASS' if passed else 'FAIL'}")
                if not passed:
                    all_passed = False

            await browser.close()

            if all_passed:
                print("\n✅ Browser Integration Test PASSED")
                return True
            print("\n⚠️ Some checks failed (Dashboard may not be running)")
            return False

        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            print("   (Is the dashboard running at http://localhost:3000?)")
            await browser.close()
            return False


if __name__ == "__main__":
    result = asyncio.run(verify_dashboard())
    sys.exit(0 if result else 1)
