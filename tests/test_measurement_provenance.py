"""Measurement provenance, exercised against real directory layouts.

These fixtures reproduce an accident that actually happened on 2026-09-10: a
virtualenv inside one HyoDo checkout resolved its editable install to a second
checkout, so `hyodo check` measured this repository's files with the other
repository's gate code. Both reported `v4.19.0`, and nothing in any output
said otherwise.

Every fixture below builds real directories — and, where the classification
depends on commits, real git checkouts — rather than stubbing the filesystem,
because the thing under test *is* the relationship between real directories.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from hyodo.provenance import (
    _VALIDITY_BY_RELATION,
    MeasurementProvenance,
    _detect_install_mode,
    is_hyodo_checkout,
    path_digest,
    resolve_provenance,
)

requires_git = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")

SAME_VERSION = "4.19.0"


def _write_checkout(root: Path) -> Path:
    """A directory shaped like a HyoDo source checkout."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "hyodo").mkdir(exist_ok=True)
    (root / "hyodo" / "__init__.py").write_text('__version__ = "4.19.0"\n', encoding="utf-8")
    (root / "pyproject.toml").write_text('[project]\nname = "hyodo"\n', encoding="utf-8")
    return root


def _git_init(root: Path, message: str) -> str:
    """Commit the tree and return the commit id."""
    env_args = [
        "-c",
        "user.email=test@example.com",
        "-c",
        "user.name=test",
        "-c",
        "commit.gpgsign=false",
    ]
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(root), *env_args, "commit", "-q", "-m", message],
        check=True,
        capture_output=True,
    )
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


# --------------------------------------------------------------------------
# Fixture A — target and measurer are the same checkout
# --------------------------------------------------------------------------


@requires_git
def test_fixture_a_self_measurement_from_the_same_checkout_is_observed(tmp_path: Path) -> None:
    checkout = _write_checkout(tmp_path / "checkout-a")
    _git_init(checkout, "initial")

    provenance = resolve_provenance(checkout, package_root=checkout, tool_version=SAME_VERSION)

    assert provenance.relation == "SELF_SAME_CHECKOUT"
    assert provenance.validity == "OBSERVED"
    assert provenance.is_green_allowed is True


# --------------------------------------------------------------------------
# Fixture B — the accident: same version, different checkout
# --------------------------------------------------------------------------


@requires_git
def test_fixture_b_measuring_self_with_another_checkouts_code_is_a_mismatch(
    tmp_path: Path,
) -> None:
    target = _write_checkout(tmp_path / "HyoDo")
    measurer = _write_checkout(tmp_path / "HyoDo-release")
    (measurer / "hyodo" / "extra.py").write_text("# diverged\n", encoding="utf-8")
    target_commit = _git_init(target, "target")
    tool_commit = _git_init(measurer, "release")
    assert target_commit != tool_commit

    provenance = resolve_provenance(target, package_root=measurer, tool_version=SAME_VERSION)

    assert provenance.relation == "SELF_OTHER_CHECKOUT"
    assert provenance.validity == "MISMATCH"
    assert provenance.is_green_allowed is False
    assert "MEASUREMENT MISMATCH" in provenance.summary()


# --------------------------------------------------------------------------
# Fixture C — ordinary use: an installed HyoDo measuring somebody else
# --------------------------------------------------------------------------


def test_fixture_c_an_external_target_is_normal_and_never_penalised(tmp_path: Path) -> None:
    project = tmp_path / "some-django-app"
    (project / "app").mkdir(parents=True)
    (project / "manage.py").write_text("# not hyodo\n", encoding="utf-8")
    installed = tmp_path / "venv" / "lib" / "python3.14" / "site-packages" / "hyodo"
    installed.mkdir(parents=True)

    provenance = resolve_provenance(project, package_root=installed, tool_version=SAME_VERSION)

    assert provenance.relation == "EXTERNAL_TARGET"
    assert provenance.validity == "OBSERVED"
    assert provenance.is_green_allowed is True
    assert "MISMATCH" not in provenance.summary()


def test_a_directory_merely_containing_a_hyodo_folder_is_not_a_checkout(tmp_path: Path) -> None:
    """Guard for fixture C: an unrelated project must not be read as self-measurement."""
    project = tmp_path / "vendor-app"
    (project / "hyodo").mkdir(parents=True)
    (project / "hyodo" / "__init__.py").write_text("", encoding="utf-8")
    (project / "pyproject.toml").write_text('[project]\nname = "vendor-app"\n', encoding="utf-8")

    assert is_hyodo_checkout(project) is False


# --------------------------------------------------------------------------
# Fixture D — self-measurement whose source cannot be compared
# --------------------------------------------------------------------------


@requires_git
def test_fixture_d_unknown_measuring_source_is_unobserved_not_green(tmp_path: Path) -> None:
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    # a checkout-shaped directory that is not under version control: its
    # commit cannot be read, so equality cannot be claimed either way
    unversioned = _write_checkout(tmp_path / "unpacked-copy")

    provenance = resolve_provenance(target, package_root=unversioned, tool_version=SAME_VERSION)

    assert provenance.relation == "SOURCE_UNOBSERVED"
    assert provenance.validity == "UNOBSERVED"
    assert provenance.is_green_allowed is False


# --------------------------------------------------------------------------
# Fixture E — the load-bearing one: equal versions never prove equal sources
# --------------------------------------------------------------------------


@requires_git
def test_fixture_e_identical_versions_do_not_make_different_sources_equal(
    tmp_path: Path,
) -> None:
    target = _write_checkout(tmp_path / "HyoDo")
    measurer = _write_checkout(tmp_path / "elsewhere")
    (measurer / "hyodo" / "drift.py").write_text("# different code\n", encoding="utf-8")
    _git_init(target, "target")
    _git_init(measurer, "elsewhere")

    same_version = resolve_provenance(target, package_root=measurer, tool_version=SAME_VERSION)
    different_version = resolve_provenance(target, package_root=measurer, tool_version="9.9.9")

    # the two runs differ in nothing but the version string, and the verdict
    # is unmoved by it: version is not an input to the classification
    assert same_version.tool_version != different_version.tool_version
    assert same_version.relation == different_version.relation == "SELF_OTHER_CHECKOUT"
    assert same_version.validity == different_version.validity == "MISMATCH"


@requires_git
def test_matching_commits_with_a_dirty_tree_cannot_claim_equality(tmp_path: Path) -> None:
    """A commit id under-describes a tree with uncommitted edits.

    Two directories at the same commit are not running the same code if either
    has local modifications, so this degrades to UNOBSERVED rather than
    asserting a match it cannot support.
    """
    target = _write_checkout(tmp_path / "HyoDo")
    commit = _git_init(target, "target")
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(target), str(clone)], check=True, capture_output=True)
    (clone / "hyodo" / "__init__.py").write_text("# edited\n", encoding="utf-8")

    provenance = resolve_provenance(target, package_root=clone, tool_version=SAME_VERSION)

    assert provenance.tool_commit == commit
    assert provenance.target_commit == commit
    assert provenance.tool_dirty is True
    assert provenance.relation == "SOURCE_UNOBSERVED"
    assert provenance.validity == "UNOBSERVED"


# --------------------------------------------------------------------------
# The contract itself
# --------------------------------------------------------------------------


def test_every_relation_has_a_validity_and_only_observed_may_be_green() -> None:
    assert set(_VALIDITY_BY_RELATION) == {
        "EXTERNAL_TARGET",
        "SELF_SAME_CHECKOUT",
        "SELF_OTHER_CHECKOUT",
        "SOURCE_UNOBSERVED",
    }
    green = {r for r, v in _VALIDITY_BY_RELATION.items() if v == "OBSERVED"}
    assert green == {"EXTERNAL_TARGET", "SELF_SAME_CHECKOUT"}
    assert _VALIDITY_BY_RELATION["SELF_OTHER_CHECKOUT"] == "MISMATCH"
    assert _VALIDITY_BY_RELATION["SOURCE_UNOBSERVED"] == "UNOBSERVED"


def test_provenance_is_a_separate_axis_from_policy() -> None:
    """Provenance vocabulary must not borrow policy's words.

    ALLOW/DENY/ASK describe what an actor was permitted to do. Reusing them for
    "the measuring code was wrong" would collapse two unrelated questions into
    one field and make the answer unreadable.
    """
    assert set(_VALIDITY_BY_RELATION.values()) <= {"OBSERVED", "MISMATCH", "UNOBSERVED"}
    assert not {"ALLOW", "DENY", "ASK"} & set(_VALIDITY_BY_RELATION.values())


@requires_git
def test_portable_receipt_carries_no_absolute_paths(tmp_path: Path) -> None:
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")

    provenance = resolve_provenance(target, package_root=target, tool_version=SAME_VERSION)
    portable = provenance.to_portable_dict()
    local = provenance.to_local_dict()

    rendered = repr(portable)
    assert str(tmp_path) not in rendered
    assert str(Path.home()) not in rendered
    assert portable["target_root_digest"] == path_digest(target.resolve())
    # the local view is allowed to keep them; it never leaves the machine
    assert str(target.resolve()) == local["target_root"]


def test_path_digest_is_stable_and_distinguishing() -> None:
    assert path_digest("/a/b") == path_digest("/a/b")
    assert path_digest("/a/b") != path_digest("/a/c")
    assert path_digest(None) is None


@pytest.mark.parametrize(
    ("relative", "expected"),
    [
        (("venv", "lib", "python3.14", "site-packages", "hyodo"), "wheel"),
        (("usr", "lib", "python3", "dist-packages", "hyodo"), "wheel"),
        (("opt", "some", "place"), "unknown"),
    ],
)
def test_install_mode_from_the_package_location(
    tmp_path: Path, relative: tuple[str, ...], expected: str
) -> None:
    package_root = tmp_path.joinpath(*relative)
    package_root.mkdir(parents=True)
    assert _detect_install_mode(package_root) == expected


def test_install_mode_is_unknown_when_the_package_cannot_be_located() -> None:
    assert _detect_install_mode(None) == "unknown"


@requires_git
def test_provenance_is_frozen_so_a_receipt_cannot_be_edited_after_the_fact(
    tmp_path: Path,
) -> None:
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    provenance = resolve_provenance(target, package_root=target, tool_version=SAME_VERSION)

    assert isinstance(provenance, MeasurementProvenance)
    with pytest.raises((AttributeError, TypeError)):
        provenance.relation = "SELF_SAME_CHECKOUT"  # type: ignore[misc]


# --------------------------------------------------------------------------
# The wiring, not just the classifier: a mismatch must reach the verdict
# --------------------------------------------------------------------------


@requires_git
def test_check_refuses_to_report_green_when_the_measurer_is_another_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The false-green this whole module exists to stop.

    A classifier that returns MISMATCH into a void changes nothing. This runs
    the real `check` command over a passing target and asserts the verdict is
    downgraded, because the gates that just ran came from a different HyoDo
    than the one being measured.

    The provenance object is real — built from two real git checkouts by the
    same code path production uses. Only its delivery is redirected, because
    reproducing the original accident end to end would mean installing a
    second HyoDo into the test interpreter.
    """
    from typer.testing import CliRunner

    from hyodo.cli import main as cli

    target = _write_checkout(tmp_path / "HyoDo")
    measurer = _write_checkout(tmp_path / "HyoDo-release")
    (measurer / "hyodo" / "extra.py").write_text("# diverged\n", encoding="utf-8")
    _git_init(target, "target")
    _git_init(measurer, "release")

    mismatch = resolve_provenance(target, package_root=measurer, tool_version=SAME_VERSION)
    assert mismatch.validity == "MISMATCH"

    project = tmp_path / "clean-project"
    project.mkdir()
    (project / "ok.py").write_text("VALUE = 1\n", encoding="utf-8")

    monkeypatch.chdir(project)
    monkeypatch.setattr(cli, "resolve_provenance", lambda *_a, **_k: mismatch)

    result = CliRunner().invoke(cli.app, ["check", "--json"])

    payload = json.loads(result.stdout)
    assert payload["status"] != "PASS", (
        "a measurement made by another checkout's code was reported as green"
    )
    assert payload["provenance"]["relation"] == "SELF_OTHER_CHECKOUT"
    assert payload["provenance"]["validity"] == "MISMATCH"


@requires_git
def test_check_json_never_carries_an_absolute_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--json` gets pasted into issues, so it carries the portable form only."""
    from typer.testing import CliRunner

    from hyodo.cli import main as cli

    checkout = _write_checkout(tmp_path / "HyoDo")
    _git_init(checkout, "target")
    provenance = resolve_provenance(checkout, package_root=checkout, tool_version=SAME_VERSION)

    project = tmp_path / "plain-project"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setattr(cli, "resolve_provenance", lambda *_a, **_k: provenance)

    result = CliRunner().invoke(cli.app, ["check", "--json"])
    rendered = json.dumps(json.loads(result.stdout)["provenance"])

    assert "/Users/" not in rendered
    assert str(tmp_path) not in rendered
    assert rendered.count("target_root_digest") == 1


@requires_git
def test_provenance_is_never_silent_even_when_it_is_fine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ "Measured by what?" must always have an answer in the terminal."""
    from typer.testing import CliRunner

    from hyodo.cli import main as cli

    checkout = _write_checkout(tmp_path / "HyoDo")
    _git_init(checkout, "target")
    provenance = resolve_provenance(checkout, package_root=checkout, tool_version=SAME_VERSION)
    assert provenance.validity == "OBSERVED"

    project = tmp_path / "plain-project"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setattr(cli, "resolve_provenance", lambda *_a, **_k: provenance)

    result = CliRunner().invoke(cli.app, ["check"])

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert any(line.startswith("Measurement:") for line in lines)
    # the verdict stays the last line, because that is the line callers parse
    assert lines[-1].startswith("HYODO ")


# --------------------------------------------------------------------------
# The panel must answer "measured by what?" in every state
# --------------------------------------------------------------------------


def test_dashboard_readout_is_quiet_only_when_the_origin_is_observed() -> None:
    from hyodo.dashboard import _provenance_readout

    value, banner = _provenance_readout(
        {
            "provenance": {
                "relation": "SELF_SAME_CHECKOUT",
                "validity": "OBSERVED",
                "target_commit": "814f6fb7b0a52f7e935b2a253825d9516be9993e",
            }
        }
    )
    assert value == "SELF 814f6fb7"
    assert banner == ""

    value, banner = _provenance_readout(
        {"provenance": {"relation": "EXTERNAL_TARGET", "validity": "OBSERVED"}}
    )
    assert value == "EXTERNAL"
    assert banner == ""


def test_dashboard_shows_a_banner_when_the_measurement_is_invalid() -> None:
    from hyodo.dashboard import _provenance_readout

    value, banner = _provenance_readout(
        {
            "provenance": {
                "relation": "SELF_OTHER_CHECKOUT",
                "validity": "MISMATCH",
                "target_commit": "814f6fb7b0a52f7e935b2a253825d9516be9993e",
                "tool_commit": "e8e1193cd36831f2b722a1a0c70133c67c691cb0",
            }
        }
    )
    assert value == "MISMATCH"
    assert "MEASUREMENT MISMATCH" in banner
    assert "814f6fb7" in banner
    assert "e8e1193c" in banner
    # the served page stays portable: no filesystem path travels with it
    assert "/Users/" not in banner

    value, banner = _provenance_readout(
        {"provenance": {"relation": "SOURCE_UNOBSERVED", "validity": "UNOBSERVED"}}
    )
    assert value == "UNOBSERVED"
    assert "UNOBSERVED" in banner


def test_dashboard_treats_a_missing_provenance_record_as_unobserved() -> None:
    """An older snapshot with no provenance key must not read as fine."""
    from hyodo.dashboard import _provenance_readout

    value, banner = _provenance_readout({})
    assert value == "UNOBSERVED"
    assert banner != ""
