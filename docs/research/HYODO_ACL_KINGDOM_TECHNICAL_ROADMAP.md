# HyoDo / ACL / KINGDOM Evidence-First Technical Roadmap

Status: working roadmap
Date: 2026-09-08

Purpose: preserve the agreed system boundaries, sequencing, and promotion gates so new research ideas do not silently turn HyoDo into a monolithic orchestrator or move unmeasured hypotheses into production.

This roadmap is intentionally conservative. It records **where a capability belongs**, **what must be measured first**, **what may proceed in parallel**, and **what must remain serial**.

## 1. System responsibility map

```text
KINGDOM
  executes tasks, schedules workers, invokes tools and skills, and owns runtime orchestration

ACL
  researches support allocation, resource recommendations, topology/support hypotheses,
  and contextual collaboration recommendations

EROS / host policy
  owns governed value/policy evaluation and execution authority boundaries

Evidence Gate
  determines whether completion claims are supported by the required evidence

HyoDo
  observes, records, validates, attests, and measures execution evidence and friction signals
```

The architecture must resist role collapse.

```text
HyoDo -> observe / attest / measure                         allowed
HyoDo -> become the general task orchestrator              not the roadmap
ACL -> recommend support/resource/topology changes         allowed
ACL -> grant execution authority                           forbidden
wisdom/population evidence -> recommendation               allowed
wisdom/population evidence -> policy/Evidence Gate bypass  forbidden
```

## 2. Current gate: close the baseline before expansion

The immediate objective is not IFC enforcement, autonomous skill evolution, RL training, dynamic topology deployment, or zero-knowledge circuits.

The immediate objective is a reproducible measured baseline:

```text
HyoDo 4.17.0 released and installable
        ↓
KINGDOM Observation Contract v1 merged under existing authority boundaries
        ↓
local-only observer explicitly enabled
        ↓
one real KINGDOM task
        ↓
HyoDo friction/evidence preview
        ↓
Measured Run #1 receipt
```

No later roadmap phase should be promoted because it is fashionable or supported by an adjacent paper. Promotion requires local evidence that the additional layer solves a measured problem.

## 3. Phase 0 — Baseline closure and measured reality

### Goal

Create the first trustworthy KINGDOM -> HyoDo measured execution trace while freezing the research object used by the 86/Wisdom work.

### Required work

- close the public ACL/research documentation hardening PR on an exact green head;
- verify HyoDo 4.17.0 through an actual installed CLI readback;
- merge KINGDOM Observation Contract v1 only after its exact-head CI remains green and local governance requirements are satisfied;
- enable only the existing local-only friction state;
- execute a real, useful KINGDOM task;
- record HyoDo events and generate a friction preview;
- preserve privacy and authority invariants;
- freeze the exact KINGDOM/HyoDo/canon/EROS research snapshot before confirmatory Wisdom evaluation.

### Phase-0 acceptance evidence

At minimum capture:

- exact KINGDOM commit SHA;
- exact HyoDo version/commit;
- observer contract version;
- consent state showing local-only / no network contribution;
- event count and event schema version;
- serial/fanout structure that is actually observable;
- retry/rework/intervention/verification signals when present;
- evidence completeness and missing-data notes;
- proof that the observer did not mutate execution authority;
- privacy review showing prohibited raw fields were not copied.

### Phase-0 non-goals

Do not add yet:

- an IFC enforcement engine inside HyoDo;
- a Stackelberg execution controller inside the Evidence Gate;
- autonomous `evolutions.json` PATCH/REBUILD behavior;
- GRPO or other RL training;
- a production DyTopo-style router;
- zk-MCP/Circom circuits;
- an automatic Wisdom Reflex runtime.

## 4. Phase 1 — Observation and passive-shadow seams

### Goal

Expand what can be **observed and compared** without allowing recommendations to contaminate active execution.

### 4.1 Information-flow observation

Compositional privacy and cross-step leakage are important future risks, but the first HyoDo role is **IFC attestation**, not IFC sovereignty.

Preferred boundary:

```text
source/message labels
        ↓
policy / IFC enforcement plane
        ↓
ALLOW / BLOCK decision
        ↓
HyoDo records:
- relevant labels
- flow decision
- governing rule reference
- provenance/evidence
```

HyoDo may later validate that a policy engine behaved as declared. It should not become the only owner of runtime authority simply because it records the decision.

### 4.2 Resource-control shadow channel

Stackelberg-style or other contextual resource controllers belong first in an ACL research shadow lane.

```text
context + measured state
        ↓
ACL resource recommendation
        ↓
PASSIVE SHADOW RECORD
        X
active execution policy
```

The prior study's reported cost reduction is a baseline to reproduce or beat, not a HyoDo product guarantee.

The Evidence Gate must remain an evidence/completion gate, not a token-budget controller.

### 4.3 Skill/topology observation

Before adopting a new orchestration standard or router, measure:

- skill invocation identity/version;
- explicit versus bulk-prompt skill activation;
- agent topology/fanout/join signals that are actually representable;
- messages/rounds/tokens/latency;
- stalls and handoffs;
- verification outcomes;
- failures and retries.

Agent Skills compatibility may be useful as an adapter. Swarm Skills, SkillForge, and DyTopo remain research references/baselines until local matched evidence supports promotion.

## 5. Phase 2 — ACL matched-budget experiments

### Goal

Test competing explanations before implementing a privileged custom controller.

Run matched tasks/models/tools/budgets across conditions such as:

```text
A fixed orchestration / fixed support
B task-structure heuristic
C generic semantic routing
D existing KINGDOM primary + checking principle
E richer interpretation retrieval
F interpretation + counter-reading + observable signals
G F + EROS-aligned ranking
H equivalent modern generic principles
I shuffled/corrupted strategy control
```

Where appropriate, include strong adjacent implementations or faithful reproductions of:

- dynamic semantic topology routing;
- explicit skill invocation;
- contextual resource allocation;
- simple modern task heuristics.

### Required metrics

Do not optimize one metric in isolation. Record a Pareto-relevant set including:

- task success / outcome quality;
- verification quality;
- token/compute cost;
- wall-clock latency;
- agent count and communication rounds;
- retry/rework;
- human intervention;
- evidence completeness;
- coordination overhead;
- authority violations;
- missing or unobservable data.

Telemetry alone does not establish that friction is necessary, productive, or avoidable. Those labels require a predeclared labeling or causal protocol.

## 6. Phase 3 — Safe evolution, proposal first

### Goal

If repeated measured evidence shows a stable coordination problem, allow the system to propose reusable changes without permitting measurement data to self-authorize code/policy mutation.

### Safe evolution pipeline

```text
measured friction/outcome evidence
        ↓
evolution / patch proposal
        ↓
shadow evaluation
        ↓
independent verification
        ↓
serial governed promotion gate
        ↓
new versioned skill/workflow/policy candidate
```

`evolution record` does **not** mean `applied mutation`.

If an `evolutions.json`-like artifact is used, it should initially be a proposal/evidence ledger. Do not let HyoDo telemetry directly perform autonomous INSERT/MODIFY/DELETE/REBUILD actions.

### Provenance rule

Never erase the evidence trail during compaction or rebuild.

```text
old evolution evidence -> immutable/versioned archive
new compacted artifact  -> new version
manifest                -> links proposal, evidence, verification, and promotion
```

Population-derived evidence remains recommendation-only and must pass local privacy, poisoning, policy, and Evidence Gate boundaries.

## 7. Phase 4 — Distributed privacy and cryptographic attestation

### Goal

Only after there is a demonstrated need for cross-runtime or third-party verification, add privacy-preserving attestations.

Potential seams include:

- IFC enforcement adapters with HyoDo evidence receipts;
- privacy-minimized population evidence;
- digest/commitment records for selected claims;
- optional zero-knowledge proof adapters for claims that genuinely require third-party verification without plaintext disclosure;
- cross-runtime audit protocols.

A zk-MCP or Circom implementation is a possible research adapter, not a current product requirement.

Prototype parameters from an external paper must not be copied as HyoDo production constants without local scalability and threat-model validation.

Preferred sequence:

```text
HyoDo evidence
        ↓
privacy-minimized claim
        ↓
digest / commitment seam
        ↓
optional future proof adapter
        ↓
third-party verification
```

## 8. Research roadmap for the 86 Strategy Canon / Wisdom Reflex

The 86/Wisdom work proceeds beside, not inside, the HyoDo runtime expansion.

```text
SERIAL
freeze exact research snapshot
        ↓
PARALLEL
A 86/86 historical/source audit
B interpretation Zettelkasten collection
C hostile related-work and null-baseline research
D HyoDo/KINGDOM measurement readiness
        ↓
SERIAL
conflict reconciliation + audited manifest
        ↓
SERIAL
freeze benchmark object and evaluation policy
        ↓
PARALLEL
matched conditions / seeds / independent verification
        ↓
SERIAL
evidence adjudication
        ↓
PARALLEL
replication / hostile review / privacy-authority audit
        ↓
SERIAL
promotion decision
```

Core doctrine:

> **Parallelize evidence gathering and independent trials; serialize truth registration, authority, convergence, and promotion.**

## 9. Existing KINGDOM facts versus proposed Wisdom research

Do not relabel existing KINGDOM behavior as new ACL novelty.

Existing project state includes:

- the 86-strategy canon and declared seven-source ROOT;
- strategy-to-EROS mappings;
- one primary principle plus one checking/counter principle;
- canonical EROS virtues and governed weighted geometric mean;
- existing authority and Evidence Gate boundaries.

Proposed research includes:

- plural attributed interpretation Zettels;
- contextual retrieval of multiple candidate interpretations;
- Top-3 as an initial, unvalidated candidate-set size;
- explicit contrast/failure-condition comparison;
- testing EROS-aligned interpretation ranking;
- evidence-updated contextual interpretation confidence.

## 10. Promotion gates

Every new technical layer must answer four questions before production promotion:

1. **Measured need** — what observed failure/friction requires this layer?
2. **Matched evidence** — does it beat a simpler baseline under the same budget and constraints?
3. **Authority safety** — can it remain recommendation-only until a governed authority path explicitly accepts it?
4. **Reproducibility/privacy** — can the result be reproduced without exposing prohibited raw data or silently changing the experimental object?

If one answer is missing, the capability remains research/shadow/adaptor status.

## 11. Current priority order

```text
P0  close exact-head docs/ACL hardening
P0  verify installed HyoDo 4.17.0
P0  merge KINGDOM Observation Contract v1 under clean governance
P0  produce Measured Run #1

P1  freeze research snapshot
P1  audit 86/86 provenance in parallel
P1  collect interpretation Zettels in parallel
P1  continue hostile baseline research in parallel

P2  freeze and run the falsifiable Wisdom benchmark
P3  consider safe evolution only if repeated evidence supports it
P4  consider distributed IFC/ZK attestation only when a measured use case requires it
```

## 12. Roadmap anti-drift rule

New external research may change the candidate technology list, but it must not silently change system ownership or phase order.

When a new paper or framework appears, classify it first:

```text
observation / attestation capability -> HyoDo candidate
support/resource recommendation      -> ACL candidate
execution/topology/skill runtime     -> KINGDOM candidate
policy/authority enforcement         -> EROS / host policy candidate
completion truth                     -> Evidence Gate candidate
```

Then decide whether it belongs in NOW, SHADOW, EXPERIMENT, or FUTURE based on measured evidence.

## 13. One-line roadmap

> **Measure reality first; compare alternatives in shadow; promote only verified improvements; keep execution, authority, evidence, and observation as separate planes.**
