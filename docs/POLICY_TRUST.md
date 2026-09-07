# Policy trust ladder

HyoDo supports four trust levels (0–3) for fine-grained policy enforcement.

Use `hyodo policy trust grant --level N` (0–3) to grant trust and
`hyodo policy trust show` to inspect it. Grants live in untracked
`.hyodo/policy-trust.json`; `[trust] max_level` in `policy.toml` only
caps the granted level. Non-interactive grants require
`HYODO_POLICY_TRUST_ALL=1`.

## What each level does

When `[trust]` is not configured the level is 1. Otherwise the effective
level is `min([trust].max_level, granted level)`. Hard `DENY` rules always
win first, and the earlier fail-closed `UNOBSERVED` outcomes (missing or
invalid policy, unobservable coverage) are unaffected by trust; trust never
softens a `DENY`, and `ASK` is never downgraded to `DENY`. Past those
checks, an event with no external variable is `ALLOW` at every level.

External variables are collected from `tool_call` and `tool_result` events:
a call to a web tool (the built-in names `web_fetch`, `browser`, `http`,
`fetch`, `WebFetch`, `WebSearch`, or any `ask_tools` entry) whose domain
matches no `[web].allowed_domains` pattern (`web_domain_unlisted`); a path
outside the root (`path_outside_root`); and any call to a built-in web tool
or an `ask_tools` entry (`ask_tools:<name>`).

| Level | External variables present | Ledger |
| --- | --- | --- |
| 0 | `ASK`, no widening at all | none |
| 1 (default) | `ASK` | none |
| 2 | `ALLOW` only when every variable is inside the boundary | required |
| 3 | `ALLOW` for any external variable (autorun) | required |

Levels 0 and 1 evaluate identically today; level 0 is the explicit
"no delegation" grant. "Inside the boundary" at level 2 means every
external variable is `path_outside_root` or `ask_tools`; a
`web_domain_unlisted` variable keeps the decision at `ASK`.

At level 2 and above, `policy check` reports
`ledger_write_required: true` and `ledger_written: false`; the call must be
recorded with `hyodo event record --policy`, which reports `ledger_written`
from the real append result.

Two fail-closed rules apply when at least one external variable is present:
at level 2 or 3 the evaluator needs an observable ledger
(`observed_steps`), otherwise the decision is `UNOBSERVED`
(`rule_id` `autorun_level2` / `autorun_level3`); and whenever `[trust]` is
configured but `.hyodo/policy-trust.json` is missing or damaged, the
decision is `UNOBSERVED` (`trust_grant_unobserved`), never a default grant.

Exit codes are unchanged: `ALLOW` 0, `DENY` 1, `UNOBSERVED` 2, `ASK` 3.

## URL credential observations

Normalized `tool.urls` entries contain `domain`, `digest`, and
`credential_shaped` (boolean or `null`). A supplied path determines the
boolean during normalization; without a path, a supplied boolean is kept,
otherwise the shape is `null` (unobserved).
When neither path nor digest is supplied, `digest` is `null`.
With the default credential boundary, a true shape means `DENY`, a missing
shape without a legacy path means `UNOBSERVED`, and false continues normal
policy evaluation. Paths remain absent from default ledgers and graphs.

`credential_shaped_path` (`hyodo/events.py`) matches case-insensitively against
a path-marker list and a query-marker list: paths containing `/.git/`, `/.env`,
`/wp-admin/`, `/.aws/`, `/.ssh/`, `/.netrc`, `/.kube/`, `credentials`, `id_rsa`,
`.pem`, or `/etc/shadow`, or queries containing `token=`, `api_key=`, `secret=`,
`password=`, `access_token=`, `apikey=`, `auth=`, or `sig=`.
