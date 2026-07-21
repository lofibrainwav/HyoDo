# HyoDo philosophy (short)

HyoDo turns AI-assisted changes into an inspectable quality loop. Public
language is English. Scores are **review signals**, not automatic approval.

Philosophy branding is intentional. Every public label pairs with a
**technical meaning** so operators never re-translate under pressure.

## Philosophy version

- **Philosophy:** V6 (Hyo supersedes one-sided Loyalty).
- **Score formula:** optional **HYOGOOK V5** F-score (geometric mean).
- CLI may say “HYOGOOK F-score (philosophy V6)” — formula ≠ philosophy
  version numbers on purpose.

The `loyalty=` alias was removed in 4.0.0. Legacy
`calculate_trinity_score()` stays frozen for historical reproducibility.

## Pillar map

| Pillar | KO / Hanja | Technical meaning | Evidence |
| --- | --- | --- | --- |
| Truth | 진 / 眞 | Type / static correctness | Command gate |
| Goodness | 선 / 善 | Tests + safety stability | Command gate + `safe` |
| Beauty | 미 / 美 | Lint / format | Command gate |
| Benevolence | 인 / 仁 | Public-surface integrity | Native AST |
| Hyo | 효 / 孝 | Consent + data protection | Native AST |
| Yeong | 영 / 永 | Continuity of measurement | history ledger |

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

## Geometric mean = fail-closed gate

Optional `hyodo score` uses a **geometric mean**:

- Arithmetic mean of (structure=1.0, security=0.0) → 0.5 (looks “ok”).
- Geometric mean with any zero axis → **0** (whole signal collapses).

Document this as engineering, not only “harmony”:

> **Fail-closed:** one pillar at 0 fails the whole review signal.

`--partial` allows missing pillars and adds `SIGNAL_CONFIDENCE_WEAK`. It
does not invent `REVIEW_SIGNAL_STRONG` via silent 1.0 fill-in (4.0.1).

## Operating boundaries

1. Human approval remains required for merge/write authority.
2. Public package is `hyodo/` (Python package + CLI).
3. Tiered model routing is design intent only — no cost guarantee.
4. Prefer CLI + CI proof over vendor-locked demos.
5. Keep philosophy names; always pair with technical meaning in UI/docs.

## See also

- [README.md](./README.md)
- [docs/PROVIDER_PROOF.md](./docs/PROVIDER_PROOF.md)
- [docs/EXTERNAL_CLAIM_AUDIT.md](./docs/EXTERNAL_CLAIM_AUDIT.md)
