# Security Policy

> "이순신의 거북선처럼 시스템을 수호한다"

## 이순신 (善 Shield) 보안 원칙

HyoDo는 이순신 전략가의 원칙에 따라 보안을 최우선으로 합니다.

### 핵심 질문

> "최악의 경우 무슨 일이 발생하는가?"

모든 보안 결정에서 이 질문을 적용합니다.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 3.1.x   | ✅ |
| 3.0.x   | ✅ |
| 2.0.x   | ⚠️ Limited support |
| 1.0.x   | ❌ |

## Reporting a Vulnerability

### Preferred Reporting Method

1. Use GitHub Private Vulnerability Reporting if available.
2. If unavailable, open a minimal public issue without exploit details.
3. Avoid publishing credentials, tokens, or reproduction payloads publicly.

### Suggested Report Format

```yaml
vulnerability_report:
  title: "[Security] Vulnerability title"
  severity: [CRITICAL/HIGH/MEDIUM/LOW]
  description: "Detailed description"
  reproduction_steps:
    - "Step 1"
    - "Step 2"
  impact: "Affected systems or workflows"
  suggested_fix: "Potential mitigation"
```

## Security Gates (`safety_gate`)

HyoDo uses the `safety_gate` hook to detect and block risky operations.

### CRITICAL Keywords (blocked immediately)

- `rm -rf /`
- `DROP DATABASE`
- `--force --hard`

### HIGH Keywords (manual review recommended)

- `delete`, `drop`
- `production`
- `credential`, `secret`, `password`
- `deploy`, `migration`

## Safe Usage

### DO

- Use the FREE-tier debugging strategists when possible
- Run `/preflight` before commit
- Pass `/check` quality gates before merge
- Keep secrets outside repository history

### DON'T

- Deploy directly to production without review
- Hardcode secrets or credentials
- Merge untested runtime changes

## Disclosure Philosophy

HyoDo prioritizes responsible disclosure and operational serenity.
Security fixes should reduce risk without increasing unnecessary system complexity.

---

*"거북선의 수호: 시스템 안전성 최우선"*
