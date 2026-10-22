# Bounded check inputs and history persistence

## Git-backed BYOG input identity

For BYOG `hyodo check` targets with an observed Git commit and valid
measurement provenance, HyoDo compares
bounded pre/post content digests in addition to the existing commit/dirty
comparison. This detects changes between two already-dirty input states.

The additive `input_snapshot` JSON object names its scope, observation state,
and before/after digests. It includes Git-tracked and unignored files plus
`.hyodo/gates.toml`, even when that configuration is ignored. Generated
`.hyodo/history.jsonl` is excluded. File names, content, executable bits, and
symlink destinations participate in the digest; external symlink targets do
not. The current bounds are 20,000 files and 128 MiB of content per snapshot.

A changed snapshot withholds JSON gate rows and changes a successful check to
`UNOBSERVED`, with process exit code 2. An unreadable or over-budget snapshot
also withholds rows and changes a successful check to `UNOBSERVED`/exit 2.
A real gate failure remains a failure rather than being hidden by a snapshot
problem. Existing terminal gate details remain observations of commands that
ran; the final verdict and exit code describe whether they can be attributed.

This is not an atomic filesystem snapshot. It cannot establish that an input
was never changed and restored between observations. It does not cover ignored
dependencies, runtime state, remote services, or inputs outside the target.
Non-Git BYOG checks retain their existing contract and do not emit
`input_snapshot`. Built-in and sampled checks do not gain this BYOG-specific
content-identity guarantee.

## History append observation

Dashboard evidence adds `history_receipt.persistence`:

- `OBSERVED`: `append_history_receipt` returned success for this collection.
- `UNOBSERVED`: it reported failure; the existing warning is also emitted.

This records append success separately from the actual gate results. A failed
append does not rewrite a passing command into a failed command. Nor may a
passing gate be used as proof that its receipt was stored. Append success is
not a guarantee of disk durability, independent attestation, host consumption,
or execution authority. Historical rows and the pinned history schema are
unchanged.
