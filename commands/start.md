---
description: "[Simple] HyoDo onboarding guide for first-time users"
allowed-tools: Read
impact: LOW
tags: [simple, help, beginner, onboarding]
mode: simple
---

# /start - HyoDo quick start

HyoDo is a model-agnostic quality gate and cost-aware review kit for AI-assisted
developers. It helps you inspect AI-generated changes before you trust them
(CLI first; optional slash-command adapters).

Start practical. Philosophy and advanced scoring are optional layers after the
basic review loop works.

## Core commands

| Command | Purpose | Example |
| :--- | :--- | :--- |
| `/check` | Code quality gates | `/check` |
| `/score` | Review score signal | `/score` |
| `/safe` | Safety early-warning | `/safe` |
| `/cost` | Cost estimate | `/cost "task"` |
| `/start` | This help | `/start` |

## 30-second quick start

```bash
1. hyodo check     # quality gates (or /check)
2. hyodo score     # review signal only (or /score)
3. hyodo safe      # safety early warning (or /safe)
4. fix or escalate — human approval still required
```

## Score system

```text
F >= 54 and S >= 8  -> strong candidate after human review
F >= 45 and S >= 7  -> review recommended
F < 45              -> fix before merge
```

## Go deeper

| Level | Commands | Notes |
| :--- | :--- | :--- |
| Beginner | `/check`, `/score`, `/safe` | Core loop |
| Intermediate | `/trinity`, `/strategist` | Deeper review |
| Advanced | `/chancellor-v3`, `/ultrawork` | Full system |

## What HyoDo is

- **Code quality** gates for AI-assisted changes
- **Cost-aware routing** to avoid unnecessary premium-model usage
- **Safety review** before risky changes are trusted

Scores support review. They do not replace tests, security review, or human
judgment. Start with `/check`.

---

*Advanced: `/trinity`, `/strategist`, `/organs`, `/ultrawork`*
