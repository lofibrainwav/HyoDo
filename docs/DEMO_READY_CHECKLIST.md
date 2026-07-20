# Demo Ready Checklist

Use this **only after** the product surface is clean. Recording is the **final**
step when everything works — not a progress ritual mid-cleanup.

## Preconditions (measured)

- [ ] On `main` (or latest release tag `v4.0.0+`), clean worktree
- [ ] `bash scripts/verify-public.sh` exits 0
- [ ] Inside HyoDo checkout: `hyodo check` prints **All executed gates passed** and exits 0
- [ ] Empty dir: `hyodo check /tmp/empty` exits **2** (not a false green)
- [ ] Secret fixture: `hyodo safe --strict` exits **1**; default `hyodo safe` exits 0
- [ ] No public claim language that implies automatic merge authority
- [ ] Dependabot open alerts reviewed (target: 0 open, or only dismissed no-patch residuals)
- [ ] Demo script aligned with current VERSION messaging (`docs/DEMO_SCRIPT_3_MIN.md`)
- [ ] Live PyPI version measured if you will mention pip (`curl` / `pip index versions hyodo`)

## Demo path (keep on public surface)

1. Show README top: model-agnostic quality gate, CLI+CI first, PyPI version badge if live
2. Terminal:

```bash
hyodo --version
hyodo check
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --hyo 0.9
hyodo safe
printf 'token = ghp_abcdefghijklmnopqrstuvwxyz012345\n' > /tmp/hyodo-demo-safe.txt
hyodo safe /tmp/hyodo-demo-safe.txt
hyodo safe --strict /tmp/hyodo-demo-safe.txt   # expect exit 1
```

3. Optional honesty beat (10s): empty dir `hyodo check` → exit 2, not a validation pass
4. Open `.github/workflows/smoke.yml` or CI green history for the release tag
5. State boundaries:
   - scores are review signals, not auto-approval
   - `check` is HyoDo-checkout release gates, not language-agnostic universal CI
   - no guaranteed cost-savings benchmark

## Do not show

- Real `.env` secrets
- Dependabot historical 310 without current open count
- Claude-only docs as the first frame (`ANTHROPIC_PROOF` is optional appendix)
- Stale dry-run receipt headers as live truth (use live terminal)

## Dry-run receipt

After local dry-run, refresh:

```bash
bash scripts/demo-dry-run.sh
```

Output lands in ignored `docs/DEMO_DRY_RUN_LATEST.md`. Regenerate it before
every demo; it is local evidence, not a tracked release claim.

## Script SSOT

- `docs/DEMO_SCRIPT_3_MIN.md`
- `docs/PROVIDER_PROOF.md`
- `docs/EXTERNAL_CLAIM_AUDIT.md`
- `docs/SECURITY_SURFACE.md`
