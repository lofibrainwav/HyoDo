# Wisdom Reflex Decision Protocol

Status: working research protocol

Purpose: preserve the current research design for turning a fixed strategy canon plus plural interpretations into a contextual, falsifiable recommendation without transferring execution authority.

## 1. Core loop

```text
historical / strategic sources
        ↓
KINGDOM 86-strategy canon
        ↓
append-only interpretation Zettelkasten
        ↓
contextual retrieval
        ↓
Top-3 interpretation candidates
        ↓
EROS evaluation: Truth · Goodness · Beauty · Humanity · Filial/Relational Responsibility · Spirit/Generativity
        ↓
weighted geometric mean
        ↓
working strategy recommendation
        ↓
authority / policy remains separate
        ↓
execution
        ↓
Evidence Gate
        ↓
HyoDo runtime friction + outcome measurement
        ↓
posterior confidence update
```

The system does not assume that old, famous, or culturally familiar interpretations are correct. Historical and popular interpretations supply priors; measured reality is allowed to lower their confidence.

## 2. Interpretation retrieval

For a current context `c`, retrieve multiple interpretations linked to relevant canonical strategies.

Do not select the single most popular interpretation. Rank candidates by contextual usefulness using evidence such as:

- fidelity to the primary source;
- provenance and independence of supporting interpretations;
- semantic/context similarity;
- observable task structure;
- prior measured performance in comparable contexts;
- counter-evidence;
- uncertainty.

The working retrieval target is the top three interpretations, not an immediate Top-1 commitment.

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

Top-3 is a research design choice, not yet a validated optimum. It must be compared with Top-1, larger candidate sets, and simpler baselines.

## 3. EROS as the judgment lens

At decision time, candidate interpretations are evaluated through six EROS dimensions:

- Truth
- Goodness
- Beauty
- Humanity
- Filial / relational responsibility
- Spirit / generativity

EROS is an evaluation lens, not a source of historical truth and not an execution-authority mechanism.

Each candidate interpretation `h` receives a context-dependent vector:

```text
x(h,c) = [truth, goodness, beauty, humanity, relational, generativity]
```

Scores should be evidence-backed where possible. A score without an inspectable rationale or evidence record is a hypothesis, not a measured fact.

## 4. Weighted geometric mean

The candidate ranking function is a weighted geometric mean rather than an arithmetic mean:

```text
S(h | c) = Π_i x_i(h,c) ^ w_i(c)
```

subject to:

```text
Σ_i w_i(c) = 1
```

The motivation is non-compensation: a severe weakness on one important dimension should not be easily hidden by very high scores on unrelated dimensions.

Context-dependent weights are permitted. For example, a consequential destructive operation may assign more weight to truth, goodness, humanity, and relational responsibility; a creative exploration task may assign more weight to beauty and generativity.

Weight selection itself is a research object and must be versioned, inspectable, and ablated. EROS weights must never be silently tuned after seeing benchmark outcomes.

Zero or near-zero values require an explicit numerical policy because geometric means are sensitive to them. That policy must be documented before confirmatory experiments.

## 5. Candidate strategy record

A strategy interpretation used by the reflex should expose:

```yaml
canonical_id:
interpretation_id:
source_provenance:
interpretation_text:
counter_principles:
when_it_fits:
when_it_fails:
observable_signals:
eros_scores:
eros_weights:
weighted_geometric_score:
score_rationale:
recommended_move:
forbidden_authority_effect:
friction_hypothesis:
empirical_confidence:
```

## 6. Recommendation, not authority

The output of the Wisdom Reflex is a recommendation or perspective ranking.

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
- mutate EROS authority state merely because a strategy scored highly.

## 7. Measurement and posterior update

Historical interpretation confidence is a prior, not the final answer.

After execution, HyoDo evidence should be used to evaluate consequences such as:

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

The measured result can update empirical confidence for an interpretation in comparable contexts.

```text
historical / interpretive prior
          +
measured runtime evidence
          ↓
contextual posterior confidence
```

Do not rewrite the original source or interpretation text when confidence changes. Update the confidence/evidence layer.

## 8. Null hypothesis

The default research null is deliberately hostile to the custom wisdom layer:

> Task-structure heuristics and generic semantic routing are sufficient; the 86 Strategy Canon provides no incremental orchestration value.

The canon earns inclusion only if it improves a matched-budget outcome after accounting for extra tokens, latency, coordination, and verification cost.

## 9. Required baselines

At minimum compare:

```text
A. fixed orchestration / fixed support
B. task-structure heuristic only
C. generic semantic routing
D. 86-strategy retrieval without counter-principle
E. 86-strategy + counter-principle
F. 86-strategy + counter-principle + observable signals + EROS ranking
G. equivalent modern generic principles
H. shuffled / corrupted strategy control
```

The last two controls separate the value of structured conditional reasoning from the value, if any, of historical/cultural provenance.

## 10. Two distinct scientific questions

Do not collapse these questions:

1. Does a paired, falsifiable strategy representation (`principle + counter-principle + when_it_fails + observable signals`) improve contextual orchestration?
2. If yes, does the historically grounded KINGDOM 86-strategy corpus outperform an equivalent set of modern generic principles?

Possible result:

```text
structured conditional strategy representation  useful
historical provenance                         no added value
```

That is a valid and informative result.

## 11. Anti-overfitting and reproducibility

- Freeze canon version before confirmatory evaluation.
- Freeze interpretation snapshot before confirmatory evaluation.
- Freeze EROS weight policy before confirmatory evaluation.
- Preserve null results and failed interpretations.
- Separate synthetic fixtures from measured runtime evidence.
- Record exact model, HyoDo version, KINGDOM version, task, support profile, and budget.
- Do not label friction as productive/necessary/avoidable from telemetry alone without a documented labeling or causal protocol.

## 12. One-line research definition

> Wisdom Reflex is retrieval + contrast + EROS-weighted convergence + measured reflux, with source, authority, and evidence boundaries kept separate.
