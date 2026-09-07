# Field-deployment absorption (`hyodo inspect`)

`hyodo inspect <path>` absorbs a whole directory the way a field-deployment
engineer would: a documents folder, a repository, or any subtree HyoDo is
pointed at. The result is an inventory whose analysis is complete by
definition — either coverage `observed/expected` is `N/N`, or every
unobserved region is explicitly enumerated under `unreadable`. Every
conclusion cites a file digest, a chunk id, or a byte range; nothing is ever
silently treated as "checked and clean".

`hyodo inspect` is a local, read-only report generator. It never calls
`evaluate_policy` and never makes a network call — absorbing a directory the
operator explicitly pointed HyoDo at is not itself an external variable the
way fetching a skill from an unlisted source is (see `docs/SKILLS.md`).

## CLI surface

```text
hyodo inspect <path> [--ignore <glob>]... [--remote-inventory <json-file>]...
              [--report md|json] [--root <dir>]
```

- `<path>`: the directory to absorb. Must exist and be a directory.
- `--ignore <glob>` (repeatable): an `fnmatch` glob tested against both the
  file's path (relative to `--root`) and its bare basename. A matching file
  is still listed in `files` with `ignored: true` and an `ignore_reason`,
  but it is excluded from `chunks-manifest.json` and from `coverage`'s
  `expected` count. `.gitignore` is never read — an explicit `--ignore` is
  the operator's decision, not an inherited one, so it cannot silently hide
  security-relevant files from `inspect`.
- `--remote-inventory <json-file>` (repeatable): see "Remote inventory"
  below.
- `--report md` (default) or `--report json`: which report renders to
  stdout. Both formats always write both manifest files.
- `--root <dir>` (default: current working directory): the base that every
  reported `path` is relative to, POSIX separators.

## Data model

`.hyodo/folder-manifest.json`, schema `hyodo.folder-manifest/v1`:

```json
{
  "schema": "hyodo.folder-manifest/v1",
  "root": "examples/fde-evidence-spine",
  "generated_at": "2026-09-06T12:00:00+00:00",
  "files": [
    {
      "path": "examples/fde-evidence-spine/README.md",
      "digest": "a1b2c3d4e5f6",
      "size": 1834,
      "mtime": "2026-09-06T11:00:00+00:00",
      "ignored": false,
      "ignore_reason": null,
      "secret_shaped": false
    }
  ],
  "unreadable": [],
  "coverage": [3, 3]
}
```

`digest` is `content_digest` (12 hex chars, `hyodo/events.py`) over the
whole file's bytes. `mtime` is ISO-8601 UTC with a `+00:00` offset.

Two optional top-level keys appear only when relevant:

- `changed_during_inspect`: `[{path, digest_before, digest_after}]` — a file
  whose bytes changed between the digest pass and the chunk pass. The run
  still exits 0; one warning line is printed per changed file.
- `remote`: declared connector inventories (see below).

`.hyodo/chunks-manifest.json`, schema `hyodo.chunks-manifest/v1` — chunk id,
file digest, byte range, chunk digest, **never chunk text**:

```json
{
  "schema": "hyodo.chunks-manifest/v1",
  "chunks": [
    {
      "chunk_id": "c-0001",
      "file_digest": "a1b2c3d4e5f6",
      "byte_range": [0, 1834],
      "chunk_digest": "f6e5d4c3b2a1"
    }
  ]
}
```

Chunks are fixed 4096-byte windows over a file's bytes (`byte_range` is
`[start, end)`, the last chunk shorter). `chunk_id` is `c-%04d`, assigned
sequentially over files sorted by relative path and then by offset (past
9999 chunks the number keeps widening rather than wrapping). Embedding a
chunk is an external BYOM node's job; HyoDo emits only ids, digests, and
byte ranges, never the vectors and never the text.

## Evaluation order

1. Walk the tree, skipping the same build/vendor directories `hyodo safe`
   already skips (`_SKIPPED_DIR_NAMES`: `.venv`, `node_modules`,
   `__pycache__`, `dist`, `build`, and the tool caches) — never walked, never
   listed.
2. Digest each readable file's whole bytes into `folder-manifest.json`.
3. Run `hyodo safe`'s `scan_text` over each readable, non-ignored file
   before anything is chunked. A file with any `category == "secret"`
   finding is `secret_shaped: true`, excluded from chunking, and reported by
   digest and location only — never by value. It still counts as observed
   (it was digested).
4. Chunk every remaining readable, non-ignored, non-secret-shaped file into
   `chunks-manifest.json`.

## Coverage

`coverage` is `[observed, expected]`:

- `expected` — every non-ignored regular file found, including unreadable
  ones.
- `observed` — those actually digested (`expected` minus `unreadable`).

The human (`--report md`) report always prints `<observed>/<expected> files
digested`, plus `unreadable: N` and `secret-shaped (not chunked): N` when
either is non-zero. Never a percentage — "unobserved" must stay visible as a
count, not get rounded away.

## Unreadable files and symlinks

An unreadable file (permission error, or any `OSError` on read) is always an
`unreadable` entry — never a silent skip. Binary files are **not**
unreadable: they are digested as bytes and chunked as byte ranges like any
other file, since chunks never depend on text decoding.

Symlinks:

- A symlink whose resolved target lies outside the resolved `<path>` is
  never followed. It is excluded from both manifests and listed under
  `unreadable` with reason `symlink_outside_root`.
- A symlink to a directory is never recursed into. It is listed under
  `unreadable` with reason `symlink_dir_skipped` (no directory symlink
  recursion).
- A symlink to a regular file inside `<path>` is followed once, like a
  normal file.

## Digest mismatch between passes

The chunk pass re-reads each file's bytes. If the whole-file digest from
that re-read differs from the digest pass's, the pass-2 digest is what
chunks are built from, the file is recorded under `changed_during_inspect`,
and one warning line is printed. The run still exits 0 — a file changing
under a live repository is reported, not silently resolved by picking one
version.

## Remote inventory (Drive-shaped, no network)

`--remote-inventory <json-file>` accepts a `hyodo.remote-inventory/v1`
document — a listing the operator already obtained from a connector (for
example, a Drive MCP tool call), never fetched by HyoDo itself:

```json
{
  "schema": "hyodo.remote-inventory/v1",
  "source": "drive:Finance-2026",
  "items": [
    {
      "id": "abc123",
      "name": "Q3 report.pdf",
      "mime_type": "application/pdf",
      "modified_at": "2026-08-01T00:00:00+00:00",
      "declared_digest": null,
      "revision": "7",
      "shared_outside": true
    }
  ]
}
```

HyoDo copies this into `folder-manifest.json` under `remote: [{source,
items_listed, items_with_declared_digest, items_shared_outside, items}]`.
**These are declarations, never observations**: remote-inventory items never
enter `coverage` and never produce chunks. A malformed file, or one with the
wrong or missing schema, exits 1 with a clear message before any manifest is
written — the same "fail closed before writing" posture the exit contract
below uses for a missing `<path>`.

A remote inventory is a claim by the connector that produced it. HyoDo never
fetches the referenced content to verify it; the claim is recorded exactly
as given, alongside its source label, so a later reviewer can see what was
declared without HyoDo pretending it observed content it never touched.

## Exit contract

| Outcome | Exit |
| --- | --- |
| Manifests written, coverage complete | 0 |
| `<path>` does not exist or is not a directory | 1 |
| A `--remote-inventory` file is malformed or the wrong schema | 1 |
| Manifest write failure (`OSError`, e.g. `.hyodo` cannot be created) | 2 |

There is no `ASK`/exit-3 case: `hyodo inspect` never calls `evaluate_policy`.

## Determinism

Two runs over an unchanged tree produce identical manifests except
`generated_at`.

## Backward compatibility

`hyodo inspect` is a wholly new command. It writes only
`.hyodo/folder-manifest.json` and `.hyodo/chunks-manifest.json`; a checkout
that has never run `inspect` is unaffected. No existing schema, CLI surface,
or exit contract changes.
