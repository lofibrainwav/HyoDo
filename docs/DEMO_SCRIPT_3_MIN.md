# HyoDo 3-Minute Demo Script

Purpose: a short recorded walkthrough or live screen-share script for reviewers,
technical enablement roles, and developer-facing interviews.

**Target version:** see `VERSION` (SSOT; do not hardcode). Current public line: **3.3.0**.

## Title

HyoDo in 3 minutes: model-agnostic quality gates for AI-assisted code

## Setup

- On `main`, clean worktree (`git status` clean), tag `v3.3.0` or later if demoing a release.
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

- model-agnostic quality gate (model/UI independent — not language-agnostic)
- CLI + CI first
- tiered routing is **intent only** (no guaranteed savings)
- PyPI: `pip install hyodo` (measure live version if you claim it)

Say: the public package is `hyodo/` (Python package + CLI).

### 0:50-1:50 - Command loop

```bash
hyodo --version
hyodo check
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --hyo 0.9
hyodo safe
# secret fixture
printf 'token = ghp_abcdefghijklmnopqrstuvwxyz012345\n' > /tmp/hyodo-demo-safe.txt
hyodo safe /tmp/hyodo-demo-safe.txt
hyodo safe --strict /tmp/hyodo-demo-safe.txt   # expect non-zero
```

Explain:

- `check` — HyoDo checkout gates (pyright / ruff / pytest / optional SBOM);
  success phrase is **All executed gates passed**; empty/foreign trees exit **2**
- `score` — **REVIEW_SIGNAL**, not final approval; emphasis % is not F-weight
- `safe` — early warning; default exit 0; **`--strict`** exit 1 on high findings

Optional 10s honesty beat:

```bash
mkdir -p /tmp/hyodo-empty-demo && hyodo check /tmp/hyodo-empty-demo
# expect exit 2: No project gates were executed / not a validation pass
```

### 1:50-2:20 - CI and proof

Open `.github/workflows/smoke.yml` or CI badge/history.

Point out:

- package build + twine + wheel install
- sdist ships only the public `hyodo` package
- public API and version SSOT
- public pytest is a release blocker (Truth Patch)

Optional: `docs/PROVIDER_PROOF.md` for multi-vendor mapping.
Do **not** lead with Claude-only pages unless the audience asks.

### 2:20-2:45 - Boundaries

State clearly:

1. Scores are review signals; humans approve merges.
2. `check` is not a universal multi-language gate.
3. No public cost-savings benchmark; tiered routing is design intent.

### 2:45-3:00 - Close

Runnable gates, explicit human authority, model-agnostic surface. HyoDo is not
slideware — it is the public slice of an inspectable AI-assisted workflow.

## Follow-up answers

### Is this an auto-approval system?

No. Strong scores are review signals. `is_strong_review_signal` never grants
write or merge authority. `should_auto_approve` is deprecated naming only.

### What about Dependabot / security?

Public package is the release gate. Extended tree alerts are advisory. Measure
open alerts live; do not quote historical inflated counts as current truth.

### PyPI?

Measure live before claiming:

```bash
curl -s https://pypi.org/pypi/hyodo/json | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['version'])"
```

As of the v3.3.0 release, public PyPI ships **3.3.0** (confirm live).
