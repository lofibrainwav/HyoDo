#!/usr/bin/env bash
# Truth MyPy 실행 (AFO/services symlink exclude)
# PH12-001: symlink 중복 분석 잡음 제거

set -euo pipefail

MYPYPATH=. python3 -m mypy \
  --explicit-package-bases \
  --ignore-missing-imports \
  --exclude '(^|/)AFO/services(/|$)' \
  services/ AFO/
