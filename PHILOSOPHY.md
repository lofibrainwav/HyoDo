# HyoDo philosophy (short)

HyoDo turns AI-assisted changes into an inspectable quality loop. Public
language is English. Scores are **review signals**, not automatic approval.

Philosophy branding is intentional. Every public label pairs with a
**technical meaning** so operators never re-translate under pressure.

## Philosophy version

- **Philosophy:** V6 (Hyo supersedes one-sided Loyalty).
- **Legacy CLI display name:** HyoDo Integrity Score.
- **Legacy command labels:** Six-Virtue Model; Trinity Gates subset.
- **Current implementation status:** the score command retains an older
  five-input geometric-mean method for compatibility. The replacement
  per-axis evaluator is not yet implemented as a general public API.
- **HYOGOOK V5** is the internal name for that older method, not a separate
  philosophy or HyoDo's current score direction.

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
| Beauty | 미 / 美 | Clarity | Lint and format |
| Benevolence | 인 / 仁 | Public usability | API and onboarding |
| Hyo | 효 / 孝 | Consent and data protection | Policy and access ledger |
| Eternity / Yeong | 영 / 永 | Continuity and persistence | History ledger |

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

## Evaluation and legacy compatibility

HyoDo does not turn its six reference virtues directly into one canonical
score. The reference model keeps an evaluation's value, confidence, evidence,
context, and observation state distinct; the current public package does not
yet implement a general per-axis evaluator. Missing evidence remains
`UNOBSERVED`; it is not converted into a numeric zero or one.

The current command still accepts five inputs and combines them with a
geometric mean. It floors a zero input for historical compatibility and
scales the result to its legacy score range. `HYOGOOK V5` is simply the
internal name for this older calculation; its `S_eternity` is not the
`Eternity` virtue.

The older formula uses a **geometric mean**:

- A geometric mean makes all five inputs matter; a low input pulls the result
  down more than an arithmetic mean would.
- This legacy calculation floors a zero input to `1` on its `1–10` scale, so
  its historical score does not represent an observed zero faithfully.

Those mechanics describe only the legacy five-input method. They do not define
HyoDo's current evaluation model.

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
