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

Exceptions are a scope boundary, not a way to approve a change. Review their
paths and reasons with the same care as source code.
