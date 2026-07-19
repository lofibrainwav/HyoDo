# `hyodo safe` rules

`hyodo safe` is an early-warning pattern scan, not a full SAST / secret-scan /
dependency audit. This document lists every rule it currently checks
(`hyodo/safety.py`) and its known limits. If a rule is not listed here, `safe`
does not check for it.

## Rule families

### Secrets exposure — `high` (`SECRET_PATTERNS`, `hyodo/safety.py:16-27`)

| Label | Matches |
|---|---|
| `aws_access_key` | `AKIA` + 16 uppercase/digit chars |
| `github_token` | `gh[pousr]_...` (20+ chars) |
| `slack_token` | `xox[baprs]-...` |
| `private_key_block` | `-----BEGIN [RSA/EC/OPENSSH] PRIVATE KEY-----` |
| `generic_api_key_assignment` | `api_key` / `secret_key` / `access_token` / `password` assigned a quoted string of 8+ chars (`key = "..."` or `key: "..."`) |

### Dangerous commands — `high` (`DANGEROUS_COMMAND_PATTERNS`, `hyodo/safety.py:29-41`)

| Label | Matches |
|---|---|
| `rm_rf_root` | `rm -rf` (or `--force`) targeting an absolute (`/...`) or home (`~...`) path |
| `git_reset_hard` | `git reset --hard` |
| `git_push_force` | `git push ... --force` |
| `drop_database` | `DROP DATABASE` / `DROP SCHEMA` |
| `drop_table` | `DROP TABLE` |
| `chmod_777` | `chmod [-R] 777` |

### Production impact — `medium` (`PRODUCTION_IMPACT_PATTERNS`, `hyodo/safety.py:43-51`)

| Label | Matches |
|---|---|
| `migration` | `alembic`, `django.db.migrations`, `flyway`, `liquibase` |
| `production_env` | `NODE_ENV` / `ENV` / `ENVIRONMENT` set to `prod`/`production` |
| `deploy_keyword` | `kubectl apply`, `terraform apply`, `helm upgrade` |
| `schema_change` | `ALTER TABLE`, `CREATE TABLE`, `DROP COLUMN` |

A fourth signal, **rollback hint** (`info` if present, `low` if absent), notes
whether the scanned text mentions `alembic`, `migration(s)`, `rollback`, or
`revert` — it is informational only and never raises risk by itself.

## Scoring

Each `high` finding adds 40 to the risk score, each `medium` adds 15, each
`low` adds 5, capped at 100. `risk_score >= 31` is `high` (review required),
`>= 11` is `caution`, otherwise `low`. See `hyodo/safety.py:219-292`.

## Honest limits

- **Directory scans cap at 40 files** (`hyodo/safety.py:97-123`), read in
  sorted path order; files beyond the cap are not scanned. Files under `.git`
  and common binary/asset suffixes (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`,
  `.pdf`, `.zip`, `.gz`, `.whl`, `.so`, `.dylib`) are skipped.
- **Default corpus (no `PATH` argument)** is `git diff HEAD`; if that is empty,
  it falls back to `git status --porcelain` text. It is never the full working
  tree contents (`hyodo/safety.py:126-151`).
- **Relative destructive paths are not matched.** `rm -rf ./build` or
  `rm -rf build/` is intentionally *not* flagged — only targets rooted at `/`
  or `~` match `rm_rf_root`, to limit false positives on ordinary build-clean
  commands.
- **Generic assignment matching can false-positive on fixtures.** Any
  `api_key = "........"`-shaped literal (8+ chars) trips
  `generic_api_key_assignment`, including test fixtures, mocks, and
  placeholder/example values — it is a pattern match, not a validity check.
- This is a lightweight, narrow-by-design pattern scan. It does not replace a
  secret scanner, SAST, dependency audit, or human security review.
