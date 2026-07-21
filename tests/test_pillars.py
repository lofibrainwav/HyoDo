"""Unit tests for the In, Hyo, and Yeong evidence collectors."""

from __future__ import annotations

import json
from pathlib import Path

from hyodo.dashboard import render_dashboard_html
from hyodo.pillars import (
    HISTORY_RELATIVE_PATH,
    append_history_receipt,
    collect_hyo_evidence,
    collect_in_evidence,
    collect_yeong_evidence,
)

SAMPLE_MODULE = '''
"""Module docstring."""

import typer
import urllib.request


def documented_public():
    """Has a docstring."""
    return typer.Option(False, "--fix", help="Apply fixes")


def undocumented_public():
    return typer.Option(None, "--plain")


def _private_helper():
    raise ValueError
    raise ValueError("with message")


class PublicThing:
    """Documented class."""

    HOST = "0.0.0.0"
'''


def _make_checkout(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    package = tmp_path / "hyodo"
    package.mkdir()
    (package / "sample.py").write_text(SAMPLE_MODULE, encoding="utf-8")
    return tmp_path


def test_in_collector_measures_docstrings_help_and_messageless_raises(tmp_path):
    root = _make_checkout(tmp_path)
    pillar = collect_in_evidence(root)
    metrics = pillar["metrics"]
    # documented_public + PublicThing documented; undocumented_public is not.
    assert metrics["public_docstring_coverage"] == {"documented": 2, "public": 3}
    assert metrics["cli_parameters_with_help"] == {"with_help": 1, "total": 2}
    # `raise ValueError` (no message) counts; `raise ValueError("with message")` does not.
    assert metrics["messageless_raises"] == 1
    assert pillar["sources"]


def test_in_collector_ignores_normal_typer_exit(tmp_path):
    root = _make_checkout(tmp_path)
    (root / "hyodo" / "cli.py").write_text(
        'import typer\n\ndef complete():\n    """Finish normally."""\n    raise typer.Exit()\n',
        encoding="utf-8",
    )

    metrics = collect_in_evidence(root)["metrics"]
    assert metrics["messageless_raises"] == 1  # Only sample.py's ValueError remains.


def test_current_public_definitions_are_all_documented():
    root = Path(__file__).resolve().parent.parent
    coverage = collect_in_evidence(root)["metrics"]["public_docstring_coverage"]
    assert coverage["documented"] == coverage["public"]


def test_hyo_collector_measures_consent_and_network_posture(tmp_path):
    root = _make_checkout(tmp_path)
    pillar = collect_hyo_evidence(root)
    metrics = pillar["metrics"]
    assert metrics["outbound_network_import_sites"] == 1  # urllib.request
    assert metrics["non_loopback_bind_literals"] == 1  # "0.0.0.0" constant
    assert metrics["mutating_flags"] == {"flags": ["--fix"], "defaulting_on": []}


def test_hyo_collector_flags_mutating_option_defaulting_on(tmp_path):
    root = _make_checkout(tmp_path)
    (root / "hyodo" / "bad.py").write_text(
        'import typer\n\nOPT = typer.Option(True, "--fix")\n', encoding="utf-8"
    )
    metrics = collect_hyo_evidence(root)["metrics"]
    assert metrics["mutating_flags"]["defaulting_on"] == ["--fix"]


def test_yeong_collector_reports_not_connected_without_ledger(tmp_path):
    root = _make_checkout(tmp_path)
    pillar = collect_yeong_evidence(root)
    assert pillar == {"sources": [], "metrics": {}}


def test_yeong_ledger_round_trip_streak_and_corruption(tmp_path):
    root = _make_checkout(tmp_path)
    green = {
        "measured_at": "2026-07-20T00:00:00+00:00",
        "gates": {"tests": {"status": "PASS"}, "lint_format": {"status": "PASS"}},
    }
    red = {
        "measured_at": "2026-07-20T01:00:00+00:00",
        "gates": {"tests": {"status": "FAIL"}, "lint_format": {"status": "PASS"}},
    }
    assert append_history_receipt(root, green)
    assert append_history_receipt(root, red)
    assert append_history_receipt(root, green)
    assert append_history_receipt(root, green)
    ledger = root / HISTORY_RELATIVE_PATH
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write("not json\n")

    metrics = collect_yeong_evidence(root)["metrics"]
    assert metrics["recorded_runs"] == 4
    assert metrics["consecutive_all_pass_runs"] == 2  # broken by the FAIL run
    assert metrics["all_pass_runs"] == 3
    assert metrics["last_non_pass_at"] == "2026-07-20T01:00:00+00:00"
    assert metrics["first_recorded_at"] == "2026-07-20T00:00:00+00:00"
    assert metrics["corrupt_lines"] == 1

    lines = [json.loads(line) for line in ledger.read_text().splitlines()[:4]]
    assert lines[0]["schema_version"] == "hyodo.history-receipt/v1"
    assert lines[1]["gates"]["tests"] == "FAIL"


def test_receipt_serializes_gate_status_enums_as_values(tmp_path):
    from hyodo.cli.main import GateStatus

    root = _make_checkout(tmp_path)
    evidence = {
        "measured_at": "2026-07-20T00:00:00+00:00",
        "gates": {"tests": {"status": GateStatus.PASS, "message": "ok"}},
    }
    assert append_history_receipt(root, evidence)
    line = json.loads((root / HISTORY_RELATIVE_PATH).read_text().strip())
    assert line["gates"]["tests"] == "PASS"
    assert collect_yeong_evidence(root)["metrics"]["consecutive_all_pass_runs"] == 1


def test_scanner_does_not_count_its_own_sentinel():
    # pillars.py compares against the non-loopback literal; the checkout scan
    # must not report the measuring instrument itself.
    from pathlib import Path

    metrics = collect_hyo_evidence(Path(__file__).resolve().parent.parent)["metrics"]
    assert metrics["non_loopback_bind_literals"] == 0


def test_render_v2_pillars_without_composite_score(tmp_path):
    root = _make_checkout(tmp_path)
    append_history_receipt(
        root,
        {"measured_at": "2026-07-20T00:00:00+00:00", "gates": {"tests": {"status": "PASS"}}},
    )
    evidence = {
        "target": str(root),
        "measured_at": "2026-07-20T00:00:00+00:00",
        "gates": {
            "typecheck": {"status": "PASS", "message": "0 errors"},
            "lint_format": {"status": "PASS", "message": "passed"},
            "tests": {"status": "PASS", "message": "1 passed in 0.01s"},
            "sbom": {"status": "PASS", "message": "generated"},
        },
        "safety": {"risk_score": 5, "findings": []},
        "pillars": {
            "in": collect_in_evidence(root),
            "hyo": collect_hyo_evidence(root),
            "yeong": collect_yeong_evidence(root),
        },
    }
    html = render_dashboard_html(evidence)
    assert "Public docstring coverage" in html
    assert "67% (2/3)" in html
    assert "Mutating flags (--fix)" in html
    assert "Recorded measurement runs" in html
    assert "All-PASS run rate" in html
    assert "100% (1/1)" in html
    assert "Not measured" not in html
    assert "composite score" in html  # the header still promises no composite score
    assert "inventory artifact" in html  # SBOM stays labelled as inventory only


def test_render_v1_evidence_still_falls_back_to_not_measured():
    evidence = {
        "target": "/tmp/HyoDo",
        "measured_at": "2026-07-20T00:00:00+00:00",
        "gates": {
            "typecheck": {"status": "PASS", "message": "0 errors"},
            "lint_format": {"status": "PASS", "message": "passed"},
            "tests": {"status": "PASS", "message": "1 passed in 0.01s"},
            "sbom": {"status": "PASS", "message": "generated"},
        },
        "safety": {"risk_score": 5, "findings": []},
    }
    html = render_dashboard_html(evidence)
    assert html.count("Not measured") == 3
