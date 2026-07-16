# Security Policy

HyoDo is a developer workflow tool for AI-assisted code review. Security reports should be handled carefully and should not expose credentials, exploit payloads, or private operational details in public threads.

## Security surface (read this first)

| Surface | Path | Release gate |
|---------|------|--------------|
| Public product | `hyodo/`, root `pyproject.toml` | Yes — CI smoke + truth/goodness gates |
| Extended / legacy | `afo_core/` | Advisory — not a public package release blocker |

GitHub Dependabot counts on `afo_core` lockfiles can be large even when the public
install path stays thin. Details: [`docs/SECURITY_SURFACE.md`](docs/SECURITY_SURFACE.md).

Historical patch notes: [`SECURITY_PATCHES.md`](SECURITY_PATCHES.md) (may be stale;
Dependabot is the live inventory for extended deps).

## Core Security Question

For every risky operation, HyoDo asks:

> What is the worst realistic outcome if this action is wrong?

This keeps destructive actions, credential exposure, deployment risk, and unsafe automation visible before they are trusted.

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
2. If private reporting is unavailable, open a minimal public issue without exploit details.
3. Do not publish credentials, tokens, real `.env` contents, or weaponized reproduction payloads publicly.

### Suggested Report Format

```yaml
vulnerability_report:
  title: "[Security] Vulnerability title"
  severity: [CRITICAL/HIGH/MEDIUM/LOW]
  description: "High-level description without secrets"
  reproduction_steps:
    - "Step 1"
    - "Step 2"
  impact: "Affected systems or workflows"
  suggested_fix: "Potential mitigation"
```

## Security Gates (`safety_gate`)

HyoDo uses the `safety_gate` hook to detect and block or escalate risky operations.

### CRITICAL Keywords (blocked immediately)

- `rm -rf /`
- `DROP DATABASE`
- `--force --hard`

### HIGH Keywords (manual review recommended)

- `delete`, `drop`
- `production`
- `credential`, `secret`, `password`
- `deploy`, `migration`

Keyword checks and `hyodo safe` are not a complete security scanner. They are early warning signals that should be combined with human review, tests, CI, Dependabot/pip-audit, and secret-scanning practices.

Scores never automatically approve risky changes.

## Safe Usage

### DO

- Inspect install scripts before running them in a sensitive environment.
- Use low-cost or read-only workflows when possible.
- Run `/preflight` before commits.
- Pass `/check` quality gates before merge.
- Keep secrets outside repository history.
- Rotate exposed keys immediately if a credential is accidentally committed.

### DON'T

- Deploy directly to production without review.
- Hardcode secrets or credentials.
- Paste real `.env` files into issues, prompts, screenshots, or logs.
- Merge untested runtime changes.
- Treat HyoDo scoring as a replacement for security review.

## Disclosure Philosophy

HyoDo prioritizes responsible disclosure and practical risk reduction. Security fixes should reduce real risk without adding unnecessary complexity.

---

Security goal: make risky AI-assisted changes visible before they become trusted code.
