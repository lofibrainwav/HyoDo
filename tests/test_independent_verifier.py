import hashlib
import json
from pathlib import Path

from hyodo.independent_verifier import verify_exact_candidate
from hyodo.nameplate import build_nameplate

SHA = "a" * 40
WHEN = "2026-09-18T06:00:00+00:00"


def _plate(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "actor_id": "verifier-seat-01",
        "role": "verifier",
        "repo": "example/HyoDo",
        "exact_artifact_sha": SHA,
        "observed_at": WHEN,
        "runtime": {
            "host": "isolated",
            "provider": "observed",
            "model": "observed",
            "mode": "read-only",
            "session_id": "fresh-01",
            "github_actor": "UNOBSERVED",
            "actor_id": "verifier-seat-01",
        },
    }
    values.update(overrides)
    runtime = dict(values["runtime"])
    runtime["actor_id"] = values["actor_id"]
    return build_nameplate(
        actor_id=values["actor_id"],
        role=values["role"],
        repo=values["repo"],
        exact_artifact_sha=values["exact_artifact_sha"],
        observed_at=values["observed_at"],
        runtime=runtime,
    )


def _repo(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@example.invalid"], check=True
    )
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "test"], check=True)
    (tmp_path / "x").write_text("x", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "x"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-qm", "candidate"], check=True)


def test_exact_candidate_pass_is_read_only(tmp_path: Path) -> None:
    _repo(tmp_path)
    import subprocess

    actual = subprocess.check_output(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True
    ).strip()
    result = verify_exact_candidate(
        root=tmp_path,
        expected_artifact_sha=actual,
        verifier_nameplate=_plate(exact_artifact_sha=actual),
        evidence={"diff": "observed"},
    )
    assert result["verdict"] == "PASS"
    assert result["isolation_scope"] == "CONTRACT_LEVEL"
    assert "process_credential_isolation_unproven" in result["residuals"]
    assert not (tmp_path / ".hyodo").exists()


def test_sha_mismatch_blocks(tmp_path: Path) -> None:
    _repo(tmp_path)
    result = verify_exact_candidate(
        root=tmp_path,
        expected_artifact_sha=SHA,
        verifier_nameplate=_plate(),
        evidence={"diff": "observed"},
    )
    assert result["verdict"] == "BLOCK"
    assert "exact_artifact_sha_mismatch" in result["residuals"]


def test_missing_identity_is_unobserved(tmp_path: Path) -> None:
    _repo(tmp_path)
    plate = _plate(actor_id="UNOBSERVED", session_id="UNOBSERVED")
    result = verify_exact_candidate(
        root=tmp_path,
        expected_artifact_sha=SHA,
        verifier_nameplate=plate,
        evidence={"diff": "observed"},
    )
    assert result["verdict"] == "UNOBSERVED"


def test_builder_or_authority_input_is_forbidden(tmp_path: Path) -> None:
    _repo(tmp_path)
    result = verify_exact_candidate(
        root=tmp_path,
        expected_artifact_sha=SHA,
        verifier_nameplate=_plate(),
        evidence={"builder_verdict": "PASS"},
    )
    assert result["verdict"] == "BLOCK"
    assert "authority_or_builder_input_forbidden" in result["residuals"]


def test_nested_authority_input_is_forbidden(tmp_path: Path) -> None:
    _repo(tmp_path)
    result = verify_exact_candidate(
        root=tmp_path,
        expected_artifact_sha=SHA,
        verifier_nameplate=_plate(),
        evidence={"raw": [{"approval": "yes"}]},
    )
    assert result["verdict"] == "BLOCK"
    assert "authority_or_builder_input_forbidden" in result["residuals"]


def test_public_schema_pin_matches_schema_bytes() -> None:
    root = Path(__file__).parents[1]
    schema = root / "schemas" / "independent-verifier-v1.schema.json"
    pin = json.loads((root / "schemas" / "independent-verifier-v1.pin.json").read_text())
    assert pin["algorithm"] == "sha256"
    assert pin["digest"] == hashlib.sha256(schema.read_bytes()).hexdigest()
