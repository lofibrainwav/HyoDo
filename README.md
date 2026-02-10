# HyoDo (孝道) — AFO Kingdom's Guardian

> **Automated Code Quality for AI-Assisted Development**
> 
> *"Where Eastern Philosophy Meets Modern Software Engineering"*

<p align="center">
  <img src="https://img.shields.io/badge/Version-3.1.0-success" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python">
  <img.shields.io/badge/Trinity_Score-94.16-brightgreen" alt="Trinity Score">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
  <img src="https://img.shields.io/badge/Security-Patched-success" alt="Security">
</p>

<p align="center">
  <a href="./i18n/ko/README.md">한국어</a> •
  <a href="./i18n/zh/README.md">中文</a> •
  <a href="./i18n/ja/README.md">日本語</a>
</p>

---

## 🎯 Executive Summary

HyoDo is the **entry point** to the AFO Kingdom ecosystem—a philosophy-driven AI development framework that evaluates code through the lens of ancient wisdom. Built as a Claude Code extension, HyoDo brings the power of the **Trinity Score** to every developer's fingertips.

Unlike traditional linters that only check syntax, HyoDo evaluates your code against five philosophical pillars, ensuring not just working code, but **wise code**.

### Key Metrics
- **Cost Reduction**: 50-70% savings on AI API costs
- **Quality Gate**: 4-stage automated validation
- **Philosophy Engine**: 44 principles from 2,000 years of wisdom
- **Security**: Zero critical vulnerabilities (continuously patched)

---

## 🏛️ The Five Pillars (眞善美孝永)

Every decision in HyoDo is governed by the **Trinity Score**—a weighted evaluation system derived from Confucian and strategic philosophy:

| Pillar | Hanja | Weight | Focus | Question |
|:------:|:-----:|:------:|:------|:---------|
| **Truth** | 眞 | 35% | Technical accuracy, type safety, evidence-based decisions | *"Will this work in 3 years?"* |
| **Goodness** | 善 | 35% | Security, stability, risk assessment, ethics | *"What's the worst case?"* |
| **Beauty** | 美 | 20% | Code clarity, documentation, UX, cognitive load | *"Can humans understand this?"* |
| **Serenity** | 孝 | 8% | Developer experience, frictionless workflows | *"Is this effortless?"* |
| **Eternity** | 永 | 2% | Long-term maintainability, knowledge preservation | *"Will this survive us?"* |

### Trinity Score Formula
```
Score = 0.35×眞 + 0.35×善 + 0.20×美 + 0.08×孝 + 0.02×永
```

### Decision Matrix

| Trinity Score | Risk Score | Action | Description |
|:-------------:|:----------:|:-------|:------------|
| ≥ 90 | ≤ 10 | **AUTO_RUN** | Proceed automatically—code meets royal standards |
| 70-89 | ≤ 10 | **ASK_COMMANDER** | Request approval—review recommended |
| < 70 | any | **BLOCK** | Changes required—fixes mandatory |

---

## ⚔️ The Three Strategists (3책사)

HyoDo implements parallel strategist analysis through the **Chancellor Orchestrator**, inspired by King Sejong's court:

```
                    ┌─────────────────────────────┐
                    │   👑 Chancellor (승상)      │
                    │   Decision Orchestrator     │
                    └──────────────┬──────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
    ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
    │ 眞 Jang     │        │ 善 Yi       │        │ 美 Shin     │
    │ Yeong-sil   │        │ Sun-sin     │        │ Saimdang    │
    │ ⚔️ Spear    │        │ 🛡️ Shield   │        │ 🌉 Bridge   │
    │ (35%)       │        │ (35%)       │        │ (20%)       │
    └─────────────┘        └─────────────┘        └─────────────┘
```

| Strategist | Symbol | Persona | Role | Internal Engine |
|:-----------|:------:|:--------|:-----|:----------------|
| **Jang Yeong-sil** | ⚔️ | Jeong Yak-yong | Architecture, technical strategy | qwen2.5-coder |
| **Yi Sun-sin** | 🛡️ | Ryu Seong-ryong | Security, risk assessment, ethics | deepseek-r1 |
| **Shin Saimdang** | 🌉 | Heo Jun | UX, documentation, clarity | qwen3-vl |

Each strategist operates in parallel, providing independent analysis that is synthesized into the final Trinity Score.

---

## 🏗️ Architecture

### The 11 Organs (十一臟六腑)

HyoDo connects to the AFO Kingdom's distributed organ system:

| Organ | Hanja | Service | Port | Role |
|:------|:-----:|:--------|:----:|:-----|
| Heart | 心 | Redis | 6379 | Session, cache, pub/sub |
| Liver | 肝 | PostgreSQL | 15432 | Persistent data storage |
| Brain | 腦 | Soul Engine | 8010 | Main FastAPI API |
| Tongue | 舌 | Ollama | 11434 | Local LLM (Qwen3-VL + Gemma) |
| Lungs | 肺 | LanceDB | — | Vector embeddings |
| Eyes | 眼 | Dashboard | 3000 | Next.js 16 monitoring UI |
| Kidney | 腎 | MCP | — | External tool connections |

### Core Components

```
HyoDo/
├── commands/          # 19 Claude Code slash commands
│   ├── /start         # Welcome guide
│   ├── /check         # 4-Gate CI validation
│   ├── /score         # Trinity Score calculation
│   ├── /safe          # Security scan (Yi Sun-sin)
│   ├── /trinity       # Full pillar audit
│   └── /cost          # AI cost estimation
├── skills/            # 4 skill categories
│   ├── trinity-score-calculator/
│   ├── strategy-engine/
│   ├── philosophy-guide/
│   └── kingdom-navigator/
├── agents/            # 3 Strategist configurations
└── afo_core/          # Backend API (FastAPI)
```

---

## 📜 Philosophy in Code: The Royal Library

HyoDo encodes **44 principles** from classical texts into software engineering practices:

### I. The Art of War (손자병법) — 13 Principles
> **Truth (眞) 70% / Serenity (孝) 30%**

1. **Know Thyself (지피지기)**: Query Context7/database before any action—hallucination prevention
2. **Win Without Fighting (상병벌모)**: Import existing libraries over writing new code
3. **DRY_RUN First (병자궤도야)**: Show simulation results before dangerous operations
4. **Speed is Value (병귀신속)**: Async/Celery for slow operations
5. **Five Factors (도천지장법)**: Align goals, environment, resources, leadership, method
6. **Regular & Irregular (정병)**: Standard patterns first, then customization
7. **Profiling (허실)**: Find bottlenecks through measurement
8. **Exception Handling (구변)**: Graceful degradation paths
9. **Observability (용간)**: Logs and monitoring as intelligence
10. **Destructive Actions (화공)**: Confirm dangerous operations with gates
11. **Ship Fast (졸속)**: MVP over perfect delay
12. **True Automation (부전이굴)**: Zero user friction
13. **Infrastructure != Code (도구와 대상의 분리)**: Docker status doesn't affect quality scores

### II. Romance of Three Kingdoms (삼국지) — 15 Principles
> **Eternity (永) 60% / Goodness (善) 40%**

14. **Loose Coupling (도원결의)**: Modules united by shared goals, not tight binding
15. **Three Retries (삼고초려)**: `Retry(max=3, backoff=exponential)` for external APIs
16. **Graceful Degradation (공성계)**: Fallback UI even when broken
17. **Borrow Arrows (초선차전)**: Leverage open source effectively
18. **Chain Strategy (연환계)**: Microservices linked into powerful pipelines
19. **Beauty Trap (미인계)**: Complex logic behind beautiful UI
20. **Iterate (칠종칠금)**: Write → Critique → Refine loop
21. **Doubt the Instrument (측정 도구의 의심)**: Verify measurement code before blaming services
22. **Environment Contracts (환경변수의 계약)**: Defensive parsing of HOST variables
23. **Optional Means N/A**: Exclude optional services from scoring (not zero)
24. **Timing (동남풍)**: Scheduler utilization

*[See full 44 principles in AFO_ROYAL_LIBRARY.md]*

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Claude Code CLI
- Git

### Installation

```bash
# Interactive installation (recommended)
curl -sSL https://raw.githubusercontent.com/lofibrainwav/HyoDo/main/install_interactive.sh | bash

# Or manual installation
git clone https://github.com/lofibrainwav/HyoDo.git ~/.hyodo
cd ~/.hyodo && ./install.sh
```

### Configuration

```bash
# Copy environment template
cp .env.minimal .env

# Edit with your API keys
nano .env
```

### Basic Usage

In Claude Code, use these commands:

```bash
/start              # Welcome guide and help
/check              # Run 4-Gate CI quality check
/score              # Calculate Trinity Score
/safe               # Security and risk scan
/trinity "analyze"  # Full pillar audit
/cost "feature"     # Estimate AI cost
```

---

## 🛡️ Security: Zero Tolerance Policy

### Current Status: ✅ All Critical Vulnerabilities Patched

| CVE | Package | Severity | Status |
|:----|:--------|:---------|:-------|
| CVE-2026-25528 | langsmith | Medium | ✅ Patched (0.6.3) |
| CVE-2026-24688 | pypdf | Medium | ✅ Patched (6.6.2) |
| CVE-2026-24486 | python-multipart | High | ✅ Patched (0.0.22) |
| CVE-2026-0994 | protobuf | High | ✅ Patched (5.29.6) |
| CVE-2026-21441 | urllib3 | High | ✅ Patched (2.6.3) |

### Security Scanning

```bash
# Run security audit
pip-audit --desc --format=table

# Check for new vulnerabilities
safety check
```

### Security Principles

1. **Never commit secrets**: Pre-commit hooks automatically detect API keys
2. **PII Redaction**: All logs mask sensitive information
3. **Sandboxed Execution**: MCP tools run in isolated environments
4. **Dependency Pinning**: All packages pinned with SHA256 hashes

See [SECURITY_PATCHES.md](SECURITY_PATCHES.md) for detailed vulnerability history.

---

## 🧪 Quality Gates: 4-Gate CI Protocol

Every change runs through the CI Lock Protocol:

```bash
make check    # Run all 4 gates
```

| Gate | Pillar | Tool | Purpose |
|:-----|:------:|:-----|:--------|
| **Gate 1** | 眞 | Pyright | Type checking, regression detection |
| **Gate 2** | 美 | Ruff | Linting, formatting (line-length: 100) |
| **Gate 3** | 善 | pytest | Unit tests (316+ tests) |
| **Gate 4** | 永 | SBOM | Security seal, dependency audit |

### Test Markers

```bash
pytest -m smoke         # Quick smoke tests
pytest -m integration   # Integration tests
pytest -m slow          # Pre-deployment tests
pytest --cov=hyodo      # Coverage report
```

---

## 📊 Evolution Timeline

| Phase | Date | Milestone |
|:------|:-----|:----------|
| **Genesis** | Dec 2024 | Visual Creator awakening |
| **Awakening** | Dec 2025 | Trinity Philosophy installed (v1.0) |
| **Harmony** | Dec 2025 | 11 Organs + Dashboard + CPA (v2.0) |
| **Expansion** | Dec 2025 | Self-expanding mode activated (v2.5) |
| **Metacognition** | Feb 2026 | Phase 106: "Doubt the Instrument" (v3.0) |
| **Royal Library** | Feb 2026 | Phase 111: 44 Principles codified (v3.1) |

*[See full evolution in AFO_EVOLUTION_LOG.md]*

---

## 🌍 AFO Kingdom Ecosystem

HyoDo is the **beginner's entry point** to the larger AFO Kingdom:

| Component | Description | Tech Stack |
|:----------|:------------|:-----------|
| **HyoDo** | CLI plugin for Claude Code | Python, Typer |
| **afo-core** | Backend API, Chancellor Graph | FastAPI, LangGraph |
| **dashboard** | Real-time monitoring UI | Next.js 16, React 19 |
| **trinity-os** | Philosophy engine, RAG | LanceDB, Ollama |

---

## 🤝 Contributing

### Quality Requirements

1. **All changes must pass 4-Gate CI**
2. **Trinity Score ≥ 70 required** for merge
3. **Evidence required**: Cite file paths, test outputs, or existing patterns
4. **No drive-by refactoring**: Keep diffs minimal

### Commit Convention

```
<type>(<scope>): <subject>

<body>

- Trinity Score: <score>
- Risk Score: <risk>
- 4-Gate CI: <status>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `security`

### Decision Labels

- 🟢 **AUTO_RUN**: Trinity ≥ 90, Risk ≤ 10
- 🟡 **ASK_COMMANDER**: Trinity 70-89
- 🔴 **BLOCK**: Trinity < 70

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

---

## 📚 Documentation

| Document | Purpose |
|:---------|:--------|
| [QUICK_START_SIMPLE.md](QUICK_START_SIMPLE.md) | 3-minute quickstart guide |
| [QUICK_START.md](QUICK_START.md) | Detailed setup instructions |
| [AGENTS.md](AGENTS.md) | AI agent governance rules |
| [SECURITY_PATCHES.md](SECURITY_PATCHES.md) | Vulnerability tracking |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [PHILOSOPHY.md](PHILOSOPHY.md) | Five Pillars deep dive |

---

## 📄 License

MIT License — See [LICENSE](LICENSE)

---

<p align="center">
  <em>"One Truth, One System, One Kingdom"</em><br>
  <strong>하나의 진리, 하나의 시스템, 하나의 왕국</strong><br><br>
  <em>Built with the Spirit of King Sejong</em><br>
  <strong>세종대왕의 정신으로</strong>
</p>
