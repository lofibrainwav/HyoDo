import hashlib
import json
import os
import subprocess
import time
from pathlib import Path


def run(cmd: str, out_dir: Path, name: str) -> None:
    t0 = time.time()
    p = subprocess.run(cmd, check=False, shell=True, text=True, capture_output=True)
    stdout_path = out_dir / f"{name}.stdout.txt"
    stderr_path = out_dir / f"{name}.stderr.txt"
    stdout_path.write_text(p.stdout, encoding="utf-8", errors="replace")
    stderr_path.write_text(p.stderr, encoding="utf-8", errors="replace")
    rec = {
        "ts": int(t0),
        "name": name,
        "cmd": cmd,
        "exit_code": p.returncode,
        "stdout_file": str(stdout_path),
        "stderr_file": str(stderr_path),
        "elapsed_sec": round(time.time() - t0, 3),
    }
    return rec


def sha256_file(path: Path) -> None:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stat_file(path: Path) -> None:
    st = path.stat()
    return {"path": str(path), "bytes": st.st_size, "sha256": sha256_file(path)}


def main() -> None:
    out_dir = Path("artifacts") / "ticket045_evidence" / str(int(time.time()))
    out_dir.mkdir(parents=True, exist_ok=True)

    base_url = os.environ.get("AFO_BASE_URL", "http://localhost:8010")
    rag_url = os.environ.get("AFO_RAG_URL", "http://localhost:8001")

    records = []
    records.append(run("git rev-parse HEAD", out_dir, "git_head"))
    records.append(run("git status -sb", out_dir, "git_status"))
    records.append(run("git diff --stat", out_dir, "git_diff_stat"))

    records.append(
        run(
            "docker ps --format 'table {{.Names}}\\t{{.Ports}}\\t{{.Status}}' || true",
            out_dir,
            "docker_ps",
        )
    )

    records.append(run(f"curl -sS {base_url}/health || true", out_dir, "curl_health_8010"))
    records.append(
        run(
            f"curl -sS {base_url}/api/5pillars/current || true",
            out_dir,
            "curl_5pillars_current",
        )
    )
    records.append(run(f"curl -sS {base_url}/api/ssot-status || true", out_dir, "curl_ssot_status"))
    records.append(run(f"curl -sS {rag_url}/health || true", out_dir, "curl_rag_health_8001"))

    file_checks = [
        "packages/afo-core/afo/rag/llamaindex_streaming_rag.py",
    ]
    file_stats = []
    for rel in file_checks:
        p = Path(rel)
        if p.exists():
            file_stats.append(stat_file(p))
        else:
            file_stats.append({"path": rel, "missing": True})

    (out_dir / "file_stats.json").write_text(json.dumps(file_stats, indent=2), encoding="utf-8")

    manifest = {
        "ticket": "TICKET-045",
        "created_ts": int(time.time()),
        "base_url": base_url,
        "rag_url": rag_url,
        "records": records,
        "file_stats": file_stats,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(str(out_dir))


if __name__ == "__main__":
    main()
