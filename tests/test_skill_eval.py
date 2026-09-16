import json

from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.skill_eval import evaluate_skill_case

CASE = {
    "eval_id": "runtime-ownership-001",
    "skill_id": "runtime-ownership-audit",
    "skill_version": "0.1.0",
    "scenario": "label and executable disagree",
    "input_fixture": {"launchd_label": "com.kingdom.memory-embed-watch"},
    "expected_behavior": {"owner": "BB", "effect_readback": "observed"},
    "forbidden_behavior": ["owner_inferred_from_label"],
    "required_evidence": [
        "launchd_label",
        "executable_path",
        "runtime_owner_readback",
        "effect_readback",
        "authority_boundary",
    ],
    "oracle": "hyodo.skill-eval/v1",
    "critical_invariants": ["label_is_not_runtime_owner"],
}


OBSERVED = {
    "execution": {
        "observed": True,
        "eval_id": "runtime-ownership-001",
        "skill_id": "runtime-ownership-audit",
        "skill_version": "0.1.0",
        "run_id": "run-001",
        "execution_id": "execution-001",
        "attempt_id": "attempt-001",
        "owner": "BB",
        "inferred_owner_from_label": False,
    },
    "effect_readback": {"observed": True, "value": "served-by-bb"},
    "evidence": {
        "launchd_label": {
            "observed": True,
            "value": "com.kingdom.memory-embed-watch",
            "freshness": "fresh",
            "producer": "kingdom",
            "run_id": "run-001",
            "execution_id": "execution-001",
            "integrity": "verified",
        },
        "executable_path": {
            "observed": True,
            "value": "/Users/brnestrm/bb/scripts/memory-embed-trigger.sh",
            "freshness": "fresh",
            "producer": "kingdom",
            "run_id": "run-001",
            "execution_id": "execution-001",
            "integrity": "verified",
        },
        "runtime_owner_readback": {
            "observed": True,
            "value": "BB",
            "freshness": "fresh",
            "producer": "kingdom",
            "run_id": "run-001",
            "execution_id": "execution-001",
            "integrity": "verified",
        },
        "effect_readback": {
            "observed": True,
            "value": "served-by-bb",
            "freshness": "fresh",
            "producer": "kingdom",
            "run_id": "run-001",
            "execution_id": "execution-001",
            "integrity": "verified",
        },
        "authority_boundary": {
            "observed": True,
            "value": {"execution_authority": False},
            "freshness": "fresh",
            "producer": "kingdom",
            "run_id": "run-001",
            "execution_id": "execution-001",
            "integrity": "verified",
        },
    },
    "receipt": {"success": True},
    "authority": {"execution_authority": False, "hyo_do_granted_execution": False},
}

CLI_RUNNER = CliRunner()


def test_observed_owner_and_effect_pass() -> None:
    assert evaluate_skill_case(case=CASE, **OBSERVED)["status"] == "PASS"


def test_receipt_without_effect_is_hold() -> None:
    result = evaluate_skill_case(
        case=CASE,
        execution=OBSERVED["execution"],
        evidence={
            **OBSERVED["evidence"],
            "effect_readback": {"observed": False, "state": "PENDING"},
        },
        effect_readback={"observed": False},
        receipt=OBSERVED["receipt"],
        authority=OBSERVED["authority"],
    )
    assert result["status"] == "HOLD"
    assert result["false_green"] is True


def test_label_inference_fails() -> None:
    result = evaluate_skill_case(
        case=CASE,
        execution={**OBSERVED["execution"], "inferred_owner_from_label": True},
        evidence=OBSERVED["evidence"],
        effect_readback=OBSERVED["effect_readback"],
        receipt=OBSERVED["receipt"],
        authority=OBSERVED["authority"],
    )
    assert result["status"] == "FAIL"
    assert result["reason"] == "owner_inferred_from_label"


def test_missing_execution_is_unobserved() -> None:
    result = evaluate_skill_case(
        case=CASE,
        execution={"observed": False},
        evidence=OBSERVED["evidence"],
        effect_readback=OBSERVED["effect_readback"],
        receipt=OBSERVED["receipt"],
        authority=OBSERVED["authority"],
    )
    assert result["status"] == "UNOBSERVED"


def test_missing_execution_identity_is_unobserved() -> None:
    execution = {**OBSERVED["execution"]}
    execution.pop("run_id")
    result = evaluate_skill_case(
        case=CASE,
        execution=execution,
        evidence=OBSERVED["evidence"],
        effect_readback=OBSERVED["effect_readback"],
        receipt=OBSERVED["receipt"],
        authority=OBSERVED["authority"],
    )
    assert result["status"] == "UNOBSERVED"
    assert result["reason"] == "execution_run_id_unobserved"


def test_hyodo_authority_leakage_fails() -> None:
    result = evaluate_skill_case(
        case=CASE,
        execution=OBSERVED["execution"],
        evidence=OBSERVED["evidence"],
        effect_readback=OBSERVED["effect_readback"],
        receipt=OBSERVED["receipt"],
        authority={"hyo_do_granted_execution": True},
    )
    assert result["status"] == "FAIL"
    assert result["reason"] == "authority_leakage"


def test_required_evidence_is_enforced_before_semantic_pass() -> None:
    evidence = {**OBSERVED["evidence"]}
    evidence.pop("executable_path")
    result = evaluate_skill_case(case=CASE, **{**OBSERVED, "evidence": evidence})
    assert result["status"] == "UNOBSERVED"
    assert result["reason"] == "required_evidence_missing"


def test_observed_false_required_evidence_is_not_present() -> None:
    evidence = {**OBSERVED["evidence"], "runtime_owner_readback": {"observed": False}}
    result = evaluate_skill_case(case=CASE, **{**OBSERVED, "evidence": evidence})
    assert result["status"] == "UNOBSERVED"


def test_evidence_correlation_mismatch_is_not_accepted() -> None:
    evidence = {
        **OBSERVED["evidence"],
        "executable_path": {**OBSERVED["evidence"]["executable_path"], "execution_id": "other"},
    }
    result = evaluate_skill_case(case=CASE, **{**OBSERVED, "evidence": evidence})
    assert result["status"] == "UNOBSERVED"
    assert result["reason"] == "required_evidence_uncorrelated"


def test_authenticated_evidence_tampering_fails() -> None:
    evidence = {
        **OBSERVED["evidence"],
        "executable_path": {**OBSERVED["evidence"]["executable_path"], "integrity": "tampered"},
    }
    result = evaluate_skill_case(case=CASE, **{**OBSERVED, "evidence": evidence})
    assert result["status"] == "FAIL"
    assert result["reason"] == "evidence_tampering"


def test_skill_eval_cli_emits_machine_verdict(tmp_path) -> None:
    payload = {"case": CASE, **OBSERVED}
    input_path = tmp_path / "runtime-ownership.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    result = CLI_RUNNER.invoke(app, ["skill-eval", "--input", str(input_path), "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["status"] == "PASS"
