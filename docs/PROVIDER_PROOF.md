# HyoDo Proof Map (Model-Agnostic)

Reviewer-facing map for evaluating HyoDo as a quality-gate kit that works
across AI coding surfaces via one shared CLI — not one vendor's plugin
format.

## One-sentence positioning

HyoDo is a model-agnostic quality gate and cost-aware review kit that turns
AI-assisted development into an inspectable loop: run a command, check
quality, surface risk, and decide whether to fix, escalate, or merge.

## What to inspect first

- Is there a vendor-neutral entrypoint?
  - `hyodo` CLI (`hyodo/cli/main.py`), `pyproject.toml`
    `[project.scripts]`
- Are gates real (not slideware)?
  - `.github/workflows/ci.yml` (5 jobs),
    `.github/workflows/smoke.yml`
- Are public claims bounded?
  - README "Two tracks" section
- Is security posture honest?
  - `SECURITY.md`, `docs/SECURITY_SURFACE.md`, `hyodo safe`
- Are runtime dependencies thin?
  - `pyproject.toml` — `jsonschema`, `typer`, `rich`, plus conditional
    `tomli` for Python 3.10

## Why the CLI is the model-agnostic surface

HyoDo ships one Python entrypoint. Any agent, shell, or CI runner that can
execute a subprocess can drive it — no vendor-specific plugin format is
required:

```bash
hyodo --version
hyodo check          # HyoDo checkout only: Pyright/Ruff/pytest/SBOM gates
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 \
  --benevolence 0.9 --hyo 0.9
hyodo safe            # dependency-light safety early-warning scan
hyodo safe --strict   # exit 1 on high-severity findings
hyodo start           # onboarding
hyodo trinity          # structured review checklist
```

Because these are plain CLI commands (see `hyodo/cli/main.py`), any coding
agent that can run shell commands can call them the same way a human does in
a terminal — the contract is the exit code and stdout, not a proprietary
integration.

## CI as parallel, reproducible proof

`.github/workflows/ci.yml` runs five independent jobs on every push and pull
request: `truth-gate` (matrix across Python 3.10/3.11/3.12), `goodness-gate`,
`beauty-gate`, `sbom`, and `trinity-score`. `.github/workflows/smoke.yml`
runs a separate install-and-CLI smoke test. These jobs are real GitHub
Actions runs, inspectable in the Actions tab — not slides.

## Thin runtime dependency surface

`pyproject.toml` declares `jsonschema>=4.18,<5`, `typer>=0.9.0`, and
`rich>=13.0.0` as runtime dependencies, plus conditional `tomli` for Python
3.10. Development/test tooling (`pytest`, `ruff`, `pyright`, etc.) is
isolated under `[project.optional-dependencies].dev` and is not required to
run the published `hyodo` package.

## Safe public claims

Use:

```text
HyoDo is designed to reduce unnecessary premium-model usage by routing work
by risk and complexity across model tiers.
```

Do not use as a guaranteed public benchmark:

```text
HyoDo saves every user a fixed percentage.
HyoDo auto-approves changes above score 90.
```

## Demo-ready narrative (3 minutes)

1. AI-assisted code is fast; trust still needs gates.
2. Show `hyodo check` / `hyodo score` / `hyodo safe` in a terminal.
3. Open CI workflows: five parallel jobs are the release-gate signal.
4. State clearly: scores are review signals; humans approve.
5. Mention cost tiers (FREE / STANDARD / PREMIUM), not a single vendor.

## Related vendor-specific map

For Claude-specific enablement language, see
[`ANTHROPIC_PROOF.md`](./ANTHROPIC_PROOF.md). That page is an adapter map, not
the only supported surface.
