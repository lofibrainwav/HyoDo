# HyoDo demo dry-run

Generated: 2026-07-16T22:08:00Z
Source branch: release/v3.1.5-demo-polish
Source commit: ded6dd6 (pre-commit worktree)
Working tree: dirty
Version: 3.1.5

## hyodo --version
```
HyoDo v3.1.5 - model-agnostic quality gates
```

## hyodo check
```
╭──────────────────────────╮
│ HyoDo Code Quality Check │
╰──────────────────────────╯
Target: .

[1/4] Truth - Type checking...
  PASS 0 errors, 0 warnings

[2/4] Beauty - Lint & Format...
  PASS All checks passed!

[3/4] Goodness - Tests...
  PASS ============================== 10 passed in 0.03s
==============================

[4/4] Eternity - Security seal...
  PASS SBOM script not found; skipped

==================================================
All gates passed
Gates support review readiness. Human approval still required.
```
exit: 0

## hyodo score
```
         HYOGOOK V5 Review Signal
┏━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━┓
┃ Pillar       ┃ Score ┃  Weight ┃  Value ┃
┡━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━┩
│ Benevolence  │    90 │     25% │   0.90 │
│ Truth        │    90 │     22% │   0.90 │
│ Goodness     │    90 │     18% │   0.90 │
│ Loyalty      │    90 │     15% │   0.90 │
│ Beauty       │    90 │     15% │   0.90 │
│              │       │         │        │
│ Eternity (S) │       │ derived │ 9.1000 │
│ F Score      │       │         │  54.60 │
│              │       │         │        │
│ TOTAL        │       │         │  90.0% │
└──────────────┴───────┴─────────┴────────┘

REVIEW_SIGNAL_STRONG (90+)
Strong review signal only. Still run tests/security checks; human approval
required.
```

## hyodo safe (working tree)
```
╭────────────────────────────────────╮
│ HyoDo Safety Check (early warning) │
╰────────────────────────────────────╯
source: git diff HEAD
  ✅ Secrets exposure
  ✅ Dangerous commands
  ⚠️ Production impact
  ✅ Rollback signal

Risk: low (0/100)
-> Low early-warning risk — final approval remains human
Note: early warning only. Not a full SAST/secret-scan/dependency audit.
```

## hyodo safe (secret fixture)
```
╭────────────────────────────────────╮
│ HyoDo Safety Check (early warning) │
╰────────────────────────────────────╯
source: file:/tmp/hyodo-demo-safe.txt
  ❌ Secrets exposure
  ✅ Dangerous commands
  ⚠️ Production impact
  ✅ Rollback signal

Findings
  -  secret/github_token: Possible credential or secret material matched

Risk: high (45/100)
-> Review required — do not proceed without human approval
Note: early warning only. Not a full SAST/secret-scan/dependency audit.
```
exit: 0 (non-zero expected under --strict; default may still print high risk)

## verify-public
```
== HyoDo public verify ==
root: <repo-root>
python: .venv/bin/python (Python 3.14.6)
hyodo: .venv/bin/hyodo
-- version sync --
OK: version 3.1.5 synchronized across all sources
-- ruff --
All checks passed!
6 files already formatted
-- pyright --
0 errors, 0 warnings, 0 informations
-- pytest --
============================= test session starts ==============================
platform darwin -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: <repo-root>
configfile: pyproject.toml
plugins: cov-7.1.0, asyncio-1.4.0, anyio-4.14.2
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 10 items

tests/test_cli_tools.py .....                                            [ 50%]
tests/test_safety.py .....                                               [100%]

============================== 10 passed in 0.03s ==============================
-- shell syntax --
-- package build --
Successfully built hyodo-3.1.5.tar.gz and hyodo-3.1.5-py3-none-any.whl
Checking dist/hyodo-3.1.5-py3-none-any.whl: PASSED
Checking dist/hyodo-3.1.5.tar.gz: PASSED
-- sdist must not ship afo_core --
sdist ok: hyodo-3.1.5.tar.gz (22575 bytes), 18 entries
-- wheel install smoke --
HyoDo v3.1.5 - model-agnostic quality gates
wheel import API ok
-- CLI smoke --
-- claim regression (public surfaces) --
== PASS: public package verify ==
```
