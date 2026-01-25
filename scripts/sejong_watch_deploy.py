import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("AFO_BASE_URL", "http://localhost:18010").rstrip("/")
OUT = os.environ.get("SEJONG_OUT", "artifacts/sejong/phase4_action2_watch.json")
SLEEP = int(os.environ.get("SEJONG_SLEEP_SEC", "10"))
MAX = int(os.environ.get("SEJONG_MAX_SEC", "7200"))


def get(url: str) -> None:
    req = urllib.request.Request(url, headers={"accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        # e.g. Connection refused
        return 0, str(e)


def main() -> None:
    t0 = time.time()

    # Ensure artifacts dir exists
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    print(f"🔭 Sejong Watchtower Active. Target: {BASE}")
    print(f"📝 Logging to: {OUT}")

    while True:
        elapsed = int(time.time() - t0)
        if elapsed > MAX:
            print("⏱️ TIMEOUT: Sejong Monitor stopping after 2 hours.")
            return 2

        h_sc, h_body = get(f"{BASE}/api/health/comprehensive")
        s_sc, s_body = get(f"{BASE}/api/skills")

        ok_health = False
        ok_skills = False
        skills_count = None

        # Check Health (200 + organs check)
        if h_sc == 200:
            try:
                d = json.loads(h_body)
                keys = set(d.keys()) if isinstance(d, dict) else set()
                # Flexible check for key naming variations
                ok_health = any(k in keys for k in ("organs_v2", "organsV2", "organs", "organs_v1"))
            except Exception:
                ok_health = False

        # Check Skills (200 + list check)
        if s_sc == 200:
            try:
                d = json.loads(s_body)
                skills = d.get("skills") if isinstance(d, dict) else None
                if skills:
                    ok_skills = True
                    skills_count = len(skills)
            except Exception:
                ok_skills = False

        status_data = {
            "as_of_sec": elapsed,
            "target_url": BASE,
            "health_status_code": h_sc,
            "skills_status_code": s_sc,
            "health_ok": ok_health,
            "skills_complete": ok_skills,
            "skills_count": skills_count,
            "timestamp": time.time(),
        }

        try:
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Write failed: {e}")

        # Console log (brief)
        # 0 = Connection Refused / Down
        prefix = "✅" if (ok_health and ok_skills) else "⏳"
        print(
            f"[{elapsed:>4}s] {prefix} Health:{h_sc} (OK:{ok_health}) | Skills:{s_sc} (OK:{ok_skills} Cnt:{skills_count})"
        )

        if ok_health and ok_skills:
            print("🎉 SEJONG VERIFIED: Remote Soul Engine is ALIVE & SKILLED!")
            print("🚀 Phase 4 Action 2 is COMPLETE.")
            return 0

        time.sleep(SLEEP)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n👋 Sejong Monitor stopped by user.")
        sys.exit(130)
