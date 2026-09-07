"""Pure column/orb layout functions for the local evidence-graph viewer.

Every function here is deterministic and does no I/O: it takes the
``hyodo.evidence-graph/v1`` node/edge shapes `hyodo/event_graph.py` already
produces and returns the layout facts `hyodo/dashboard.py` renders as HTML
(rollout step (b),
`docs/superpowers/specs/2026-09-06-hyodo-core-engine-monitor-design.md`).
Nothing here computes a composite score, a probability, or a confidence
value, and nothing here changes a policy decision — nothing does anything
but re-read fields the schema already carries.
"""

from __future__ import annotations

from typing import Any

#: Fixed column order (spec section 2): Truth, Goodness, Beauty, Benevolence,
#: Hyo. Eternity is not a column — it is read off the orb (section 4).
VIRTUE_COLUMNS: tuple[str, ...] = ("jin", "seon", "mi", "in", "hyo")

#: Gutter sentinel for an event the mapping table (spec section 3) does not
#: match at all. Distinct from the empty list `assign_columns` returns for
#: `prompt`/`model_response`, which match the table's last row on purpose
#: ("no column") and are not unclassified.
UNCLASSIFIED = "unclassified"

#: Section 3 table, row 4: "type-check, lint tools" -> Truth.
_TYPECHECK_LINT_PATTERNS: tuple[str, ...] = (
    "typecheck",
    "type-check",
    "type_check",
    "pyright",
    "mypy",
    "tsc",
    "lint",
    "ruff",
    "eslint",
    "flake8",
)
#: Section 3 table, row 5: "test runner" -> Goodness.
_TEST_RUNNER_PATTERNS: tuple[str, ...] = ("test", "pytest", "jest", "vitest", "mocha")
#: Section 3 table, row 6: "formatter" -> Beauty.
_FORMATTER_PATTERNS: tuple[str, ...] = ("format", "fmt", "prettier", "black", "gofmt")
#: Section 3 table, row 7: "doc/onboarding tools" -> Benevolence.
_DOC_PATTERNS: tuple[str, ...] = ("doc", "readme", "onboard", "changelog")

#: Section 3 table, row 8: data-boundary rule ids -> Hyo.
_HYO_RULE_IDS = frozenset({"data_boundary", "data_boundary_undeclared"})
#: Section 3 table, row 9: web-credential rule ids -> Goodness + Hyo.
_WEB_CREDENTIAL_RULE_IDS = frozenset(
    {"web_credential_path_denied", "web_credential_path_unobserved"}
)
#: Section 3 table, last row: mission/time-axis events carry no column.
_NO_COLUMN_KINDS = frozenset({"prompt", "model_response"})


def _matches(name: str, patterns: tuple[str, ...]) -> bool:
    return bool(name) and any(pattern in name for pattern in patterns)


def assign_columns(node: dict[str, Any]) -> list[str]:
    """Place one graph node (spec section 3's event -> virtue mapping table).

    `node` is one entry of `build_event_graph(...)["nodes"]`. Returns the
    virtue column keys (`VIRTUE_COLUMNS`) this event matches, in fixed
    column order, spanning every matched row rather than forcing a single
    pick. `prompt`/`model_response` events match the table's own "no
    column" row and return an empty list — they feed the time axis and
    mission only, and are never counted against the unclassified gutter.
    Any other event matching no row returns `[UNCLASSIFIED]`.
    """
    kind = node.get("kind")
    policy = node.get("policy") if isinstance(node.get("policy"), dict) else {}
    rule_id = policy.get("rule_id") if isinstance(policy, dict) else None
    tool = node.get("tool") if isinstance(node.get("tool"), dict) else {}
    name = str(tool.get("name") or "").lower() if isinstance(tool, dict) else ""

    matched: list[str] = []

    def _add(column: str) -> None:
        """Append *column* once, keeping the mapping table's match order."""
        if column not in matched:
            matched.append(column)

    if kind == "decision":
        # Row: decision (ALLOW/ASK/DENY/UNOBSERVED) -> Goodness. An ALLOW is
        # still observed evidence; an UNOBSERVED decision renders as the
        # decision's own UNOBSERVED tile under Goodness, not the gutter.
        _add("seon")
    if kind in ("tool_call", "tool_result"):
        if _matches(name, _TYPECHECK_LINT_PATTERNS):
            _add("jin")
        if _matches(name, _TEST_RUNNER_PATTERNS):
            _add("seon")
        if _matches(name, _FORMATTER_PATTERNS):
            _add("mi")
        if _matches(name, _DOC_PATTERNS):
            _add("in")
    if kind == "error":
        _add("jin")
    if rule_id in _HYO_RULE_IDS:
        _add("hyo")
    if rule_id in _WEB_CREDENTIAL_RULE_IDS:
        _add("seon")
        _add("hyo")

    if kind in _NO_COLUMN_KINDS:
        return []
    if not matched:
        return [UNCLASSIFIED]
    # Keep the fixed column order regardless of the order rows matched in.
    return [column for column in VIRTUE_COLUMNS if column in matched]


def hyo_chain(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, bool]:
    """Structural Hyo check (spec section 3, "not a table lookup").

    An event is filial (`True`) if walking its `parent_event_id` chain,
    hop by hop, reaches its run's mission event (the run's lowest
    `step_index` `prompt` event from `actor == "human"`, spec section 2).
    The mission event itself counts as filial. An event with no parent, a
    parent chain that terminates before the mission, a chain that cycles,
    or a run with no observed mission is an orphan (`False`).
    """
    node_by_id = {node["id"]: node for node in nodes if node.get("id")}
    parent_of: dict[str, str] = {}
    for edge in edges:
        if edge.get("type") == "parent_event_id":
            target, source = edge.get("target"), edge.get("source")
            if isinstance(target, str) and isinstance(source, str):
                parent_of[target] = source

    mission_by_run: dict[str, str] = {}
    mission_step: dict[str, int] = {}
    for node in nodes:
        run_id = node.get("run_id")
        step = node.get("step_index")
        if (
            isinstance(run_id, str)
            and node.get("kind") == "prompt"
            and node.get("actor") == "human"
            and isinstance(step, int)
            and not isinstance(step, bool)
            and (run_id not in mission_step or step < mission_step[run_id])
        ):
            mission_by_run[run_id] = node["id"]
            mission_step[run_id] = step

    result: dict[str, bool] = {}
    for node in nodes:
        node_id = node.get("id")
        if not isinstance(node_id, str):
            continue
        run_id = node.get("run_id")
        mission_id = mission_by_run.get(run_id) if isinstance(run_id, str) else None
        if mission_id is None:
            result[node_id] = False
            continue
        if node_id == mission_id:
            result[node_id] = True
            continue
        seen = {node_id}
        current = parent_of.get(node_id)
        chained = False
        while current is not None:
            if current == mission_id:
                chained = True
                break
            if current not in node_by_id or current in seen:
                break
            seen.add(current)
            current = parent_of.get(current)
        result[node_id] = chained
    return result


def column_coverage(
    nodes: list[dict[str, Any]],
    assignments: dict[str, list[str]],
    edges: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    """`observed / expected` per column (spec sections 3-4).

    `assignments` is `{node_id: assign_columns(node)}`. For the four
    non-Hyo columns, `expected` is the count of events the mapping table
    placed on that column and `observed` is how many of those are actual
    evidence rather than the column's own UNOBSERVED tile (a `decision`
    node whose `decision` is `UNOBSERVED`). Hyo's ratio is structural
    instead, per section 3: `expected` is every event in the run and
    `observed` is the count `hyo_chain` marks filial — deviates from the
    brief's two-argument sketch by taking `edges` too, because the
    structural chain calculation needs them; see the implementer report.
    """
    node_by_id = {node["id"]: node for node in nodes if node.get("id")}
    chain = hyo_chain(nodes, edges)
    coverage: dict[str, dict[str, int]] = {}
    for column in VIRTUE_COLUMNS:
        if column == "hyo":
            observed = sum(1 for chained in chain.values() if chained)
            expected = len(nodes)
        else:
            assigned = [node_id for node_id, columns in assignments.items() if column in columns]
            expected = len(assigned)
            observed = sum(
                1
                for node_id in assigned
                if not (
                    node_by_id.get(node_id, {}).get("kind") == "decision"
                    and node_by_id.get(node_id, {}).get("decision") == "UNOBSERVED"
                )
            )
        coverage[column] = {"observed": observed, "expected": expected}
    return coverage


def orb_state(graph: dict[str, Any]) -> dict[str, Any]:
    """The orb's three signals (spec section 4), each read off existing facts.

    `graph` is a full `hyodo.evidence-graph/v1` dict
    (`build_event_graph(...)` / `hyodo report --format graph`). Returns:

    - `decision`: the latest `decision`-kind event's `policy.decision` by
      `ts`, or `"UNOBSERVED"` when the ledger is not `READY` or no decision
      event was observed — the orb never claims a clean run it did not see.
    - `coverage`: `{"observed", "expected"}` summed across the five column
      badges (`column_coverage`), so the number is never a new synthesis,
      only a second rendering of numbers already on the page.
    - `latest_ts`: the most recent `ts` across every node (any kind), for
      the pulse decay; `None` when there are no timestamped nodes.
    """
    raw_nodes = graph.get("nodes")
    raw_edges = graph.get("edges")
    nodes: list[dict[str, Any]] = raw_nodes if isinstance(raw_nodes, list) else []
    edges: list[dict[str, Any]] = raw_edges if isinstance(raw_edges, list) else []
    assignments = {
        node["id"]: assign_columns(node) for node in nodes if isinstance(node.get("id"), str)
    }
    coverage = column_coverage(nodes, assignments, edges)
    total_observed = sum(entry["observed"] for entry in coverage.values())
    total_expected = sum(entry["expected"] for entry in coverage.values())

    decision = "UNOBSERVED"
    if graph.get("status") == "READY":
        latest_decision_ts: str | None = None
        for node in nodes:
            if node.get("kind") != "decision":
                continue
            ts = node.get("ts")
            if not isinstance(ts, str) or not ts:
                continue
            if latest_decision_ts is None or ts > latest_decision_ts:
                latest_decision_ts = ts
                candidate = node.get("decision")
                if isinstance(candidate, str) and candidate:
                    decision = candidate

    latest_ts: str | None = None
    for node in nodes:
        ts = node.get("ts")
        if isinstance(ts, str) and ts and (latest_ts is None or ts > latest_ts):
            latest_ts = ts

    return {
        "decision": decision,
        "coverage": {"observed": total_observed, "expected": total_expected},
        "latest_ts": latest_ts,
    }


def build_actor_rows(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    """Derive display rows and collapsible sub-agent nesting (spec section 2).

    Rows are `human`, `agent:<label>`, and `hyodo` — the schema's actor
    field stays coarse (`agent`/`human`/`hyodo`,
    `hyodo/events.py:37 ACTORS`); `<label>` is a display-only sub-label
    derived from the row's earliest `tool.name`, never a new schema field.
    A row nests under another row when its earliest event's
    `parent_event_id` resolves to a `tool_call` belonging to a different
    row — entirely derived from the `parent_event_id` edge Phase 1-B
    already ships.

    Returns `{"order": [row_key, ...], "rows": {row_key: {...}}}` where
    each row dict has `actor`, `events` (node ids, earliest first), and
    `parent_row` (`None` for a top-level row).
    """
    parent_of: dict[str, str] = {}
    for edge in edges:
        if edge.get("type") == "parent_event_id":
            target, source = edge.get("target"), edge.get("source")
            if isinstance(target, str) and isinstance(source, str):
                parent_of[target] = source
    node_by_id = {node["id"]: node for node in nodes if isinstance(node.get("id"), str)}

    def _label_for(node: dict[str, Any]) -> str:
        """Display row key for *node*: raw actor, or `agent:<tool.name>`."""
        actor = node.get("actor")
        if actor != "agent":
            return str(actor) if actor else "unknown"
        tool = node.get("tool") if isinstance(node.get("tool"), dict) else {}
        name = tool.get("name") if isinstance(tool, dict) else None
        return f"agent:{name}" if isinstance(name, str) and name else "agent"

    def _sort_key(node: dict[str, Any]) -> int:
        """Sort nodes by `step_index`, treating a missing one as earliest."""
        step = node.get("step_index")
        return step if isinstance(step, int) and not isinstance(step, bool) else 0

    rows: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for node in sorted(nodes, key=_sort_key):
        node_id = node.get("id")
        if not isinstance(node_id, str):
            continue
        key = _label_for(node)
        if key not in rows:
            rows[key] = {"actor": node.get("actor"), "events": [], "parent_row": None}
            order.append(key)
        rows[key]["events"].append(node_id)

    for key in order:
        row = rows[key]
        if row["actor"] != "agent" or not row["events"]:
            continue
        first_id = row["events"][0]
        parent_id = parent_of.get(first_id)
        parent_node = node_by_id.get(parent_id) if isinstance(parent_id, str) else None
        if parent_node is not None and parent_node.get("kind") == "tool_call":
            parent_key = _label_for(parent_node)
            if parent_key != key:
                row["parent_row"] = parent_key

    return {"order": order, "rows": rows}
