# HyoDo Quick Start

Local AI agent guardrails for FDE and CI. Adopters first;
contributors second.

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

`safe` is an early-warning scanner, not a penetration test.

## 3. Bring-Your-Own-Gates (any project)

```bash
hyodo init                 # detect tools, write .hyodo/gates.toml
hyodo check                # runs the absorbed gates
hyodo dashboard --open     # view the evidence
```

Measured contracts (v4.2.0):

- `hyodo init` refuses an existing `.hyodo/gates.toml` (exit **1**)
  unless you pass `--force`.
- No tooling detected → honest starter template (commented examples),
  not a guessed linter.
- Starter with zero defined gates → `hyodo check` exit **2**
  (`This is not a validation pass`).
- With gates present, `check` runs **user** gates before any checkout
  preset.

### Six pillars, two kinds of evidence

| Pillar (Hanja/Korean/English) | Measured by |
| --- | --- |
| 眞 / 진 / Truth | Command gate (type checker) |
| 善 / 선 / Goodness | Command gate (test runner) |
| 美 / 미 / Beauty | Command gate (linter/formatter) |
| 仁 / 인 / Benevolence | Native AST scan |
| 孝 / 효 / Filial Piety | Native consent/data posture |
| 永 / 영 / Eternity | `.hyodo/history.jsonl` ledger |

Benevolence / Hyo / Eternity are never command gates — `init` cannot
absorb them, and no `gates.toml` entry can fake them green.

## 4. Optional review score

```bash
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 \
  --benevolence 0.9 --hyo 0.9
```

| Signal | Meaning |
| --- | --- |
| REVIEW_SIGNAL_STRONG (90+) | Strong; human review still required |
| REVIEW_SIGNAL_CAUTION (70–89) | Review before proceeding |
| REVIEW_SIGNAL_BLOCK (&lt;70) | Improve before merge |

Geometric mean is **fail-closed** (any pillar 0 → whole signal 0). See
[PHILOSOPHY.md](./PHILOSOPHY.md). All five pillars required unless
`--partial` (confidence-weak; no silent STRONG).

## 5. HyoDo contributors — dogfood `check`

Without `.hyodo/gates.toml`, `check` uses the HyoDo checkout preset:

```bash
./.venv/bin/hyodo check
```

Use the venv binary when `pipx`/global installs shadow PATH.

## Honesty contracts

| Command | Contract |
| --- | --- |
| `safe` | Default never blocks; `--strict` → 1 on high; bad path → 2 |
| `check` | Exit 0 if ≥1 gate ran and all passed; empty/bad toml → 2 |
| `init` | Existing config → 1 unless `--force` |
| `score` | Review signal only — never auto-approve |

## Next

- Product overview: [README.md](./README.md)
- Pillar map: [PHILOSOPHY.md](./PHILOSOPHY.md)
- Provider proof: [docs/PROVIDER_PROOF.md](./docs/PROVIDER_PROOF.md)
- Demo script: [docs/DEMO_SCRIPT_3_MIN.md](./docs/DEMO_SCRIPT_3_MIN.md)
