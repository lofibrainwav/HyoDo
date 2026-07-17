#!/usr/bin/env python3
"""Verify a published HyoDo version on public PyPI.

Success criteria (supply-chain seal):
  - version exists and is not yanked
  - wheel + sdist present
  - optional: both files have non-null provenance (Trusted Publishing attestations)
  - optional: cold pip install + hyodo --version smoke

Exit 0 on success, 1 on failure.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


def fetch_json(url: str, timeout: int = 30) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "hyodo-verify-pypi-release/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def version_payload(version: str) -> Dict[str, Any]:
    return fetch_json(f"https://pypi.org/pypi/hyodo/{version}/json")


def provenance_for_file(meta: Dict[str, Any], filename: str) -> Optional[Any]:
    """Best-effort provenance extraction across PyPI JSON shapes."""
    # Top-level (some Warehouse responses)
    top = meta.get("provenance")
    if top is not None:
        return top
    for url in meta.get("urls") or []:
        if url.get("filename") != filename:
            continue
        if "provenance" in url and url["provenance"] is not None:
            return url["provenance"]
        # Some responses embed attestation URLs under digests/extensions
        for key in ("provenance", "attestations", "has_provenance"):
            if url.get(key) not in (None, False, ""):
                return url.get(key)
    # Integrity API (PEP 740 / Warehouse integrity)
    try:
        integrity = fetch_json(f"https://pypi.org/integrity/hyodo/{meta['info']['version']}/{filename}/provenance")
        return integrity
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    except Exception:
        return None


def wait_for_version(version: str, retries: int, sleep_seconds: float) -> Dict[str, Any]:
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            data = version_payload(version)
            if data.get("info", {}).get("version") == version:
                return data
        except Exception as exc:  # noqa: BLE001 - retry loop
            last_err = exc
        print(f"poll {attempt}/{retries}: version {version} not ready yet ({last_err})")
        time.sleep(sleep_seconds)
    raise SystemExit(f"PyPI version {version} not available after {retries} polls: {last_err}")


def require_files(meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    urls = meta.get("urls") or []
    kinds = {u.get("packagetype") for u in urls}
    if "bdist_wheel" not in kinds or "sdist" not in kinds:
        raise SystemExit(f"expected wheel+sdist, got packagetypes={sorted(kinds)}")
    if meta.get("info", {}).get("yanked"):
        raise SystemExit("version is yanked")
    for u in urls:
        if u.get("yanked"):
            raise SystemExit(f"file yanked: {u.get('filename')}")
    return urls


def check_provenance(meta: Dict[str, Any], urls: List[Dict[str, Any]]) -> None:
    missing: List[str] = []
    for u in urls:
        name = u["filename"]
        prov = provenance_for_file(meta, name)
        if prov in (None, {}, [], False):
            missing.append(name)
            print(f"PROVENANCE missing: {name}")
        else:
            print(f"PROVENANCE present: {name}")
    if missing:
        raise SystemExit(
            "provenance null/missing for: "
            + ", ".join(missing)
            + " (configure PyPI Trusted Publishing + re-publish)"
        )


def install_smoke(version: str) -> None:
    with tempfile.TemporaryDirectory(prefix="hyodo-pypi-smoke-") as tmp:
        venv = Path(tmp) / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        pip = venv / "bin" / "pip"
        hyodo = venv / "bin" / "hyodo"
        python = venv / "bin" / "python"
        subprocess.run([str(pip), "install", "-U", "pip"], check=True, capture_output=True)
        subprocess.run(
            [str(pip), "install", "--no-cache-dir", f"hyodo=={version}"],
            check=True,
        )
        out = subprocess.check_output([str(hyodo), "--version"], text=True)
        if version not in out:
            raise SystemExit(f"hyodo --version mismatch: {out!r}")
        code = subprocess.check_output(
            [str(python), "-c", "import hyodo; print(hyodo.__version__)"],
            text=True,
        ).strip()
        if code != version:
            raise SystemExit(f"import version mismatch: {code!r}")
        print(f"install smoke ok: {out.strip()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Expected PyPI version, e.g. 3.1.8")
    parser.add_argument("--require-provenance", action="store_true")
    parser.add_argument("--install-smoke", action="store_true")
    parser.add_argument("--retries", type=int, default=18)
    parser.add_argument("--sleep-seconds", type=float, default=10.0)
    args = parser.parse_args()

    meta = wait_for_version(args.version, args.retries, args.sleep_seconds)
    urls = require_files(meta)
    print(f"version {args.version} live; files={len(urls)}")
    for u in urls:
        print(
            f"  {u.get('packagetype')}: {u.get('filename')} "
            f"size={u.get('size')} sha256={u.get('digests', {}).get('sha256', '')[:16]}..."
        )

    if args.require_provenance:
        check_provenance(meta, urls)

    if args.install_smoke:
        install_smoke(args.version)

    print("PASS: PyPI release verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
