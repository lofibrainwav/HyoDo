# HyoDo Quick Start

Path for adopters first; HyoDo contributors second.

## 1. Install

```bash
pipx install hyodo
# or: pip install -U hyodo
hyodo --version
```

From source (contributors / dogfood):

```bash
git clone https://github.com/lofibrainwav/HyoDo.git
cd HyoDo
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## 2. Immediate value — `safe` (any repo)

```bash
cd your-project
hyodo safe                 # print findings, exit 0
hyodo safe --strict        # exit 1 on high-severity findings
hyodo safe --json          # CI-friendly JSON
```

### Minimal GitHub Actions

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install hyodo
- run: hyodo safe --strict --json
```

`safe` is an early-warning scanner (secrets, dangerous commands, production
impact) — not a penetration test.

## 3. Optional — your own gates (4.2+)

```bash
hyodo init                 # write .hyodo/gates.toml from existing tools
hyodo check                # run absorbed gates
hyodo dashboard --open     # evidence panel at 127.0.0.1:8768
```

Without `.hyodo/gates.toml`, `check` only runs the **HyoDo checkout preset**
(or exits with guidance / `UNSUPPORTED` outside that checkout). Use `init` for
arbitrary projects.

## 4. Optional review score

```bash
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 \
  --benevolence 0.9 --hyo 0.9
```

| Signal | Meaning |
| --- | --- |
| REVIEW_SIGNAL_STRONG (90+) | Strong; tests and human review still required |
| REVIEW_SIGNAL_CAUTION (70–89) | Review before proceeding |
| REVIEW_SIGNAL_BLOCK (&lt;70) | Improve before merge |

Geometric mean is **fail-closed** (any pillar 0 → whole signal 0). See
[PHILOSOPHY.md](./PHILOSOPHY.md). All five pillars are required unless
`--partial` (confidence-weak marker; no silent STRONG inflation).

## 5. HyoDo contributors — dogfood `check`

From a HyoDo checkout with dev extras:

```bash
./.venv/bin/hyodo check
```

Use the venv binary when `pipx`/global installs shadow PATH.

## Honesty contracts

| Command | Contract |
| --- | --- |
| `safe` | Default never blocks; `--strict` → exit 1 on high; bad path → exit 2 |
| `check` | Exit 0 only if ≥1 gate **executed** and all executed gates passed; malformed `gates.toml` → exit 2; zero gates → exit 2 (not a pass) |
| `score` | Review signal only — never auto-approve |

## Next

- Product overview: [README.md](./README.md)
- Pillar ↔ engineering map: [PHILOSOPHY.md](./PHILOSOPHY.md)
- Provider proof: [docs/PROVIDER_PROOF.md](./docs/PROVIDER_PROOF.md)
- Demo script: [docs/DEMO_SCRIPT_3_MIN.md](./docs/DEMO_SCRIPT_3_MIN.md)
