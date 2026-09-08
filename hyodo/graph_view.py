"""Pure column/orb layout functions for the local evidence-graph viewer.

Every function here is deterministic and does no I/O: it takes the
``hyodo.evidence-graph/v1`` node/edge shapes `hyodo/event_graph.py` already
produces and returns the layout facts `hyodo/dashboard.py` renders as HTML
(rollout step (b),
`docs/superpowers/specs/2026-09-06-hyodo-core-engine-monitor-design.md`).
Nothing here computes a composite score, a probability, or a confidence
value, and nothing here changes a policy decision — nothing does anything
but re-read fields the schema already carries.

The one exception is :func:`build_actor_rings` (Package 2-C, step (c) of
the core-engine-monitor rollout): it reads local, already-shipped
artifacts (`.hyodo/skills/manifest.json`, `.hyodo/chunks-manifest.json`,
`.hyodo/connect.json`) to fill the skills/memory/routines rings — no
network call, ever, and no new artifact is written.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from hyodo.policy import path_outside_root

#: Fixed column order (spec section 2): Truth, Goodness, Beauty, Benevolence,
#: Hyo. Eternity is not a column — it is read off the orb (section 4).
VIRTUE_COLUMNS: tuple[str, ...] = ("jin", "seon", "mi", "in", "hyo")

#: Gutter sentinel for an event the mapping table (spec section 3, as
#: amended by this PR's brief finding 3) does not match at all. Distinct
#: from the empty list `assign_columns` returns for a digest-less
#: `model_response`, which matches the table's own "no column" row on
#: purpose and is not unclassified.
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
#: Owner review round 2 (brief finding 3): a test runner is a Truth event
#: (it proves a claim), not a Goodness one — Goodness stays reserved for
#: the policy decision that gated it. Overrides the original spec section
#: 3 table row, which this PR's brief supersedes.
_TEST_RUNNER_PATTERNS: tuple[str, ...] = ("test", "pytest", "jest", "vitest", "mocha")
#: Section 3 table, row 6: "formatter" -> Beauty.
_FORMATTER_PATTERNS: tuple[str, ...] = ("format", "fmt", "prettier", "black", "gofmt")
#: Section 3 table, row 7: "doc/onboarding tools" -> Benevolence.
_DOC_PATTERNS: tuple[str, ...] = ("doc", "readme", "onboard", "changelog")
#: Owner review round 2 (brief finding 3): a file read/write/edit is a Hyo
#: event (it touches the project's own boundary) unless it was ASK/DENY-
#: gated or the path itself sits outside the checkout, in which case the
#: decision is the salient fact, not the file touch.
#:
#: #204 item 26: the original two entries here (`read_file`, `write_file`)
#: were placeholder/demo names that no real host ever sends, so a real
#: Claude Code transcript's `Read`/`Write`/`NotebookEdit` events fell
#: through to the unclassified gutter instead of Hyo/Goodness. This is an
#: exact (post-lowercasing) name set, not a substring list like the other
#: `_..._PATTERNS` tuples above — `read`/`write` as *substrings* would
#: also match unrelated names such as `readme` or `already_written`, which
#: `_DOC_PATTERNS` already owns. Two host families are covered:
#: - Claude Code (`Read`, `Write`, `Edit`, `MultiEdit`, `NotebookEdit`)
#: - Cursor and this repo's own fixtures/demo tooling (`read_file`,
#:   `write_file`, `edit_file`, bare `edit`)
_FILE_TOOL_NAMES: frozenset[str] = frozenset(
    {
        # Claude Code.
        "read",
        "write",
        "edit",
        "multiedit",
        "notebookedit",
        # Cursor / demo / this repo's own fixtures.
        "read_file",
        "write_file",
        "edit_file",
    }
)
#: Owner review round 2 (brief finding 3): a network fetch is a Goodness
#: event (it is exactly the kind of action `evaluate_policy` gates).
_WEB_TOOL_PATTERNS: tuple[str, ...] = ("web_fetch", "browser", "http")

#: Section 3 table, row 8: data-boundary rule ids -> Hyo.
_HYO_RULE_IDS = frozenset({"data_boundary", "data_boundary_undeclared"})
#: Section 3 table, row 9: web-credential rule ids -> Goodness + Hyo.
_WEB_CREDENTIAL_RULE_IDS = frozenset(
    {"web_credential_path_denied", "web_credential_path_unobserved"}
)


def _matches(name: str, patterns: tuple[str, ...]) -> bool:
    return bool(name) and any(pattern in name for pattern in patterns)


def _is_outside_root(paths: list[Any], root: Path | None) -> bool | None:
    """Return whether any of *paths* resolves outside *root*.

    `True`/`False` mirror `hyodo.policy.evaluate_policy`'s own
    ``path_outside_root:`` check exactly (`hyodo.policy.path_outside_root`,
    the one shared implementation) — an absolute path that happens to sit
    under *root* reads as inside, not outside, the same way policy reads
    it; only a path that actually resolves elsewhere (a `..` escape, a
    different absolute tree entirely) reads as outside.

    `None` means "unknown": *root* was not available to resolve against
    (`assign_columns` was called on a graph payload with no `root` field
    and no root passed explicitly). The caller must not guess Hyo or
    Goodness in that case — the #206 judge finding this PR fixes was
    exactly that guess (every absolute path silently read as outside root
    regardless of where the real project root was).
    """
    if root is None:
        return None
    for path in paths:
        if not isinstance(path, str) or not path:
            continue
        if path_outside_root(path, root):
            return True
    return False


def assign_columns(node: dict[str, Any], root: Path | None = None) -> list[str]:
    """Place one graph node (spec section 3's event -> virtue mapping table).

    `node` is one entry of `build_event_graph(...)["nodes"]`. Returns the
    virtue column keys (`VIRTUE_COLUMNS`) this event matches, in fixed
    column order, spanning every matched row rather than forcing a single
    pick. A `prompt` event (the mission's own root) always maps to Hyo. A
    `model_response` maps to Beauty only when it carries an observed
    `io.output_digest`; without one it returns an empty list — it still
    feeds the time axis, but nothing was measured to classify, so it is
    never counted against the unclassified gutter either. Any other event
    matching no row returns `[UNCLASSIFIED]`.

    `root` is the project checkout the file-tool Hyo/Goodness split
    resolves paths against (`_is_outside_root`, mirroring
    `hyodo.policy.evaluate_policy`'s own boundary check) — pass the same
    `root` the caller already resolved the ledger with (`build_event_graph`
    also stamps it onto the graph payload's own ``root`` field for a
    caller working from the JSON alone, e.g. `orb_state`). Omitting it does
    not fall back to guessing from the path text: a file-tool event with no
    root to check against lands in the unclassified gutter (unless another
    row also matches it), never silently Hyo or Goodness.
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
            _add("jin")
        if _matches(name, _FORMATTER_PATTERNS):
            _add("mi")
        if _matches(name, _DOC_PATTERNS):
            _add("in")
        if name in _FILE_TOOL_NAMES:
            raw_paths = tool.get("paths") if isinstance(tool, dict) else None
            paths = raw_paths if isinstance(raw_paths, list) else []
            if node.get("decision") in ("ASK", "DENY"):
                _add("seon")
            else:
                outside = _is_outside_root(paths, root)
                if outside is True:
                    _add("seon")
                elif outside is False:
                    _add("hyo")
                # outside is None: root unknown, do not guess — this row
                # neither adds Hyo nor Goodness, so the node falls through
                # to the unclassified gutter unless another row matches it.
        if _matches(name, _WEB_TOOL_PATTERNS):
            _add("seon")
    if kind == "error":
        _add("jin")
    if kind == "prompt":
        # Owner review round 2 (brief finding 3): the mission's own prompt
        # is the Hyo chain's root (`hyo_chain` marks it filial by
        # definition), so it renders in the Hyo column rather than
        # feeding the time axis with no column at all.
        _add("hyo")
    if kind == "model_response":
        raw_io = node.get("io")
        io = raw_io if isinstance(raw_io, dict) else {}
        if io.get("output_digest"):
            _add("mi")
        else:
            # Owner review round 2 (brief finding 3): a model response with
            # no observed output digest carries no evidence to place on a
            # column — it still feeds the time axis, but not the gutter
            # (nothing was measured to classify, so nothing is
            # unclassified either).
            return []
    if rule_id in _HYO_RULE_IDS:
        _add("hyo")
    if rule_id in _WEB_CREDENTIAL_RULE_IDS:
        _add("seon")
        _add("hyo")

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


def orb_state(graph: dict[str, Any], root: Path | None = None) -> dict[str, Any]:
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

    `root` overrides the checkout `assign_columns`'s file-tool Hyo/Goodness
    split resolves paths against; when omitted, this falls back to the
    graph payload's own ``root`` field (`build_event_graph` stamps it
    there) so a caller working from the JSON alone still classifies real
    paths correctly instead of guessing from path text.
    """
    raw_nodes = graph.get("nodes")
    raw_edges = graph.get("edges")
    nodes: list[dict[str, Any]] = raw_nodes if isinstance(raw_nodes, list) else []
    edges: list[dict[str, Any]] = raw_edges if isinstance(raw_edges, list) else []
    if root is None:
        graph_root = graph.get("root")
        root = Path(graph_root) if isinstance(graph_root, str) and graph_root else None
    assignments = {
        node["id"]: assign_columns(node, root) for node in nodes if isinstance(node.get("id"), str)
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

    A row is one actor lineage, never one event. `human` and `hyodo` are
    each a single row (the schema's actor field stays coarse,
    `hyodo/events.py:37 ACTORS`). An `agent` lineage is a connected run of
    `parent_event_id` links between `agent`-actor events (`_lane_root`
    below) — so one real sub-agent calling several differently named tools
    in sequence stays *one* row, not one row per tool call — and is
    labelled, display-only, from the lineage's earliest event's
    `tool.name`; never a new schema field and never the row's identity
    (row identity is the lineage, `tool.name` only picks its label). When
    an event carries the optional `actor_id` field, row identity is
    instead `(actor, actor_id)` directly — key `agent:<actor_id>`, label
    `agent <actor_id>` — so two differently labelled agents in one run are
    always two rows even when one's `parent_event_id` chains into the
    other's; `_lane_root`'s walk also stops at the first `actor_id`
    boundary it meets, for the same reason. Absent `actor_id`, this is
    unchanged from before that field existed. A row nests under another
    row when its lineage's earliest event's `parent_event_id` resolves to
    a `tool_call` belonging to a different lineage — entirely derived from
    the `parent_event_id` edge Phase 1-B already ships.

    Returns `{"order": [row_key, ...], "rows": {row_key: {...}}}` where
    each row dict has `actor`, `label` (display text), `events` (node ids,
    earliest first), `parent_row` (`None` for a top-level row), `depth`
    (`0` for a top-level row, otherwise one more than its `parent_row`'s
    depth — labelled `actor_id` chains can nest more than one level deep),
    `role` (coordinator ruling, additive, no schema change — see below),
    and `hyo_hierarchy` (same ruling).

    `role` is derived only from the graph, fixed precedence
    `human > orchestrator > reviewer > worker`:

    - `"human"`: the row's `actor` is `"human"`.
    - `"orchestrator"`: some *other* `agent`-actor row's first event's
      `parent_event_id` points at one of this row's events (this row
      spawned a child *agent* lane). A `human` or `hyodo` row landing as
      another row's child does not qualify — that is not spawned work,
      it is the mission or a policy evaluation citing back (fix round 1,
      coordinator live-screenshot review).
    - `"reviewer"`: this row has at least one event whose `evidence_refs`
      cite another actor's events (an `evidence_ref` edge whose source
      belongs to a different `actor`) *and* the row has no write-shaped
      tool call (`tool.name` containing `write`, `edit`, `create`,
      `delete`, `rm`, `patch`, `commit`, or `push`, case-insensitive).
    - `"worker"`: none of the above.

    `hyo_hierarchy` is `{"own_connected": bool, "children": int,
    "children_disconnected": int}`: `own_connected` is `True` when every
    one of this row's own events chains to its run's mission
    (`hyo_chain`, section 3's structural Hyo check); `children` counts
    this row's direct `parent_row` children only (never grandchildren —
    an orchestrator row's own `children_disconnected` is filled in from
    its direct children's already-computed `own_connected`, so no
    recursive re-walk is needed even when `depth` goes past 1);
    `children_disconnected` counts those
    children whose own `own_connected` is `False` — an orchestrator row
    inherits its children's orphaned counts this way, without re-walking
    the chain itself.
    """
    parent_of: dict[str, str] = {}
    for edge in edges:
        if edge.get("type") == "parent_event_id":
            target, source = edge.get("target"), edge.get("source")
            if isinstance(target, str) and isinstance(source, str):
                parent_of[target] = source
    node_by_id = {node["id"]: node for node in nodes if isinstance(node.get("id"), str)}

    def _sort_key(node: dict[str, Any]) -> int:
        """Sort nodes by `step_index`, treating a missing one as earliest."""
        step = node.get("step_index")
        return step if isinstance(step, int) and not isinstance(step, bool) else 0

    def _actor_id(node: dict[str, Any] | None) -> str | None:
        value = node.get("actor_id") if isinstance(node, dict) else None
        return value if isinstance(value, str) and value else None

    def _lane_root(node_id: str) -> str:
        """Walk `parent_event_id` up while the parent is also `agent`-actor.

        Two `agent`-actor events belong to the same lineage (row) exactly
        when this returns the same id for both — the actor lineage, never
        a `tool.name`, is the row identity. The walk also stops the moment
        the parent event carries a different `actor_id` than the current
        event — two labelled agents are always two rows, even when one's
        `parent_event_id` chains into the other's.
        """
        current = node_id
        seen = {node_id}
        while True:
            parent_id = parent_of.get(current)
            if not isinstance(parent_id, str):
                return current
            parent_node = node_by_id.get(parent_id)
            if parent_node is None or parent_node.get("actor") != "agent":
                return current
            if _actor_id(parent_node) != _actor_id(node_by_id.get(current)):
                return current
            if parent_id in seen:
                return current
            seen.add(parent_id)
            current = parent_id

    def _tool_name(node: dict[str, Any]) -> str | None:
        tool = node.get("tool") if isinstance(node.get("tool"), dict) else {}
        name = tool.get("name") if isinstance(tool, dict) else None
        return name if isinstance(name, str) and name else None

    def _row_key_and_label(node: dict[str, Any]) -> tuple[str, str]:
        """Stable row id + display label for *node*'s lineage (not the event itself).

        When the event carries an `actor_id`, row identity is
        `(actor, actor_id)` directly — key `agent:<actor_id>`, label
        `agent <actor_id>` — regardless of `parent_event_id` topology, so
        two labelled agents (e.g. two orchestrated sub-agents in one run)
        never collapse into one row and the same labelled agent's events
        always land in one row. Absent `actor_id`, behaviour is unchanged
        (lineage derived from `_lane_root`'s `parent_event_id` walk).
        """
        actor = node.get("actor")
        if actor != "agent":
            label = str(actor) if actor else "unknown"
            return label, label
        actor_id = _actor_id(node)
        if actor_id is not None:
            return f"agent:{actor_id}", f"agent {actor_id}"
        node_id = node.get("id")
        root_id = _lane_root(node_id) if isinstance(node_id, str) else str(node_id)
        root_node = node_by_id.get(root_id, node)
        tool_name = _tool_name(root_node)
        label = f"agent:{tool_name}" if tool_name else "agent"
        return f"agent:{root_id}", label

    rows: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for node in sorted(nodes, key=_sort_key):
        node_id = node.get("id")
        if not isinstance(node_id, str):
            continue
        key, label = _row_key_and_label(node)
        if key not in rows:
            rows[key] = {
                "actor": node.get("actor"),
                "label": label,
                "events": [],
                "parent_row": None,
            }
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
            parent_key, _parent_label = _row_key_and_label(parent_node)
            if parent_key != key:
                row["parent_row"] = parent_key

    # `depth`: 0 for a top-level row, otherwise one more than its
    # `parent_row`'s depth. A cycle (only reachable via a malformed/hand-
    # edited ledger) is broken by treating the row that closes it as
    # top-level rather than looping forever.
    depth_by_key: dict[str, int] = {}

    def _depth(key: str, seen: set[str] | None = None) -> int:
        if key in depth_by_key:
            return depth_by_key[key]
        parent_key = rows.get(key, {}).get("parent_row")
        if not isinstance(parent_key, str) or parent_key not in rows:
            depth_by_key[key] = 0
            return 0
        seen = seen if seen is not None else set()
        if key in seen:
            depth_by_key[key] = 0
            return 0
        seen.add(key)
        value = _depth(parent_key, seen) + 1
        depth_by_key[key] = value
        return value

    for key in order:
        rows[key]["depth"] = _depth(key)

    # Coordinator ruling (additive, no schema change): `role` and
    # `hyo_hierarchy`, both derived only from `nodes`/`edges` already
    # gathered above.
    chain = hyo_chain(nodes, edges)
    for key in order:
        row = rows[key]
        row["hyo_hierarchy"] = {
            "own_connected": all(chain.get(event_id, False) for event_id in row["events"]),
            "children": 0,
            "children_disconnected": 0,
        }
    for key in order:
        parent_key = rows[key].get("parent_row")
        if not isinstance(parent_key, str) or parent_key not in rows:
            continue
        parent_hierarchy = rows[parent_key]["hyo_hierarchy"]
        parent_hierarchy["children"] += 1
        if not rows[key]["hyo_hierarchy"]["own_connected"]:
            parent_hierarchy["children_disconnected"] += 1

    def _has_write_tool_call(row_events: list[str]) -> bool:
        for event_id in row_events:
            node = node_by_id.get(event_id)
            if node is None:
                continue
            tool = node.get("tool") if isinstance(node.get("tool"), dict) else {}
            name = str(tool.get("name") or "").lower() if isinstance(tool, dict) else ""
            if name and any(word in name for word in _WRITE_TOOL_WORDS):
                return True
        return False

    def _cites_another_actor(row_events: list[str], actor: Any) -> bool:
        row_event_ids = set(row_events)
        for edge in edges:
            if edge.get("type") != "evidence_ref" or edge.get("target") not in row_event_ids:
                continue
            source_id = edge.get("source")
            source_node = node_by_id.get(source_id) if isinstance(source_id, str) else None
            if source_node is not None and source_node.get("actor") != actor:
                return True
        return False

    orchestrator_keys: set[str] = set()
    for key in order:
        row = rows[key]
        # Fix round 1 (coordinator, live screenshot): only an `agent` child
        # lane makes its spawning row an orchestrator. A `human` or `hyodo`
        # row landing as another row's child (e.g. `hyodo` citing back to
        # the row it evaluated) is not itself "spawned work" — it stays
        # whatever `_cites_another_actor`/write-tool-call already ruled.
        agent_first_events = {
            rows[other]["events"][0]
            for other in order
            if other != key and rows[other]["events"] and rows[other]["actor"] == "agent"
        }
        owned_events = set(row["events"])
        if any(parent_of.get(first_event) in owned_events for first_event in agent_first_events):
            orchestrator_keys.add(key)

    for key in order:
        row = rows[key]
        if row["actor"] == "human":
            row["role"] = "human"
        elif key in orchestrator_keys:
            row["role"] = "orchestrator"
        elif _cites_another_actor(row["events"], row["actor"]) and not _has_write_tool_call(
            row["events"]
        ):
            row["role"] = "reviewer"
        else:
            row["role"] = "worker"

    return {"order": order, "rows": rows}


#: Case-insensitive substring markers for a "write-shaped" tool call
#: (coordinator ruling, `build_actor_rows`'s reviewer-role detection).
_WRITE_TOOL_WORDS: tuple[str, ...] = (
    "write",
    "edit",
    "create",
    "delete",
    "rm",
    "patch",
    "commit",
    "push",
)


def _read_json_object(path: Path) -> dict[str, Any] | None:
    """Read one JSON object from *path*; absent/unreadable/malformed -> `None`."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _build_skills_ring(root: Path) -> dict[str, Any]:
    """Skills ring (spec section 5, ring 1): one entry per ingested skill.

    Reads `.hyodo/skills/manifest.json` (Stage 2-A) if present. Each entry
    is `{"name", "rule_ids", "pillar_profile"}`: `rule_ids` is the
    manifest's own `compiled_rule_ids` for that skill (already computed at
    ingest time, no re-parse needed); `pillar_profile` is a six-slot count
    of that skill's *compiled* rules per pillar
    (`hyodo.skills.PILLARS` order), re-derived live via
    `hyodo.skills.rules_for_manifest_entry` because the manifest itself
    only stores rule ids and digests, never a per-pillar tally. Absent
    manifest -> `{"status": "unobserved", "skills": []}`, per the brief
    ("not available until skill lenses ship" note, spec section 5).
    """
    from hyodo.skills import PILLARS as SKILL_PILLARS
    from hyodo.skills import load_manifest, rules_for_manifest_entry

    manifest, _status = load_manifest(root)
    if manifest is None:
        return {"status": "unobserved", "skills": []}
    entries = manifest.get("skills")
    entries = entries if isinstance(entries, list) else []
    skills: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        profile = dict.fromkeys(SKILL_PILLARS, 0)
        for rule in rules_for_manifest_entry(entry, root):
            if rule.compiled is None:
                continue
            for pillar in rule.pillars:
                if pillar in profile:
                    profile[pillar] += 1
        rule_ids = entry.get("compiled_rule_ids")
        skills.append(
            {
                "name": entry.get("name"),
                "rule_ids": list(rule_ids) if isinstance(rule_ids, list) else [],
                "pillar_profile": profile,
            }
        )
    return {"status": "ok" if skills else "unobserved", "skills": skills}


def _read_chunk_digests(root: Path) -> list[str]:
    """Absorbed-source chunk digests from `.hyodo/chunks-manifest.json` (Stage 2-B).

    2-B has not shipped yet (spec section 9's own inputs list), so this
    reads defensively: any shape other than `{"chunks": [{"digest": ...}]}`
    returns an empty list rather than raising. Digests only, per the
    memory-ring rule (spec section 5, ring 2) — chunk text never crosses
    this boundary.
    """
    data = _read_json_object(root / ".hyodo" / "chunks-manifest.json")
    chunks = data.get("chunks") if isinstance(data, dict) else None
    if not isinstance(chunks, list):
        return []
    digests: set[str] = set()
    for chunk in chunks:
        digest = chunk.get("digest") if isinstance(chunk, dict) else None
        if isinstance(digest, str):
            digests.add(digest)
    return sorted(digests)


def _build_memory_ring(
    row_events: list[dict[str, Any]], edges: list[dict[str, Any]], root: Path
) -> dict[str, Any]:
    """Memory ring (spec section 5, ring 2): this row's cited events plus chunk digests.

    "Events this actor cited" is read off already-validated `evidence_ref`
    edges (never a broken ref, per `hyodo.event_graph.build_event_graph`),
    restricted to edges whose citing event (`target`) is one of this row's
    own `kind == "decision"` events, per the brief. Every node in this ring
    cites the event id it came from, by construction (it *is* an event id
    or a gate id, never new text).
    """
    decision_ids = {event.get("id") for event in row_events if event.get("kind") == "decision"}
    cited: set[str] = set()
    for edge in edges:
        if edge.get("type") != "evidence_ref" or edge.get("target") not in decision_ids:
            continue
        source = edge.get("source")
        if isinstance(source, str):
            cited.add(source)
    chunk_digests = _read_chunk_digests(root)
    events = sorted(cited)
    return {
        "status": "ok" if events or chunk_digests else "unobserved",
        "events": events,
        "chunk_digests": chunk_digests,
    }


def _build_routines_ring(row_events: list[dict[str, Any]], root: Path) -> dict[str, Any]:
    """Routines ring (spec section 5, ring 3): repeated tool-call patterns + connect targets.

    "Repeated" is `tool.name` recurring at least twice across this row's
    own `tool_call`/`tool_result` events (counts only, never percentages,
    Ruling 4). `.hyodo/connect.json` (Phase 1-D) contributes the harnesses
    already wired for this project — not actor-specific, since `connect`
    state carries no actor attribution, so every row sees the same list.
    """
    names = [
        event["tool"]["name"]
        for event in row_events
        if isinstance(event.get("tool"), dict) and isinstance(event["tool"].get("name"), str)
    ]
    counts = Counter(names)
    tool_counts = {name: count for name, count in sorted(counts.items()) if count >= 2}

    from hyodo.connect import load_connect_state

    state = load_connect_state(root)
    targets = state.get("targets")
    connect_targets = sorted(targets.keys()) if isinstance(targets, dict) else []

    return {
        "status": "ok" if tool_counts or connect_targets else "unobserved",
        "tool_counts": tool_counts,
        "connect_targets": connect_targets,
    }


def _build_tools_ring(
    row_events: list[dict[str, Any]],
    all_nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    """Tools ring (spec section 5, ring 4): one node per distinct `tool.name`.

    Colour key is the *latest* `policy.decision` for that tool, per the
    brief. A `decision`-kind event's own `parent_event_id` is the
    `tool_call` it evaluates (the same convention `hyodo/dashboard.py`'s
    fixtures and the local viewer already assume); this walks that link
    across the *whole* graph (`all_nodes`/`edges`), not just this row,
    because the decision event's actor is `hyodo`, never this row's own
    actor. `"UNOBSERVED"` when no decision was ever recorded for any call
    of that tool.
    """
    parent_of: dict[str, str] = {}
    for edge in edges:
        if edge.get("type") == "parent_event_id":
            target, source = edge.get("target"), edge.get("source")
            if isinstance(target, str) and isinstance(source, str):
                parent_of[target] = source

    latest_decision_by_call: dict[str, tuple[str, str]] = {}
    for node in all_nodes:
        if node.get("kind") != "decision":
            continue
        node_id = node.get("id")
        call_id = parent_of.get(node_id) if isinstance(node_id, str) else None
        decision = node.get("decision")
        ts = node.get("ts")
        if not isinstance(call_id, str) or not isinstance(decision, str) or not decision:
            continue
        ts_key = ts if isinstance(ts, str) else ""
        existing = latest_decision_by_call.get(call_id)
        if existing is None or ts_key >= existing[0]:
            latest_decision_by_call[call_id] = (ts_key, decision)

    tool_names: dict[str, list[str]] = {}
    for event in row_events:
        if event.get("kind") != "tool_call":
            continue
        tool = event.get("tool") if isinstance(event.get("tool"), dict) else {}
        name = tool.get("name") if isinstance(tool, dict) else None
        event_id = event.get("id")
        if isinstance(name, str) and name and isinstance(event_id, str):
            tool_names.setdefault(name, []).append(event_id)

    tools: list[dict[str, Any]] = []
    for name in sorted(tool_names):
        latest_ts = ""
        decision = "UNOBSERVED"
        for call_id in tool_names[name]:
            entry = latest_decision_by_call.get(call_id)
            if entry is not None and entry[0] >= latest_ts:
                latest_ts, decision = entry
        tools.append({"name": name, "decision": decision})

    return {"status": "ok" if tools else "unobserved", "tools": tools}


def build_actor_rings(graph: dict[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    """Build every actor row's four-ring content (spec section 5).

    `graph` is a full `hyodo.evidence-graph/v1` dict
    (`hyodo.report.build_report_graph(root)`); `root` is the checkout
    whose local artifacts feed the rings (never the network, per the
    brief). Returns `{row_key: {"skills", "memory", "routines", "tools"}}`
    for *every* row `build_actor_rows` derives from `graph`, keyed exactly
    the way that function keys its own `rows` dict — `GET /api/actor?key=`
    (`hyodo/dashboard.py`) looks a single key up in this dict and 404s
    when it is absent, per Ruling 3.

    Reading inward to outward (spec section 5): `skills` is the innermost
    ring and is the same for every row (skill ingestion carries no
    per-actor attribution in the schema); `memory`, `routines`, and
    `tools` are each derived from that specific row's own events.
    """
    raw_nodes = graph.get("nodes")
    raw_edges = graph.get("edges")
    nodes: list[dict[str, Any]] = raw_nodes if isinstance(raw_nodes, list) else []
    edges: list[dict[str, Any]] = raw_edges if isinstance(raw_edges, list) else []
    node_by_id = {node["id"]: node for node in nodes if isinstance(node.get("id"), str)}
    rows_tree = build_actor_rows(nodes, edges)
    skills_ring = _build_skills_ring(root)

    rings: dict[str, dict[str, Any]] = {}
    for key, row in rows_tree["rows"].items():
        row_events = [
            node_by_id[event_id] for event_id in row.get("events", []) if event_id in node_by_id
        ]
        rings[key] = {
            "skills": skills_ring,
            "memory": _build_memory_ring(row_events, edges, root),
            "routines": _build_routines_ring(row_events, root),
            "tools": _build_tools_ring(row_events, nodes, edges),
        }
    return rings
