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
| `generic_api_key_assignment` | `api_key` / `secret_key` / `access_token` / `password` assigned a quoted string of 8+ chars (`key = "..."` or `key: "..."`), except for a small set of conventional placeholders |

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

The level depends on coverage as well as the score:

- Coverage `UNOBSERVED` (nothing scanned, a missing path, or a scan that could
  not read every file): a score that would be `low` is reported as level
  `unobserved` instead, because the absence of findings in content that was not
  read is not low risk. Findings in the files that were read can still raise
  the level to `caution` or `high`.
- Coverage `PARTIAL` (a capped scan): the level comes from the score as usual,
  so it can be `low`. That `low` covers only the observed files; the verdict
  line reports `PARTIAL`, not `PASS`.
- Coverage `FULL`: the level comes from the score.

The level never changes the exit code. The exit codes are:

- `2` when the target is missing, or when any selected file could not be read
  (including a file over the size cap), in every mode: the scan is incomplete.
  Findings in the files that were read are still shown.
- Otherwise, default mode exits `0` whatever the findings (early warning),
  including a `PARTIAL` or empty (`UNOBSERVED`) corpus.
- Otherwise, `--strict` exits `2` when coverage is not `FULL` (even with `high`
  findings), else `1` on a `high` finding, else `0`.

## Honest limits

- **Directory scans cap at 40 files** (`hyodo/safety.py:97-123`, override with
  `--max-files`), read in sorted path order; files beyond the cap are not
  scanned. Files under `.git` and common binary/asset suffixes (`.png`,
  `.jpg`, `.jpeg`, `.gif`, `.webp`, `.pdf`, `.zip`, `.gz`, `.whl`, `.so`,
  `.dylib`) are skipped. `hyodo safe` discloses coverage, not just the
  configured cap: it reports how many scannable files were actually read
  against how many exist (e.g. `scanned 40 of 45 files`), so partial
  coverage is never silent.
- **Default corpus (no `PATH` argument)** is `git diff HEAD`; if that is empty,
  it falls back to `git status --porcelain` text. It is never the full working
  tree contents (`hyodo/safety.py:126-151`).
- **Relative destructive paths are not matched.** `rm -rf ./build` or
  `rm -rf build/` is intentionally *not* flagged — only targets rooted at `/`
  or `~` match `rm_rf_root`, to limit false positives on ordinary build-clean
  commands.
- **Generic assignment matching can false-positive on fixtures.** An
  `api_key = "........"`-shaped literal (8+ chars) generally trips
  `generic_api_key_assignment`, including test fixtures and mocks. The scanner
  suppresses only conventional values that are unambiguously placeholders:
  selected forms beginning with `example`, `placeholder`, or `dummy` and a
  known field suffix, plus `changeme`, `replace_me`, and `your_<name>_here`.
  Values such as `test-token-1234` remain findings because a synthetic-looking
  value can still be usable in a real environment. This is still a pattern
  match, not a validity check.
- This is a lightweight, narrow-by-design pattern scan. It does not replace a
  secret scanner, SAST, dependency audit, or human security review.
