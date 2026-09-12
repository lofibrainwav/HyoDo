# Information Flow Attestation v0

Status: **observer-side contract + fixture implementation**.

HyoDo IFA records observed information lineage. It does not authorize, block,
or schedule execution.

## Separation of edges

Three relationships remain distinct:

- causal parent: execution causality;
- `evidence_refs`: citation/evidence support;
- IFA flow: observed information-derived-from relationship.

None is inferred from another.

## Vocabulary

Sensitivity:

```text
public | internal | confidential | restricted | unknown
```

Transformation:

```text
copy | summarize | redact | aggregate | unknown
```

Sink:

```text
local_process | local_file | human_visible | external_network | unknown
```

No raw prompt, response, code, path, or secret value is required by this
contract.

## Declassification

A transform such as `redact` does not declassify by itself. A declassification
is observed only when it carries explicit evaluator provenance, an evidence
reference, and an output sensitivity label.

Missing or malformed declassification provenance leaves the original
sensitivity in force for the attestation and marks the claimed declassification
unobserved.

## Readback

`hyodo.ifa.attest_information_flow()` returns a deterministic local receipt:

```text
status
flows
invalid
unresolved
risks
authority_decision = null
```

`status=OBSERVED` means the supplied observation rows were valid and all event
endpoints were resolved. It does not mean the flow was safe or authorized.

An external sensitive sink produces privacy-risk evidence only. HyoDo does not
turn that observation into a DENY.

## Promotion boundary

This v0 contract may merge independently of Graph v2 because it does not mutate
`hyodo.agent-event/v1` or the production evidence graph. Production graph
integration waits for the Graph v2 contract freeze and its causal identities.
