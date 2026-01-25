import asyncio
import sys

from playwright.async_api import async_playwright


async def verify_chat():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # or False to see
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        print("🌐 Navigating to Dashboard...")
        try:
            await page.goto("http://localhost:3000", timeout=30000)
            await page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"❌ Failed to load dashboard: {e}")
            sys.exit(1)

        # 1. Check Button Presence
        print("🔍 Looking for Floating Chat Button...")
        button = page.locator("button:has(svg.lucide-message-circle)")
        await button.wait_for(state="visible", timeout=5000)
        print("✅ Button Found!")

        await page.screenshot(
            path=".gemini/antigravity/brain/a805a42d-de23-4690-bbb3-e36fd1dfc691/verify_chat_button.png"
        )
        print("📸 Screenshot text: Button Initial State")

        # 2. Click Button
        print("🖱️ Clicking Chat Button...")
        await button.click()
        await page.wait_for_timeout(1000)  # Wait for animation

        # 3. Check Modal Presence
        print("🔍 Checking for Modal...")
        # GraphRAGQuery has "Ask the Kingdom" text
        modal_text = page.locator("text=Ask the Kingdom")
        await modal_text.wait_for(state="visible", timeout=5000)
        print("✅ Chat Modal Opened!")

        await page.screenshot(
            path=".gemini/antigravity/brain/a805a42d-de23-4690-bbb3-e36fd1dfc691/verify_chat_modal.png"
        )
        print("📸 Screenshot text: Chat Modal State")

        await browser.close()
        print("🎉 Verification Complete.")


if __name__ == "__main__":
    asyncio.run(verify_chat())
