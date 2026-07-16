# HyoDo demo dry-run

Generated: 2026-07-16T21:17:11Z
Branch: fix/hyodo-pre-demo-clutter-purge
Commit: b4f25c9 (pre-commit working tree)
Version: 3.1.4

## hyodo --version
```
HyoDo v3.1.4 - model-agnostic quality gates
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
  PASS ============================== 10 passed in 0.04s 
==============================

[4/4] Eternity - Security seal...
  PASS SBOM script not found; skipped

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
Strong review signal only. Still run tests/security checks; human approval required.
```

## hyodo safe
```
╭────────────────────────────────────╮
│ HyoDo Safety Check (early warning) │
╰────────────────────────────────────╯
source: git diff HEAD
  ✅ Secrets exposure
  ✅ Dangerous commands
  ⚠️ Production impact
  ✅ Rollback signal

Risk: low (5/100)
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

Note: Full `bash scripts/verify-public.sh` is the release gate; this receipt is CLI surface only.
