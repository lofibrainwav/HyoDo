# Measured Run #3 candidate receipt — historical

> This document records the pre-public candidate measurement. It is retained
> for lineage and is superseded by the native public-package Evidence Pack v1
> for `kingdom-measured-run-3-public-4.18.0-2026-09-10`.

This receipt records an actual KINGDOM run against a locally installed HyoDo
4.18.0 candidate. It is not the public-release proof; the signed tag, PyPI
provenance, and native public-package run are recorded separately.

## Scope

- Run ID: `kingdom-measured-run-3-2026-09-10`
- Observed: `2026-09-10T04:11:37Z`–`2026-09-10T04:11:40Z`
- KINGDOM root: `/Users/brnestrm/kingdom`
- KINGDOM source HEAD readback: `17fc4f5eccc1cebd14f023a15981c740a60b8f7c`
- HyoDo release worktree HEAD: `034a189610c0b237a18fcb17a9fafbe4a89098b6`
- Installed readback: `HyoDo v4.18.0 - model-agnostic quality gates`
- The KINGDOM worktree was already dirty. The run did not modify tracked files.

The candidate wheel was installed into `/tmp/hyodo-run3-venv`; the checkout
was not used as the installed package. The measured commands were read-only
KINGDOM status/git readbacks plus deliberately bounded local retry/wait probes.

## Signal matrix

| Signal | Result | Evidence in ledger/report |
| --- | --- | --- |
| serial | MEASURED | two events at step 0, `r3-serial-*` |
| parallel | MEASURED | four events at step 1, two concurrent commands |
| DAG join | MEASURED | `r3-join-result` cites both parallel results |
| retry | MEASURED | failed attempt exit 1 followed by successful attempt exit 0 |
| wait | MEASURED | `measurement.wait`, observed wait `204 ms` |
| rework | MEASURED | second retry attempt tagged `rework` |
| human intervention | MEASURED | `r3-human-approval`, actor `human` |
| unresolved observation | MEASURED | sidecar observation `obs-unresolved`, unresolved dependency `missing-event-r3` |

The event ledger contains 16 valid events and zero corrupt lines. The graph
report contains 16 nodes, 9 edges, 7 parent links, and 2 evidence references.
The join evidence is explicit rather than inferred from ordering alone.

## HyoDo observation boundary

The event policy fields are `unevaluated` for this harness. This run measures
the observation adapter and graph projection; it does not grant authority,
evaluate an execution policy, or turn a successful shell command into a gate
decision. The unresolved observation remains unresolved and is not promoted to
success.

## Renderer readback

The public evidence graph was loaded with the actual report JSON:

- rendered event buttons: `16`
- rendered graph edges: `9`
- sampled edge/cell collisions: `0`
- console errors: `0`
- boundary label: `LOCAL DATA / NOT SEALED`

The renderer check matters because the first prototype collapsed co-located
events sharing a `(row, step)` cell. The fix preserves every event as its own
focusable tile inside a shared DAW-style cell.

## Artifacts

| Artifact | SHA-256 |
| --- | --- |
| `/Users/brnestrm/kingdom/.hyodo/agent-events.jsonl` | `579123cd1edc0a7246c0941cb87b9f087178ed0dbf26dacdb3a03d08d4c05ae7` |
| `/Users/brnestrm/kingdom/.hyodo/reports/hyodo-report.graph.json` | `fe0d082a42cd941bd297a5c706cd83927fbe3c202047d414e504d9355ce4c9fb` |
| candidate wheel `hyodo-4.18.0-py3-none-any.whl` | `a853ac36c784049a98e6c7d3120644160aea3a47c2d8c7016e0819922b42272d` |

## Result

Run #3 is **MEASURED** for the eight requested observation signals. It is not
yet public-release proof: signed tag, PyPI provenance, and the clean install
against the published artifact remain separate release-chain gates.
