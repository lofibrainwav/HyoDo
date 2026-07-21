# HyoDo philosophy (short)

HyoDo turns AI-assisted changes into an inspectable quality loop. Public language
is English. Scores are **review signals**, not automatic approval.

Philosophy branding is intentional. Every public label always pairs with a
**technical meaning** so operators never re-translate under pressure.

## Philosophy version

- **Philosophy:** V6 (Hyo supersedes one-sided Loyalty).
- **Score formula lineage:** HYOGOOK F-score V5 math (geometric mean of inputs).
- CLI titles may say “HYOGOOK F-score (philosophy V6)” — formula ≠ philosophy
  version numbers on purpose.

The `loyalty=` alias (deprecated in 3.3.0) was removed in 4.0.0. The legacy
`calculate_trinity_score()` path is frozen so historical numbers stay
reproducible.

## Pillar map (always keep the parentheses)

| Pillar | Hanja / Korean | English | Technical meaning | Typical evidence |
| --- | --- | --- | --- | --- |
| Truth | 眞 / 진 | Truth | Type / static correctness | Command gates: Pyright, mypy, `tsc`, `go vet`, `cargo check`, … |
| Goodness | 善 / 선 | Goodness | Tests + safety stability | Command gates: pytest / `npm test` / … and `hyodo safe` findings |
| Beauty | 美 / 미 | Beauty | Lint, format, maintainability | Command gates: Ruff, ESLint, formatters, … |
| Benevolence | 仁 / 인 | Benevolence | Structural integrity of the public surface | Native **AST** scan: public docstrings, CLI help, message-less `raise` |
| Hyo | 孝 / 효 | Filial Piety | Consent + data-protection posture | Native **AST** scan: mutating flags default off, outbound imports, non-loopback binds |
| Eternity / Yeong | 永 / 영 | Eternity | Continuity of honest measurement | `.hyodo/history.jsonl` append-only ledger; consecutive all-PASS on **executed** gates only |

### Two measurement kinds

1. **Command gates (Truth / Goodness / Beauty)** — tools the project already
   owns. With HyoDo 4.2+, `hyodo init` absorbs them into `.hyodo/gates.toml`
   (Bring-Your-Own-Gates). They can also come from HyoDo’s own checkout preset.
2. **Native collectors (Benevolence / Hyo / Yeong)** — never replaced by a shell
   command. Unavailable sources render `Not measured`; they are not invented.

## Geometric mean = fail-closed gate

The optional `hyodo score` combines input pillars with a **geometric mean**:

- Arithmetic mean of (structure=1.0, security=0.0) → 0.5 (looks “half fine”).
- Geometric mean with any zero axis → **0** (whole signal collapses).

Document this as an engineering property, not only as “harmony”:

> **Fail-closed:** one pillar at 0 fails the whole review signal.

`--partial` allows missing pillars (defaulted carefully for the math) and adds
`SIGNAL_CONFIDENCE_WEAK`. It does **not** turn weak input into
`REVIEW_SIGNAL_STRONG` by silent 1.0 fill-in (fixed in 4.0.1).

## Operating boundaries

1. Human approval remains required for merge/write authority.
2. Public package is `hyodo/` (Python package + CLI).
3. Tiered model routing is design intent only — no guaranteed cost savings.
4. Prefer CLI + CI proof over vendor-locked demos.
5. Keep philosophy names; always pair them with technical parentheses in UI and
   docs (branding without cognitive tax).

## See also

- [README.md](./README.md) — user-first command path
- [docs/PROVIDER_PROOF.md](./docs/PROVIDER_PROOF.md)
- [docs/EXTERNAL_CLAIM_AUDIT.md](./docs/EXTERNAL_CLAIM_AUDIT.md)
