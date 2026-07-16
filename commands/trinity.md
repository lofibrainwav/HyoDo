---
description: "Compute Trinity / HYOGOOK review signal and decision support"
allowed-tools: Read, Bash(git diff:*), Bash(git status:*), Bash(curl:*)
impact: CRITICAL
tags: [trinity, score, decision, 5pillars]
---

# Trinity score (review signal)

Compute a Trinity / HYOGOOK review signal for `$ARGUMENTS`.

This is decision support only. It is not automatic merge approval.

## Optional MCP integration

If Soul Engine is running:

```bash
curl -s http://localhost:8010/api/trinity/calculate \
  -H "Content-Type: application/json" \
  -d '{"task": "$ARGUMENTS", "context": {}}'
```

## Five-pillar checklist (0-100 each)

### Truth - 35%

- [ ] Is the implementation correct?
- [ ] Does it follow existing patterns?
- [ ] Are types safe?

### Goodness - 35%

- [ ] Are tests present?
- [ ] Does CI pass?
- [ ] Are side effects controlled?

### Beauty - 20%

- [ ] Is the code clean?
- [ ] Does lint pass?
- [ ] Is duplication avoided?

### Serenity / DX - 8%

- [ ] Is UX impact limited?
- [ ] Are error messages clear?
- [ ] Can it run one-shot?

### Eternity - 2%

- [ ] Is it documented?
- [ ] Is evidence recorded?
- [ ] Is rollback possible?

## Decision support

| Condition | Action |
| :--- | :--- |
| **Trinity >= 90 AND Risk <= 10** | **REVIEW_SIGNAL_STRONG** (human approval candidate — not auto-merge) |
| **Trinity >= 75 AND Risk <= 25** | **ASK_HUMAN** (explicit confirmation needed) |
| **Trinity < 70 OR Risk > 30** | **BLOCK** |
| **Secrets/Auth impact detected** | **CRITICAL_BLOCK** |

## Output format

```yaml
trinity_score:
  total: [score]/100
  pillars:
    truth: [score]
    goodness: [score]
    beauty: [score]
    serenity: [score]
    eternity: [score]
  risk_score: [score]/100
  decision: [REVIEW_SIGNAL_STRONG | ASK_HUMAN | BLOCK]  # not auto-merge
```
