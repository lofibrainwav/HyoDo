"""Candidate six-lens runtime assembled from nursery components."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hyodo.evidence_plate import (
    LENSES,
    extract_evidence_atoms,
    extract_lens_evidence,
    make_evidence_plate,
)

DIMENSIONS = (
    "freshness",
    "provenance",
    "safety",
    "clarity",
    "impact",
    "consent",
    "continuity",
    "reproducibility",
)
EXPERIMENTAL_PROJECTION = {
    "truth": ("freshness", "provenance", "reproducibility"),
    "goodness": ("safety",),
    "beauty": ("clarity",),
    "benevolence": ("impact",),
    "hyo": ("consent",),
    "eternity": ("continuity",),
}


def _artifact(value: Any) -> bool:
    """Validate the output binding without reimplementing atom extraction."""
    return (
        isinstance(value, str)
        and len(value) in {40, 64}
        and all(char in "0123456789abcdef" for char in value.lower())
    )


def measure_six_lenses(evidence: dict[str, Any]) -> dict[str, Any]:
    """Produce six independent evidence projections with explicit residuals."""
    artifact = evidence.get("exact_artifact_sha")
    atoms = extract_evidence_atoms(evidence)
    dimensions = {name: evidence.get(name, "UNOBSERVED") for name in DIMENSIONS}
    plates = []
    for lens in LENSES:
        selected, _ = extract_lens_evidence(atoms, lens)
        plate = make_evidence_plate(evidence, lens)
        if not selected:
            plate["residuals"].append("evidence_unobserved")
            plate["state"] = "UNOBSERVED"
        plates.append(plate)
    return {
        "schema_version": "hyodo.six-lens-measurement/v1",
        "exact_artifact_sha": artifact if _artifact(artifact) else "UNOBSERVED",
        "plates": plates,
        "projection_status": "EXPERIMENTAL",
        "experimental_dimensions": dimensions,
        "experimental_projection": {
            lens: list(keys) for lens, keys in EXPERIMENTAL_PROJECTION.items()
        },
        "components": [
            "C1:isolated-judges",
            "C2:shared-atoms",
            "C3:dimension-projection",
            "CX:unknown-preserved",
        ],
        "authority": "UNOBSERVED",
    }


def _last_history_entry(root: Path) -> dict[str, Any] | None:
    history_path = root / ".hyodo" / "history.jsonl"
    if not history_path.is_file():
        return None
    try:
        lines = [
            line.strip()
            for line in history_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except OSError:
        return None
    for raw in reversed(lines):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _pillar_gates_observed(gates: dict[str, Any], pillar: str) -> dict[str, str]:
    observed: dict[str, str] = {}
    for name in sorted(gates):
        row = gates.get(name)
        if not isinstance(row, dict) or row.get("pillar") != pillar:
            continue
        status = row.get("status")
        if status in {"PASS", "FAIL"}:
            observed[name] = str(status)
    return observed


def collect_workspace_six_lens_envelope(root: Path) -> dict[str, Any]:
    """Deterministically collect observed 6-lens evidence atoms from *root*.

    Reads only existing local receipts (``.hyodo/history.jsonl``,
    ``.hyodo/events.jsonl``, ``.hyodo/host-promise-observation.json``,
    ``.hyodo/gates-trust.json``, ``.hyodo/skills/lock.json``) and git state.
    Any dimension not backed by concrete local evidence remains ``UNOBSERVED``.
    """
    from hyodo.events import read_agent_events
    from hyodo.host_promise_observation import load_host_promise_observation
    from hyodo.independent_verifier import observe_candidate

    root = root.resolve()
    candidate = observe_candidate(root)
    commit = candidate.get("head_sha")
    exact_sha = (
        commit
        if (isinstance(commit, str) and _artifact(commit) and candidate.get("worktree") == "CLEAN")
        else "UNOBSERVED"
    )
    envelope: dict[str, Any] = dict.fromkeys(DIMENSIONS, "UNOBSERVED")
    envelope["exact_artifact_sha"] = exact_sha
    if exact_sha == "UNOBSERVED":
        return envelope

    history = _last_history_entry(root)
    if isinstance(history, dict):
        raw_prov = history.get("provenance")
        prov: dict[str, Any] = raw_prov if isinstance(raw_prov, dict) else {}
        raw_gates = history.get("gates")
        gates: dict[str, Any] = raw_gates if isinstance(raw_gates, dict) else {}
        if prov.get("target_commit") == exact_sha and prov.get("target_dirty") is False:
            envelope["freshness"] = {"status": "FRESH", "target_commit": exact_sha}
            if prov.get("validity") == "OBSERVED":
                envelope["provenance"] = {
                    "validity": "OBSERVED",
                    "relation": prov.get("relation", "UNOBSERVED"),
                    "target_commit": exact_sha,
                }
            input_digest = history.get("input_digest")
            if isinstance(input_digest, dict):
                before = input_digest.get("before")
                after = input_digest.get("after")
                if isinstance(before, str) and before and before == after:
                    envelope["reproducibility"] = {"input_digest": before, "stable": True}
            safety_gates = _pillar_gates_observed(gates, "goodness")
            if safety_gates:
                envelope["safety"] = {"gates": safety_gates}
            clarity_gates = _pillar_gates_observed(gates, "beauty")
            if clarity_gates:
                envelope["clarity"] = {"gates": clarity_gates}

    # Benevolence (impact): policy-evaluated events, model-response receipts, or locked skills.
    impact_signals: dict[str, Any] = {}
    events, corrupt = read_agent_events(root)
    if events is not None and corrupt == 0 and events:
        policy_eval_count = sum(
            1
            for ev in events
            if isinstance(ev.get("policy"), dict)
            and ev["policy"].get("decision") in {"ALLOW", "DENY", "ASK"}
        )
        model_resp_count = sum(1 for ev in events if ev.get("kind") == "model_response")
        if policy_eval_count or model_resp_count:
            impact_signals["policy_evaluated_events"] = policy_eval_count
            impact_signals["model_response_receipts"] = model_resp_count
    skills_lock = root / ".hyodo" / "skills" / "lock.json"
    if skills_lock.is_file():
        try:
            lock_data = json.loads(skills_lock.read_text(encoding="utf-8"))
            if isinstance(lock_data, dict) and isinstance(lock_data.get("skills"), list):
                impact_signals["locked_skills"] = len(lock_data["skills"])
        except (OSError, json.JSONDecodeError):
            pass
    if impact_signals:
        envelope["impact"] = impact_signals

    # Hyo (consent): host promise observation or explicit gate-trust receipt.
    consent_signals: dict[str, Any] = {}
    promise_obs = load_host_promise_observation(root)
    if isinstance(promise_obs, dict) and promise_obs.get("state") == "OBSERVED":
        consent_signals["host_promise"] = {
            "state": "OBSERVED",
            "resolution": promise_obs.get("resolution", "UNOBSERVED"),
        }
    gates_trust = root / ".hyodo" / "gates-trust.json"
    if gates_trust.is_file():
        try:
            trust_data = json.loads(gates_trust.read_text(encoding="utf-8"))
            if isinstance(trust_data, dict) and isinstance(trust_data.get("digest"), str):
                consent_signals["gates_trust_digest"] = trust_data["digest"]
        except (OSError, json.JSONDecodeError):
            pass
    if consent_signals:
        envelope["consent"] = consent_signals

    # Eternity (continuity): intact agent-event ledger with zero corrupt lines.
    if events is not None and corrupt == 0 and events:
        import hashlib

        ledger_canonical = "\n".join(
            json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            for ev in events
        )
        ledger_digest = "sha256:" + hashlib.sha256(ledger_canonical.encode("utf-8")).hexdigest()
        envelope["continuity"] = {
            "event_count": len(events),
            "corrupt_lines": 0,
            "ledger_digest": ledger_digest,
        }

    return envelope


def measure_workspace_six_lenses(root: Path) -> dict[str, Any]:
    """Collect deterministic workspace evidence from *root* and project all six lenses."""
    return measure_six_lenses(collect_workspace_six_lens_envelope(root))
