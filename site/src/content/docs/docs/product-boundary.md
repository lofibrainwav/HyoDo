---
title: Product boundary
description: What HyoDo owns, what it does not own, and the invariants that keep evidence separate from authority.
---

HyoDo is a local verification and evidence layer for AI-assisted work. It helps
people see which checks ran, what they found, and what remains unknown. It does
not become the authority that plans, executes, merges, deploys, or remembers
work on behalf of another system.

## HyoDo owns

- local quality gates and their fail-closed verification status;
- evidence, measurement, validation, ledger, and attestation surfaces;
- local policy evaluation and explicit `ALLOW` / `DENY` / `ASK` /
  `UNOBSERVED` results; and
- observation of execution evidence supplied by an integrating host.

## HyoDo does not own

- task planning, routing, dispatch, or worker lifecycle;
- orchestration, recovery, settlement, merge, or deployment authority;
- the integrating host's current runtime state;
- external memory, knowledge bases, or continuity systems; or
- facts that HyoDo did not observe.

An integrating host may choose to enforce a HyoDo result, but the act of
enforcement belongs to that host.

## Factory Developer Preview

Factory (`examples/factory-loop/`) is an optional companion that runs from a
source checkout of this repository. It is not part of the published `hyodo`
package, and the lists above describe that package. Factory can discover
skills, report where each one came from, and suggest which skills fit a task.
A suggestion is evidence for the host, not a dispatch: the host decides what
to load and run, and owns execution, isolation, and authorization. Its
host-directed run path is experimental. No host is listed as verified, because
a configured adapter or a matching source hash is a narrower fact than a
connected session.

## Invariants

1. **Execution is not evidence.** Work happening does not prove the claimed
   checks ran.
2. **Evidence is not authority.** A receipt or policy result does not itself
   execute, merge, deploy, or approve anything.
3. **Missing evidence is not a pass.** Unreadable or absent evidence remains
   `UNOBSERVED`.
4. **Recorded history is not current runtime truth.** A memory, report, or
   previous receipt can inform review without proving what is true now.

## Public product and consumer closure

HyoDo is an independently installable public package. A user needs HyoDo and
their own project, not any particular agency, memory system, cloud provider,
or access to the original developer's runtime. The portable interface is the documented CLI, versioned
input/output schemas, and optional MCP adapter. A host may supply its own
gates, events, policy, and evidence, but HyoDo does not assume control of that
host's identity, approval database, or worker.

**Close HyoDo as a product, not as a customer's workflow.** A published
release is closed only by HyoDo-owned release-chain evidence (source and
version identity, CI, signed tag/release, SBOM, publication provenance, clean
installation and readback). An integration's successful test or broken
approval path cannot substitute for that release evidence, and cannot
silently reopen or invalidate a previously sealed release.

**Close each consumer separately.** A consuming system owns its configured
gate commands, evidence-source freshness, retry/approval policy, enforcement,
execution and post-deployment readback. Report its results as
`consumer_name + target revision + observation window + measured status`.
A consumer's `FAIL` means HyoDo observed a failure in that scope; it is not
a failure of HyoDo's published package without independent reproduction
against the package's public contract. An incomplete observation is never
treated as a complete green result.

Avoid private installation assumptions, hard-coded developer paths, or
consumer-specific requirements in HyoDo core. Validate portable behavior in
an isolated project with only the published package; test host integrations
separately. Existing human approval and release ownership remain in force.

## External integrations

Agent runtimes, CI systems, editors, and continuity stores may provide evidence
to HyoDo or consume evidence from it. Those integrations do not become HyoDo
state merely because HyoDo can observe or attest them.

`hyodo.orchestration-observation/v1` records an observation supplied by an
external executor. It does not execute the observed work, mutate the host, or
grant execution authority.

## Status vocabulary

Use **HyoDo status** only for HyoDo-owned source, package, gates, evidence,
dashboard, and HyoDo-owned runtime surfaces. Describe an external system's
state as that system's state. If ownership is not established, report it as
`UNATTRIBUTED` rather than assigning it to HyoDo.
