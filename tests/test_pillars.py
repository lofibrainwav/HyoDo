"""Unit tests for the In, Hyo, and Yeong evidence collectors."""

from __future__ import annotations

import json
from pathlib import Path

from hyodo.dashboard import render_dashboard_html
from hyodo.pillars import (
    HISTORY_RELATIVE_PATH,
    RECEIPT_SCHEMA_VERSION,
    append_history_receipt,
    collect_hyo_evidence,
    collect_in_evidence,
    collect_yeong_evidence,
    gate_set_fingerprint,
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


def test_src_layout_repo_is_autodetected_via_pyproject_name(tmp_path):
    root = tmp_path
    (root / "pyproject.toml").write_text('[project]\nname = "mypkg"\n', encoding="utf-8")
    package = root / "src" / "mypkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "core.py").write_text(
        '"""Core module."""\n\n'
        "import socket\n\n\n"
        "def documented():\n"
        '    """Docstring."""\n'
        "    return 1\n\n\n"
        "def undocumented():\n"
        "    return 2\n",
        encoding="utf-8",
    )
    in_pillar = collect_in_evidence(root)
    assert in_pillar["sources"] == ["ast scan of src/mypkg"]
    assert in_pillar["metrics"]["public_docstring_coverage"] == {"documented": 1, "public": 2}

    hyo_pillar = collect_hyo_evidence(root)
    assert hyo_pillar["sources"] == ["ast scan of src/mypkg"]
    assert hyo_pillar["metrics"]["outbound_network_import_sites"] == 1  # socket


def test_top_level_package_repo_is_autodetected_and_skips_venv_and_hidden(tmp_path):
    root = tmp_path
    (root / ".venv").mkdir()
    (root / ".venv" / "__init__.py").write_text("", encoding="utf-8")
    (root / ".hidden").mkdir()
    (root / ".hidden" / "__init__.py").write_text("", encoding="utf-8")
    package = root / "mypkg"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "core.py").write_text(
        '"""Core."""\n\n\ndef documented():\n    """Docstring."""\n    return 1\n',
        encoding="utf-8",
    )
    pillar = collect_in_evidence(root)
    assert pillar["sources"] == ["ast scan of mypkg"]
    assert pillar["metrics"]["public_docstring_coverage"] == {"documented": 1, "public": 1}


def test_repo_without_python_code_returns_empty_contract(tmp_path):
    root = tmp_path
    (root / "go.mod").write_text("module example.com/thing\n\ngo 1.22\n", encoding="utf-8")
    assert collect_in_evidence(root) == {"sources": [], "metrics": {}}
    assert collect_hyo_evidence(root) == {"sources": [], "metrics": {}}


def test_root_level_scripts_only_repo_is_scanned(tmp_path):
    root = tmp_path
    (root / "build.py").write_text(
        '"""Build script."""\n\n\ndef run():\n    """Run it."""\n    return 0\n',
        encoding="utf-8",
    )
    pillar = collect_in_evidence(root)
    assert pillar["sources"] == ["ast scan of root-level *.py files"]
    assert pillar["metrics"]["public_docstring_coverage"] == {"documented": 1, "public": 1}


def test_root_hyodo_checkout_takes_priority_over_pyproject_name(tmp_path):
    # _make_checkout writes tmp_path/hyodo/sample.py + a bare pyproject.toml;
    # overriding the name here proves root/hyodo (a) still wins over the
    # src/<name>-or-<name> lookup (b) — the original hardcoded path is a
    # regression lock, not just one option among several.
    root = _make_checkout(tmp_path)
    (root / "pyproject.toml").write_text('[project]\nname = "other"\n', encoding="utf-8")
    pillar = collect_in_evidence(root)
    assert pillar["sources"] == ["ast scan of the checkout's hyodo/ package"]
    assert pillar["metrics"]["public_docstring_coverage"] == {"documented": 2, "public": 3}


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
    assert lines[0]["schema_version"] == RECEIPT_SCHEMA_VERSION
    assert lines[1]["gates"]["tests"] == "FAIL"


def test_yeong_skip_gates_do_not_block_all_pass(tmp_path):
    """SKIP is unobserved, not failed: executed gates decide all-PASS (제6조 10항).

    A gate that never runs (e.g. sbom tool not installed) must not permanently
    pin the all-PASS rate to 0%, and must stay visible as a skipped-gate count.
    """
    root = _make_checkout(tmp_path)
    green_with_skip = {
        "measured_at": "2026-07-20T00:00:00+00:00",
        "gates": {"tests": {"status": "PASS"}, "sbom": {"status": "SKIP"}},
    }
    assert append_history_receipt(root, green_with_skip)
    metrics = collect_yeong_evidence(root)["metrics"]
    assert metrics["all_pass_runs"] == 1
    assert metrics["consecutive_all_pass_runs"] == 1
    assert metrics["last_non_pass_at"] == ""
    assert metrics["runs_with_skipped_gates"] == 1


def test_yeong_all_skip_run_is_not_all_pass(tmp_path):
    """A run with zero executed gates must not count as all-PASS (no false green)."""
    root = _make_checkout(tmp_path)
    all_skip = {
        "measured_at": "2026-07-20T00:00:00+00:00",
        "gates": {"sbom": {"status": "SKIP"}, "typecheck": {"status": "UNSUPPORTED"}},
    }
    assert append_history_receipt(root, all_skip)
    metrics = collect_yeong_evidence(root)["metrics"]
    assert metrics["all_pass_runs"] == 0
    assert metrics["consecutive_all_pass_runs"] == 0
    assert metrics["last_non_pass_at"] == "2026-07-20T00:00:00+00:00"


def test_yeong_fail_with_skip_is_not_all_pass(tmp_path):
    root = _make_checkout(tmp_path)
    red_with_skip = {
        "measured_at": "2026-07-20T02:00:00+00:00",
        "gates": {"tests": {"status": "FAIL"}, "sbom": {"status": "SKIP"}},
    }
    assert append_history_receipt(root, red_with_skip)
    metrics = collect_yeong_evidence(root)["metrics"]
    assert metrics["all_pass_runs"] == 0
    assert metrics["last_non_pass_at"] == "2026-07-20T02:00:00+00:00"


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


# --- Issue #87: gate_set_fingerprint (receipt coverage shrink must break streak) ---


def test_gate_set_fingerprint_is_deterministic_for_empty_and_named_sets():
    """Empty and non-empty name sets hash via json.dumps(sorted(...)) (12 hex)."""
    empty = gate_set_fingerprint([])
    assert empty == gate_set_fingerprint(())
    assert len(empty) == 12
    assert all(c in "0123456789abcdef" for c in empty)

    # Order of input names must not matter; payload is sorted then JSON-encoded.
    a = gate_set_fingerprint(["tests", "lint_format", "typecheck", "sbom"])
    b = gate_set_fingerprint(["sbom", "typecheck", "lint_format", "tests"])
    assert a == b
    assert a != empty
    assert a != gate_set_fingerprint(["tests"])


def test_gate_set_fingerprint_pipe_in_name_does_not_collide():
    """TOML quoted keys may contain '|'; encoding must not join-collide (#87 fix)."""
    left = gate_set_fingerprint(["a|b", "c"])
    right = gate_set_fingerprint(["a", "b|c"])
    assert left != right
    assert len(left) == 12
    assert len(right) == 12


def test_receipt_records_gate_set_fingerprint(tmp_path):
    root = _make_checkout(tmp_path)
    evidence = {
        "measured_at": "2026-07-21T00:00:00+00:00",
        "gates": {
            "typecheck": {"status": "PASS"},
            "lint_format": {"status": "PASS"},
            "tests": {"status": "PASS"},
            "sbom": {"status": "PASS"},
        },
    }
    assert append_history_receipt(root, evidence)
    line = json.loads((root / HISTORY_RELATIVE_PATH).read_text().strip())
    expected = gate_set_fingerprint(["typecheck", "lint_format", "tests", "sbom"])
    assert line["gate_set_fingerprint"] == expected
    assert line["schema_version"] == RECEIPT_SCHEMA_VERSION
    assert RECEIPT_SCHEMA_VERSION == "hyodo.history-receipt/v2"


def test_receipt_empty_gate_set_fingerprint_is_deterministic(tmp_path):
    root = _make_checkout(tmp_path)
    assert append_history_receipt(root, {"measured_at": "2026-07-21T00:00:00+00:00", "gates": {}})
    line = json.loads((root / HISTORY_RELATIVE_PATH).read_text().strip())
    assert line["gates"] == {}
    assert line["gate_set_fingerprint"] == gate_set_fingerprint([])


def test_yeong_same_gate_set_streak_accumulates(tmp_path):
    root = _make_checkout(tmp_path)
    four_gate_pass = {
        "measured_at": "2026-07-21T00:00:00+00:00",
        "gates": {
            "typecheck": {"status": "PASS"},
            "lint_format": {"status": "PASS"},
            "tests": {"status": "PASS"},
            "sbom": {"status": "PASS"},
        },
    }
    for hour in range(3):
        four_gate_pass = {
            **four_gate_pass,
            "measured_at": f"2026-07-21T0{hour}:00:00+00:00",
        }
        assert append_history_receipt(root, four_gate_pass)
    metrics = collect_yeong_evidence(root)["metrics"]
    assert metrics["consecutive_all_pass_runs"] == 3
    assert metrics["all_pass_runs"] == 3


def test_yeong_gate_set_change_resets_streak(tmp_path):
    """4-gate all-PASS then trivial 1-gate all-PASS must not extend the streak (#87)."""
    root = _make_checkout(tmp_path)
    four_gate = {
        "gates": {
            "typecheck": {"status": "PASS"},
            "lint_format": {"status": "PASS"},
            "tests": {"status": "PASS"},
            "sbom": {"status": "PASS"},
        },
    }
    trivial = {"gates": {"npm-test": {"status": "PASS"}}}
    assert append_history_receipt(root, {**four_gate, "measured_at": "2026-07-21T00:00:00+00:00"})
    assert append_history_receipt(root, {**four_gate, "measured_at": "2026-07-21T01:00:00+00:00"})
    assert append_history_receipt(root, {**trivial, "measured_at": "2026-07-21T02:00:00+00:00"})
    metrics = collect_yeong_evidence(root)["metrics"]
    # Only the latest fingerprint (trivial) participates; streak is 1, not 3.
    assert metrics["consecutive_all_pass_runs"] == 1
    assert metrics["all_pass_runs"] == 3  # all three runs were still all-PASS


def test_yeong_legacy_receipt_without_fingerprint_derives_compatibly(tmp_path):
    """Pre-v2 ledger lines lack gate_set_fingerprint; derive from gates keys."""
    root = _make_checkout(tmp_path)
    ledger = root / HISTORY_RELATIVE_PATH
    ledger.parent.mkdir(exist_ok=True)
    four_names = ["lint_format", "sbom", "tests", "typecheck"]
    legacy_fp = gate_set_fingerprint(four_names)
    # Append-only: write legacy-shaped lines by hand (no fingerprint field).
    legacy_lines = [
        {
            "schema_version": "hyodo.history-receipt/v1",
            "measured_at": "2026-07-20T00:00:00+00:00",
            "gates": {
                "typecheck": "PASS",
                "lint_format": "PASS",
                "tests": "PASS",
                "sbom": "PASS",
            },
        },
        {
            "schema_version": "hyodo.history-receipt/v1",
            "measured_at": "2026-07-20T01:00:00+00:00",
            "gates": {
                "typecheck": "PASS",
                "lint_format": "PASS",
                "tests": "PASS",
                "sbom": "PASS",
            },
        },
    ]
    with ledger.open("w", encoding="utf-8") as handle:
        for entry in legacy_lines:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")

    # Same gate set via modern append (stores fingerprint).
    assert append_history_receipt(
        root,
        {
            "measured_at": "2026-07-21T00:00:00+00:00",
            "gates": {
                "typecheck": {"status": "PASS"},
                "lint_format": {"status": "PASS"},
                "tests": {"status": "PASS"},
                "sbom": {"status": "PASS"},
            },
        },
    )
    modern = json.loads(ledger.read_text(encoding="utf-8").splitlines()[-1])
    assert modern["gate_set_fingerprint"] == legacy_fp

    metrics = collect_yeong_evidence(root)["metrics"]
    # Derived legacy fingerprints match the modern one → streak continues.
    assert metrics["consecutive_all_pass_runs"] == 3
    assert metrics["recorded_runs"] == 3

    # A coverage shrink after legacy lines still resets streak.
    assert append_history_receipt(
        root,
        {
            "measured_at": "2026-07-21T01:00:00+00:00",
            "gates": {"npm-test": {"status": "PASS"}},
        },
    )
    metrics_after = collect_yeong_evidence(root)["metrics"]
    assert metrics_after["consecutive_all_pass_runs"] == 1
    assert metrics_after["recorded_runs"] == 4
