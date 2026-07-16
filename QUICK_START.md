# HyoDo 1-Minute Quick Start Guide

> Code quality check + visible review trail = Done.

<p align="center">
  <a href="./i18n/ko/QUICK_START.md">한국어</a> •
  <a href="./i18n/zh/QUICK_START.md">中文</a> •
  <a href="./i18n/ja/QUICK_START.md">日本語</a>
</p>

## 1. Installation (30 seconds)

```bash
git clone https://github.com/lofibrainwav/HyoDo.git
cd HyoDo && ./install.sh
```

## 2. Start Using (30 seconds)

```bash
/start    # Help
/check    # Code quality check
/score    # View score
```

**That's it!** These 3 commands are all you need.

---

## Understanding Scores

| Score | Meaning | Action |
|-------|---------|--------|
| **90+ points** | Safe | Proceed immediately |
| **70-89 points** | Caution | Review before proceeding |
| **Below 70 points** | Risky | Fixes required |

---

## Simple Mode Commands (5 total)

| Command | What it does |
|---------|--------------|
| `/start` | View help |
| `/check` | Code quality check |
| `/score` | View score |
| `/safe` | Safety inspection |
| `/cost "task"` | Cost prediction |

**This is all you need to know.**

---

## Cost Savings

HyoDo is designed to reduce unnecessary premium-model usage by routing work by
risk and complexity. Treat historic percentage claims as internal observations
from selected workflows, not as a guaranteed benchmark.

| Task shape | Suggested path |
|------------|----------------|
| Read-only inspection | Use local search, `/check`, or free/low-cost review first |
| Simple cleanup | Use lower-cost model paths and verify with gates |
| High-risk changes | Escalate to stronger review, tests, and human approval |

---

<details>
<summary><strong>Advanced Features (Advanced Mode)</strong></summary>

### Detailed Analysis Commands

| Command | Purpose |
|---------|---------|
| `/trinity` | Detailed analysis of 5 quality metrics |
| `/strategist` | Analysis from 3 expert perspectives |
| `/ultrawork` | Parallel task execution |
| `/organs` | System status check |

### Philosophical Framework

Quality scores consist of 5 pillars:

| Item | Weight | Meaning |
|------|--------|---------|
| Accuracy | 35% | Is the code correct? |
| Safety | 35% | Are there any issues? |
| Readability | 20% | Is it easy to read? |
| Usability | 8% | Is it easy to use? |
| Sustainability | 2% | Will it last? |

### Expert Analysis (3 Strategists)

| Expert | Perspective | Key Question |
|--------|-------------|--------------|
| Jang Yeong-sil | Technical | "Will this be valid in 3 years?" |
| Yi Sun-sin | Safety | "What's the worst case?" |
| Shin Saimdang | UX | "Is it easy to understand?" |

</details>

---

## Next Steps

- Want to learn more: [README.md](README.md)
- Want a reviewer-facing proof map: [docs/ANTHROPIC_PROOF.md](docs/ANTHROPIC_PROOF.md)
- Want to contribute: [CONTRIBUTING.md](CONTRIBUTING.md)
