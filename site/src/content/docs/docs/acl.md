---
title: ACL — Adaptive Collaboration Layer
description: A working field note on evidence-grounded support allocation, human wisdom as a metacognitive prior, and measurable collaboration friction.
---

> **Status — working research field note, verified 2026-09-08.** ACL here means **Adaptive Collaboration Layer**, not the Association for Computational Linguistics. This page is not a claim of peer review, venue submission, or first-in-field novelty.

# Adaptive Collaboration Layer

HyoDo measures what happened. ACL asks a different question:

> **How much support should this human–AI workflow need in this context?**

The research goal is not maximum autonomy and not minimum human involvement. It is to reduce **avoidable friction** while preserving **necessary friction** and allowing **productive friction** when clarification, dissent, or verification improves the outcome.

## Hard separation: authority, support, proof

| Layer | Question | Responsibility |
| --- | --- | --- |
| **EROS / local authority** | **Whether?** | Is this action permitted at all? |
| **ACL / support allocation** | **How much support?** | How much supervision, explanation, parallel exploration, intervention, or verification is useful? |
| **Evidence Gate** | **Done?** | Is completion actually supported by evidence? |

The invariant is intentionally stronger than a recommendation policy:

```text
Population evidence → ACL support recommendation  ✅
Population evidence → execution authority         ❌
Population evidence → override local policy       ❌
Population evidence → override Evidence Gate      ❌
```

A common task may still require approval. A statistically successful pattern may still be blocked. A culturally familiar proverb may suggest a perspective, but it never grants authority.

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

These are not contradictory rules. They are contextual lenses. The same system may use broad parallel exploration, converge to one plan, then execute with a single authority line and many independent workers.

A compact operating hypothesis is:

> **Think widely. Decide once. Execute in parallel where independence permits. Verify independently.**

The research question is whether a culturally and historically grounded strategy prior can improve **contextual topology choice** and **support allocation** without becoming a hidden authority system.

## Why this is a real research problem in 2026

Several adjacent research strands now point at the same gap from different directions.

### 1. Agent architecture must match task structure

Google Research evaluated **180 agent configurations** and reported that multi-agent coordination helped strongly on parallelizable work but degraded sequential tasks. Their centralized architecture improved Finance-Agent performance by **80.9%** over a single agent, while multi-agent variants degraded PlanCraft by **39–70%**. A predictive model selected the optimal architecture for **87% of unseen task configurations**. The same study also found substantial error amplification in independent multi-agent setups compared with centralized orchestration.

Source: [Google Research — “Towards a science of scaling agent systems: When and why agent systems work” (2026-01-28)](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/).

This supports a narrower principle than “more agents are better”:

```text
parallelizable / decomposable → parallelism may help
sequential / tightly shared state → coordination tax may dominate
```

### 2. “Wisdom” is being separated from raw intelligence

A 2026 *Trends in Cognitive Sciences* article, **“Imagining and building wise machines: the centrality of AI metacognition,”** argues that AI capability should include metacognitive strategies such as **intellectual humility, perspective-taking, and context adaptability** — especially for problems that are novel, ambiguous, or resistant to purely analytic treatment.

Source: [Johnson et al., 2026, PubMed / Trends in Cognitive Sciences](https://pubmed.ncbi.nlm.nih.gov/41760502/).

That is close to the role proposed here for a Wisdom Reflex: not a database of answers, but a repertoire of strategies for judging **which way of thinking fits the current problem**.

### 3. Understanding a proverb is easier than using it well

EACL 2026 research on culturally grounded figurative language evaluated 22 LLMs and found a **14.07% drop** from understanding to pragmatic use. Providing contextual sentences improved pragmatic-use accuracy by **10.66%**.

Source: [Attia et al., “Beyond Understanding: Evaluating the Pragmatic Gap in LLMs’ Cultural Processing of Figurative Language,” EACL 2026](https://aclanthology.org/2026.eacl-long.341/).

This distinction matters for the project. A system that can explain a maxim but cannot select or reject it in context does not yet have the proposed reflex.

### 4. Korean cultural knowledge has the same application gap

KIM Bench contains **1,175 Korean idiom instances** and reports that models still struggle with deep semantic and contextual understanding even when larger or locally trained models perform better.

Source: [Wang, Park & Kim, “Benchmarking Korean Idiom Understanding,” RANLP 2025](https://aclanthology.org/2025.ranlp-1.156/).

Nunchi-Bench similarly reports that models often recognize cultural facts but struggle to apply them in practical scenarios; explicit cultural framing helped more than simply changing the prompt language.

Source: [Kim & Lee, “Nunchi-Bench,” Findings of ACL 2025](https://aclanthology.org/2025.findings-acl.794/).

These results make **contextual application** a better benchmark target than quote recall.

### 5. Friction can be productive

In an August 2026 program, Anthropic reported results from three external research groups using privacy-preserving analysis of roughly **250,000 Claude.ai or Claude Code conversations**. Stanford SALT researchers found that people directed and oversaw the work in nearly three-quarters of conversations and that human–AI friction was common but often **productive**: iteration helped people clarify intent, refine output, and remain engaged with the task.

Source: [Anthropic — “Enabling independent research on how people use Claude” (2026-08-26)](https://www.anthropic.com/research/enabling-independent-research).

This argues against a one-dimensional objective such as “minimize all friction.”

### 6. Production teams are already measuring operational friction

Google Cloud has recommended operational measures such as revert / undo behavior, intervention rate, time-to-verify, and output friction for production agents.

Source: [Google Cloud — “The KPIs that actually matter for production AI agents”](https://cloud.google.com/transform/the-kpis-that-actually-matter-for-production-ai-agents).

ACL therefore treats friction as an empirical runtime object, not only a philosophical metaphor.

## Working friction taxonomy

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

The first empirical version should resist collapsing these categories into one scalar until measured data shows that such an aggregation is defensible.

## The proposed Wisdom Reflex loop

```text
Human wisdom corpus
(classics · 86 strategy canon · proverbs · accumulated lessons)
        ↓
contextual perspective retrieval
        ↓
counter-principle retrieval
        ↓
task-structure assessment
(decomposability · sequential dependence · uncertainty · reversibility · consequence)
        ↓
collaboration topology / support recommendation
        ↓
execution
        ↓
HyoDo runtime evidence
        ↓
friction + outcome measurement
        ↓
next hypothesis / calibration
```

The critical transition is from **retrieval** to **contextual application**. The system should be able to say not only “this maxim is related,” but “this principle is more relevant than its counter-principle under these observed conditions — and here is the evidence after execution.”

## Current project state: what exists and what does not

This page separates HyoDo from its experimental companion runtime, KINGDOM.

### HyoDo

- HyoDo has a local `hyodo.agent-event/v1` evidence ledger and policy / evidence surfaces.
- **Friction Contribution v1** exists as a local-only, explicit-opt-in derived record. It does not ship a collector, uploader, or population backend. See [Friction Contribution](/docs/friction-contribution/).
- The contribution contract is intentionally privacy-minimized: it derives coarse task / orchestration / retry / intervention / verification / evidence buckets rather than exporting raw prompts, responses, code, paths, or local identifiers.
- HyoDo does **not** contain the KINGDOM 86-strategy runtime and does not gain execution authority from wisdom or population evidence.

### KINGDOM experimental runtime

At the verified KINGDOM snapshot used for this note, several ingredients already exist:

- an **86-strategy ↔ EROS ↔ lessons ↔ Korean-proverb SSOT**, described as a machine-readable canon rather than static prose: [86-stratagem-eros-map.json](https://github.com/lofibrainwav/kingdom/blob/28f5c33700f4832d697578086db79f82bdbc22bf/.claude/skills/strategy/86-stratagem-eros-map.json);
- a [command doctrine](https://github.com/lofibrainwav/kingdom/blob/28f5c33700f4832d697578086db79f82bdbc22bf/agent/core/command-doctrine.js) that retrieves strategy principles from task text;
- a [Wisdom Imprint](https://github.com/lofibrainwav/kingdom/blob/28f5c33700f4832d697578086db79f82bdbc22bf/agent/core/wisdom-imprint.js) model that keeps interpretation separate from measured reality and forbids direct EROS score mutation from the wisdom layer; and
- an observation-only KINGDOM → HyoDo bridge proposed in [KINGDOM PR #773](https://github.com/lofibrainwav/kingdom/pull/773).

But the key gap is still open:

> **There is no measured, automatic Wisdom Reflex router that converts contextual wisdom + task structure into collaboration topology and then demonstrates lower avoidable friction.**

The current command doctrine is still primarily keyword-driven and currently stamps its mission execution mode as sequential. Parallel-agent capabilities exist elsewhere in KINGDOM, but the wisdom layer has not yet been empirically shown to select among single, replica-parallel, structural-parallel, or diverge→converge topologies.

## Evidence status: do not count fixtures as reality

The observation bridge's own contract explicitly distinguishes CI fixtures from measured production evidence. As of this snapshot, **Measured KINGDOM ↔ HyoDo Run #1 is not yet counted**.

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
- avoidable retry and rework;
- human intervention;
- verification failure;
- evidence completeness;
- coordination overhead;
- productive clarification / useful dissent where observable;
- topology selected;
- whether a counter-principle was considered; and
- **authority violations — target: zero**.

## Falsifiable hypotheses

1. **Topology alignment:** task-structure-aware topology selection will outperform a fixed orchestration mode on mixed sequential / parallelizable tasks.
2. **Context over recall:** contextual wisdom application will outperform keyword-only strategy retrieval on topology-choice accuracy.
3. **Counter-principle check:** explicitly retrieving a countervailing principle will reduce over-application of a single maxim.
4. **Support without authority:** ACL can reduce avoidable intervention / rework without increasing unsafe or unproven execution.
5. **Measurement honesty:** some friction will correlate with better outcomes; therefore a useful friction model must distinguish productive / necessary / avoidable classes rather than optimizing only for lower totals.

## What would count as progress

```text
HyoDo instrument release
        ↓
KINGDOM observation bridge merged
        ↓
Measured Run #1
        ↓
~10 real runs: observability-gap audit
        ↓
30–50 real runs across task / risk / topology classes
        ↓
ACL ablations
        ↓
only then: population contribution experiments
```

Population contribution remains downstream of local measurement. The system should learn which coarse fields are actually useful **before** building a network collector.

## Novelty boundary

This field note does **not** claim that HyoDo invented multi-agent coordination, AI metacognition, cultural reasoning, human–AI friction, or adaptive autonomy. Each is an active research area.

The narrower research opportunity is to test whether these currently adjacent strands can be joined into one auditable loop:

> **culturally grounded metacognitive strategy prior → contextual collaboration topology / support choice → privacy-minimized runtime friction evidence → calibration, while authority remains local and separately governed.**

In the sources reviewed above, the components are largely studied separately. That observation is a research map, not a priority claim. The project still has to earn its contribution through measured results.

## Source discipline

External numbers on this page are linked to the source that reports them. Project implementation claims link to exact repository snapshots or public PRs where possible. Synthetic fixtures, release-preparation receipts, and design intent are never counted as measured ACL effectiveness.
