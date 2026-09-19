# fix: reconcile doctrine workflow and harden evidence boundaries

Malformed admission/orchestration observations could crash validation or write
non-standard JSON. Release gating accepted placeholder authorization and counted
skipped CI checks as successful. Reject malformed inputs before writes, require
non-placeholder authority/head references, and keep skipped checks separate
from observed successful checks.

Add a four-step reconciliation runbook with independent state axes, conditional
specialist lanes, existing-primitive reuse, delegated-authority boundaries and
separate product/research closure. Its schema is test-only; this change creates
no public state format, host executor or authority resolver.

Validation and observed limitations are recorded in
[the adversarial review](./hyodo-unified-doctrine-adversarial-review.md).
The candidate includes negative controls that failed before the fixes and
schema guard-removal tests. Focused checks: 164 passed. Isolated
`bash scripts/verify-public.sh`: exit 0, full pytest 1,748 passed with no skips,
lint/type/build/install checks passed. Installed-wheel admission smoke: six
cases passed. The separate CLI pytest run had one opt-in SBOM skip; that case
passed in the full integration-enabled run. This draft is not permission to
merge, and no remote PR or deployment is claimed.

Compatibility: valid existing observation shapes remain accepted. Non-finite
numbers, malformed enum types and absence markers are rejected. The release
CI snapshot gains a `skipped` list; `passed` counts actual successes only.
All-skipped snapshots block; mixed success/skipped snapshots still require the
host's independent required-check policy. Host grant owner, scope, expiry and
revocation authentication remain external responsibilities.
