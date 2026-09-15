---
title: Why HyoDo
description: Why HyoDo exists next to the tools you already run, and what it deliberately does not do.
---

## Why not just run ruff / pytest in CI?

You already can, and HyoDo does not replace that. The gap it closes is
different: a normal green check tells you a command returned zero, not
whether that command actually ran against the code you think it ran
against. Evidence that a check ran is a different claim from a green light
that appears when nothing ran. HyoDo makes that boundary explicit — an
empty or malformed gate configuration exits `2`, not `0`, so "unmeasured"
can never be reported as "passed."

## How is this different from AI code review bots?

Most AI review bots are advisory and cloud-hosted: they comment on a pull
request from the outside, after the fact. HyoDo is local-first and
fail-closed by default — it runs in your own environment, reuses your own
tooling, and reports missing or unreadable evidence as `UNOBSERVED` instead of
turning it into a pass. Its optional legacy HyoDo score is a review signal,
not permission to merge or deploy. The compatibility command retains an older
five-input geometric-mean method, internally named HYOGOOK V5, while HyoDo's
replacement evaluation model is being updated. The current public package
does not yet provide a general per-axis evaluator, and the model does not
define the six reference values as one canonical score.

## Is it a sandbox?

No. HyoDo is not a runtime sandbox or a process interceptor. A `DENY`
decision from `hyodo policy check` is recorded for audit, but the caller —
the agent runtime invoking HyoDo — is responsible for actually stopping the
agent. HyoDo observes and records; enforcement of a `DENY` result belongs to
whoever is running the agent.

## Next

- [Quickstart](/docs/quickstart/)
- [Trust](/docs/trust/)

HyoDo does not claim an installed base; see `docs/CLAIMS.md`.
