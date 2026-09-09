# Measured Run #1 receipt

This is a runtime measurement receipt, not a research result and not a claim
that ACL, Graph v2, or Wisdom Reflex is implemented.

## Scope

- Observed locally: 2026-09-08 23:36:29–23:36:30 -07:00
  (`2026-09-09T06:36:29Z`–`2026-09-09T06:36:30Z`)
- KINGDOM task: `node cli/index.js status --json`
- Task class: read-only status/recent/EROS readback
- Command exit code: `0`
- KINGDOM repository: `/Users/brnestrm/kingdom`
- KINGDOM commit SHA: `17fc4f5eccc1cebd14f023a15981c740a60b8f7c`
- KINGDOM worktree was already dirty; this run did not modify its tracked
  files or existing WIP.
- The task output included an EROS readback of `S=0 UNKNOWN fresh=false`; this
  stale/unknown observation was preserved and was not treated as a success.

## Installed HyoDo readback

The installed entrypoint was tested from `/tmp` so the HyoDo checkout could not
shadow the installed package on `sys.path`.

| Field | Observed value |
| --- | --- |
| entrypoint | `/Users/brnestrm/.local/bin/hyodo` |
| entrypoint target | `/Users/brnestrm/.local/pipx/venvs/hyodo/bin/hyodo` |
| installed version | `HyoDo v4.17.0 - model-agnostic quality gates` |
| installed module | `/Users/brnestrm/.local/pipx/venvs/hyodo/lib/python3.14/site-packages/hyodo/__init__.py` |
| friction command | `hyodo friction preview` was present in installed help |

The HyoDo source checkout was independently at `bf4fd1941f1efbc3c1a5e8d89dcf45e35a03d732`; this is source context only, not substituted for the installed-binary readback above.

## HyoDo ledger receipt

- Ledger: `.hyodo/agent-events.jsonl`
- Run ID (local selection filter only): `b1f046bb-f634-419d-b893-d493afde8717`
- Event count: `4`
- Event schema: `hyodo.agent-event/v1`
- Event kinds: `prompt`, `tool_call`, `tool_result`, `decision`
- Actor identity observed by v1: one actor label, `kingdom-status-readback`
- Ledger corrupt lines for this preview: `0`
- Command output: `1429` bytes; digest-only output digest `dcb01359d6b9`

The events were appended with default digest-only storage. No raw prompt,
response, or command body was retained in the ledger.

## Friction preview readback

The installed 4.17.0 binary was run as:

```bash
hyodo friction preview \
  --root /Users/brnestrm/HyoDo \
  --run-id b1f046bb-f634-419d-b893-d493afde8717 \
  --json
```

Observed preview envelope: `hyodo.friction-preview/v1`.

| Field | Observed value |
| --- | --- |
| `network_consent` | `false` |
| `network_transport` | `disabled` |
| `nothing_transmitted` | `true` |
| `enabled` | `false` |
| `source` | `observed` |
| `runs_observed` | `1` |
| `source_quality` | `complete` |
| `task_class` | `read_only` |
| `risk_bucket` | `low` |
| `orchestration_pattern` | `serial` |
| `parallelism_bucket` | `1` |
| `event_count_bucket` | `4-7` |
| `retry / rework / verification_failure` | `0 / 0 / 0` |
| `human_intervention / approval_wait / resource_conflict` | `0 / none / 0` |
| `evidence_completeness` | `missing` |
| `outcome` | `unknown` |
| friction delta | `UNOBSERVED` — no before/after comparator was run |

This is the topology v1 actually observed: sequential, one actor, no fan-out,
and no join. The command completed with exit code 0, but the friction outcome
remains `unknown` because no HyoDo policy evaluator stamped a measured
decision. Zero buckets are not reported as friction improvement.

## Sensor interpretation

`hyodo friction preview` is not a score. It is a local deriver from
`hyodo.agent-event/v1` ledger rows: it groups rows by `run_id`, emits one
`hyodo.friction-contribution/v1` object per run, and places those objects in
the preview envelope's `contributions[]`. The human-readable panel and
`--json` use the same contribution objects. Preview may be `enabled=false`
and still produce this local readback; it does not transmit anything.

The contribution object has exactly 18 fixed fields and rejects additional
properties. It intentionally contains no integrity score, trust level, gate
PASS/FAIL result, three-way friction label, cost, or success-quality metric.
Gate evidence can only appear indirectly through `evidence_refs` when the
host records it; it is not converted into a gate verdict by the deriver.

For this receipt, `human_intervention=0` means that this captured ledger had
no event with `actor="human"`. It does not mean that human friction was
absent. Likewise, `retry`, `rework`, `resource_conflict`, and
`verification_failure` remained zero because the corresponding event tags or
evaluated evidence were not recorded. `outcome=unknown` reflects the absence
of an `evaluated_by` decision, not command success quality.

The default-hook interpretation is therefore a sensor-contract warning: a
hook that records only `tool.name`, occasional paths, and digest-only output
will generally yield `unknown` task/risk, `serial`/`1`, zero tagged counters,
`unobserved` evidence completeness, `unknown` outcome, and `unknown` provider.
`human_intervention=1` occurs only if its first prompt is actually normalized
as an `actor="human"` ledger event; the deriver does not infer that value from
the existence of a prompt alone. Those defaults are not evidence of “no
friction”; they show that the sensor has not observed the relevant fields.

One implementation detail is recorded explicitly: although a contribution is
selected by `--run-id`, `run_id` is not exported in the contribution object.
In the current v1 implementation, `source_quality` is derived from the
ledger-wide corrupt-line count and propagated to each selected contribution;
it is not an independent per-run corruption calculation. An unreadable ledger
is a different case: preview reports an unreadable source with exit code `2`
and zero contributions.

Accordingly, this Run #1 can establish the v1 observation path and its
privacy/authority boundary, but it cannot test an ACL hypothesis or claim a
friction change without host-provided tags, actor/step metadata, evaluated
decisions, and a before/after comparator.

## Export and authority checks

- Contribution envelope: `hyodo.friction-contribution/v1`.
- Contribution keyset matched the strict allow-list exactly.
- Forbidden export keys observed: none (`run_id`, `event_id`, `actor_id`,
  `timestamp`, `prompt`, and `path` were absent).
- The preview's `never_export` list contained all v1 prohibited categories:
  prompts, responses, source code, diffs, file contents, file paths, secrets,
  credentials, emails, raw command arguments, raw event bodies, event IDs, run
  IDs, actor IDs, exact timestamps, persistent user IDs, and persistent machine
  IDs.
- Authority readback: `may_influence_acl_support=true`,
  `may_grant_execution_authority=false`, `may_override_local_policy=false`,
  `may_override_evidence_gate=false`.
- Observer permission mutation: `false` within the observed scope. KINGDOM's
  pre/post tracked diff remained the pre-existing dirty set only; no permission,
  policy, ACL, or authority file was changed by the read-only status task. The
  HyoDo ledger append was the requested measurement artifact, not a permission
  mutation.

## Result

Run #1 is **measured and disappointing by design**: the bridge recorded a real
KINGDOM readback, but it observed only sequential topology, missing evidence
completeness, unknown outcome, and no measurable friction delta. No automatic
ACL/Wisdom behavior is inferred from this run.
