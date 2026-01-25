import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

SOUL = os.getenv("SOUL_ENGINE_URL", "http://127.0.0.1:8010").rstrip("/")
DASH = os.getenv("DASHBOARD_URL", "http://127.0.0.1:3000").rstrip("/")


def get_json(url: str, timeout: int = 2) -> dict:
    """Safely fetch JSON from a URL using standard library."""
    if not url.lower().startswith(("http://", "https://")):
        return {}
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # nosec B310
            if 200 <= response.status < 300:
                return json.loads(response.read().decode("utf-8"))
    except Exception:
        pass
    return {}


def get_headers_snippet(url: str, lines: int = 5, timeout: int = 2) -> str:
    """Fetch headers securely and return top N lines."""
    if not url.lower().startswith(("http://", "https://")):
        return ""
    try:
        # Note: Some servers might strictly require GET, but HEAD is efficient
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec B310
            # Reconstruct status line roughly (urllib abstracts it)
            output = [f"HTTP/1.1 {response.status} {response.reason}"]
            for k, v in response.headers.items():
                output.append(f"{k}: {v}")
            return "\n".join(output[:lines])
    except urllib.error.HTTPError as e:
        # If HEAD fails (e.g. 404/405), try to capture that status too
        output = [f"HTTP/1.1 {e.code} {e.reason}"]
        for k, v in e.headers.items():
            output.append(f"{k}: {v}")
        return "\n".join(output[:lines])
    except Exception:
        pass
    return ""


def run() -> dict:
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    evidence_dir = Path("artifacts/trinity") / ts
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # 1. Backend Health Checks
    health_j = get_json(f"{SOUL}/health")
    b_organs = health_j.get("organs") or {}
    b_keys = sorted(b_organs.keys())
    ks = len(b_organs) if b_organs else None

    # 2. Frontend Kingdom Status Checks
    ks2_j = get_json(f"{DASH}/api/kingdom-status")
    f_organs = ks2_j.get("organs") or []
    f_names = [o.get("name") for o in f_organs if isinstance(o, dict)]

    # 3. Code Analysis (Static)
    route_path = Path("packages/dashboard/src/app/api/kingdom-status/route.ts")
    route_txt = route_path.read_text(encoding="utf-8") if route_path.exists() else ""
    has_try = "try" in route_txt
    has_catch = "catch" in route_txt and "Backend fetch failed" in route_txt
    has_return = "return NextResponse.json" in route_txt

    out = {
        "asof": ts,
        "backend": {
            "url": SOUL,
            "health_http_head": get_headers_snippet(f"{SOUL}/health"),
            "organs_keys": b_keys,
            "organs_keys_length": ks,
        },
        "frontend": {
            "url": DASH,
            "kingdom_status_http_head": get_headers_snippet(f"{DASH}/api/kingdom-status"),
            "organs_len": len(f_organs),
            "organs_names": f_names,
        },
        "t20_ssot_checks": {
            "backend_organs_4": (ks == 4 if ks is not None else False),
            "frontend_organs_5": (len(f_organs) == 5),
            "frontend_has_eyes": ("Eyes" in f_names),
            "route_try_catch_return": (has_try and has_catch and has_return),
        },
    }

    (evidence_dir / "full_stack_verify.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
