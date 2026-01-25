#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def log_event(job_name, status, message="") -> None:
    log_dir = Path("artifacts/evolution")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "ci_history.jsonl"

    event = {
        "timestamp": datetime.now(datetime.UTC).isoformat(),
        "job": job_name,
        "status": status,
        "repo": os.getenv("GITHUB_REPOSITORY", "unknown"),
        "run_id": os.getenv("GITHUB_RUN_ID", "local"),
        "actor": os.getenv("GITHUB_ACTOR", "unknown"),
        "ref": os.getenv("GITHUB_REF", "unknown"),
        "message": message,
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    print(f"📖 [Historian] Logged {status} for {job_name}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: ci_historian.py <job_name> <status> [message]")
        sys.exit(1)

    log_event(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
