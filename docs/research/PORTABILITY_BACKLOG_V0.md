# Portability research backlog — from the Software v0 run

Two findings the independent judge left open when Software Portability v0
closed. Both are recorded here as **questions to answer later**, not as defects
to patch into the sealed run.

This file deliberately carries no evidence of its own. The measurements,
fixtures, oracle, and verdict live in the sealed receipts and are canonical
there:

- [`PORTABILITY_SOFTWARE_V0_RECEIPT.md`](./PORTABILITY_SOFTWARE_V0_RECEIPT.md)
  — the run, its results, and every preserved limitation
- [`PORTABILITY_JUDGE_RECEIPT_V0.md`](./PORTABILITY_JUDGE_RECEIPT_V0.md)
  — the independent verdict and both open findings in full
- [`PORTABILITY_RESEARCH_V0.md`](./PORTABILITY_RESEARCH_V0.md)
  — the frozen protocol

Software Portability v0 is **not reopened** by this backlog. Nothing here
changes the sealed run, its oracle, or its verdict.

## SW-03 — evidence search completeness

**Question.** How does a source search know it is finished?

The v0 preflight found a representable artifact for the replay family and
stopped. A stronger executable source existed and was not surfaced. The same
shape had already occurred once earlier in the run and been corrected — and the
correction widened the search only for the families that had nothing, not for
the families that already had something.

A source that is good enough ends the search. That is the pattern worth a rule.

**Open.** What makes a search reportable as complete rather than merely
successful? Detail in
[`PORTABILITY_JUDGE_RECEIPT_V0.md`](./PORTABILITY_JUDGE_RECEIPT_V0.md),
"Open finding 2".

## SW-09 — state partition semantics

**Question.** Is a halted action *unmeasured* or *positively contradicted*?

Three independent readings of one piece of evidence disagreed: the frozen
oracle, the independent judge, and the baseline arm each reached a different
state. The precedence ladder was applied identically by all three, so this is
not a tie-breaking accident — they disagreed about which conditions the evidence
satisfies at all.

**Open.** Do the four local states partition the evidence space, or is there a
boundary case between "the effect was never measured" and "we observed the
effect not happening"? Detail in
[`PORTABILITY_JUDGE_RECEIPT_V0.md`](./PORTABILITY_JUDGE_RECEIPT_V0.md),
"Open finding 1".

## Scope

These two items only. The Software lane stays closed, Professional and Creative
stay `UNOBSERVED`, and Core promotion stays `NOT_ELIGIBLE`. Any future
Professional or Creative work is a separate pre-registered experiment and does
not generalize from the Software result.
