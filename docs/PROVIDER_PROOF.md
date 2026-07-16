# HyoDo Proof Map (Model-Agnostic)

Reviewer-facing map for evaluating HyoDo as a quality-gate kit that works across
major AI coding surfaces — not only one vendor.

## One-sentence positioning

HyoDo is a model-agnostic quality gate and cost-aware review kit that turns
AI-assisted development into an inspectable loop: run a command, check quality,
surface risk, and decide whether to fix, escalate, or merge.

## What to inspect first

| Review question | HyoDo evidence |
|-----------------|----------------|
| Is there a vendor-neutral entrypoint? | `hyodo` CLI (`hyodo/cli/main.py`), `pyproject.toml` scripts |
| Are gates real (not slideware)? | `.github/workflows/ci.yml`, `.github/workflows/smoke.yml` |
| Are public claims bounded? | README "What HyoDo does not claim" |
| Is security posture honest? | `SECURITY.md`, `docs/SECURITY_SURFACE.md`, `hyodo safe` |
| Can agents wrap the same loop? | `commands/check.md`, `score.md`, `safe.md`, `start.md` |

## Provider mapping (examples, not exclusivity)

| Provider / surface | How to use HyoDo |
|--------------------|------------------|
| Plain terminal | `pip install -e ".[dev]" && hyodo check` |
| Claude Code | Load `commands/` slash docs; still prefer CLI for CI parity |
| OpenAI Codex / CLI agents | Call `hyodo` in shell tools; follow `AGENTS.md` if present |
| xAI Grok | Same CLI; optional project skills adapter |
| Google Gemini CLI | Same CLI; route cost tiers by risk, not brand |
| Cursor | Terminal tasks + optional rules pointing at `hyodo check/safe` |
| Local models (Ollama etc.) | FREE tier for lint/test/debug; HyoDo gates remain external truth |

## Safe public claims

Use:

```text
HyoDo is designed to reduce unnecessary premium-model usage by routing work by
risk and complexity across model tiers.
```

Do not use as a guaranteed public benchmark:

```text
HyoDo saves every user a fixed percentage.
HyoDo auto-approves changes above score 90.
```

## Demo-ready narrative (3 minutes)

1. AI-assisted code is fast; trust still needs gates.
2. Show `hyodo check` / `hyodo score` / `hyodo safe` in a terminal.
3. Open CI workflows: public package is the release surface.
4. State clearly: scores are review signals; humans approve.
5. Mention cost tiers (FREE / STANDARD / PREMIUM), not a single vendor.

## Related vendor-specific map

For Claude-specific enablement language, see
[`ANTHROPIC_PROOF.md`](./ANTHROPIC_PROOF.md). That page is an adapter map, not
the only supported surface.
