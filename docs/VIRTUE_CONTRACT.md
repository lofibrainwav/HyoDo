# Canonical Virtue Contract

HyoDo has exactly six independent virtue axes. The executable source of truth
is [`hyodo/virtues.py`](../hyodo/virtues.py); this document explains the
contract without creating a second list.

| Canonical virtue | Document label | Machine key / compatibility label | Measurement | Score role | Graph role |
|---|---|---|---|---|---|
| Truth | Truth | `truth` / Truth | 眞 / 진; tests, typing, static checks | Independent measured axis | Pillar column |
| Goodness | Good | `goodness` / Goodness | 善 / 선; safety findings and coverage | Independent measured axis | Pillar column |
| Beauty | Beauty | `beauty` / Beauty | 美 / 미; lint, format, clarity evidence | Independent measured axis | Pillar column |
| Benevolence | Humanity | `benevolence` / Benevolence | 仁 / 인; public-surface and onboarding evidence | Independent measured axis | Pillar column |
| Hyo | Hyo | `hyo` / Hyo | 孝 / 효; policy, host-binding, access-ledger evidence | Independent measured axis | Pillar column |
| Eternity / Yeong | Longevity | `eternity` / Eternity | 永 / 영; append-only history and continuity evidence | Independent measured axis | Continuity indicator |

The philosophy-to-engineering definition uses the document labels `Truth`,
`Good`, `Beauty`, `Humanity`, `Hyo`, and `Longevity`. These are presentation
labels, not new axes. Existing machine keys and compatibility labels remain
stable: `goodness`, `benevolence`, and `eternity` are not renamed in this
compatibility-preserving step. The dashboard may still show the audience label
`Filial Piety` for the canonical `Hyo` key.

Every measured virtue reports `OBSERVED`, `PARTIAL`, or `UNOBSERVED`. A virtue
is not evidence; evidence is not a decision; a score or receipt is not
execution authority.

## Score and aggregation boundary

HyoDo does **not** define or emit a canonical aggregate across the six virtue
axes. The `HARMONY_AGGREGATE_KEY` value `harmony_aggregate` in
`hyodo/virtues.py` is a reserved namespace constant, not a formula, measured
axis, graph field, or current CLI output.

The current `hyodo score` and `hyodo score --from-check` paths are legacy
HYOGOOK V5 compatibility behavior. They use five inputs (Benevolence, Truth,
Goodness, Hyo, and Beauty); their derived `S_eternity` / harmony value is not
the independent Eternity virtue and does not represent a six-axis summary.
When `--from-check` cannot observe one or more inputs, it may show a partial
observed-input harmony signal but withholds TOTAL. See
[`SCORE_DERIVATION.md`](SCORE_DERIVATION.md) for the exact behavior.

The philosophy-to-engineering reference defines an evaluation record as
`(value, confidence, evidence, state)` for an individual axis, with missing
evidence reported as `UNOBSERVED`. That axis-evaluation contract is not yet
implemented as a general HyoDo API in the current public package. A host may
define a separately governed, profile-specific summary; HyoDo does not supply
that host-owned aggregation or turn it into action authority.

HyoDo is a host-neutral public layer. Integrating hosts own orchestration,
memory, retrieval, runtime, execution, and final authority. KINGDOM is a
reference consumer and research harness, not part of HyoDo.
