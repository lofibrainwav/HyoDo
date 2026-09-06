# HyoDo basic usage

Every command below is a real `hyodo` CLI command in the current release.
Nothing here grants approval: scores and scan results are review signals, and
missing evidence is reported as missing, never as green.

## 1. Scan before you trust a change

```bash
hyodo safe --strict
```

Early-warning scan for secrets, destructive commands, and production-impact
patterns. Exit `0` reports, `1` means a high-severity finding under `--strict`,
`2` means the path could not be scanned. The output states how many files were
scanned out of how many were found, so partial coverage is never hidden.

## 2. Reuse the checks your project already has

```bash
hyodo init     # detects pytest, Ruff, mypy, Pyright, npm scripts, Go, Cargo, Makefile
hyodo check    # runs the detected gates; exit 2 when nothing measurable ran
```

`init` writes `.hyodo/gates.toml`. `check` exits `0` only when executed gates
passed. An empty or malformed gate file exits `2`, not `0`.

## 3. Optional review score

```bash
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --hyo 0.9
```

Prints the HyoDo Integrity Score from the Six-Virtue Model and its geometric
mean. Trinity Gates is the structured subset; HYOGOOK V5 is the formula
lineage. A single pillar at zero collapses the signal. The score is decision
support for a human reviewer; it never authorizes a merge or a deploy.

## 4. Record what an agent did

```bash
hyodo event validate --file step.json
hyodo event record --file step.json --root . --policy .hyodo/policy.toml
hyodo policy check --file step.json --config .hyodo/policy.toml
```

Events are appended to `.hyodo/agent-events.jsonl` (digest-only by default).
`policy check` exits `0` on ALLOW, `1` on DENY, `2` when the policy or ledger is
unobservable. A DENY must be enforced by the caller; HyoDo is not a sandbox.
See [`fde-evidence-spine/`](./fde-evidence-spine/) for a complete example.

## 5. Look at the evidence

```bash
hyodo report --format md      # or html, sarif
hyodo dashboard --open        # local loopback panel on :8768
```
