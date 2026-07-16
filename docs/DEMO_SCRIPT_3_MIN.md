# HyoDo 3-Minute Demo Script

Purpose: a short recorded walkthrough or live screen-share script for reviewers,
technical enablement roles, and developer-facing interviews.

## Title

HyoDo in 3 minutes: model-agnostic quality gates for AI-assisted code

## Setup

- Open the HyoDo repository.
- Keep `README.md`, `QUICK_START_SIMPLE.md`, and a terminal visible.
- Use a disposable sample repo or harmless local fixture for live commands.
- Do not show real `.env` contents or private production paths.
- Prefer CLI commands so the demo is not locked to one agent vendor.

## Script

### 0:00-0:20 - Problem

AI-assisted code is fast, but speed is not the same as trust. HyoDo is a
quality-gate kit for making AI-generated changes inspectable before they become
trusted code — on Claude, Codex, Grok, Gemini, Cursor, or plain terminal.

### 0:20-0:50 - Public surface

Start with the README. The first promise is intentionally practical: quality
gates, safety checks, and cost-aware review. No guaranteed savings claim, no
blind auto-approval. Public package is `hyodo/`; extended `afo_core/` is advisory.

### 0:50-1:35 - Command loop

Show the core loop in a terminal:

```bash
hyodo check
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --loyalty 0.9
hyodo safe
```

Explain:

- `check` runs quality gates (ruff / pyright / pytest path).
- `score` gives a review signal, not a final approval.
- `safe` surfaces risky patterns as an early warning, not a full SAST product.

Optional: mention slash-command adapters under `commands/` for agent UIs.

### 1:35-2:15 - CI and proof

Open `.github/workflows/smoke.yml` or `.github/workflows/ci.yml`.

Point out:

- package build and metadata validation;
- CLI entrypoint smoke checks;
- public API import checks;
- advisory separation for extended legacy modules (`afo_core`).

### 2:15-2:45 - Cost-aware routing

Open the README cost-aware routing section.

Say:

HyoDo is designed to reduce unnecessary premium-model use by routing by risk and
complexity across FREE / STANDARD / PREMIUM tiers. I treat historic cost ranges
as internal observations unless a public benchmark is linked.

### 2:45-3:00 - Close

This is how I teach adoption: runnable systems, clear gates, and explicit human
approval boundaries. HyoDo is not slideware; it is the public slice of how I
turn AI-assisted development into a workflow teams can inspect across vendors.

## Follow-up answers

### Is this an auto-approval system?

No. Scores support review. Tests, security checks, and human judgment remain
required.

### Why does GitHub show many security alerts?

Most Dependabot volume is on the extended `afo_core` lock surface. The public
`hyodo` package is intentionally thin. See `docs/SECURITY_SURFACE.md`.

### Does it only work with Claude Code?

No. CLI and CI are primary. Claude Code is one optional adapter.
