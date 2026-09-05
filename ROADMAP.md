# HyoDo roadmap

This roadmap describes direction, not a delivery promise. Work is accepted only
when implementation, tests, documentation, and release evidence agree.

## Current public baseline

HyoDo 4.11.0 is the current measured baseline.

Landed and released:

- `hyodo safe` for early-warning scans with strict and JSON modes.
- Bring-Your-Own-Gates with `hyodo init` and `hyodo check`.
- FDE evidence spine with event validation, append-only audit records, and
  local policy checks.
- Schema validation, local eval runs, and deterministic evidence reports.
- MCP M1-M4: stdio, loopback/private Tailscale serve, `mcp doctor`, access
  ledger, and agent-rules opt-in.
- Python 3.10-3.14 CI coverage plus a pinned MCP SDK v1 compatibility lane.
- PyPI Trusted Publishing with post-publish provenance and install readback.

The public package remains local-first and model-agnostic. Missing or unreadable
evidence is not converted into a pass.

## Current focus

### External adoption

- Keep the README and Quick Start centered on adopter tasks, not internal terms.
- Preserve clear install, exit-code, support, and security boundaries.
- Keep PyPI metadata aligned with the GitHub product description.

### Release honesty

- Keep the protected final release check non-skippable when upstream jobs fail.
- Preserve Python and MCP compatibility coverage as release evidence.
- Keep documentation claims tied to measured CI and published artifacts.

### Evidence integrity

- Keep policy decisions separate from caller assertions.
- Preserve fail-closed handling for unreadable ledgers and invalid inputs.
- Keep default agent-event storage digest-only unless an operator explicitly
  permits more.

## Next candidates

These items require an issue, explicit scope, and acceptance tests before
implementation:

- Add machine-readable `hyodo check` results for CI consumers.
- Improve `safe` rule precision and document known false positives.
- Add an optional measured second-device MCP receipt without making it a
  requirement for local-client use.
- Evaluate an index for large event ledgers instead of full-ledger scans.
- Decide whether the advisory public SBOM should become a release blocker.
- Add stronger release-signing guidance for annotated Git tags.
- Measure any routing or cost guidance before making savings claims.

## Landed milestones

- **v4.4.0** — FDE Phase 1 evidence spine: agent events + policy gate.
- **v4.8.x** — security and observability honesty hardening.
- **v4.9.0** — MCP SDK v1/v2 dual-major compatibility.
- **v4.10.0** — `hyodo mcp doctor`.
- **v4.11.0** — MCP access ledger + agent-rules opt-in; M4 complete.

## Later exploration

- Additional language and repository adapters.
- A plugin API for custom gates.
- Optional browser or service integrations outside the core CLI.
- Optional hash-chain or at-rest encryption for agent events with a clear key
  management story.
- Exportable audit packs beyond the current local HTML/Markdown report.

Exploration does not imply support or a release date. The public package should
remain useful without optional services, model providers, or agent interfaces.

## Proposing roadmap work

Open an [issue](https://github.com/lofibrainwav/HyoDo/issues) describing:

1. the user problem;
2. why existing commands do not solve it;
3. the smallest verifiable change;
4. compatibility and security risks;
5. measurable acceptance criteria.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the development workflow.
