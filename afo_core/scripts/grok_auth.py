# Trinity Score: 90.0 (Established by Chancellor)
"""Grok Browser Authentication Bridge
Phase 15: The Grok Singularity (Web Mode)

Usage:
    python grok_auth.py

Description:
    Opens a browser window for the user to login to x.com / grok.com.
    Once logged in, extracts the necessary session cookies (auth_token, ct0)
    and saves them to secrets/grok_session.json.
"""

import json
import os

from playwright.sync_api import sync_playwright

SESSION_FILE = "secrets/grok_session.json"
TARGET_URL = "https://x.com/i/grok"  # or https://grok.com


def authenticate_grok() -> None:
    print("🚀 [GrokAuth] Launching Browser for Authentication...")

    with sync_playwright() as p:
        # Launch browser (Headful so user can interact)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"👉 Please login to Grok at: {TARGET_URL}")
        page.goto(TARGET_URL)

        # Wait for user to login (Check for specific element that indicates logged in state)
        # We'll wait for the input box usually present in chat interface
        try:
            print("⏳ Waiting for login... (Time limit: 120s)")
            # Common selector for X/Grok input area or sidebar
            page.wait_for_selector('[data-testid="GrokDrawer"]', timeout=120000)
            print("✅ Login detected!")
        except Exception:
            print("⚠️ Timeout or Login detection failed. Saving verify screenshot.")
            page.screenshot(path="login_debug.png")
            # Continue anyway, maybe user is logged in but selector changed

        # Extract Cookies
        cookies = context.cookies()
        auth_cookies = {
            c["name"]: c["value"]
            for c in cookies
            if c["name"] in ["auth_token", "ct0", "x-csrf-token"]
        }

        if "auth_token" in auth_cookies:
            print(f"✅ Auth Token captured: {auth_cookies['auth_token'][:10]}...")

            # Save to file
            os.makedirs("secrets", exist_ok=True)
            with open(SESSION_FILE, "w") as f:
                json.dump(auth_cookies, f, indent=2)
            print(f"💾 Session saved to {SESSION_FILE}")
            print("🎉 Grok Bridge is ready!")
        else:
            print("❌ 'auth_token' not found in cookies. Please try again.")

        browser.close()


if __name__ == "__main__":
    authenticate_grok()
