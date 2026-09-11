# HyoDo / ACL / KINGDOM Evidence-First Technical Roadmap

Status: working roadmap
Date: 2026-09-08
Last measured update: 2026-09-10 PT (Phase-0 readback against the public 4.19.2 line)

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

## 2. Current gate: complete Evidence Pack v1 before expansion

The immediate objective is not IFC enforcement, autonomous skill evolution, RL training, dynamic topology deployment, or zero-knowledge circuits.

The immediate objective is **Evidence Pack v1**: a small but attributable set of real KINGDOM executions that proves what HyoDo can and cannot observe across materially different outcomes.

Measured progress is now:

```text
research-source snapshot boundary defined
        ↓
HyoDo 4.17.0 released and installable                         OBSERVED
        ↓
KINGDOM Observation Contract v1 merged                        OBSERVED
        ↓
Measured Run #1 — infrastructure/provider failure             OBSERVED
        ↓
observer fidelity repair — single-agent serial classification OBSERVED
        ↓
Measured Run #2 — output/verification quality failure         OBSERVED
        ↓
Coder coarse terminal truth (ok + closed status enum)         OBSERVED
        ↓
Measured Run #2b — same execution behavior, unknown -> fail   OBSERVED
        ↓
target-run isolation capability (KINGDOM #779)                OBSERVED
        ↓
Run #3 actual use of that filter                              UNOBSERVED
        ↓
Measured Run #3 — successful real execution                   OBSERVED
        ↓
Run #1 and Run #3 receipts in this repository                 OBSERVED
        ↓
Run #2 / #2b standalone receipts                              MISSING
        ↓
sensor coverage matrix                                        OBSERVED
        ↓
Evidence Pack v1                                              SEALED
```

Read back 2026-09-10 against the published 4.19.2 line. What changed since
this table was first written, and what did not:

- **Run #3 is measured and sealed.** `EVIDENCE_PACK_V1_2026-09-10.md` seals it
  by content hash, and its five release-chain rows — signed tag, public
  wheel/sdist, SBOM, PyPI provenance, clean install — were `HOLD` at the time
  and have since been measured against the published 4.18.0 artifacts and
  appended to that pack.
- **`target-run attribution isolation` splits into two facts.** The capability
  is `OBSERVED`: KINGDOM #779 merged 2026-09-09 and does what this row asks —
  filters the observation bridge by an explicit target run *before* privacy
  mapping, keeps unrelated runs out of counts and actor tracking, never copies
  the raw producer run id into HyoDo events, and does not persist the shared
  cursor during a filtered measurement.

  Whether Run #3 *used* it is `UNOBSERVED`. Neither Run #3 receipt records a
  `run_filter` line. What they record is an isolated evidence root, which is
  storage isolation — a different thing. #779 merged a day before the corrected
  run, so it could have been used; being able to use a filter is not evidence
  of having used it, and the capability is not read backwards into the run.
- **The sensor coverage matrix exists**, read from the KINGDOM contract, its
  trace producer and the bridge rather than from what this document wished for:
  `SENSOR_COVERAGE_MATRIX.md`. Separating a missing producer vocabulary from a
  deliberately excluded channel turned out to need three causes rather than
  two -- a channel emitted and dropped by the allowlist, a signal that exists
  in the producer but never reaches its trace payload, and a concept the
  producer does not have. Each needs different work to close.

  It also records that receipts come from two different layers: Run #1/#2/#2b
  measured the producer path, while Run #3 was constructed by a harness. Both
  are true about different things, and a single coverage number over the two
  would claim an observation capability this system does not have.
- **Run #2 and #2b standalone receipts are `MISSING`.** Both runs exist as
  prose in section 3 of this document. Copying that prose into receipt files
  would change the format of a claim without adding a measurement, so the
  Phase-0 bundle requirement stays partially met.

Declaring Phase 0 complete is an authority decision, not a measurement, and
these two open rows belong to whoever makes it.

There are **two different freezes**:

1. **Research-source freeze** — pins the canon/EROS/KINGDOM/HyoDo objects that parallel source and interpretation workers are auditing.
2. **Measured-run execution freeze** — pins the exact merged runtime used for each real measurement receipt.

Do not confuse them. The first must occur before large parallel 86/Wisdom audit lanes. The second occurs immediately before each measured execution and must be recorded in the evidence receipt.

No later roadmap phase should be promoted because it is fashionable or supported by an adjacent paper. Promotion requires local evidence that the additional layer solves a measured problem.

## 3. Phase 0 — Baseline closure through Evidence Pack v1

### Goal

Produce a citation-quality baseline that includes failure from infrastructure, failure from output/verification quality, a controlled sensor correction, and one successful execution — with attribution, privacy, authority non-interference, and known sensor gaps made explicit.

### Measured state so far

#### Run #1 — infrastructure/provider failure

Observed baseline properties:

- real KINGDOM execution trace reached HyoDo;
- 16 HyoDo ledger events were recorded;
- prohibited raw-field leakage observed: 0;
- policy decision/evaluator remained unevaluated/null;
- execution failed before useful Coder output because the critical LLM chain was unavailable;
- outcome remained `unknown` because terminal producer truth was not yet present;
- the first observer version misclassified the single-agent execution as `multi_actor_serial`.

Interpretation: useful failure sample and sensor-discovery baseline, not a successful task sample.

#### Run #2 — output/verification quality failure

After observer fidelity repair and LLM-chain recovery:

- the execution advanced through 18 pipeline steps;
- Coder produced output;
- Reviewer rejected the result 8 times;
- the run remained a real execution failure;
- single-agent attribution mapped to one actor and `orchestration_pattern=serial`;
- prohibited raw leakage remained 0;
- HyoDo outcome remained `unknown` because the producer still did not emit terminal truth;
- retry/rework/review rejection/iteration detail remained unobserved because Observation Contract v1 only consumes the four Coder lifecycle channels.

Interpretation: the failure axis moved from model availability to output/verification quality while the privacy and authority boundaries remained intact.

#### Coder terminal-truth correction

KINGDOM then added only coarse terminal truth to existing Coder lifecycle traces:

```text
task-finished -> ok: boolean + closed canonical status enum
run-finished  -> ok: boolean + closed canonical status enum
```

The change did not add raw error text, generated code, reviewer prose, paths, prompts, responses, retry behavior, scheduling changes, EROS changes, or Evidence Gate changes.

#### Run #2b — controlled sensor remeasurement

The same failing fixture was rerun after the terminal-truth change.

Observed comparison:

```text
execution steps           18 -> 18
Reviewer rejections        8 -> 8
iterations                 3 -> 3
execution result        FAIL -> FAIL
HyoDo outcome        unknown -> fail (for new-code target runs)
raw leakage               0 -> 0
```

This is the first measured evidence that HyoDo can classify a real KINGDOM failure as `fail` while execution behavior remains unchanged.

Run #2b also exposed the remaining attribution problem: unrelated processes shared the same `kingdom:events` stream, so the measurement contained both new-code target runs and unrelated old-code runs. Schema differences made them distinguishable after the fact, but that is not a durable attribution contract.

### Remaining Phase-0 work

1. **Target-run attribution isolation**
   - filter the observation bridge by an explicit target KINGDOM run before privacy mapping;
   - unrelated runs must not affect event counts, actor tracking, or HyoDo output;
   - raw producer run id must remain local and absent from HyoDo events/receipts;
   - filtered measurement must not corrupt the normal observer's persisted cursor/tracker state.
2. **Measured Run #3 — successful sample**
   - choose a small, real, high-probability task;
   - freeze exact KINGDOM/HyoDo execution versions;
   - use the attribution-isolated observation path;
   - obtain a real successful outcome sample.
3. **Sensor coverage matrix**
   - mark each desired signal as OBSERVED, PARTIAL, or UNOBSERVED;
   - distinguish missing producer vocabulary from intentionally excluded channels;
   - keep Reviewer coarse verdict, retry/rework, iteration detail, model/provider identity, and resource-conflict signals honest if still unwired.
4. **Evidence Pack v1 seal**
   - bundle Run #1, Run #2, Run #2b, Run #3, exact version pointers, privacy/authority checks, and the sensor coverage matrix;
   - record residual limitations rather than repairing them post hoc inside the pack.

### Phase-0 acceptance evidence

At minimum capture:

- exact research-source snapshot pointers;
- exact KINGDOM commit SHA for every measured run;
- exact HyoDo version/commit;
- observer contract/filter version;
- consent state showing local-only / no network contribution;
- explicit stream/run attribution boundary for Run #3;
- event count and event schema version;
- serial/fanout structure that is actually observable;
- measured terminal outcome where producer truth exists;
- retry/rework/intervention/reviewer/verification signals only when actually wired;
- evidence completeness and missing-data notes;
- proof that the observer/filter did not mutate execution authority or behavior;
- privacy review showing prohibited raw fields were not copied;
- sensor coverage matrix across the sealed runs.

### Phase-0 non-goals

Do not add yet:

- an IFC enforcement engine inside HyoDo;
- a Stackelberg execution controller inside the Evidence Gate;
- autonomous `evolutions.json` PATCH/REBUILD behavior;
- GRPO or other RL training;
- a production DyTopo-style router;
- zk-MCP/Circom circuits;
- an automatic Wisdom Reflex runtime;
- automatic Reviewer intervention or policy authority because Reviewer telemetry becomes observable.

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

### 4.3 Skill/topology/reviewer observation

Before adopting a new orchestration standard or router, measure only signals that have explicit producers and documented privacy transforms:

- skill invocation identity/version;
- explicit versus bulk-prompt skill activation;
- agent topology/fanout/join signals that are actually representable;
- messages/rounds/tokens/latency;
- stalls and handoffs;
- verification outcomes;
- failures and retries;
- optional coarse Reviewer verdict (`approved` / `rejected`) as a separate producer lane if later justified.

Reviewer verdict must remain distinct from Coder terminal truth. Observing `rejected` must not itself grant Reviewer new authority or change the execution result path.

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
freeze exact research-source snapshot
        ↓
PARALLEL
A 86/86 historical/source audit
B interpretation Zettelkasten collection
C hostile related-work and null-baseline research
D Evidence Pack v1 completion / HyoDo-KINGDOM measurement readiness
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

Each measured-run execution snapshot is a separate runtime receipt inside lane D. It does not authorize changing the already frozen source/canon object being audited by lanes A-C.

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
OBSERVED / SEALED
HyoDo 4.17.0 release
Observation Contract v1
Measured Run #1
observer fidelity correction
Measured Run #2
Coder terminal truth correction
Measured Run #2b unknown -> fail validation
Measured Run #3 successful sample
Evidence Pack v1 seal
public release chain 4.18.0 .. 4.19.2 (tag, SBOM, provenance, install)
Cursor/Codex host adapters, fixture-verified
Codex live host callback reaching the ledger
target-run isolation capability (KINGDOM #779)
sensor coverage matrix, read from producer code

SERIAL P0 — REMAINING
Run #2 / #2b standalone receipts            MISSING
        ↓
Run #3 use of the #779 target-run filter    UNOBSERVED
        ↓
Phase 0 COMPLETE                            authority decision

PARALLEL P1 — NOW
live host canary: an installed Cursor/Codex process reaching the ledger
(the 4.19.2 canary fed a synthetic payload to the CLI; no host was observed)

PARALLEL RESEARCH LANES
A 86/86 provenance audit
B interpretation Zettelkasten collection
C hostile baseline / related-work research
D Evidence Pack / measurement completion

SERIAL C1
reconcile source/interpretation conflicts and freeze audited manifest

SERIAL S1
freeze falsifiable Wisdom benchmark + evaluation policy

PARALLEL P2
run matched benchmark conditions / seeds / independent verification

SERIAL C2/C3
adjudicate evidence and decide promotion

FUTURE
consider safe evolution only if repeated evidence supports it
consider distributed IFC/ZK attestation only when a measured use case requires it
```

## 12. Status labels

Use these labels in future roadmap updates so ideas do not drift into implied implementation:

```text
SHIPPED     implemented and released
OBSERVED    directly verified in the current target state
READY       prerequisites satisfied but not yet promoted/executed
IN_PROGRESS active work with incomplete evidence
SHADOW      recommendation/evaluation path causally excluded from authority
EXPERIMENT  falsifiable research condition
FUTURE      intentionally deferred candidate
BLOCKED     cannot proceed until an explicit dependency is satisfied
UNOBSERVED  not directly verified
MISSING     the artifact does not exist, so there is nothing to verify
```

`MISSING` and `UNOBSERVED` are not interchangeable. `UNOBSERVED` says nobody
looked; `MISSING` says there is nothing to look at. Collapsing them would hide
which of the two a reader is facing.

A paper result is never `SHIPPED` or `OBSERVED` for HyoDo merely because the paper reports it.

## 13. Roadmap anti-drift rule

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

## 14. One-line roadmap

> **Measure reality first; isolate attribution before citation; compare alternatives in shadow; promote only verified improvements; keep execution, authority, evidence, and observation as separate planes.**
