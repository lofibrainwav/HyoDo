# Changelog

All notable changes to HyoDo will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `.pre-commit-hooks.yaml` — `hyodo-check` and `hyodo-safe-strict` hooks so
  `hyodo check` runs under the pre-commit framework from any consuming repo.
- `hyodo report --format sarif` — writes a SARIF v2.1.0 log to
  `.hyodo/reports/hyodo-report.sarif`. Measured policy DENYs and unreadable
  ledgers become `error` results. SARIF is a visibility surface; `hyodo check`
  remains the fail-closed gate for missing or unmeasured quality evidence.
- `.github/actions/hyodo` — composite GitHub Action that installs HyoDo from
  the same pinned repository ref, runs `hyodo check`, and can optionally upload
  the matching SARIF report to the GitHub Security tab.

## [4.11.0] - 2026-09-03

Feature release: MCP access ledger and agent-rules opt-in (Issue #95 M4 complete).

### Added

- `hyodo mcp access-log` — audit trail of MCP tool invocations. Every tool call
  is recorded to `.hyodo/mcp-access.jsonl` (append-only, best-effort, never
  blocks the call). Supports `--root`, `--limit`, and `--json`. Fail-closed on
  missing `mcp` extra (exit 2, install hint).
- `hyodo mcp rules list` — show active agent rules from
  `.hyodo/agent-rules.toml` (or built-in defaults when absent). Supports
  `--root` and `--json`.
- `hyodo mcp rules init` — write default agent rules to
  `.hyodo/agent-rules.toml` (idempotent, preserves an existing file).
- `hyodo_agent_rules` MCP tool — returns current agent rules over the MCP
  protocol.

## [4.10.0] - 2026-09-03

Feature release: new `hyodo mcp doctor` diagnostic command.

### Added

- `hyodo mcp doctor` — read-only local MCP setup diagnostic. Reports SDK
  availability and major version, workspace root validity, port availability
  (and dashboard-reserved 8768), and Tailscale connectivity. Supports `--json`
  for machine-readable output. Always exits 0; diagnoses, never blocks.
  Fail-closed on missing `mcp` extra (exit 2, install hint).

## [4.9.0] - 2026-09-03

Compatibility release: the optional MCP adapter now runs on both MCP Python
SDK majors, and release tooling stops failing on valid distributions.

### Fixed

- The MCP adapter now runs on both MCP Python SDK majors. The SDK's v2.0.0
  removed `mcp.server.fastmcp` (renamed `FastMCP` to `MCPServer` in
  `mcp.server.mcpserver`) and moved host/port/`json_response`/
  `streamable_http_path` from the constructor into `streamable_http_app()`,
  which made the dependabot range-widening PR fail CI for a month. A new
  `hyodo._mcp_compat` resolves the installed major once per process; the CLI's
  "MCP support is not installed" probe works on both (and still fails closed
  with exit 2 on a core install without the extra); CI now exercises the v1
  line on a pinned job so widening the extra to `mcp>=1.27,<3` cannot silently
  drop it.
- `scripts/verify-public.sh` and the smoke/publish workflows now upgrade
  `twine` to `>=7` before `twine check`. twine 6.x cannot parse the
  Metadata-Version 2.5 sdists current hatchling emits and failed the local
  full verify on a valid distribution.

- Dashboard evidence now names why a safety risk score is absent. `risk_score`
  is still omitted when there is nothing to scan (an empty change set must not
  read as "score 0, therefore safe"), but a single `null` could not tell
  "the scan never ran" apart from "the scan ran and found nothing to measure".
  A consumer read it the wrong way and rendered a scan that had actually run as
  unobserved. `safety.risk_score_state` now carries `measured` or
  `no_scan_target` alongside it. Additive field — existing consumers are
  unaffected.

## [4.8.2] - 2026-09-02

Security release: MCP network-bind hardening and public-surface validation.

### Changed

- `hyodo mcp serve` now accepts `--bind loopback|tailscale`; direct public
  `0.0.0.0` listeners are rejected.
- Tailscale HTTP mode requires an explicit token and records only hashed access
  metadata.

## [4.8.1] - 2026-09-02

Patch release: MCP adapter compatibility and CLI polish.

## [4.8.0] - 2026-09-02

Feature release: optional local MCP adapter and dashboard surfaces.

## [4.4.0] - 2026-07-20

Feature release: local FDE evidence and report surfaces.

## [4.3.0] - 2026-07-20

Feature release: eval and policy refinements.

## [4.2.0] - 2026-07-20

Feature release: schema and agent event tooling.

## [4.0.1] - 2026-07-20

Truth patch: score honesty and required-pillar handling.

## [4.0.0] - 2026-07-20

Major release: philosophy V6 cleanup and removal of automatic-approval semantics.

## [3.3.0] - 2026-07-20

Feature release: Hyo pillar restored; loyalty compatibility alias deprecated.

## [3.2.1] - 2026-07-20

Patch release: Pyright interpreter pin for clean environment checks.

## [3.2.0] - 2026-07-19

Feature release: outward JSON safety reporting and check honesty hardening.

## [3.1.8] - 2026-07-16

Supply-chain release: PyPI Trusted Publishing and provenance verification.

## [3.1.7] - 2026-07-16

Truth patch: format gate, safe scan contracts, and path-stable tests.

## [3.1.6] - 2026-07-16

Truth patch: false-green quality gates removed.

## [3.1.5] - 2026-07-16

Pre-demo surface polish.

## [3.1.4] - 2026-07-16

GitHub release publication; PyPI was intentionally separate at the time.

## [3.1.3] - 2026-07-16

Patch release.

## [3.1.2] - 2026-07-16

Patch release.

## [3.1.1] - 2026-07-16

Patch release.

## [3.1.0] - 2026-05

Initial tagged public release series.
