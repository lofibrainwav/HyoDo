---
title: Support allocation field note
description: A research-only field note on evidence-grounded support profiles, strategy priors, collaboration topology, and measurable friction.
---

> **Status — research-only field note, reviewed 2026-09-20.**
> This is not a shipped HyoDo capability, runtime, classifier, or authority layer.
> It is not a claim of peer review, venue submission, first-in-field novelty, or
> measured effectiveness.

# Support allocation field note

**Reader map.** This is the focused field note for the **strategy-prior +
collaboration-topology** hypothesis. See [Research](/docs/research/) for the
broader empirical program, benchmark status, related work, evaluation design,
and publication boundary. See
[Friction Contribution](/docs/friction-contribution/) for the local,
privacy-minimized measurement contract.

The page keeps its historical URL so existing links do not break. The public
terminology is intentionally generic: the research question matters more than
an internal project name.

## Product boundary first

HyoDo measures and records evidence. The research described here asks a
different question: **what support profile should a human–AI workflow receive
in this context?**

Three responsibilities stay separate:

| Responsibility | Question | Meaning |
| --- | --- | --- |
| **Authorization policy** | **Whether?** | Is this action permitted at all? |
| **Support allocation** | **What support profile?** | What oversight, verification, explanation, exploration, or budget is useful? |
| **Evidence validation** | **Done?** | Is completion actually supported by evidence? |

This separation is a hard invariant:

```text
Population evidence → support recommendation  ✅
Population evidence → execution authority     ❌
Population evidence → override local policy   ❌
Population evidence → override evidence gate  ❌
```

A support recommendation is advisory. The integrating host still owns
execution and enforcement.

## Working support model

The current hypothesis combines four evidence families:

```text
local prior
    +
population prior
    +
context similarity
    +
current evidence
        ↓
support-profile recommendation
```

Candidate conditioning signals include:

- prior successful executions;
- missing or incomplete evidence;
- task risk and reversibility;
- task novelty;
- retries and rework;
- verification failures;
- human interventions;
- approval wait;
- resource conflicts; and
- orchestration pattern.

The output should remain a profile rather than being forced into one scalar
unless data shows that a scalar preserves the distinctions that matter.

## Strategy-prior hypothesis

Human communities have compressed recurring experience about timing,
cooperation, restraint, trust, conflict, verification, and responsibility into
texts, maxims, proverbs, and stories. The research question is whether a
provenance-governed strategy corpus can provide a useful metacognitive prior
for choosing *how to reason and collaborate* without becoming authority.

A usable strategy prior must:

1. preserve source provenance;
2. expose counter-principles rather than presenting one maxim as universal;
3. remain conditioned on task structure and current evidence;
4. never grant execution authority; and
5. beat simpler baselines after accounting for cost.

If it cannot do that, it has not earned a place in the model.

## Friction as a research target

Friction Contribution v1 observes coarse operational signals such as retries,
rework, intervention, wait, resource conflict, evidence completeness, and
outcome. It does **not** automatically know whether friction was necessary,
productive, or avoidable.

Those three classes are a **research labeling target**. They are not a shipped HyoDo
classifier. Any experiment using them must document who or what produced the
label and how outcome leakage was controlled. HyoDo is **not a shipped HyoDo classifier**
for those categories.

Examples:

- a retry may be productive if it catches a real defect;
- an approval wait may be necessary for a destructive action;
- fewer interventions may be harmful if operators lose the ability to notice
  failures.

The research therefore measures outcomes and evidence quality, not merely
whether interaction counts went down.

## Proposed strategy-prior loop

```text
provenance-governed strategy corpus
        ↓
retrieve candidate principles + counter-principles
        ↓
combine with task structure + current evidence
        ↓
recommend support profile / collaboration topology
        ↓
observe outcome, cost, rework, and evidence quality
        ↓
evaluate against simpler baselines
```

There is no automatic router in the shipped HyoDo product that performs this
loop.

## Minimal benchmark

A useful benchmark needs materially different task classes and collaboration
patterns rather than one synthetic happy path. At minimum, report:

- task class and reversibility;
- model / environment version;
- support profile;
- orchestration pattern;
- human intervention;
- retry / rework;
- verification failures;
- evidence completeness;
- wall-clock and token / compute cost; and
- final outcome.

Measured runs and synthetic fixtures must remain separate.

## Baselines designed to disprove the strategy-prior hypothesis

The strategy prior should be compared against:

```text
fixed support / orchestration
vs task-structure heuristic
vs generic semantic retrieval
vs strategy retrieval without counter-principle
vs strategy + counter-principle + task structure
```

A more complicated method is not better merely because it is more
philosophically interesting. It must improve measured outcomes or reduce
avoidable burden enough to justify its cost.

## Related work boundary

Relevant work already covers human deferral, autonomy levels, dynamic
oversight, topology selection, authorization, and metacognitive strategy
selection. The contribution cannot simply be "agents should know when to ask"
or "more agents are better."

One useful cultural-context benchmark is
[Kim & Lee, “Nunchi-Bench,” Findings of the Association for Computational Linguistics 2025](https://aclanthology.org/2025.findings-acl.794/).
The broader [Research](/docs/research/) page tracks the comparison set used for
the working paper.

## Threats to validity

- **Selection bias:** measured tasks may overrepresent one workflow or risk
  class.
- **Outcome leakage:** a friction label produced after seeing the result may
  encode the answer.
- **Model drift:** provider and model updates can change the operating regime.
- **Operator adaptation:** people learn the system, so intervention rates are
  not stationary.
- **Cost blindness:** a small quality gain may not justify extra latency or
  compute.
- **Corpus bias:** a strategy source can reflect one culture, era, or author;
  counter-principles and provenance are required.
- **Authority leakage:** no empirical prior may bypass local authorization.

## Publication boundary

This is a working research note. It is **not submitted, not peer reviewed, and
not accepted**. Publication readiness should be earned from broader measured
evidence, reproducible evaluation, ablations, failure cases, and explicit
limits rather than from a target venue name.
