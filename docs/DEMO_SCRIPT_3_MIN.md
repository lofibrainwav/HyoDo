# HyoDo 3-Minute Demo Script

Purpose: a short recorded walkthrough or live screen-share script for reviewers,
technical enablement roles, and developer-facing interviews.

## Title

HyoDo in 3 minutes: quality gates for Claude Code

## Setup

- Open the HyoDo repository.
- Keep `README.md`, `QUICK_START_SIMPLE.md`, and a terminal visible.
- Use a disposable sample repo or harmless local fixture for live commands.
- Do not show real `.env` contents or private production paths.

## Script

### 0:00-0:20 - Problem

AI-assisted code is fast, but speed is not the same as trust. HyoDo is my
Claude Code quality-gate kit for making AI-generated changes inspectable before
they become trusted code.

### 0:20-0:50 - Public surface

Start with the README. The first promise is intentionally practical: quality
gates, safety checks, and cost-aware review. No guaranteed savings claim, no
blind auto-approval.

### 0:50-1:35 - Command loop

Show the core loop:

```text
/check
/score
/safe
```

Explain:

- `/check` runs quality gates.
- `/score` gives a review signal, not a final approval.
- `/safe` surfaces risky operations before they land.

### 1:35-2:15 - CI and proof

Open `.github/workflows/smoke.yml` or `.github/workflows/ci.yml`.

Point out:

- package build and metadata validation;
- CLI entrypoint smoke checks;
- public API import checks;
- advisory separation for extended legacy modules.

### 2:15-2:45 - Cost-aware routing

Open the README cost-aware routing section.

Say:

HyoDo is designed to reduce unnecessary premium-model use by routing by risk and
complexity. I treat historic cost ranges as internal observations unless a public
benchmark is linked.

### 2:45-3:00 - Close

This is how I teach adoption: runnable systems, clear gates, and explicit human
approval boundaries. HyoDo is not slideware; it is the public slice of how I
turn AI-assisted development into a workflow teams can inspect.

## Follow-up answers

### Is this an auto-approval system?

No. Scores support review. Tests, security checks, and human judgment remain
required.

### Where are the private production systems?

Private systems are not exposed in HyoDo. This repo is the public workflow kit:
commands, gates, scoring utilities, and onboarding material.

### What would you improve next?

Add a public benchmark fixture for cost-aware routing and a short video showing
the command loop end to end.
