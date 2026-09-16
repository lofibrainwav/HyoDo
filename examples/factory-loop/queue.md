# Factory queue

One feature per item. The runner (`factory-loop.sh`) takes the first unchecked
item, isolates it on its own branch, hands it to the host's builder and
reviewer, and then asks HyoDo whether the gates actually ran and passed.

An item is a frozen contract, not a wish. Write it before the night starts and
do not let the builder or the reviewer edit it. Fields:

- **goal** — one sentence a reviewer can falsify.
- **non-goals** — what the builder must not touch, even if tempting.
- **mock** — path to the functional prototype or fixture that is the answer key.
- **gates** — the gate names in `.hyodo/gates.toml` that must run and pass.
  If none of them can run, `hyodo check` exits 2 and the item stays open.

The runner never marks an item done. A human does that after the merge.

## Items

One item per line so the runner can read it with a single `grep`.

- [ ] `csv-export` — goal: `/reports/export` returns a CSV of the current filter; non-goals: no schema changes, no new dependencies; mock: `mocks/csv-export.http`; gates: `pytest`, `ruff`
- [ ] `retry-on-timeout` — goal: outbound HTTP client retries idempotent GETs twice with jittered backoff; non-goals: no retries on POST, no global timeout change; mock: `mocks/retry-fixture.json`; gates: `pytest`
