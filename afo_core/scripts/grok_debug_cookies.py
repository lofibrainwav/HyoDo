# Trinity Score: 90.0 (Established by Chancellor)
"""Grok Cookie Forensics
Direct SQLite Access to verify if cookies exist (bypassing decryption)
"""

import os
import shutil
import sqlite3


def check_cookies() -> None:
    print("🕵️‍♂️ [CookieForensics] Deep Search...")

    base_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    profiles = ["Default"] + [f"Profile {i}" for i in range(1, 10)]

    found_any = False

    for profile in profiles:
        cookie_path = os.path.join(base_path, profile, "Cookies")
        if not os.path.exists(cookie_path):
            continue

        print(f"📂 Checking DB: {profile}")

        # Copy to temp to avoid lock
        temp_db = f"/tmp/cookies_{profile.replace(' ', '_')}.db"  # nosec B108
        try:
            shutil.copy2(cookie_path, temp_db)
        except OSError:
            print("   ⚠️ File Locked! (Chrome might still be running locally?)")
            continue

        try:
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()

            # Check for x.com or twitter.com or grok.com
            query = "SELECT host_key, name, path, creation_utc FROM cookies WHERE host_key LIKE '%x.com%' OR host_key LIKE '%twitter.com%' OR host_key LIKE '%grok.com%'"
            cursor.execute(query)
            rows = cursor.fetchall()

            count_auth = 0
            for row in rows:
                host, name, _path, created = row
                if name == "auth_token":
                    count_auth += 1
                    print(f"   🔥 FOUND 'auth_token' row! Host: {host}, Created: {created}")
                    found_any = True

            print(f"   => Total X/Twitter cookies: {len(rows)}, auth_tokens: {count_auth}")

            conn.close()
            os.remove(temp_db)

            if count_auth > 0:
                print(
                    f"✅ CONFIRMED: Auth token exists in {profile}. The previous script failed to decrypt it."
                )
                return profile

        except Exception as e:
            print(f"   ❌ DB Error: {e}")

    if not found_any:
        print("❄️  No 'auth_token' rows found in ANY profile database.")
        print("    Possibilities: Incognito mode? Different browser? Or not flushed to disk yet.")


if __name__ == "__main__":
    check_cookies()
