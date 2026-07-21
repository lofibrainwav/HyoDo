# HyoDo roadmap

This roadmap describes direction, not a delivery promise. Work is accepted only
when implementation, tests, documentation, and release evidence agree.

## Current focus

### Reliable public CLI

- Keep `check`, `safe`, and `score` exit contracts stable.
- Preserve Python 3.10, 3.11, and 3.12 CI coverage.
- Prevent zero-gate and unreadable-path false positives.
- Keep the wheel and source distribution limited to the public package.

### Clear public documentation

- Maintain one short README and one Quick Start.
- Keep provider, security, and release claims tied to inspectable evidence.
- Keep the public surface limited to the `hyodo/` package and its tests.

### Secure releases

- Publish through PyPI Trusted Publishing.
- Verify tag, version, provenance, package contents, and cold installation.
- Keep long-lived publishing tokens out of the normal release path.

## Next candidates

These items require an issue, an explicit scope, and acceptance tests before
implementation:

- Generalize `hyodo check` beyond HyoDo checkouts without weakening its exit
  contract.
- Improve safety rule precision and document known false positives.
- Add machine-readable check results for CI consumers.
- Measure routing guidance before making any cost-savings claim.
- **FDE Phase 2** — strict schema validation gate for agent payloads
  (`hyodo schema check`).
- **FDE Phase 3** — local golden-dataset eval harness (`hyodo eval`).
- **FDE Phase 4** — executive sign-off HTML/MD report from ledger evidence.

## In progress / landed (Unreleased)

- **FDE Phase 1 Evidence Spine** — agent event ledger + policy gate + adapter
  contract (`hyodo event` / `hyodo policy`). Digest-default; not a full
  tool-call interceptor. Sample MCP/runtime adapters remain optional follow-ups.

## Later exploration

- Additional language and repository adapters.
- A plugin API for custom gates.
- Optional browser or service integrations outside the core CLI.
- Optional hash-chain / at-rest encryption for agent-events (needs key story).

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
