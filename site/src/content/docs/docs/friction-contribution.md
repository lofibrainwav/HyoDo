---
title: Friction Contribution
description: Privacy-first local friction derivation for future ACL research priors.
---

> **Version boundary.** The `hyodo friction` command is introduced in **HyoDo 4.17.0**. HyoDo 4.16.x and earlier do not expose this command. Friction Contribution v1 is local only: HyoDo does not upload friction data, and network transport is disabled.

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

## Check the instrument before using it

```bash
hyodo --version
hyodo friction --help
```

If `hyodo --version` reports 4.16.x or earlier, `hyodo friction` is not part of
that installation. Upgrade to a 4.17.0-or-newer release before following the
commands below.

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
and Friction Contribution v1 has no upload transport.

A future collector must request fresh, separate consent rather than inheriting
this local setting.

## What a contribution may contain

The strict v1 schema allows coarse fields such as:

```json
{
  "schema": "hyodo.friction-contribution/v1",
  "source_schema": "hyodo.agent-event/v1",
  "hyodo_version": "4.17.0",
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

## Measurement boundary

Friction Contribution v1 derives coarse operational signals such as retry,
rework, intervention, wait, resource-conflict, evidence-completeness, and
outcome buckets. It does **not** automatically decide whether an observed
friction episode was **necessary**, **productive**, or **avoidable**.

Those categories are research labels. Classifying them defensibly may require
outcome context, causal comparison, independent review, or human annotation.
A lower retry count, for example, is not automatically a better outcome if the
missing retry would have caught an error.

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

Population experience can eventually help answer **what support profile is
useful here?** It cannot answer **whether this action is authorized?**

That separation keeps the research model aligned with HyoDo/KINGDOM:

- **EROS / Authority — whether?**
- **ACL — what support profile?**
- **Evidence Gate — done?**

## No collector yet

v1 deliberately ships without a telemetry endpoint, uploader, installation
identifier, population-prior download, or automatic ACL support change. The
first goal is an inspectable, reproducible local measurement contract.

See the [ACL field note](/docs/acl/) for the Wisdom Reflex and collaboration-topology hypothesis, the [Research](/docs/research/) page for the broader empirical program, and the repository's `docs/FRICTION_CONTRIBUTION.md` for the detailed protocol boundary.
