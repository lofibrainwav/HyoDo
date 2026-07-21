# HyoDo Quick Start

## Install

### PyPI

```bash
pip install -U 'hyodo==4.0.1'
```

Or install an isolated command-line version:

```bash
pipx install hyodo
```

### From source

```bash
git clone https://github.com/lofibrainwav/HyoDo.git
cd HyoDo
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Core CLI (any directory)

```bash
hyodo --version
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 \
  --benevolence 0.9 --hyo 0.9
hyodo safe
hyodo safe --strict  # exit 1 on high-severity findings
hyodo dashboard --open  # opens the local dashboard at 127.0.0.1:8768
```

## HyoDo checkout gates

After the **From source** setup above, run the HyoDo release gates from the
checkout:

```bash
hyodo check
```

If a separate installation (such as `pipx`) appears earlier on your `PATH`, use
the checkout command explicitly:

```bash
./.venv/bin/hyodo check
```

## Score meaning

Scores are **review signals only**. They never replace human approval.

| Signal | Meaning |
| --- | --- |
| REVIEW_SIGNAL_STRONG (90+) | Strong; tests and human review still required |
| REVIEW_SIGNAL_CAUTION (70-89) | Review before proceeding |
| REVIEW_SIGNAL_BLOCK (&lt;70) | Improve before merge |

## Check / safe honesty (v3.1.8+)

- `hyodo check` is a **HyoDo package checkout** gate, not a universal project scanner.
- Zero executed gates → exit **2** (`This is not a validation pass`).
- Prefer `is_strong_review_signal()` over deprecated `should_auto_approve()`.

## Next

- Product overview: [README.md](./README.md)
- Multi-provider proof: [docs/PROVIDER_PROOF.md](./docs/PROVIDER_PROOF.md)
- Demo script (record last): [docs/DEMO_SCRIPT_3_MIN.md](./docs/DEMO_SCRIPT_3_MIN.md)
