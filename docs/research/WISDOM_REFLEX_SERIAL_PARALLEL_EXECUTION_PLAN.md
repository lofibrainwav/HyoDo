# Wisdom Reflex — Serial / Parallel Research Execution Plan

Status: working research execution contract
Date: 2026-09-08

Purpose: define what may be parallelized, what must remain serial, and where evidence barriers are required while auditing the KINGDOM 86 Strategy Canon and testing the Wisdom Reflex hypothesis.

This plan does **not** change the 86 canon, production EROS, KINGDOM authority, or HyoDo runtime. It defines research workflow only.

## 1. Operating rule

> **Explore broadly in parallel. Converge through one accountable decision line. Execute independent trials in parallel. Verify independently. Promote only after a serial evidence gate.**

A shorter mnemonic:

```text
many scouts → one registrar → many trials → one adjudication → independent verification
```

Parallelism is used to increase coverage and reduce wall-clock time where work is independent. Serial stages are used where order, shared state, reproducibility, or authority would otherwise become ambiguous.

## 2. Non-negotiable boundaries

### Never parallelize competing writes to the same canonical state

The following have a **single-writer / serial commit** rule:

- canonical 86 IDs and names;
- canon version declaration;
- final source-attribution status for an audited entry;
- frozen interpretation snapshot used in a confirmatory experiment;
- frozen EROS/ranking-weight policy used in a confirmatory experiment;
- benchmark protocol version;
- final evidence adjudication;
- promotion of a research result into a project lesson, policy proposal, or new canon version.

Multiple workers may investigate the same question independently, but they submit evidence to one registrar/adjudicator rather than editing the same truth record concurrently.

### Never let parallel recommendations become parallel authority

```text
parallel investigation     allowed
parallel hypothesis        allowed
parallel plans             allowed
parallel independent runs  allowed
parallel final authority   forbidden
parallel canon writers     forbidden
competing final truth      forbidden
```

Independent verifiers may run in parallel. The final completion state is still produced through one governed adjudication / Evidence Gate path.

## 3. Stage graph

```text
S0  Freeze research object
 │
 ├───────────────┬────────────────┬────────────────┐
 ▼               ▼                ▼                ▼
P1 Source audit  P2 Interpretation P3 Related-work  P4 Measurement readiness
                 Zettelkasten      / null baselines  / instrumentation
 └───────────────┴────────────────┴────────────────┘
                         │
                         ▼
C1 Serial convergence / conflict register
                         │
                         ▼
S1 Freeze benchmark snapshot + evaluation policy
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          P5 Run set A  P5 Run B  P5 Run N
              └──────────┼──────────┘
                         ▼
C2 Serial adjudication
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
        P6 replication  external  adversarial review
              └──────────┼──────────┘
                         ▼
C3 Serial promotion decision
```

`S` = serial freeze/gate, `P` = parallel lane, `C` = serial convergence.

## 4. S0 — Freeze the research object (SERIAL)

Before large parallel work starts, record exact immutable pointers:

- KINGDOM commit SHA;
- HyoDo commit/version;
- exact 86 canon snapshot;
- current strategy skill doctrine;
- current EROS virtue vocabulary and governed weight/profile source;
- current HyoDo friction/evidence schema;
- current benchmark protocol version.

The purpose is reproducibility. No worker may silently reinterpret a moving `main` branch as the same experimental object.

Acceptance:

```text
one frozen snapshot
one canonical manifest
no ambiguous HEAD references
```

## 5. P1 — Historical/source audit (PARALLEL)

Split the 86 entries into independent audit batches. Parallel workers may check:

- primary text location;
- edition/translation;
- whether the current KINGDOM `book` label is historically supportable;
- later/popular attribution versus primary-source wording;
- ambiguity, mistranslation, or anachronism;
- independent secondary scholarship.

Recommended operational decomposition:

```text
worker A: canon 1–15
worker B: canon 16–30
worker C: canon 31–45
worker D: canon 46–60
worker E: canon 61–73
worker F: canon 74–86
worker G: adversarial spot-check across all source families
```

These ranges are workload batches only, not new canon groupings.

Each worker outputs evidence records. They do not rewrite canonical IDs/names.

## 6. P2 — Interpretation Zettelkasten (PARALLEL)

For each audited canon entry, collect attributed interpretations in parallel from different perspectives, for example:

- source-faithful historical reading;
- philosophical commentary;
- military/strategic commentary;
- organizational/management reading;
- popular/practitioner reading;
- critical/counter-reading;
- KINGDOM operational interpretation;
- measured KINGDOM lesson when available.

Each Zettel must identify its provenance and type. Model-generated interpretations are labeled `GENERATED_SUGGESTION`, never silently promoted to historical interpretation.

Append-only principle:

```text
source text     is not rewritten
old Zettel      is not overwritten
new reading     appends a new Zettel
confidence      changes in a separate evidence layer
```

## 7. P3 — External research and hostile baselines (PARALLEL)

Separate workers should maintain competing explanations and strong baselines, including where relevant:

- task-structure heuristics;
- generic semantic routing / dynamic topology;
- explicit skill invocation;
- adaptive autonomy / resource allocation;
- metacognitive routing;
- equivalent modern generic principles;
- shuffled/corrupted strategy controls.

The external-review lane must actively search for work that makes the custom 86/Wisdom layer unnecessary.

Default null:

> Task structure and generic semantic routing are sufficient; historically grounded strategy interpretations add no incremental value.

## 8. P4 — Measurement readiness (PARALLEL to P1–P3)

While source and interpretation work proceeds, the instrumentation lane may independently prepare measurement capability:

- HyoDo exact version/readiness;
- KINGDOM → HyoDo observation bridge status;
- privacy/consent boundary;
- task/run identifiers and reproducibility metadata;
- observable retry, rework, intervention, verification, evidence, latency, resource, and coordination signals;
- explicit statement of which friction classes cannot be inferred from telemetry alone.

This lane must not implement a Wisdom router before the research object and benchmark are frozen.

## 9. C1 — Canon audit convergence (SERIAL)

After parallel collection, one registrar/adjudication pass reconciles conflicts for each entry.

For every disagreement, preserve the disagreement rather than force false consensus.

Example:

```yaml
current_kingdom_label: The Art of War / Sunzi tradition
primary_source_status: disputed
source_candidate_A: ...
source_candidate_B: ...
reason_for_status: ...
```

Outputs:

- audited canon manifest;
- provenance/conflict register;
- interpretation index;
- unresolved-question list;
- no silent canon rewrite.

## 10. Candidate retrieval and Top-k (SERIAL specification, PARALLEL evaluation)

The candidate retrieval algorithm must be specified once before confirmatory evaluation.

The current discussion proposes **Top-3 interpretations** as the first experimental setting, but Top-3 is not assumed optimal or canonical.

Test in parallel across matched tasks:

```text
Top-1
Top-3
Top-5 or another larger k
simple generic semantic baseline
```

Do not choose `k` after seeing which value makes the Wisdom condition look best in confirmatory results.

## 11. EROS-aligned evaluation (SERIAL policy definition)

Canonical KINGDOM virtue vocabulary is:

```text
진 = truth
선 = goodness
미 = beauty
인 = benevolence
효 = filialPiety
영 = eternity
```

KINGDOM already uses a governed weighted geometric-mean EROS system. The research question is whether an EROS-aligned evaluation is useful for ranking competing interpretations.

Before experiments, serially decide and freeze one of these paths:

1. use the canonical governed EROS calculator/profile where semantically valid; or
2. use a clearly separate research-only EROS-aligned suitability score that has **zero authority effect**.

Never create an unlabeled shadow EROS authority score.

If research ranking uses a weighted geometric mean, freeze:

- score scale;
- zero/near-zero numerical policy;
- weight source;
- missing-value handling;
- tie handling;
- rationale/evidence requirement.

## 12. S1 — Freeze benchmark snapshot (SERIAL)

Before confirmatory runs, freeze:

- canon snapshot;
- source-audit snapshot;
- interpretation Zettelkasten snapshot;
- candidate retrieval algorithm and `k` values;
- EROS/ranking policy;
- task set;
- models;
- tool access;
- budgets;
- stopping rules;
- outcome metrics;
- friction-label protocol;
- statistical analysis plan where applicable.

After this barrier, no condition may be rewritten because preliminary results look bad.

## 13. P5 — Benchmark execution (PARALLEL)

Run independent matched conditions in parallel where they do not share mutable state.

Minimum condition family:

```text
A fixed orchestration / fixed support
B task-structure heuristic
C generic semantic routing
D existing KINGDOM primary + checking principle
E richer interpretation retrieval
F interpretation + counter-reading + observable signals
G F + EROS-aligned ranking
H equivalent modern generic principles
I shuffled/corrupted control
```

Parallelization dimensions may include:

- independent tasks;
- independent seeds;
- independent condition replicas;
- independent verification runs.

Do **not** parallelize two conditions against the same mutable external resource unless isolation is proven.

## 14. C2 — Evidence adjudication (SERIAL)

All result streams converge into one evidence table.

Evaluate at minimum:

- task success / outcome quality;
- latency;
- token/compute cost;
- coordination cost;
- retry/rework;
- intervention;
- verification failures;
- evidence completeness;
- authority violations;
- uncertainty / missing data.

Do not label an episode productive, necessary, or avoidable from telemetry alone unless the predeclared labeling/causal protocol supports it.

The result is allowed to be:

```text
Wisdom layer wins
Wisdom layer ties
Wisdom layer loses
insufficient evidence
```

All four are valid research outcomes.

## 15. P6 — Replication and adversarial verification (PARALLEL)

After primary adjudication, use parallel independent verification lanes:

- rerun with different task slices;
- rerun with another model family where feasible;
- external/NotebookLM hostile review;
- source-audit spot check by a different reviewer;
- privacy and authority audit;
- negative controls and corrupted-canon controls.

This is parallel verification, not parallel authority.

## 16. C3 — Promotion decision (SERIAL)

Only after evidence and replication may one governed promotion decision occur.

Possible promotions are separate:

- `MEASURED_LESSON`: runtime-supported lesson;
- research result: publishable evidence claim;
- implementation proposal: candidate router/support logic;
- canon correction/version: historical/provenance correction;
- production behavior: requires its own authority/change process.

A positive benchmark result does not automatically change the canon or production EROS.

## 17. Practical rule for deciding serial versus parallel

Use **parallel** when all are true:

```text
work items are independent
different workers need not mutate the same state
failure of one lane does not invalidate another lane's write
a deterministic merge/adjudication step exists
```

Use **serial** when any are true:

```text
later work depends on an earlier decision
multiple writers would touch the same canonical state
ordering changes meaning
an authority/policy/evidence decision is being made
the experimental object must be frozen for reproducibility
results from parallel lanes must be reconciled
```

## 18. Operational application to the current project

Run these lanes together now:

```text
PARALLEL LANE A — 86/86 source audit
PARALLEL LANE B — interpretation Zettelkasten collection
PARALLEL LANE C — hostile external related-work / baseline audit
PARALLEL LANE D — HyoDo 4.17 + KINGDOM #773 measurement readiness
```

Then stop at one barrier:

```text
SERIAL BARRIER — audited canon manifest + conflict register + frozen research snapshot
```

Only after that barrier start the confirmatory Wisdom benchmark.

## 19. One-line doctrine

> **Parallelize evidence gathering and independent trials; serialize truth registration, authority, convergence, and promotion.**
