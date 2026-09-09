# Friction Contribution v1

HyoDo can derive coarse friction signals from its local `hyodo.agent-event/v1`
ledger. In v1, this feature is **local only**: there is no collector endpoint,
background uploader, hosted dataset write, or network transport.

```text
agent-events.jsonl
      ↓ local derivation only
hyodo.friction-contribution/v1
      ↓ preview or explicit local export
hyodo.friction-export/v1
```

## Consent boundary

Friction Contribution is **OFF by default**.

```bash
hyodo friction status
hyodo friction preview
hyodo friction on --yes
hyodo friction export --yes
hyodo friction off
hyodo friction contract
```

`hyodo friction on` enables only **local contribution preparation**. It does
not grant network consent. The persisted state explicitly stores
`network_consent: false`, and network transport is hard-disabled in this
release.

If HyoDo later gains a network collector, that collector must obtain a new,
separate, explicit consent action. It must not inherit permission from the v1
local `enabled` flag.

`hyodo friction preview` works even while contribution preparation is OFF so an
operator can inspect the exact derived record before opting in locally. The
preview never sends data. `hyodo friction export` is the separate Lane C file
write: it requires `enabled=true` and explicit `--yes`, and defaults to
`.hyodo/friction-export.json`. It never uploads the file.

In a non-interactive shell, export without `--yes` refuses with
`confirmation_required` and writes nothing. Export while disabled also writes
nothing. An unreadable ledger refuses the write with exit code 2.

The state file `.hyodo/friction-contribution.json` contains only local
preparation state. It never accumulates contribution rows. The export file is
a separate envelope with schema `hyodo.friction-export/v1`:

```json
{
  "schema": "hyodo.friction-export/v1",
  "hyodo_version": "4.17.0",
  "exported_at": "2026-09-09T00:00:00+00:00",
  "consent": {
    "enabled": true,
    "network_consent": false,
    "scope": "local_only_v1"
  },
  "observation": {},
  "contributions": [],
  "never_export": [],
  "authority": {}
}
```

The export reuses the preview's observation and contribution objects. It does
not add `run_id`, `event_id`, `actor_id`, paths, prompts, model strings, raw
arguments, or ledger rows. `exported_at` exists only on the envelope; it is not
added to the fixed 18-field contribution contract.

## Strict contribution shape

The schema is `hyodo.friction-contribution/v1`. Print the exact machine-readable
JSON Schema with:

```bash
hyodo friction contract --json
```

Each record contains only these allow-listed fields:

- `schema`
- `source_schema`
- `hyodo_version`
- `task_class`
- `risk_bucket`
- `orchestration_pattern`
- `event_count_bucket`
- `parallelism_bucket`
- `retry_bucket`
- `rework_bucket`
- `verification_failure_bucket`
- `human_intervention_bucket`
- `approval_wait_bucket`
- `resource_conflict_bucket`
- `evidence_completeness`
- `outcome`
- `provider_class`
- `source_quality`

The contract uses `additionalProperties: false`. Unknown or newly invented
fields cannot silently enter the contribution surface.

## Never exported by v1

The contribution object has no field for:

- prompts or model-response bodies;
- source code, diffs, or file contents;
- file paths or repository names;
- secrets or credentials;
- email bodies or addresses;
- raw command arguments;
- raw event bodies;
- `event_id`;
- `run_id`;
- `actor_id`;
- exact timestamps;
- persistent user identifiers; or
- persistent machine identifiers.

HyoDo may use `run_id`, `actor_id`, step indices, and timestamps **locally while
deriving** coarse buckets. Those values are not copied into the output
contract. `--run-id` on `hyodo friction preview` is a local selection filter
only and is not echoed into the contribution.

Model names are reduced to a coarse provider class (`openai`, `anthropic`,
`google`, `xai`, `meta`, `other`, or `unknown`). Exact model strings are not
part of the contract.

## Derived, not guessed

The v1 deriver prefers explicit structured evidence over inference:

- `task:<class>` and `risk:<bucket>` tags are consumed only from fixed
  allow-lists;
- HTTP method can establish coarse read/write risk when available;
- retries, rework, resource conflicts, and verification failures require
  explicit safe tags;
- an `ASK` approval wait becomes a coarse time bucket, never an exact time;
- fan-out is observed only when distinct `actor_id` values share a step;
- missing evidence becomes `unknown` or `unobserved` instead of a guessed
  classification.

Caller-asserted policy claims do not count as measured decisions. A policy
outcome influences the contribution only when the ledger carries HyoDo
policy-evaluator provenance (`evaluated_by`).

## Population evidence is not authority

This is a protocol invariant, not a product slogan:

```text
Population evidence → ACL support recommendation  YES
Population evidence → execution authority         NO
Population evidence → override local policy       NO
Population evidence → override Evidence Gate      NO
```

A future population prior can answer questions such as “how much supervision
usually reduced retries for this task class?” It cannot answer “may this user
perform this action?”

EROS/local authority decides **whether** an action is permitted. ACL decides
**how much support** is appropriate. The Evidence Gate decides whether the
claimed result is actually proven.

## State file

Local state is stored at:

```text
.hyodo/friction-contribution.json
```

It is written owner-only (`0600`) and contains no contribution rows or raw
ledger content. A missing state file is an honest default OFF. A malformed or
unreadable state file fails closed to OFF/UNOBSERVED.

## What v1 deliberately does not implement

- no telemetry server;
- no HTTP client for contributions;
- no background upload;
- no persistent installation identifier;
- no population-prior download;
- no automatic ACL level change;
- no authority or policy override.

Those are separate future product and research decisions. The v1 goal is to
make the local measurement contract inspectable and testable **before** any
network collection exists.
