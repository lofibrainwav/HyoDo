"""Check or synchronize canonical release notes with a GitHub Release body.

The repository document under ``docs/releases/<version>.md`` is the source of
truth. The default mode is read-only and reports drift. ``--apply`` performs an
explicit ``gh release edit`` and then reads the release back before returning
success.

Exit contract:

- 0: observed and in sync
- 1: observed drift or failed post-write verification
- 2: UNOBSERVED (required local/remote evidence could not be read)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def canonical_notes(root: Path, version: str) -> Path:
    return root / "docs" / "releases" / f"{version}.md"


def _run(*args: str, timeout: int = 30) -> subprocess.CompletedProcess[str] | None:
    if shutil.which(args[0]) is None:
        return None
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _normalized(value: str) -> str:
    return value.replace("\r\n", "\n").rstrip() + "\n"


def read_remote_body(*, repo: str, tag: str) -> str | None:
    done = _run("gh", "release", "view", tag, "--repo", repo, "--json", "body")
    if done is None or done.returncode != 0:
        return None
    try:
        payload = json.loads(done.stdout)
    except json.JSONDecodeError:
        return None
    body = payload.get("body")
    return body if isinstance(body, str) else None


def notes_in_sync(*, repo: str, tag: str, notes: str) -> bool | None:
    remote = read_remote_body(repo=repo, tag=tag)
    if remote is None:
        return None
    return _normalized(remote) == _normalized(notes)


def apply_notes(*, repo: str, tag: str, path: Path) -> bool | None:
    done = _run(
        "gh",
        "release",
        "edit",
        tag,
        "--repo",
        repo,
        "--notes-file",
        str(path),
    )
    if done is None:
        return None
    return done.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    parser.add_argument("--repo", default="lofibrainwav/HyoDo")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    path = canonical_notes(args.root, args.version)
    try:
        notes = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        print(f"UNOBSERVED: canonical release notes unreadable: {path}")
        return 2

    tag = f"v{args.version}"
    observed = notes_in_sync(repo=args.repo, tag=tag, notes=notes)
    if observed is None:
        print(f"UNOBSERVED: GitHub Release body could not be read: {tag}")
        return 2
    if observed:
        print(f"OBSERVED: {tag} release body matches {path}")
        return 0
    if not args.apply:
        print(f"DRIFT: {tag} release body differs from {path}")
        return 1

    applied = apply_notes(repo=args.repo, tag=tag, path=path)
    if applied is None:
        print(f"UNOBSERVED: GitHub Release edit could not be attempted: {tag}")
        return 2
    if not applied:
        print(f"DRIFT: GitHub Release edit failed: {tag}")
        return 1

    verified = notes_in_sync(repo=args.repo, tag=tag, notes=notes)
    if verified is None:
        print(f"UNOBSERVED: post-write GitHub Release readback unavailable: {tag}")
        return 2
    if not verified:
        print(f"DRIFT: post-write GitHub Release body still differs: {tag}")
        return 1
    print(f"OBSERVED: synchronized and verified {tag} from {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
