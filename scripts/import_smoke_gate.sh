#!/usr/bin/env bash
set -euo pipefail
poetry run python -c "from AFO import api_server; assert hasattr(api_server, 'app'); print('IMPORT_SMOKE_OK')"
