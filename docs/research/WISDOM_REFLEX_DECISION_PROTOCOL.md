# Wisdom Reflex Decision Protocol

Status: working research protocol

Purpose: preserve the current research design for testing whether a fixed strategy canon plus plural interpretations can improve contextual recommendations without transferring execution authority or silently redefining the existing KINGDOM EROS system.

## 1. What is existing versus proposed

Existing KINGDOM state includes:

- a fixed 86-strategy project canon;
- a declared 7-source strategy ROOT;
- strategy ↔ EROS mappings;
- a doctrine of one primary principle plus one checking/counter principle;
- the canonical EROS six axes 진·선·미·인·효·영;
- a weighted geometric-mean EROS calculation in the current governance system.

Proposed research additions from the 2026-09-08 discussion include:

- multiple attributed interpretation Zettels per canonical strategy;
- contextual retrieval of several interpretation candidates;
- **Top-3** as an initial experimental candidate-set size;
- contrasting those candidates before convergence;
- testing whether EROS-aligned evaluation helps choose among interpretations;
- updating an interpretation's empirical confidence from measured runtime evidence.

Top-3 is not an existing KINGDOM canon rule and is not assumed optimal.

## 2. Core research loop

```text
historical / strategic sources
        ↓
KINGDOM 86-strategy canon
        ↓
append-only interpretation Zettelkasten
        ↓
contextual retrieval
        ↓
multiple interpretation candidates
(Top-3 is the first proposed experimental setting)
        ↓
contrast / counter-reading / failure-condition check
        ↓
EROS-aligned evaluation using 진·선·미·인·효·영
        ↓
weighted geometric-mean ranking experiment
        ↓
working strategy recommendation
        ↓
existing authority / policy remains separate
        ↓
execution
        ↓
Evidence Gate
        ↓
HyoDo runtime friction + outcome measurement
        ↓
evidence-updated interpretation confidence
```

The system does not assume that old, famous, or culturally familiar interpretations are correct. Historical and popular interpretations supply candidate priors; measured reality is allowed to lower their empirical confidence.

Do not use the word `posterior` as a formal Bayesian claim unless a probabilistic model and update rule have actually been specified and calibrated.

## 3. Interpretation retrieval

For a current context `c`, retrieve multiple interpretations linked to relevant canonical strategies.

Do not select the single most popular interpretation. Candidate retrieval may consider evidence such as:

- fidelity to the primary source;
- provenance and independence of supporting interpretations;
- semantic/context similarity;
- observable task structure;
- prior measured performance in comparable contexts;
- counter-evidence;
- uncertainty.

The first proposed candidate-set size is three:

```text
context
  ↓
interpretation candidate 1
interpretation candidate 2
interpretation candidate 3
  ↓
contrast / counter-argument / failure-condition check
  ↓
convergence
```

This Top-3 setting is a research design choice, not a validated optimum. It must be compared with Top-1, larger candidate sets, and simpler baselines.

## 4. Canonical EROS vocabulary

Use the current KINGDOM canonical virtue names rather than inventing alternate English glosses:

- 진 — `truth`
- 선 — `goodness`
- 미 — `beauty`
- 인 — `benevolence`
- 효 — `filialPiety`
- 영 — `eternity`

Current KINGDOM glosses further describe 효 as alignment with the human commander's real purpose and peace rather than literal obedience, and 영 as record/reproduction/inheritance across future sessions or generations.

These meanings are project governance semantics. They are not historical definitions of the classical sources.

## 5. EROS-aligned judgment without creating a shadow authority system

The research hypothesis is that candidate interpretations can be compared through the six canonical EROS dimensions at decision time.

However, this must **not** silently create a second EROS authority score or mutate the production EROS state.

There are two possibilities to test explicitly:

1. **Reuse canonical EROS evaluation** through the existing governed calculator/profile where appropriate; or
2. **Use a research-only EROS-aligned suitability vector**, clearly labeled as experimental and causally excluded from execution authority.

Which path is correct is currently unresolved and must be fixed before confirmatory experiments.

A research candidate may expose:

```text
x(h,c) = [truth, goodness, beauty, benevolence, filialPiety, eternity]
```

A score without an inspectable rationale or evidence record is a hypothesis, not a measured fact.

## 6. Weighted geometric mean

The existing KINGDOM EROS governance system uses a weighted geometric mean. The research proposal is to test whether the same non-compensatory form is useful for interpretation ranking:

```text
S(h | c) = Π_i x_i(h,c) ^ w_i(c)
```

subject to:

```text
Σ_i w_i(c) = 1
```

The motivation is non-compensation: a severe weakness on one important dimension should not be easily hidden by very high scores on unrelated dimensions.

Important boundary: **the mathematical form is existing; applying it to interpretation ranking is proposed research.**

The current KINGDOM runtime also has canonical/profile-owned EROS weights and thresholds. This research protocol must not duplicate or silently fork them. If an experiment uses different weights, they must be labeled research weights, versioned, frozen before evaluation, and kept out of the execution-authority path.

Any zero-value behavior must likewise respect a predeclared numerical policy. Do not infer production BLOCK semantics for a research-only ranking unless the official EROS gate is actually being invoked.

## 7. Candidate interpretation record

A strategy interpretation used by the research reflex should expose:

```yaml
canonical_id:
interpretation_id:
source_provenance:
interpretation_text:
interpretation_type:
counter_principles:
when_it_fits:
when_it_fails:
observable_signals:
eros_alignment:
eros_weight_source:
ranking_score:
score_rationale:
recommended_move:
forbidden_authority_effect:
friction_hypothesis:
empirical_confidence:
```

Do not call a research ranking score the canonical `EROS score` unless it is actually produced by the canonical EROS calculator under its governed contract.

## 8. Recommendation, not authority

The output of the Wisdom Reflex research layer is a recommendation or perspective ranking.

It may recommend, for example:

- more or less exploration;
- single versus parallel execution;
- replica planning before convergence;
- deeper verification;
- additional human review;
- a lower resource budget;
- a different tool or skill class.

It may not:

- grant execution permission;
- bypass local policy;
- substitute for required human approval;
- lower an Evidence Gate;
- mutate production EROS authority state merely because a strategy ranked highly.

## 9. Measurement and confidence update

Historical interpretation confidence is a prior assumption, not the final answer.

After execution, HyoDo evidence can help evaluate consequences such as:

- task success / outcome quality;
- retry and rework;
- verification failures;
- evidence completeness;
- human intervention;
- approval wait;
- coordination overhead;
- latency and token / compute cost;
- authority violations;
- defensibly labeled productive / necessary / avoidable friction.

The measured result may update empirical confidence for an interpretation in comparable contexts.

```text
historical / interpretive starting confidence
          +
measured runtime evidence
          ↓
evidence-updated contextual confidence
```

Do not rewrite the original source or interpretation text when confidence changes. Update only the confidence/evidence layer.

## 10. Null hypothesis

The default research null is deliberately hostile to the custom wisdom layer:

> Task-structure heuristics and generic semantic routing are sufficient; the 86 Strategy Canon provides no incremental orchestration value.

The canon earns an empirical role only if it improves a matched-budget outcome after accounting for extra tokens, latency, coordination, and verification cost.

## 11. Required baselines

At minimum compare:

```text
A. fixed orchestration / fixed support
B. task-structure heuristic only
C. generic semantic routing
D. current KINGDOM primary-principle + checking-principle behavior
E. richer interpretation retrieval without EROS-aligned ranking
F. richer interpretations + counter-reading + observable signals
G. F + EROS-aligned weighted-geometric ranking
H. equivalent modern generic principles
I. shuffled / corrupted strategy control
```

The last two controls separate the value of structured conditional reasoning from the value, if any, of historical/cultural provenance.

## 12. Two distinct scientific questions

Do not collapse these questions:

1. Does a richer, falsifiable interpretation representation (`interpretation + counter-reading + when_it_fails + observable signals`) improve contextual orchestration beyond the **existing** KINGDOM primary/check-principle behavior and simpler routers?
2. If yes, does historically grounded interpretation provenance add value beyond an equivalent set of modern generic principles?

Possible result:

```text
structured conditional interpretation  useful
historical provenance                   no added value
```

That is a valid and informative result.

## 13. Anti-overfitting and reproducibility

- Freeze canon version before confirmatory evaluation.
- Freeze interpretation snapshot before confirmatory evaluation.
- Freeze any research ranking-weight policy before confirmatory evaluation.
- Preserve null results and failed interpretations.
- Separate synthetic fixtures from measured runtime evidence.
- Record exact model, HyoDo version, KINGDOM version, task, support profile, and budget.
- Do not label friction as productive/necessary/avoidable from telemetry alone without a documented labeling or causal protocol.
- Do not reinterpret existing KINGDOM behavior as a new ACL contribution merely because the research vocabulary changed.

## 14. One-line research definition

> Wisdom Reflex research tests whether attributed interpretation retrieval + contrast + EROS-aligned convergence + measured reflux adds value beyond the existing KINGDOM strategy doctrine and simpler routing baselines, while keeping source, authority, and evidence boundaries separate.
