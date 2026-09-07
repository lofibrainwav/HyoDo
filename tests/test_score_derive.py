"""Tests for `hyodo/score_derive.py` and `hyodo score --from-check`.

Covers the derivation module's own contract: the rule table is total (every
rule_id it can emit maps to a known pillar), an UNOBSERVED pillar is excluded
from the geometric-mean Eternity term and surfaced rather than defaulted, CLI
overrides are recorded in provenance, an empty project reports UNOBSERVED
rather than a number for pillars with no evidence, derivation is
deterministic for identical inputs, and the CLI's `--from-check --json` path
returns a `derivation` key end to end.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.score_derive import (
    PILLAR_NAMES,
    PILLAR_RULE_TABLE,
    apply_override,
    derive_pillars,
    geometric_mean_observed,
)

runner = CliRunner()


def test_rule_table_is_total() -> None:
    """Every rule_id in the table targets one of the five known pillars."""
    assert PILLAR_RULE_TABLE, "table must not be empty"
    for rule_id, spec in PILLAR_RULE_TABLE.items():
        assert spec.pillar in PILLAR_NAMES, f"{rule_id} targets unknown pillar {spec.pillar!r}"


def test_derive_pillars_provenance_rule_ids_are_all_in_table(tmp_path: Path) -> None:
    """Every rule_id a real derivation emits is present in PILLAR_RULE_TABLE."""
    derived = derive_pillars(
        tmp_path,
        check={"truth_gate": "PASS", "beauty_gate": "FAIL"},
        safe={"high": 1, "medium": 2, "scanned_files": 3, "total_scannable": 4},
        test_integrity={"total_tests": 10, "vacuous_tests": 2},
    )
    for result in derived.by_name().values():
        for row in result.provenance:
            if row.rule_id.startswith("override."):
                continue
            assert row.rule_id in PILLAR_RULE_TABLE


def test_unobserved_pillar_is_none_not_zero_or_hundred(tmp_path: Path) -> None:
    derived = derive_pillars(tmp_path, check=None, safe=None, test_integrity=None)
    # Hyo is always computed from the filesystem, but benevolence has no
    # signal source at all when check is None.
    assert derived.benevolence.value is None
    assert derived.benevolence.coverage == "UNOBSERVED"
    assert derived.benevolence.provenance == ()


def test_unobserved_pillar_excluded_from_eternity_and_surfaced(tmp_path: Path) -> None:
    derived = derive_pillars(
        tmp_path,
        check={"truth_gate": "PASS", "beauty_gate": "PASS"},
        safe={"high": 0, "medium": 0, "scanned_files": 5, "total_scannable": 5},
        test_integrity=None,  # truth still partially observed via check.truth_gate
    )
    by_name = derived.by_name()
    unobserved = [name for name, r in by_name.items() if r.value is None]
    observed_values = [r.value for r in by_name.values() if r.value is not None]

    assert "benevolence" in unobserved
    # The geometric mean helper only ever receives observed values; an
    # UNOBSERVED pillar's absence must not become an implicit 0 inside it.
    eternity = geometric_mean_observed(observed_values)
    assert eternity > 0
    # A pillar reported UNOBSERVED is never silently scored.
    assert by_name["benevolence"].value is None


def test_override_is_recorded_in_provenance(tmp_path: Path) -> None:
    derived = derive_pillars(tmp_path, check=None, safe=None, test_integrity=None)
    overridden = apply_override(derived.benevolence, 0.75)

    assert overridden.override is True
    assert overridden.value == 75.0
    assert overridden.coverage == "OBSERVED"
    assert len(overridden.provenance) == 1
    row = overridden.provenance[0]
    assert row.override is True
    assert row.rule_id == "override.benevolence"
    assert row.as_dict()["override"] is True


def test_empty_directory_gives_unobserved_not_a_number(tmp_path: Path) -> None:
    """An empty directory has no tests, no findings, and no check signals."""
    derived = derive_pillars(
        tmp_path,
        check=None,
        safe=None,
        test_integrity={"total_tests": 0, "vacuous_tests": 0},
    )
    # No test cases exist to measure -- the ratio rule must not fire (it
    # would otherwise read as a perfect 1.0 for "zero tests, zero vacuous").
    assert derived.truth.value is None
    assert derived.truth.coverage == "UNOBSERVED"
    assert derived.benevolence.value is None
    assert derived.benevolence.coverage == "UNOBSERVED"
    assert derived.goodness.value is None
    assert derived.goodness.coverage == "UNOBSERVED"


def test_derivation_is_deterministic(tmp_path: Path) -> None:
    (tmp_path / ".hyodo").mkdir()
    (tmp_path / ".hyodo" / "gates.toml").write_text("", encoding="utf-8")
    kwargs = {
        "check": {"truth_gate": "PASS", "beauty_gate": "PASS"},
        "safe": {"high": 2, "medium": 1, "scanned_files": 8, "total_scannable": 10},
        "test_integrity": {"total_tests": 20, "vacuous_tests": 3},
    }
    first = derive_pillars(tmp_path, **kwargs).as_dict()
    second = derive_pillars(tmp_path, **kwargs).as_dict()
    assert first == second


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)


def test_cli_from_check_json_returns_derivation_key(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "sample.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=tmp_path, check=True)

    result = runner.invoke(app, ["score", "--from-check", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert "derivation" in payload
    for pillar in PILLAR_NAMES:
        assert pillar in payload["derivation"]
    assert payload["note"] == "Review signal only — not automatic approval."


def test_cli_from_check_override_marks_provenance(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "sample.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=tmp_path, check=True)

    result = runner.invoke(
        app,
        [
            "score",
            "--from-check",
            "--root",
            str(tmp_path),
            "--benevolence",
            "0.9",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    benevolence = payload["derivation"]["benevolence"]
    assert benevolence["override"] is True
    assert benevolence["value"] == 90.0
    assert benevolence["provenance"][0]["override"] is True


def test_cli_from_check_rejects_invalid_root() -> None:
    result = runner.invoke(app, ["score", "--from-check", "--root", "/no/such/path"])
    assert result.exit_code == 2


def test_cli_from_check_json_observes_benevolence_via_dx_signals(tmp_path: Path) -> None:
    """A repo with a README start-hint + entry point yields OBSERVED Benevolence.

    Exercises the `hyodo check` -> `_collect_check_observation` ->
    `collect_dx_signals` wiring end to end: readme_present,
    start_hint_present and help_text_present should all fire with
    provenance, and the pillar should be OBSERVED with a full TOTAL score
    once every pillar is supplied.
    """
    _init_git_repo(tmp_path)
    (tmp_path / "sample.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "# Sample project\n\nThis README exists to document the sample project "
        "for the purposes of this test, and it is long enough to pass the "
        "non-empty README size threshold used by dx_signals.\n\n"
        "## Quick start\n\n```bash\nhyodo start\n```\n\n"
        "Run `sample --help` for usage.\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "sample"\n\n[project.scripts]\nsample = "sample.cli:app"\n',
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=tmp_path, check=True)

    result = runner.invoke(
        app,
        [
            "score",
            "--from-check",
            "--root",
            str(tmp_path),
            "--truth",
            "0.9",
            "--goodness",
            "0.9",
            "--hyo",
            "0.9",
            "--beauty",
            "0.9",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    benevolence = payload["derivation"]["benevolence"]
    assert benevolence["coverage"] == "OBSERVED"
    assert benevolence["value"] == 100.0
    provenance_rule_ids = {row["rule_id"] for row in benevolence["provenance"]}
    assert provenance_rule_ids == {
        "check.readme_present",
        "check.start_hint_present",
        "check.help_text_present",
    }
    assert payload["unobserved_pillars"] == []
    assert isinstance(payload["score"], float)
