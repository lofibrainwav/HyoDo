#!/usr/bin/env python3
"""Generate a CycloneDX SBOM for the *public* HyoDo surface only.

The public runtime closure is `typer`, `rich` and their transitive
dependencies. To avoid inventorying the dev environment (which would pull the
generator itself plus pytest/ruff/pyright into the SBOM), this builds the public
wheel and installs it into a clean throwaway virtualenv created **without pip**
(so the venv bootstrap packages `pip`/`setuptools`/`wheel` never leak into the
inventory), then inventories *that* environment. The result is scope-checked
before it is accepted.

Used by the Eternity gate (`hyodo check` -> `run_sbom_check`) and by the advisory
CI step. "Offline" here means the *generation* step makes no network calls;
provisioning the clean venv (installing the wheel + typer/rich) may.

Exit codes: 0 = scoped SBOM written; 2 = scope violation (a real defect); 3 =
environment failure (could not build/install/inventory — e.g. offline).
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import sys
import sysconfig
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "dist" / "sbom.cyclonedx.json"

# The public runtime closure must be present.
REQUIRED_COMPONENTS = {"typer", "rich"}

# These must never appear in a public SBOM: venv bootstrap seeds, the generator
# itself, dev/test/lint tooling, and anything from the advisory afo_core tree.
FORBIDDEN_COMPONENTS = {
    "pip",
    "setuptools",
    "wheel",
    "cyclonedx-bom",
    "cyclonedx-python-lib",
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "hypothesis",
    "ruff",
    "pyright",
    "build",
    "twine",
    "pyyaml",
    "fastapi",
    "httpx",
}


class ScopeError(ValueError):
    """Raised when a generated SBOM is not exactly the public runtime closure."""


def _component_names(sbom: dict) -> set[str]:
    return {c["name"].lower() for c in sbom.get("components", [])}


def assert_public_scope(sbom: dict) -> None:
    """Raise ScopeError unless the SBOM is exactly the public runtime closure."""
    names = _component_names(sbom)

    missing = sorted(r for r in REQUIRED_COMPONENTS if r not in names)
    if missing:
        raise ScopeError(f"SBOM is missing required public runtime components: {missing}")

    leaked = sorted(names & FORBIDDEN_COMPONENTS)
    if leaked:
        raise ScopeError(f"SBOM leaked dev/bootstrap components: {leaked}")

    afo = sorted(n for n in names if "afo_core" in n or "afo-core" in n)
    if afo:
        raise ScopeError(f"SBOM leaked afo_core components: {afo}")


def normalize_for_comparison(sbom: dict) -> tuple:
    """Reduce an SBOM to its stable contract for reproducibility comparison.

    Volatile fields (serialNumber, metadata.timestamp) are ignored. The
    ``environment`` command emits a trivial dependency graph, so the meaningful
    stable signal is the component (name, version) set.
    """
    components = sorted((c["name"], c.get("version")) for c in sbom.get("components", []))
    dependencies = sorted(
        (d["ref"], tuple(sorted(d.get("dependsOn", [])))) for d in sbom.get("dependencies", [])
    )
    return components, dependencies


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)


def _clean_venv_runtime_env() -> dict[str, str] | None:
    """Return a local loader environment for portable macOS Python builds.

    uv's macOS Python distributions use an ``@executable_path`` reference for
    ``libpython``.  A venv relocates the interpreter but not that sibling
    library, so Python launched from the clean venv can fail before pip or
    CycloneDX gets a chance to run.  Only add the loader path when the ambient
    interpreter explicitly advertises an existing library; other platforms and
    incomplete installations keep the normal subprocess environment.
    """
    if sys.platform != "darwin":
        return None

    libdir = sysconfig.get_config_var("LIBDIR")
    ldlib = sysconfig.get_config_var("LDLIBRARY")
    if not libdir or not ldlib:
        return None

    library = Path(libdir) / ldlib
    if not library.is_file():
        return None

    env = os.environ.copy()
    existing = env.get("DYLD_LIBRARY_PATH")
    env["DYLD_LIBRARY_PATH"] = (
        f"{library.parent}{os.pathsep}{existing}" if existing else str(library.parent)
    )
    return env


def build_clean_env(workdir: Path) -> Path:
    """Build the public wheel and install it into a pip-less clean venv.

    The venv is created *without* pip so no bootstrap packages are seeded; the
    wheel is installed using the ambient interpreter's pip via ``--python``, so
    only the wheel's own runtime closure ends up in the inventoried environment.
    Returns the clean venv's python interpreter.
    """
    wheel_dir = workdir / "wheel"
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            str(wheel_dir),
            str(ROOT),
        ]
    )
    wheels = sorted(wheel_dir.glob("hyodo-*.whl"))
    if not wheels:
        raise RuntimeError("wheel build produced no hyodo wheel")

    clean = workdir / "cleanvenv"
    venv.create(clean, with_pip=False)
    py = clean / "bin" / "python"
    if not py.exists():  # pragma: no cover - windows layout
        py = clean / "Scripts" / "python.exe"
    clean_env = _clean_venv_runtime_env()
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "--python",
            str(py),
            "install",
            "--disable-pip-version-check",
            "-q",
            str(wheels[0]),
        ],
        env=clean_env,
    )
    return py


def generate(output: Path = DEFAULT_OUTPUT) -> dict:
    """Generate the public SBOM to `output` and return it. Scope is enforced.

    A scope violation removes the (mis-scoped) output file before raising, so a
    nonzero exit never leaves a misleading artifact on disk.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hyodo-sbom-") as tmp:
        py = build_clean_env(Path(tmp))
        _run(
            [
                sys.executable,
                "-m",
                "cyclonedx_py",
                "environment",
                str(py),
                "--pyproject",
                str(ROOT / "pyproject.toml"),
                "--mc-type",
                "library",
                "--output-reproducible",
                "--of",
                "JSON",
                "-o",
                str(output),
            ],
            env=_clean_venv_runtime_env(),
        )
        sbom = json.loads(output.read_text(encoding="utf-8"))
        try:
            assert_public_scope(sbom)
        except ScopeError:
            # Remove the mis-scoped artifact, but never let a cleanup error mask
            # the ScopeError — a scope violation must always surface as exit 2.
            with contextlib.suppress(OSError):
                output.unlink(missing_ok=True)
            raise
        return sbom


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a CycloneDX SBOM for the public HyoDo surface."
    )
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    try:
        sbom = generate(output=args.output)
    except ScopeError as exc:
        print(f"SBOM scope violation: {exc}", file=sys.stderr)
        return 2
    except (subprocess.CalledProcessError, RuntimeError, FileNotFoundError, OSError) as exc:
        detail = exc.stderr.strip() if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        print(f"SBOM generation failed (environment): {detail}", file=sys.stderr)
        return 3

    components = sorted(c["name"] for c in sbom.get("components", []))
    print(f"SBOM written to {args.output} ({len(components)} components): {', '.join(components)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
