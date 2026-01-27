# Trinity Score: 90.0 (Established by Chancellor)
"""Grok.com Capture Script
Target: grok.com (Standalone)
Purpose: Extract session cookies from the user's active Chrome session.
"""

import json
import os

from playwright.sync_api import sync_playwright

SESSION_FILE = "secrets/grok_com_session.json"
USER_DATA_DIR = "${HOME}/Library/Application Support/Google/Chrome"  # macOS default


def capture_grok_com() -> None:
    print("🕵️‍♂️ [Grok.com] Connecting to System Chrome...")

    with sync_playwright() as p:
        try:
            # Attempt to launch persistent context using the User Data Dir
            # tailored for macOS to get the actual user session
            browser = p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                channel="chrome",
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )

            page = browser.pages[0]
            print("🌍 Navigating to https://grok.com/ ...")
            page.goto("https://grok.com/")
            page.wait_for_timeout(3000)  # Wait for hydration

            cookies = browser.cookies("https://grok.com")

            # Filter for likely auth candidates
            # Grok.com likely uses specific tokens. We'll save ALL for inspection first
            # but prioritize looking for common auth patterns.
            print(f"🍪 Found {len(cookies)} cookies.")

            relevant_cookies = {}
            for c in cookies:
                # Capture everything for now to be safe, filtering later
                relevant_cookies[c["name"]] = c["value"]
                if (
                    "token" in c["name"].lower()
                    or "auth" in c["name"].lower()
                    or "session" in c["name"].lower()
                ):
                    print(f"   -> Found potential token: {c['name']}")

            # Save
            if relevant_cookies:
                os.makedirs("secrets", exist_ok=True)
                with open(SESSION_FILE, "w") as f:
                    json.dump(relevant_cookies, f, indent=2)
                print(f"✅ Saved {len(relevant_cookies)} cookies to {SESSION_FILE}")
            else:
                print("❌ No cookies found for grok.com. Are you logged in?")

            # Keep open briefly to confirm visual success if needed
            # page.wait_for_timeout(2000)
            browser.close()

        except Exception as e:
            print(f"❌ Error: {e}")
            print(
                "💡 Tip: Close Google Chrome completely before running this (to unlock the profile)."
            )


if __name__ == "__main__":
    capture_grok_com()
