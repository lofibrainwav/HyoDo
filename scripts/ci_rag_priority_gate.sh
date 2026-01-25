#!/usr/bin/env bash
set -euo pipefail

python -c "import afo; import afo.rag_flag; import afo.rag_shadow; print('imports: OK')"
pytest -q packages/afo-core/tests/test_rag_rollout_priority.py -q
