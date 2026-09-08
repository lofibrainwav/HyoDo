---
title: Research
description: Working research notes behind HyoDo's evidence-grounded human–AI collaboration model.
---

> **Status — working research note, updated 2026-09-08.** This page describes research in progress. It is not a claim of peer review, submission, or acceptance by the Association for Computational Linguistics (ACL) or any other venue.

# Adaptive Collaboration Layer

**Working title:** *Adaptive Collaboration Layer: Evidence-Grounded Support Allocation for Human–AI Agents*

HyoDo is the local-first evidence and gate substrate. The Adaptive Collaboration Layer (ACL) is the research layer that asks a different question: **how much support should a human–AI workflow need in this context?**

To avoid an overloaded acronym: **ACL on this page means Adaptive Collaboration Layer**. The Association for Computational Linguistics is written out when we refer to a publication venue.

## Three questions, three responsibilities

| Layer | Question | Responsibility |
| --- | --- | --- |
| **EROS / Authority** | **Whether?** | Is this action permitted at all? |
| **ACL / Support allocation** | **How much support?** | How much supervision, explanation, intervention, or collaboration is appropriate? |
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
ACL support recommendation
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

The output is a **support recommendation**, not an authorization token.

## Why HyoDo matters to the research

HyoDo v4.16.0 already provides a local-first surface for gates, event records, policy decisions, evidence links, reports, and inspection. That makes it possible to study collaboration from traceable runtime evidence instead of relying only on self-reported model confidence.

The next empirical step is to derive friction signals locally and test whether they predict when more or less support is useful.

A future population prior may use **explicitly opted-in, privacy-transformed friction contributions**. The proposed contract is derived-metrics-first: raw prompts, model responses, source code, diffs, credentials, file paths, email bodies, and raw event bodies are not population features by default.

Before any population signal is consumed by ACL, it must pass validation, aggregation, versioning, and bias / poisoning checks.

## Research status

The research program has already completed three internal stages:

1. **Research framing and terminology.** The system was translated from internal operating language into human-centered agent research terms, with KRO as a typed runtime/process backbone.
2. **Runtime experiments.** ACT / ASK / ABSTAIN scenarios and evidence-layer traces were exercised to establish a reproducible trace format.
3. **Trace-based evaluation baseline.** A sealed benchmark baseline established a versioned dataset, scoring metrics, negative controls, and append-only benchmark evidence.

The current stage is a **working-paper refresh**: update the research claim against the 2025–2026 literature, connect HyoDo friction evidence to support allocation, and produce a broader measured empirical results table before any venue submission claim.

## Current empirical baseline — useful, but not submission-grade

The existing sealed baseline is real, but intentionally small:

| Provenance | n | Current result | What it actually proves |
| --- | ---: | --- | --- |
| Synthetic | 14 | ACT / ASK / ABSTAIN precision = 1.0 in the sealed fixture set | The benchmark machinery is deterministic against its specification-derived fixtures; **not** real-world system quality. |
| Measured | 3 | All three are external-write cases labeled ASK | The measured trace path works, but there is no measured ACT or ABSTAIN coverage yet. |

The benchmark integrity layer also passed its sealed regression suites (**9/9** vessel checks and **6/6** trace-experiment checks) and correctly surfaced one definition-to-implementation design debt around an unreachable evidence-missing decision path.

That is enough to say **the evaluation vessel exists and catches at least one real design gap**. It is not enough to say ACL's support-allocation policy has been empirically validated.

Before submission, the measured set must grow across task classes, risk levels, orchestration patterns, models/environments, and support levels, with genuine ACT / ASK / ABSTAIN diversity and failure cases. Synthetic perfect scores must remain separated from measured evidence.

## Updated research claim

Recent work already studies when agents should defer to humans, how autonomy levels can be classified, and how authorization can be enforced. Our narrower claim is therefore not simply “agents should know when to ask.”

The working hypothesis is:

> **Human–AI agent systems can allocate support more effectively when local experience, population experience, context similarity, and current evidence are combined, while execution authority and proof-of-completion remain independently governed.**

This gives us a falsifiable evaluation target: support allocation should reduce unnecessary intervention and rework **without** increasing unsafe or unproven execution.

## Related work we now have to beat or complement

- [HILA — Adaptive Collaboration with Humans (2026)](https://arxiv.org/abs/2603.07972) learns a metacognitive policy for autonomous solving versus human deferral in multi-agent systems.
- [Levels of Autonomy for AI Agents (2025)](https://arxiv.org/abs/2506.12469) defines five autonomy levels through changing human roles: operator, collaborator, consultant, approver, and observer.
- [Measuring AI agent autonomy in practice (Anthropic, 2026)](https://www.anthropic.com/research/measuring-agent-autonomy) measures real human–agent autonomy patterns across millions of interactions.
- [LATTICE (2026)](https://doi.org/10.3389/frai.2026.1800407) separates planning, execution, and governance with deterministic policy enforcement and auditable authorization.
- [The Behavioral Credibility Trilemma (2026)](https://arxiv.org/abs/2605.25739) shows why confidence-gated autonomy can create incentives for inflated confidence, strengthening the case for separating support evidence from execution authority.

KRO remains useful as the typed runtime/process representation that makes intent, plan, tool use, evidence, decision, and memory inspectable. It is a method backbone, not the sole novelty claim.

## Evaluation plan

The next public-quality evaluation should report, at minimum:

| Metric | What it tests |
| --- | --- |
| Support-allocation accuracy | Did ACL recommend an appropriate support level for the task/context? |
| Human intervention rate | Did the system reduce unnecessary intervention? |
| Rework / retry rate | Did lower support increase recovery work? |
| Verification failure rate | Did support allocation preserve evidence quality? |
| Evidence completeness | Was the claimed outcome backed by traceable evidence? |
| Authority violations | Did population/local priors ever bypass policy? Target: **zero**. |
| Calibration by cohort | Does the recommendation remain reliable across task, model, environment, and orchestration cohorts? |

Ablations should compare at least:

```text
current evidence only
vs local prior + current evidence
vs population prior + current evidence
vs local + population + similarity + current evidence
```

Population observations must be weighted by context similarity and uncertainty rather than treated as universal truth.

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
- a documented support-level labeling protocol;
- benchmark fixtures that do not contain private user data;
- evaluation scripts;
- ablation results;
- failure cases and contradictory evidence; and
- exact HyoDo / model / environment versions used for each reported result.

Until those artifacts exist and have been read back successfully, this page remains a **working research note**, not a finished paper.
