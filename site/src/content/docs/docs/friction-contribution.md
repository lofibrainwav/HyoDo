---
title: Friction Contribution
description: Privacy-first local friction derivation for future ACL research priors.
---

> **Local only in v1.** HyoDo does not upload friction data in this release. Network transport is disabled.

# Friction Contribution v1

HyoDo can turn local `hyodo.agent-event/v1` traces into coarse,
privacy-transformed `hyodo.friction-contribution/v1` records.

```text
local agent events
      ↓
local friction derivation
      ↓
strict allow-listed contribution
      ↓
local preview only
```

The point is to define the sensor contract **before** any population collector
exists.

## OFF by default

```bash
hyodo friction status
hyodo friction preview
hyodo friction on --yes
hyodo friction off
hyodo friction contract --json
```

`friction on` means **prepare derived contribution records locally**. It is not
network consent. The local state explicitly records `network_consent: false`,
and this release has no upload transport.

A future collector must request fresh, separate consent rather than inheriting
this local setting.

## What a contribution may contain

The strict v1 schema allows coarse fields such as:

```json
{
  "schema": "hyodo.friction-contribution/v1",
  "source_schema": "hyodo.agent-event/v1",
  "hyodo_version": "4.16.0",
  "task_class": "code_change",
  "risk_bucket": "medium",
  "orchestration_pattern": "fanout",
  "event_count_bucket": "4-7",
  "parallelism_bucket": "2",
  "retry_bucket": "1",
  "rework_bucket": "0",
  "verification_failure_bucket": "1",
  "human_intervention_bucket": "0",
  "approval_wait_bucket": "none",
  "resource_conflict_bucket": "0",
  "evidence_completeness": "complete",
  "outcome": "pass",
  "provider_class": "anthropic",
  "source_quality": "complete"
}
```

The JSON Schema uses `additionalProperties: false`; print the installed
contract with `hyodo friction contract --json`.

## What cannot leave through this contract

There are no v1 fields for raw prompts, responses, source code, diffs, file
contents, file paths, credentials, emails, raw commands, raw event bodies,
`event_id`, `run_id`, `actor_id`, exact timestamps, persistent user IDs, or
persistent machine IDs.

Some of those values may be inspected **locally during derivation**. For
example, distinct actors sharing a step can establish a fan-out pattern, and
timestamps around an `ASK` can establish a wait bucket. The source values are
then discarded from the contribution shape.

Exact model names are reduced to a coarse provider class. Unknown evidence is
reported as `unknown` or `unobserved` instead of being guessed.

## Measured policy only

Caller-asserted `ALLOW` / `DENY` / `ASK` claims do not become friction
outcomes. The deriver only reads a decision when HyoDo evaluator provenance is
present in the ledger.

That keeps a caller from manufacturing a favorable population prior by simply
claiming its own work was allowed.

## The authority invariant

```text
Population evidence → ACL support recommendation  ✅
Population evidence → execution authority         ❌
Population evidence → override local policy       ❌
Population evidence → override Evidence Gate      ❌
```

Population experience can eventually help answer **how much support?** It
cannot answer **whether this action is authorized?**

That separation keeps the research model aligned with HyoDo/KINGDOM:

- **EROS / Authority — whether?**
- **ACL — how much support?**
- **Evidence Gate — done?**

## No collector yet

v1 deliberately ships without a telemetry endpoint, uploader, installation
identifier, population-prior download, or automatic ACL level change. The
first goal is an inspectable, reproducible local measurement contract.

See the [Research](/docs/research/) note for the ACL evaluation direction, and
the repository's `docs/FRICTION_CONTRIBUTION.md` for the detailed protocol
boundary.
