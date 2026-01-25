# Trinity Score: 90.0 (Established by Chancellor)
"""Grok Auto Connect - The Chrome Link
Phase 15: The Grok Singularity

Description:
    Automatically extracts x.com/twitter.com authentication cookies
    from the user's local Google Chrome browser.
"""

import json
import logging
import os

import browser_cookie3

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GrokLink")

SESSION_FILE = "secrets/grok_session.json"


def extract_grok_token() -> None:
    print("🕵️‍♂️ [GrokLink] Scanning ALL Original Chrome Profiles for x.com keys...")

    base_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    profiles = ["Default"] + [f"Profile {i}" for i in range(1, 10)]

    found_token = None
    found_ct0 = None

    for profile in profiles:
        cookie_file = os.path.join(base_path, profile, "Cookies")
        if not os.path.exists(cookie_file):
            continue

        print(f"📂 Checking {profile}...")
        try:
            cj = browser_cookie3.chrome(cookie_file=cookie_file, domain_name="x.com")
            for cookie in cj:
                if cookie.name == "auth_token":
                    found_token = cookie.value
                    print(f"🔥 Found auth_token in {profile}: {found_token[:6]}...")
                elif cookie.name == "ct0":
                    found_ct0 = cookie.value

            if not found_token:
                # Try twitter.com
                cj = browser_cookie3.chrome(cookie_file=cookie_file, domain_name="twitter.com")
                for cookie in cj:
                    if cookie.name == "auth_token":
                        found_token = cookie.value
                        print(
                            f"🔥 Found auth_token in {profile} (via twitter): {found_token[:6]}..."
                        )
                    elif cookie.name == "ct0":
                        found_ct0 = cookie.value

            if found_token:
                break

        except Exception:
            # db lock or generic error
            # print(f"   (Skip {profile}: {e})")
            pass

    if found_token:
        # Save to secrets
        os.makedirs("secrets", exist_ok=True)
        secrets = {"auth_token": found_token}
        if found_ct0:
            secrets["ct0"] = found_ct0

        with open(SESSION_FILE, "w") as f:
            json.dump(secrets, f, indent=2)

        print(f"💾 Grok Session saved to {SESSION_FILE}")
        print("🚀 Connection Established! Grok Engine is now ONLINE.")
    else:
        print("❌ Could not find 'auth_token' in ANY profile.")
        print("   Please make sure you are logged into x.com in Chrome.")


if __name__ == "__main__":
    extract_grok_token()
