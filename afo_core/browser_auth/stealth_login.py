# Trinity Score: 90.0 (Established by Chancellor)
# mypy: ignore-errors
"""
Stealth Login Automation
Browser Bridge Phase 9: "The Ghost"
"""

import asyncio
import os
import sys

from playwright.async_api import async_playwright

# Ensure AFO is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
afo_dir = os.path.dirname(os.path.dirname(current_dir))  # AFO_Kingdom
if afo_dir not in sys.path:
    sys.path.append(afo_dir)

try:
    from AFO.api_wallet import APIWallet

    print("✅ APIWallet module loaded successfully.")
except ImportError as e:
    print(f"⚠️ APIWallet import failed: {e}")
    # Fallback for direct execution
    try:
        sys.path.append(os.path.join(current_dir, ".."))
        from api_wallet import APIWallet

        print("✅ APIWallet loaded via fallback.")
    except ImportError:
        print("❌ APIWallet NOT found. Tokens will NOT be saved.")
        APIWallet = None


class Stealther:
    """
    Jipijigi (Know Yourself): Mimic a real human to avoid detection.
    """

    @staticmethod
    async def apply_stealth(page):
        # 1. Mask Webdriver
        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
        )

        # 2. Mock Languages
        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """
        )

        # 3. Mock Plugins (Basic)
        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """
        )

        # 4. Chrome Runtime
        await page.add_init_script(
            """
            window.chrome = { runtime: {} };
        """
        )


async def run_stealth_login(service="openai"):
    """
    Launches a stealth browser for the user to log in, then extracts tokens.
    """
    print(f"👻 Starting Stealth Browser for {service}...")

    target_url = ""
    token_keys = []

    if service == "openai":
        target_url = "https://chat.openai.com"
        token_keys = ["__Secure-next-auth.session-token"]
    elif service == "anthropic":
        target_url = "https://claude.ai"
        token_keys = ["sessionKey"]
    elif service == "google":
        target_url = "https://aistudio.google.com"
        token_keys = ["__Secure-1PSID"]

    # USE REAL CHROME USER DATA to bypass Cloudflare
    user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    print(f"🕵️ Target User Data Dir: {user_data_dir}")

    # Try to find Real Chrome (Bypasses Cloudflare better than Chromium)
    executable_path = None
    potential_chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(potential_chrome_path):
        executable_path = potential_chrome_path
        print(f"🕵️ Using System Chrome Key: {executable_path}")
    else:
        print("⚠️ System Chrome not found, falling back to bundled Chromium.")

    async with async_playwright() as p:
        # Launch Persistent Context (Saves cookies to disk!)
        print(f"👻 Starting Persistent Stealth Browser for {service}...", flush=True)

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--exclude-switches=enable-automation",
            "--use-fake-ui-for-media-stream",
        ]

        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            executable_path=executable_path,  # Use Real Chrome if found
            headless=False,
            args=launch_args,
            ignore_default_args=["--enable-automation"],  # Critical for stealth
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await Stealther.apply_stealth(page)

        print(f"👉 Please log in to {service} in the opened window.", flush=True)
        try:
            await page.goto(target_url)
        except Exception as e:
            print(f"⚠️ Nav error (ignoring): {e}", flush=True)

        # Wait for token to appear in cookies
        found_token = None
        attempt = 0
        while not found_token:
            cookies = await context.cookies()
            for cookie in cookies:
                # print(f"DEBUG: Cookie {cookie['name']}", flush=True)
                if cookie["name"] in token_keys:
                    found_token = cookie["value"]
                    print(f"✅ Token Found: {cookie['name']}", flush=True)
                    break

            if not found_token:
                attempt += 1
                if attempt % 5 == 0:
                    print(
                        f"⏳ Waiting for login... ({len(cookies)} cookies seen)",
                        flush=True,
                    )
                await asyncio.sleep(2)

            if not found_token:
                print("⏳ Waiting for login... (Check your browser)")
                await asyncio.sleep(3)

        print(f"🎣 Captured Token: {found_token[:15]}...")

        # Save to Wallet
        if APIWallet:
            wallet = APIWallet()
            key_name = f"{service}_session_stealth"
            wallet.add(
                name=key_name,
                api_key=found_token,
                key_type="session_token",
                service=service,
                description=f"Union[SEALED, Extracted] via Stealth Mode ({service}) | Do not disturb until expired.",
                read_only=False,
            )
            print(f"💾 Securely saved to Wallet as '{key_name}'", flush=True)
        else:
            print(f"🔑 Token (Not Saved): {found_token}", flush=True)

        print("🎉 Mission Complete. Closing browser in 5 seconds...", flush=True)
        await asyncio.sleep(5)
        await asyncio.sleep(5)
        await context.close()


if __name__ == "__main__":
    # Default to openAI if no args (or user can change)
    service_arg = "openai"
    if len(sys.argv) > 1:
        service_arg = sys.argv[1]
    asyncio.run(run_stealth_login(service_arg))
