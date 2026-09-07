# Ephemeral visual evidence (`hyodo eye`)

`hyodo eye` lets an agent or operator prove *what was on screen* without
HyoDo ever storing a picture of it. A screenshot is captured through an
external tool you configure, hashed two ways, shown to the operator with a
visible countdown, then deleted — and the deletion itself is recorded as a
second ledger event. Proof of existence and proof of destruction are a
pair; neither one alone is the point.

## What is stored

- An exact content digest (`content_digest()`, the same 12-hex-char SHA-256
  prefix every other ledger event uses) of the captured file's bytes.
- A 64-bit perceptual hash (`phash_algo: "dct64"`), 16 lowercase hex
  characters, computed from the decoded pixels.
- Timestamps, a TTL, and whether the file was kept.

## What is never stored

- The image itself. `hyodo eye` never writes pixel bytes into the agent
  ledger (`.hyodo/agent-events.jsonl`), never base64-encodes an image into
  an event, and never uploads a capture anywhere.
- A percentage, a probability, or a confidence score for how similar two
  captures are. `hyodo eye verify` only ever reports a raw Hamming
  distance out of 64 bits.

## BYOM: bring your own capture tool

HyoDo does not ship a screen-capture tool. Configure one in
`.hyodo/config.toml`:

```toml
schema = "hyodo.config/v1"

[eye]
command = ["screencapture", "-x", "{out}"]
```

`{out}` is replaced with the temporary output path HyoDo chooses
(`<root>/.hyodo/eye/<uuid>.png`) before the command runs. The command runs
as `subprocess.run(argv, timeout=30)` with **no shell** — the array is the
literal argv, so there is no quoting or injection surface. An environment
variable overrides the config file for one-off runs:

```bash
HYODO_EYE_COMMAND='["screencapture", "-x", "{out}"]' hyodo eye capture
```

With neither configured, `hyodo eye capture` exits 2, `UNOBSERVED`,
`rule_id = "eye_tool_absent"` — never a silent no-op.

## Policy: an undeclared boundary, not a free tool

`eye.capture` joins the same built-in, unconditional external-variable set
as `skills.ingest`: it always produces an external variable (`eye_capture`)
regardless of `ask_tools` configuration, and only trust level 3 (full
delegation) softens the decision to `ALLOW` on its own. Trust level 2's
"inside the boundary" carve-out was never meant to cover an undeclared
screen capture, so it stays `ASK` there exactly like level 1. Approve an
`ASK` interactively with `--yes` (this records a human decision event
before the capture runs).

## Exit codes

| Outcome | Exit |
| --- | --- |
| `ALLOW` (capture proceeds) | 0 |
| `DENY` (including `eye_keep_insufficient_trust`) | 1 |
| `UNOBSERVED` (no tool configured, capture failed, unsupported image, or destruction unprovable) | 2 |
| `ASK` | 3 |

## `--keep`

`--keep` retains the file instead of deleting it, and requires trust level
>= 2 — below that it is an outright `DENY`
(`rule_id = "eye_keep_insufficient_trust"`) with no capture attempted at
all. At trust level >= 2 with `--keep`, the capture event is recorded with
`kept: true`, `destroyed_at: null` permanently, and the JSON output
carries `ledger_write_required: true`, the same obligation any other
autorun decision picks up at that trust level (see `docs/POLICY_TRUST.md`).

## The existence + destruction pair

A successful capture always writes two ledger events with the same
`phash`/`ttl_s`:

1. `tool_result`, `meta.tags = ["eye-capture"]`, `meta.ephemeral.destroyed_at: null` —
   proof the capture happened.
2. `tool_result`, `meta.tags = ["eye-destroy"]`, `parent_event_id` pointing
   at event 1, `meta.ephemeral.destroyed_at` set to the deletion timestamp —
   proof the file is gone.

If the capture format cannot be decoded, `phash` is `null` on both events
(`meta.ephemeral.unsupported: true`), the file is still deleted, and the
command still exits 2 (`rule_id = "eye_image_unsupported"`) — an
unsupported format is not silently treated as a clean capture. If deletion
itself fails, HyoDo cannot prove destruction: it records
`meta.tags = ["evidence_destruction_failed"]`, `kept: true`,
`destroyed_at: null`, and exits 2 even though the capture succeeded.

## `hyodo eye verify`

```bash
hyodo eye verify --against <event_id> [--phash-threshold N]
```

Re-captures now, through the same policy gate as `capture` (the re-capture
is itself ephemeral: deleted, both its events recorded), and reports the
Hamming distance between the fresh hash and the referenced event's stored
`phash` — `same screen (distance N of 64)` or
`different screen (distance N of 64)`, never a percentage. The threshold
comes from `--phash-threshold`, then `[ephemeral].phash_distance_threshold`
in `.hyodo/policy.toml` (default 10 of 64 bits), and is advisory only — it
never changes a policy decision. An event with no stored `phash`, or a
`phash_algo` that does not match today's `"dct64"`, is a plain error
(exit 1) rather than a distance.
