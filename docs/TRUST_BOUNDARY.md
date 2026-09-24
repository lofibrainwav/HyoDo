# Trust boundary contract (4.21.7)

This is the single source for what HyoDo trusts when it verifies a checkout.
Every trust-bearing code path follows it; a change to it is a contract change
and is reviewed on its own, before any implementation that depends on it.

## Subject

The HyoDo 4.21.x trust and evidence boundary: BYOG gate execution, policy
trust, MCP bridge pairing, scan exceptions, `hyodo safe` and `hyodo check`
verdicts, and the ledgers behind continuity receipts and evidence reports.

## Trusted

- Operator-owned state in per-user storage outside every checkout
  (`~/.hyodo/state/`, or `$HYODO_STATE_HOME`), bound to the resolved
  workspace path.
- Evidence HyoDo observes at run time: files it actually scanned, gates it
  actually ran, and ledger bytes it appended itself (anchored in user state).
- Exact artifact provenance: the wheel under test is the wheel that ships.

## Untrusted

- Approval supplied by the checkout (`.hyodo/gates-trust.json`).
- Authority supplied by the checkout (`.hyodo/policy-trust.json`).
- Authentication supplied by the checkout (`.hyodo/pairing.json`).
- Exceptions supplied by the checkout (`.hyodo/scan-exceptions.toml`) until
  an operator approves that exact content.
- Historical evidence supplied by the checkout (`.hyodo/agent-events.jsonl`,
  `.hyodo/mcp-access.jsonl`) that HyoDo did not append on this machine.
- A caller's assertion that no independent observation backs.

## Invariant

A checkout may propose policy and configuration. It can never supply its own
authority. A file inside the checkout with an authority-shaped name is
reported as seen and ignored; it is never deleted and never honored.

Observation is reported as observed:

| Observed | Is not |
| --- | --- |
| 0 files scanned | `PASS` |
| sampled gates | full project coverage (`project_coverage: SAMPLED`, `complete: false`) |
| a skipped gate | `PASS` |
| partial coverage | complete |
| a ledger that parses | a ledger written here (`origin: UNVERIFIED`) |

## Authority

An evidence result is not execution, merge, publish, or deployment authority.
The host and the human operator keep that authority. Environment
pre-approvals (`HYODO_GATES_TRUST_ALL`, `HYODO_POLICY_TRUST_ALL`,
`HYODO_SCAN_EXCEPTIONS_DIGEST`) are an operator's decision expressed in a job
definition; use them only where changes to `.hyodo/` already require human
review before they run.

## Verification

- `tests/test_hostile_clone.py`: a repository that ships every untrusted item
  above, cloned to a fresh path and attacked through the installed CLI.
- `tests/test_security_matrix.py`: stale state, upgrading with legacy files,
  and the interactive approval paths.
- `scripts/release/hostile_clone_gauntlet.sh`: runs the gauntlet against the
  built wheel; required in CI (`Goodness Gate - Safety`) and in `publish.yml`
  before upload. A skipped or short run blocks.

## Upgrading to 4.21.7

- **Approvals are asked for once more.** Gate approvals, policy trust grants,
  and pairings recorded inside `.hyodo/` by earlier versions are not read.
  Run `hyodo check` in a terminal to approve the gate set again, re-run
  `hyodo policy trust grant`, and re-pair with `hyodo mcp pair`. The old files
  are left in place and reported as ignored; delete them when convenient.
- **Scan exceptions need approval.** Run `hyodo safe --approve-exceptions`
  once per checkout, and again after any edit to the file. In CI, pin the
  reviewed digest with `HYODO_SCAN_EXCEPTIONS_DIGEST`.
- **CI that relied on a committed receipt.** A job that ran BYOG gates because
  `.hyodo/gates-trust.json` was committed now reports `SKIP`. Set
  `HYODO_GATES_TRUST_ALL=1` on that job only if `.hyodo/gates.toml` changes
  require review before they reach it.
- **`hyodo safe` in CI needs a path.** On a clean checkout, `hyodo safe` with
  no path has nothing to scan and reports `UNOBSERVED` (exit 2 with
  `--strict`). Use `hyodo safe . --strict --max-files 0`.
- **Existing ledgers are unverified.** A ledger written before 4.21.7 has no
  origin anchor, so continuity and the evidence report stay `UNOBSERVED` for
  it. Move the old ledger aside to start an anchored one; its history is not
  lost, it is simply no longer counted as locally observed.
- **Sampled checks are not complete.** `hyodo check --json` on built-in
  sampled gates now reports `complete: false` and `project_coverage: SAMPLED`.
  `coverage` keeps its 4.21 meaning (gate coverage).
