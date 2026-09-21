# Portability Research v0 — Source Inventory

Status: **initial inventory / no fixture results yet**  
Snapshot basis: `origin/main` after HyoDo 4.20.2 research-doc reconciliation

This inventory records what source material is actually available for the
three-domain falsification pilot. It does not treat filenames, profile labels,
or generic tests as evidence of a domain workflow.

## Inventory rule

An item is `OBSERVED` only when the repository contains a concrete artifact
that can support a bounded claim about the stated domain. A reusable helper,
test label, or design note may be a candidate source to inspect, but it does
not become domain evidence by naming alone.

| Domain | Inventory state | What is actually available | What remains unobserved |
| --- | --- | --- | --- |
| Software | `OBSERVED` for repository verification workflows | source checkout, commits, tests, policies, runtime identity, ledger events, evidence-graph fixtures, release receipts | external team workflow and independently supplied software case |
| Professional | `UNOBSERVED` | audience/profile terminology and generic approval-boundary tests only | a real bounded professional case, source documents, approval, submission, and observed effect |
| Creative | `UNOBSERVED` | generic image/asset handling tests and presentation code only | a real creative asset lineage, edit/provenance record, approval, publication, and observed effect |

## Software source set

The following artifacts are concrete candidates for the Software inventory:

- `examples/fde-evidence-spine/` — evidence and policy examples;
- `examples/factory-loop/` — source/test/policy execution workflow example;
- `examples/host-policies/` — host policy and approval-boundary examples;
- `tests/fixtures/graph-v2-join/` — subject/evidence join and unresolved-parent
  controls;
- `tests/fixtures/dashboard-truth-cases.json` — dashboard truth cases;
- `tests/fixtures/acceptance-join-live-mismatch.json` — live/source mismatch
  control;
- `docs/research/EVIDENCE_RECONCILIATION_2026-09-20.md` — measured
  reconciliation record; and
- the final runtime identity and `.hyodo` ledger, when a fresh checkout is
  explicitly frozen for the run.

These artifacts can support bounded claims about source identity, evidence
binding, freshness, test or deployment state, and observed runtime effect. They
cannot establish general software quality or the correctness of an external
team's engineering decision.

## Professional source gap

The repository contains terms such as `professional`, `approval`, and `case`
in audience and boundary tests. Those are implementation and policy evidence,
not a professional-domain case record. No professional source package is
currently admitted to the pilot.

Required before Professional fixtures can move beyond `UNOBSERVED`:

1. a bounded case with an identified subject;
2. the exact claim under review;
3. source references that support only that claim;
4. approval or authority boundary evidence;
5. a submission or downstream effect record; and
6. a limitation stating that HyoDo does not judge professional correctness.

## Creative source gap

Image hashes, asset handling, design pages, and generic media tests show that
the repository can process asset-shaped data. They do not provide a creative
workflow with provenance, edit history, approval, publication, and observed
effect. No creative source package is currently admitted to the pilot.

Required before Creative fixtures can move beyond `UNOBSERVED`:

1. an identified asset and subject;
2. the exact bounded claim about the asset or edit;
3. provenance and edit evidence;
4. approval or ownership boundary evidence;
5. a publication or delivery effect record; and
6. a limitation stating that HyoDo does not judge taste or creative quality.

## Admission rule for the next run

Do not manufacture Professional or Creative fixtures from Software examples.
The next run may execute Software controls and adversarial cases, but the
three-domain portability comparison remains `UNOBSERVED` until independently
supplied Professional and Creative source packages pass this inventory gate.

The inventory itself is not a Core proposal and does not change any runtime,
schema, package, release, or authority contract.

