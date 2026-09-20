# Security Policy

HyoDo is a developer workflow tool for AI-assisted code review. Security reports should be handled carefully and should not expose credentials, exploit payloads, or private operational details in public threads.

## Security surface (read this first)

| Surface | Path | Release gate |
|---------|------|--------------|
| Public product | `hyodo/`, root `pyproject.toml` | Yes — CI smoke + truth/goodness gates |

The public install path is intentionally thin (`typer`, `rich`). Details:
[`docs/SECURITY_SURFACE.md`](docs/SECURITY_SURFACE.md).

## Supply chain / PyPI publish

Public package upload uses **PyPI Trusted Publishing (OIDC)** only — see
[`docs/PYPI_TRUSTED_PUBLISHING.md`](docs/PYPI_TRUSTED_PUBLISHING.md).

- No long-lived PyPI API token in GitHub repository secrets for the supported path
- Publish runs only from annotated tags matching `VERSION`, via `.github/workflows/publish.yml`
- GitHub Environment `pypi` is the approval surface
- Post-publish verification requires non-null provenance on wheel and sdist when
  `--require-provenance` is used

## Core Security Question

For every risky operation, HyoDo asks:

> What is the worst realistic outcome if this action is wrong?

This keeps destructive actions, credential exposure, deployment risk, and unsafe automation visible before they are trusted.

## Supported Versions

The current public release is HyoDo **4.20.0**. Security fixes target the
current `4.20.x` release line. Older release lines must be upgraded before a
security report can be reproduced against a supported artifact.

| Version | Supported |
|---------|-----------|
| 4.20.x  | ✅ Current release line |
| < 4.20  | ❌ Upgrade required |

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

HyoDo's `safety_gate` and `hyodo safe` scan for risky-operation patterns and
report findings. They do not execute, authorize, block, or escalate an
operation. A caller or CI system may use the result to enforce a stop or
request review.

### High-risk patterns (reported; caller/CI enforcement)

- `rm -rf` against absolute or home-directory targets
- `git reset --hard`
- `git push ... --force`
- `DROP DATABASE` or `DROP SCHEMA`
- `DROP TABLE`
- `chmod 777`

By default, `hyodo safe` prints findings and exits `0`. With
`hyodo safe --strict`, a high-severity finding returns a non-zero exit code;
the caller or CI decides whether that result blocks further action.

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
- Run `hyodo safe` before commits.
- Pass `hyodo check` quality gates before merge.
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
