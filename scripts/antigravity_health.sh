#!/usr/bin/env bash
set -euo pipefail
set -a
source .env.antigravity
set +a
python system_health_check.py
