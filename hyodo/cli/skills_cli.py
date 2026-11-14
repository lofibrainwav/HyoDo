"""CLI sub-applications for skill ingestion/lens/proposal and admission observations."""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from hyodo.admission_observation import append_admission_observation
from hyodo.events import (
    AGENT_EVENT_SCHEMA_VERSION,
    append_agent_event,
    count_run_events,
    unevaluated_policy,
    validate_event,
)
from hyodo.policy import (
    POLICY_RELATIVE_PATH,
    POLICY_SCHEMA_ID,
    PolicyConfig,
    PolicyDecision,
    apply_decision_to_event,
    evaluate_policy,
    try_load_policy,
)
from hyodo.skills import (
    MANIFEST_RELATIVE_PATH as SKILLS_MANIFEST_RELATIVE_PATH,
)
from hyodo.skills import (
    build_ingest_tool,
    build_node_ingest_tool,
    compute_lens,
    load_manifest,
    manifest_entry,
    node_manifest_entry,
    node_rules_for,
    parse_node_retrieval_file,
    parse_skill_rules,
    render_proposal,
    resolve_source,
    save_manifest,
    save_proposal,
    skill_name_for,
    validate_node_retrieval,
)
from hyodo.skills import (
    store_body as store_skill_body,
)

console = Console()

skills_app = typer.Typer(
    name="skills",
    help="Ingest a project's own skills as a lens over the six pillars",
    add_completion=False,
)

admission_app = typer.Typer(
    name="admission",
    help="Bounded policy-admission observations from an external executor",
    add_completion=False,
)


@admission_app.command("record")
def admission_record(
    file: str | None = typer.Option(
        None, "--file", "-f", help="Path to one hyodo.admission-observation/v1 JSON object"
    ),
    stdin_flag: bool = typer.Option(
        False, "--stdin", help="Read one admission observation from stdin"
    ),
    root: str = typer.Option(
        ".", "--root", help="Project root that owns .hyodo/admission-observations.jsonl"
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit a machine-readable JSON receipt"),
) -> None:
    """Validate and append one bounded external policy-admission observation."""
    if (file is None) == (not stdin_flag):
        result = {"ok": False, "reasons": ["provide_exactly_one_of_file_or_stdin"], "exit_code": 2}
        if json_output:
            console.print_json(json.dumps(result))
        else:
            console.print("[red]UNOBSERVED[/red] admission observation — input boundary invalid")
        raise typer.Exit(2)

    try:
        if stdin_flag:
            text = sys.stdin.read()
        else:
            assert file is not None
            text = Path(file).read_text(encoding="utf-8")
        payload = json.loads(text)
        normalized = append_admission_observation(Path(root).resolve(), payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        result = {"ok": False, "reasons": [str(error)], "exit_code": 2}
        if json_output:
            console.print_json(json.dumps(result))
        else:
            console.print(f"[red]UNOBSERVED[/red] admission observation — {error}")
        raise typer.Exit(2) from error

    result = {
        "ok": True,
        "schema": normalized["schema"],
        "observation_id": normalized["observation_id"],
        "exit_code": 0,
    }
    if json_output:
        console.print_json(json.dumps(result))
    else:
        console.print(f"[green]RECORDED[/green] {normalized['observation_id']}")


def _new_agent_event(
    *,
    kind: str,
    actor: str,
    tool: dict[str, Any] | None = None,
    run_id: str,
    step_index: int = 0,
) -> dict[str, Any]:
    """Build a minimal, unvalidated ``hyodo.agent-event/v1`` shell for HyoDo-synthesized events."""
    raw: dict[str, Any] = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "run_id": run_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "step_index": step_index,
        "actor": actor,
    }
    if tool is not None:
        raw["tool"] = tool
    return raw


_SKILLS_EXIT_CODES = {"ALLOW": 0, "DENY": 1, "UNOBSERVED": 2, "ASK": 3}


def _skills_ingest_from_node(
    *,
    from_node: str,
    root: str,
    yes: bool,
    json_output: bool,
) -> None:
    """``hyodo skills ingest --from-node <file>``: BYOM research-node hand-off."""
    root_path = Path(root).resolve()
    data, parse_reasons = parse_node_retrieval_file(Path(from_node))
    if data is None:
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": parse_reasons, "exit_code": 1}))
        else:
            console.print(f"[red]malformed retrieval file: {', '.join(parse_reasons)}[/red]")
        raise typer.Exit(1)

    retrieval, reasons = validate_node_retrieval(data)
    if retrieval is None:
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": reasons, "exit_code": 1}))
        else:
            console.print(f"[red]malformed retrieval file: {', '.join(reasons)}[/red]")
        raise typer.Exit(1)

    tool = build_node_ingest_tool(retrieval.node)
    run_id = str(uuid.uuid4())
    raw_event = _new_agent_event(kind="tool_call", actor="hyodo", tool=tool, run_id=run_id)
    ok, event_reasons, normalized = validate_event(raw_event)
    if not ok or normalized is None:  # pragma: no cover - internal construction guard
        message = f"internal error building node ingest event: {event_reasons}"
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": event_reasons, "exit_code": 2}))
        else:
            console.print(f"[red]{message}[/red]")
        raise typer.Exit(2)
    normalized["meta"]["tags"] = ["skills-ingest", "node"]

    policy_path = root_path / POLICY_RELATIVE_PATH
    cfg, policy_err = try_load_policy(policy_path)
    if cfg is None:
        if policy_err == "policy_missing":
            cfg = PolicyConfig(
                schema=POLICY_SCHEMA_ID,
                max_steps=None,
                allowed_tools=None,
                blocked_path_globs=(),
            )
        else:
            message = f"policy unobserved ({policy_err}); not ALLOW"
            if json_output:
                console.print_json(
                    json.dumps({"ok": False, "reasons": [policy_err], "exit_code": 2})
                )
            else:
                console.print(f"[red]{message}[/red]")
            raise typer.Exit(2)

    observed = count_run_events(root_path, run_id)
    decision = evaluate_policy(normalized, cfg, observed_steps=observed, root=root_path)
    stamped = apply_decision_to_event(normalized, decision)
    append_agent_event(root_path, stamped)

    effective_decision = decision.decision
    approval_event_id: str | None = None
    if decision.decision == "ASK" and yes:
        approval_claim = {
            "decision": "ALLOW",
            "rule_id": "operator_approval",
            "reason": "operator approved via --yes",
        }
        approval_raw = _new_agent_event(kind="decision", actor="human", run_id=run_id, step_index=1)
        ok2, _reasons2, approval_normalized = validate_event(approval_raw)
        if ok2 and approval_normalized is not None:
            approval_normalized["policy"] = unevaluated_policy(claimed=approval_claim)
            if append_agent_event(root_path, approval_normalized):
                approval_event_id = approval_normalized["event_id"]
                effective_decision = "ALLOW"

    manifest_data, manifest_status = load_manifest(root_path)
    existing_skills = (
        list(manifest_data.get("skills", []))
        if manifest_data is not None and manifest_status == "ok"
        else []
    )

    compiled_rule_count = 0
    if effective_decision == "ALLOW":
        rules = node_rules_for(retrieval)
        compiled_rule_count = sum(1 for rule in rules if rule.compiled is not None)
        entry = node_manifest_entry(retrieval, rules, ingested_at=stamped["event_id"])
        existing_skills = [
            row for row in existing_skills if row.get("source") != entry["source"]
        ] + [entry]
        save_manifest(root_path, existing_skills)

    exit_code = _SKILLS_EXIT_CODES[decision.decision]
    if effective_decision == "ALLOW" and decision.decision == "ASK":
        exit_code = 0

    result = {
        "decision": decision.decision,
        "effective_decision": effective_decision,
        "rule_id": decision.rule_id,
        "reason": decision.reason,
        "trust_level": decision.trust_level,
        "source": f"node:{retrieval.node}",
        "readable": True,
        "content_digest": None,
        "compiled_rule_count": compiled_rule_count,
        "manifest": str(root_path / SKILLS_MANIFEST_RELATIVE_PATH),
        "event_id": stamped["event_id"],
        "approval_event_id": approval_event_id,
        "exit_code": exit_code,
    }
    if json_output:
        console.print_json(json.dumps(result))
    else:
        console.print(f"[bold]{decision.decision}[/bold] node:{retrieval.node}")
        console.print(f"  reason: {decision.reason}")
        if effective_decision == "ALLOW" and decision.decision == "ASK":
            console.print("  approved via --yes; manifest compiled")
        elif effective_decision == "ALLOW":
            console.print(f"  compiled {compiled_rule_count} mechanical rule(s)")
        elif decision.decision == "ASK":
            console.print("  re-run with --yes, or grant trust level 3, to compile")
    raise typer.Exit(exit_code)


@skills_app.command("ingest")
def skills_ingest(
    source: str | None = typer.Argument(
        None, help="Local path or http(s) URL to a skill Markdown file"
    ),
    root: str = typer.Option(".", "--root", help="Project root that owns .hyodo/skills/"),
    from_node: str | None = typer.Option(
        None,
        "--from-node",
        help=(
            "Path to a hyodo.skill-retrieval/v1 JSON file from an external research "
            "node (BYOM); mutually exclusive with SOURCE"
        ),
    ),
    store_body: bool = typer.Option(
        False,
        "--store-body",
        help="Persist the skill body at .hyodo/skills/bodies/<digest>.md (default: not stored)",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Approve an ASK decision now; records a human_response approval event, then proceeds",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
) -> None:
    """
    Ingest one skill source as a lens: record it, evaluate policy, compile its
    rules into ``.hyodo/skills/manifest.json`` on a proceeding decision.

    Ingesting a skill is treated as an external variable exactly like a web
    fetch — never silently ALLOW. Exit 0 ALLOW, 1 DENY, 2 UNOBSERVED, 3 ASK
    (re-run with ``--yes`` or after granting trust level 3 to proceed).
    A ``url:`` source is never fetched in this package: only its domain is
    recorded, with ``content_digest: null`` and ``status: "unreadable"``.

    ``--from-node <file>`` takes a research node's ``hyodo.skill-retrieval/v1``
    hand-off instead of SOURCE: the node owns embeddings/vectors and never
    sends them, HyoDo stores only rule text (<= 512 chars), digests, and an
    ordinal rank. A malformed file exits 1 and writes nothing.
    """
    if from_node is not None:
        if source is not None:
            console.print("[red]pass either SOURCE or --from-node, not both[/red]")
            raise typer.Exit(1)
        _skills_ingest_from_node(from_node=from_node, root=root, yes=yes, json_output=json_output)
        return
    if source is None:
        console.print("[red]missing SOURCE (or pass --from-node)[/red]")
        raise typer.Exit(1)

    root_path = Path(root).resolve()
    parsed = resolve_source(root_path, source)
    tool = build_ingest_tool(parsed)
    run_id = str(uuid.uuid4())
    raw_event = _new_agent_event(kind="tool_call", actor="hyodo", tool=tool, run_id=run_id)
    ok, reasons, normalized = validate_event(raw_event)
    if not ok or normalized is None:  # pragma: no cover - internal construction guard
        message = f"internal error building ingest event: {reasons}"
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": reasons, "exit_code": 2}))
        else:
            console.print(f"[red]{message}[/red]")
        raise typer.Exit(2)

    policy_path = root_path / POLICY_RELATIVE_PATH
    cfg, policy_err = try_load_policy(policy_path)
    if cfg is None:
        if policy_err == "policy_missing":
            cfg = PolicyConfig(
                schema=POLICY_SCHEMA_ID,
                max_steps=None,
                allowed_tools=None,
                blocked_path_globs=(),
            )
        else:
            message = f"policy unobserved ({policy_err}); not ALLOW"
            if json_output:
                console.print_json(
                    json.dumps({"ok": False, "reasons": [policy_err], "exit_code": 2})
                )
            else:
                console.print(f"[red]{message}[/red]")
            raise typer.Exit(2)

    observed = count_run_events(root_path, run_id)
    decision = evaluate_policy(normalized, cfg, observed_steps=observed, root=root_path)
    stamped = apply_decision_to_event(normalized, decision)
    append_agent_event(root_path, stamped)

    effective_decision = decision.decision
    approval_event_id: str | None = None
    if decision.decision == "ASK" and yes:
        approval_claim = {
            "decision": "ALLOW",
            "rule_id": "operator_approval",
            "reason": "operator approved via --yes",
        }
        approval_raw = _new_agent_event(kind="decision", actor="human", run_id=run_id, step_index=1)
        ok2, _reasons2, approval_normalized = validate_event(approval_raw)
        if ok2 and approval_normalized is not None:
            approval_normalized["policy"] = unevaluated_policy(claimed=approval_claim)
            if append_agent_event(root_path, approval_normalized):
                approval_event_id = approval_normalized["event_id"]
                effective_decision = "ALLOW"

    manifest_data, manifest_status = load_manifest(root_path)
    existing_skills = (
        list(manifest_data.get("skills", []))
        if manifest_data is not None and manifest_status == "ok"
        else []
    )

    compiled_rule_count = 0
    if effective_decision == "ALLOW":
        rules = []
        if parsed.readable and parsed.content is not None:
            skill_name = skill_name_for(parsed.resolved_path) if parsed.resolved_path else "skill"
            rules = parse_skill_rules(skill_name, parsed.content)
            compiled_rule_count = sum(1 for rule in rules if rule.compiled is not None)
            if store_body and parsed.content_digest_value is not None:
                store_skill_body(root_path, parsed.content_digest_value, parsed.content)
        entry = manifest_entry(
            parsed,
            rules,
            ingested_at=stamped["event_id"],
            body_stored=bool(store_body and parsed.readable),
        )
        existing_skills = [
            row for row in existing_skills if row.get("source") != entry["source"]
        ] + [entry]
        save_manifest(root_path, existing_skills)

    exit_code = _SKILLS_EXIT_CODES[decision.decision]
    if effective_decision == "ALLOW" and decision.decision == "ASK":
        exit_code = 0

    result = {
        "decision": decision.decision,
        "effective_decision": effective_decision,
        "rule_id": decision.rule_id,
        "reason": decision.reason,
        "trust_level": decision.trust_level,
        "source": parsed.manifest_source,
        "readable": parsed.readable,
        "content_digest": parsed.content_digest_value,
        "compiled_rule_count": compiled_rule_count,
        "manifest": str(root_path / SKILLS_MANIFEST_RELATIVE_PATH),
        "event_id": stamped["event_id"],
        "approval_event_id": approval_event_id,
        "exit_code": exit_code,
    }
    if json_output:
        console.print_json(json.dumps(result))
    else:
        console.print(f"[bold]{decision.decision}[/bold] {parsed.manifest_source}")
        console.print(f"  reason: {decision.reason}")
        if effective_decision == "ALLOW" and decision.decision == "ASK":
            console.print("  approved via --yes; manifest compiled")
        elif effective_decision == "ALLOW":
            console.print(f"  compiled {compiled_rule_count} mechanical rule(s)")
        elif decision.decision == "ASK":
            console.print("  re-run with --yes, or grant trust level 3, to compile")
    raise typer.Exit(exit_code)


@skills_app.command("lens")
def skills_lens(
    root: str = typer.Option(".", "--root", help="Project root that owns .hyodo/skills/"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
) -> None:
    """
    Print per-pillar coverage/coherence from ingested skills, with provenance.

    Numbers are always integer ``observed/expected`` and ``passed/observed``
    pairs — never a percentage or a probability. A missing or malformed
    manifest is reported as unobserved (exit 2), while still rendering empty
    coverage rows. A source digest mismatch is also unobserved (exit 2) and
    its rules are not evaluated.
    """
    root_path = Path(root).resolve()
    result = compute_lens(root_path)

    if result.manifest_status == "malformed":
        typer.echo("manifest.json is malformed; treating as empty", err=True)

    if json_output:
        payload = {
            "manifest_status": result.manifest_status,
            "pillars": [
                {
                    "pillar": pillar.pillar,
                    "expected": pillar.expected,
                    "observed": pillar.observed,
                    "passed": pillar.passed,
                    "provenance": [
                        {"rule_id": rid, "skill": skill, "status": status}
                        for rid, skill, status in pillar.provenance
                    ],
                }
                for pillar in result.pillars
            ],
            "unclassified": {
                "pillar": result.unclassified.pillar,
                "expected": result.unclassified.expected,
                "observed": result.unclassified.observed,
                "passed": result.unclassified.passed,
                "provenance": [
                    {"rule_id": rid, "skill": skill, "status": status}
                    for rid, skill, status in result.unclassified.provenance
                ],
            },
            "unobserved": result.unobserved,
        }
        console.print_json(json.dumps(payload))
    else:
        for pillar in [*result.pillars, result.unclassified]:
            console.print(
                f"[bold]{pillar.pillar}[/bold]: "
                f"{pillar.observed}/{pillar.expected} observed, "
                f"{pillar.passed}/{pillar.observed} passed"
            )
            for rid, skill, status in pillar.provenance:
                console.print(f"    [{status}] {rid} ({skill})")
        console.print(f"unobserved: {len(result.unobserved)}")
        for item in result.unobserved:
            console.print(
                f"    {item['rule_id']} ({item['skill']}) digest={item['rule_text_digest']}"
            )

    exit_code = 2 if result.manifest_status in {"missing", "malformed", "mismatch"} else 0
    raise typer.Exit(exit_code)


@skills_app.command("propose")
def skills_propose(
    root: str = typer.Option(".", "--root", help="Project root that owns .hyodo/skills/"),
    accept: bool = typer.Option(
        False,
        "--accept",
        help="Write .hyodo/skills/proposed.md and record one ledger event",
    ),
) -> None:
    """
    Print a tailored custom skill made of every currently-passing compiled
    rule from ingested skills. Without --accept nothing is written and no
    event is recorded; --accept writes exactly one file and records exactly
    one ledger event. Never calls evaluate_policy — nothing external is
    contacted at proposal time, only sources already judged at ingest time.
    """
    root_path = Path(root).resolve()
    project_name = root_path.name or "project"
    result = render_proposal(root_path, project_name)

    if result.manifest_status == "malformed":
        typer.echo("manifest.json is malformed; proposal sections are empty", err=True)
    elif result.manifest_status == "mismatch":
        typer.echo(
            "manifest source digest mismatch; proposal was not accepted",
            err=True,
        )

    console.print(result.markdown, end="")

    if accept and result.manifest_status != "mismatch":
        save_proposal(root_path, result.markdown)
        run_id = str(uuid.uuid4())
        raw_event = _new_agent_event(
            kind="tool_call",
            actor="hyodo",
            tool={
                "name": "skills.propose",
                "paths": [str(SKILLS_MANIFEST_RELATIVE_PATH)],
                "urls": [],
            },
            run_id=run_id,
        )
        ok, _reasons, normalized = validate_event(raw_event)
        if ok and normalized is not None:
            decision = PolicyDecision(
                decision="ALLOW",
                rule_id=None,
                reason="skills propose: local render, no external variable; evaluate_policy not called",
                coverage=(0, 0),
                external_variables=(),
                trust_level=1,
            )
            stamped = apply_decision_to_event(normalized, decision)
            append_agent_event(root_path, stamped)

    raise typer.Exit(2 if result.manifest_status == "mismatch" else 0)
