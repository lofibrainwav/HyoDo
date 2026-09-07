---
title: Eye
description: Prove what was on screen without HyoDo ever storing a picture of it — capture, hash, show, destroy.
---

## What it does

`hyodo eye` lets an agent or operator prove *what was on screen* without
storing a picture of it. A screenshot is captured through an external tool
you configure, hashed two ways, shown to the operator with a visible
countdown, then deleted — and the deletion itself is recorded as a second
ledger event. Proof of existence and proof of destruction are always a
pair.

```bash
hyodo eye capture
hyodo eye verify --against <event_id>
```

HyoDo ships no capture tool (BYOM): configure one in `.hyodo/config.toml`
(`[eye] command = ["screencapture", "-x", "{out}"]`) or
`HYODO_EYE_COMMAND`. With neither configured, `capture` exits 2,
`UNOBSERVED`, never a silent no-op.

## What is stored

- An exact content digest of the captured file's bytes.
- A 64-bit perceptual hash (`dct64`, 16 lowercase hex chars) of the
  decoded pixels.
- Timestamps, a TTL, and whether the file was kept (`--keep`).

## What is never stored

- The image itself. No pixel bytes ever reach the agent ledger, no
  base64-encoded image, no upload anywhere.
- A percentage, probability, or confidence score for how similar two
  captures are. `eye verify` only reports a raw Hamming distance out of 64
  bits.

## Exit codes

| Outcome | Exit |
| --- | --- |
| `ALLOW` (capture proceeds) | 0 |
| `DENY` (including insufficient trust for `--keep`) | 1 |
| `UNOBSERVED` (no tool configured, capture failed, unsupported image, destruction unprovable) | 2 |
| `ASK` | 3 |

`eye.capture` is an unconditional external variable — it stays `ASK` below
trust level 3 unless approved interactively with `--yes`.

## Full reference

[docs/EYE.md](https://github.com/lofibrainwav/HyoDo/blob/main/docs/EYE.md)
covers the existence/destruction event pair and `--keep` in full.

## Next

- [Graph Export](/docs/graph-export/)
- [Trust](/docs/trust/)
