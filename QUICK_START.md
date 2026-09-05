# HyoDo Quick Start

Get useful local guardrails in an existing repository without replacing its
tests, linters, or CI.

## 1. Install

```bash
pipx install hyodo
# or: pip install -U hyodo
hyodo --version
```

Python 3.10+ is supported.

## 2. Scan any repository

```bash
cd your-project
hyodo safe                 # report findings
hyodo safe --strict        # exit 1 on high-severity findings
hyodo safe --json          # machine-readable output
```

`safe` is an early-warning scanner, not a full security audit.

### Minimal GitHub Actions

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install hyodo
- run: hyodo safe --strict --json
```

## 3. Reuse the checks you already have

```bash
hyodo init
hyodo check
```

`init` detects supported project tooling and writes `.hyodo/gates.toml`.
It can absorb pytest, Ruff, mypy, Pyright, npm scripts, Go, Cargo, and
Makefile targets.

Important contracts:

- Existing `.hyodo/gates.toml` → `init` exits **1** unless `--force` is used.
- No supported tooling detected → a commented starter is written, not a guess.
- Zero executable gates → `check` exits **2**. This is not a validation pass.
- A failing gate → `check` exits **1**.
- At least one executed gate and all pass → `check` exits **0**.

## 4. Optional local evidence panel

```bash
hyodo dashboard --open
```

The dashboard binds to loopback and displays measured evidence. Missing sources
remain unmeasured rather than being converted into a healthy score.

## 5. Optional agent evidence and policy

```bash
hyodo event validate --file step.json
hyodo event record --file step.json --root . --policy .hyodo/policy.toml
hyodo policy check --file step.json --config .hyodo/policy.toml
hyodo schema check --schema agent.schema.json --payload step.json --json
```

Event storage is digest-only by default. A DENY result is recorded, but the
caller is responsible for stopping the agent.

## 6. Optional MCP adapter

Install the MCP extra:

```bash
pip install 'hyodo[mcp]'
```

Local stdio:

```bash
hyodo mcp stdio --root .
```

Private Tailscale connector:

```bash
hyodo mcp serve --bind tailscale --bind-ip 100.99.88.77 \
  --token "$HYODO_MCP_TOKEN" --root .
```

Useful MCP operations:

```bash
hyodo mcp doctor
hyodo mcp access-log --root .
hyodo mcp rules list --root .
```

The adapter reuses HyoDo's CLI contracts. It does not create a separate policy
engine or expose a public listener.

## 7. Optional review signal

```bash
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 \
  --benevolence 0.9 --hyo 0.9
```

HYOGOOK V5 is a review aid only. It never grants automatic approval, and
unmeasured pillars do not silently become green.

## Command exit summary

| Command | Contract |
| --- | --- |
| `safe` | `0` report complete · `1` strict high finding · `2` bad path |
| `init` | `0` config written · `1` existing config without `--force` |
| `check` | `0` executed gates passed · `1` failed · `2` none/malformed |
| `event` / `policy` | `0` valid/ALLOW · `1` invalid/DENY · `2` unobserved |
| `schema check` | `0` valid · `1` validation error · `2` unobserved input |

## Contributors

```bash
git clone https://github.com/lofibrainwav/HyoDo.git
cd HyoDo
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
bash scripts/verify-public.sh
```

## Next

- Product overview: [`README.md`](./README.md)
- Security model: [`SECURITY.md`](./SECURITY.md)
- Evidence model: [`PHILOSOPHY.md`](./PHILOSOPHY.md)
- MCP design: [`docs/HYODO_MCP_CONNECTOR_DESIGN.md`](./docs/HYODO_MCP_CONNECTOR_DESIGN.md)
- Release history: [`CHANGELOG.md`](./CHANGELOG.md)
