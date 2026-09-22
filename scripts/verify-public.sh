#!/usr/bin/env bash
# HyoDo public package verification (English)
# Does NOT install afo_core extended stack.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== HyoDo public verify =="
echo "root: $ROOT"

if [[ ! -f pyproject.toml ]] || [[ ! -d hyodo ]]; then
  echo "ERROR: run from HyoDo repo root"
  exit 1
fi

PYTHON="${PYTHON:-python3}"
BINDIR=""
if [[ -x .venv/bin/python ]]; then
  PYTHON=".venv/bin/python"
  BINDIR=".venv/bin"
elif [[ -x venv/bin/python ]]; then
  PYTHON="venv/bin/python"
  BINDIR="venv/bin"
else
  # Fresh macOS/Homebrew Python may be externally managed (PEP 668). Create
  # an isolated environment instead of attempting to mutate system packages.
  VENV_CREATOR="${PYTHON}"
  if ! "${VENV_CREATOR}" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' 2>/dev/null; then
    VENV_CREATOR=""
    for candidate in python3.14 python3.13 python3.12 python3.11 python3.10; do
      if command -v "${candidate}" >/dev/null 2>&1 && \
         "${candidate}" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' 2>/dev/null; then
        VENV_CREATOR="${candidate}"
        break
      fi
    done
  fi
  if [[ -z "${VENV_CREATOR}" ]]; then
    echo "ERROR: Python 3.10+ is required to create the verification environment" >&2
    exit 1
  fi
  echo "no project virtualenv found; creating .venv"
  "${VENV_CREATOR}" -m venv .venv
  PYTHON=".venv/bin/python"
  BINDIR=".venv/bin"
fi

echo "python: $PYTHON ($($PYTHON --version 2>&1))"

# Ensure the editable dev install exists. `uv venv` intentionally does not seed
# pip, so a perfectly standard project venv may make `python -m pip` unavailable.
# Prefer the existing pip path when present; otherwise use uv as the bootstrap
# installer for this interpreter. The dev extra includes pip, so later package
# build/install checks can continue using `python -m pip` without a second path.
if "$PYTHON" -m pip --version >/dev/null 2>&1; then
  "$PYTHON" -m pip install -e ".[dev]" -q
elif command -v uv >/dev/null 2>&1; then
  echo "pip not present in $PYTHON; bootstrapping dev dependencies with uv"
  uv pip install --python "$PYTHON" -e ".[dev]" -q
else
  echo "ERROR: $PYTHON has no pip and uv is unavailable; cannot install verification dependencies" >&2
  exit 1
fi
"$PYTHON" -m pip --version >/dev/null 2>&1 || {
  echo "ERROR: verification environment still has no pip after dependency bootstrap" >&2
  exit 1
}

if [[ -n "$BINDIR" && -x "$BINDIR/hyodo" ]]; then
  HYODO=("$BINDIR/hyodo")
else
  HYODO=("$PYTHON" -m hyodo.cli.main)
fi
echo "hyodo: ${HYODO[*]}"

echo "-- version sync --"
$PYTHON scripts/release/check_version_sync.py
EXPECTED_VERSION="$(tr -d '[:space:]' < VERSION)"

echo "-- ruff --"
# Same scope as the CI lane (.github/workflows/ci.yml): release scripts are
# linted too. A narrower scope here made this script report success on a tree
# that CI then rejected.
$PYTHON -m ruff check hyodo tests scripts --output-format=concise
$PYTHON -m ruff format --check hyodo tests scripts

echo "-- pyright --"
$PYTHON -m pyright --pythonpath "$PYTHON" hyodo

echo "-- pytest --"
# Exercise the opt-in SBOM build/venv/inventory path in the bounded public
# verification lane so the published test result does not hide that coverage.
HYODO_SBOM_INTEGRATION=1 $PYTHON -m pytest tests -q --tb=short

echo "-- shell syntax --"
bash -n install.sh
bash -n install_interactive.sh

echo "-- package build --"
VERIFY_PARENT="${TMPDIR:-/tmp}"
if [[ ! -d "$VERIFY_PARENT" ]]; then
  VERIFY_PARENT="/tmp"
fi
VERIFY_DIR="$(mktemp -d "$VERIFY_PARENT/hyodo-public-verify.XXXXXX")"
echo "verification artifacts: $VERIFY_DIR"
# Upgrade explicitly: a stale local twine (<7) cannot parse Metadata-Version 2.5
# sdist metadata produced by current hatchling and fails `twine check` spuriously.
$PYTHON -m pip install -q --upgrade build twine
$PYTHON -m build --outdir "$VERIFY_DIR/dist"
# `dist/` also contains the CycloneDX SBOM, which is a release evidence
# asset rather than a Python distribution.  Keep Twine scoped to artifacts
# that it can validate as uploadable package files.
$PYTHON -m twine check "$VERIFY_DIR"/dist/*.whl "$VERIFY_DIR"/dist/*.tar.gz

echo "-- built-artifact README links --"
# The source-only pytest run above cannot see these artifacts and reports this
# check as UNOBSERVED. Re-run it against the files just built, and require them,
# so the description users actually download is observed on every verify.
HYODO_DIST_DIR="$VERIFY_DIR/dist" HYODO_REQUIRE_BUILT_ARTIFACTS=1 \
  $PYTHON -m pytest tests/test_pypi_readme_links.py -q --tb=short \
  -k test_built_artifacts_publish_the_rewritten_description -rs -p no:cacheprovider \
  | tee "$VERIFY_DIR/readme-artifact-pytest.log"
if ! grep -Eq '^=* ?1 passed, [0-9]+ deselected in ' "$VERIFY_DIR/readme-artifact-pytest.log"; then
  echo "ERROR: built-artifact README check did not pass exactly once (see above)" >&2
  exit 1
fi

echo "-- sdist must not ship afo_core --"
"$PYTHON" scripts/release/verify_sdist_scope.py "$VERIFY_DIR"/dist/*.tar.gz
$PYTHON - "$VERIFY_DIR/dist" <<'PY'
import sys
import tarfile
import zipfile
from pathlib import Path

dist = Path(sys.argv[1])
sdists = list(dist.glob("*.tar.gz"))
assert sdists, "no sdist found"
with tarfile.open(sdists[0]) as t:
    names = t.getnames()
required = {
    "/schemas/runtime-identity-v1.schema.json",
    "/schemas/runtime-identity-v1.pin.json",
}
missing = [suffix for suffix in required if not any(name.endswith(suffix) for name in names)]
if missing:
    raise SystemExit(f"ERROR: sdist missing runtime identity contract files: {missing}")
bad = [n for n in names if "/afo_core/" in n or n.endswith("/afo_core")]
if bad:
    raise SystemExit(f"ERROR: sdist contains afo_core paths ({len(bad)}), e.g. {bad[:3]}")
print(f"sdist content checks ok: {sdists[0].name}, {len(names)} entries")

wheels = list(dist.glob("*.whl"))
assert wheels, "no wheel found"
with zipfile.ZipFile(wheels[0]) as archive:
    wheel_names = set(archive.namelist())
required_wheel = {
    "schemas/runtime-identity-v1.schema.json",
    "schemas/runtime-identity-v1.pin.json",
}
missing_wheel = sorted(required_wheel - wheel_names)
if missing_wheel:
    raise SystemExit(f"ERROR: wheel missing runtime identity contract files: {missing_wheel}")
print(f"wheel ok: {wheels[0].name}, runtime identity files present")
PY

echo "-- wheel install smoke --"
$PYTHON -m venv "$VERIFY_DIR/wheel-venv"
WHEEL_PYTHON="$VERIFY_DIR/wheel-venv/bin/python"
"$WHEEL_PYTHON" -m pip install -q "$VERIFY_DIR/dist/hyodo-${EXPECTED_VERSION}-py3-none-any.whl"
(
cd "$VERIFY_DIR"
"$VERIFY_DIR/wheel-venv/bin/hyodo" --version | grep -F "$EXPECTED_VERSION"
"$WHEEL_PYTHON" -I - <<PY
import hyodo
import sys
from pathlib import Path
assert Path(hyodo.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
assert hyodo.__version__ == "${EXPECTED_VERSION}", hyodo.__version__
from hyodo import is_strong_review_signal, calculate_hygook_v5_score
assert is_strong_review_signal(95, 5) is True
assert is_strong_review_signal(50, 5) is False
f, s = calculate_hygook_v5_score(1, 1, 1, 1, 1)
assert round(f, 2) == 60.00 and round(s, 2) == 10.00
print("wheel import API ok")
PY
)

echo "-- CLI smoke --"
# The working environment remains editable; the wheel smoke uses its own venv.
# HyoDo checkout: expect executed gates to pass (never the false-green "All gates passed" alone)
set +e
"${HYODO[@]}" check >"$VERIFY_DIR/check.out" 2>&1
CHECK_EC=$?
set -e
grep -q "All executed gates passed" "$VERIFY_DIR/check.out"
test "$CHECK_EC" -eq 0
# Empty/non-HyoDo tree must not false-green
EMPTY_DIR="$VERIFY_DIR/empty"
mkdir "$EMPTY_DIR"
set +e
"${HYODO[@]}" check "$EMPTY_DIR" >"$VERIFY_DIR/check-empty.out" 2>&1
EMPTY_EC=$?
set -e
test "$EMPTY_EC" -eq 2
grep -q "No project gates were executed" "$VERIFY_DIR/check-empty.out"
grep -q "This is not a validation pass" "$VERIFY_DIR/check-empty.out"
if grep -q "All gates passed" "$VERIFY_DIR/check-empty.out"; then
  echo "ERROR: false-green 'All gates passed' on empty tree"
  exit 1
fi
"${HYODO[@]}" score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --hyo 0.9 >"$VERIFY_DIR/score.out"
grep -q "REVIEW_SIGNAL" "$VERIFY_DIR/score.out"
printf 'token = ghp_abcdefghijklmnopqrstuvwxyz012345\n' >"$VERIFY_DIR/safe-fixture.txt"
set +e
"${HYODO[@]}" safe "$VERIFY_DIR/safe-fixture.txt" >"$VERIFY_DIR/safe.out" 2>&1
SAFE_EC=$?
"${HYODO[@]}" safe --strict "$VERIFY_DIR/safe-fixture.txt" >"$VERIFY_DIR/safe-strict.out" 2>&1
SAFE_STRICT_EC=$?
set -e
test "$SAFE_EC" -eq 0
test "$SAFE_STRICT_EC" -eq 1
grep -Eq "secret|Risk|high|caution" "$VERIFY_DIR/safe.out"

echo "-- claim regression (public surfaces) --"
if grep -rEn "Auto-approve|AUTO_RUN|Proceed immediately|Candidate for approval" \
  README.md QUICK_START.md SECURITY.md CONTRIBUTING.md \
  RELEASE_CHECKLIST.md hyodo/cli/main.py commands/score.md commands/check.md 2>/dev/null; then
  echo "ERROR: banned auto-approve / proceed-immediately phrasing found"
  exit 1
fi

echo "== PASS: public package verify =="
