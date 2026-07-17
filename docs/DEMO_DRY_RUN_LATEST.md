# HyoDo demo dry-run

Generated: 2026-07-17T00:31:24Z
Source branch: docs/hyodo-3.1.6-docs-sync
Source commit: 3789af7 (docs update worktree; base = origin/main Truth Patch)
Working tree: dirty (docs WIP at generation)
Version: 3.1.6
PyPI live (measured): 3.1.6

## hyodo --version
```
HyoDo v3.1.6 - model-agnostic quality gates
```

## hyodo check (HyoDo checkout)
```
╭──────────────────────────╮
│ HyoDo Code Quality Check │
╰──────────────────────────╯
Target: <repo-root>
HyoDo checkout: <repo-root>

[1/4] Truth - Type checking...
  PASS 0 errors, 0 warnings

[2/4] Beauty - Lint & Format...
  PASS All checks passed!

[3/4] Goodness - Tests...
  PASS ============================== 28 passed in 0.10s
==============================

[4/4] Eternity - Security seal...
  SKIP SBOM script not found; not executed

==================================================
All executed gates passed
Gates support review readiness. Human approval still required.
```
exit: 0

## hyodo score
```
             HYOGOOK V5 Review Signal
┏━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Pillar       ┃ Score ┃ Review emphasis ┃  Value ┃
┡━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Benevolence  │    90 │  25% (not in F) │   0.90 │
│ Truth        │    90 │  22% (not in F) │   0.90 │
│ Goodness     │    90 │  18% (not in F) │   0.90 │
│ Loyalty      │    90 │  15% (not in F) │   0.90 │
│ Beauty       │    90 │  15% (not in F) │   0.90 │
│              │       │                 │        │
│ Eternity (S) │       │  geometric mean │ 9.1000 │
│ F Score      │       │         sum + S │  54.60 │
│              │       │                 │        │
│ TOTAL        │       │                 │  90.0% │
└──────────────┴───────┴─────────────────┴────────┘
Review emphasis is not used in the F formula (F = sum(1–10 pillars) + geometric
mean).

REVIEW_SIGNAL_STRONG (90+)
Strong review signal only. Still run tests/security checks; human approval
required.
```

## hyodo safe (secret fixture)
```
╭────────────────────────────────────╮
│ HyoDo Safety Check (early warning) │
╰────────────────────────────────────╯
source: file:/tmp/hr-sec.txt
  ❌ Secrets exposure
  ✅ Dangerous commands
  ⚠️ Production impact
  ✅ Rollback signal

Findings
  -  secret/github_token: Possible credential or secret material matched

Risk: high (45/100)
-> Review required — do not proceed without human approval
Note: early warning only. Not a full SAST/secret-scan/dependency audit.
Directory scan cap: 40 files; default corpus is git diff/status when no path.
```
exit: 0

## hyodo safe --strict (secret fixture)
```
╭────────────────────────────────────╮
│ HyoDo Safety Check (early warning) │
╰────────────────────────────────────╯
source: file:/tmp/hr-sec.txt
  ❌ Secrets exposure
  ✅ Dangerous commands
  ✅ Production impact
  ✅ Rollback signal

Findings
  -  secret/github_token: Possible credential or secret material matched

Risk: high (45/100)
-> Review required — do not proceed without human approval
Note: early warning only. Not a full SAST/secret-scan/dependency audit.
Directory scan cap: 40 files; default corpus is git diff/status when no path.
```
exit: 1

## hyodo check (empty non-HyoDo tree)
```
╭──────────────────────────╮
│ HyoDo Code Quality Check │
╰──────────────────────────╯
Target: /private/var/folders/mp/7m5m295d1jb17rnk1j9761xh0000gn/T/tmp.ueOZVvBWnm
Not a HyoDo package checkout (requires pyproject.toml + hyodo/ at project root).
Model-agnostic ≠ language-agnostic. General Python project gates are not claimed
in this version.

[1/4] Truth - Type checking...
  UNSUPPORTED not a HyoDo checkout; typecheck not executed

[2/4] Beauty - Lint & Format...
  UNSUPPORTED not a HyoDo checkout; lint not executed

[3/4] Goodness - Tests...
  UNSUPPORTED not a HyoDo checkout; tests not executed

[4/4] Eternity - Security seal...
  UNSUPPORTED not a HyoDo checkout; SBOM not executed

==================================================
No project gates were executed
This is not a validation pass.
```
exit: 2

## Notes

- Receipt is CLI surface evidence for docs sync; full release gate remains `bash scripts/verify-public.sh`.
- Trust live terminal over this header if re-recording later.
- Public install: `pip install -U 'hyodo==3.1.6'`.
