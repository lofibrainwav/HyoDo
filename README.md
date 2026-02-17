# HyoDo (孝道)

> **Automated Code Review for AI-Assisted Development**
> **HYOGOOK V5 (五德憲章) — Phase 127+**
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
  <img src="https://img.shields.io/badge/Version-3.1.0-success" alt="Version">
</p>

---

## 🚀 What's New in v3.1.0

- **🎯 대화형 설치**: `install_interactive.sh` - 초보자용 5단계 설치
- **⚡ 최소 설치 모드**: Docker 없이 2분 완료
- **📦 경량 Docker**: `docker-compose.minimal.yml` - Redis + PostgreSQL만
- **📚 간편 가이드**: `QUICK_START_SIMPLE.md` - 3분 퀵스타트

---

## What is HyoDo?

HyoDo is a **code quality automation system** designed for AI-assisted development workflows. It integrates with [Claude Code](https://claude.ai/code) to provide:

- **Trinity Score** - 6-pillar philosophy-based code evaluation (HYOGOOK V5)
- **Automated Quality Gates** - CI/CD integration with smart routing
- **Cost-Aware Routing** - Reduce AI API costs by 40-70%
- **Multi-Agent Collaboration** - Parallel strategist analysis

## The Six Pillars (仁眞善忠美永)

HyoDo evaluates code through six philosophical pillars using **HYOGOOK V5 (五德憲章)**:

```
F = (T + G + In + B + C) + ⁵√(T × G × In × B × C)
S = ⁵√(T × G × In × B × C)  # Geometric Mean (永)
```

| Pillar | Hanja | Weight | Role | Focus |
|:------:|:-----:|:------:|:-----|:------|
| **仁** | Benevolence | **25%** | Chancellors | Developer experience, user serenity |
| **眞** | Truth | **22%** | Jang Yeong-sil | Technical accuracy, architecture |
| **善** | Goodness | **18%** | Yi Sun-sin | Security, stability, ethics |
| **忠** | Loyalty | **15%** | Kim Yu-sin | SSOT compliance, cultural continuity |
| **美** | Beauty | **15%** | Shin Saimdang | Clean code, UX, documentation |
| **永** | Eternity | **Geometric** | System | Harmony & sustainability |

**Range**: F ∈ [6, 60], S ∈ [1, 10]

> **Note**: Legacy WEIGHTED_V1 (Phase ≤126) used: 眞18%, 善18%, 美12%, 孝40%, 永12%.

## Quick Start (3분 완료)

### ⚡ 초보자용 설치 (추천)

```bash
# 대화형 설치 (5단계, 3분)
curl -sSL https://raw.githubusercontent.com/lofibrainwav/HyoDo/main/install_interactive.sh | bash

# Claude Code에서 실행
cd ~/.hyodo && claude
/start    # 시작 가이드
```

### 📦 수동 설치

```bash
# Clone the repository
git clone https://github.com/lofibrainwav/HyoDo.git
cd HyoDo

# Install (creates Claude Code skills)
./install.sh
```

### 🐳 Docker 설치 (전체 기능)

```bash
# 최소 설치 (Redis + PostgreSQL)
docker-compose -f docker-compose.minimal.yml up -d

# 전체 설치 (모든 11장기)
docker-compose up -d
```

### Basic Usage

In Claude Code, use these commands:

```bash
/check          # Run 4-Gate CI quality check
/score          # Calculate Trinity Score
/safe           # Security and risk scan
/trinity        # Full Trinity analysis
```

### Score Interpretation (HYOGOOK V5)

| F Score | S Score | Status | Action |
|:-------:|:-------:|:-------|:-------|
| **F ≥ 54** | **S ≥ 8** | Excellent | `AUTO_RUN` — Auto-approve |
| **F ≥ 45** | **S ≥ 7** | Good | `ASK_COMMANDER` — Review recommended |
| **F < 45** | — | Needs Work | `BLOCK` — Improvements required |

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
├── commands/       # Claude Code slash commands (19개 스킬)
├── skills/         # Skill definitions (4개 카테고리)
├── agents/         # AI agent configurations (3책사)
├── scripts/        # Automation scripts
├── hooks/          # Git hooks
└── afo_core/       # Core library
```

## Requirements

### 최소 설치 (추천)
- Python 3.10+
- Claude Code CLI
- Git

### 전체 설치
- Python 3.10+
- Claude Code CLI
- Git
- Docker & Docker Compose
- Redis, PostgreSQL, Ollama (또는 Docker로 실행)

## Configuration

### 최소 설정 (.env.minimal)
```bash
cp .env.minimal .env
# ANTHROPIC_API_KEY만 설정하면 OK
```

### 전체 설정 (.env.example)
```bash
cp .env.example .env
# 12개 변수 설정 (Ollama, Redis, PostgreSQL 등)
```

## Documentation

| 문서 | 설명 |
|------|------|
| [QUICK_START_SIMPLE.md](QUICK_START_SIMPLE.md) | 🚀 3분 퀵스타트 |
| [QUICK_START.md](QUICK_START.md) | 📚 상세 가이드 |
| [install_interactive.sh](install_interactive.sh) | 🎯 대화형 설치 |
| [docker-compose.minimal.yml](docker-compose.minimal.yml) | ⚡ 경량 Docker |

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

All contributions are evaluated using the Six Pillars. A Trinity Score of F ≥ 45 AND S ≥ 7 is required for PRs (HYOGOOK V5).

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
