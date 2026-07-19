"""Tests for the public-surface SBOM generator and the Eternity gate.

The scoping contract (only the public runtime `typer`/`rich` closure, never the
generator or dev tooling, never `afo_core`) is a pure function that is unit
tested here and also enforced by ``scripts/generate_sbom.py`` at generation time.
The full build->clean-venv->inventory pipeline is exercised by an opt-in
integration test (``HYODO_SBOM_INTEGRATION=1``), so the default suite stays fast
and offline.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from hyodo.cli.main import GateStatus, run_sbom_check

ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = ROOT / "scripts" / "generate_sbom.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_sbom", _SCRIPT)
    assert spec is not None, f"cannot load {_SCRIPT}"
    assert spec.loader is not None, f"no loader for {_SCRIPT}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generate_sbom = _load_generator()


def _sbom(*component_names: str, deps=None) -> dict:
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "metadata": {"component": {"name": "hyodo", "version": "3.1.8", "type": "library"}},
        "components": [{"name": n, "version": "1.0.0"} for n in component_names],
        "dependencies": deps or [],
    }


# --- assert_public_scope (pure contract) --------------------------------------


def test_assert_public_scope_accepts_runtime_only():
    generate_sbom.assert_public_scope(_sbom("typer", "rich", "click", "Pygments"))


def test_assert_public_scope_rejects_missing_runtime():
    with pytest.raises(ValueError, match="missing required"):
        generate_sbom.assert_public_scope(_sbom("rich", "click"))  # no typer


@pytest.mark.parametrize(
    "forbidden", ["pytest", "ruff", "pyright", "cyclonedx-bom", "hypothesis", "pip", "setuptools"]
)
def test_assert_public_scope_rejects_dev_or_bootstrap_component(forbidden):
    with pytest.raises(ValueError, match="dev/bootstrap"):
        generate_sbom.assert_public_scope(_sbom("typer", "rich", forbidden))


def test_assert_public_scope_rejects_afo_core():
    with pytest.raises(ValueError, match="afo_core"):
        generate_sbom.assert_public_scope(_sbom("typer", "rich", "afo_core"))


# --- normalize_for_comparison (reproducibility contract) ----------------------


def test_normalize_ignores_volatile_fields():
    a = _sbom("typer", "rich")
    a["serialNumber"] = "urn:uuid:aaaaaaaa-0000-0000-0000-000000000000"
    a["metadata"]["timestamp"] = "2026-01-01T00:00:00Z"
    b = _sbom("rich", "typer")  # different order, no volatile fields
    assert generate_sbom.normalize_for_comparison(a) == generate_sbom.normalize_for_comparison(b)


def test_normalize_detects_real_component_difference():
    a = _sbom("typer", "rich")
    b = _sbom("typer", "rich", "extra")
    assert generate_sbom.normalize_for_comparison(a) != generate_sbom.normalize_for_comparison(b)


# --- run_sbom_check (Eternity gate) -------------------------------------------
#
# These run the REAL subprocess path (a tiny stub generator with a fixed exit
# code) instead of mocking subprocess.run, so the exit-code -> gate-status
# contract is actually exercised offline.


def _root_with_stub(tmp_path: Path, exit_code: int) -> Path:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "generate_sbom.py").write_text(
        f"import sys\nsys.exit({exit_code})\n", encoding="utf-8"
    )
    return tmp_path


def test_run_sbom_check_pass_on_exit_0(tmp_path):
    assert run_sbom_check(_root_with_stub(tmp_path, 0), verbose=False).status is GateStatus.PASS


def test_run_sbom_check_fail_on_scope_violation_exit_2(tmp_path):
    assert run_sbom_check(_root_with_stub(tmp_path, 2), verbose=False).status is GateStatus.FAIL


def test_run_sbom_check_skip_on_environment_failure_exit_3(tmp_path):
    # Environment failure (e.g. offline) must SKIP, never hard-fail the gate.
    assert run_sbom_check(_root_with_stub(tmp_path, 3), verbose=False).status is GateStatus.SKIP


def test_run_sbom_check_fail_on_unexpected_exit_1(tmp_path):
    # An unexpected generator failure (exit 1: bug, corrupt output, unhandled
    # exception) must FAIL — never be masked as an environment SKIP. This is the
    # anti-ghost-gate honesty contract for sec-1.
    assert run_sbom_check(_root_with_stub(tmp_path, 1), verbose=False).status is GateStatus.FAIL


@pytest.mark.parametrize("exit_code", [1, 4, 42, 137])
def test_run_sbom_check_fail_on_any_unexpected_exit(tmp_path, exit_code):
    # Only 0/2/3 are defined; every other code is an unexpected failure -> FAIL.
    assert (
        run_sbom_check(_root_with_stub(tmp_path, exit_code), verbose=False).status
        is GateStatus.FAIL
    )


def test_run_sbom_check_skip_when_script_absent(tmp_path):
    assert run_sbom_check(tmp_path, verbose=False).status is GateStatus.SKIP


# --- main() exit-code contract (0/2/3) ----------------------------------------


def test_main_returns_2_on_scope_violation(monkeypatch, tmp_path):
    def _raise(output):
        raise generate_sbom.ScopeError("SBOM leaked dev/bootstrap components: ['pytest']")

    monkeypatch.setattr(generate_sbom, "generate", _raise)
    assert generate_sbom.main(["-o", str(tmp_path / "s.json")]) == 2


def test_main_returns_3_on_environment_failure(monkeypatch, tmp_path):
    def _raise(output):
        raise RuntimeError("wheel build produced no hyodo wheel")

    monkeypatch.setattr(generate_sbom, "generate", _raise)
    assert generate_sbom.main(["-o", str(tmp_path / "s.json")]) == 3


# --- end-to-end (opt-in: real build + clean venv + inventory) -----------------


@pytest.mark.skipif(
    not os.environ.get("HYODO_SBOM_INTEGRATION"),
    reason="set HYODO_SBOM_INTEGRATION=1 to run the real build/venv/inventory pipeline",
)
def test_generate_end_to_end_is_scoped_and_reproducible(tmp_path):
    out1 = tmp_path / "sbom1.json"
    out2 = tmp_path / "sbom2.json"
    sbom1 = generate_sbom.generate(output=out1)
    sbom2 = generate_sbom.generate(output=out2)

    names = {c["name"].lower() for c in sbom1["components"]}
    assert "typer" in names
    assert "rich" in names
    # no dev/generator tooling and no venv bootstrap seeds
    assert not (
        names & {"pytest", "ruff", "pyright", "cyclonedx-bom", "pip", "setuptools", "wheel"}
    )
    # scope self-check must have passed inside generate(); reproducible across runs
    assert generate_sbom.normalize_for_comparison(sbom1) == generate_sbom.normalize_for_comparison(
        sbom2
    )
