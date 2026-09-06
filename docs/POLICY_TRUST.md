# Policy trust ladder

HyoDo supports four trust levels (0–3) for fine-grained policy enforcement.

Use `hyodo policy trust grant --level N` (0–3) to grant trust and
`hyodo policy trust show` to inspect it. Grants live in untracked
`.hyodo/policy-trust.json`; `[trust] max_level` in `policy.toml` only
caps the granted level. Non-interactive grants require
`HYODO_POLICY_TRUST_ALL=1`.
