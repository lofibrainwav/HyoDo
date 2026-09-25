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
import os
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


def _commit_all(root: Path, message: str) -> str:
    env_args = [
        "-c",
        "user.email=test@example.com",
        "-c",
        "user.name=test",
        "-c",
        "commit.gpgsign=false",
    ]
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(root), *env_args, "commit", "-q", "-m", message],
        check=True,
        capture_output=True,
    )
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _git_init(root: Path, message: str) -> str:
    """Commit the tree and return the commit id."""
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    return _commit_all(root, message)


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


@requires_git
def test_a_clean_tree_reports_dirty_false_not_unobserved(tmp_path: Path) -> None:
    """A clean checkout must report `dirty=False`, not `None` (UNOBSERVED).

    `git status --porcelain` prints an empty string for a clean tree. The
    helper used to fold that empty output into `None`, which degraded every
    clean-checkout provenance receipt to "dirty unobserved" — the exact
    opposite of what a verification tool should claim about a clean tree.
    Found on the live 4.20.0 dashboard: a fully aligned, clean checkout still
    reported `source_dirty: null`.
    """
    target = _write_checkout(tmp_path / "HyoDo")
    commit = _git_init(target, "target")
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(target), str(clone)], check=True, capture_output=True)

    provenance = resolve_provenance(clone, package_root=clone, tool_version=SAME_VERSION)

    assert provenance.tool_commit == commit
    assert provenance.target_commit == commit
    assert provenance.tool_dirty is False
    assert provenance.target_dirty is False
    assert provenance.relation == "SELF_SAME_CHECKOUT"
    assert provenance.validity == "OBSERVED"


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


# --------------------------------------------------------------------------
# Fixture F — an installed copy (wheel) measuring a HyoDo checkout
#
# Found against the public 4.21.3 wheel on 2026-09-22. An installed copy has no
# commit of its own, yet two shortcuts gave it one:
#   * `git rev-parse` run inside site-packages answers with whatever repository
#     happens to enclose the virtualenv, so an unrelated repo's HEAD was
#     reported as the measuring code's commit;
#   * a virtualenv living inside the target made the package path look
#     "within" the checkout, so a wheel was declared the same code as a source
#     tree it had never been compared with — a false green on a clean,
#     committed edit to `hyodo/`.
# An installed copy is now compared by content: the files that actually run
# against the target's `hyodo/` source.
# --------------------------------------------------------------------------


def _install_copy(source_checkout: Path, site_packages: Path) -> Path:
    """Lay the checkout's `hyodo/` out the way a wheel install does."""
    site_packages.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_checkout / "hyodo", site_packages / "hyodo")
    return site_packages


def _venv_site_packages(root: Path) -> Path:
    return root / ".venv" / "lib" / "python3.12" / "site-packages"


@requires_git
def test_fixture_f_wheel_inside_the_target_is_not_trusted_after_the_source_changes(
    tmp_path: Path,
) -> None:
    """The false green: a clean, committed source edit next to an older wheel."""
    target = _write_checkout(tmp_path / "HyoDo")
    (target / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    _git_init(target, "target")
    site = _install_copy(target, _venv_site_packages(target))
    (target / "hyodo" / "__init__.py").write_text(
        '__version__ = "4.19.0"\nCHANGED = True\n', encoding="utf-8"
    )
    _commit_all(target, "edit the source the wheel was built from")

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    assert provenance.install_mode == "wheel"
    assert provenance.target_dirty is False
    assert provenance.relation == "SELF_OTHER_CHECKOUT"
    assert provenance.validity == "MISMATCH"
    assert provenance.is_green_allowed is False


@requires_git
def test_fixture_f_wheel_inside_the_target_with_identical_source_is_observed(
    tmp_path: Path,
) -> None:
    target = _write_checkout(tmp_path / "HyoDo")
    (target / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    _git_init(target, "target")
    site = _install_copy(target, _venv_site_packages(target))

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    assert provenance.relation == "SELF_SAME_CHECKOUT"
    assert provenance.validity == "OBSERVED"
    assert provenance.tool_commit is None


@requires_git
def test_fixture_f_an_enclosing_repository_is_not_the_wheels_commit(tmp_path: Path) -> None:
    """A virtualenv inside some other repo must not borrow that repo's HEAD."""
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    unrelated = tmp_path / "unrelated-project"
    unrelated.mkdir()
    (unrelated / "README.md").write_text("not hyodo\n", encoding="utf-8")
    (unrelated / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    unrelated_commit = _git_init(unrelated, "unrelated")
    site = _install_copy(target, _venv_site_packages(unrelated))

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    assert provenance.tool_commit is None
    assert provenance.tool_commit != unrelated_commit
    assert provenance.tool_dirty is None
    assert provenance.relation == "SELF_SAME_CHECKOUT"
    assert provenance.validity == "OBSERVED"


@requires_git
def test_fixture_f_a_diverged_wheel_is_a_mismatch_named_by_content(tmp_path: Path) -> None:
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    unrelated = tmp_path / "unrelated-project"
    unrelated.mkdir()
    (unrelated / "README.md").write_text("not hyodo\n", encoding="utf-8")
    _git_init(unrelated, "unrelated")
    site = _install_copy(target, _venv_site_packages(unrelated))
    (site / "hyodo" / "__init__.py").write_text('__version__ = "4.19.0"\n# old\n', encoding="utf-8")

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    assert provenance.tool_commit is None
    assert provenance.relation == "SELF_OTHER_CHECKOUT"
    assert provenance.validity == "MISMATCH"
    summary = provenance.summary()
    assert "MEASUREMENT MISMATCH" in summary
    assert "installed package content differs" in summary
    assert "unknown" not in summary


@requires_git
@pytest.mark.parametrize("side", ["target_only", "installed_only"])
def test_fixture_f_a_file_present_on_one_side_only_is_a_mismatch(tmp_path: Path, side: str) -> None:
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    site = _install_copy(target, tmp_path / "venv" / "lib" / "python3.12" / "site-packages")
    extra_root = target if side == "target_only" else site
    (extra_root / "hyodo" / "extra.py").write_text("# only here\n", encoding="utf-8")

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    assert provenance.relation == "SELF_OTHER_CHECKOUT"
    assert provenance.validity == "MISMATCH"


@requires_git
def test_fixture_f_bytecode_caches_are_not_source(tmp_path: Path) -> None:
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    site = _install_copy(target, tmp_path / "venv" / "lib" / "python3.12" / "site-packages")
    cache = site / "hyodo" / "__pycache__"
    cache.mkdir()
    (cache / "__init__.cpython-312.pyc").write_bytes(b"\x00compiled")

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    assert provenance.relation == "SELF_SAME_CHECKOUT"
    assert provenance.validity == "OBSERVED"


@requires_git
@pytest.mark.skipif(os.name != "posix", reason="mode-000 directory fixture is POSIX-only")
def test_fixture_f_an_unreadable_source_subdirectory_is_unobserved_not_mismatch(
    tmp_path: Path,
) -> None:
    """Unreadable source is missing evidence, not proof that source differs.

    Python 3.13+ Path.rglob() suppresses directory-scanning OSErrors. The old
    traversal then saw the unreadable subtree as absent and incorrectly
    classified an otherwise identical wheel/source pair as MISMATCH.
    """
    target = _write_checkout(tmp_path / "HyoDo")
    hidden = target / "hyodo" / "privatepkg"
    hidden.mkdir()
    (hidden / "__init__.py").write_text("# same source\n", encoding="utf-8")
    _git_init(target, "target")
    site = _install_copy(target, tmp_path / "venv" / "lib" / "python3.12" / "site-packages")

    previous_mode = hidden.stat().st_mode & 0o777
    hidden.chmod(0)
    try:
        try:
            next(hidden.iterdir())
        except PermissionError:
            pass
        else:
            pytest.skip("current user can still traverse a mode-000 directory")

        provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)
    finally:
        hidden.chmod(previous_mode)

    assert provenance.relation == "SOURCE_UNOBSERVED"
    assert provenance.validity == "UNOBSERVED"
    assert provenance.is_green_allowed is False


@requires_git
def test_fixture_f_an_installed_copy_that_cannot_be_read_is_unobserved(tmp_path: Path) -> None:
    """Boundary guard, not a regression lock: this already held before the fix.

    It pins the new content path's answer for an empty install to
    SOURCE_UNOBSERVED, so a later change cannot turn "nothing to compare"
    into a match.
    """
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    empty_site = tmp_path / "venv" / "lib" / "python3.12" / "site-packages"
    empty_site.mkdir(parents=True)

    provenance = resolve_provenance(target, package_root=empty_site, tool_version=SAME_VERSION)

    assert provenance.relation == "SOURCE_UNOBSERVED"
    assert provenance.validity == "UNOBSERVED"


@requires_git
def test_fixture_f_a_checkout_copy_nested_in_another_repo_borrows_no_commit(
    tmp_path: Path,
) -> None:
    """A checkout-shaped copy with no repository of its own has no commit to report."""
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    outer = tmp_path / "outer-repo"
    outer.mkdir()
    (outer / "README.md").write_text("outer\n", encoding="utf-8")
    outer_commit = _git_init(outer, "outer")
    nested_copy = _write_checkout(outer / "vendored" / "HyoDo")

    provenance = resolve_provenance(target, package_root=nested_copy, tool_version=SAME_VERSION)

    assert provenance.tool_commit != outer_commit
    assert provenance.tool_commit is None
    assert provenance.relation == "SOURCE_UNOBSERVED"


@requires_git
def test_fixture_f_a_stale_copy_nested_inside_the_target_is_not_the_target(
    tmp_path: Path,
) -> None:
    """Containment is not identity: a vendored copy inside the checkout proves nothing."""
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    nested = _write_checkout(target / "vendor" / "hyodo-old")
    (nested / "hyodo" / "__init__.py").write_text(
        '__version__ = "4.19.0"\n# old\n', encoding="utf-8"
    )

    provenance = resolve_provenance(target, package_root=nested, tool_version=SAME_VERSION)

    assert provenance.relation != "SELF_SAME_CHECKOUT"
    assert provenance.is_green_allowed is False


@requires_git
def test_fixture_f_a_nested_checkout_at_another_commit_is_a_mismatch(tmp_path: Path) -> None:
    """Two real repositories with different commits must be compared, not nested away."""
    target = _write_checkout(tmp_path / "HyoDo")
    (target / ".gitignore").write_text("nested/\n", encoding="utf-8")
    target_commit = _git_init(target, "target")
    nested = _write_checkout(target / "nested" / "HyoDo")
    (nested / "hyodo" / "drift.py").write_text("# different code\n", encoding="utf-8")
    nested_commit = _git_init(nested, "nested")
    assert nested_commit != target_commit

    provenance = resolve_provenance(target, package_root=nested, tool_version=SAME_VERSION)

    assert provenance.tool_commit == nested_commit
    assert provenance.relation == "SELF_OTHER_CHECKOUT"
    assert provenance.validity == "MISMATCH"


@requires_git
def test_inherited_git_location_variables_cannot_forge_the_targets_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`GIT_DIR`/`GIT_WORK_TREE` override `git -C <root>` for every call.

    Found by red-team review: pointing both at the measuring checkout made the
    target report the measurer's commit, so two different trees compared as
    the same commit and came out OBSERVED. Each query must describe the
    directory it names, whatever the caller's environment says.
    """
    target = _write_checkout(tmp_path / "HyoDo")
    target_commit = _git_init(target, "target")
    measurer = _write_checkout(tmp_path / "evil")
    (measurer / "hyodo" / "gates.py").write_text("# different code\n", encoding="utf-8")
    measurer_commit = _git_init(measurer, "evil")
    monkeypatch.setenv("GIT_DIR", str(measurer / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(measurer))

    provenance = resolve_provenance(target, package_root=measurer, tool_version=SAME_VERSION)

    assert provenance.target_commit == target_commit
    assert provenance.tool_commit == measurer_commit
    assert provenance.relation == "SELF_OTHER_CHECKOUT"
    assert provenance.validity == "MISMATCH"


@requires_git
@pytest.mark.parametrize("flag", ["--skip-worktree", "--assume-unchanged"])
def test_index_bits_that_hide_an_edit_cannot_make_two_trees_equal(
    tmp_path: Path, flag: str
) -> None:
    """Same commit and a clean `git status` are not the same code.

    Found by red-team review: `git update-index --skip-worktree` (or
    `--assume-unchanged`) on an edited file keeps `git status --porcelain`
    empty, so a tampered clone at the target's commit came out OBSERVED and
    `hyodo check` printed a full PASS. Equality is now always backed by the
    files themselves.
    """
    target = _write_checkout(tmp_path / "HyoDo")
    commit = _git_init(target, "target")
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(target), str(clone)], check=True, capture_output=True)
    (clone / "hyodo" / "__init__.py").write_text(
        '__version__ = "4.19.0"\n# hidden\n', encoding="utf-8"
    )
    subprocess.run(
        ["git", "-C", str(clone), "update-index", flag, "hyodo/__init__.py"],
        check=True,
        capture_output=True,
    )

    provenance = resolve_provenance(target, package_root=clone, tool_version=SAME_VERSION)

    assert provenance.tool_commit == provenance.target_commit == commit
    assert provenance.tool_dirty is False
    assert provenance.relation == "SELF_OTHER_CHECKOUT"
    assert provenance.validity == "MISMATCH"
    summary = provenance.summary()
    assert "commits match" in summary
    assert "same version string" not in summary


@requires_git
def test_a_git_that_lies_cannot_produce_a_green(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A `git` earlier on PATH may say anything; green still needs equal files."""
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    measurer = _write_checkout(tmp_path / "other")
    (measurer / "hyodo" / "gates.py").write_text("# different code\n", encoding="utf-8")
    _git_init(measurer, "other")
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()
    fake_git = fakebin / "git"
    fake_git.write_text(
        "#!/bin/sh\n"
        'root="$2"; shift 2\n'
        'case "$*" in\n'
        '  "rev-parse HEAD") echo deadbeefdeadbeefdeadbeefdeadbeefdeadbeef ;;\n'
        '  "rev-parse --show-toplevel") echo "$root" ;;\n'
        '  "status --porcelain") ;;\n'
        "esac\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fakebin}{os.pathsep}{os.environ['PATH']}")

    provenance = resolve_provenance(target, package_root=measurer, tool_version=SAME_VERSION)

    assert provenance.tool_commit == provenance.target_commit
    assert provenance.is_green_allowed is False


@pytest.mark.parametrize(
    "name_line",
    ['name="hyodo"', "name   =   'hyodo'", 'name = "HyoDo"', "name = 'HYODO'"],
)
def test_a_reformatted_project_name_is_still_a_hyodo_checkout(
    tmp_path: Path, name_line: str
) -> None:
    """Found by red-team review: `name="hyodo"` (no spaces) was read as another project.

    That moved a HyoDo target onto EXTERNAL_TARGET, the one relation that is
    green without any comparison, so a different tool's code measured it
    green. The name is now read as TOML and normalized.
    """
    root = tmp_path / "HyoDo"
    (root / "hyodo").mkdir(parents=True)
    (root / "hyodo" / "__init__.py").write_text("", encoding="utf-8")
    (root / "pyproject.toml").write_text(f"[project]\n{name_line}\n", encoding="utf-8")

    assert is_hyodo_checkout(root) is True


def test_an_unreadable_project_file_next_to_the_package_is_not_external(tmp_path: Path) -> None:
    """A pyproject that cannot be parsed must not buy the evidence-free green."""
    root = tmp_path / "HyoDo"
    (root / "hyodo").mkdir(parents=True)
    (root / "hyodo" / "__init__.py").write_text("", encoding="utf-8")
    (root / "pyproject.toml").write_text('[project\nname = "hyodo-broken\n', encoding="utf-8")

    assert is_hyodo_checkout(root) is True


@requires_git
def test_a_reformatted_target_is_still_compared(tmp_path: Path) -> None:
    target = tmp_path / "HyoDo"
    (target / "hyodo").mkdir(parents=True)
    (target / "hyodo" / "__init__.py").write_text('__version__ = "4.19.0"\n', encoding="utf-8")
    (target / "pyproject.toml").write_text('[project]\nname="hyodo"\n', encoding="utf-8")
    _git_init(target, "target")
    measurer = _write_checkout(tmp_path / "other")
    (measurer / "hyodo" / "gates.py").write_text("# different code\n", encoding="utf-8")
    _git_init(measurer, "other")

    provenance = resolve_provenance(target, package_root=measurer, tool_version=SAME_VERSION)

    assert provenance.relation != "EXTERNAL_TARGET"
    assert provenance.is_green_allowed is False


@requires_git
@pytest.mark.parametrize("cruft", [".DS_Store", ".gates.py.swp", "gates.py.swo", "gates.py~"])
def test_operating_system_and_editor_litter_is_not_source(tmp_path: Path, cruft: str) -> None:
    """A Finder or editor file beside the code is not code; it must not fail a match."""
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    site = _install_copy(target, tmp_path / "venv" / "lib" / "python3.12" / "site-packages")
    (target / "hyodo" / cruft).write_bytes(b"\x00litter")

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    assert provenance.relation == "SELF_SAME_CHECKOUT"
    assert provenance.validity == "OBSERVED"


@requires_git
def test_a_sourceless_module_beside_the_package_is_code(tmp_path: Path) -> None:
    """`hyodo/extra.pyc` outside `__pycache__/` imports as `hyodo.extra`."""
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    site = _install_copy(target, tmp_path / "venv" / "lib" / "python3.12" / "site-packages")
    (site / "hyodo" / "extra.pyc").write_bytes(b"\x00compiled")

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    assert provenance.relation == "SELF_OTHER_CHECKOUT"
    assert provenance.validity == "MISMATCH"


@requires_git
@pytest.mark.parametrize("damage", ["missing", "directory"])
def test_a_target_whose_project_file_is_gone_is_not_external(tmp_path: Path, damage: str) -> None:
    """A partial copy of a HyoDo checkout must not buy the evidence-free green.

    Found by red-team review: with `pyproject.toml` missing (or a directory),
    a target holding the real `hyodo/` source was classified EXTERNAL_TARGET
    and measured green by different code. The measuring side is unaffected:
    an installed copy in site-packages still has no project file and is still
    compared by content.
    """
    target = _write_checkout(tmp_path / "HyoDo")
    (target / "pyproject.toml").unlink()
    if damage == "directory":
        (target / "pyproject.toml").mkdir()
    measurer = _write_checkout(tmp_path / "other")
    (measurer / "hyodo" / "gates.py").write_text("# different code\n", encoding="utf-8")
    _git_init(measurer, "other")

    provenance = resolve_provenance(target, package_root=measurer, tool_version=SAME_VERSION)

    assert provenance.relation != "EXTERNAL_TARGET"
    assert provenance.is_green_allowed is False


@pytest.mark.parametrize(
    ("tool_commit", "must_say"),
    [
        (None, "installed HyoDo"),
        ("814f6fb7b0a52f7e935b2a253825d9516be9993e", "commits match"),
    ],
)
def test_dashboard_banner_names_the_kind_of_mismatch(
    tool_commit: str | None, must_say: str
) -> None:
    """An installed copy has no commit, and equal commits can hide different files.

    The banner used to print "commit unknown ... Same version string" for the
    first and two equal commits for the second, neither of which tells the
    reader what differs.
    """
    from hyodo.dashboard import _provenance_readout

    value, banner = _provenance_readout(
        {
            "provenance": {
                "relation": "SELF_OTHER_CHECKOUT",
                "validity": "MISMATCH",
                "target_commit": "814f6fb7b0a52f7e935b2a253825d9516be9993e",
                "tool_commit": tool_commit,
            }
        }
    )

    assert value == "MISMATCH"
    assert must_say in banner
    assert "unknown" not in banner
    assert "Same version string" not in banner


@requires_git
def test_every_git_location_variable_is_stripped() -> None:
    """A future git that adds a repository-relocating variable must fail here, not in the field."""
    from hyodo.provenance import _GIT_LOCATION_ENV

    listed = subprocess.run(
        ["git", "rev-parse", "--local-env-vars"], check=True, capture_output=True, text=True
    ).stdout.split()

    assert listed, "git printed no local environment variables"
    assert set(listed) <= _GIT_LOCATION_ENV


@requires_git
def test_a_tree_larger_than_the_hash_limit_is_unobserved_not_green(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Past the file limit nothing is compared, so nothing may be claimed equal."""
    monkeypatch.setattr("hyodo.provenance._MAX_SOURCE_FILES", 3)
    target = _write_checkout(tmp_path / "HyoDo")
    for index in range(5):
        (target / "hyodo" / f"module_{index}.py").write_text("# same\n", encoding="utf-8")
    _git_init(target, "target")
    site = _install_copy(target, tmp_path / "venv" / "lib" / "python3.12" / "site-packages")

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    assert provenance.relation == "SOURCE_UNOBSERVED"
    assert provenance.is_green_allowed is False


# --------------------------------------------------------------------------
# Benevolence: a normal developer setup running the same code is not a mismatch
# --------------------------------------------------------------------------


@requires_git
@pytest.mark.parametrize(
    "litter",
    [
        ".idea/workspace.xml",
        ".vscode/settings.json",
        ".mypy_cache/3.12/hyodo.json",
        ".pytest_cache/v/cache/nodeids",
        ".ruff_cache/0.1/cache",
        "gates.py.orig",
        "gates.py.rej",
        ".~lock.notes.odt#",
    ],
)
def test_tool_and_editor_directories_are_not_source(tmp_path: Path, litter: str) -> None:
    """Hidden paths cannot be imported as modules, and merge leftovers are not code."""
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    site = _install_copy(target, tmp_path / "venv" / "lib" / "python3.12" / "site-packages")
    stray = target / "hyodo" / litter
    stray.parent.mkdir(parents=True, exist_ok=True)
    stray.write_bytes(b"not code")

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    assert provenance.relation == "SELF_SAME_CHECKOUT"
    assert provenance.validity == "OBSERVED"


@requires_git
def test_windows_line_endings_are_the_same_code(tmp_path: Path) -> None:
    """A `core.autocrlf=true` checkout holds CRLF; Python reads it as the same source."""
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    site = _install_copy(target, tmp_path / "venv" / "lib" / "python3.12" / "site-packages")
    source = target / "hyodo" / "__init__.py"
    source.write_bytes(source.read_bytes().replace(b"\n", b"\r\n"))

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    assert provenance.relation == "SELF_SAME_CHECKOUT"
    assert provenance.validity == "OBSERVED"


@requires_git
def test_a_mismatch_names_the_file_that_differs(tmp_path: Path) -> None:
    """ "Content differs" alone sends a reader hunting; the first differing path does not."""
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    site = _install_copy(target, tmp_path / "venv" / "lib" / "python3.12" / "site-packages")
    (target / "hyodo" / "notes.txt").write_text("scratch\n", encoding="utf-8")

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    assert provenance.relation == "SELF_OTHER_CHECKOUT"
    assert "notes.txt" in provenance.summary()
    assert "only in this checkout" in provenance.summary()


def test_one_directory_spelled_two_ways_is_the_same_directory(tmp_path: Path) -> None:
    """A symlinked (or, on macOS, differently cased) path to the target is the target.

    Boundary guard: symlinks already resolved to the same path. The case
    spelling this protects cannot be built portably in a test, so the guard
    pins the shared `_same_directory` path both use.
    """
    target = _write_checkout(tmp_path / "HyoDo")
    alias = tmp_path / "alias"
    alias.symlink_to(target)
    (target / "hyodo" / "untracked_scratch.py").write_text("# local\n", encoding="utf-8")

    provenance = resolve_provenance(target, package_root=alias, tool_version=SAME_VERSION)

    assert provenance.relation == "SELF_SAME_CHECKOUT"


def test_an_editable_install_is_reported_as_editable(monkeypatch: pytest.MonkeyPatch) -> None:
    """uv writes `"editable":true` with no space; the marker check stripped spaces from one side only."""
    import hyodo.provenance as provenance_module

    class _Dist:
        def read_text(self, name: str) -> str:
            return '{"dir_info":{"editable":true},"url":"file:///x"}'

    monkeypatch.setattr(
        "importlib.metadata.Distribution.from_name", staticmethod(lambda _name: _Dist())
    )

    assert provenance_module._has_editable_marker() is True


@requires_git
@pytest.mark.parametrize("hidden", [".plugins/extra.py", ".data/config.json", ".hidden_module.py"])
def test_an_unlisted_hidden_path_is_still_compared(tmp_path: Path, hidden: str) -> None:
    """Only named tool and cache paths are skipped; any other dot path may be read by code."""
    target = _write_checkout(tmp_path / "HyoDo")
    _git_init(target, "target")
    site = _install_copy(target, tmp_path / "venv" / "lib" / "python3.12" / "site-packages")
    extra = target / "hyodo" / hidden
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("loaded by path\n", encoding="utf-8")

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    assert provenance.relation == "SELF_OTHER_CHECKOUT"
    assert provenance.validity == "MISMATCH"


@requires_git
@pytest.mark.parametrize("name", ["asset.bin", "icon.png", "notes.txt"])
def test_line_endings_are_normalized_only_in_known_text(tmp_path: Path, name: str) -> None:
    """A CRLF-only difference in a binary (or undecodable) file is a real byte difference."""
    target = _write_checkout(tmp_path / "HyoDo")
    payload = b"\xff\xfe binary\n\x80 more\n" if name != "notes.txt" else b"plain text\n"
    (target / "hyodo" / name).write_bytes(payload)
    _git_init(target, "target")
    site = _install_copy(target, tmp_path / "venv" / "lib" / "python3.12" / "site-packages")
    (target / "hyodo" / name).write_bytes(payload.replace(b"\n", b"\r\n"))

    provenance = resolve_provenance(target, package_root=site, tool_version=SAME_VERSION)

    if name == "notes.txt":
        assert provenance.relation == "SELF_SAME_CHECKOUT"
    else:
        assert provenance.relation == "SELF_OTHER_CHECKOUT"
