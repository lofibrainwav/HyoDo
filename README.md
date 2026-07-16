# HyoDo

> **A Claude Code quality gate and cost-aware review kit for AI-assisted developers.**

HyoDo helps developers using Claude Code review, score, and ship AI-assisted code with
a repeatable quality workflow. It provides slash commands, scoring utilities, safety
checks, and CI-friendly gates so AI-generated changes can be inspected before they
become trusted code.

<p align="center">
  <a href="./i18n/ko/README.md">한국어</a> •
  <a href="./i18n/zh/README.md">中文</a> •
  <a href="./i18n/ja/README.md">日本語</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Works_with-Claude_Code-blueviolet" alt="Claude Code">
  <img src="https://img.shields.io/badge/Cost_Aware-Routing-green" alt="Cost-aware routing">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
  <img src="https://img.shields.io/badge/Python-3.10+-blue" alt="Python">
  <img src="https://img.shields.io/badge/Version-3.1.0-success" alt="Version">
</p>

---

## 30-second proof

| Proof point | What to inspect |
|-------------|-----------------|
| Public package | `hyodo/` Python package, `pyproject.toml`, and `hyodo` CLI entrypoint |
| Claude Code workflow | `commands/` slash commands for `/start`, `/check`, `/score`, `/safe`, and `/cost` |
| Quality gates | `.github/workflows/ci.yml` and `.github/workflows/smoke.yml` |
| Safety posture | `SECURITY.md`, `.env.example`, `.env.minimal`, and installer inspection steps |
| Cost discipline | Cost-aware routing language and public claim note below; no guaranteed savings claim |

If you are reviewing HyoDo for a role, partnership, or technical screen, start with
[`QUICK_START_SIMPLE.md`](./QUICK_START_SIMPLE.md) and
[`docs/ANTHROPIC_PROOF.md`](./docs/ANTHROPIC_PROOF.md).

## Who is this for?

HyoDo is for developers and small teams who:

- use Claude Code or AI-assisted coding workflows;
- want a repeatable review checklist before trusting AI-generated changes;
- need fast local checks for linting, typing, tests, and safety;
- want to route simple tasks away from expensive model calls when possible;
- prefer command-driven workflows that can later be connected to CI.

## What problem does it solve?

AI-assisted development is fast, but speed without review creates risk. HyoDo turns review into a simple operating loop:

```text
AI-assisted change
→ /check
→ score + safety review
→ fix or escalate
→ ship with a visible quality trail
```

The goal is not blind automation. The goal is to make AI-assisted work easier to inspect, safer to merge, and cheaper to operate.

## What HyoDo does not claim

- It does **not** replace human code review, tests, or security review.
- It does **not** guarantee a fixed cost-reduction percentage.
- It does **not** auto-approve risky changes just because a score is high.
- It does **not** require the optional philosophy layer to use the practical gates.

## What is included?

- **Claude Code commands** — `/check`, `/score`, `/safe`, `/trinity`, and related workflow helpers.
- **Quality gates** — lint, format, type, test, and security-oriented checks.
- **Scoring utilities** — Python package and CLI helpers for repeatable review scoring.
- **Cost-aware routing** — designed to reduce unnecessary premium-model usage by routing work by risk and complexity.
- **Public package gates** — CI checks for the public `hyodo` package, with extended legacy checks separated as advisory.

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

### Run with Claude Code

```bash
cd ~/.hyodo && claude
/start    # onboarding guide
/check    # quality gate
/score    # scoring utility
/safe     # safety-oriented review
```

## Requirements

### Minimal setup

- Python 3.10+
- Claude Code CLI
- Git

### Full setup

- Python 3.10+
- Claude Code CLI
- Git
- Docker & Docker Compose
- Redis, PostgreSQL, Ollama, or the provided Docker setup

## Configuration

### Minimal configuration

```bash
cp .env.minimal .env
# Set ANTHROPIC_API_KEY in .env
```

### Full configuration

```bash
cp .env.example .env
# Fill in the services you plan to use
```

Keep secrets out of git history. Never commit `.env` files containing real credentials.

## Basic Usage

In Claude Code, use these commands:

```bash
/check          # Run quality gates
/score          # Calculate review score
/safe           # Security and risk scan
/trinity        # Full scoring analysis
```

## Score Interpretation

| F Score | S Score | Status | Suggested Action |
|:-------:|:-------:|:-------|:-----------------|
| **F ≥ 54** | **S ≥ 8** | Excellent | Candidate for approval after human review |
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

## Cost-Aware Routing

HyoDo is designed to avoid sending every task to the most expensive model path.

| Tier | Use Case | Cost Profile |
|------|----------|--------------|
| FREE | Read-only, search, inspection | $0 where available |
| CHEAP | Simple edits, low-risk cleanup | Low |
| EXPENSIVE | Complex refactors, high-risk decisions | Standard |

> Public claim note: earlier internal docs referenced percentage-based cost targets.
> Treat those as selected-workflow observations, not a guaranteed benchmark,
> unless a public benchmark is linked.

## Philosophy Layer: HYOGOOK V5

HyoDo also includes an optional philosophy-driven scoring model called **HYOGOOK V5**. It evaluates code through six review pillars and uses a geometric mean component so weak dimensions cannot be fully hidden by strong ones.

```text
F = (T + G + In + B + C) + ⁵√(T × G × In × B × C)
S = ⁵√(T × G × In × B × C)
```

| Pillar | Hanja | Weight | Focus |
|:------:|:-----:|:------:|:------|
| **Benevolence** | 仁 | **25%** | Developer experience, user serenity |
| **Truth** | 眞 | **22%** | Technical accuracy, architecture |
| **Goodness** | 善 | **18%** | Security, stability, ethics |
| **Loyalty** | 忠 | **15%** | SSOT compliance, project context |
| **Beauty** | 美 | **15%** | Clean code, UX, documentation |
| **Eternity** | 永 | **Geometric** | Harmony and sustainability |

**Range**: F ∈ [6, 60], S ∈ [1, 10]

> Legacy note: WEIGHTED_V1 used 眞/善/美/孝/永. HyoDo v3.1.0 public docs use the HYOGOOK V5 six-pillar model.

## Project Structure

```text
hyodo/
├── commands/       # Claude Code slash commands
├── skills/         # Skill definitions
├── agents/         # AI agent configurations
├── scripts/        # Automation scripts
├── hooks/          # Git hooks
└── afo_core/       # Extended core modules
```

## Documentation

| Document | Purpose |
|----------|---------|
| [QUICK_START_SIMPLE.md](QUICK_START_SIMPLE.md) | 3-minute quick start |
| [QUICK_START.md](QUICK_START.md) | Detailed guide |
| [install_interactive.sh](install_interactive.sh) | Interactive installer |
| [docker-compose.minimal.yml](docker-compose.minimal.yml) | Lightweight Docker setup |
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
