#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: $0 <path-to-IEP-file> [label]"
  exit 2
fi

SRC="$1"
LABEL="${2:-IEP}"

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

test -f "$SRC" || { echo "[FAIL] file not found: $SRC"; exit 1; }

DEST_DIR="docs/evidence/ieps"
mkdir -p "$DEST_DIR"

BASENAME="$(basename "$SRC")"
DEST="$DEST_DIR/$BASENAME"

cp -f "$SRC" "$DEST"

SHA="$(shasum -a 256 "$DEST" | awk '{print $1}')"
echo "$SHA  $DEST" > "$DEST.sha256"

INDEX="docs/evidence/INDEX.md"
touch "$INDEX"

if ! rg -qF "$DEST" "$INDEX" 2>/dev/null; then
  {
    echo "- [$LABEL] $BASENAME"
    echo "  - file: $DEST"
    echo "  - sha256: $SHA"
    echo "  - as-of: $(date -I)"
  } >> "$INDEX"
fi

echo "[OK] imported: $DEST"
echo "[OK] sha256:  $SHA"
echo "[OK] index:   $INDEX"
