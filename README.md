# HyoDo (孝道)

> **Automated Code Review for AI-Assisted Development**
> Built Where Philosophy Breathes Through Code

<p align="center">
  <a href="./i18n/ko/README.md">한국어</a> •
  <a href="./i18n/zh/README.md">中文</a> •
  <a href="./i18n/ja/README.md">日本語</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Works_with-Claude_Code-blueviolet" alt="Claude Code">
  <img src="https://img.shields.io/badge/Saves-50--70%25_AI_Costs-green" alt="Cost Savings">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
  <img src="https://img.shields.io/badge/Python-3.10+-blue" alt="Python">
</p>

---

## What is HyoDo?

HyoDo is a **code quality automation system** designed for AI-assisted development workflows. It integrates with [Claude Code](https://claude.ai/code) to provide:

- **Trinity Score** - 5-pillar philosophy-based code evaluation
- **Automated Quality Gates** - CI/CD integration with smart routing
- **Cost-Aware Routing** - Reduce AI API costs by 40-70%
- **Multi-Agent Collaboration** - Parallel strategist analysis

## The Five Pillars (眞善美孝永)

HyoDo evaluates code through five philosophical pillars:

| Pillar | Weight | Focus |
|--------|--------|-------|
| **眞 (Truth)** | 35% | Technical accuracy, type safety, test coverage |
| **善 (Goodness)** | 35% | Security, stability, error handling |
| **美 (Beauty)** | 20% | Code clarity, documentation, UX |
| **孝 (Serenity)** | 8% | Maintainability, low cognitive load |
| **永 (Eternity)** | 2% | Long-term sustainability |

**Trinity Score Formula:**
```
Score = 0.35×眞 + 0.35×善 + 0.20×美 + 0.08×孝 + 0.02×永
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/lofibrainwav/HyoDo.git
cd HyoDo

# Install (creates Claude Code skills)
./install.sh
```

### Basic Usage

In Claude Code, use these commands:

```bash
/check          # Run 4-Gate CI quality check
/score          # Calculate Trinity Score
/safe           # Security and risk scan
/trinity        # Full Trinity analysis
```

### Score Interpretation

| Score | Status | Action |
|-------|--------|--------|
| **90+** | Excellent | Auto-approve eligible |
| **70-89** | Good | Review recommended |
| **50-69** | Needs Work | Improvements required |
| **<50** | Critical | Block until fixed |

## Features

### 4-Gate CI Protocol

```
Gate 1: Pyright (眞 Truth) → Type checking
Gate 2: Ruff (美 Beauty) → Lint + format
Gate 3: pytest (善 Goodness) → Test coverage
Gate 4: SBOM (永 Eternity) → Security seal
```

### Three Strategists

HyoDo uses three AI strategists for balanced analysis:

- **Jang Yeong-sil (장영실)** - Technical architecture (眞)
- **Yi Sun-sin (이순신)** - Security & stability (善)
- **Shin Saimdang (신사임당)** - UX & clarity (美)

### Cost-Aware Routing

Automatically routes tasks to appropriate tiers:

| Tier | Use Case | Cost |
|------|----------|------|
| FREE | Read-only, search | $0 |
| CHEAP | Simple edits | Low |
| EXPENSIVE | Complex refactors | Standard |

## Project Structure

```
hyodo/
├── commands/       # Claude Code slash commands
├── skills/         # Skill definitions
├── agents/         # AI agent configurations
├── scripts/        # Automation scripts
├── hooks/          # Git hooks
└── afo_core/       # Core library
```

## Requirements

- Python 3.10+
- Claude Code CLI
- Git

## Configuration

Create `.env` from the example:

```bash
cp .env.example .env
```

Key settings:
- `TRINITY_THRESHOLD=90` - Auto-approve threshold
- `RISK_THRESHOLD=10` - Max acceptable risk

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

All contributions are evaluated using the Five Pillars. A Trinity Score >= 70 is required for PRs.

## License

MIT License - see [LICENSE](./LICENSE)

## Links

- [Documentation](./docs/)
- [Roadmap](./ROADMAP.md)
- [Changelog](./CHANGELOG.md)
- [Security Policy](./SECURITY.md)

---

<p align="center">
  <em>"孝道 (HyoDo) - The Way of Devotion"</em><br>
  Built with the Spirit of King Sejong
</p>
