"""The 4.21 Golden Contract: what `hyodo check` may and may not claim.

Two axes run side by side and this file pins both at once, because the whole
point of 4.21 is that they can disagree:

* the 4.20 *machine* contract -- process exit code and the JSON ``status`` /
  ``gates_ran`` / ``gates_total`` / ``failed`` keys -- which existing callers
  parse and which must not move;
* the 4.21 *honesty* axis -- ``coverage`` / ``complete`` / ``effective`` and
  the human verdict line -- which says what the run actually supports.

The case that motivated all of it: one gate passing beside one gate skipped
used to print ``HYODO PASS``. It must now print ``HYODO UNOBSERVED`` while the
exit code and legacy status stay exactly where 4.20 left them.
"""

from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.check_honesty import gate_coverage
from hyodo.cli.main import app
from hyodo.gates import (
    GATES_CONFIG_RELATIVE_PATH,
    GATES_TRUST_ENV_VAR,
    GATES_TRUST_STATE_NAME,
)
from hyodo.user_state import user_state_home, workspace_identity, workspace_state_path

runner = CliRunner()

# A command that certainly does not exist, so its gate is declared and then
# skipped -- the only honest way to manufacture partial coverage.
_ABSENT_BINARY = "hyodo-no-such-binary-4210"


def _flat(text: str) -> str:
    """Collapse whitespace so assertions survive Rich's terminal wrapping.

    A sentence the CLI prints as one thought may arrive split across lines at
    an 80-column width. Pinning the wrapped form would make the test a hostage
    of the terminal width rather than of the wording.
    """
    return " ".join(text.split())


def _write_gates(root: Path, body: str) -> None:
    config = root / GATES_CONFIG_RELATIVE_PATH
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text('schema = "hyodo.gates/v1"\n' + body, encoding="utf-8")


def _gate(name: str, command: str, pillar: str = "goodness") -> str:
    return f'\n[gates.{name}]\npillar = "{pillar}"\ncommand = "{command}"\n'


def _check_json(root: Path, *extra: str) -> tuple[int, dict]:
    result = runner.invoke(app, ["check", str(root), "--json", *extra])
    return result.exit_code, json.loads(result.output)


def _verdict_line(root: Path, *extra: str) -> tuple[int, str]:
    result = runner.invoke(app, ["check", str(root), "--quiet", *extra])
    return result.exit_code, result.output.strip().splitlines()[-1]


@pytest.fixture
def trusted(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pre-approve the command set so trust is not the variable under test."""
    monkeypatch.setenv(GATES_TRUST_ENV_VAR, "1")


# --------------------------------------------------------------------------
# full / partial / fail / no-exec
# --------------------------------------------------------------------------


def test_full_coverage_pass_is_unchanged(tmp_path: Path, trusted: None) -> None:
    _write_gates(tmp_path, _gate("ok", "true"))

    exit_code, payload = _check_json(tmp_path)

    assert exit_code == 0
    assert payload["status"] == "PASS"
    assert payload["gates_ran"] == 1
    assert payload["gates_total"] == 1
    assert payload["coverage"] == "FULL"
    assert payload["complete"] is True
    assert payload["effective"] == "PASS"
    assert payload["verdict"].startswith("HYODO PASS")


def test_one_pass_one_skip_is_not_a_pass(tmp_path: Path, trusted: None) -> None:
    _write_gates(tmp_path, _gate("ok", "true") + _gate("absent", _ABSENT_BINARY, "truth"))

    exit_code, payload = _check_json(tmp_path)

    # 4.20 machine contract: a skip is not a failure, so nothing here moves.
    assert exit_code == 0
    assert payload["status"] == "PASS"
    assert payload["gates_ran"] == 1
    assert payload["gates_total"] == 2
    assert payload["failed"] == []
    # 4.21 honesty axis.
    assert payload["coverage"] == "PARTIAL"
    assert payload["complete"] is False
    assert payload["effective"] == "UNOBSERVED"
    assert payload["verdict"].startswith("HYODO UNOBSERVED")
    assert not payload["verdict"].startswith("HYODO PASS")


def test_partial_human_verdict_never_opens_with_pass(tmp_path: Path, trusted: None) -> None:
    _write_gates(tmp_path, _gate("ok", "true") + _gate("absent", _ABSENT_BINARY, "truth"))

    exit_code, line = _verdict_line(tmp_path)

    assert exit_code == 0
    assert line.startswith("HYODO UNOBSERVED")
    assert "1/2" in line
    # Says what is missing, not only the ratio.
    assert "not executed" in line


def test_observed_failure_stays_a_failure(tmp_path: Path, trusted: None) -> None:
    _write_gates(tmp_path, _gate("bad", "false"))

    exit_code, payload = _check_json(tmp_path)

    assert exit_code == 1
    assert payload["status"] == "FAIL"
    assert payload["effective"] == "FAIL"
    assert payload["failed"] == ["bad"]


def test_failure_with_partial_coverage_is_still_fail(tmp_path: Path, trusted: None) -> None:
    """Incomplete coverage must never soften an observed failure."""
    _write_gates(tmp_path, _gate("bad", "false") + _gate("absent", _ABSENT_BINARY, "truth"))

    exit_code, payload = _check_json(tmp_path)

    assert exit_code == 1
    assert payload["status"] == "FAIL"
    assert payload["coverage"] == "PARTIAL"
    assert payload["effective"] == "FAIL"


def test_no_gate_executed_exits_2(tmp_path: Path, trusted: None) -> None:
    _write_gates(tmp_path, _gate("absent", _ABSENT_BINARY))

    exit_code, payload = _check_json(tmp_path)

    assert exit_code == 2
    assert payload["status"] == "UNOBSERVED"
    assert payload["coverage"] == "NONE"
    assert payload["complete"] is False
    assert payload["effective"] == "UNOBSERVED"


# --------------------------------------------------------------------------
# definition drift (the approved command set changed)
# --------------------------------------------------------------------------


def test_changed_command_set_is_refused_without_naming_the_bypass(tmp_path: Path) -> None:
    _write_gates(tmp_path, _gate("ok", "true"))
    trust = workspace_state_path(tmp_path, GATES_TRUST_STATE_NAME)
    trust.parent.mkdir(parents=True, exist_ok=True)
    trust.write_text(
        json.dumps(
            {
                "schema": "hyodo.gates-trust/v2",
                "workspace_id": workspace_identity(tmp_path),
                "approved": {"deadbeef": {"via": "prompt"}},
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["check", str(tmp_path)])

    assert result.exit_code == 2
    # Refused, not silently run.
    assert "not approved" in _flat(result.output)
    # The commands that would have run are shown...
    assert "true" in _flat(result.output)
    # ...and the previously approved argv is not invented, only its absence.
    assert "UNOBSERVED" in _flat(result.output)
    # The escape hatch is never handed to whoever is being blocked.
    assert GATES_TRUST_ENV_VAR not in _flat(result.output)


def test_first_ever_run_says_none_not_changed(tmp_path: Path) -> None:
    _write_gates(tmp_path, _gate("ok", "true"))

    result = runner.invoke(app, ["check", str(tmp_path)])

    assert result.exit_code == 2
    assert "no command set has been approved" in _flat(result.output)
    assert GATES_TRUST_ENV_VAR not in _flat(result.output)


def test_refused_command_set_is_effective_unobserved(tmp_path: Path) -> None:
    _write_gates(tmp_path, _gate("ok", "true"))

    exit_code, payload = _check_json(tmp_path)

    assert exit_code == 2
    assert payload["effective"] == "UNOBSERVED"
    assert payload["complete"] is False
    assert payload["trust"]["via"] == "none"
    assert payload["trust"]["previous_command_set"] == "NONE"


# --------------------------------------------------------------------------
# TRUST_ALL compatibility and observability
# --------------------------------------------------------------------------


def test_trust_all_still_pre_approves_and_is_observable(tmp_path: Path, trusted: None) -> None:
    _write_gates(tmp_path, _gate("ok", "true"))

    exit_code, payload = _check_json(tmp_path)

    assert exit_code == 0
    assert payload["status"] == "PASS"
    assert payload["trust"]["via"] == f"env:{GATES_TRUST_ENV_VAR}"
    assert payload["trust"]["persistence"] == "OBSERVED"


def test_second_run_reports_previously_approved(tmp_path: Path, trusted: None) -> None:
    _write_gates(tmp_path, _gate("ok", "true"))
    assert _check_json(tmp_path)[0] == 0

    exit_code, payload = _check_json(tmp_path)

    assert exit_code == 0
    assert payload["trust"]["via"] == "previously-approved"


# --------------------------------------------------------------------------
# trust receipt persistence failure
# --------------------------------------------------------------------------


def test_unpersistable_trust_receipt_does_not_rewrite_gate_results(
    tmp_path: Path, trusted: None
) -> None:
    """A receipt that cannot be stored is surfaced, never charged to a gate."""
    _write_gates(tmp_path, _gate("ok", "true"))
    state_home = user_state_home()
    state_home.mkdir(parents=True, exist_ok=True)
    state_home.chmod(stat.S_IRUSR | stat.S_IXUSR)  # readable, not writable
    try:
        exit_code, payload = _check_json(tmp_path)
    finally:
        state_home.chmod(stat.S_IRWXU)

    # The gate ran and passed; only the receipt is missing.
    assert exit_code == 0
    assert payload["status"] == "PASS"
    assert payload["gates_ran"] == 1
    assert payload["effective"] == "PASS"
    assert payload["trust"]["via"] == f"env:{GATES_TRUST_ENV_VAR}"
    assert payload["trust"]["persistence"] == "UNOBSERVED"


# --------------------------------------------------------------------------
# first-run honesty
# --------------------------------------------------------------------------


def test_zero_detection_does_not_create_a_live_gates_toml(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")

    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0
    assert not (tmp_path / GATES_CONFIG_RELATIVE_PATH).exists()
    assert (tmp_path / ".hyodo" / "gates.toml.example").is_file()


def test_pyproject_presence_is_not_reported_as_a_detected_tool(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")

    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0
    assert "No supported tool was detected" in _flat(result.output)
    assert "pyproject.toml" in _flat(result.output)
    assert "not a detected tool" in _flat(result.output)


def test_sampled_fallback_survives_zero_gate_init(tmp_path: Path) -> None:
    """After a zero-detection init, `check` must still measure something."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")
    (tmp_path / "sample.sh").write_text("echo ok\n", encoding="utf-8")
    assert runner.invoke(app, ["init", str(tmp_path)]).exit_code == 0

    exit_code, payload = _check_json(tmp_path)

    assert exit_code == 0
    assert payload["sampled"] is True
    assert payload["gates_ran"] >= 1


def test_product_identity_wording_is_aligned() -> None:
    sentence = "Local evidence verification for AI-assisted work."
    assert sentence in _flat(runner.invoke(app, ["--help"]).output)
    assert sentence in _flat(runner.invoke(app, ["version"]).output)
    assert sentence in _flat(runner.invoke(app, ["--version"]).output)


# --------------------------------------------------------------------------
# measurement provenance
# --------------------------------------------------------------------------


def _provenance_with(relation: str, target: Path):
    from hyodo.provenance import PROVENANCE_SCHEMA_VERSION, MeasurementProvenance

    return MeasurementProvenance(
        schema_version=PROVENANCE_SCHEMA_VERSION,
        tool_name="hyodo",
        tool_version="4.21.0",
        package_root=target,
        python_executable="/usr/bin/python3",
        target_root=target,
        tool_commit="a" * 40,
        target_commit="b" * 40,
        tool_dirty=False,
        target_dirty=False,
        install_mode="source",
        relation=relation,  # type: ignore[arg-type]
    )


@pytest.mark.parametrize(
    ("relation", "validity"),
    [("SELF_OTHER_CHECKOUT", "MISMATCH"), ("SOURCE_UNOBSERVED", "UNOBSERVED")],
)
def test_invalid_provenance_downgrades_effective(
    tmp_path: Path, trusted: None, monkeypatch: pytest.MonkeyPatch, relation: str, validity: str
) -> None:
    _write_gates(tmp_path, _gate("ok", "true"))
    monkeypatch.setattr(
        "hyodo.cli.main.resolve_provenance",
        lambda root, **kw: _provenance_with(relation, tmp_path),
    )

    exit_code, payload = _check_json(tmp_path)

    # The gate really did pass and the exit code still says so.
    assert exit_code == 0
    assert payload["gates_ran"] == 1
    assert payload["coverage"] == "FULL"
    assert payload["provenance"]["validity"] == validity
    assert payload["effective"] == "UNOBSERVED"


def test_mismatch_keeps_its_4_20_status_semantics(
    tmp_path: Path, trusted: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """4.20 already downgraded `status` on MISMATCH; 4.21 must not undo that."""
    _write_gates(tmp_path, _gate("ok", "true"))
    monkeypatch.setattr(
        "hyodo.cli.main.resolve_provenance",
        lambda root, **kw: _provenance_with("SELF_OTHER_CHECKOUT", tmp_path),
    )

    exit_code, payload = _check_json(tmp_path)

    assert exit_code == 0
    assert payload["status"] == "UNOBSERVED"


def test_source_unobserved_keeps_its_4_20_status_semantics(
    tmp_path: Path, trusted: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """4.20 left `status` PASS on an unobservable source; only `effective` moves."""
    _write_gates(tmp_path, _gate("ok", "true"))
    monkeypatch.setattr(
        "hyodo.cli.main.resolve_provenance",
        lambda root, **kw: _provenance_with("SOURCE_UNOBSERVED", tmp_path),
    )

    exit_code, payload = _check_json(tmp_path)

    assert exit_code == 0
    assert payload["status"] == "PASS"
    assert payload["effective"] == "UNOBSERVED"


# --------------------------------------------------------------------------
# Coverage equality
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("observed", "expected", "want"),
    [
        (2, 2, "FULL"),
        (1, 2, "PARTIAL"),
        (0, 2, "NONE"),
        (0, 0, "NONE"),
        (3, 2, "NONE"),
    ],
)
def test_gate_coverage_is_full_only_on_equality(observed: int, expected: int, want: str) -> None:
    """FULL iff `expected > 0 and observed == expected`; a count above the
    declared set is not coverage, so it never reads as FULL."""
    assert gate_coverage(observed, expected) == want
