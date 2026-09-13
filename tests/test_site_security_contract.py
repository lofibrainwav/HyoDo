"""Keep the public hyodo.app security configuration reviewable and complete."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERCEL_CONFIG = REPO_ROOT / "site" / "vercel.json"
ROBOTS = REPO_ROOT / "site" / "public" / "robots.txt"
SECURITY_TXT = REPO_ROOT / "site" / "public" / ".well-known" / "security.txt"


REQUIRED_HEADERS = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), geolocation=(), microphone=(), payment=(), usb=()",
    "Access-Control-Allow-Origin": "https://hyodo.app",
}


def _response_headers() -> dict[str, str]:
    config = json.loads(VERCEL_CONFIG.read_text())
    rules = config["headers"]
    assert [rule["source"] for rule in rules] == ["/(.*)"]
    return {item["key"]: item["value"] for item in rules[0]["headers"]}


def test_public_site_has_required_response_headers() -> None:
    headers = _response_headers()
    for key, value in REQUIRED_HEADERS.items():
        assert headers.get(key) == value

    csp = headers["Content-Security-Policy"]
    for directive in (
        "default-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "form-action 'self'",
        "upgrade-insecure-requests",
    ):
        assert directive in csp
    assert "Access-Control-Allow-Origin: *" not in str(headers)


def test_public_security_discovery_files_are_canonical() -> None:
    robots = ROBOTS.read_text()
    assert "User-agent: *" in robots
    assert "Sitemap: https://hyodo.app/sitemap-index.xml" in robots

    security_txt = SECURITY_TXT.read_text()
    assert "Contact: https://github.com/lofibrainwav/HyoDo/security/advisories/new" in security_txt
    assert "Policy: https://github.com/lofibrainwav/HyoDo/blob/main/SECURITY.md" in security_txt
    assert "Canonical: https://hyodo.app/.well-known/security.txt" in security_txt
    assert "Expires: 2027-09-13T00:00:00.000Z" in security_txt
