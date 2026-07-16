# External Claim Audit (Measured)

**Date:** 2026-07-16 (PDT)  
**Repo:** `lofibrainwav/HyoDo`  
**Method:** file/CLI/CI/GitHub Dependabot readback (no estimation)  
**Merged baseline:** PR #5 (`0eceb08`) — English-only public surface, real `hyodo safe`, claim alignment

This audit checks external market/strategy claims against repository evidence.

---

## Claim set under review

1. **Market need:** AI speed outruns human review; "speed without review creates risk"; creators need time back from repetitive gates.
2. **Reality check:** high infra friction (Docker/Redis/Postgres); philosophical overhead (HYOGOOK); unproven cost savings.
3. **Strategic pivot:** become a frictionless single-purpose one-command risk gate.

---

## 1) Market need — measured verdict

| External claim | Verdict | Evidence |
|----------------|---------|----------|
| AI generation speed creates review bottleneck | **Supported (product thesis, not market survey)** | README problem statement: "speed without review creates risk"; loop is check/score/safe before trust |
| Need for automated lint/test/safety gates | **Supported by product design** | Public package implements `hyodo check` (pyright/ruff/pytest/SBOM path) + CI workflows |
| Need to free producers from repetitive verification | **Partially supported** | Gates automate checks; human approval still required by design (`does not auto-approve`) |

**Caveat:** This audit does **not** include external user interviews or TAM data. It only verifies that HyoDo's stated problem matches its implemented loop.

---

## 2) Reality check — measured verdict

### 2.1 High infra friction

| External claim | Verdict | Evidence |
|----------------|---------|----------|
| World wants light tools | **Aligned with current public package** | Root deps are only `typer`, `rich` (`pyproject.toml`) |
| Docker/Redis/Postgres required for AI code verification | **Overstated for public path; true for extended path** | README Full setup lists Docker/Redis/Postgres as **optional extended** services; CI installs `pip install -e ".[dev]"` only; smoke installs wheel and runs CLI |
| Installer still surfaces heavy path | **Supported historically; mitigated in this branch** | Old installer UI offered full mode with Redis+Postgres; rewritten installer defaults to **minimal**, labels extended infra optional |

**Measured friction (public path):**

```text
pip install -e ".[dev]"
hyodo check
hyodo safe
```

No Docker required for public package smoke.

**Residual friction:**

- Repo still contains `afo_core/`, Docker files, and Dependabot noise from extended locks.
- Interactive installer historically asked for Anthropic key even when CLI gates do not need it (now optional wording).

### 2.2 Philosophical overhead

| External claim | Verdict | Evidence |
|----------------|---------|----------|
| HYOGOOK V5 is unique but optional learning cost | **Supported** | README presents HYOGOOK under optional philosophy layer; practical gates first |
| Everyday merge users may treat it as luxury | **Plausible; docs partially mitigate** | Score CLI outputs `REVIEW_SIGNAL_*` not auto-approval; still visible as product vocabulary |
| Philosophy leads product face | **Mostly false after public-readiness docs** | README top leads with model-agnostic quality gate; HYOGOOK is below usage |

### 2.3 Unproven cost efficiency

| External claim | Verdict | Evidence |
|----------------|---------|----------|
| Cost-aware routing claimed without guaranteed benchmark | **Supported** | README badge + section exist; explicit "does not guarantee fixed cost-reduction percentage" |
| No public math benchmark | **Supported** | No linked public benchmark file/results found in public docs (search of README/docs) |
| Enterprises lack objective adoption proof for savings | **Supported as gap** | Docs intentionally forbid percentage savings claims without benchmark |

---

## 3) Strategic pivot — measured fit

External recommendation: frictionless single purpose — one terminal command that scores risk of AI-generated code.

| Required attribute | Current measured state | Gap |
|--------------------|------------------------|-----|
| One-command local gate | `hyodo check` works | Good |
| Immediate risk signal | `hyodo safe` now scans patterns (not fixed green) | Good early-warning; not full SAST |
| Minimal deps | `typer`+`rich` public runtime | Good |
| No Docker required | True for public path | Docs must keep extended path clearly secondary |
| No philosophy required | Practical path works without HYOGOOK understanding | Keep philosophy optional |
| Prove cost savings | Not proven publicly | Needs benchmark or drop as primary pitch |
| Repo first impression matches single purpose | Improved (CLI-first README), but monorepo still heavy (`afo_core`, many commands) | Packaging/split or stronger "public vs extended" boundary |

**Verdict:** The pivot is directionally correct and **partially already implemented** in the public package. The remaining blocker is not the CLI core — it is **repo surface weight** (extended tree, Dependabot count, optional philosophy/cost claims) that still dilutes the single-purpose story.

---

## 4) Security number context (related credibility)

| Metric (2026-07-16) | Value |
|---------------------|-------|
| Dependabot open alerts | 310 (pip) |
| Location | 100% under `afo_core/` manifests |
| Public package Dependabot | 0 (thin deps) |
| Code scanning analyses | none configured |
| Secret scanning open | 0 |

External "quality gate is contaminated" narrative is **impression-true** on GitHub Security tab, **technically overstated** for the public install path.

---

## 5) Action implications (product)

Priority order implied by measurements:

1. Keep public path one-liner: `pip install && hyodo check && hyodo safe` — **done in public package**
2. Keep extended infra out of minimal install defaults — **done in installer/docs**
3. Keep HYOGOOK optional and non-blocking — **done**
4. Either publish a cost benchmark or demote "cost-aware" from primary badge — **demoted to tiered-routing intent badge**
5. Reduce `afo_core` Dependabot noise (lock SSOT + patch/remove) so Security tab matches public surface truth — **open track** (see `SECURITY_SURFACE.md`)

---

## 6) Language policy (this branch)

- Public product language: **English only**
- Removed: `i18n/ko`, `i18n/zh`, `i18n/ja`
- Non-English legacy notes replaced or stripped outside `afo_core/`

---

## Source commands used

```bash
# deps
rg -n "dependencies|typer|rich" pyproject.toml
# CI install path
rg -n "pip install|docker|redis" .github/workflows/*.yml
# claims
rg -n "does not|guarantee|Docker|HYOGOOK|Cost" README.md
# CLI
hyodo check
hyodo safe
# Dependabot
gh api graphql -f query='... vulnerabilityAlerts totalCount ...'
```
