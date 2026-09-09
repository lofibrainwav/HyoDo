# ACL / Wisdom Reflex Research Protocol Index

Status: working research documentation

This directory is the durable roadmap and protocol surface for the HyoDo / ACL / KINGDOM research program. The public `/docs/acl/` page remains a high-level field note; these repository documents define the stricter execution and research contracts.

Read them in this order.

## 0. Top-level technical roadmap — what belongs where and when

[`HYODO_ACL_KINGDOM_TECHNICAL_ROADMAP.md`](./HYODO_ACL_KINGDOM_TECHNICAL_ROADMAP.md)

This is the top-level roadmap. Start here before adopting a new framework, paper, controller, skill system, privacy mechanism, or orchestration feature.

It defines:

- the responsibility boundary between KINGDOM, ACL, EROS/host policy, Evidence Gate, and HyoDo;
- the difference between a research-source freeze and a Measured Run execution freeze;
- Phase 0 baseline closure and Measured Run #1;
- Phase 1 observation/passive-shadow seams;
- Phase 2 matched-budget ACL experiments;
- Phase 3 proposal-first safe evolution;
- Phase 4 distributed privacy / cryptographic attestation;
- the NOW / SHADOW / EXPERIMENT / FUTURE promotion discipline;
- the rule that new SOTA research may change candidate technologies but must not silently collapse system ownership or skip evidence gates.

Current top-level doctrine:

> **Measure reality first; compare alternatives in shadow; promote only verified improvements; keep execution, authority, evidence, and observation as separate planes.**

## 1. Canon first — what is being studied

[`86_STRATEGY_CANON_AUDIT_PROTOCOL.md`](./86_STRATEGY_CANON_AUDIT_PROTOCOL.md)

Use this before making any new Wisdom Reflex implementation.

It defines:

- the current KINGDOM 86-strategy canon boundary;
- the current 7-source declaration versus independently audited historical provenance;
- CANON / SOURCE / INTERPRETATION / CONFIDENCE separation;
- append-only Zettelkasten interpretation records;
- existing KINGDOM primary-principle + checking-principle doctrine;
- generated-suggestion labeling;
- anti-contamination and authority boundaries;
- a single-writer registrar/adjudicator for canonical convergence.

## 2. Decision experiment — what is new research

[`WISDOM_REFLEX_DECISION_PROTOCOL.md`](./WISDOM_REFLEX_DECISION_PROTOCOL.md)

It separates existing KINGDOM behavior from proposed research, including:

- multiple attributed interpretation candidates;
- Top-3 as an initial, unvalidated experimental setting;
- counter-readings and failure conditions;
- canonical EROS vocabulary: 진·선·미·인·효·영 = truth / goodness / beauty / benevolence / filialPiety / eternity;
- testing an EROS-aligned weighted-geometric interpretation ranking without creating shadow authority;
- HyoDo evidence-updated confidence;
- hostile null baselines against task heuristics, generic semantic routing, modern generic principles, and corrupted controls.

## 3. Execution topology — how to work without creating coordination friction

[`WISDOM_REFLEX_SERIAL_PARALLEL_EXECUTION_PLAN.md`](./WISDOM_REFLEX_SERIAL_PARALLEL_EXECUTION_PLAN.md)

Core rule:

> **Parallelize evidence gathering and independent trials; serialize truth registration, authority, convergence, and promotion.**

Practical rhythm:

```text
SERIAL: freeze exact research-source snapshot
        ↓
PARALLEL: source audit + interpretation collection + hostile external research + measurement readiness
        ↓
SERIAL: reconcile conflicts and freeze audited manifest
        ↓
SERIAL: freeze benchmark object and evaluation policy
        ↓
PARALLEL: matched benchmark conditions / seeds / independent verification
        ↓
SERIAL: evidence adjudication
        ↓
PARALLEL: replication / external hostile review / privacy-authority audit
        ↓
SERIAL: promotion decision
```

**Do not start the large parallel 86/Wisdom audit lanes before the initial exact research-source snapshot is frozen.** Otherwise different workers may unknowingly audit different versions of KINGDOM, EROS, or the 86 canon and create false disagreement.

The Measured Run #1 runtime freeze is separate. It pins the exact merged runtime immediately before the real execution receipt and must not silently redefine the already frozen canon/source object being audited.

Current parallel lanes after the initial research-source freeze:

```text
A — 86/86 historical/source audit
B — interpretation Zettelkasten collection
C — hostile related-work / null-baseline audit
D — HyoDo + KINGDOM measurement readiness and Measured Run #1
```

All four lanes stop at a serial convergence barrier. Parallel workers submit evidence; a single registrar/adjudicator owns the canonical convergence write.

## Current non-claims

Until measured evidence exists, do not claim:

- Top-3 is optimal;
- historically grounded interpretations beat generic semantic routing;
- EROS-aligned interpretation ranking improves outcomes;
- historical/cultural provenance adds value beyond equivalent modern principles;
- HyoDo telemetry alone can classify friction as necessary, productive, or avoidable;
- an automatic Wisdom Reflex runtime is already implemented;
- IFC enforcement, autonomous skill evolution, DyTopo-style routing, Stackelberg control, or zk-MCP are current HyoDo production capabilities merely because they appear in adjacent research.

## Authority invariant

```text
wisdom / history / population evidence → recommendation          allowed
wisdom / history / population evidence → execution authority     forbidden
wisdom / history / population evidence → local policy bypass     forbidden
wisdom / history / population evidence → Evidence Gate override  forbidden
```

## Immediate roadmap gate

1. Freeze the exact research-source snapshot.
2. Start the 86/86 source audit, interpretation Zettelkasten, hostile baseline research, and measurement-readiness lane in parallel.
3. In the measurement lane, close the exact-head documentation PR, verify installed HyoDo 4.17.0, merge the observation contract under clean governance, freeze the exact runtime, and produce Measured Run #1.
4. Converge source/interpretation conflicts through one registrar/adjudicator.
5. Freeze the benchmark object and evaluation policy.
6. Only then run the falsifiable Wisdom benchmark.
7. Treat safe evolution, IFC enforcement expansion, and cryptographic attestation as later phases that require measured need and separate promotion evidence.
