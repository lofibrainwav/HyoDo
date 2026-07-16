# Demo Ready Checklist

Use this before recording the 3-minute HyoDo demo.

## Preconditions (measured)

- [x] On `main` (or latest release tag), clean worktree
- [x] `bash scripts/verify-public.sh` exits 0
- [x] `hyodo check` prints **All gates passed** and exits 0
- [x] No public claim language that implies automatic merge authority
- [x] Dependabot open alerts reviewed (target: 0 open, or only dismissed no-patch residuals)
- [x] Demo script aligned with current VERSION messaging (`docs/DEMO_SCRIPT_3_MIN.md`)

## Demo path (keep on public surface)

1. Show README top: model-agnostic quality gate, CLI+CI first
2. Terminal:

```bash
hyodo --version
hyodo check
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --loyalty 0.9
hyodo safe
printf 'token = ghp_abcdefghijklmnopqrstuvwxyz012345\n' > /tmp/hyodo-demo-safe.txt
hyodo safe /tmp/hyodo-demo-safe.txt
```

3. Open `.github/workflows/smoke.yml` or CI green history for the release tag
4. State boundaries:
   - scores are review signals, not auto-approval
   - `afo_core` is advisory extended tree, not the public package
   - no guaranteed cost-savings benchmark

## Do not show

- Real `.env` secrets
- afo_core Docker/Redis unless asked
- Dependabot historical 310 without current open count
- Claude-only docs as the first frame (`ANTHROPIC_PROOF` is optional appendix)

## Dry-run receipt

After local dry-run, refresh:

```bash
bash scripts/demo-dry-run.sh
```

Output lands in `docs/DEMO_DRY_RUN_LATEST.md` (generated, safe to re-run).

## Script SSOT

- `docs/DEMO_SCRIPT_3_MIN.md`
- `docs/PROVIDER_PROOF.md`
- `docs/EXTERNAL_CLAIM_AUDIT.md`
- `docs/SECURITY_SURFACE.md`
