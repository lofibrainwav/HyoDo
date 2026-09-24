#!/usr/bin/env bash
# Hostile-clone gauntlet: attack the built wheel with a repository that ships
# its own HyoDo authority state (gate approvals, policy trust, pairing, scan
# exceptions, ledgers). Release blocker: publish.yml runs this against the
# exact wheel it is about to upload, and CI runs it on every change.
#
# Usage: scripts/release/hostile_clone_gauntlet.sh dist/hyodo-X.Y.Z-py3-none-any.whl
#
# A skipped, deselected, or short run is a failure, never a pass.
set -euo pipefail

wheel="${1:?usage: hostile_clone_gauntlet.sh <wheel>}"
test -f "$wheel"
min_tests=10

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

uv venv --quiet --python 3.12 "$work/venv"
constraint=()
if [ -f requirements.runtime.txt ]; then
  constraint=(--constraint requirements.runtime.txt)
fi
uv pip install --quiet --python "$work/venv/bin/python" "${constraint[@]}" "$wheel"

installed="$(cd "$work" && "$work/venv/bin/python" -c 'import hyodo, pathlib; print(pathlib.Path(hyodo.__file__).resolve())')"
case "$installed" in
  "$(cd "$work" && pwd -P)"/venv/*) ;;
  *) echo "gauntlet: wheel interpreter imports hyodo from $installed, not the wheel" >&2; exit 1 ;;
esac

HYODO_GAUNTLET_PYTHON="$work/venv/bin/python" \
  python -m pytest tests/test_hostile_clone.py -q -p no:cacheprovider \
  --junitxml="$work/gauntlet.xml"

python - "$work/gauntlet.xml" "$min_tests" <<'PY'
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1]).getroot()
suite = root if root.tag == "testsuite" else root.find("testsuite")
assert suite is not None, "gauntlet: no testsuite in junit report"
tests = int(suite.get("tests", "0"))
bad = {key: int(suite.get(key, "0")) for key in ("failures", "errors", "skipped")}
minimum = int(sys.argv[2])
if tests < minimum or any(bad.values()):
    print(f"gauntlet: BLOCK tests={tests} (min {minimum}) {bad}", file=sys.stderr)
    sys.exit(1)
print(f"gauntlet: PASS {tests} hostile-clone checks against the built wheel")
PY
