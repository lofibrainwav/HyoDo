# KINGDOM 86 Strategy Canon Audit Protocol

Status: working research protocol

Purpose: preserve the existing KINGDOM 86-strategy canon while separating the canon as KINGDOM currently declares it, historical source evidence, later interpretations, KINGDOM-specific interpretation, and empirical evidence.

Related protocols:

- [`WISDOM_REFLEX_DECISION_PROTOCOL.md`](./WISDOM_REFLEX_DECISION_PROTOCOL.md)
- [`WISDOM_REFLEX_SERIAL_PARALLEL_EXECUTION_PLAN.md`](./WISDOM_REFLEX_SERIAL_PARALLEL_EXECUTION_PLAN.md)

## 1. Canon boundary

The current KINGDOM strategy skill describes the 86-strategy system as a **7-source ROOT**:

1. The Art of War / Sunzi traditions
2. Three Kingdoms traditions
3. Machiavelli / The Prince
4. Clausewitz / On War
5. East Asian ethical and relational traditions
6. The Thirty-Six Stratagems
7. KINGDOM-derived metacognitive operating lessons

That seven-source description is a **current KINGDOM project declaration**, not proof that every one of the 86 entries has already been historically audited against a primary source. The purpose of this protocol is to perform that audit without rewriting the object being studied.

The number, canonical identifier, and existing canonical name of each of the 86 entries are frozen during research evaluation.

Research must not invent a new strategy and silently assign it an existing canon number. Generated examples, NotebookLM suggestions, model-generated paraphrases, and modern analogies are non-canonical until separately reviewed and explicitly promoted through a versioned canon process.

## 2. Three separable layers

```text
CANON           current KINGDOM identifier/name and project mapping
SOURCE          primary/secondary source evidence and provenance
INTERPRETATION  append-only attributed readings
CONFIDENCE      revisable evidence-backed confidence
```

The current canon is frozen for a confirmatory experiment.
The historical source record is corrected when better evidence appears, with provenance preserved.
Interpretations may accumulate and disagree.
Confidence may change as evidence changes.

Do not rewrite a source quotation, historical attribution, or prior interpretation merely because a later experiment performs differently.

## 3. Required audit record for every canonical strategy

Each of the 86 entries should eventually have an audit record with at least:

```yaml
canonical_id:
canonical_name:
current_kingdom_book_label:
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

`current_kingdom_book_label` records what the current machine-readable canon says. `primary_source` and `source_location` record what independent source audit can actually support. They must not be silently collapsed into one field.

## 4. Interpretation Zettelkasten

A canonical strategy may have many interpretation notes.

Example shape:

```text
#1 Canonical strategy
  ├─ Zettel A: source-faithful historical reading
  ├─ Zettel B: philosophical / organizational reading
  ├─ Zettel C: popular or practitioner reading
  ├─ Zettel D: KINGDOM agent-orchestration interpretation
  ├─ Zettel E: critical / counter-reading
  └─ Zettel F: measured KINGDOM lesson
```

Interpretation notes are append-only research objects. They should preserve provenance: author or source, edition/translation where relevant, date, uncertainty, and whether the interpretation is historical scholarship, popular interpretation, project interpretation, generated suggestion, or measured runtime lesson.

Popularity is not truth. Citation count is not contextual fitness. A widely repeated interpretation may remain low-confidence if it is weakly grounded or performs poorly in measured use.

## 5. Existing counter-principle doctrine versus new research work

KINGDOM already declares a strategy application rule of **one primary principle plus one checking/counter principle** for a judgment. That existing doctrine must be preserved as prior system behavior rather than presented as a new ACL invention.

The new research question is narrower: whether richer, attributed interpretation records and their explicit failure conditions improve contextual selection beyond the current principle/check-principle mechanism and simpler baselines.

A strategy is not a universal rule. Every interpretation used experimentally should therefore expose one or more counter-principles or explicit failure conditions.

The research question is not:

> Is this strategy true?

It is:

> Under which observable conditions does this interpretation appear useful, and under which conditions does a competing interpretation or principle dominate?

## 6. Canon versus generated suggestion

Use these labels consistently:

- `CANON`: existing KINGDOM 86 entry
- `CURRENT_KINGDOM_LABEL`: current project attribution/book label
- `SOURCE`: independently inspected textual/historical evidence
- `INTERPRETATION`: an attributed reading of the source/canon
- `PROJECT_INTERPRETATION`: KINGDOM-specific operational reading
- `HYPOTHESIS`: falsifiable when/why claim
- `GENERATED_SUGGESTION`: model-generated candidate, never canonical by default
- `MEASURED_LESSON`: interpretation or update supported by runtime evidence

A generated example must never inherit a canon number just because it resembles a familiar classical principle.

## 7. Research anti-contamination rule

Do not modify the canon after seeing benchmark results in order to improve measured performance.

If a canonical entry is later found to have weak provenance, mistranslation, duplication, or historical error, record the defect explicitly. Preserve the old identifier for reproducibility and handle correction through a versioned canon change process rather than silent rewriting.

## 8. Relationship to EROS and authority

The current KINGDOM canon maps strategies to the six canonical EROS virtues: `truth`, `goodness`, `beauty`, `benevolence`, `filialPiety`, and `eternity` (진·선·미·인·효·영).

Those mappings are part of the current project state and should be audited separately from historical provenance.

Historical prestige, cultural familiarity, citation frequency, EROS alignment, and measured past success do not by themselves grant execution authority.

```text
strategy evidence → interpretation/recommendation  allowed
strategy evidence → local policy override          forbidden
strategy evidence → human approval bypass          forbidden
strategy evidence → Evidence Gate override         forbidden
```

The canon is a reasoning prior, not a sovereign.
