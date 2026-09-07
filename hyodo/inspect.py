"""Field-deployment absorption: `hyodo inspect`.

Pure logic for walking a directory into two manifests:

- ``.hyodo/folder-manifest.json`` (``hyodo.folder-manifest/v1``): one entry
  per file observed, a digest, and an honest ``coverage`` pair.
- ``.hyodo/chunks-manifest.json`` (``hyodo.chunks-manifest/v1``): fixed-size
  byte-range chunks over every non-excluded, readable file. Chunks never
  carry file text or a body key — only ids, digests, and byte ranges.

No network call is made anywhere in this module. No policy decision is made
here either: ``inspect`` never calls ``evaluate_policy`` (see the Stage 2
design doc, Package 2-B) because absorbing a directory the operator already
pointed HyoDo at is not itself an external variable.
"""

from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hyodo.events import content_digest
from hyodo.safety import _SKIPPED_DIR_NAMES, scan_text

FOLDER_MANIFEST_SCHEMA = "hyodo.folder-manifest/v1"
CHUNKS_MANIFEST_SCHEMA = "hyodo.chunks-manifest/v1"
REMOTE_INVENTORY_SCHEMA = "hyodo.remote-inventory/v1"

CHUNK_SIZE = 4096
_SCAN_TEXT_CAP = 200_000


class RemoteInventoryError(ValueError):
    """Raised when a `--remote-inventory` file is missing, malformed, or the wrong schema."""


@dataclass
class InspectResult:
    """The full outcome of one `hyodo inspect` run, pre-rendering.

    ``folder_manifest`` and ``chunks_manifest`` are the exact JSON-serializable
    documents written to disk. ``warnings`` carries human-readable lines
    (currently only digest-mismatch-during-inspect notices) printed once by
    the CLI regardless of ``--report`` format.
    """

    folder_manifest: dict[str, Any]
    chunks_manifest: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


def _is_ignored(rel_posix: str, name: str, patterns: list[str]) -> str | None:
    """Return the matching glob (as an `ignore_reason` suffix) or None.

    Tested against both the path relative to root and the bare basename, so
    an operator can write either `--ignore "*.log"` or `--ignore "build/*"`.
    """
    for pattern in patterns:
        if fnmatch.fnmatch(rel_posix, pattern) or fnmatch.fnmatch(name, pattern):
            return pattern
    return None


def _walk_files(root: Path) -> list[Path]:
    """List regular files and readable-once symlinks under *root*, skipping build caches.

    `_SKIPPED_DIR_NAMES` directories (and anything under `.git*`) are never
    walked at all, matching `hyodo/safety.py`'s corpus rule. Directory
    symlinks are surfaced by the caller as `unreadable`/`symlink_dir_skipped`
    rather than recursed into (no directory symlink recursion).
    """
    results: list[Path] = []

    def _walk(dir_path: Path) -> None:
        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: p.name)
        except OSError:
            return
        for entry in entries:
            if entry.name.startswith(".git"):
                continue
            if entry.is_dir() and not entry.is_symlink():
                if entry.name in _SKIPPED_DIR_NAMES:
                    continue
                _walk(entry)
            else:
                results.append(entry)

    _walk(root)
    return results


def _resolve_symlink_status(entry: Path, root: Path) -> tuple[str | None, Path | None]:
    """Return (`unreadable` reason, resolved target) for one directory entry.

    A symlink to a directory is never recursed into (`symlink_dir_skipped`,
    no resolved target). A symlink whose resolved target lies outside the
    resolved root is never followed (`symlink_outside_root`, no resolved
    target). A symlink inside root pointing at a regular file is followed
    once: reason is None and the resolved target path is returned so the
    caller can record it as `symlink_target` — never the target's own path
    silently standing in for the symlink's.
    """
    if not entry.is_symlink():
        return None, None
    try:
        resolved = entry.resolve(strict=True)
    except OSError:
        return "symlink_outside_root", None
    resolved_root = root.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return "symlink_outside_root", None
    if resolved.is_dir():
        return "symlink_dir_skipped", None
    return None, resolved


def _lexical_display_path(entry: Path, root_abs: Path) -> str:
    """Return *entry*'s own path relative to *root_abs*, POSIX, never resolving symlinks.

    `root_abs` must already be an absolute (but not necessarily resolved)
    path. Using `Path.absolute()` here (not `.resolve()`) is deliberate: a
    symlink must be reported under its own lexical location, never under
    whatever it happens to point at.
    """
    try:
        return entry.absolute().relative_to(root_abs).as_posix()
    except ValueError:
        return entry.as_posix()


def load_remote_inventory(path: str) -> dict[str, Any]:
    """Load and validate one `hyodo.remote-inventory/v1` document.

    Raises :class:`RemoteInventoryError` on any missing file, invalid JSON,
    wrong/missing schema, or malformed `items` shape. HyoDo never fetches the
    referenced content; this only records the operator-supplied claim.
    """
    file_path = Path(path)
    try:
        raw = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RemoteInventoryError(f"cannot read remote inventory file: {path} ({exc})") from exc
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RemoteInventoryError(f"remote inventory is not valid JSON: {path} ({exc})") from exc
    if not isinstance(doc, dict):
        raise RemoteInventoryError(f"remote inventory must be a JSON object: {path}")
    if doc.get("schema") != REMOTE_INVENTORY_SCHEMA:
        raise RemoteInventoryError(
            f"remote inventory has wrong/missing schema (expected {REMOTE_INVENTORY_SCHEMA}): {path}"
        )
    source = doc.get("source")
    if not isinstance(source, str) or not source:
        raise RemoteInventoryError(f"remote inventory missing non-empty 'source': {path}")
    items = doc.get("items")
    if not isinstance(items, list):
        raise RemoteInventoryError(f"remote inventory 'items' must be a list: {path}")
    for item in items:
        if not isinstance(item, dict):
            raise RemoteInventoryError(f"remote inventory item is not an object: {path}")
        if not isinstance(item.get("id"), str) or not item.get("id"):
            raise RemoteInventoryError(f"remote inventory item missing non-empty 'id': {path}")
        if not isinstance(item.get("name"), str) or not item.get("name"):
            raise RemoteInventoryError(f"remote inventory item missing non-empty 'name': {path}")
        for optional_key in ("mime_type", "modified_at", "declared_digest", "revision"):
            if (
                optional_key in item
                and item[optional_key] is not None
                and not isinstance(item[optional_key], str)
            ):
                raise RemoteInventoryError(
                    f"remote inventory item '{optional_key}' must be a string or null: {path}"
                )
        if (
            "shared_outside" in item
            and item["shared_outside"] is not None
            and not isinstance(item["shared_outside"], bool)
        ):
            raise RemoteInventoryError(
                f"remote inventory item 'shared_outside' must be a bool or null: {path}"
            )
    return doc


def _summarize_remote_inventory(doc: dict[str, Any]) -> dict[str, Any]:
    """Fold one validated remote-inventory document into a folder-manifest `remote[]` row."""
    items = doc["items"]
    return {
        "source": doc["source"],
        "items_listed": len(items),
        "items_with_declared_digest": sum(1 for it in items if it.get("declared_digest")),
        "items_shared_outside": sum(1 for it in items if it.get("shared_outside") is True),
        "items": items,
    }


def run_inspect(
    path: str,
    *,
    root: str | Path | None = None,
    ignore: list[str] | None = None,
    remote_inventory_paths: list[str] | None = None,
) -> InspectResult:
    """Absorb *path* into folder-manifest and chunks-manifest documents.

    *root* (default: current working directory) is the base that `path`
    entries are reported relative to; it need not equal `path`. Raises
    :class:`NotADirectoryError` when `path` does not exist or is not a
    directory (caller maps this to exit 1), and :class:`RemoteInventoryError`
    when any `--remote-inventory` file fails validation (caller maps this to
    exit 1, before any manifest is written).
    """
    target = Path(path)
    if not target.is_dir():
        raise NotADirectoryError(f"not a directory: {path}")

    base_root = Path(root) if root is not None else Path.cwd()
    root_abs = base_root.absolute()

    remote_rows: list[dict[str, Any]] = []
    for inv_path in remote_inventory_paths or []:
        doc = load_remote_inventory(inv_path)
        remote_rows.append(_summarize_remote_inventory(doc))

    ignore_patterns = list(ignore or [])
    entries = _walk_files(target)

    files: list[dict[str, Any]] = []
    unreadable: list[dict[str, Any]] = []
    # Pass-1 digest, keyed by absolute path, for files eligible for chunking.
    pass1_digest: dict[Path, str] = {}
    chunkable: list[Path] = []
    expected = 0

    for entry in entries:
        # Report path relative to --root, POSIX separators — the entry's own
        # lexical location, never a symlink's resolved target.
        display_path = _lexical_display_path(entry, root_abs)
        name = entry.name
        ignore_match = _is_ignored(display_path, name, ignore_patterns)

        symlink_reason, symlink_resolved = _resolve_symlink_status(entry, target)
        if symlink_reason is not None:
            # Ignored files are entirely out of coverage scope (rule: ignore
            # excludes from chunks *and* from coverage's expected count), so an
            # ignored, unreadable symlink is neither counted nor reported.
            if not ignore_match:
                expected += 1
                unreadable.append({"path": display_path, "reason": symlink_reason})
            continue

        symlink_target_display: str | None = None
        if entry.is_symlink() and symlink_resolved is not None:
            try:
                symlink_target_display = symlink_resolved.relative_to(root_abs.resolve()).as_posix()
            except ValueError:
                symlink_target_display = symlink_resolved.as_posix()

        try:
            data = entry.read_bytes()
            stat = entry.stat()
        except OSError as exc:
            if ignore_match:
                continue
            expected += 1
            unreadable.append(
                {"path": display_path, "reason": f"read_error:{exc.__class__.__name__}"}
            )
            continue

        digest = content_digest(data)
        assert digest is not None  # content_digest(bytes) never returns None
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

        if ignore_match:
            # Still listed (rule 3), but out of coverage/chunk scope entirely.
            files.append(
                {
                    "path": display_path,
                    "digest": digest,
                    "size": stat.st_size,
                    "mtime": mtime,
                    "ignored": True,
                    "ignore_reason": f"pattern:{ignore_match}",
                    "secret_shaped": False,
                    "symlink_target": symlink_target_display,
                }
            )
            continue

        expected += 1
        text = data[:_SCAN_TEXT_CAP].decode("utf-8", errors="replace")
        findings = scan_text(text, path=display_path)
        secret_shaped = any(f.category == "secret" for f in findings)

        files.append(
            {
                "path": display_path,
                "digest": digest,
                "size": stat.st_size,
                "mtime": mtime,
                "ignored": False,
                "ignore_reason": None,
                "secret_shaped": secret_shaped,
                "symlink_target": symlink_target_display,
            }
        )

        if not secret_shaped:
            pass1_digest[entry] = digest
            chunkable.append(entry)

    observed = expected - len(unreadable)

    # Pass 2: chunk. Re-read bytes; a whole-file digest mismatch vs pass 1 is
    # reported (changed_during_inspect) but never blocks the run.
    changed_during_inspect: list[dict[str, str]] = []
    warnings: list[str] = []
    chunks: list[dict[str, Any]] = []
    chunk_seq = 1

    for entry in sorted(chunkable, key=lambda p: p.relative_to(target).as_posix()):
        try:
            data = entry.read_bytes()
        except OSError:
            # Became unreadable between passes; leave it out of chunks silently
            # rather than crash — folder-manifest already recorded pass-1 state.
            continue
        digest_before = pass1_digest[entry]
        digest_after = content_digest(data)
        if digest_after != digest_before:
            display_path = _lexical_display_path(entry, root_abs)
            changed_during_inspect.append(
                {
                    "path": display_path,
                    "digest_before": digest_before or "",
                    "digest_after": digest_after or "",
                }
            )
            warnings.append(
                f"warning: {display_path} changed during inspect "
                f"({digest_before} -> {digest_after}); chunks reflect the newer content"
            )

        size = len(data)
        offset = 0
        if size == 0:
            chunk_id = f"c-{chunk_seq:04d}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "file_digest": digest_after,
                    "byte_range": [0, 0],
                    "chunk_digest": content_digest(b""),
                }
            )
            chunk_seq += 1
            continue
        while offset < size:
            end = min(offset + CHUNK_SIZE, size)
            chunk_id = f"c-{chunk_seq:04d}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "file_digest": digest_after,
                    "byte_range": [offset, end],
                    "chunk_digest": content_digest(data[offset:end]),
                }
            )
            chunk_seq += 1
            offset = end

    try:
        root_display = Path(path).resolve().relative_to(base_root.resolve()).as_posix()
    except ValueError:
        root_display = Path(path).as_posix()

    folder_manifest: dict[str, Any] = {
        "schema": FOLDER_MANIFEST_SCHEMA,
        "root": root_display,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
        "unreadable": unreadable,
        "coverage": [observed, expected],
    }
    if changed_during_inspect:
        folder_manifest["changed_during_inspect"] = changed_during_inspect
    if remote_rows:
        folder_manifest["remote"] = remote_rows

    chunks_manifest: dict[str, Any] = {
        "schema": CHUNKS_MANIFEST_SCHEMA,
        "chunks": chunks,
    }

    return InspectResult(
        folder_manifest=folder_manifest, chunks_manifest=chunks_manifest, warnings=warnings
    )


def write_manifests(result: InspectResult, root: str | Path) -> tuple[Path, Path]:
    """Write both manifests under `<root>/.hyodo/`. Raises OSError on any write failure."""
    hyodo_dir = Path(root) / ".hyodo"
    hyodo_dir.mkdir(parents=True, exist_ok=True)
    folder_path = hyodo_dir / "folder-manifest.json"
    chunks_path = hyodo_dir / "chunks-manifest.json"
    folder_path.write_text(json.dumps(result.folder_manifest, indent=2) + "\n", encoding="utf-8")
    chunks_path.write_text(json.dumps(result.chunks_manifest, indent=2) + "\n", encoding="utf-8")
    return folder_path, chunks_path


def render_report_md(result: InspectResult) -> str:
    """Render the human Markdown report: coverage line, counts, top-level lists."""
    manifest = result.folder_manifest
    observed, expected = manifest["coverage"]
    out: list[str] = []
    out.append(f"# hyodo inspect: {manifest['root']}")
    out.append("")
    out.append(f"{observed}/{expected} files digested")
    unreadable_count = len(manifest["unreadable"])
    secret_shaped_count = sum(1 for f in manifest["files"] if f.get("secret_shaped"))
    ignored_count = sum(1 for f in manifest["files"] if f.get("ignored"))
    if unreadable_count:
        out.append(f"unreadable: {unreadable_count}")
    if secret_shaped_count:
        out.append(f"secret-shaped (not chunked): {secret_shaped_count}")
    if ignored_count:
        out.append(f"ignored: {ignored_count}")
    out.append(f"chunks: {len(result.chunks_manifest['chunks'])}")
    if manifest.get("changed_during_inspect"):
        out.append(f"changed during inspect: {len(manifest['changed_during_inspect'])}")
    if manifest.get("remote"):
        out.append("")
        out.append("## Remote inventory (declared, not observed)")
        for row in manifest["remote"]:
            out.append(
                f"- {row['source']}: {row['items_listed']} items listed, "
                f"{row['items_with_declared_digest']} with declared digest, "
                f"{row['items_shared_outside']} shared outside"
            )
    if unreadable_count:
        out.append("")
        out.append("## Unreadable")
        for entry in manifest["unreadable"]:
            out.append(f"- {entry['path']} ({entry['reason']})")
    return "\n".join(out) + "\n"


def render_report_json(result: InspectResult) -> str:
    """Render the folder-manifest JSON document (the `--report json` body)."""
    return json.dumps(result.folder_manifest, indent=2) + "\n"
