"""Tests for the Phase 1-E test-integrity scanner (`hyodo/test_integrity.py`).

Covers the spec's own test plan row for 1-E: a no-op test body is flagged
`no_assertion`; `assert 1 == 1` only is flagged `constant_assertion`; a real
computed assertion is not flagged; `@pytest.mark.skip` without `reason=` is
flagged, with `reason=` it is not; `# hyodo: allow-vacuous` suppresses
`no_target_reference`; and a no-tests project reports UNOBSERVED (all-zero),
never a failure.
"""

import dataclasses
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import GateResult, GateStatus, app, find_repo_root
from hyodo.test_integrity import TestIntegrityReport, VacuousTestFinding, scan_test_integrity

runner = CliRunner()


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_no_op_test_body_is_flagged_no_assertion(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "test_nothing.py",
        "import hyodo\n\n\ndef test_nothing():\n    hyodo.__version__\n",
    )
    report = scan_test_integrity(tmp_path)
    assert report.total_tests == 1
    assert report.vacuous_tests == 1
    assert any(f.category == "no_assertion" for f in report.findings)


def test_constant_assertion_only_is_flagged(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "test_const.py",
        "import hyodo\n\n\ndef test_const():\n    hyodo.__version__\n    assert 1 == 1\n",
    )
    report = scan_test_integrity(tmp_path)
    assert report.vacuous_tests == 1
    findings = [f for f in report.findings if f.category == "constant_assertion"]
    assert len(findings) == 1
    assert findings[0].function == "test_const"


def test_real_computed_assertion_is_not_flagged(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "test_real.py",
        "import hyodo\n\n\ndef test_real():\n    result = hyodo.__version__ + ''\n"
        "    assert result == hyodo.__version__\n",
    )
    report = scan_test_integrity(tmp_path)
    assert report.vacuous_tests == 0
    assert not any(f.category in {"no_assertion", "constant_assertion"} for f in report.findings)


def test_same_module_helper_with_assert_is_not_flagged(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "test_helper_ok.py",
        "import hyodo\n\n\n"
        "def _check_version_shape(value):\n    assert value == hyodo.__version__\n\n\n"
        "def test_delegates_to_helper():\n    _check_version_shape(hyodo.__version__)\n",
    )
    report = scan_test_integrity(tmp_path)
    assert report.vacuous_tests == 0
    assert not any(f.function == "test_delegates_to_helper" for f in report.findings)


def test_attribute_call_with_colliding_name_is_still_flagged(tmp_path: Path) -> None:
    """``w.process()`` never reaches the free ``process`` helper, so no credit."""
    _write(
        tmp_path,
        "test_helper_collision.py",
        "class Widget:\n    def process(self, value):\n        return value * 2\n\n\n"
        "def process(value):\n    assert value > 0\n\n\n"
        "def test_calls_method_not_helper():\n    Widget().process(5)\n",
    )
    report = scan_test_integrity(tmp_path)
    assert any(f.function == "test_calls_method_not_helper" for f in report.findings)


def test_same_module_helper_without_assert_still_flagged(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "test_helper_bad.py",
        "import hyodo\n\n\n"
        "def _touch_version(value):\n    return value\n\n\n"
        "def test_delegates_to_no_op_helper():\n    _touch_version(hyodo.__version__)\n",
    )
    report = scan_test_integrity(tmp_path)
    findings = [f for f in report.findings if f.function == "test_delegates_to_no_op_helper"]
    assert any(f.category == "no_assertion" for f in findings)


def test_helper_in_another_module_is_not_resolved(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "_helpers.py",
        "def check_version_shape(value):\n    assert value\n",
    )
    _write(
        tmp_path,
        "test_helper_elsewhere.py",
        "import hyodo\nfrom _helpers import check_version_shape\n\n\n"
        "def test_uses_other_module_helper():\n    check_version_shape(hyodo.__version__)\n",
    )
    report = scan_test_integrity(tmp_path)
    findings = [f for f in report.findings if f.function == "test_uses_other_module_helper"]
    assert any(f.category == "no_assertion" for f in findings)


def test_unexplained_skip_end_to_end(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "test_skip.py",
        "import pytest\nimport hyodo\n\n\n"
        "@pytest.mark.skip\n"
        "def test_no_reason():\n    assert hyodo.__version__\n\n\n"
        '@pytest.mark.skip(reason="flaky on CI")\n'
        "def test_with_reason():\n    assert hyodo.__version__\n",
    )
    report = scan_test_integrity(tmp_path)
    skip_findings = {f.function: f for f in report.findings if f.category == "unexplained_skip"}
    assert "test_no_reason" in skip_findings
    assert "test_with_reason" not in skip_findings


def test_allow_vacuous_suppresses_no_target_reference(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "test_fixture_only.py",
        "def test_flagged(fixture):\n    assert fixture == 1\n\n\n"
        "def test_suppressed(fixture):  # hyodo: allow-vacuous\n    assert fixture == 1\n",
    )
    report = scan_test_integrity(tmp_path)
    targets = {
        f.function: f.category for f in report.findings if f.category == "no_target_reference"
    }
    assert "test_flagged" in targets
    assert "test_suppressed" not in targets


def test_no_target_reference_cites_no_rule_id_when_not_overlapping(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "test_fixture.py",
        "def test_uses_fixture(fixture):\n    assert fixture.value == 1\n",
    )
    report = scan_test_integrity(tmp_path)
    findings = [f for f in report.findings if f.category == "no_target_reference"]
    assert len(findings) == 1
    # Real assertion present, so this function is not also flagged vacuous.
    assert report.vacuous_tests == 0


def test_anti_gaming_rule_ids_are_cited_in_details(tmp_path: Path) -> None:
    _write(tmp_path, "test_empty.py", 'def test_nothing():\n    """Docstring only."""\n    pass\n')
    report = scan_test_integrity(tmp_path)
    no_assertion = [f for f in report.findings if f.category == "no_assertion"]
    assert len(no_assertion) == 1
    assert "HYO-SAFE-010" in no_assertion[0].detail


def test_no_tests_project_is_unobserved_not_failure(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("nothing to see here", encoding="utf-8")
    report = scan_test_integrity(tmp_path)
    assert report == TestIntegrityReport(
        scanned_files=0, total_files=0, total_tests=0, vacuous_tests=0, findings=()
    )


def test_unreadable_file_counted_in_total_but_not_scanned(tmp_path: Path) -> None:
    _write(tmp_path, "test_broken.py", "def test_bad(:\n    pass\n")
    report = scan_test_integrity(tmp_path)
    assert report.total_files == 1
    assert report.scanned_files == 0
    assert report.total_tests == 0


def test_pytest_raises_context_manager_counts_as_observation(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "test_raises.py",
        "import pytest\n\n\ndef test_raises_case():\n"
        "    with pytest.raises(ValueError):\n        raise ValueError('boom')\n",
    )
    report = scan_test_integrity(tmp_path)
    assert not any(f.category == "no_assertion" for f in report.findings)


def test_test_class_methods_are_discovered(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "test_class.py",
        "class TestThing:\n    def test_method(self):\n        pass\n",
    )
    report = scan_test_integrity(tmp_path)
    assert report.total_tests == 1
    assert any(f.function == "test_method" for f in report.findings)


def test_dataclasses_are_frozen() -> None:
    finding = VacuousTestFinding(
        path="tests/test_x.py", line=1, function="test_x", category="no_assertion", detail="x"
    )
    with_report = TestIntegrityReport(
        scanned_files=1, total_files=1, total_tests=1, vacuous_tests=1, findings=(finding,)
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        with_report.total_tests = 2  # type: ignore[misc]


# --- CLI wiring: `hyodo check --strict-tests` ---------------------------------


def _hyodo_root() -> Path:
    root = find_repo_root(Path(__file__).resolve())
    assert root is not None, "test must run inside a HyoDo checkout"
    return root


def test_check_strict_tests_fails_truth_gate_when_pyright_passes_and_tests_vacuous() -> None:
    hyodo_root = _hyodo_root()
    ok = GateResult(GateStatus.PASS, "ok")
    skip = GateResult(GateStatus.SKIP, "skipped")
    vacuous_report = TestIntegrityReport(
        scanned_files=1,
        total_files=1,
        total_tests=2,
        vacuous_tests=1,
        findings=(
            VacuousTestFinding(
                path="tests/test_x.py",
                line=1,
                function="test_x",
                category="no_assertion",
                detail="asserts nothing",
            ),
        ),
    )

    with (
        patch("hyodo.cli.main.run_pyright_check", return_value=ok),
        patch("hyodo.cli.main.run_ruff_check", return_value=ok),
        patch("hyodo.cli.main.run_pytest_check", return_value=ok),
        patch("hyodo.cli.main.run_sbom_check", return_value=skip),
        patch("hyodo.cli.main.scan_test_integrity", return_value=vacuous_report),
    ):
        result = runner.invoke(app, ["check", str(hyodo_root), "--strict-tests"])

    assert result.exit_code == 1
    assert "test-integrity: 1/2 tests assert nothing" in result.output


def test_check_without_strict_tests_ignores_vacuous_tests_for_exit_code() -> None:
    hyodo_root = _hyodo_root()
    ok = GateResult(GateStatus.PASS, "ok")
    skip = GateResult(GateStatus.SKIP, "skipped")
    vacuous_report = TestIntegrityReport(
        scanned_files=1,
        total_files=1,
        total_tests=2,
        vacuous_tests=1,
        findings=(),
    )

    with (
        patch("hyodo.cli.main.run_pyright_check", return_value=ok),
        patch("hyodo.cli.main.run_ruff_check", return_value=ok),
        patch("hyodo.cli.main.run_pytest_check", return_value=ok),
        patch("hyodo.cli.main.run_sbom_check", return_value=skip),
        patch("hyodo.cli.main.scan_test_integrity", return_value=vacuous_report),
    ):
        result = runner.invoke(app, ["check", str(hyodo_root)])

    assert result.exit_code == 0
    assert "Test integrity: 1/2 tests assert nothing" in result.output


def test_check_json_includes_test_integrity_object() -> None:
    hyodo_root = _hyodo_root()
    ok = GateResult(GateStatus.PASS, "ok")
    skip = GateResult(GateStatus.SKIP, "skipped")
    report = TestIntegrityReport(
        scanned_files=1, total_files=1, total_tests=3, vacuous_tests=0, findings=()
    )

    with (
        patch("hyodo.cli.main.run_pyright_check", return_value=ok),
        patch("hyodo.cli.main.run_ruff_check", return_value=ok),
        patch("hyodo.cli.main.run_pytest_check", return_value=ok),
        patch("hyodo.cli.main.run_sbom_check", return_value=skip),
        patch("hyodo.cli.main.scan_test_integrity", return_value=report),
    ):
        result = runner.invoke(app, ["check", str(hyodo_root), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["test_integrity"]["total_tests"] == 3
    assert payload["test_integrity"]["vacuous_tests"] == 0


def test_check_reports_unobserved_when_no_tests_found() -> None:
    hyodo_root = _hyodo_root()
    ok = GateResult(GateStatus.PASS, "ok")
    skip = GateResult(GateStatus.SKIP, "skipped")
    empty_report = TestIntegrityReport(
        scanned_files=0, total_files=0, total_tests=0, vacuous_tests=0, findings=()
    )

    with (
        patch("hyodo.cli.main.run_pyright_check", return_value=ok),
        patch("hyodo.cli.main.run_ruff_check", return_value=ok),
        patch("hyodo.cli.main.run_pytest_check", return_value=ok),
        patch("hyodo.cli.main.run_sbom_check", return_value=skip),
        patch("hyodo.cli.main.scan_test_integrity", return_value=empty_report),
    ):
        result = runner.invoke(app, ["check", str(hyodo_root), "--strict-tests"])

    assert result.exit_code == 0
    assert "Test integrity: UNOBSERVED" in result.output
