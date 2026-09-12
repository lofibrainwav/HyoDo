# Graph v2 multi-parent contract

Status: **contract + normalization implementation**. Public `hyodo.event_graph`
and the dashboard remain v1 until the integration gate lands separately.

## Purpose

Graph v2 represents real fork/join topology without changing the meaning of
`evidence_refs` or silently truncating a join to one parent.

The causal graph direction is always:

```text
child -> parent
```

`evidence_refs` are citation/evidence links, not causal parents.

## Event compatibility

### v1

`hyodo.agent-event/v1` remains valid and keeps its optional singular
`parent_event_id`.

### v2

`hyodo.agent-event/v2` represents causal parents with:

```json
{
  "schema_version": "hyodo.agent-event/v2",
  "event_id": "join",
  "run_id": "run-1",
  "parent_event_ids": ["branch-a", "branch-b"]
}
```

Normalization rules:

- v1 `parent_event_id` becomes zero or one entry in `parent_event_ids`;
- v2 parents are de-duplicated and sorted for deterministic serialization;
- v2 with zero/one parent can be represented by a legacy singular view;
- v2 with multiple parents is **not** truncated: the legacy singular parent is
  reported as unavailable/unrepresentable;
- `evidence_refs` never enter the causal parent set;
- unknown schemas are structurally invalid.

## Independent structural axes

Graph v2 reports these separately:

```text
acyclic
references_resolved
structurally_valid
```

Therefore a missing parent may yield:

```text
acyclic=true
references_resolved=false
structurally_valid=false
```

and must never be rendered as a healthy graph simply because the resolved
subgraph has no cycle.

A causal parent must exist in the same `run_id`. Cross-run parents are reported
separately from unresolved parents and are excluded from SCC adjacency.

## Independent SCC oracle

Tarjan remains the independent cycle oracle. The v2 contract does not infer
cycle status from UI traversal or from a first-parent walk.

```python
from hyodo.graph_v2 import validate_graph_v2

result = validate_graph_v2(events)
```

A singleton self-loop reports only `self_cycle`. A multi-node SCC reports
`join_cycle` plus its internal `join_cycle_edge` findings.

## Frozen acceptance cases

The contract suite covers at least:

| Case | Expected |
| --- | --- |
| v1 single parent | normalizes losslessly |
| v2 single parent | legacy-representable |
| v2 diamond join | valid DAG, four singleton SCCs |
| reversed input order | identical deterministic result |
| missing parent | acyclic but unresolved/invalid |
| cross-run parent | separate cross-run finding |
| self-loop | `self_cycle` |
| join-only cycle | multi-node SCC detected |
| two disjoint cycles | two independent cyclic SCCs |
| `evidence_refs` only | no causal edge |
| duplicate event id | structurally invalid |
| unknown schema | structurally invalid |

## Boundary

This contract does not grant execution authority, change EROS, route agents,
or reinterpret citations as causal flow. Production viewer/report integration,
ledger writer support for v2, and v1/v2 migration readback are separate serial
promotion gates under #222.
