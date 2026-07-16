# HyoDo Proof Map for Claude Code Enablement

This page is a reviewer-facing map for people evaluating HyoDo as public proof
of Claude Code, agentic workflow, and technical enablement experience.

## One-sentence positioning

HyoDo is a Claude Code quality gate and cost-aware review kit that turns
AI-assisted development into an inspectable loop: run a command, check quality,
surface risk, and decide whether to fix, escalate, or merge.

## What to inspect first

| Review question | HyoDo evidence |
|-----------------|----------------|
| Can this person build with Claude Code-style workflows? | `commands/` slash commands and `QUICK_START_SIMPLE.md` |
| Can this person teach adoption through runnable material? | `README.md`, `QUICK_START_SIMPLE.md`, `install_interactive.sh` |
| Can this person instrument success criteria? | `.github/workflows/ci.yml`, `.github/workflows/smoke.yml` |
| Can this person discuss security and review boundaries? | `SECURITY.md`, `/safe`, safety gate docs |
| Can this person reason about cost without overclaiming? | README cost-aware routing section and public claim note |

## Claude Code capability mapping

| Capability area | HyoDo surface |
|-----------------|---------------|
| Slash-command workflow | `commands/check.md`, `commands/score.md`, `commands/safe.md`, `commands/start.md` |
| Repeatable review gates | `hyodo/cli/main.py`, `.github/workflows/ci.yml`, `.github/workflows/smoke.yml` |
| Safe onboarding | `install_interactive.sh`, `.env.minimal`, `SECURITY.md` |
| Skills and agent patterns | `skills/`, `agents/`, `commands/SKILL_INDEX.md` |
| Cost-aware operation | `/cost`, README cost-aware routing, public claim note |

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
2. HyoDo gives Claude Code users a small command loop: `/check`, `/score`, `/safe`.
3. CI and package smoke tests make the review trail visible outside the chat.
4. Cost-aware routing keeps low-risk work away from unnecessary premium-model use.
5. Human review remains the final approval boundary.

## Current boundary

HyoDo is public proof of a practical review workflow. It is not a claim that all
private production systems, customer results, or internal governance details are
publicly reproducible in this repository.
