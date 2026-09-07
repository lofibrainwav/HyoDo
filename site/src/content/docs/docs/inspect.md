---
title: Inspect
description: Absorb a directory into a digest inventory and byte-range chunk map — local, read-only, no policy call.
---

## What it does

`hyodo inspect <path>` walks a directory the way a field-deployment
engineer would — a documents folder, a repository, or any subtree — and
produces an inventory whose analysis is complete by definition: every file
is either digested, or explicitly listed under `unreadable`. It writes
`.hyodo/folder-manifest.json` (whole-file digests) and
`.hyodo/chunks-manifest.json` (fixed 4096-byte chunk ranges). It is
read-only and never calls `evaluate_policy` — absorbing a directory you
explicitly pointed HyoDo at is not an external variable.

```bash
hyodo inspect docs --ignore "*.png"
```

## What is stored

- A 12-hex-char content digest, size, and mtime per file.
- Byte ranges and chunk digests in `chunks-manifest.json` — never chunk
  text.
- An `unreadable` entry (with a reason) for anything that could not be
  digested, including symlinks that escape the root.
- A `--remote-inventory` claim, copied verbatim under `remote:` — a
  connector's own declaration, never verified by fetching.

## What is never stored

- File contents, chunk text, or embeddings of any kind — chunking a file
  is not the same as vectorizing it; HyoDo emits ids, digests, and byte
  ranges only.
- A file with a `secret`-category finding from `hyodo safe`'s scanner:
  it is digested (still "observed") but excluded from chunking and
  reported by digest and location only, never by value.
- A percentage. `coverage` is always printed as `<observed>/<expected>
  files digested`, an integer count.

## Exit codes

| Outcome | Exit |
| --- | --- |
| Manifests written, coverage complete | 0 |
| `<path>` missing/not a directory, or malformed `--remote-inventory` | 1 |
| Manifest write failed (`OSError`) | 2 |

There is no `ASK`/exit-3 case — `hyodo inspect` never calls
`evaluate_policy`.

## Full reference

[docs/INSPECT.md](https://github.com/lofibrainwav/HyoDo/blob/main/docs/INSPECT.md)
covers the data model, symlink handling, and the remote-inventory schema in
full.

## Next

- [Graph Export](/docs/graph-export/)
- [Skills](/docs/skills/)
