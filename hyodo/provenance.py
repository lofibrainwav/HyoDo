"""Measurement provenance: which HyoDo code measured which target, from where.

A PASS proves nothing until you know what produced it. HyoDo's own local CLI
made that concrete on 2026-09-10: a virtualenv in one checkout resolved its
editable install to a *different* HyoDo checkout, so `hyodo check` measured
this repository's files with another repository's gate code. Both reported
`v4.19.0`. Nothing in the output distinguished them.

That failure has a shape worth naming. It is not a policy question — no rule
was violated and no authority was exceeded — so it does not belong on the
ALLOW/DENY/ASK/UNOBSERVED axis, which describes what an actor was permitted
to do. It is a question about whether a measurement is *valid at all*, and it
gets its own axis:

    policy      ALLOW / DENY / ASK / UNOBSERVED
    provenance  OBSERVED / MISMATCH / UNOBSERVED

The two are independent. A run can be fully permitted and still be measured by
the wrong code.

Relations
---------
The naive rule "package root != target root, therefore complain" is wrong, and
wrong in the direction that would make HyoDo useless: the normal, intended
shape of this tool is an installed HyoDo measuring somebody else's project.
The relation is classified first, and only self-measurement can mismatch:

``EXTERNAL_TARGET``
    The target is not a HyoDo checkout. This is ordinary use. Provenance is
    recorded and has no effect on any gate.
``SELF_SAME_CHECKOUT``
    HyoDo measuring itself with its own code.
``SELF_OTHER_CHECKOUT``
    HyoDo measuring itself with code from somewhere else. Never green.
``SOURCE_UNOBSERVED``
    Self-measurement where the sources cannot be compared. Recorded as
    unobserved, never silently green.

Version is deliberately absent from that decision. Two builds can carry the
same version string and different code — that is exactly how the original
accident stayed invisible. Equal versions never prove equal sources here.

Privacy
-------
An absolute path carries a username. `to_local_dict()` keeps paths, because a
developer reading their own terminal needs them. `to_portable_dict()` is what
travels: commit ids, install mode, relation, and salted-free digests of the
paths, so two receipts can still be compared for "same place or not" without
publishing anyone's home directory.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

PROVENANCE_SCHEMA_VERSION = "hyodo.measurement-provenance/v1"

Relation = Literal[
    "EXTERNAL_TARGET",
    "SELF_SAME_CHECKOUT",
    "SELF_OTHER_CHECKOUT",
    "SOURCE_UNOBSERVED",
]
Validity = Literal["OBSERVED", "MISMATCH", "UNOBSERVED"]
InstallMode = Literal["editable", "wheel", "source", "unknown"]

#: Relation -> measurement validity. Kept as data so the mapping can be read
#: at a glance and asserted in one test rather than traced through branches.
_VALIDITY_BY_RELATION: dict[str, Validity] = {
    "EXTERNAL_TARGET": "OBSERVED",
    "SELF_SAME_CHECKOUT": "OBSERVED",
    "SELF_OTHER_CHECKOUT": "MISMATCH",
    "SOURCE_UNOBSERVED": "UNOBSERVED",
}

_GIT_TIMEOUT_SECONDS = 5


def _run_git(root: Path, *args: str) -> str | None:
    """`git -C root <args>`, or None if git is absent or the call fails.

    Provenance must never be the reason a measurement crashes: every failure
    here degrades to "not observed", which the caller reports honestly.
    """
    if shutil.which("git") is None:
        return None
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def git_commit(root: Path) -> str | None:
    """Full commit id of the checkout containing `root`, if it is one."""
    return _run_git(root, "rev-parse", "HEAD")


def git_is_dirty(root: Path) -> bool | None:
    """True if the checkout has uncommitted changes; None if unobservable."""
    if git_commit(root) is None:
        return None
    status = _run_git(root, "status", "--porcelain")
    if status is None:
        return None
    return bool(status.strip())


def path_digest(value: Path | str | None) -> str | None:
    """Stable, non-reversing id for a filesystem path.

    Portable receipts need to answer "was this the same place?" without
    carrying `/Users/<name>/...` off the machine that produced them.
    """
    if value is None:
        return None
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]


def is_hyodo_checkout(root: Path) -> bool:
    """True when `root` is a source checkout of HyoDo itself.

    Deliberately narrow: a directory that merely contains a folder called
    `hyodo` is not a checkout, so an unrelated project cannot be misread as
    self-measurement and dragged onto the mismatch path.
    """
    if not (root / "hyodo" / "__init__.py").is_file():
        return False
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return False
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:
        return False
    return 'name = "hyodo"' in text or "name = 'hyodo'" in text


def _detect_install_mode(package_root: Path | None) -> InstallMode:
    """editable / wheel / source, from where the imported package actually is."""
    if package_root is None:
        return "unknown"
    parts = {part.lower() for part in package_root.parts}
    if "site-packages" in parts or "dist-packages" in parts:
        return "wheel"
    if is_hyodo_checkout(package_root):
        # imported straight out of a checkout: either an editable install
        # pointing at it, or a plain `python -m hyodo` from the source tree
        return "editable" if _has_editable_marker() else "source"
    return "unknown"


def _has_editable_marker() -> bool:
    """True when this interpreter resolves `hyodo` through an editable install."""
    try:
        from importlib.metadata import Distribution, PackageNotFoundError
    except ImportError:  # pragma: no cover - importlib.metadata is stdlib
        return False
    try:
        direct_url = Distribution.from_name("hyodo").read_text("direct_url.json")
    except (PackageNotFoundError, OSError, ValueError):
        return False
    if not direct_url:
        return False
    return '"editable": true' in direct_url.replace(" ", "")


def _default_package_root() -> Path | None:
    """Directory that contains the imported `hyodo` package, if resolvable."""
    module = sys.modules.get(__name__)
    file = getattr(module, "__file__", None)
    if not file:
        return None
    return Path(file).resolve().parent.parent


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


@dataclass(frozen=True)
class MeasurementProvenance:
    """Who measured what, with which code, and whether that is even valid."""

    schema_version: str
    tool_name: str
    tool_version: str | None
    package_root: Path | None
    python_executable: str | None
    target_root: Path
    tool_commit: str | None
    target_commit: str | None
    tool_dirty: bool | None
    target_dirty: bool | None
    install_mode: InstallMode
    relation: Relation

    @property
    def validity(self) -> Validity:
        """Whether this measurement is valid at all, on its own axis.

        Never ALLOW/DENY/ASK: those answer what an actor was permitted to do,
        which is a different question from whether the measuring code was the
        right code.
        """
        return _VALIDITY_BY_RELATION[self.relation]

    @property
    def is_green_allowed(self) -> bool:
        """False when a green verdict would be unsupported by its own origin."""
        return self.validity == "OBSERVED"

    def summary(self) -> str:
        """One line a person can act on, in the terminal they are already reading."""
        if self.relation == "EXTERNAL_TARGET":
            return f"measured by {self.tool_name} {self.tool_version or '?'} ({self.install_mode})"
        if self.relation == "SELF_SAME_CHECKOUT":
            return f"self-measured from this checkout ({self.install_mode})"
        if self.relation == "SELF_OTHER_CHECKOUT":
            return (
                f"MEASUREMENT MISMATCH: target {_short(self.target_commit)} was measured by "
                f"{self.tool_name} from {self.package_root} at {_short(self.tool_commit)} — "
                "same version string, different code"
            )
        return (
            "measurement source UNOBSERVED: cannot prove the measuring code matches this "
            f"checkout ({self.install_mode})"
        )

    def to_local_dict(self) -> dict[str, Any]:
        """Full detail, absolute paths included. For this machine only."""
        return {
            "schema_version": self.schema_version,
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "package_root": str(self.package_root) if self.package_root else None,
            "python_executable": self.python_executable,
            "target_root": str(self.target_root),
            "tool_commit": self.tool_commit,
            "target_commit": self.target_commit,
            "tool_dirty": self.tool_dirty,
            "target_dirty": self.target_dirty,
            "install_mode": self.install_mode,
            "relation": self.relation,
            "validity": self.validity,
        }

    def to_portable_dict(self) -> dict[str, Any]:
        """What may leave the machine: no absolute paths, no usernames."""
        return {
            "schema_version": self.schema_version,
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "package_root_digest": path_digest(self.package_root),
            "target_root_digest": path_digest(self.target_root),
            "python_version": ".".join(str(p) for p in sys.version_info[:3]),
            "tool_commit": self.tool_commit,
            "target_commit": self.target_commit,
            "tool_dirty": self.tool_dirty,
            "target_dirty": self.target_dirty,
            "install_mode": self.install_mode,
            "relation": self.relation,
            "validity": self.validity,
        }


def _short(commit: str | None) -> str:
    return commit[:8] if commit else "unknown"


def _classify(
    *,
    target_root: Path,
    package_root: Path | None,
    tool_commit: str | None,
    target_commit: str | None,
    tool_dirty: bool | None,
    target_dirty: bool | None,
) -> Relation:
    """Relation between the measuring code and the measured target.

    Version is not an input. Two builds can share a version string and differ
    in every line of code, which is precisely how the original mismatch stayed
    invisible for hours.
    """
    if not is_hyodo_checkout(target_root):
        return "EXTERNAL_TARGET"
    if package_root is not None and _is_within(package_root, target_root):
        return "SELF_SAME_CHECKOUT"
    if tool_commit is None or target_commit is None:
        return "SOURCE_UNOBSERVED"
    if tool_commit != target_commit:
        return "SELF_OTHER_CHECKOUT"
    # Equal commits, but a dirty tree means the commit under-describes the code
    # that actually ran, so equality cannot be claimed.
    if tool_dirty or target_dirty:
        return "SOURCE_UNOBSERVED"
    return "SELF_SAME_CHECKOUT"


def resolve_provenance(
    target_root: Path,
    *,
    package_root: Path | None = None,
    tool_version: str | None = None,
    tool_name: str = "hyodo",
    python_executable: str | None = None,
) -> MeasurementProvenance:
    """Describe the current measurement's origin.

    Every argument can be supplied explicitly so the classification can be
    exercised against real directory layouts in tests instead of only against
    whatever this interpreter happens to be running.
    """
    target = Path(target_root).resolve()
    package = Path(package_root).resolve() if package_root is not None else _default_package_root()

    if tool_version is None:
        try:
            from hyodo import __version__ as _version

            tool_version = _version
        except (ImportError, AttributeError):  # pragma: no cover - defensive
            tool_version = None

    tool_commit = git_commit(package) if package is not None else None
    target_commit = git_commit(target)
    tool_dirty = git_is_dirty(package) if package is not None else None
    target_dirty = git_is_dirty(target)

    relation = _classify(
        target_root=target,
        package_root=package,
        tool_commit=tool_commit,
        target_commit=target_commit,
        tool_dirty=tool_dirty,
        target_dirty=target_dirty,
    )

    return MeasurementProvenance(
        schema_version=PROVENANCE_SCHEMA_VERSION,
        tool_name=tool_name,
        tool_version=tool_version,
        package_root=package,
        python_executable=python_executable if python_executable is not None else sys.executable,
        target_root=target,
        tool_commit=tool_commit,
        target_commit=target_commit,
        tool_dirty=tool_dirty,
        target_dirty=target_dirty,
        install_mode=_detect_install_mode(package),
        relation=relation,
    )
