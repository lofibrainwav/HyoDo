# ruff: noqa
import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(".").resolve()
OUT_DIR = ROOT / "artifacts" / "ssot_roadmap_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = os.environ.get("AFO_BASE_URL", "http://localhost:8010").rstrip("/")

    "Antigravity",
    "T1.1",
    "T1.2",
    "T1.3",
    "T2.1",
    "T2.2",
    "T2.3",
    "T3.1",
    "T3.2",
    "T3.3",
    "Organs V1",
    "Ollama",
    "RAG Service",
    "Trinity CI",
    "GenUI",
    "TICKET-045",
    "TICKET-046",
    "TICKET-047",
]

SCAN_EXTS = {".md", ".py", ".json", ".yaml", ".yml", ".txt"}
MAX_BYTES = 2_000_000


def http_get_json(path: str) -> None:
    url = f"{BASE_URL}{path}"
    req = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=3) as r:
            raw = r.read().decode("utf-8", errors="replace")
            try:
                return {
                    "ok": True,
                    "url": url,
                    "status": r.status,
                    "json": json.loads(raw),
                }
            except json.JSONDecodeError:
                return {"ok": True, "url": url, "status": r.status, "raw": raw[:2000]}
    except (HTTPError, URLError, TimeoutError) as e:
        return {"ok": False, "url": url, "error": str(e)}


def scan_repo() -> None:
    hits = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in SCAN_EXTS:
            continue
        try:
            if p.stat().st_size > MAX_BYTES:
                continue
            data = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        for pat, ticket in PATTERNS.items():
            idx = data.find(pat)
            if idx != -1:
                start = max(0, idx - 80)
                end = min(len(data), idx + 200)
                snippet = data[start:end].replace("\n", "\\n")
                if len(snippet) > 80:
                    snippet = snippet[:40] + "..." + snippet[-40:]
                issues.append(
                    {
                        "path": str(p.relative_to(ROOT)),
                        "ticket": ticket,
                        "line": data[:idx].count("\n") + 1,
                        "snippet": snippet,
                    }
                )
                hits.append({"file": str(p.relative_to(ROOT)), "pattern": pat, "ticket": ticket})
    return hits
    payload = {
        "as_of": ts,
        "base_url": BASE_URL,
        "repo_scan_hits": scan_repo(),
        "endpoints": {
            "/health": http_get_json("/health"),
            "/api/health": http_get_json("/api/health"),
            "/api/5pillars": http_get_json("/api/5pillars"),
            "/chancellor/engines": http_get_json("/chancellor/engines"),
        },
    }

    out_path = OUT_DIR / f"audit_{int(time.time())}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": str(out_path),
                "as_of": ts,
                "hits": len(payload["repo_scan_hits"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
