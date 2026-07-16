---
description: "[Simple] Show a quality review score signal"
allowed-tools: Read, Glob, Grep, Bash(hyodo:*)
impact: LOW
tags: [simple, score, beginner]
mode: simple
alias: trinity
---

# /score - quality review signal

Shows a **review signal** for the current change. (Advanced: `/trinity`)

Scores support decisions. A high score does **not** mean automatic approval of risky changes.

## Usage

Agent slash command:

```text
/score
/score "change summary"
```

Vendor-neutral CLI:

```bash
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --loyalty 0.9
```

## Score hints (beginner table)

| Item | Weight | Meaning |
| :--- | :--- | :--- |
| Accuracy | 35% | Is the code correct? |
| Safety | 35% | Is it free of obvious risk? |
| Readability | 20% | Is it easy to read? |
| Convenience | 8% | Is it easy to use? |
| Durability | 2% | Will it hold over time? |

The public CLI HYOGOOK V5 path computes F/S from Benevolence/Truth/Goodness/Loyalty/Beauty inputs. The table above is a beginner-facing hint only.

## Example output

```text
Quality score: 92/100 (North Star Balance: OPTIMAL)

[Truth] Accuracy: 95
[Goodness] Safety: 90
[Beauty] Readability: 88
[Serenity] Convenience: 92
[Eternity] Durability: 90

-> REVIEW_SIGNAL_STRONG (90+)
-> Human final approval, tests, and security review still required
```

## Score -> action

| Score | State | Next action |
| :--- | :--- | :--- |
| 90+ | Strong review signal | Candidate after tests/security/human checks |
| 70-89 | Caution | Review, then proceed |
| <70 | Risk | Fix before merge |

**Disallowed claim:** score-only auto-run, auto-merge, or auto-deploy.

---

*For deeper analysis use `/trinity` or `/strategist`.*
