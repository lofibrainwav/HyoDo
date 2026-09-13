# Canonical Virtue Contract

HyoDo has exactly six independent virtue axes. The executable source of truth
is [`hyodo/virtues.py`](../hyodo/virtues.py); this document explains the
contract without creating a second list.

| Canonical virtue | Label | Measurement | Score role | Graph role |
|---|---|---|---|---|
| Truth | 眞 / 진 | Tests, typing, static checks | Independent measured axis | Pillar column |
| Goodness | 善 / 선 | Safety findings and coverage | Independent measured axis | Pillar column |
| Beauty | 美 / 미 | Lint, format, clarity evidence | Independent measured axis | Pillar column |
| Benevolence | 仁 / 인 | Public-surface and onboarding evidence | Independent measured axis | Pillar column |
| Hyo | 孝 / 효 | Policy, host-binding, access-ledger evidence | Independent measured axis | Pillar column |
| Eternity / Yeong | 永 / 영 | Append-only history and continuity evidence | Independent measured axis | Continuity indicator |

Presentation aliases must not create new axes: the dashboard may show the
English display phrase `Filial Piety` for the canonical `Hyo` key, while
contracts and machine fields use `hyo` / `Hyo`.

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
