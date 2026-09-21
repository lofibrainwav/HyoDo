# Portability Research v0

Status: **research-only / proposal frozen for execution**  
Product boundary: **HyoDo 4.20.2 remains frozen**

This protocol tests whether HyoDo needs a small, reusable evidence primitive at
all. It does not define a new Core schema, runtime capability, aggregate score,
or authority semantic.

## Research question

Can three independent domains expose the same evidence failure with the same
minimal primitive, without forcing domain expertise or large adapter logic into
HyoDo?

The pilot covers 36 adversarial fixtures:

| Domain | Fixtures | Boundary |
| --- | ---: | --- |
| Software | 12 | source, commit, runtime, test, deployment |
| Professional | 12 | case, source, approval, submission, effect |
| Creative | 12 | asset, edit, provenance, approval, publication |

The fixture count is a falsification pilot, not evidence of generality.

## Research Envelope: questions, not schema

Each domain is first evaluated using the questions below. The questions are
not required fields and must not be converted into a mandatory envelope before
the pilot produces evidence for doing so.

1. Can we identify the subject?
2. What exact claim is being supported?
3. What evidence supports only that claim?
4. What binds evidence to this subject?
5. How fresh is it?
6. Was the claimed effect observed?
7. Where does authority stop?
8. What human burden remained?

Existing domain evidence is the source material. The research layer reads it;
it does not rewrite or promote it into HyoDo runtime truth.

## Adversarial fixture families

Each domain should contain one or more fixtures for every family below, with
the domain-specific subject and evidence retained in its native form:

- stale evidence;
- wrong subject binding;
- replayed or duplicated evidence;
- missing claimed effect;
- unsupported conclusion beyond the evidence scope;
- ambiguous authority or approval boundary;
- incomplete provenance;
- conflicting evidence;
- missing human decision;
- valid bounded support;
- valid support with an explicit limitation; and
- domain-specific near miss.

The valid cases are controls. They must not be used to claim that the system
understands professional correctness, creative quality, or software quality.

## Oracle and outcomes

The oracle records the expected bounded result independently of the candidate
representation. Every fixture receives one of:

```text
SUPPORTED       evidence supports only the stated bounded claim
BLOCKED         evidence is insufficient, stale, misbound, or contradictory
AMBIGUOUS       evidence and authority boundaries cannot be resolved
UNOBSERVED      the claimed effect was not measured
```

The primary error measures are:

- **false-green**: a fixture is treated as supported when the oracle says it is
  blocked, ambiguous, or unobserved;
- **false-block**: a bounded supported fixture is rejected without an evidence
  defect;
- **ambiguity**: the result cannot be assigned without inventing missing
  evidence or authority; and
- **adapter exception cost**: domain-specific branches, translations, and
  special cases required to use a candidate primitive.

`EVIDENCE_SUPPORTED` must never appear alone in a result summary. The minimum
display unit is:

```text
Support:     SUPPORTED
Scope:       "used spreadsheet X in this calculation"
Evidence:    [ref-17, ref-22]
Observed at: 2026-09-21T00:00:00Z
Limitations: "does not establish professional correctness"
```

## Human burden instrumentation

Do not optimize only for elapsed verification time. Record these separately:

- active verification time;
- manual cross-check count;
- context switches;
- unresolved questions;
- rework after wrong reliance; and
- instrumentation time and added data-entry burden.

A candidate fails the burden test if it reduces visible verification time by
silently removing necessary checks or increasing wrong-reliance rework.

## Six-lens boundary

The six lenses are a bounded human review lens over observed evidence:

```text
Evidence Core       What is observed?
        ↓
Six lenses           How should a human inspect it?
        ↓
Human/domain owner   What should we decide?
```

The pilot must reject any design that turns a lens into truth, authority,
professional correctness, or creative taste. HyoDo may report provenance,
freshness, binding, approval, and observed effect; it does not decide whether a
tax conclusion is legally correct or whether an artwork is beautiful.

## Candidate survival rule

A primitive becomes a **Core Candidate** only if all conditions hold:

1. It is independently needed in all three domains.
2. Removing it increases a measured false-green or false-block result.
3. It is simpler than the domain-specific logic it replaces.
4. Its instrumentation burden is not excessive.
5. It does not take over authority, taste, or expert judgment.

The number of surviving fields is not the primary result. Adapter exception
cost and failure deltas are primary results. A small apparent core with large
domain-specific exception code is a failed abstraction.

## Execution order

```text
freeze source/evidence snapshots
        ↓
parallel: three domain evidence inventories
        ↓
parallel: 36 adversarial fixture evaluations
        ↓
serial: oracle adjudication and conflict record
        ↓
compare: no-envelope baseline vs candidate primitive(s)
        ↓
report: false-green, false-block, ambiguity, burden, exception cost
        ↓
promotion proposal only if every survival rule passes
```

The first run must preserve null results and domain exceptions. No Core
promotion, schema pin, public package change, or authority change is implied by
this document.

## Non-claims

This protocol does not claim that:

- the three domains are representative of all domains;
- 36 fixtures establish portability;
- a shared question implies a shared data field;
- HyoDo can judge domain correctness or creative quality; or
- a future Core primitive will exist.

