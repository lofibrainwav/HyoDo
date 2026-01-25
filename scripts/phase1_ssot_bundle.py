import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(".").resolve()
OUT_DIR = ROOT / "artifacts" / "ssot_phase1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

AFO_BASE_URL = os.environ.get("AFO_BASE_URL", "http://localhost:8010").rstrip("/")
RAG_BASE_URL = os.environ.get("AFO_RAG_URL", "http://localhost:8001").rstrip("/")


def run(cmd) -> None:
    p = subprocess.run(cmd, check=False, cwd=str(ROOT), text=True, capture_output=True)
    return {
        "cmd": cmd,
        "rc": p.returncode,
        "out": p.stdout.strip(),
        "err": p.stderr.strip(),
    }


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str | None:
    if not p.exists() or not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def http_probe(url: str, timeout=6) -> None:
    req = Request(url, method="GET", headers={"Accept": "application/json"})
    t0 = perf_counter()
    try:
        with urlopen(req, timeout=timeout) as r:
            body = r.read()
            ms = (perf_counter() - t0) * 1000.0
            return {
                "ok": True,
                "url": url,
                "status": getattr(r, "status", None),
                "ms": ms,
                "sha256": sha256_bytes(body),
                "snapshot": body.decode("utf-8", errors="replace")[:2000],
            }
    except HTTPError as e:
        ms = (perf_counter() - t0) * 1000.0
        try:
            body = e.read()
        except Exception:
            body = b""
        return {
            "ok": False,
            "url": url,
            "status": getattr(e, "code", None),
            "ms": ms,
            "sha256": sha256_bytes(body),
            "snapshot": body.decode("utf-8", errors="replace")[:2000],
            "error": str(e),
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
            if (
                "Trinity Score" in txt
                or "5pillars" in txt
                or ("pillars" in txt and "Trinity" in txt)
            ):
                hits.append(str(p.relative_to(ROOT)))
                if len(hits) >= limit:
                    return hits
    return hits


def main() -> None:
    ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    roadmap_path = ROOT / "docs" / "ANTIGRAVITY_ROADMAP_2026.md"
    ch_spec = ROOT / "docs" / "AFO_CHANCELLOR_GRAPH_SPEC.md"

    organs_truth_hits = sorted([str(p.relative_to(ROOT)) for p in ROOT.rglob("organs_truth.py")])[
        :5
    ]
    t11_logs = sorted(
        [
            str(p.relative_to(ROOT))
            for p in ROOT.glob("artifacts/t11_ollama_integration_ssot_*.jsonl")
        ]
    )

    bundle = {
        "ticket": "ANTIGRAVITY_PHASE1",
        "as_of": ts,
        "env": {
            "AFO_BASE_URL": AFO_BASE_URL,
            "AFO_RAG_URL": RAG_BASE_URL,
            "git_sha": run(["git", "rev-parse", "HEAD"])["out"],
            "python": run(["python", "-V"])["out"],
        },
        "files": {
            "docs/ANTIGRAVITY_ROADMAP_2026.md": {
                "exists": roadmap_path.exists(),
                "sha256": sha256_file(roadmap_path),
                "bytes": roadmap_path.stat().st_size if roadmap_path.exists() else None,
            },
            "docs/AFO_CHANCELLOR_GRAPH_SPEC.md": {
                "exists": ch_spec.exists(),
                "sha256": sha256_file(ch_spec),
                "bytes": ch_spec.stat().st_size if ch_spec.exists() else None,
            },
            "organs_truth_candidates": [
                {"path": p, "sha256": sha256_file(ROOT / p)} for p in organs_truth_hits
            ],
            "t11_ssot_logs": [{"path": p, "sha256": sha256_file(ROOT / p)} for p in t11_logs],
        },
        "endpoints": {
            "afo_health": http_probe(f"{AFO_BASE_URL}/health"),
            "afo_api_health": http_probe(f"{AFO_BASE_URL}/api/health"),
            "afo_api_5pillars": http_probe(f"{AFO_BASE_URL}/api/5pillars"),
            "afo_chancellor_engines": http_probe(f"{AFO_BASE_URL}/chancellor/engines"),
            "rag_health": http_probe(f"{RAG_BASE_URL}/health"),
        },
        "commands": {
            "system_health_check_py": run(["python", "system_health_check.py"]),
        },
    }

    out_path = OUT_DIR / f"phase1_bundle_{int(time.time())}.jsonl"
    out_path.write_text(json.dumps(bundle, ensure_ascii=False) + "\n", encoding="utf-8")

    out_sha = sha256_file(out_path)

    summary = {
        "wrote": str(out_path.relative_to(ROOT)),
        "sha256": out_sha,
        "git_sha": bundle["env"]["git_sha"],
        "python": bundle["env"]["python"],
        "roadmap_exists": bundle["files"]["docs/ANTIGRAVITY_ROADMAP_2026.md"]["exists"],
        "roadmap_sha256": bundle["files"]["docs/ANTIGRAVITY_ROADMAP_2026.md"]["sha256"],
        "health_status": bundle["endpoints"]["afo_health"].get("status"),
        "rag_health_status": bundle["endpoints"]["rag_health"].get("status"),
        "t11_logs_count": len(bundle["files"]["t11_ssot_logs"]),
        "organs_truth_hits": len(bundle["files"]["organs_truth_candidates"]),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
