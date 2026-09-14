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

## Derived aggregate namespaces

`harmony_aggregate` is the canonical derived aggregate over six raw virtue
measurements. It is not the Eternity virtue. The 4.19.4 HYOGOOK V5 compatibility
path retains its public `S_eternity` output and its `0 → 1` floor; this is a
historical derived harmony value, not a measured Eternity result.

HyoDo is a host-neutral public layer. Integrating hosts own orchestration,
memory, retrieval, runtime, execution, and final authority. KINGDOM is a
reference consumer and research harness, not part of HyoDo.
