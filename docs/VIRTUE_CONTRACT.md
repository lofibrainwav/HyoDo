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

## Scope, proxy, and authority contract

Each axis keeps its philosophical scope separate from the evidence HyoDo can
currently measure. A proxy is a bounded observation surface, not the virtue
itself. Every axis also carries an explicit coverage limitation and the same
authority boundary: review signal only; never execution authority.

| Canonical virtue | Philosophical scope | Current measurable proxy | Coverage limitation |
|---|---|---|---|
| Truth | Truthful technical claims and correct representation of system behavior | Tests, typing, and static checks | Selected implementation properties only; not truth in every context |
| Goodness | Reduce preventable harm while preserving necessary safeguards | Safety findings and coverage | Does not measure all downstream harm or risk |
| Beauty | Coherence, clarity, and form that make work easier to understand and maintain | Lint, format, and clarity evidence | Does not establish usability for every audience |
| Benevolence / 仁 | Other-awareness, relationship awareness, and sensitivity to participant, role, and context | Public usability, API/onboarding clarity, and user-facing failure visibility | Does not fully measure relationships, other-awareness, or participant experience |
| Hyo / 孝 | Technology carries its share of the burden; respect choice, consent, context, and protective friction | Consent, context alignment, privacy/data protection, and observed friction or intervention signals | Does not measure total human cost; no calibrated friction score is defined |
| Eternity / 永 | Preserve continuity and learn responsibly across time | Append-only history and continuity evidence | Records do not prove long-term value by themselves |

The 仁 relationship/participant scope is therefore larger than the current
public-surface proxy:

```text
MeasuredProxy_仁 ⊂ Scope_仁
```

Likewise, consent, context alignment, privacy, and friction observations are
current Hyo proxies, not a complete measurement of human burden:

```text
MeasuredProxy_孝 ⊂ Scope_孝
```

Observation state remains separate from both scope and proxy: each measured
axis reports `OBSERVED`, `PARTIAL`, or `UNOBSERVED`. HyoDo does not convert a
proxy into a virtue judgment, merge it into authority, or use it to authorize
an action in an integrating host.

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
evidence reported as `UNOBSERVED`. HyoDo supplies the evidence and state half
of that record and never the value: the per-lens receipt is
[`hyodo.lens-evidence/v1`](../schemas/lens-evidence-v1.schema.json), which
carries the lens, subject, state, proxy coverage, provenance, evidence
references, residuals, and observation time, and rejects any score, value,
weight, aggregate, decision, or authority field. A per-axis value, a judge,
weights, floors, and any profile-specific summary belong to the integrating
host, which should record its judgment separately and bind it to the evidence
receipt by digest. HyoDo does not supply that host-owned judgment or turn it
into action authority.

`hyodo/score_derive.py` is frozen legacy compatibility for
`hyodo score --from-check`. It is kept, not extended: new consumers use the
lens-evidence receipt instead, and `tests/test_lens_boundary.py` pins its
importers.

## Deterministic results and host judgment

The line between HyoDo and a host is whether a result needs a value judgment.
A deterministic result of a declared rule belongs to HyoDo: a gate's
fail-closed `PASS`/`FAIL`, "0 high-severity findings in the observed scope",
a policy rule's `ALLOW`/`DENY`/`ASK`/`UNOBSERVED`, or a lens's `PARTIAL`
coverage. A virtue score, a contextual weight, a minimum floor, a six-axis
aggregate, routing, and execution authority belong to the host.

Observing a lens's declared proxies in full is proxy coverage, not virtue
coverage. A `truth` receipt with every proxy observed still means only that
the selected implementation properties were checked.

## Eternity and time

Time and sequence are the coordinate system; Eternity is what can be observed
about continuity along them: whether the record is contiguous, where it
breaks, how much was not observed, and whether its origin is trustworthy.
HyoDo's ledgers carry a local sequence number that never goes backwards and
record each break as a gap with a reason (`hyodo/ledger_origin.py`), so an
unobserved stretch is stated rather than left as silence. The continuity
receipt reports both per ledger.

## Candidate proxy extensions (not canonical)

The following proxies are candidates for the existing 仁 and 孝 scopes. They
extend what may be measured inside each scope; they do not replace the scope,
the current proxies, or the coverage limitations in `hyodo/virtues.py`, and
they are not measured by any shipped command. Each is promoted into the
canonical contract only after a canary shows it can be observed
deterministically.

| Virtue | Existing scope (unchanged) | Candidate proxies |
|---|---|---|
| Benevolence / 仁 | Relationship awareness and sensitivity to participant, role, and context | Participants per event; observed causal links between events; who/what/when/where/how of an event; the host-supplied "why" recorded as a separate, attributed claim that is checked for consistency but never trusted as authority |
| Hyo / 孝 | Technology carries its share of the burden; consent, context, privacy, protective friction | Delivery clarity of HyoDo's own output: what can be trusted now, what cannot be trusted yet and why, and the single decision left to the person; uncertainty stated as counts ("3 of 5 checks ran"); audience-appropriate wording |

Consent, context alignment, privacy, and protective friction remain Hyo
proxies. A delivery proxy that dropped them would narrow the scope, which this
contract does not allow.

HyoDo is a host-neutral public layer. Integrating hosts own orchestration,
memory, retrieval, runtime, execution, and final authority. KINGDOM is a
reference consumer and research harness, not part of HyoDo.
