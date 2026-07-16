# HyoDo Quick Start

> Prefer the simple path: **[QUICK_START_SIMPLE.md](./QUICK_START_SIMPLE.md)**

## Install

```bash
git clone https://github.com/lofibrainwav/HyoDo.git
cd HyoDo
pip install -e ".[dev]"
```

## Core CLI (model-agnostic)

```bash
hyodo --version
hyodo check
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --loyalty 0.9
hyodo safe
```

## Score meaning

Scores are **review signals only**. They never replace human approval.

| Signal | Meaning |
|--------|---------|
| REVIEW_SIGNAL_STRONG (90+) | Strong signal — still require tests, security, human gate |
| REVIEW_SIGNAL_CAUTION (70-89) | Review before proceed |
| REVIEW_SIGNAL_BLOCK (&lt;70) | Improve before merge |

## Next

- Full onboarding: [QUICK_START_SIMPLE.md](./QUICK_START_SIMPLE.md)
- Multi-provider proof: [docs/PROVIDER_PROOF.md](./docs/PROVIDER_PROOF.md)
- Demo script (record last): [docs/DEMO_SCRIPT_3_MIN.md](./docs/DEMO_SCRIPT_3_MIN.md)
