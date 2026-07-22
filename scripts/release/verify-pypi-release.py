#!/usr/bin/env python3
"""Verify a published HyoDo version on public PyPI.

Success criteria (supply-chain seal):
  - version exists and is not yanked
  - wheel + sdist present
  - optional: both files have non-null provenance (Trusted Publishing attestations)
  - optional: cold pip install + hyodo --version smoke

Provenance and simple-index lag are common right after publish. This script
polls the version JSON first, then **separately retries** provenance (JSON
fields + PEP 740 integrity API) and install smoke (index → wheel-url fallback).

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
from typing import Any

USER_AGENT = "hyodo-verify-pypi-release/1.1"


def fetch_json(url: str, timeout: int = 30) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def version_payload(version: str) -> dict[str, Any]:
    return fetch_json(f"https://pypi.org/pypi/hyodo/{version}/json")


def integrity_provenance_url(version: str, filename: str) -> str:
    return f"https://pypi.org/integrity/hyodo/{version}/{filename}/provenance"


def fetch_integrity_provenance(version: str, filename: str) -> tuple[Any | None, str | None]:
    """Return (payload_or_None, error_kind).

    error_kind:
      - None when payload is present
      - ``\"http_404\"`` when integrity API says not ready / missing
      - ``\"http_N\"`` for other HTTP errors
      - ``\"network\"`` for transport/parse failures
    """
    url = integrity_provenance_url(version, filename)
    try:
        payload = fetch_json(url)
        if payload in (None, {}, [], False):
            return None, "empty"
        return payload, None
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, "http_404"
        return None, f"http_{exc.code}"
    except Exception:
        return None, "network"


def provenance_from_version_json(meta: dict[str, Any], filename: str) -> Any | None:
    """Extract provenance from the version JSON only (no integrity HTTP call)."""
    top = meta.get("provenance")
    if top not in (None, {}, [], False):
        return top
    for url in meta.get("urls") or []:
        if url.get("filename") != filename:
            continue
        if url.get("provenance") not in (None, {}, [], False):
            return url.get("provenance")
        for key in ("attestations", "has_provenance"):
            if url.get(key) not in (None, False, ""):
                return url.get(key)
    return None


def provenance_for_file(meta: dict[str, Any], filename: str) -> Any | None:
    """Best-effort provenance: version JSON first, then PEP 740 integrity API."""
    from_json = provenance_from_version_json(meta, filename)
    if from_json is not None:
        return from_json
    version = str(meta.get("info", {}).get("version") or "")
    if not version:
        return None
    payload, _kind = fetch_integrity_provenance(version, filename)
    return payload


def wait_for_version(version: str, retries: int, sleep_seconds: float) -> dict[str, Any]:
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            data = version_payload(version)
            if data.get("info", {}).get("version") == version:
                if attempt > 1:
                    print(f"version {version} ready on poll {attempt}/{retries}")
                return data
            last_err = RuntimeError("version field mismatch")
        except Exception as exc:
            last_err = exc
        print(f"poll version {attempt}/{retries}: not ready yet ({last_err})")
        if attempt < retries:
            time.sleep(sleep_seconds)
    raise SystemExit(f"PyPI version {version} not available after {retries} polls: {last_err}")


def require_files(meta: dict[str, Any]) -> list[dict[str, Any]]:
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


def _artifact_filenames(urls: list[dict[str, Any]]) -> list[str]:
    names = [u["filename"] for u in urls if u.get("filename")]
    # Prefer wheel + sdist only (ignore any extra legacy files).
    preferred = [
        n for n in names if n.endswith(".whl") or n.endswith(".tar.gz") or n.endswith(".zip")
    ]
    return preferred or names


def wait_for_provenance(
    version: str,
    filenames: list[str],
    retries: int,
    sleep_seconds: float,
) -> None:
    """Poll until every artifact has provenance, or fail with a clear reason.

    PyPI Trusted Publishing often attaches integrity attestations *after* the
    version JSON is already queryable. A single-shot check right after
    ``wait_for_version`` produces false reds (observed on 4.0.1).
    """
    last_missing: list[str] = []
    last_kinds: dict[str, str] = {}

    for attempt in range(1, retries + 1):
        missing: list[str] = []
        kinds: dict[str, str] = {}
        meta: dict[str, Any] | None = None
        try:
            meta = version_payload(version)
        except Exception as exc:
            print(f"poll provenance {attempt}/{retries}: version JSON refresh failed ({exc})")
            if attempt < retries:
                time.sleep(sleep_seconds)
            last_missing = list(filenames)
            continue

        for name in filenames:
            from_json = provenance_from_version_json(meta, name)
            if from_json not in (None, {}, [], False):
                print(f"PROVENANCE present (version-json): {name}")
                continue
            payload, kind = fetch_integrity_provenance(version, name)
            if payload not in (None, {}, [], False):
                print(f"PROVENANCE present (integrity-api): {name}")
                continue
            missing.append(name)
            kinds[name] = kind or "unknown"
            print(f"PROVENANCE missing: {name} ({kinds[name]})")

        if not missing:
            if attempt > 1:
                print(f"PROVENANCE ready for all files on poll {attempt}/{retries}")
            return

        last_missing = missing
        last_kinds = kinds
        print(
            f"poll provenance {attempt}/{retries}: still missing "
            f"{', '.join(missing)} — CDN/attestation lag is common right after publish"
        )
        if attempt < retries:
            time.sleep(sleep_seconds)

    # Fail with a message that distinguishes lag from misconfiguration.
    only_404 = last_missing and all(
        last_kinds.get(n) in {"http_404", "empty"} for n in last_missing
    )
    if only_404:
        raise SystemExit(
            "provenance still missing after "
            f"{retries} polls for: {', '.join(last_missing)} "
            "(integrity API returned 404/empty — either Trusted Publishing is not "
            "configured, or attestation CDN lag exceeded the retry budget; "
            "re-run this job once attestations are live)"
        )
    raise SystemExit(
        "provenance null/missing for: "
        + ", ".join(f"{n}({last_kinds.get(n, '?')})" for n in last_missing)
        + " after "
        + str(retries)
        + " polls"
    )


def check_provenance(meta: dict[str, Any], urls: list[dict[str, Any]]) -> None:
    """One-shot provenance check (kept for unit tests / local dry use)."""
    version = str(meta.get("info", {}).get("version") or "")
    missing: list[str] = []
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
            + (
                " (configure PyPI Trusted Publishing + re-publish)"
                if not version
                else " (re-run after attestation lag, or configure Trusted Publishing)"
            )
        )


def install_smoke(version: str, retries: int = 12, sleep_seconds: float = 10.0) -> None:
    """Cold install smoke.

    Prefer ``pip install hyodo==VERSION`` from the public index. If the simple
    index lags the version JSON API (common right after publish), fall back to
    the wheel URL from the version JSON (still files.pythonhosted.org).
    Refresh the wheel URL each attempt so a late-published wheel is picked up.
    """
    last_err: BaseException | None = None
    with tempfile.TemporaryDirectory(prefix="hyodo-pypi-smoke-") as tmp:
        venv = Path(tmp) / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        pip = venv / "bin" / "pip"
        hyodo = venv / "bin" / "hyodo"
        python = venv / "bin" / "python"
        subprocess.run([str(pip), "install", "-U", "pip"], check=True, capture_output=True)

        for attempt in range(1, retries + 1):
            wheel_url: str | None = None
            try:
                meta = version_payload(version)
                wheel = next(
                    (u for u in meta.get("urls") or [] if u.get("packagetype") == "bdist_wheel"),
                    None,
                )
                if wheel and wheel.get("url"):
                    wheel_url = str(wheel["url"])
            except Exception as exc:
                print(f"install attempt {attempt}/{retries}: version JSON refresh failed ({exc})")

            targets: list[tuple[str, str]] = [(f"hyodo=={version}", "index")]
            if wheel_url:
                targets.append((wheel_url, "wheel-url"))

            for target, label in targets:
                try:
                    subprocess.run(
                        [str(pip), "install", "--no-cache-dir", target],
                        check=True,
                        capture_output=True,
                        text=True,
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
                    print(f"install smoke ok ({label}, attempt {attempt}): {out.strip()}")
                    return
                except subprocess.CalledProcessError as exc:
                    last_err = exc
                    err = (exc.stderr or exc.stdout or str(exc))[-300:]
                    print(f"install attempt {attempt}/{retries} via {label} failed: {err}")
                except SystemExit as exc:
                    last_err = exc
                    print(f"install attempt {attempt}/{retries} via {label} failed: {exc}")
            if attempt < retries:
                time.sleep(sleep_seconds)
    raise SystemExit(f"install smoke failed after {retries} attempts: {last_err}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Expected PyPI version, e.g. 4.0.1")
    parser.add_argument("--require-provenance", action="store_true")
    parser.add_argument("--install-smoke", action="store_true")
    parser.add_argument(
        "--retries",
        type=int,
        default=18,
        help="Max polls for version readiness, provenance lag, and install smoke",
    )
    parser.add_argument("--sleep-seconds", type=float, default=10.0)
    parser.add_argument(
        "--provenance-retries",
        type=int,
        default=None,
        help="Override provenance-only poll budget (default: same as --retries)",
    )
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
        prov_retries = (
            args.provenance_retries if args.provenance_retries is not None else args.retries
        )
        wait_for_provenance(
            args.version,
            _artifact_filenames(urls),
            retries=prov_retries,
            sleep_seconds=args.sleep_seconds,
        )

    if args.install_smoke:
        install_smoke(args.version, retries=args.retries, sleep_seconds=args.sleep_seconds)

    print("PASS: PyPI release verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
