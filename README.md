# HyoDo

> **A model-agnostic quality-gate kit for AI-assisted developers.**

HyoDo helps developers review, score, and ship AI-assisted code with a repeatable
quality workflow. Primary surface is the `hyodo` CLI and CI gates. Optional adapters
cover Claude Code, Codex, Grok, Gemini CLI, Cursor, and other agent UIs so
AI-generated changes can be inspected before they become trusted code.

<p align="center">
  <img src="https://img.shields.io/badge/Model-Agnostic-0A7-blue" alt="Model agnostic">
  <img src="https://img.shields.io/badge/CLI%2BCI-First-blueviolet" alt="CLI and CI first">
  <img src="https://img.shields.io/badge/Tiered_Routing-intent_only-lightgrey" alt="Tiered routing intent only">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
  <img src="https://img.shields.io/badge/Python-3.10+-blue" alt="Python">
  <img src="https://img.shields.io/badge/Version-3.1.3-success" alt="Version">
</p>

---

## 30-second proof

| Proof point | What to inspect |
|-------------|-----------------|
| Public package | `hyodo/` Python package, `pyproject.toml`, and `hyodo` CLI entrypoint |
| Agent adapters | `commands/` slash-command docs (Claude and compatible agents) plus plain CLI |
| Quality gates | `.github/workflows/ci.yml` and `.github/workflows/smoke.yml` |
| Safety posture | `SECURITY.md`, `docs/SECURITY_SURFACE.md`, `.env.example`, `.env.minimal` |
| Routing discipline | Tiered model routing is design intent only; no guaranteed savings claim |

If you are reviewing HyoDo for a role, partnership, or technical screen, start with
[`QUICK_START_SIMPLE.md`](./QUICK_START_SIMPLE.md),
[`docs/PROVIDER_PROOF.md`](./docs/PROVIDER_PROOF.md),
[`docs/EXTERNAL_CLAIM_AUDIT.md`](./docs/EXTERNAL_CLAIM_AUDIT.md), and optionally
[`docs/ANTHROPIC_PROOF.md`](./docs/ANTHROPIC_PROOF.md) for Claude-specific mapping.

## Who is this for?

HyoDo is for developers and small teams who:

- use AI-assisted coding workflows (any major model vendor or local models);
- want a repeatable review checklist before trusting AI-generated changes;
- need fast local checks for linting, typing, tests, and safety;
- want to route simple tasks away from expensive model calls when possible;
- prefer CLI/CI-first workflows that optional agent UIs can wrap.

## What problem does it solve?

AI-assisted development is fast, but speed without review creates risk. HyoDo turns review into a simple operating loop:

```text
AI-assisted change
→ hyodo check   (or /check in an agent adapter)
→ hyodo score + hyodo safe
→ fix or escalate
→ ship with a visible quality trail
```

The goal is not blind automation. The goal is to make AI-assisted work easier to inspect, safer to merge, and cheaper to operate.

## What HyoDo does not claim

- It does **not** replace human code review, tests, or security review.
- It does **not** guarantee a fixed cost-reduction percentage.
- It does **not** automatically approve risky changes just because a score is high.
- It does **not** require the optional philosophy layer to use the practical gates.
- It does **not** treat Dependabot alerts on optional/legacy `afo_core` as failures of the public `hyodo` package.

## What is included?

- **CLI-first quality loop** — `hyodo check`, `hyodo score`, `hyodo safe`, `hyodo trinity`.
- **Agent adapters** — `commands/` docs for slash-command UIs (Claude Code and compatible tools).
- **Quality gates** — lint, format, type, test, and security-oriented checks.
- **Scoring utilities** — Python package helpers for repeatable review signals.
- **Tiered model routing (intent)** — optional guidance to prefer FREE/STANDARD/PREMIUM paths by risk and complexity. Not a measured savings product.
- **Public package gates** — CI checks for the public `hyodo` package, with extended `afo_core` checks separated as advisory.

## Quick Start

### Recommended install: clone, inspect, then run

```bash
git clone https://github.com/lofibrainwav/HyoDo.git ~/.hyodo
cd ~/.hyodo

# Optional: inspect the installer before running it
sed -n '1,220p' install_interactive.sh

# Interactive setup
./install_interactive.sh
```

### One-line install for trusted environments

```bash
curl -sSL https://raw.githubusercontent.com/lofibrainwav/HyoDo/main/install_interactive.sh | bash
```

### Run with the CLI (recommended, model-agnostic)

```bash
cd ~/.hyodo
pip install -e ".[dev]"
hyodo start
hyodo check
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --loyalty 0.9
hyodo safe
```

### Optional: agent slash-command adapter

If you use Claude Code or another slash-command agent that can load `commands/`:

```bash
cd ~/.hyodo
# open your agent of choice, then:
/start
/check
/score
/safe
```

## Requirements

### Minimal setup

- Python 3.10+
- Git
- Terminal (any agent UI optional)

### Full setup

- Python 3.10+
- Git
- Optional agent CLI (Claude Code, Codex, Grok, Gemini CLI, Cursor, etc.)
- Docker & Docker Compose when using extended local services
- Redis, PostgreSQL, Ollama, or the provided Docker setup only if you need extended modules

## Configuration

### Minimal configuration

```bash
cp .env.minimal .env
# Set provider keys only for the adapters you actually use
```

### Full configuration

```bash
cp .env.example .env
# Fill in the services you plan to use
```

Keep secrets out of git history. Never commit `.env` files containing real credentials.

## Basic Usage

```bash
hyodo check     # Run quality gates
hyodo score     # Calculate review signal (not auto-approval)
hyodo safe      # Lightweight safety early-warning scan
hyodo trinity "describe change"  # Structured review checklist
```

## Score Interpretation

| F Score | S Score | Status | Suggested Action |
|:-------:|:-------:|:-------|:-----------------|
| **F ≥ 54** | **S ≥ 8** | Excellent | Strong review signal — human approval still required |
| **F ≥ 45** | **S ≥ 7** | Good | Review recommended |
| **F < 45** | — | Needs Work | Improve before merge |

Scores are decision support, not a replacement for human review.

## Quality Gates

### 4-Gate CI Protocol

```text
Gate 1: Pyright → type checking
Gate 2: Ruff → lint + format
Gate 3: pytest → tests
Gate 4: SBOM / security-oriented seal
```

## Tiered model routing (intent only)

HyoDo can help teams **think in tiers** so not every task goes to a premium model.
This is routing guidance, not a cost-savings guarantee.

| Tier | Use Case | Example providers (not exclusive) | Cost Profile |
|------|----------|-----------------------------------|--------------|
| FREE / local | Read-only, search, lint, tests | Ollama, local open models | $0 where available |
| STANDARD | Simple edits, low-risk cleanup | Codex, Gemini, Grok, mid-tier APIs | Low-moderate |
| PREMIUM | Complex refactors, high-risk decisions | Claude, GPT, Gemini pro tiers, etc. | Higher |

> **No public savings benchmark is linked.** Do not claim fixed percentage reductions.
> If you need enterprise cost proof, measure your own workflows first.

## Philosophy Layer: HYOGOOK V5

HyoDo also includes an optional philosophy-driven scoring model called **HYOGOOK V5**. It evaluates code through six review pillars and uses a geometric mean component so weak dimensions cannot be fully hidden by strong ones.

```text
F = (T + G + In + B + C) + ⁵√(T × G × In × B × C)
S = ⁵√(T × G × In × B × C)
```

| Pillar | Weight | Focus |
|:------:|:------:|:------|
| **Benevolence** | **25%** | Developer experience, user serenity |
| **Truth** | **22%** | Technical accuracy, architecture |
| **Goodness** | **18%** | Security, stability, ethics |
| **Loyalty** | **15%** | SSOT compliance, project context |
| **Beauty** | **15%** | Clean code, UX, documentation |
| **Eternity** | **Geometric** | Harmony and sustainability |

**Range**: F ∈ [6, 60], S ∈ [1, 10]

> Legacy note: WEIGHTED_V1 used an older five-pillar label set. HyoDo v3.1.0 public docs use the HYOGOOK V5 six-pillar model.

## Project Structure

```text
hyodo/              # Public Python package (release surface)
commands/           # Optional agent slash-command adapters
docs/               # Architecture, proof maps, security surface
.github/workflows/  # CI/smoke gates for public package
afo_core/           # Extended/legacy modules (advisory, not public gate)
```

## Documentation

| Document | Purpose |
|----------|---------|
| [QUICK_START_SIMPLE.md](QUICK_START_SIMPLE.md) | 3-minute quick start |
| [docs/PROVIDER_PROOF.md](docs/PROVIDER_PROOF.md) | Model-agnostic proof map |
| [docs/SECURITY_SURFACE.md](docs/SECURITY_SURFACE.md) | Public package vs afo_core security boundary |
| [docs/EXTERNAL_CLAIM_AUDIT.md](docs/EXTERNAL_CLAIM_AUDIT.md) | Measured audit of external market claims |
| [QUICK_START.md](QUICK_START.md) | Detailed guide |
| [install_interactive.sh](install_interactive.sh) | Interactive installer (English, minimal-first) |
| [docker-compose.minimal.yml](docker-compose.minimal.yml) | Optional extended Docker setup |
| [SECURITY.md](SECURITY.md) | Security policy |
| [CHANGELOG.md](CHANGELOG.md) | Release notes |

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

All contributions are evaluated with practical quality gates first. The HYOGOOK V5 score can be used as an additional review signal, but passing tests, security checks, and human review remains required.

## License

MIT License - see [LICENSE](./LICENSE)

## Links

- [Documentation](./docs/)
- [Roadmap](./ROADMAP.md)
- [Changelog](./CHANGELOG.md)
- [Security Policy](./SECURITY.md)

---

<p align="center">
  <em>HyoDo — safer AI-assisted development through visible quality gates.</em>
</p>
