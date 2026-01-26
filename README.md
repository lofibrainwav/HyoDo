# HyoDo (孝道)

> **AI-Powered Code Quality Automation for Claude Code**

<p align="center">
  <a href="./i18n/ko/README.md">한국어</a> •
  <a href="./i18n/zh/README.md">中文</a> •
  <a href="./i18n/ja/README.md">日本語</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Claude_Code-Plugin-blueviolet" alt="Claude Code">
  <img src="https://img.shields.io/badge/Cost_Savings-50--70%25-green" alt="Cost Savings">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

---

## What is HyoDo?

HyoDo is a **Claude Code plugin** that automates code quality checks using the Trinity Score system. It helps you:

- **Catch issues early** — Before they become problems
- **Save AI costs** — 50-70% reduction through intelligent caching
- **Make confident decisions** — Clear pass/fail scoring

---

## Quick Start (30 seconds)

```bash
/start              # Help
/check              # Code quality check
/score              # View score (90+ = safe)
/safe               # Safety inspection
/cost "task desc"   # Cost prediction
```

**That's it!** This is all you need to know.

---

## Trinity Score

HyoDo evaluates your code across three dimensions:

| Dimension | Weight | What It Checks |
|:----------|:------:|:---------------|
| **眞 Truth** | 35% | Type safety, logic correctness, tests passing |
| **善 Goodness** | 35% | Security, stability, error handling |
| **美 Beauty** | 20% | Code style, documentation, readability |

Plus **孝 Serenity (8%)** for developer experience and **永 Eternity (2%)** for maintainability.

### Score Interpretation

| Score | Status | Action |
|:-----:|:------:|:-------|
| 90+ | ✅ Safe | Proceed immediately |
| 70-89 | ⚠️ Caution | Review before proceeding |
| < 70 | ❌ Risky | Fixes required |

---

## Installation

### Option 1: Git Clone
```bash
git clone https://github.com/lofibrainwav/HyoDo.git ~/.hyodo
```

### Option 2: One-Click Install
```bash
curl -sSL https://raw.githubusercontent.com/lofibrainwav/HyoDo/main/install.sh | bash
```

---

## Commands

### Simple Mode (Recommended)

| Command | Description |
|:--------|:------------|
| `/start` | Getting started guide |
| `/check` | Run quality check |
| `/score` | View Trinity Score |
| `/safe` | Security inspection |
| `/cost` | AI cost prediction |

### Advanced Mode

| Command | Description |
|:--------|:------------|
| `/trinity` | Detailed score breakdown |
| `/preflight` | Pre-commit validation |
| `/ultrawork` | Parallel task execution |
| `/evidence` | Audit logging |
| `/rollback` | Undo changes |

---

## How It Works

```
Your Code → HyoDo Analysis → Trinity Score → Decision
                                    │
                         ┌──────────┼──────────┐
                         │          │          │
                      90+: GO    70-89: ASK   <70: STOP
```

HyoDo uses local AI (Ollama) for analysis, keeping your code private and costs low.

---

## Documentation

| Document | Description |
|:---------|:------------|
| [QUICK_START.md](QUICK_START.md) | 5-minute quickstart |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide |
| [ROADMAP.md](ROADMAP.md) | Future plans |

---

## Philosophy

**HyoDo (孝道)** means "The Way of Serenity" — reducing friction in your development workflow.

Inspired by the wisdom of King Sejong's era, HyoDo applies three perspectives to every decision:

- **Jang Yeong-sil** ⚔️ — "Will this work in 3 years?"
- **Yi Sun-sin** 🛡️ — "What's the worst case?"
- **Shin Saimdang** 🌉 — "Can users understand this?"

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT - [LICENSE](LICENSE)

---

<p align="center">
  <em>New here? Start with <code>/start</code>!</em>
</p>
