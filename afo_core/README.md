# AFO Core

AFO Core is the experimental FastAPI and agent-runtime tree bundled with the
HyoDo repository. It is maintained separately from the published `hyodo`
package and is not included in HyoDo wheels or source distributions.

## Requirements

- Python 3.12 or 3.13
- External services such as Redis only for the features that use them

## Install

From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e "./afo_core[agents,browser]"
```

The `agents` and `browser` extras are required by the full API server import
graph. Playwright browser binaries are needed only for browser-backed flows.
Install them separately when required:

```bash
playwright install chromium
```

Machine-learning dependencies are intentionally separate because they are
large and platform-sensitive:

```bash
pip install -e "./afo_core[ml]"
```

## Run

```bash
PYTHONPATH=afo_core uvicorn AFO.api_server:app --host 127.0.0.1 --port 8010
```

Do not expose the development server publicly without configuring secrets,
authentication, and backing services.

## Verify

```bash
ruff check afo_core/
ruff format --check afo_core/
python -m compileall -q afo_core
PYTHONPATH=afo_core pytest -q \
  afo_core/tests/test_librarian_agent.py \
  afo_core/tests/test_chancellor_v3_routers.py \
  afo_core/tests/test_v3_routing_verification.py \
  afo_core/tests/api/chancellor_v2/test_orchestrator.py \
  afo_core/tests/api/test_api_pillars.py
```

Architecture notes under `afo_core/docs/` describe experiments and historical
designs. Treat executable code, `pyproject.toml`, and current CI as the runtime
contract.
