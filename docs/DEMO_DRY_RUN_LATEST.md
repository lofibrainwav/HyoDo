# HyoDo demo dry-run

Generated: 2026-07-16T21:00:27Z
Branch: fix/hyodo-check-package-mode
Commit: 999fae0
Version: 3.1.3

## hyodo --version
```
HyoDo v3.1.3 - model-agnostic quality gates
```

## hyodo check (repo)
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
  PASS ============================== 10 passed in 0.04s 
==============================

[4/4] Eternity - Security seal...
  PASS SBOM script not found; skipped

==================================================
All gates passed
Gates support review readiness. Human approval still required.
```

## hyodo check (package mode empty cwd)
```
╭──────────────────────────╮
│ HyoDo Code Quality Check │
╰──────────────────────────╯
Target: .

[1/4] Truth - Type checking...
  PASS package mode; typecheck skipped

[2/4] Beauty - Lint & Format...
  PASS package mode; lint skipped

[3/4] Goodness - Tests...
  PASS No repository test suite found; package smoke checks only

[4/4] Eternity - Security seal...
  PASS No repository checkout found; SBOM skipped in package mode

==================================================
All gates passed
Gates support review readiness. Human approval still required.
```

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
Candidate for approval after tests, security checks, and human review.
```
