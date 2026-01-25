# Trinity Score: 90.0 (Established by Chancellor)
"""Grok.com Static Cookie Dump
Target: grok.com (Standalone, Chrome DB)
Purpose: Extract session cookies without launching Chrome (bypassing lock issues).
"""

import json
import os
import shutil

import browser_cookie3

SESSION_FILE = "secrets/grok_com_session.json"


def dump_cookies() -> None:
    print("🕵️‍♂️ [Grok.com] Reading Chrome Cookies directly...")

    try:
        # browser_cookie3 automatically finds the Chrome cookie DB
        # domain_name filter is efficient
        cj = browser_cookie3.chrome(domain_name="grok.com")

        relevant_cookies = {}
        found = False

        for cookie in cj:
            found = True
            relevant_cookies[cookie.name] = cookie.value

            # Print potentially key tokens
            if any(k in cookie.name for k in ["token", "session", "auth"]):
                print(f"   -> Found Access Token: {cookie.name} = {cookie.value[:10]}...")

        if found:
            os.makedirs("secrets", exist_ok=True)
            with open(SESSION_FILE, "w") as f:
                json.dump(relevant_cookies, f, indent=2)
            print(
                f"✅ SUCCESS: Captured session! Saved {len(relevant_cookies)} cookies to {SESSION_FILE}"
            )

        else:
            print("❌ No cookies found for 'grok.com'.")
            print("   - Are you logged in to https://grok.com?")
            print("   - Is the domain exactly 'grok.com'?")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 If 'database is locked', try copying the file manually or closing Chrome deeply.")


if __name__ == "__main__":
    dump_cookies()
