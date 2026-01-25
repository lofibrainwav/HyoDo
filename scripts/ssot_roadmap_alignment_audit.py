import hashlib
import json
import os
import time
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(".").resolve()
OUT_DIR = ROOT / "artifacts" / "ssot_roadmap_alignment"
OUT_DIR.mkdir(parents=True, exist_ok=True)

AFO_BASE_URL = os.environ.get("AFO_BASE_URL", "http://localhost:8010").rstrip("/")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def http_probe(path: str, timeout=5) -> None:
    url = f"{AFO_BASE_URL}{path}"
    req = Request(url, method="GET", headers={"Accept": "application/json"})
    t0 = perf_counter()
    try:
        with urlopen(req, timeout=timeout) as r:
            raw = r.read()
            ms = (perf_counter() - t0) * 1000.0
            txt = raw.decode("utf-8", errors="replace")
            try:
                snap = json.loads(txt)
            except json.JSONDecodeError:
                snap = txt[:2000]
            return {
                "ok": True,
                "url": url,
                "status": getattr(r, "status", None),
                "ms": ms,
                "snapshot": snap,
            }
    except HTTPError as e:
        ms = (perf_counter() - t0) * 1000.0
        try:
            body = e.read().decode("utf-8", errors="replace")[:2000]
        except Exception:
            body = ""
        return {
            "ok": False,
            "url": url,
            "status": getattr(e, "code", None),
            "ms": ms,
            "error": str(e),
            "snapshot": body,
        }
    except (URLError, TimeoutError) as e:
        ms = (perf_counter() - t0) * 1000.0
        return {"ok": False, "url": url, "status": None, "ms": ms, "error": str(e)}


def find_trinity_refs(limit=20) -> None:
    hits = []
    scan_dirs = ["docs", "packages", "scripts"]
    for d in scan_dirs:
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in [
                ".md",
                ".py",
                ".ts",
                ".tsx",
                ".json",
                ".yaml",
                ".yml",
            ]:
                continue
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if "Trinity Score" in txt or "5pillars" in txt or "pillars" in txt and "Trinity" in txt:
                hits.append(str(p.relative_to(ROOT)))
                if len(hits) >= limit:
                    return hits
    return hits


def main() -> None:
    ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    roadmap_path = ROOT / "docs" / "ANTIGRAVITY_ROADMAP_2026.md"

    payload = {
        "ticket": "ROADMAP_ALIGNMENT",
        "as_of": ts,
        "afo_base_url": AFO_BASE_URL,
        "roadmap": {
            "path": str(roadmap_path.relative_to(ROOT)),
            "exists": roadmap_path.exists(),
            "bytes": roadmap_path.stat().st_size if roadmap_path.exists() else None,
            "sha256": sha256_file(roadmap_path) if roadmap_path.exists() else None,
        },
        "endpoints": {
            "/health": http_probe("/health", timeout=5),
            "/api/health": http_probe("/api/health", timeout=5),
            "/api/5pillars": http_probe("/api/5pillars", timeout=5),
            "/chancellor/engines": http_probe("/chancellor/engines", timeout=5),
        },
        "trinity_refs_candidates": find_trinity_refs(limit=20),
    }

    out_path = OUT_DIR / f"roadmap_alignment_audit_{int(time.time())}.jsonl"
    out_path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")

    summary = {
        "wrote": str(out_path),
        "roadmap_exists": payload["roadmap"]["exists"],
        "roadmap_sha256": payload["roadmap"]["sha256"],
        "health_status": payload["endpoints"]["/health"].get("status"),
        "api_health_status": payload["endpoints"]["/api/health"].get("status"),
        "pillars_status": payload["endpoints"]["/api/5pillars"].get("status"),
        "engines_status": payload["endpoints"]["/chancellor/engines"].get("status"),
        "trinity_refs_hits": len(payload["trinity_refs_candidates"]),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
