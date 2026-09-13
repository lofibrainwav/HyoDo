# HyoDo philosophy (short)

HyoDo turns AI-assisted changes into an inspectable quality loop. Public
language is English. Scores are **review signals**, not automatic approval.

Philosophy branding is intentional. Every public label pairs with a
**technical meaning** so operators never re-translate under pressure.

## Philosophy version

- **Philosophy:** V6 (Hyo supersedes one-sided Loyalty).
- **Public name:** HyoDo Integrity Score.
- **Model:** Six-Virtue Model.
- **Subset:** Trinity Gates.
- **Formula lineage:** HYOGOOK V5 (geometric mean).
- Formula lineage and philosophy version are separate identifiers on purpose.

The `loyalty=` alias was removed in 4.0.0. Legacy
`calculate_trinity_score()` stays frozen for historical reproducibility.

The canonical six-virtue contract is defined in
[`hyodo/virtues.py`](./hyodo/virtues.py). The six virtues are independent
measurement axes; a computed aggregate is not a virtue.

## Pillar map

| Pillar | KO / Hanja | Technical meaning | Evidence |
| --- | --- | --- | --- |
| Truth | 진 / 眞 | Technical correctness | Tests, typing, static checks |
| Goodness | 선 / 善 | Safety and stability | Safety findings and coverage |
| Beauty | 미 / 美 | Clarity and maintainability | Lint, format, clarity evidence |
| Benevolence | 인 / 仁 | Public and developer usability | Public-surface and onboarding evidence |
| Hyo | 효 / 孝 | Consent, context alignment, and data protection | Policy, host-binding, access-ledger evidence |
| Eternity / Yeong | 영 / 永 | Continuity, persistence, and longitudinal evidence | Append-only history and continuity evidence |

### Two measurement kinds

1. **Command gates (Truth / Goodness / Beauty)** — tools the project
   already owns. With 4.2+, `hyodo init` absorbs them into
   `.hyodo/gates.toml` (Bring-Your-Own-Gates).
2. **Native collectors (Benevolence / Hyo / Yeong)** — never replaced by
   a shell command. Unavailable → `Not measured`.

AST (Benevolence / Hyo) covers public docstrings, CLI help, message-less
`raise`, mutating flags defaulting off, outbound imports, and non-loopback
binds. Yeong uses append-only `.hyodo/history.jsonl` and counts all-PASS
on **executed** gates only (skips never fake green).

## Aggregation and legacy compatibility

The canonical six-virtue aggregate uses raw 0–1 virtue measurements. A measured
zero makes `harmony_aggregate` zero. Missing measurements remain
`UNOBSERVED` and are not silently converted to zero or one.

The public HYOGOOK V5 compatibility formula remains frozen. It scales raw
values from `0 → 1` and `1 → 10`, and its returned `S_eternity` is a legacy
derived harmony value, not the `Eternity` virtue.

The legacy formula uses a **geometric mean**:

- Arithmetic mean of (structure=1.0, security=0.0) → 0.5 (looks “ok”).
- In the canonical aggregate, any measured zero axis → **0**.
- In HYOGOOK V5, the `0 → 1` floor remains for compatibility.

Document this as engineering, not only “harmony”:

> **Canonical fail-closed:** one measured virtue at 0 collapses the
> `harmony_aggregate`; this statement does not describe HYOGOOK V5.

`--partial` allows missing pillars and adds `SIGNAL_CONFIDENCE_WEAK`. It
does not invent `REVIEW_SIGNAL_STRONG` via silent 1.0 fill-in (4.0.1).

## Operating boundaries

1. Human approval remains required for merge/write authority.
2. Public package is `hyodo/` (Python package + CLI).
3. Tiered model routing is design intent only — no cost guarantee.
4. Prefer CLI + CI proof over vendor-locked demos.
5. Keep philosophy names; always pair with technical meaning in UI/docs.

HyoDo is a public, host-neutral evidence and policy lens. The integrating host
or harness owns orchestration, memory, retrieval, runtime, execution, and final
authority. HyoDo receipts and scores never grant execution authority.

## See also

- [README.md](./README.md)
- [docs/PROVIDER_PROOF.md](./docs/PROVIDER_PROOF.md)
- [docs/EXTERNAL_CLAIM_AUDIT.md](./docs/EXTERNAL_CLAIM_AUDIT.md)
