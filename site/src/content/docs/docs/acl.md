---
title: ACL — Adaptive Collaboration Layer
description: A working field note on evidence-grounded support profiles, human wisdom as a metacognitive prior, and measurable collaboration friction.
---

> **Status — working research field note, reviewed 2026-09-08.** ACL here means **Adaptive Collaboration Layer**, not the Association for Computational Linguistics. This page is not a claim of peer review, venue submission, first-in-field novelty, or measured effectiveness.

# Adaptive Collaboration Layer

**Reader map.** This page is the focused field note for the **Wisdom Reflex + collaboration-topology** hypothesis. See [Research](/docs/research/) for the broader ACL empirical program, sealed benchmark baseline, related work, and publication status. See [Friction Contribution](/docs/friction-contribution/) for the local measurement contract.

## Current claim lock

The public product boundary is fixed below. The [Measured Run #1 receipt](https://github.com/lofibrainwav/HyoDo/blob/main/docs/research/MEASURED_RUN_1_2026-09-08.md) records one observed KINGDOM/HyoDo execution; it is not a claim of ACL effectiveness.

| Capability | Status | Evidence boundary |
| --- | --- | --- |
| gates / ledger / friction preview | SHIPPED | Local preview/export; ledger. |
| Graph v1 | SHIPPED (site DEMO FIXTURE) | Local dashboard; fixed demo site. |
| Graph v2 join | NOT BUILT | No join runtime/viewer; SCC oracle only. |
| Cursor/Codex hooks | UNOBSERVED | No verified host adapter. |
| remote MCP / ChatGPT | CONTRACT ONLY | Hosted contract; runtime unobserved. |
| ACL runtime / Wisdom Reflex | RESEARCH | Hypothesis; no automatic router. |
| friction collector | NOT BUILT | No collector/uploader; transport disabled. |

HyoDo measures what happened. ACL asks a different question:

> **What support profile should this human–AI workflow receive in this context?**

“Support” should not be treated as one scalar before evidence justifies that simplification. A useful profile may vary independently across dimensions:

| Support dimension | Example question |
| --- | --- |
| **Human oversight** | Is a checkpoint or explicit approval useful? |
| **Verification depth** | How much independent checking is warranted? |
| **Explanation depth** | How much rationale or trace visibility is useful? |
| **Exploration / topology** | Single path, parallel specialists, diverse replicas, or diverge→converge? |
| **Resource budget** | How much extra time / compute / coordination is justified? |

The research goal is not maximum autonomy and not minimum human involvement. It is to reduce **avoidable friction** while preserving **necessary friction** and allowing **productive friction** when clarification, dissent, or verification improves the outcome.

## Hard separation: authority, support, proof

| Layer | Question | Responsibility |
| --- | --- | --- |
| **EROS / local authority** | **Whether?** | Is this action permitted at all? |
| **ACL / support allocation** | **What support profile?** | What oversight, verification, explanation, exploration, or budget is useful? |
| **Evidence Gate** | **Done?** | Is completion actually supported by evidence? |

The invariant is intentionally stronger than a recommendation policy:

```text
Population evidence → ACL support recommendation  ✅
Population evidence → execution authority         ❌
Population evidence → override local policy       ❌
Population evidence → override Evidence Gate      ❌
```

A common task may still require approval. A statistically successful pattern may still be blocked. A culturally familiar maxim may suggest a perspective, but it never grants authority.

## Human wisdom as a metacognitive prior

The working hypothesis extends ACL beyond telemetry. Human societies have compressed recurring experience about timing, cooperation, restraint, trust, conflict, verification, and responsibility into classical texts, maxims, proverbs, and stories.

We do **not** treat that material as universal truth or as executable policy.

```text
Wisdom ≠ truth
Wisdom ≠ authority
Wisdom = accumulated human hypothesis / perspective prior
```

The useful capability is not recalling a proverb on command. It is having relevant and countervailing perspectives available quickly enough to test them against the current situation.

For example:

- **Romanized Korean: “Baekjijangdo matdeulmyeon natda”** — even a sheet of paper is easier to lift together — can suggest more parallel workers when work is independently decomposable.
- **Romanized Korean: “Sagongi maneumyeon baega saneuro ganda”** — too many boatmen send the boat up the mountain — can warn against multiple competing decision owners or writers.

These are not executable rules. They are contextual lenses. The same system may use broad parallel exploration, converge to one plan, then execute with a single authority line and many independent workers.

A compact operating hypothesis is:

> **Think widely. Decide once. Execute in parallel where independence permits. Verify independently.**

The research question is whether a culturally and historically grounded strategy prior adds measurable value to **contextual topology choice** and **support allocation** beyond simpler task-structure heuristics.

## Corpus governance: culture is provenance, not authority

A wisdom corpus creates its own risks. The research contract should therefore require:

- source provenance: tradition, era, edition, translator, and uncertainty where known;
- counter-principles rather than one-sided maxim retrieval;
- culture or language as **source metadata**, never a basis for inferring what a user should believe from nationality, ethnicity, or identity;
- explicit treatment of translation ambiguity and copyright / licensing constraints;
- exclusion or quarantining of dehumanizing, discriminatory, or otherwise unsafe material from recommendation authority; and
- inspectable links from a recommendation back to the corpus items that influenced it.

The phrase **KINGDOM 86-strategy project canon** on this page refers to a project-specific machine-readable strategy set. It is not a claim that history contains a universally recognized “86-strategy canon.”

## Why this is a real research problem in 2026

Several adjacent research strands point at the same gap from different directions.

### 1. Agent architecture must match task structure

The primary paper **“Towards a Science of Scaling Agent Systems”** evaluates **180 agent configurations** across five architectures and three model families. It reports that centralized coordination improved a parallelizable Finance-Agent task by **80.9%** over a single agent, while multi-agent variants degraded sequential PlanCraft performance by **39–70%**. Its empirical model selected the optimal coordination strategy for **87% of held-out configurations**, and independent multi-agent systems showed much larger error amplification than centralized coordination.

Sources: [Kim et al., arXiv:2512.08296](https://arxiv.org/abs/2512.08296) and the companion [Google Research summary](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/).

This supports a narrower principle than “more agents are better”:

```text
parallelizable / decomposable → parallelism may help
sequential / tightly shared state → coordination tax may dominate
```

### 2. “Wisdom” is being separated from raw intelligence

A 2026 *Trends in Cognitive Sciences* article, **“Imagining and building wise machines: the centrality of AI metacognition,”** distinguishes object-level strategies from metacognitive strategies such as **intellectual humility, perspective-taking, and context adaptability**. It argues that wisdom evaluation should be context-sensitive and should judge the strategy-selection process, not only the outcome.

Sources: [Johnson et al., PubMed](https://pubmed.ncbi.nlm.nih.gov/41760502/) and DOI `10.1016/j.tics.2026.01.002`.

That is close to the role proposed here for a Wisdom Reflex: not a database of answers, but a repertoire of strategies for judging **which way of thinking fits the current problem**.

### 3. Understanding a proverb is easier than using it well

EACL 2026 research on culturally grounded figurative language evaluated 22 LLMs and found a **14.07% drop** from understanding to pragmatic use. Providing contextual sentences improved pragmatic-use accuracy by **10.66%**.

Source: [Attia et al., “Beyond Understanding: Evaluating the Pragmatic Gap in LLMs’ Cultural Processing of Figurative Language,” EACL 2026](https://aclanthology.org/2026.eacl-long.341/).

A system that can explain a maxim but cannot select, reject, or balance it in context does not yet demonstrate the proposed reflex.

### 4. Korean cultural knowledge has the same application gap

KIM Bench contains **1,175 Korean idiom instances** and reports persistent difficulty with deep semantic and contextual understanding.

Source: [Wang, Park & Kim, “Benchmarking Korean Idiom Understanding,” RANLP 2025](https://aclanthology.org/2025.ranlp-1.156/).

Nunchi-Bench likewise distinguishes factual cultural recognition from practical application and reports stronger gains from explicit cultural framing than from simply changing the prompt language.

Source: [Kim & Lee, “Nunchi-Bench,” Findings of ACL 2025](https://aclanthology.org/2025.findings-acl.794/).

These results make **contextual application** a better benchmark target than quote recall.

### 5. Friction can be productive

Anthropic’s August 2026 independent-research program reported privacy-preserving analyses across roughly **250,000 Claude.ai / Claude Code conversations**. The Stanford SALT work in that program found human direction and oversight in nearly three-quarters of conversations and described human–AI friction as common but often productive: iteration can clarify intent, refine output, and keep people engaged.

Source: [Anthropic — “Enabling independent research on how people use Claude” (2026-08-26)](https://www.anthropic.com/research/enabling-independent-research).

This argues against a one-dimensional objective such as “minimize all friction.”

### 6. Production teams are already measuring operational friction

Google Cloud has recommended operational measures such as revert / undo behavior, intervention rate, time-to-verify, and output friction for production agents.

Source: [Google Cloud — “The KPIs that actually matter for production AI agents”](https://cloud.google.com/transform/the-kpis-that-actually-matter-for-production-ai-agents).

This is industry guidance rather than peer-reviewed evidence, but it reinforces the practical need for runtime measures beyond task accuracy.

## Working friction taxonomy — and its measurement boundary

```text
TOTAL COLLABORATION FRICTION
        │
        ├── Necessary friction
        │     approval for consequential action
        │     security review
        │     evidence gate
        │
        ├── Productive friction
        │     clarification
        │     dissent / counter-plan
        │     useful verification
        │     learning / perspective shift
        │
        └── Avoidable friction
              duplicate work
              bad routing
              unnecessary retries
              preventable rework
              excessive coordination
              ambiguous ownership
```

This taxonomy is a **research labeling target**, not a shipped HyoDo classifier. HyoDo Friction Contribution v1 derives coarse operational buckets such as retry, rework, intervention, wait, resource conflict, evidence completeness, and outcome. It does not automatically know whether a particular episode was necessary, productive, or avoidable.

The `hyodo friction` command is introduced in **HyoDo 4.17.0**. Installations on 4.16.x or earlier do not expose it. See [Friction Contribution](/docs/friction-contribution/) for the exact contract and version boundary.

The first empirical version should resist collapsing the three friction classes into one scalar until measured data shows that such an aggregation is defensible.

## The proposed Wisdom Reflex loop

```text
Human wisdom corpus
(classics · KINGDOM 86-strategy project canon · proverbs · accumulated lessons)
        ↓
contextual perspective retrieval
        ↓
counter-principle retrieval
        ↓
task-structure assessment
(decomposability · sequential dependence · uncertainty · reversibility · consequence)
        ↓
collaboration topology / support-profile recommendation
        ↓
execution
        ↓
HyoDo runtime evidence
        ↓
friction + outcome measurement
        ↓
next hypothesis / calibration
```

The critical transition is from **retrieval** to **contextual application**. The system should be able to say not only “this maxim is related,” but “this principle appears more relevant than its counter-principle under these observed conditions — and the execution evidence did or did not support that choice.”

## Current project state: what exists and what does not

This page separates HyoDo from its experimental companion runtime, KINGDOM.

### HyoDo

- HyoDo has a local `hyodo.agent-event/v1` evidence ledger and policy / evidence surfaces.
- Friction Contribution v1 is implemented on the 4.17.0 line as a local-only, explicit-opt-in derived record. It does not ship a collector, uploader, or population backend.
- The contribution contract is intentionally privacy-minimized: it derives coarse task / orchestration / retry / intervention / verification / evidence buckets rather than exporting raw prompts, responses, code, paths, or local identifiers.
- HyoDo does **not** contain the KINGDOM strategy runtime and does not gain execution authority from wisdom or population evidence.
- The current event model has one optional `parent_event_id` per event plus separate `evidence_refs`. It can represent fan-out through sibling events, but it does **not** explicitly model an arbitrary multi-parent execution join as multiple parent edges. That limitation should be measured before the schema is expanded.

### KINGDOM experimental runtime

At the verified KINGDOM snapshot used for this note, several ingredients already exist:

- a project-specific **86-strategy ↔ EROS ↔ lessons ↔ Korean-proverb SSOT**: [86-stratagem-eros-map.json](https://github.com/lofibrainwav/kingdom/blob/28f5c33700f4832d697578086db79f82bdbc22bf/.claude/skills/strategy/86-stratagem-eros-map.json);
- a [command doctrine](https://github.com/lofibrainwav/kingdom/blob/28f5c33700f4832d697578086db79f82bdbc22bf/agent/core/command-doctrine.js) that retrieves strategy principles from task text;
- a [Wisdom Imprint](https://github.com/lofibrainwav/kingdom/blob/28f5c33700f4832d697578086db79f82bdbc22bf/agent/core/wisdom-imprint.js) model that keeps interpretation separate from measured reality and forbids direct EROS score mutation from the wisdom layer; and
- an observation-only KINGDOM → HyoDo bridge proposed in [KINGDOM PR #773](https://github.com/lofibrainwav/kingdom/pull/773).

But the key gap remains open:

> **There is no measured, automatic Wisdom Reflex router that converts contextual wisdom + task structure into a support profile / collaboration topology and then demonstrates better outcomes or lower avoidable friction.**

The current command doctrine is still primarily keyword-driven and currently stamps its mission execution mode as sequential. Parallel-agent capabilities exist elsewhere in KINGDOM, but the wisdom layer has not yet been empirically shown to select among single, replica-parallel, structural-parallel, or diverge→converge topologies.

## Evidence status: do not count fixtures as reality

The observation bridge’s own contract explicitly distinguishes CI fixtures from measured production evidence. **Measured KINGDOM ↔ HyoDo Run #1 is now counted as an observability baseline only**; it does not establish ACL effectiveness, a friction reduction, or a Wisdom Reflex result. See the [receipt](https://github.com/lofibrainwav/HyoDo/blob/main/docs/research/MEASURED_RUN_1_2026-09-08.md).

That is the next scientific gate. A useful result is allowed to be disappointing — for example, missing evidence completeness, unexpectedly sequential execution, or no measurable friction reduction. Those are measurements, not failures to hide.

## Minimal Wisdom Reflex benchmark

The first benchmark should test contextual use, not memorization.

| Scenario | Expected reasoning pressure | Candidate topology |
| --- | --- | --- |
| Large set of independent transformations | “many hands” can help; low shared state | structural parallelism |
| One shared-state migration / single-writer operation | coordination and ownership dominate | single authority / serialized write |
| Uncertain architecture choice | benefit from diverse hypotheses before commitment | replica planning → compare → converge |
| Consequential destructive operation | reversibility and evidence dominate speed | extra verification / approval support |

For each case, measure:

- task success / outcome quality;
- avoidable retry and rework where defensibly labeled;
- human intervention;
- verification failure;
- evidence completeness;
- coordination overhead;
- wall-clock latency and token / compute cost;
- productive clarification / useful dissent where observable;
- topology and support profile selected;
- whether a counter-principle was considered; and
- **authority violations — target: zero**.

## Baselines designed to disprove the Wisdom Reflex

A useful experiment must make it possible for the wisdom layer to lose. At minimum, compare:

```text
A. fixed sequential / fixed-support baseline
B. task-structure heuristic only
C. generic semantic retrieval, no project wisdom corpus
D. wisdom retrieval without counter-principle
E. wisdom + counter-principle + task structure
```

The important question is not whether E can produce plausible rationales. It is whether E improves outcomes, calibration, or friction **beyond B and C after accounting for extra latency, tokens, and coordination cost**.

## Falsifiable hypotheses

1. **Topology alignment:** task-structure-aware topology selection will outperform a fixed orchestration mode on mixed sequential / parallelizable tasks.
2. **Wisdom increment:** a contextual wisdom prior will add measurable value beyond a task-structure-only router; if it does not, the custom wisdom layer is not justified by this benchmark.
3. **Context over recall:** contextual wisdom application will outperform keyword-only strategy retrieval on topology-choice accuracy.
4. **Counter-principle check:** explicitly retrieving a countervailing principle will reduce over-application of a single maxim enough to justify its added cost.
5. **Support without authority:** ACL can reduce avoidable intervention / rework without increasing unsafe or unproven execution.
6. **Measurement honesty:** some friction will correlate with better outcomes; therefore a useful friction model must distinguish productive / necessary / avoidable classes rather than optimizing only for lower totals.

## Threats to validity

Before treating a positive result as evidence for “wisdom,” test these alternatives:

- the gain may come entirely from **task-structure classification**, not cultural or historical wisdom;
- a generic semantic router may match the project corpus;
- counter-principle retrieval may improve rhetoric while adding cost without improving outcomes;
- topology effects may dominate all support-allocation effects;
- labels for productive / necessary / avoidable friction may be subjective or outcome-leaking;
- repeated tasks, models, or operators may create non-independent samples;
- results may not generalize across model families, task classes, languages, or cultural corpora; and
- a corpus may encode historical bias or obsolete norms even when retrieval quality is technically high.

These are not footnotes to remove later; they are part of the benchmark design.

## What would count as progress

```text
HyoDo friction-capable instrument release
        ↓
KINGDOM observation bridge merged
        ↓
Measured Run #1
        ↓
~10 real runs: observability-gap audit
        ↓
30–50 real runs across task / risk / topology classes
        ↓
ACL + Wisdom Reflex ablations
        ↓
only then: population contribution experiments
```

Population contribution remains downstream of local measurement. The system should learn which coarse fields are actually useful **before** building a network collector.

## Novelty boundary

This field note does **not** claim that HyoDo invented multi-agent coordination, AI metacognition, cultural reasoning, human–AI friction, adaptive autonomy, or proverb-based reasoning. Each is an active research area.

The narrower research opportunity is to test whether these currently adjacent strands can be joined into one auditable loop:

> **provenance-governed metacognitive strategy prior → contextual support profile / topology choice → privacy-minimized runtime friction evidence → falsifiable calibration, while authority remains local and separately governed.**

In the sources reviewed above, the components are largely studied separately. That observation is a research map, not a priority claim. The project still has to earn its contribution through measured results and competitive baselines.

## Source discipline

External quantitative claims on this page link to the source that reports them, with primary papers preferred where practical and institutional summaries treated as companion context. Project implementation claims link to exact repository snapshots or public PRs where possible. Synthetic fixtures, release-preparation receipts, design intent, and plausible rationales are never counted as measured ACL effectiveness.
