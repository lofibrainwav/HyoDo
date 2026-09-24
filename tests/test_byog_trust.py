"""Tests for hyodo.gates Bring-Your-Own-Gates trust-on-first-use (BYOG-Trust).

Covers the fix for the security report: `.hyodo/gates.toml` in a freshly
cloned, unreviewed repository executed immediately on `hyodo check`, with no
signal to the operator about what was about to run. The command set now needs
explicit approval before a single subprocess starts: a new or changed set is
refused (SKIP, never PASS) in a non-interactive environment unless
pre-approved, or shown to an operator for approval interactively.

All commands are the running interpreter (``sys.executable -c ...``)
writing a marker file to disk, or hermetic stdlib binaries (``true``/
``false``) -- so "did it actually run" is observed on disk, not merely
inferred from the reported status string.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import hyodo.gates as gates
from hyodo.gates import (
    GATES_TRUST_ENV_VAR,
    GATES_TRUST_RELATIVE_PATH,
    GATES_TRUST_STATE_NAME,
    SCHEMA_ID,
    GatesConfig,
    GateTrustDecision,
    UserGate,
    UserGateResult,
    compute_gate_set_fingerprint,
    load_gates_config,
    resolve_gate_trust,
    run_user_gates,
)
from hyodo.user_state import workspace_identity, workspace_state_path

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _marker_gate(name: str, marker: Path, *, payload: str = "ran") -> UserGate:
    """One gate whose command writes *marker* to disk -- proof of execution."""
    probe = f"import pathlib; pathlib.Path({str(marker)!r}).write_text({payload!r})"
    return UserGate(name=name, pillar="truth", command=(sys.executable, "-c", probe), timeout=10)


def _config(*user_gates: UserGate) -> GatesConfig:
    return GatesConfig(schema=SCHEMA_ID, gates=user_gates)


def _force_noninteractive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gates, "_is_noninteractive", lambda: True)


def _force_interactive(monkeypatch: pytest.MonkeyPatch, answer: str) -> None:
    monkeypatch.setattr(gates, "_is_noninteractive", lambda: False)
    monkeypatch.setattr("builtins.input", lambda prompt="": answer)


def _approve_first_use(
    config: GatesConfig, root: Path, monkeypatch: pytest.MonkeyPatch
) -> list[UserGateResult]:
    _force_interactive(monkeypatch, "y")
    results = run_user_gates(config, root)
    assert all(result.status == "PASS" for result in results)
    return results


def _write_gates_toml(root: Path, body: str) -> Path:
    hyodo_dir = root / ".hyodo"
    hyodo_dir.mkdir(parents=True, exist_ok=True)
    path = hyodo_dir / "gates.toml"
    path.write_text(body, encoding="utf-8")
    return path


def _trust_store(root: Path) -> dict:
    return json.loads(
        workspace_state_path(root, GATES_TRUST_STATE_NAME).read_text(encoding="utf-8")
    )


def _write_user_trust(root: Path, text: str) -> None:
    path = workspace_state_path(root, GATES_TRUST_STATE_NAME)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# explicit approval: first sighting is not silently executable
# ---------------------------------------------------------------------------


def test_first_use_requires_interactive_approval_and_records_trust(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    marker = tmp_path / "marker.txt"
    config = _config(_marker_gate("write", marker))
    _force_interactive(monkeypatch, "y")

    results = run_user_gates(config, tmp_path)

    assert results[0].status == "PASS"
    assert marker.exists()  # actually ran -- not just reported PASS

    store = _trust_store(tmp_path)
    assert store["schema"] == "hyodo.gates-trust/v2"
    assert store["workspace_id"] == workspace_identity(tmp_path)
    fingerprint = compute_gate_set_fingerprint(config)
    assert fingerprint in store["approved"]
    assert store["approved"][fingerprint]["via"] == "prompt"


def test_resolve_gate_trust_first_use_is_not_approved_without_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(UserGate(name="ok", pillar="truth", command=("true",), timeout=5))
    _force_noninteractive(monkeypatch)

    decision = resolve_gate_trust(config, tmp_path)

    assert isinstance(decision, GateTrustDecision)
    assert decision.approved is False
    # 4.21: the refusal must not hand the reader the variable that skips it --
    # a bypass printed beside a security decision is a bypass that gets used.
    assert GATES_TRUST_ENV_VAR not in decision.reason
    # It still says what is wrong and how to approve legitimately.
    assert "not approved" in decision.reason
    assert "no command set has been approved" in decision.reason
    assert decision.via == "none"
    assert decision.previous == "NONE"


def test_first_use_noninteractive_without_env_var_skips_without_executing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fresh checkout must not execute arbitrary project commands silently."""
    marker = tmp_path / "marker.txt"
    config = _config(_marker_gate("write", marker))
    _force_noninteractive(monkeypatch)

    results = run_user_gates(config, tmp_path)

    assert results[0].status == "SKIP"
    assert not marker.exists()


# ---------------------------------------------------------------------------
# drift: a command set that changes after a baseline was already recorded
# ---------------------------------------------------------------------------


def test_drift_noninteractive_skips_without_executing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline_marker = tmp_path / "baseline.txt"
    drift_marker = tmp_path / "drift.txt"

    baseline = _config(_marker_gate("write", baseline_marker))
    baseline_results = _approve_first_use(baseline, tmp_path, monkeypatch)
    assert baseline_results[0].status == "PASS"
    assert baseline_marker.exists()

    # Same gate name, different command executed -- this is drift.
    drifted = _config(_marker_gate("write", drift_marker, payload="drifted"))
    _force_noninteractive(monkeypatch)

    results = run_user_gates(drifted, tmp_path)

    # (a) the unapproved (drifted) command never executed.
    assert not drift_marker.exists()
    # (b) that state is reported as SKIP, never PASS.
    assert results[0].status == "SKIP"
    assert results[0].status != "PASS"
    assert GATES_TRUST_ENV_VAR not in results[0].message
    # (c) the previously approved argv was never recorded, so it is reported
    # as UNOBSERVED rather than guessed at.
    assert "UNOBSERVED" in results[0].message


def test_drift_is_detected_via_resolve_gate_trust(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline = _config(UserGate(name="g", pillar="truth", command=("true",), timeout=5))
    run_user_gates(baseline, tmp_path)  # seeds trust for `true`

    drifted = _config(UserGate(name="g", pillar="truth", command=("false",), timeout=5))
    _force_noninteractive(monkeypatch)

    decision = resolve_gate_trust(drifted, tmp_path)

    assert decision.approved is False
    assert decision.fingerprint != compute_gate_set_fingerprint(baseline)


def test_gates_toml_command_change_invalidates_trust(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """(d) via the real .hyodo/gates.toml + load_gates_config path, not just
    constructed dataclasses -- proves the fix works on the production
    config-loading path `hyodo check` actually uses."""
    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.probe]
pillar = "truth"
command = "true"
""",
    )
    config = load_gates_config(tmp_path)
    assert config is not None
    baseline_results = _approve_first_use(config, tmp_path, monkeypatch)
    assert baseline_results[0].status == "PASS"

    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.probe]
pillar = "truth"
command = "false"
""",
    )
    changed = load_gates_config(tmp_path)
    assert changed is not None
    _force_noninteractive(monkeypatch)

    results = run_user_gates(changed, tmp_path)

    assert results[0].status == "SKIP"


# ---------------------------------------------------------------------------
# (c) approval / pre-approval executes normally
# ---------------------------------------------------------------------------


def test_drift_preapproved_via_env_var_executes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline_marker = tmp_path / "baseline.txt"
    drift_marker = tmp_path / "drift.txt"
    _approve_first_use(_config(_marker_gate("write", baseline_marker)), tmp_path, monkeypatch)

    drifted = _config(_marker_gate("write", drift_marker, payload="drifted"))
    monkeypatch.setenv(GATES_TRUST_ENV_VAR, "1")
    _force_noninteractive(monkeypatch)  # the escape hatch must work in CI

    results = run_user_gates(drifted, tmp_path)

    assert results[0].status == "PASS"
    assert drift_marker.exists()

    store = _trust_store(tmp_path)
    fingerprint = compute_gate_set_fingerprint(drifted)
    assert store["approved"][fingerprint]["via"] == f"env:{GATES_TRUST_ENV_VAR}"


def test_drift_approved_interactively_executes_and_persists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline_marker = tmp_path / "baseline.txt"
    drift_marker = tmp_path / "drift.txt"
    _approve_first_use(_config(_marker_gate("write", baseline_marker)), tmp_path, monkeypatch)

    drifted = _config(_marker_gate("write", drift_marker, payload="drifted"))
    _force_interactive(monkeypatch, "y")

    results = run_user_gates(drifted, tmp_path)

    assert results[0].status == "PASS"
    assert drift_marker.exists()

    store = _trust_store(tmp_path)
    fingerprint = compute_gate_set_fingerprint(drifted)
    assert store["approved"][fingerprint]["via"] == "prompt"


def test_drift_declined_interactively_skips_without_executing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline_marker = tmp_path / "baseline.txt"
    drift_marker = tmp_path / "drift.txt"
    _approve_first_use(_config(_marker_gate("write", baseline_marker)), tmp_path, monkeypatch)

    drifted = _config(_marker_gate("write", drift_marker, payload="drifted"))
    _force_interactive(monkeypatch, "n")

    results = run_user_gates(drifted, tmp_path)

    assert not drift_marker.exists()
    assert results[0].status == "SKIP"


def test_interactive_prompt_eof_declines_without_crashing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline_marker = tmp_path / "baseline.txt"
    drift_marker = tmp_path / "drift.txt"
    _approve_first_use(_config(_marker_gate("write", baseline_marker)), tmp_path, monkeypatch)

    drifted = _config(_marker_gate("write", drift_marker, payload="drifted"))
    monkeypatch.setattr(gates, "_is_noninteractive", lambda: False)

    def _raise_eof(prompt: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise_eof)

    results = run_user_gates(drifted, tmp_path)

    assert not drift_marker.exists()
    assert results[0].status == "SKIP"


def test_reverting_to_a_previously_approved_command_set_is_silent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both historical fingerprints stay trusted: reverting to a command set
    an operator already reviewed once does not force a repeat approval."""
    config_a = _config(UserGate(name="g", pillar="truth", command=("true",), timeout=5))
    config_b = _config(UserGate(name="g", pillar="truth", command=("false",), timeout=5))

    _approve_first_use(config_a, tmp_path, monkeypatch)  # explicitly approved baseline

    _force_interactive(monkeypatch, "y")
    results_b = run_user_gates(config_b, tmp_path)  # drift, approved once
    assert results_b[0].status == "FAIL"  # `false` executed honestly and failed

    _force_noninteractive(monkeypatch)
    results_a_again = run_user_gates(config_a, tmp_path)  # revert to A
    assert results_a_again[0].status == "PASS"


# ---------------------------------------------------------------------------
# fingerprint semantics
# ---------------------------------------------------------------------------


def test_fingerprint_ignores_name_and_pillar_and_timeout() -> None:
    a = _config(UserGate(name="a", pillar="truth", command=("true",), timeout=5))
    b = _config(
        UserGate(name="totally-different-name", pillar="beauty", command=("true",), timeout=999)
    )
    assert compute_gate_set_fingerprint(a) == compute_gate_set_fingerprint(b)


def test_fingerprint_changes_with_command() -> None:
    a = _config(UserGate(name="g", pillar="truth", command=("true",), timeout=5))
    b = _config(UserGate(name="g", pillar="truth", command=("false",), timeout=5))
    assert compute_gate_set_fingerprint(a) != compute_gate_set_fingerprint(b)


def test_fingerprint_changes_with_env_prefix() -> None:
    a = _config(UserGate(name="g", pillar="truth", command=("true",), timeout=5, env=()))
    b = _config(UserGate(name="g", pillar="truth", command=("true",), timeout=5, env=("X=1",)))
    assert compute_gate_set_fingerprint(a) != compute_gate_set_fingerprint(b)


def test_fingerprint_stable_regardless_of_gate_order() -> None:
    forward = _config(
        UserGate(name="a", pillar="truth", command=("true",), timeout=5),
        UserGate(name="b", pillar="goodness", command=("false",), timeout=5),
    )
    backward = _config(
        UserGate(name="b", pillar="goodness", command=("false",), timeout=5),
        UserGate(name="a", pillar="truth", command=("true",), timeout=5),
    )
    assert compute_gate_set_fingerprint(forward) == compute_gate_set_fingerprint(backward)


# ---------------------------------------------------------------------------
# CI env-var truthiness + malformed/unexpected trust store resilience
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_ci_env_var_truthy_values_force_noninteractive(
    value: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CI", value)
    assert gates._is_noninteractive() is True


@pytest.mark.parametrize("value", ["0", "false", "", "no"])
def test_ci_env_var_falsy_values_are_not_truthy(
    value: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CI", value)
    assert gates._env_truthy("CI") is False


def test_malformed_trust_store_requires_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_user_trust(tmp_path, "{not json")

    config = _config(UserGate(name="g", pillar="truth", command=("true",), timeout=5))
    _force_noninteractive(monkeypatch)

    results = run_user_gates(config, tmp_path)

    assert results[0].status == "SKIP"  # a corrupt receipt cannot silently approve execution


def test_trust_store_with_non_dict_approved_field_requires_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_user_trust(
        tmp_path,
        json.dumps(
            {
                "schema": "hyodo.gates-trust/v2",
                "workspace_id": workspace_identity(tmp_path),
                "approved": "not-a-dict",
            }
        ),
    )

    config = _config(UserGate(name="g", pillar="truth", command=("true",), timeout=5))
    _force_noninteractive(monkeypatch)

    results = run_user_gates(config, tmp_path)

    assert results[0].status == "SKIP"


# ---------------------------------------------------------------------------
# hostile checkout: authority state shipped inside the tree is never honored
# ---------------------------------------------------------------------------


def test_preseeded_checkout_receipt_never_approves_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A clone that ships a receipt for its own gates must not run them."""
    marker = tmp_path / "pwned.txt"
    config = _config(_marker_gate("pwn", marker))
    receipt = tmp_path / GATES_TRUST_RELATIVE_PATH
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(
        json.dumps(
            {
                "schema": "hyodo.gates-trust/v1",
                "workspace_id": workspace_identity(tmp_path),
                "approved": {compute_gate_set_fingerprint(config): {"via": "prompt"}},
            }
        ),
        encoding="utf-8",
    )
    _force_noninteractive(monkeypatch)

    decision = resolve_gate_trust(config, tmp_path)
    results = run_user_gates(config, tmp_path)

    assert decision.approved is False
    assert "checkout-local .hyodo/gates-trust.json ignored" in decision.reason
    assert results[0].status == "SKIP"
    assert not marker.exists()


def test_approval_does_not_follow_a_copy_of_the_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Approval binds to the workspace path, so a copied tree starts unapproved."""
    original = tmp_path / "original"
    copy = tmp_path / "copy"
    original.mkdir()
    copy.mkdir()
    config = _config(UserGate(name="g", pillar="truth", command=("true",), timeout=5))
    _approve_first_use(config, original, monkeypatch)
    _force_noninteractive(monkeypatch)

    assert resolve_gate_trust(config, original).approved is True
    assert resolve_gate_trust(config, copy).approved is False


def test_user_state_receipt_for_another_workspace_is_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(UserGate(name="g", pillar="truth", command=("true",), timeout=5))
    _write_user_trust(
        tmp_path,
        json.dumps(
            {
                "schema": "hyodo.gates-trust/v2",
                "workspace_id": "sha256:" + "0" * 64,
                "approved": {compute_gate_set_fingerprint(config): {"via": "prompt"}},
            }
        ),
    )
    _force_noninteractive(monkeypatch)

    assert resolve_gate_trust(config, tmp_path).approved is False
