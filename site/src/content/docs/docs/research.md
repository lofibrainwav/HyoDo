---
title: Research
description: Working research notes behind HyoDo's evidence-grounded human–AI collaboration model.
---

> **Status — working research program, updated 2026-09-08.** This page describes research in progress. It is not a claim of peer review, submission, or acceptance by the Association for Computational Linguistics (ACL) or any other venue.

# Adaptive Collaboration Layer research program

**Reader map.** This page is the broader empirical program: benchmark status, related work, evaluation design, ablations, and publication boundary. For the focused **Wisdom Reflex + collaboration-topology** hypothesis, including corpus governance, null baselines, and threats to validity, see the [ACL field note](/docs/acl/). For the local privacy-minimized sensor contract, see [Friction Contribution](/docs/friction-contribution/).

**Working title:** *Adaptive Collaboration Layer: Evidence-Grounded Support Allocation for Human–AI Agents*

HyoDo is the local-first evidence and gate substrate. The Adaptive Collaboration Layer (ACL) is the research layer that asks: **what support profile should a human–AI workflow receive in this context?**

To avoid an overloaded acronym: **ACL on this page means Adaptive Collaboration Layer**. The Association for Computational Linguistics is written out when we refer to a publication venue.

## Three questions, three responsibilities

| Layer | Question | Responsibility |
| --- | --- | --- |
| **EROS / Authority** | **Whether?** | Is this action permitted at all? |
| **ACL / Support allocation** | **What support profile?** | What oversight, verification, explanation, exploration, or budget is appropriate? |
| **Evidence Gate** | **Done?** | Is completion actually proven by evidence? |

This separation is a hard research invariant:

> **Population evidence may influence support allocation. It must never grant execution authority.**

A task can be statistically routine and still require approval or be blocked because the local action is destructive, out of scope, or insufficiently evidenced.

## Current support model

The working ACL model combines four evidence families:

```text
local prior
    +
population prior
    +
context similarity
    +
current evidence
        ↓
ACL support-profile recommendation
```

Candidate conditioning signals include:

- prior successful executions;
- missing or incomplete evidence;
- task risk and reversibility;
- task novelty;
- confidence and calibration signals;
- cognitive-load proxies;
- retries and rework;
- verification failures;
- human interventions;
- approval wait;
- resource conflicts; and
- orchestration pattern.

The output is a **support recommendation**, not an authorization token. The research should not assume that support can be compressed into one scalar until data shows that doing so preserves the useful distinctions among oversight, verification, explanation, exploration, and resource budget.

## Instrument version boundary

HyoDo's local evidence, gate, policy, report, and inspection surfaces predate the friction instrument. The `hyodo friction` command is introduced in **HyoDo 4.17.0**; HyoDo 4.16.x and earlier do not expose that command.

That distinction matters for reproducibility: a paper, benchmark, or measured run must record the exact installed HyoDo version rather than treating the development branch and the latest published package as interchangeable.

Friction Contribution v1 defines a local-only, explicit-opt-in derived measurement surface before any population collector exists. Raw prompts, model responses, source code, diffs, credentials, file paths, email bodies, and raw event bodies are not population features by default.

Before any population signal is consumed by ACL, it must pass validation, aggregation, versioning, deduplication, and bias / poisoning checks.

## Research status

The research program has completed three internal stages:

1. **Research framing and terminology.** The system was translated from internal operating language into human-centered agent research terms, with KRO as a typed runtime/process backbone.
2. **Runtime experiments.** ACT / ASK / ABSTAIN scenarios and evidence-layer traces were exercised to establish a reproducible trace format.
3. **Trace-based evaluation baseline.** A sealed benchmark baseline established a versioned dataset, scoring metrics, negative controls, and append-only benchmark evidence.

The current stage is a **working-paper refresh plus measured-runtime expansion**: update the research claim against the 2025–2026 literature, connect HyoDo friction evidence to support allocation, and produce a broader measured empirical results table before any venue submission claim.

## Current empirical baseline — useful, but not submission-grade

The existing sealed baseline is intentionally small:

| Provenance | n | Current result | What it actually proves |
| --- | ---: | --- | --- |
| Synthetic | 14 | ACT / ASK / ABSTAIN precision = 1.0 in the sealed fixture set | The benchmark machinery is deterministic against its specification-derived fixtures; **not** real-world system quality. |
| Measured | 3 | All three are external-write cases labeled ASK | The measured trace path works, but there is no measured ACT or ABSTAIN coverage yet. |

The benchmark integrity layer also passed its sealed regression suites (**9/9** vessel checks and **6/6** trace-experiment checks) and surfaced one definition-to-implementation design debt around an unreachable evidence-missing decision path.

That is enough to say **the evaluation vessel exists and catches at least one real design gap**. It is not enough to say ACL's support-allocation policy or Wisdom Reflex has been empirically validated.

Before submission, the measured set must grow across task classes, risk levels, orchestration patterns, models/environments, and support profiles, with genuine ACT / ASK / ABSTAIN diversity and failure cases. Synthetic perfect scores must remain separated from measured evidence.

## Updated research claim

Recent work already studies when agents should defer to humans, how autonomy levels can be classified, how authorization can be enforced, how multi-agent topology interacts with task structure, and how metacognitive strategies can be evaluated. The claim therefore cannot simply be “agents should know when to ask” or “more agents are better.”

The working hypothesis is narrower:

> **Human–AI agent systems can allocate support more effectively when local experience, population experience, context similarity, current evidence, and task structure are combined, while execution authority and proof-of-completion remain independently governed.**

The Wisdom Reflex is an additional hypothesis, not an assumed ingredient: a provenance-governed strategy prior must outperform simpler task-structure and semantic-routing baselines after accounting for cost, or it has not earned a place in the model.

## Related work we have to beat or complement

- [HILA — Adaptive Collaboration with Humans (2026)](https://arxiv.org/abs/2603.07972) learns a metacognitive policy for autonomous solving versus human deferral in multi-agent systems.
- [Levels of Autonomy for AI Agents (2025)](https://arxiv.org/abs/2506.12469) defines five autonomy levels through changing human roles: operator, collaborator, consultant, approver, and observer.
- [Measuring AI agent autonomy in practice (Anthropic, 2026)](https://www.anthropic.com/research/measuring-agent-autonomy) measures real human–agent autonomy patterns across millions of interactions.
- [Towards a Science of Scaling Agent Systems](https://arxiv.org/abs/2512.08296) shows that coordination topology must match measurable task properties and that multi-agent overhead can harm sequential work.
- [Imagining and building wise machines: the centrality of AI metacognition](https://pubmed.ncbi.nlm.nih.gov/41760502/) treats intellectual humility, perspective-taking, and context adaptability as metacognitive strategy-selection capabilities.
- [LATTICE (2026)](https://doi.org/10.3389/frai.2026.1800407) separates planning, execution, and governance with deterministic policy enforcement and auditable authorization.
- [The Behavioral Credibility Trilemma (2026)](https://arxiv.org/abs/2605.25739) shows why confidence-gated autonomy can create incentives for inflated confidence, strengthening the case for separating support evidence from execution authority.

KRO remains useful as the typed runtime/process representation that makes intent, plan, tool use, evidence, decision, and memory inspectable. It is a method backbone, not the sole novelty claim.

## Evaluation plan

The next public-quality evaluation should report, at minimum:

| Metric | What it tests |
| --- | --- |
| Support-profile quality | Did ACL recommend an appropriate combination of oversight, verification, explanation, exploration, and budget? |
| Human intervention rate | Did the system reduce unnecessary intervention? |
| Rework / retry rate | Did lower support increase recovery work? |
| Verification failure rate | Did support allocation preserve evidence quality? |
| Evidence completeness | Was the claimed outcome backed by traceable evidence? |
| Coordination overhead | Did topology gains exceed communication / synchronization cost? |
| Wall-clock and token / compute cost | Was any improvement worth the extra resources? |
| Authority violations | Did population/local priors ever bypass policy? Target: **zero**. |
| Calibration by cohort | Does the recommendation remain reliable across task, model, environment, and orchestration cohorts? |

The friction taxonomy on the ACL field note — necessary, productive, avoidable — is an **analysis target**, not an automatically observed label in Friction Contribution v1. Any result using those classes must document who or what labeled them and how outcome leakage was controlled.

## Required ablations

The support-evidence ablation should compare at least:

```text
current evidence only
vs local prior + current evidence
vs population prior + current evidence
vs local + population + similarity + current evidence
```

The Wisdom Reflex ablation should separately compare:

```text
fixed orchestration / support
vs task-structure heuristic only
vs generic semantic retrieval
vs wisdom retrieval without counter-principle
vs wisdom + counter-principle + task structure
```

Population observations must be weighted by context similarity and uncertainty rather than treated as universal truth. A wisdom corpus must likewise be treated as provenance-governed hypotheses, not identity-derived user norms.

## Non-negotiable invariants

```text
Population evidence → ACL support recommendation  ✅
Population evidence → execution authority         ❌
Population evidence → override local policy       ❌
Population evidence → override Evidence Gate      ❌
```

Likewise, HyoDo's Integrity Score remains a **review signal**, never approval.

## Publication status

**Not submitted. Not peer reviewed. Not accepted.**

The intended path is an ACL-family human-centered NLP / LLM-agent research submission through ACL Rolling Review once the refreshed empirical evidence is strong enough. Venue timing is deliberately not treated as product truth; the research should earn submission readiness from measurements first.

## Reproducibility direction

The public artifact should ultimately include:

- versioned task and trace schemas;
- exact HyoDo / model / environment versions for every result;
- a documented support-profile labeling protocol;
- a documented friction-class labeling protocol;
- benchmark fixtures that do not contain private user data;
- evaluation and ablation scripts;
- latency / token / compute accounting;
- failure cases, null results, and contradictory evidence; and
- corpus provenance plus counter-principle links for any Wisdom Reflex experiment.

Until those artifacts exist and have been read back successfully, this page remains a **working research program**, not a finished paper.
