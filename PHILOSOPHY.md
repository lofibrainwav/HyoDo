# HyoDo philosophy (short)

HyoDo turns AI-assisted changes into an inspectable quality loop. Public language
is English. Scores are **review signals**, not automatic approval.

## HYOGOOK V5 pillars (public scoring)

| Pillar | Focus |
| --- | --- |
| Benevolence | Developer experience and user serenity |
| Truth | Technical accuracy and evidence |
| Goodness | Security and stability |
| Hyo | Reciprocal and voluntary continuity — SSOT discipline |
| Beauty | Clarity and maintainability |
| Eternity | Geometric-mean harmony (derived) |

Philosophy version: **V6**. Hyo (孝) supersedes the earlier one-sided
Loyalty (忠): a reciprocal and voluntary relational discipline. The
`loyalty=` alias (deprecated in 3.3.0) was removed in 4.0.0. The
legacy `calculate_trinity_score()` compatibility path is frozen as-is so
historical scores remain reproducible.

## Operating boundaries

1. Human approval remains required for merge/write authority.
2. Public package is `hyodo/` (Python package + CLI).
3. Tiered model routing is design intent only — no guaranteed cost savings.
4. Prefer CLI + CI proof over vendor-locked demos.

See also [README.md](./README.md),
[docs/PROVIDER_PROOF.md](./docs/PROVIDER_PROOF.md), and
[docs/EXTERNAL_CLAIM_AUDIT.md](./docs/EXTERNAL_CLAIM_AUDIT.md).
