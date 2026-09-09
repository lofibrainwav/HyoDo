# Graph v2 join contract (fixture freeze)

Status: **fixture and contract freeze only**. This document does not ship a
Graph v2 viewer, a multi-parent runtime, an ACL router, or a friction metric.

## Purpose

Graph v2 join validation answers one topology question: does the directed
parent graph contain a cycle? The graph direction is always:

```text
child -> parent
```

`evidence_refs` are not parent edges and are excluded from this graph.
`parent_event_id` remains the HyoDo v1 singular pointer; a join adapter may
provide multiple parent edges as separate `child -> parent` pairs.

## Frozen fixture shape

Each fixture is a deterministic JSON object with this shape:

```json
{
  "schema": "hyodo.graph-v2-join-fixture/v1",
  "fixture": "name",
  "nodes": ["A", "B"],
  "edges": [{"child": "B", "parent": "A"}],
  "expected": {
    "acyclic": true,
    "components": [["A"], ["B"]],
    "cycle_reasons": [],
    "unresolved_refs": []
  }
}
```

`nodes` and each component are name-sorted. Components are sorted by their
first member. An edge whose endpoint is absent from `nodes` is unresolved and
does not become an SCC node. The five frozen fixtures are:

| Fixture | Expected result |
| --- | --- |
| `linear-chain` | three singleton SCCs; DAG |
| `diamond-join` | four singleton SCCs; DAG |
| `triangle-cycle` | one SCC of size three; `join_cycle` |
| `a-j-join-cycle` | `{A,J}` cyclic and `{B}` separate; `join_cycle` |
| `unresolved-parent` | missing parent skipped; DAG with `unresolved_ref` |

## Independent oracle

The Tarjan implementation is a pure oracle exposed as:

```python
from hyodo.tarjan_scc import has_directed_cycle, hyodo_parent_edges, tarjan_scc

nodes, edges = hyodo_parent_edges(events)
result = tarjan_scc(nodes, edges)
```

`result.components` is the complete SCC report. A component with more than one
node is a directed cycle (`join_cycle`). A singleton with a self-loop is a
`self_cycle`. Internal edges of a non-trivial SCC are reported as
`join_cycle_edge`. `result.acyclic` is the independent yes/no oracle.

Lane B may use a separate 3-color DFS to report one human-readable back edge;
that reason and the Tarjan report are intentionally independent. Hopcroft–Karp
is not a cycle detector and does not belong in this path. It remains a future
scheduler matching primitive only.

## Boundary

This freeze does not connect SCC output to `hyodo.event_graph`, ACL runtime,
EROS authority, the public viewer, or `hyodo friction preview`. A cycle result
is topology evidence, not a gate verdict, trust level, score, or execution
authority.
