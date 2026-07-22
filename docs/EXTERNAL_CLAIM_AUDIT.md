# External Claim Audit (Measured)

**Date:** 2026-07-21
**Repo:** `lofibrainwav/HyoDo`
**Surface under audit:** public package only (`hyodo/`, root
`pyproject.toml`, `tests/`, `scripts/`, `.github/workflows/`)
**Method:** file/CLI/CI/GitHub Dependabot readback (no estimation)

This audit checks external market/strategy claims against the current
repository state. HyoDo publishes a single public surface — there is no
separate extended or advisory tree in this repo.

---

## Claim set under review

1. **Market need:** AI speed outruns human review; "speed without review
   creates risk"; developers need a fast, honest gate.
2. **Reality check:** claimed minimal dependencies, no required heavy
   infrastructure, and a bounded scope for `hyodo check`.
3. **Positioning:** two-track design — `safe` for any repository, `check`
   scoped to a HyoDo checkout only.

---

## 1) Market need — measured verdict

- AI generation speed creates a review bottleneck
  - Verdict: Supported (product thesis, not market survey)
  - Evidence: README: "HyoDo provides a small CLI and CI workflow for
    reviewing AI-assisted changes"
- Need for automated lint/test/safety gates
  - Verdict: Supported by product design
  - Evidence: `hyodo check` runs Pyright, Ruff, pytest, and an SBOM
    check (`hyodo/cli/main.py`)
- Gates should not replace human approval
  - Verdict: Supported by explicit disclaimer
  - Evidence: README: "without granting automatic approval"; HYOGOOK
    section: "Scores support review; they never replace tests,
    security checks, or human approval"

**Caveat:** this audit does not include external user interviews or
market-size data. It only verifies that HyoDo's stated problem matches
its implemented CLI behavior.

---

## 2) Reality check — measured verdict

### 2.1 Dependency weight

- Public runtime deps are minimal
  - Verdict: Confirmed
  - Evidence: `pyproject.toml` `dependencies = ["typer>=0.9.0",
    "rich>=13.0.0"]`
- No required container/database services
  - Verdict: Confirmed for the surface in this repo
  - Evidence: Neither README nor `docs/` reference a required
    Docker, Redis, or Postgres step for `pip install`, `hyodo check`,
    or `hyodo safe`
- sdist ships only the public surface
  - Verdict: Confirmed
  - Evidence: `pyproject.toml`
    `[tool.hatch.build.targets.sdist] only-include` lists `hyodo`,
    `tests`, `README.md`, `LICENSE`, `CHANGELOG.md`, `VERSION`,
    `pyproject.toml`, `SECURITY.md`, `CONTRIBUTING.md`,
    `CODE_OF_CONDUCT.md`

**Measured install path:**

```bash
pip install -U hyodo
hyodo --version
hyodo safe path/to/file_or_diff_context
```

**Measured checkout path (for `hyodo check` itself):**

```bash
git clone https://github.com/lofibrainwav/HyoDo.git
cd HyoDo
python -m pip install -e ".[dev]"
hyodo check
```

Neither path requires a container runtime or an external database in
this repository.

### 2.2 Scope claim — `check` vs `safe`

- `hyodo safe` works on any repository
  - Verdict: Supported by design and docs
  - Evidence: README: "`safe` — outward, any repository"
- `hyodo check` is scoped to a HyoDo checkout, not arbitrary
  projects
  - Verdict: Supported by design, docs, and code
  - Evidence: README: "`check` — reference, a HyoDo checkout only";
    `hyodo check` exit contract table (`0`/`1`/`2`) documents a
    bounded, self-referential gate
- A zero-gate run is never reported as success
  - Verdict: Supported
  - Evidence: README: "A zero-gate run is never reported as
    success"; `hyodo check` exit `2` = "path is missing or no
    applicable gate ran"

### 2.3 Optional review score (HYOGOOK V5)

- HYOGOOK is optional, not required for the practical CLI path
  - Verdict: Supported
  - Evidence: README: "The practical CLI works without this
    optional philosophy layer"
- HYOGOOK output is advisory, not an approval gate
  - Verdict: Supported
  - Evidence: README: "Scores support review; they never replace
    tests, security checks, or human approval"

### 2.4 Optional local MCP adapter

- MCP support is opt-in and leaves the core runtime dependency set unchanged
  - Verdict: Confirmed
  - Evidence: `pyproject.toml` defines `hyodo[mcp]`; the base dependency
    list contains only `typer` and `rich`
- The shipped MCP transports are explicit local stdio, loopback, and guarded
  private-network HTTP
  - Verdict: Confirmed
  - Evidence: `hyodo mcp stdio` starts `hyodo/mcp_server.py` with the MCP SDK
    `stdio` transport. `hyodo mcp serve --bind loopback` fixes HTTP to
    `127.0.0.1`; `--bind tailscale --bind-ip 100.x --token` validates the
    tailnet range and refuses a missing or blank token before listening.
- MCP tools wrap the existing CLI contracts for one locked host workspace
  - Verdict: Confirmed
  - Evidence: `hyodo/mcp_server.py` delegates `safe`, `check`, `event
    record`, and `policy check` through `hyodo.cli.main`; policy paths that
    escape the workspace return exit `2`
- Public listeners, unobserved second-device success, and automatic agent
  authority
  - Verdict: Not shipped and not claimed
  - Evidence: `0.0.0.0` and public interfaces are rejected. Tailscale serves
    the locked host workspace only; this repository has no observed
    second-device tool call receipt.

---

## 3) Positioning fit — measured state

External expectation: a fast, low-friction, honestly-scoped gate rather
than a broad or philosophy-first product.

Required attribute vs. current measured state:

- One-command outward gate
  - `hyodo safe` runs against any repository/diff, default exit
    `0`, `--strict` exits `1` on high-severity findings
- Bounded, non-misleading `check` scope
  - `hyodo check` is explicitly documented and coded as
    HyoDo-checkout-only, with a three-way exit contract
- Minimal runtime deps
  - `typer` + `rich` only, per `pyproject.toml`
- Philosophy layer optional
  - HYOGOOK documented as optional and non-blocking
- Release surface stated narrowly
  - README "Scope" table lists only `hyodo/` and `tests/` +
    `.github/workflows/` as the release surface

**Verdict:** the two-track (`safe` outward / `check` reference-only)
positioning matches what is implemented and documented in this repo. No
gap was found between the stated scope and the measured CLI behavior.

---

## 4) Security number context (related credibility)

Metric (2026-07-19), value, and source:

- Dependabot open alerts (live GitHub API)
  - Value: 1
  - Source: `gh api graphql`
    `vulnerabilityAlerts(states: OPEN) { totalCount }`
- Public runtime dependency count
  - Value: 2 (`typer`, `rich`)
  - Source: `pyproject.toml`
- Code scanning (CodeQL)
  - Value: not configured
  - Source: no workflow present in `.github/workflows/`

A live Dependabot readback is required before any "N alerts" figure is
cited elsewhere in the repo; this count is a point-in-time measurement
and will change.

---

## 5) Release-gate mechanics (related to "quality gate" claim)

- `hyodo check` runs real static/type/test gates, not a stub
  - Verdict: Supported
  - Evidence: `hyodo/cli/main.py` invokes Pyright, Ruff, pytest,
    and `run_sbom_check`, which shells out to
    `scripts/generate_sbom.py`
- Publishing uses Trusted Publishing (OIDC), not a long-lived
  token
  - Verdict: Supported
  - Evidence: `.github/workflows/publish.yml` header: "Publish
    HyoDo to PyPI via Trusted Publishing (OIDC) only. No
    long-lived API token."
- Version consistency is checked in CI
  - Verdict: Supported
  - Evidence: `.github/workflows/smoke.yml` runs
    `python scripts/release/check_version_sync.py`

---

## 6) Action implications (product)

Priority order implied by measurements:

1. Keep the outward path minimal: `pip install -U hyodo && hyodo safe`
   — **measured true today**.
2. Keep `hyodo check` explicitly scoped to a HyoDo checkout in both
   README and CLI exit contract — **measured true today**.
3. Keep HYOGOOK optional and non-blocking — **measured true today**.
4. Re-run the Dependabot readback before restating any alert count in
   product docs — counts drift and must not be hardcoded as constants.

---

## 7) Language policy (this repo)

- Public product language: **English only**, per `CLAUDE.md`.

---

## Source commands used

```bash
# deps and sdist scope
rg -n "dependencies|typer|rich|only-include" pyproject.toml

# CI/publish/smoke mechanics
rg -n "pip install|Trusted Publishing|check_version_sync" \
  .github/workflows/*.yml

# claims
rg -n "does not|guarantee|Scope|HYOGOOK" README.md

# CLI gate wiring
rg -n "run_sbom_check|Pyright|Ruff|pytest" hyodo/cli/main.py

# CLI behavior
hyodo check
hyodo safe

# Dependabot (live)
gh api graphql -f query='{repository(owner:"lofibrainwav",name:"HyoDo"){
  vulnerabilityAlerts(states: OPEN){ totalCount } } }'
```
