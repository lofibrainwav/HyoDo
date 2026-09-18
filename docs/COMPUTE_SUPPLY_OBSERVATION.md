# Compute Supply Observation

`hyodo.compute-supply-observation/v1` is an evidence contract for externally
discovered compute supply.

It records three independent layers:

```text
CATALOG            what exists now
USER_AVAILABILITY  what the current user configuration/auth can see
LIVE_ACCESS        what is invocable now, including observed quota/access
```

HyoDo does not load adapters, discover providers, select models, route work,
or authorize execution. A `FREE_OK` observation is evidence for a host such as
KINGDOM; it is never a placement decision.

Credentials and prompt/response content are excluded or redacted. Unknown
values remain `UNOBSERVED`, and freshness is explicit through `observed_at` and
`fresh_until`.
