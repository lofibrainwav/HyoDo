# HyoDo Security Surface

This document defines what GitHub "Security and quality" numbers mean for HyoDo
and how release gates relate to dependency alerts.

## Two surfaces

| Surface | Path | Release blocker? | Typical Dependabot impact |
|---------|------|------------------|---------------------------|
| **Public product** | `hyodo/`, root `pyproject.toml` | **Yes** | Minimal (`typer`, `rich`, optional dev tools) |
| **Extended / legacy** | `afo_core/` lockfiles | **No (advisory)** | High volume (LLM stacks, parsers, servers) |

CI already treats `afo_core` lint as advisory (`continue-on-error: true` in
`.github/workflows/ci.yml`). Public smoke tests install and run the `hyodo`
package only.

## How to read "Security and quality 310"

As of the 2026-07-16 audit:

- Open Dependabot alerts were **pip-only** and concentrated under `afo_core/`
  manifests (`poetry.lock`, `requirements.txt`, `requirements-lock.txt`).
- The same CVE often appears on multiple lock files, so UI count **inflates**
  unique issues.
- Code scanning (CodeQL) was **not** configured (`no analysis found`).
- Secret scanning open alerts: **0**.

Therefore:

```text
UI alert count ≠ public package vulnerability count
UI alert count ≠ unique CVE count
```

## Current operational policy

1. **Public install path must stay thin.** Do not add heavy LLM/server deps to
   root `pyproject.toml` without an explicit optional extra and review.
2. **afo_core upgrades are a separate track.** Prefer lock single-sourcing
   (one generator) before mass version bumps.
3. **Critical/High on afo_core** should be patched or removed when those modules
   are actually executed; otherwise mark optional/unmaintained clearly.
4. **Do not claim "all vulnerabilities patched"** in `SECURITY_PATCHES.md`
   unless a fresh Dependabot/pip-audit readback is attached.

## Verification commands

Public package:

```bash
pip install -e ".[dev]"
hyodo check
hyodo safe
python -m pytest tests -q
```

Dependency posture (extended tree; not a public gate):

```bash
# example — requires tooling installed in that environment
pip-audit -r afo_core/requirements.txt || true
```

## Related docs

- [`SECURITY.md`](../SECURITY.md) — reporting and keyword safety gates
- [`SECURITY_PATCHES.md`](../SECURITY_PATCHES.md) — historical patch log (may be stale)
- [`.github/dependabot.yml`](../.github/dependabot.yml) — update grouping
