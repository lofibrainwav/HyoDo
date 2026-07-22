"""Dashboard target resolution for Bring-Your-Own-Gates projects.

Before this contract the dashboard required a HyoDo package checkout
(``pyproject.toml`` + ``hyodo/``), so a project that had already adopted
HyoDo through ``hyodo init`` -- i.e. it owns a ``.hyodo/gates.toml`` --
was rejected with exit 2 and could never see In/Hyo/Yeong.

The gate is widened for the dashboard only. ``find_repo_root`` keeps its
original meaning ("is this a HyoDo package checkout?") because ``check``
and the built-in preset selection depend on it.
"""

from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app, find_repo_root, resolve_dashboard_root

runner = CliRunner()

GATES_TOML = """schema = "hyodo.gates/v1"

[gates.echo]
pillar = "truth"
command = "true"
timeout = 30
"""


def _byog_project(tmp_path: Path) -> Path:
    (tmp_path / ".hyodo").mkdir()
    (tmp_path / ".hyodo" / "gates.toml").write_text(GATES_TOML, encoding="utf-8")
    return tmp_path


def test_byog_project_is_accepted_as_dashboard_root(tmp_path):
    """A project with .hyodo/gates.toml is a valid dashboard target."""
    project = _byog_project(tmp_path)
    assert resolve_dashboard_root(project) == project.resolve()


def test_hyodo_checkout_still_resolves(tmp_path):
    """The original HyoDo checkout path keeps working (no regression)."""
    checkout = find_repo_root(Path(__file__).resolve())
    assert checkout is not None
    assert resolve_dashboard_root(checkout) == checkout


def test_plain_directory_is_still_rejected(tmp_path):
    """No gates.toml and no hyodo/ package -> still unobservable, not green."""
    (tmp_path / "README.md").write_text("nothing here\n", encoding="utf-8")
    assert resolve_dashboard_root(tmp_path) is None


def test_find_repo_root_meaning_is_unchanged(tmp_path):
    """BYOG adoption must NOT make a project look like a HyoDo checkout.

    find_repo_root answers "is this a HyoDo package checkout?" and is used by
    check and preset selection -- widening it there would mis-route those.
    """
    project = _byog_project(tmp_path)
    assert find_repo_root(project) is None


def test_dashboard_rejects_plain_directory_with_exit_2(tmp_path):
    """Unobservable target stays exit 2 -- never a silent pass."""
    (tmp_path / "README.md").write_text("nothing\n", encoding="utf-8")
    result = runner.invoke(app, ["dashboard", str(tmp_path), "--once"])
    assert result.exit_code == 2
