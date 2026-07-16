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

## Next patch track (afo_core)

### Applied in Dependabot P0 PR (2026-07-16)

Lock regenerated with Poetry after security floor bumps:

| Package | Before (stale lock) | After |
|---------|---------------------|-------|
| litellm | 1.72.0 | **1.92.0** |
| nltk | 3.9.2 | **3.10.0** |
| json-repair | 0.55.0 | **0.61.5** |
| transformers | 4.57.6 | **5.12.1** |
| pypdf | 6.6.0 | **6.14.2** |
| python-multipart | 0.0.21 | **0.0.32** |
| urllib3 | 2.6.3 | **2.7.0** |
| cryptography | 46.0.3 | **49.0.0** |
| langchain-core | 1.2.7 | **1.4.9** |
| chromadb | 1.4.1 | 1.4.1 (no safe patched release in range yet) |

Also:
- Removed `requirements-lock.txt` (duplicate Dependabot surface)
- `requirements.txt` is export of `poetry.lock` (SSOT)
- Dropped `crewai` (forced vulnerable litellm/json-repair pins)
- Dropped `moviepy` (conflicted with secure pillow>=12.2)
- Python range for afo_core: `>=3.10,<3.14` (litellm constraint)

### Residual risk

| Item | Status |
|------|--------|
| chromadb critical class without patched version | Still residual if rag extra is installed |
| starlette/aiohttp | May still have medium/high depending on advisory DB |
| agents extras without crewai | Reduced capability until upstream allows secure pins |

**Execution rule:** regenerate with Poetry, export `requirements.txt`, never hand-edit lock hashes. Public package CI must remain green without installing full afo_core.

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
