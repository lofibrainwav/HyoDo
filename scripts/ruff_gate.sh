#!/usr/bin/env bash
set -euo pipefail

echo "== ruff report (exit-zero) =="
ruff check . --exit-zero --statistics

echo
echo "== ruff gate (core only) =="
ruff check packages/afo-core packages/dashboard
