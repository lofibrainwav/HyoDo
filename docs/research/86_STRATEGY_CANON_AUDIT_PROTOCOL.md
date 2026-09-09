# KINGDOM 86 Strategy Canon Audit Protocol

Status: working research protocol

Purpose: preserve the existing KINGDOM 86-strategy canon while separating historical source material, later interpretations, KINGDOM-specific interpretation, and empirical evidence.

## 1. Canon boundary

The KINGDOM 86-strategy set is a project-curated canon assembled from seven source families:

1. The Art of War / Sunzi traditions
2. Three Kingdoms historical and literary traditions
3. Machiavelli / The Prince
4. Clausewitz / On War
5. East Asian ethical and relational traditions
6. The Thirty-Six Stratagems
7. KINGDOM-derived metacognitive operating lessons

The number, canonical identifier, and existing canonical name of each of the 86 entries are frozen during research evaluation.

Research must not invent a new strategy and silently assign it an existing canon number. Generated examples, NotebookLM suggestions, model-generated paraphrases, and modern analogies are non-canonical until separately reviewed and explicitly promoted.

## 2. Three immutable/separable layers

```text
SOURCE          historical primary/secondary source evidence
INTERPRETATION  append-only human/model interpretation records
CONFIDENCE      revisable empirical/contextual confidence
```

The source layer is not rewritten to fit later experiments.
Interpretations may accumulate and disagree.
Confidence may change as evidence changes.

## 3. Required audit record for every canonical strategy

Each of the 86 entries should eventually have an audit record with at least:

```yaml
canonical_id:
canonical_name:
source_family:
primary_source:
source_location:
source_confidence:
historical_notes:
translation_notes:
kingdom_interpretation:
known_alternative_interpretations:
counter_principles:
when_it_fits:
when_it_fails:
observable_signals:
recommended_move:
forbidden_authority_effect:
friction_hypothesis:
eros_relation:
evidence_status:
```

## 4. Interpretation Zettelkasten

A canonical strategy may have many interpretation notes.

Example shape:

```text
#1 Canonical strategy
  ├─ Zettel A: source-faithful military interpretation
  ├─ Zettel B: organizational interpretation
  ├─ Zettel C: agent-orchestration interpretation
  ├─ Zettel D: critical / counter-reading
  └─ Zettel E: measured KINGDOM lesson
```

Interpretation notes are append-only research objects. They should preserve provenance: author or source, edition/translation where relevant, date, uncertainty, and whether the interpretation is historical scholarship, popular interpretation, project interpretation, or measured runtime lesson.

Popularity is not truth. Citation count is not contextual fitness. A widely repeated interpretation may remain low-confidence if it is weakly grounded or performs poorly in measured use.

## 5. Counter-principle requirement

A strategy is not a universal rule. Every strategy used experimentally should be paired with one or more counter-principles or explicit failure conditions.

The research question is not:

> Is this strategy true?

It is:

> Under which observable conditions does this interpretation appear useful, and under which conditions does a competing principle dominate?

## 6. Canon versus generated suggestion

Use these labels consistently:

- `CANON`: existing KINGDOM 86 entry
- `SOURCE`: historical textual evidence
- `INTERPRETATION`: an attributed reading of the source/canon
- `PROJECT_INTERPRETATION`: KINGDOM-specific operational reading
- `HYPOTHESIS`: falsifiable when/why claim
- `GENERATED_SUGGESTION`: model-generated candidate, never canonical by default
- `MEASURED_LESSON`: interpretation or update supported by runtime evidence

## 7. Research anti-contamination rule

Do not modify the canon after seeing benchmark results in order to improve measured performance.

If a canonical entry is later found to have weak provenance, mistranslation, duplication, or historical error, record the defect explicitly. Preserve the old identifier for reproducibility and handle correction through a versioned canon change process rather than silent rewriting.

## 8. Relationship to authority

Historical prestige, cultural familiarity, citation frequency, EROS score, and measured past success do not grant execution authority.

```text
strategy evidence → interpretation/recommendation  allowed
strategy evidence → local policy override          forbidden
strategy evidence → human approval bypass          forbidden
strategy evidence → Evidence Gate override         forbidden
```

The canon is a reasoning prior, not a sovereign.
