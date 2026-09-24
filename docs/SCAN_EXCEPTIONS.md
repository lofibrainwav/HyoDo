# Auditable local scan exceptions

Some workspaces keep private legal or financial working material next to
product code. HyoDo supports narrow, reviewed exceptions in
`.hyodo/scan-exceptions.toml` so those materials do not distort product-code
validation.

```toml
schema = "hyodo.scan-exceptions/v1"

[[general_exceptions]]
path = "private/legal/**"
reason = "private legal working material"

[[safety_exceptions]]
path = "fixtures/**"
rule = "dangerous_command/git_push_force"
reason = "detection fixture"
```

## Contract

- `general_exceptions` omit only matching workspace-relative paths from
  `hyodo check --general` syntax discovery.
- `safety_exceptions` suppress only one exact `category/label` finding at a
  matching workspace-relative path.
- Every entry requires a non-empty `reason`.
- Absolute and parent-directory paths are rejected.
- If the file exists but is malformed, `hyodo check --general` and
  `hyodo safe` exit `2`; the result is never a validation pass.
- `hyodo safe` reports the number of safety findings suppressed by the policy
  in both human and JSON output.

## Approval

The exceptions file is written by the repository, so it cannot approve
itself. Until an operator approves the file's exact digest, nothing in it is
applied: findings stay visible and `hyodo safe` reports
`exceptions_status: "unapproved"` with the number of entries withheld.

- `hyodo safe --approve-exceptions` shows every entry and its digest and asks
  for approval in a terminal. The approval is stored in per-user state outside
  the checkout, bound to this checkout's path and to this exact file content.
  Any edit to the file needs a new approval. It is refused without a terminal.
- Automation that has reviewed the file out of band can pin its digest with
  `HYODO_SCAN_EXCEPTIONS_DIGEST=sha256:<hex>`. Only that exact content is
  applied; a pull request that edits the file changes the digest and its
  exceptions are withheld again.

Exceptions are a scope boundary, not a way to approve a change. Review their
paths and reasons with the same care as source code.
