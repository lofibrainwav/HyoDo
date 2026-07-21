# HyoDo

**Honest quality gates for AI-assisted Python work.**

[![CI](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml/badge.svg)](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hyodo)](https://pypi.org/project/hyodo/)
[![Python](https://img.shields.io/pypi/pyversions/hyodo)](https://pypi.org/project/hyodo/)
[![License](https://img.shields.io/github/license/lofibrainwav/HyoDo)](./LICENSE)

Scan AI-assisted changes for secrets, dangerous commands, and production-impact
risks — then, when you are ready, absorb *your* project's own tests and linters
as quality gates. Scores and philosophy labels are **review signals only**; they
never grant automatic approval.

## Start here (any repository)

Value you can feel in under a minute — no HyoDo checkout required:

```bash
pipx install hyodo              # isolated CLI (or: pip install -U hyodo)
cd your-project
hyodo safe                      # early-warning scan (secrets, dangerous cmds, prod impact)
hyodo safe --strict             # exit 1 when a high-severity finding exists
hyodo safe --json               # machine-readable findings for CI
```

### CI snippet (GitHub Actions)

```yaml
- run: pipx install hyodo
- run: hyodo safe --strict --json
```

`hyodo safe` is an early-warning scanner, not a full security audit. It runs on
any repository with no setup.

### Bring your own gates (optional, 4.2+)

When you want *your* typechecker / linter / test runner as first-class gates:

```bash
hyodo init                 # detect tooling → write .hyodo/gates.toml
hyodo check                # run absorbed gates (Bring-Your-Own-Gates)
hyodo dashboard --open     # local evidence panel
```

`hyodo init` reads existing project signals (`pyproject.toml` pytest/ruff/mypy/
pyright, npm test/lint, `tsconfig.json`, `go.mod`, `Cargo.toml`, Makefile
`test:`/`lint:`) and writes `.hyodo/gates.toml`. HyoDo does not reinvent those
tools — it runs the ones you already trust.

## Six pillars — philosophy kept, engineering mapped

Branding stays. Every label always ships with its technical meaning so you never
have to translate mid-incident:

| Pillar (Hanja / Korean / English) | Technical meaning | How it is measured |
| --- | --- | --- |
| 眞 / 진 / **Truth** | Type / static correctness | **Command gate** — Pyright, mypy, `tsc --noEmit`, `go vet`, `cargo check`, … (yours via `init`, or HyoDo preset) |
| 善 / 선 / **Goodness** | Tests + safety stability | **Command gate** — pytest, `npm test`, `go test`, `cargo test`, … plus `hyodo safe` findings |
| 美 / 미 / **Beauty** | Lint / format / maintainability | **Command gate** — Ruff, ESLint, formatters, … |
| 仁 / 인 / **Benevolence** | Structural integrity of public surface | **Native AST scan** — public docstrings, CLI help coverage, message-less `raise` |
| 孝 / 효 / **Filial Piety (Hyo)** | Consent + data-protection posture | **Native AST scan** — mutating flags stay opt-in, outbound network import sites, non-loopback bind literals |
| 永 / 영 / **Eternity (Yeong)** | Continuity of honest measurement | **Local ledger** — append-only `.hyodo/history.jsonl`, consecutive all-PASS on *executed* gates |

Truth / Goodness / Beauty come from commands you (or `hyodo init`) absorb.
Benevolence / Hyo / Yeong are **never** command gates — HyoDo measures them from
the checkout so a fake-green shell script cannot game them. Unavailable sources
show `Not measured` instead of inventing a score.

### Optional review score (fail-closed math)

```bash
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 \
  --benevolence 0.9 --hyo 0.9
```

HYOGOOK F-score (philosophy **V6**; formula lineage V5) combines the five input
pillars with a **geometric mean**. That is not literary “harmony” — it is a
**fail-closed gate**: if any pillar is 0, the whole signal collapses to 0
(arithmetic mean would hide a zero security axis behind a high average).

- All five pillars must be provided unless you pass `--partial` (marks
  `SIGNAL_CONFIDENCE_WEAK`; does not invent a STRONG band).
- Scores support review; they never replace tests, `safe`, or human approval.

Full map: [PHILOSOPHY.md](./PHILOSOPHY.md).

## Local instrument panel

Watch stability and pillar evidence update on your machine:

```bash
hyodo dashboard --open
# → http://127.0.0.1:8768
```

```text
┌─ HyoDo evidence ──────────────────────────────────────┐
│  眞 Truth     PASS / FAIL / Not measured              │
│  善 Goodness  PASS / FAIL / Not measured              │
│  美 Beauty    PASS / FAIL / Not measured              │
│  仁 In        AST structural integrity …              │
│  孝 Hyo       consent / outbound / bind posture …     │
│  永 Yeong     history streak (executed gates only)    │
│  [Measure again now]   raw JSON → /api/evidence       │
└───────────────────────────────────────────────────────┘
```

(Replace this ASCII stand-in with a real screenshot when you record one —
`docs/` is a good home.)

The panel **never** invents a composite score. With `.hyodo/gates.toml`, gate
rows use your absorbed gate names; otherwise the HyoDo checkout preset labels
apply. In / Hyo / Yeong always come from native collectors.

### How it works / security (details)

- **Loopback only** — the server binds to `127.0.0.1` so local analysis is not
  exposed on the LAN.
- **Poll, not websocket** — the page hits `/api/evidence` every 15s and reloads
  only when the snapshot changes (keeps the CLI dependency surface small).
- **`--interval N`** — background re-measure every N seconds; default snapshot
  is fixed at server start.
- **Measure again now** — token-protected, no path/command injection; may take
  minutes while gates run; last good snapshot is kept on failure.
- **Change-safety card** — scans the current Git diff scope; no diff →
  `Not measured` (never inflated into a whole-repo risk claim).
- Optional `--allow-origin` allowlist for local API consumers (explicit only).

## Install

Python 3.10 or newer.

```bash
pip install -U hyodo
# or: pipx install hyodo
hyodo --version
```

See [Quick Start](./QUICK_START.md) for the full first-run path.

## Commands

| Command | Purpose |
| --- | --- |
| `hyodo start` | Onboarding guidance |
| `hyodo safe [PATH]` | Safety findings (non-blocking) |
| `hyodo safe --strict [PATH]` | Exit 1 on high-severity findings |
| `hyodo safe --json [PATH]` | JSON findings for CI |
| `hyodo init [PATH]` | Detect tools → write `.hyodo/gates.toml` (BYOG, 4.2+) |
| `hyodo check [PATH]` | Run absorbed gates, else HyoDo checkout preset |
| `hyodo check --general` | Bounded multi-language syntax sample gates (opt-in) |
| `hyodo score ...` | Optional review signal (fail-closed geometric mean) |
| `hyodo dashboard` | Local evidence-only instrument panel |
| `hyodo trinity "CHANGE"` | Structured review checklist |

### `hyodo safe` exit contract

| Exit | Meaning |
| ---: | --- |
| `0` | Findings printed (default mode never blocks) |
| `1` | `--strict` and at least one high-severity finding |
| `2` | Path missing or unreadable |

### `hyodo check` exit contract

| Exit | Meaning |
| ---: | --- |
| `0` | At least one gate ran and every **executed** gate passed |
| `1` | An executed gate failed |
| `2` | Path missing, malformed `.hyodo/gates.toml`, or no applicable gate ran |

Resolution order: `--general` (explicit) → `.hyodo/gates.toml` (BYOG) → HyoDo
checkout preset (Pyright / Ruff / pytest / optional SBOM) → guidance toward
`hyodo init`. Zero executed gates is never success. Malformed `gates.toml`
exits `2` with the parse error (never silent skip).

## Scope

| Surface | Status |
| --- | --- |
| `hyodo/` Python package and CLI | Public release surface |
| `tests/` and `.github/workflows/` | Release verification |

**Model-agnostic** means the core CLI does not require a specific AI provider or
agent UI. It does **not** mean every language is fully supported end-to-end.
`--general` is a bounded syntax sample (per-language file caps, vendor dirs
pruned), not a claim of universal multi-stack coverage.

## For contributors (HyoDo dogfood)

HyoDo runs its **own** release preset on this repository so the tool eats its
cooking (honesty contract). That path is for people contributing to HyoDo — not
the first thing a new adopter should read.

```bash
git clone https://github.com/lofibrainwav/HyoDo.git
cd HyoDo
python -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]"
./.venv/bin/hyodo check          # Pyright + Ruff + pytest + optional SBOM
```

Prefer `./.venv/bin/hyodo` when a global/`pipx` install shadows the checkout.
Day-to-day contribution workflow: [CONTRIBUTING.md](./CONTRIBUTING.md).

## Documentation

- [Quick Start](./QUICK_START.md)
- [Philosophy (pillar ↔ engineering map)](./PHILOSOPHY.md)
- [Documentation index](./docs/README.md)
- [Provider support evidence](./docs/PROVIDER_PROOF.md)
- [Security boundaries](./docs/SECURITY_SURFACE.md)
- [External claim audit](./docs/EXTERNAL_CLAIM_AUDIT.md)
- [Changelog](./CHANGELOG.md)
- [Roadmap](./ROADMAP.md)

## Contributing and security

See [CONTRIBUTING.md](./CONTRIBUTING.md) before opening a pull request. Report
security issues through the process in [SECURITY.md](./SECURITY.md).

## License

HyoDo is available under the [MIT License](./LICENSE).
