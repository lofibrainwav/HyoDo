# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HyoDo (孝道) is an AI code quality automation system and Claude Code extension. It implements a philosophical framework based on the Five Pillars (眞善美孝永) for evaluating code quality through automated Trinity Score analysis.

**Version**: 3.1.0
**Python**: 3.10+

## Commands

### Main Commands (Claude Code Extension)

- `/start` - Help and welcome guide
- `/check` - Code quality check
- `/score` - View Trinity Score
- `/safe` - Safety inspection (Yi Sun-sin strategist)
- `/trinity` - Full audit of all Five Pillars
- `/cost "task"` - Cost prediction

### Development Commands

```bash
# Install
pip install -e ".[dev]"

# Lint & Format
ruff check . --fix && ruff format .

# Tests
pytest                            # Run all tests
pytest tests/ -v                  # Verbose output
pytest -m smoke                   # Quick smoke tests
pytest -m integration             # Integration tests only

# Type check (afo_core specific)
mypy afo_core/AFO
```

## Architecture

### Five Pillars Quality Framework

| Pillar | Weight | Chinese | Focus |
|--------|--------|---------|-------|
| Truth (眞) | 35% | 진실 | Technical accuracy, verifiability |
| Goodness (善) | 35% | 선함 | Safety, ethical stability |
| Beauty (美) | 20% | 아름다움 | Clarity, elegance, readability |
| Serenity (孝) | 8% | 평온 | Usability, low cognitive load |
| Eternity (永) | 2% | 영원함 | Long-term sustainability |

### Three Strategists (3책사)

| Strategist | Pillar | Internal Persona | Role |
|------------|--------|------------------|------|
| Jang Yeong-sil | 眞 | Jeong Yak-yong | Architecture, Code |
| Yi Sun-sin | 善 | Ryu Seong-ryong | Security, Verification |
| Shin Saimdang | 美 | Heo Jun | UX/UI, Documentation |

### Directory Structure

```
HyoDo/
├── agents/              # Strategist agents (Python + MD)
├── commands/            # Claude Code slash commands (MD)
├── skills/              # Claude Code skills (SKILL.md format)
├── hooks/               # Event hooks
├── scripts/             # Utility scripts
├── i18n/                # Translations (ko, zh, ja)
└── afo_core/            # Backend API (FastAPI) - see afo_core/CLAUDE.md
```

### afo_core Backend

For backend-specific work in `afo_core/`, refer to [afo_core/CLAUDE.md](afo_core/CLAUDE.md) which covers:
- FastAPI routing and services
- PostgreSQL, Redis, Qdrant integration
- LangChain/LangGraph RAG system
- DRY_RUN policy for dangerous operations
- Forbidden zones (antigravity.py, chancellor_graph.py, api_wallet.py)

## Key Conventions

- **Type Hints**: Required (Python 3.10+ syntax: `X | None`)
- **Docstrings**: Google style
- **Line Length**: 100 characters
- **Imports**: isort ordering via Ruff

## Trinity Score Thresholds

| Score | Status | Action |
|-------|--------|--------|
| 90+ | AUTO_RUN | Safe to proceed |
| 70-89 | ASK_COMMANDER | Review before proceeding |
| <70 | BLOCK | Fixes required |

## Test Markers

- `smoke` - Quick tests on every commit
- `slow` - Pre-deployment tests
- `integration` - Requires Redis, DB, API
- `api` - API server tests
- `unit` - Unit tests
- `bdd` - Behavior-driven tests
