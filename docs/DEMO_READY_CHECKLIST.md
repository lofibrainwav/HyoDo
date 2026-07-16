# Demo Ready Checklist

Use this before recording the 3-minute HyoDo demo.

## Preconditions (measured)

- [ ] On `main`, clean worktree
- [ ] `bash scripts/verify-public.sh` exits 0
- [ ] No public claim language: AUTO_RUN / Auto-approve
- [ ] Dependabot open alerts reviewed (target: 0 open, or only dismissed no-patch residuals)

## Demo path (keep on public surface)

1. Show README top: model-agnostic quality gate, CLI+CI first
2. Terminal:

```bash
pip install -e ".[dev]"
hyodo check
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --loyalty 0.9
hyodo safe
```

3. Open `.github/workflows/smoke.yml` or CI green badge
4. State boundaries:
   - scores are review signals, not auto-approval
   - `afo_core` is advisory extended tree, not the public package
   - no guaranteed cost-savings benchmark

## Do not show

- Real `.env` secrets
- afo_core Docker/Redis unless asked
- Dependabot historical 310 without current number

## Script SSOT

- `docs/DEMO_SCRIPT_3_MIN.md`
- `docs/PROVIDER_PROOF.md`
- `docs/EXTERNAL_CLAIM_AUDIT.md`
- `docs/SECURITY_SURFACE.md`
