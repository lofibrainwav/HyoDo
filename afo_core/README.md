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
bash afo_core/scripts/dev_env.sh
source afo_core/.venv/bin/activate
```

The script is the single source of truth for the install contract — CI's
`afo-core-contract` job runs the same script with `--system`. It pins
Python to the supported `>=3.12,<3.14` range, creates an isolated
`afo_core/.venv` (which also shields test collection from pytest plugins
installed elsewhere on the machine), and installs
`-e "./afo_core[agents,browser]"`.

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

## Platform support boundary

On macOS, AFO is a CPU-only internal legacy tree. Its supported role is
development, inspection, and non-QLoRA legacy workflows; it is not a GPU
training surface. The QLoRA trainer requires a Linux host with an NVIDIA CUDA
GPU and stops before model loading on unsupported hosts. This repository does
not provide Docker or Kubernetes GPU setup for that legacy path.

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
