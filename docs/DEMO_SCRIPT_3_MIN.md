# HyoDo 3-Minute Demo Script

Purpose: a short recorded walkthrough or live screen-share script for reviewers,
technical enablement roles, and developer-facing interviews.

**Target version:** see `VERSION` (SSOT; do not hardcode).

## Title

HyoDo in 3 minutes: model-agnostic quality gates for AI-assisted code

## Setup

- On `main`, clean worktree (`git status` clean).
- Run `bash scripts/verify-public.sh` (must exit 0) before recording.
- Run `bash scripts/demo-dry-run.sh`; its receipt is a pre-commit worktree
  record, so use the live terminal output—not the receipt header—as the
  recording source of truth.
- Keep `README.md`, terminal, and optionally `docs/PROVIDER_PROOF.md` visible.
- Prefer CLI so the demo is not locked to one agent vendor.
- Do **not** show real `.env` contents or private production paths.

## Script

### 0:00-0:20 - Problem

AI-assisted code is fast, but speed is not the same as trust. HyoDo is a
quality-gate kit for making AI-generated changes inspectable before they become
trusted code — on Claude, Codex, Grok, Gemini, Cursor, or plain terminal.

### 0:20-0:50 - Public surface

Start with the README top:

- model-agnostic quality gate
- CLI + CI first
- tiered routing is **intent only** (no guaranteed savings)

Say: public package is `hyodo/`; extended `afo_core/` is advisory and not the
demo path.

### 0:50-1:40 - Command loop

```bash
hyodo --version
hyodo check
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --loyalty 0.9
hyodo safe
# optional secret fixture
printf 'token = ghp_abcdefghijklmnopqrstuvwxyz012345\n' > /tmp/hyodo-demo-safe.txt
hyodo safe /tmp/hyodo-demo-safe.txt
```

Explain:

- `check` — 4 gates (pyright / ruff / pytest / optional SBOM); exit 0 only if all pass
- `score` — **REVIEW_SIGNAL**, not final approval
- `safe` — early warning; secrets fixture should show high risk / human gate

### 1:40-2:15 - CI and proof

Open `.github/workflows/smoke.yml` or CI badge/history.

Point out:

- package build + twine + wheel install
- sdist does **not** ship `afo_core`
- public API and version SSOT

Optional: `docs/PROVIDER_PROOF.md` for multi-vendor mapping.
Do **not** lead with Claude-only pages unless the audience asks.

### 2:15-2:40 - Boundaries

State clearly:

1. Scores are review signals; humans approve merges.
2. `afo_core` is advisory extended tree.
3. No public cost-savings benchmark; tiered routing is design intent.

### 2:40-3:00 - Close

Runnable gates, explicit human authority, model-agnostic surface. HyoDo is not
slideware — it is the public slice of an inspectable AI-assisted workflow.

## Follow-up answers

### Is this an auto-approval system?

No. Strong scores are review signals. `is_strong_review_signal` never grants
write or merge authority.

### What about Dependabot / security?

Public package is the release gate. Extended tree alerts are advisory. As of
3.1.x readiness work, open Dependabot alerts were driven to zero with documented
no-patch residual policy for afo_core-only packages.

### PyPI?

GitHub release matching `VERSION` is the demo source of truth. PyPI publish is a
separate decision; do not claim a newer PyPI version unless measured live.
