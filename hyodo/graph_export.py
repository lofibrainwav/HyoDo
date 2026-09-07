"""The Package 2-C export bridge: ``hyodo.graph-export/v1``.

An external note system (Zettelkasten-shaped or otherwise) turns this
artifact into permanent notes. Everything here is a pure, deterministic
function over an already-built ``hyodo.evidence-graph/v1`` dict
(`hyodo.report.build_report_graph`); nothing here reads the ledger itself
and nothing here writes a file — the CLI command in `hyodo/cli/main.py`
owns confirmation and the write.

Per the design
(`docs/superpowers/specs/2026-09-06-hyodo-agent-os-stage2-design.md`,
Package 2-C), only ids, parents, refs, claims, and clusters cross this
bridge; note bodies, chunk text, and embeddings never do.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hyodo.graph_view import UNCLASSIFIED, assign_columns

GRAPH_EXPORT_SCHEMA_VERSION = "hyodo.graph-export/v1"

#: `assign_columns`'s short column keys mapped to the export's full pillar
#: names (spec's `hyodo.graph-export/v1` JSON example). "yeong"/"eternity"
#: never appears as an `assign_columns` result (Eternity is orb-only, not a
#: column, per `hyodo/graph_view.py`), so its cluster list is always empty
#: — present, per the spec's fixed six keys, never populated by this rule
#: table.
_COLUMN_TO_PILLAR: dict[str, str] = {
    "jin": "truth",
    "seon": "goodness",
    "mi": "beauty",
    "in": "benevolence",
    "hyo": "hyo",
}

#: The six spec-fixed cluster keys, always present in `clusters`, plus the
#: additive seventh key (Ruling 1) for a decision event `assign_columns`
#: places nowhere.
CLUSTER_PILLAR_KEYS: tuple[str, ...] = (
    "truth",
    "goodness",
    "beauty",
    "benevolence",
    "hyo",
    "eternity",
)


def compute_backlinks(edges: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Reverse-index every non-broken `evidence_refs` entry (spec, evaluation order 3).

    `edges` is `hyodo.evidence-graph/v1`'s own `edges` list
    (`hyodo/event_graph.py:build_event_graph`) — an `evidence_ref` edge only
    exists there for a ref that already resolved (a broken ref never
    produces one, so this function never re-derives edge validity itself,
    per the spec's evaluation order 2). A gate reference (`target_kind`
    `"gate"`) is not an event and is not a key here — `backlinks` reverse-
    indexes *events cited*, not gate ids.

    Returns `{cited_event_id: [citing_event_id, ...]}`, values sorted, keys
    only for events cited at least once (Ruling 2).
    """
    backlinks: dict[str, set[str]] = {}
    for edge in edges:
        if edge.get("type") != "evidence_ref" or edge.get("target_kind") != "event":
            continue
        cited = edge.get("source")
        citing = edge.get("target")
        if isinstance(cited, str) and isinstance(citing, str):
            backlinks.setdefault(cited, set()).add(citing)
    return {cited: sorted(citing_ids) for cited, citing_ids in sorted(backlinks.items())}


def compute_clusters(nodes: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Group decision-event ids by pillar (spec evaluation order 4, Ruling 1).

    Reuses `assign_columns` — the deterministic event -> virtue mapping
    table already shipped for the local graph viewer — as the pillar rule
    for each `kind == "decision"` event. A decision `assign_columns` places
    on no real column (returns `[UNCLASSIFIED]`) goes to the additive
    seventh `"unclassified"` key instead of being dropped; the six spec
    keys stay present (possibly empty) regardless.
    """
    clusters: dict[str, list[str]] = {key: [] for key in CLUSTER_PILLAR_KEYS}
    clusters[UNCLASSIFIED] = []
    for node in nodes:
        if node.get("kind") != "decision":
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str):
            continue
        columns = assign_columns(node)
        if not columns or columns == [UNCLASSIFIED]:
            clusters[UNCLASSIFIED].append(node_id)
            continue
        for column in columns:
            pillar = _COLUMN_TO_PILLAR.get(column)
            if pillar and node_id not in clusters[pillar]:
                clusters[pillar].append(node_id)
    return {key: sorted(ids) for key, ids in clusters.items()}


def build_graph_export(graph: dict[str, Any], *, generated_at: str | None = None) -> dict[str, Any]:
    """Build the `hyodo.graph-export/v1` artifact from a full evidence graph dict.

    `graph` is `hyodo.report.build_report_graph(root)`'s return value. On a
    pre-1-B ledger (no `parent_event_id`/`evidence_refs` fields anywhere),
    `graph["edges"]` is already empty, so `backlinks` comes back `{}` and
    every cluster list stays empty too — an honestly empty export, not an
    error (spec evaluation order 1, backward compatibility section).
    """
    raw_nodes = graph.get("nodes")
    raw_edges = graph.get("edges")
    nodes: list[dict[str, Any]] = raw_nodes if isinstance(raw_nodes, list) else []
    edges: list[dict[str, Any]] = raw_edges if isinstance(raw_edges, list) else []
    return {
        "schema": GRAPH_EXPORT_SCHEMA_VERSION,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "nodes": nodes,
        "edges": edges,
        "backlinks": compute_backlinks(edges),
        "clusters": compute_clusters(nodes),
    }
