# Measured Run #3 corrected-v2 receipt

This is the relation-complete rerun of Measured Run #3. The first Run #3
receipt remains preserved as the original observation; this receipt is the
one used to inspect causal edges in the graph viewer.

## Readback

- Run ID: `kingdom-measured-run-3-corrected-v2-2026-09-10`
- HyoDo candidate: `HyoDo v4.18.0 - model-agnostic quality gates`
- KINGDOM command root: `/Users/brnestrm/kingdom`
- Isolated evidence root: `/Users/brnestrm/kingdom/.hyodo/run3-corrected-v2-root`
- Status: `READY`
- Events: `17`
- Edges: `21`
- Parent links: `16`
- Evidence references: `5`
- Unresolved references: `0`
- Corrupt event lines: `0`

## Relationship contract measured

The corrected harness recorded explicit relationships instead of relying on
step order:

`human mission → serial → parallel A/B → DAG join → retry 1 → human approval → rework → wait → unresolved observation`

The parallel branches are linked to the join with evidence references. The
failed retry is linked to the human approval, the approval is linked to the
rework attempt, and the unresolved observation is linked to the wait result.
These are recorded parent/evidence edges, not renderer-inferred chronology.

## Signal matrix

| Signal | Result | Readback |
| --- | --- | --- |
| serial | MEASURED | explicit mission/serial parent chain |
| parallel | MEASURED | two concurrent branches, both parent-linked |
| DAG join | MEASURED | join call/result plus two evidence refs |
| retry | MEASURED | `/usr/bin/false` exit 1, then success |
| wait | MEASURED | observed wait `202 ms` |
| rework | MEASURED | second attempt explicitly parented to human approval |
| human intervention | MEASURED | approval parented to failed retry result |
| unresolved observation | MEASURED | final observation parented to wait result and tagged unresolved |

## Artifact hashes

- Ledger SHA-256: `3bf6f4d9e5b765efa45b96863f01f97be860aaa2579cdaebb7dacd35144f99aa`
- Graph SHA-256: `14532fac355814aa98c728a718d057214ba285fd1f0bff7e621ae732a408b992`

This corrected-v2 receipt still does not establish signed-tag, PyPI
provenance, SBOM-publication, or clean-install-from-PyPI proof.
