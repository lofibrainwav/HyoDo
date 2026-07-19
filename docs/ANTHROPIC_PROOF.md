# HyoDo Proof Map for Claude Code Enablement

This page is a **Claude-specific adapter map**. For the model-agnostic product
proof, start with [`PROVIDER_PROOF.md`](./PROVIDER_PROOF.md).

This page helps reviewers evaluating HyoDo as public proof of Claude Code,
agentic workflow, and technical enablement experience.

## One-sentence positioning

HyoDo is a model-agnostic quality gate kit that Claude Code (and any terminal
agent) can drive through one CLI. It turns AI-assisted development into an
inspectable loop: run a command, check quality, surface risk, and decide
whether to fix, escalate, or merge.

## What to inspect first

- Can this person build with Claude Code-style workflows?
  `hyodo/cli/main.py`, `README.md`, `QUICK_START.md`
- Can this person teach adoption through runnable material?
  `README.md`, `QUICK_START.md`, `install_interactive.sh`
- Can this person instrument success criteria?
  `.github/workflows/ci.yml`, `.github/workflows/smoke.yml`
- Can this person discuss security and review boundaries?
  `SECURITY.md`, `docs/SECURITY_SURFACE.md`, `hyodo safe`
- Can this person reason about cost without overclaiming?
  `docs/EXTERNAL_CLAIM_AUDIT.md`, `docs/PROVIDER_PROOF.md`

## Claude Code capability mapping

- Repeatable review gates: `hyodo check`, `hyodo score`, `hyodo safe`
  (`hyodo/cli/main.py`)
- CI parity with local runs: `.github/workflows/ci.yml`,
  `.github/workflows/smoke.yml`
- Safe onboarding: `install_interactive.sh`, `.env.minimal`, `SECURITY.md`
- Reviewer checklist workflow: `hyodo trinity "CHANGE"`
- Release-surface honesty: `docs/PROVIDER_PROOF.md`,
  `docs/EXTERNAL_CLAIM_AUDIT.md`

Claude Code, or any other terminal-based coding agent, can call the same
`hyodo` entrypoints a human runs locally — there is no separate
Claude-only code path to keep in sync.

## Safe public claims

Use:

```text
HyoDo is designed to reduce unnecessary premium-model usage by routing work by
risk and complexity.
```

Do not use as a guaranteed public benchmark:

```text
HyoDo saves every user a fixed percentage.
```

Historic internal ranges can be discussed only as selected-workflow observations
unless a public benchmark is linked.

## Demo-ready narrative

1. AI-assisted code is fast, but speed without review creates risk.
2. Run the vendor-neutral CLI in a terminal: `hyodo check`, `hyodo score`,
   `hyodo safe`. Claude Code drives the same commands through its shell tool.
3. CI (`.github/workflows/ci.yml`) and package smoke tests
   (`.github/workflows/smoke.yml`) make the review trail visible outside the
   chat.
4. `hyodo trinity "CHANGE"` produces a structured review checklist any agent
   can follow before merge.
5. Human review remains the final approval boundary — scores never
   auto-approve.

## Current boundary

HyoDo is public proof of a practical review workflow. It is not a claim that all
private production systems, customer results, or internal governance details are
publicly reproducible in this repository.
