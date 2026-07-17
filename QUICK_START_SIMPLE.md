# HyoDo 3-Minute Quick Start

> A fast, inspectable setup path for HyoDo quality gates (model-agnostic).

HyoDo is a code-quality workflow kit for AI-assisted development. Start with the
CLI for review and safety checks. Optional slash-command adapters live in
`commands/` for Claude Code and compatible agent UIs.

**Model-agnostic** = independent of AI model / agent UI.  
**Not** language-agnostic: full `hyodo check` targets a **HyoDo package checkout**.

## 1. Install

### Fastest: PyPI

```bash
pip install -U 'hyodo==3.1.7'
hyodo --version
```

### Recommended for development: clone, inspect, then run

```bash
git clone https://github.com/lofibrainwav/HyoDo.git ~/.hyodo
cd ~/.hyodo

# Optional but recommended for first-time users
sed -n '1,220p' install_interactive.sh

./install_interactive.sh
```

### One-line install for trusted environments

```bash
curl -sSL https://raw.githubusercontent.com/lofibrainwav/HyoDo/main/install_interactive.sh | bash
```

### Editable install from clone

```bash
cd ~/.hyodo
pip install -e ".[dev]"
hyodo --version
```

## 2. Configure keys only if needed

```bash
cd ~/.hyodo
cp .env.minimal .env
# Edit only the provider keys for adapters you actually use
```

Do not commit `.env` files with real credentials. The core CLI gates do not
require a cloud model API key.

## 3. Run the quality loop (CLI first)

From a **HyoDo clone** (for full `check`):

```bash
cd ~/.hyodo
hyodo start
hyodo check
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --loyalty 0.9
hyodo safe
hyodo safe --strict   # CI-friendly: exit 1 on high-severity findings
```

From **any directory** (PyPI install):

```bash
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --loyalty 0.9
hyodo safe path/to/file_or_diff_context
# hyodo check outside a HyoDo checkout exits 2 (not a false green)
```

### Optional agent adapter

If your agent loads `commands/`:

```text
/start
/check
/score
/safe
```

---

## Core Commands

| Command | Purpose | Example |
|--------|---------|---------|
| `hyodo start` / `/start` | Onboarding guide | `hyodo start` |
| `hyodo check` / `/check` | HyoDo checkout release gates | `hyodo check` |
| `hyodo score` / `/score` | Review signal (not auto-approval) | `hyodo score` |
| `hyodo safe` / `/safe` | Safety early-warning scan | `hyodo safe` |
| `hyodo safe --strict` | Exit 1 on high findings | `hyodo safe --strict` |
| `/cost` | Cost estimate / routing signal | `/cost` |

### Exit contracts (Truth Patch, v3.1.7+)

| Command | Exit 0 | Exit 1 | Exit 2 |
|---------|--------|--------|--------|
| `check` | ≥1 gate executed and all PASS | any FAIL | missing path / zero gates executed |
| `safe` | always after print (early warning) | n/a | missing path / scan failure |
| `safe --strict` | no high findings | any high finding | missing path / scan failure |

---

## What is HYOGOOK V5?

HYOGOOK V5 is HyoDo's optional scoring model. It reviews code through six dimensions and uses a geometric mean component so weak areas remain visible instead of being hidden by stronger ones.

```text
F = (T + G + In + B + C) + ⁵√(T × G × In × B × C)
S = ⁵√(T × G × In × B × C)
```

Review-emphasis percentages in the full README are **not** F-score weights.

| F Score | S Score | Meaning | Suggested action |
|--------|--------|---------|------------------|
| F ≥ 54 | S ≥ 8 | Strong | Strong review signal — human approval still required |
| F ≥ 45 | S ≥ 7 | Good | Review recommended |
| F < 45 | - | Needs work | Fix before merge |

Scores support review. They do not replace human judgment, tests, or security checks.

---

## Troubleshooting

### I only want the CLI (any model vendor)

```bash
pip install -U 'hyodo==3.1.7'
hyodo --version
hyodo safe
hyodo score -t 0.9 -g 0.9 -b 0.9 -i 0.9 -c 0.9
```

### `hyodo check` says no gates executed

That is intentional outside a HyoDo checkout. Clone this repo (or pass its path)
to run release gates. Exit code **2** means “not a validation pass,” not success.

### Commands do not appear in my agent UI

Use the CLI path above first. Agent adapters depend on how your tool loads
project `commands/` or skills.

### I need a Claude-specific proof map

See [docs/ANTHROPIC_PROOF.md](docs/ANTHROPIC_PROOF.md). For all providers, see
[docs/PROVIDER_PROOF.md](docs/PROVIDER_PROOF.md).

---

## Next Steps

- [Full README](README.md)
- [Provider proof map](docs/PROVIDER_PROOF.md)
- [Security surface](docs/SECURITY_SURFACE.md)
- [Detailed guide](QUICK_START.md)
- [3-minute demo script](docs/DEMO_SCRIPT_3_MIN.md)
- [Contributing guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

---

**HyoDo helps make AI-assisted code easier to inspect before it is trusted.**
