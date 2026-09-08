"""Installed HyoDo CLI dispatcher.

The mature command surface remains defined in :mod:`hyodo.cli.main`. This
module adds the local-only Friction Contribution sub-app without modifying the
large legacy command module, keeping every existing command registration and
callback intact.
"""

from hyodo.cli.main import app
from hyodo.friction_cli import app as friction_app

app.add_typer(friction_app, name="friction")

__all__ = ["app"]
