# HyoDo Quick Start

## Install

### PyPI

```bash
pip install -U 'hyodo==4.0.0'
```

### From source

```bash
git clone https://github.com/lofibrainwav/HyoDo.git
cd HyoDo
pip install -e ".[dev]"
```

## Core CLI (model-agnostic)

```bash
hyodo --version
hyodo check          # HyoDo checkout only
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 \
  --benevolence 0.9 --hyo 0.9
hyodo safe
hyodo safe --strict  # exit 1 on high-severity findings
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
