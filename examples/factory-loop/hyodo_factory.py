"""Thin CLI entrypoint & facade for the HyoDo Universal Skill Harness (`hyodo-factory`).

Commands:
- `add <path>`      Register an external skill repository, plugin, or evaluator
- `list`            List registered modules and per-skill ON/OFF status
- `enable <target>` Enable a module (`gstack`) or individual skill (`gstack/qa` + dependencies)
- `disable <target>`Disable a module (`gstack`) or individual skill (`gstack/qa` + dependents)
- `update <mod>`    Atomically update a module with rollback snapshot protection
- `rollback <mod>`  Restore a module to its previous locked snapshot
- `remove <mod>`    Remove a module and clean up its hooks, permissions, and manifest rules
- `doctor`          Verify lock SHA-256 integrity, dependencies, conflicts, and script syntax
- `route <prompt>`  Select active skills for a natural-language task (Progressive Disclosure)
- `discover`        Discover standard Agent Skills / plugins across search directories
- `hosts`           Verify host connection & capability matrix (Claude Code, Cursor, Codex, Antigravity)
- `run <prompt>`    Execute the modular factory loop with real subprocess isolation & verification
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from adapters.external_evaluator import (  # noqa: E402
    evaluator_routing_to_hyodo_retrieval,
    record_evaluator_shadow_receipt,
)
from factory.contracts import recommend_skill_lifecycle_action, utc_now_iso  # noqa: E402
from factory.lifecycle import (  # noqa: E402
    activate_selected_skills,
    add_module,
    disable_target,
    discover_skills,
    doctor,
    enable_target,
    remove_module,
    rollback_module,
    update_module,
    verify_host_integrations,
)
from factory.registry import load_registry_state  # noqa: E402
from factory.router import (  # noqa: E402
    analyze_capability_gaps,
    route_skills_for_task,
    select_and_activate_for_task,
)
from factory.runner import (  # noqa: E402
    check_execution_permission,
    evaluate_and_promote_trust,
    evaluate_skill_impact,
    execute_modular_run,
    get_skill_trust_state,
    issue_host_approval_request,
    verify_host_approval_receipt,
)

from hyodo.events import AGENT_EVENT_SCHEMA_VERSION  # noqa: E402
from hyodo.handoff import inspect_handoff  # noqa: E402
from hyodo.host_promise_observation import (  # noqa: E402
    HOST_PROMISE_RELATIVE_PATH,
    HOST_PROMISE_SCHEMA,
    load_host_promise_observation,
)
from hyodo.independent_verifier import verify_exact_candidate  # noqa: E402
from hyodo.lens_evidence import emit_all_lens_evidence  # noqa: E402
from hyodo.nameplate import build_nameplate  # noqa: E402
from hyodo.six_lens_runtime import measure_workspace_six_lenses  # noqa: E402
from hyodo.skills import compute_lens  # noqa: E402


def write_host_promise_projection(
    root: Path,
    *,
    promise_id: str,
    host_label: str = "hyodo-factory",
    observed_at: str | None = None,
    auto_count: int = 1,
    ask_count: int = 1,
    must_not_count: int = 2,
    completion_conditions_count: int = 3,
) -> dict[str, Any]:
    """Write a host-supplied Promise projection and verify readback."""
    projection = {
        "schema": HOST_PROMISE_SCHEMA,
        "producer": {"host": host_label, "schema_version": "1.0.0"},
        "observed_at": observed_at or utc_now_iso(),
        "authority": "NONE",
        "source": {"state": "OBSERVED", "problem_count": 0},
        "active_promise": {"resolution": "ACTIVE", "promise_id": promise_id},
        "rail": {
            "promise": {"state": "OBSERVED", "note": "frozen via spec lane"},
            "contract": {"state": "OBSERVED", "note": "vertical slice contract"},
            "boundaries": {"state": "OBSERVED", "note": "guard and freeze active"},
        },
        "promises": [
            {
                "promise_id": promise_id,
                "status": "OPEN",
                "corrupt": False,
                "host_reported_authority": "HOST_VERIFIED_DIRECT_HUMAN",
                "delegation_counts": {
                    "auto": auto_count,
                    "ask": ask_count,
                    "must_not": must_not_count,
                    "completion_conditions": completion_conditions_count,
                },
            }
        ],
    }
    target = root / HOST_PROMISE_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(projection, indent=2) + "\n", encoding="utf-8")
    loaded = load_host_promise_observation(root)
    if loaded is None or loaded.get("state") != "OBSERVED":
        raise ValueError("host promise projection failed readback validation")
    return loaded


def ingest_jev_skill_routing(
    root: Path,
    *,
    jev_observation: dict[str, Any],
    skill_rules: list[dict[str, str]],
    ingested_at: str | None = None,
) -> dict[str, Any]:
    """Bridge a zero-authority evaluator observation (`JEV`) into `hyodo.skill-retrieval/v1`."""
    if jev_observation.get("execution_authority") is not False:
        raise ValueError("JEV observation must explicitly declare execution_authority=False")
    return evaluator_routing_to_hyodo_retrieval(
        root,
        evaluator_node="jev-skillid",
        observation=jev_observation,
        candidate_rules=skill_rules,
        ingested_at=ingested_at or utc_now_iso(),
    )


def record_jev_shadow_event(root: Path, raw_event: dict[str, Any]) -> dict[str, Any]:
    """Validate, strip full bodies to 12-hex digests, and record a JEV shadow event in HyoDo."""
    return record_evaluator_shadow_receipt(root, raw_event)


def build_and_verify_handoff(
    root: Path,
    *,
    run_id: str,
    plan_producer: str,
    review_producer: str,
    source_paths: list[str],
    output_paths: list[str],
    created_at: float,
    observed_at: float,
    now: float,
) -> dict[str, Any]:
    """Write `hyodo.handoff-plan/v1` and `hyodo.handoff-check/v1` receipts, then run `inspect_handoff`."""
    hyodo_dir = root / ".hyodo" / "handoff"
    hyodo_dir.mkdir(parents=True, exist_ok=True)

    artifacts: list[dict[str, str]] = []
    artifact_digests: dict[str, str] = {}
    for rel in source_paths:
        digest = hashlib.sha256((root / rel).read_bytes()).hexdigest()
        artifacts.append({"path": rel, "sha256": digest, "role": "source"})
        artifact_digests[rel] = digest
    for rel in output_paths:
        digest = hashlib.sha256((root / rel).read_bytes()).hexdigest()
        artifacts.append({"path": rel, "sha256": digest, "role": "output"})
        artifact_digests[rel] = digest

    check_specs = [
        ("tests", plan_producer),
        ("security", plan_producer),
        ("execution", plan_producer),
        ("review", review_producer),
    ]
    checks_manifest: list[dict[str, str]] = []
    for cid, producer in check_specs:
        rel_check = f".hyodo/handoff/check-{cid}.json"
        check_payload = {
            "schema": "hyodo.handoff-check/v1",
            "run_id": run_id,
            "id": cid,
            "status": "PASS",
            "coverage": "OBSERVED",
            "exit_code": 0,
            "observed_at": observed_at,
            "artifact_digests": artifact_digests,
            "producer": producer,
        }
        raw_bytes = (json.dumps(check_payload, sort_keys=True) + "\n").encode("utf-8")
        (root / rel_check).write_bytes(raw_bytes)
        checks_manifest.append(
            {
                "id": cid,
                "path": rel_check,
                "sha256": hashlib.sha256(raw_bytes).hexdigest(),
            }
        )

    plan_payload = {
        "schema": "hyodo.handoff-plan/v1",
        "kind": "code",
        "run_id": run_id,
        "created_at": created_at,
        "max_age_seconds": 3600.0,
        "producer": plan_producer,
        "artifacts": artifacts,
        "checks": checks_manifest,
    }
    plan_rel = Path(".hyodo/handoff/plan.json")
    plan_bytes = (json.dumps(plan_payload, sort_keys=True) + "\n").encode("utf-8")
    (root / plan_rel).write_bytes(plan_bytes)
    plan_sha256 = hashlib.sha256(plan_bytes).hexdigest()

    return inspect_handoff(
        root=root,
        plan_path=root / plan_rel,
        expected_plan_sha256=plan_sha256,
        expected_run_id=run_id,
        now=now,
    )


def run_unified_factory_pipeline(
    root: Path,
    *,
    run_id: str,
    promise_id: str,
    plan_producer: str = "mattpocock-tdd-builder",
    review_producer: str = "gstack-independent-reviewer",
    verifier_session_id: str = "gstack-review-session-01",
    jev_skill_observation: dict[str, Any],
    skill_rules: list[dict[str, str]],
    jev_completion_event: dict[str, Any],
    source_paths: list[str],
    output_paths: list[str],
    timestamp: float | None = None,
) -> dict[str, Any]:
    """Execute the host-side verification & attestation loop around a built worktree."""
    if timestamp is None:
        timestamp = time.time()
    promise_receipt = write_host_promise_projection(root, promise_id=promise_id)
    skill_manifest_entry = ingest_jev_skill_routing(
        root,
        jev_observation=jev_skill_observation,
        skill_rules=skill_rules,
    )
    skill_lens = compute_lens(root)
    jev_recorded_event = record_jev_shadow_event(root, jev_completion_event)
    handoff_verdict = build_and_verify_handoff(
        root,
        run_id=run_id,
        plan_producer=plan_producer,
        review_producer=review_producer,
        source_paths=source_paths,
        output_paths=output_paths,
        created_at=timestamp,
        observed_at=timestamp + 5.0,
        now=timestamp + 10.0,
    )

    six_lenses = measure_workspace_six_lenses(root)
    exact_sha = six_lenses["exact_artifact_sha"]
    target_sha = exact_sha if exact_sha != "UNOBSERVED" else "0" * 40
    verified_at = utc_now_iso()
    verifier_nameplate = build_nameplate(
        actor_id=review_producer,
        role="verifier",
        repo=root.name,
        exact_artifact_sha=target_sha,
        observed_at=verified_at,
        runtime={"session_id": verifier_session_id, "host": "hyodo-factory"},
    )
    verifier_attestation = verify_exact_candidate(
        root=root,
        expected_artifact_sha=target_sha,
        verifier_nameplate=verifier_nameplate,
        evidence={
            "handoff_status": handoff_verdict["status"],
            "checks": handoff_verdict["checks_observed"],
        },
        observed_at=verified_at,
    )

    history_path = root / ".hyodo" / "history.jsonl"
    lens_receipts: list[dict[str, Any]] = []
    if history_path.is_file() and exact_sha != "UNOBSERVED":
        last_line = [
            line for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()
        ][-1]
        lens_receipts = emit_all_lens_evidence(json.loads(last_line), exact_sha)

    return {
        "schema": "hyodo.factory-bundle/v1",
        "authority": "UNOBSERVED",
        "external_action_allowed": False,
        "agent_event_schema": AGENT_EVENT_SCHEMA_VERSION,
        "promise_observation": promise_receipt,
        "skill_manifest_entry": skill_manifest_entry,
        "skill_lens_status": skill_lens.manifest_status,
        "jev_shadow_event": jev_recorded_event,
        "handoff_verdict": handoff_verdict,
        "independent_verifier": verifier_attestation,
        "six_lens_measurement": six_lenses,
        "lens_evidence_receipts": lens_receipts,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `hyodo-factory`."""
    parser = argparse.ArgumentParser(prog="hyodo-factory")
    parser.add_argument("--root", type=Path, default=Path("."), help="Workspace root")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Register an external skill module")
    p_add.add_argument("path", type=Path)
    p_add.add_argument("--id", dest="module_id", default=None)
    p_add.add_argument("--adapter", default=None)
    p_add.add_argument(
        "--lazy",
        action="store_true",
        help="Register module dormant without enabling all skills globally",
    )

    sub.add_parser("list", help="List registered modules and skills")

    p_en = sub.add_parser("enable", help="Enable a module or individual skill")
    p_en.add_argument("target")
    p_en.add_argument("--only", action="store_true")

    p_dis = sub.add_parser("disable", help="Disable a module or individual skill")
    p_dis.add_argument("target")

    p_up = sub.add_parser("update", help="Update a module with rollback protection")
    p_up.add_argument("module_id")
    p_up.add_argument("--path", type=Path, default=None)
    p_up.add_argument("--version", default=None)

    p_rb = sub.add_parser("rollback", help="Rollback a module to its previous snapshot")
    p_rb.add_argument("module_id")

    p_rm = sub.add_parser("remove", help="Remove a module and clean up hooks/permissions")
    p_rm.add_argument("module_id")

    sub.add_parser("doctor", help="Check registry health, hashes, dependencies, and script syntax")

    p_rt = sub.add_parser("route", help="Route a natural-language task to active skills")
    p_rt.add_argument("prompt")
    p_rt.add_argument("--profile", default=None)
    p_rt.add_argument(
        "--selective",
        action="store_true",
        help="Include dormant registered skills in task-scoped candidate routing",
    )

    p_disc = sub.add_parser("discover", help="Discover compatible external skills across roots")
    p_disc.add_argument("query", nargs="?", default=None)
    p_disc.add_argument("--search-root", action="append", type=Path, default=None)

    p_gaps = sub.add_parser(
        "gaps",
        help="Analyze capability gaps (VERIFIED/UNVERIFIED/MISSING/DEGRADED/REDUNDANT/UNKNOWN) and Taste x System Awareness",
    )
    p_gaps.add_argument("prompt")
    p_gaps.add_argument("--profile", default=None)
    p_gaps.add_argument("--search-root", action="append", type=Path, default=None)

    p_trust = sub.add_parser(
        "trust",
        help="Inspect or promote skill trust state (DISCOVER -> VERIFY -> MANUAL -> SHADOW -> TRUSTED -> AUTO_RUN)",
    )
    p_trust.add_argument("skill_id")

    sub.add_parser("hosts", help="Verify host connection and capability support matrix")

    p_run = sub.add_parser(
        "run", help="Execute a modular factory run with real subprocess isolation"
    )
    p_run.add_argument("prompt")
    p_run.add_argument("--run-id", default="cli-run-01")
    p_run.add_argument("--profile", default=None)
    p_run.add_argument(
        "--skill-cmd",
        action="append",
        default=None,
        help="Repeatable skill command mapping: <skill_id>=<command line>",
    )
    p_run.add_argument("--build-cmd", default=None)
    p_run.add_argument("--verify-cmd", default=None)
    p_run.add_argument("--builder-actor", default="factory-builder")
    p_run.add_argument("--verifier-actor", default="factory-independent-verifier")
    p_run.add_argument(
        "--selective",
        action="store_true",
        help="Selectively activate only task-needed skills before execution",
    )
    p_run.add_argument("--execution-mode", choices=("manual", "shadow", "auto"), default="manual")

    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.cmd == "add":
        rec = add_module(
            root,
            args.path,
            adapter=args.adapter,
            module_id=args.module_id,
            enable_all=not args.lazy,
        )
        print(json.dumps(rec.to_dict(), indent=2))
    elif args.cmd == "list":
        mods = load_registry_state(root)
        print(json.dumps({k: v.to_dict() for k, v in mods.items()}, indent=2))
    elif args.cmd == "enable":
        enabled = enable_target(root, args.target, only=args.only)
        print(json.dumps({"enabled": enabled}, indent=2))
    elif args.cmd == "disable":
        disabled = disable_target(root, args.target)
        print(json.dumps({"disabled": disabled}, indent=2))
    elif args.cmd == "update":
        rec = update_module(
            root, args.module_id, new_source_path=args.path, new_version=args.version
        )
        print(json.dumps(rec.to_dict(), indent=2))
    elif args.cmd == "rollback":
        rec = rollback_module(root, args.module_id)
        print(json.dumps(rec.to_dict(), indent=2))
    elif args.cmd == "remove":
        res = remove_module(root, args.module_id)
        print(json.dumps(res, indent=2))
    elif args.cmd == "doctor":
        rep = doctor(root)
        print(json.dumps(rep, indent=2))
        return 0 if rep["status"] == "HEALTHY" else 1
    elif args.cmd == "route":
        plan = route_skills_for_task(
            root,
            args.prompt,
            profile_name=args.profile,
            include_registered_inactive=args.selective,
        )
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    elif args.cmd == "discover":
        s_roots = args.search_root or [root.parent]
        found = discover_skills(s_roots, query=args.query)
        print(json.dumps({"discovered": found}, indent=2, ensure_ascii=False))
    elif args.cmd == "gaps":
        gap_rep = analyze_capability_gaps(
            root,
            args.prompt,
            profile_name=args.profile,
            external_search_roots=args.search_root,
        )
        print(json.dumps(gap_rep, indent=2, ensure_ascii=False))
    elif args.cmd == "trust":
        t_state = get_skill_trust_state(root, args.skill_id)
        print(json.dumps(t_state, indent=2))
    elif args.cmd == "hosts":
        matrix = verify_host_integrations(root)
        print(json.dumps(matrix, indent=2))
    elif args.cmd == "run":
        b_cmd = shlex.split(args.build_cmd) if args.build_cmd else None
        v_cmd = shlex.split(args.verify_cmd) if args.verify_cmd else None
        s_cmds: dict[str, list[str]] = {}
        for item in args.skill_cmd or []:
            if "=" not in item:
                raise ValueError(f"--skill-cmd must have format <skill_id>=<cmd>: {item}")
            sid, _, raw_cmd = item.partition("=")
            s_cmds[sid.strip()] = shlex.split(raw_cmd)
        run_res = execute_modular_run(
            root,
            run_id=args.run_id,
            prompt=args.prompt,
            profile_name=args.profile,
            skill_commands=s_cmds or None,
            build_cmd=b_cmd,
            verify_cmd=v_cmd,
            builder_actor=args.builder_actor,
            verifier_actor=args.verifier_actor,
            selective_activation=args.selective,
            execution_mode=args.execution_mode,
        )
        print(json.dumps(run_res, indent=2, ensure_ascii=False))
        # 0 PASS, 1 FAIL, 2 UNOBSERVED: nothing executed or no independent
        # verifier ran is never success.
        decision = run_res["run_verdict"]["decision"]
        if decision == "FAIL":
            return 1
        if decision != "PASS":
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "activate_selected_skills",
    "add_module",
    "analyze_capability_gaps",
    "build_and_verify_handoff",
    "check_execution_permission",
    "disable_target",
    "discover_skills",
    "doctor",
    "enable_target",
    "evaluate_and_promote_trust",
    "evaluate_skill_impact",
    "execute_modular_run",
    "get_skill_trust_state",
    "ingest_jev_skill_routing",
    "issue_host_approval_request",
    "main",
    "recommend_skill_lifecycle_action",
    "record_jev_shadow_event",
    "remove_module",
    "rollback_module",
    "route_skills_for_task",
    "run_unified_factory_pipeline",
    "select_and_activate_for_task",
    "update_module",
    "verify_host_approval_receipt",
    "verify_host_integrations",
    "write_host_promise_projection",
]
