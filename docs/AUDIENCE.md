# Audience profiles

`--audience` picks a vocabulary, never a decision. The verdict word, exit
code, `rule_id`, evidence references (file:line, event ids, digests), and
`--json` payload content are byte-identical across `vibe`, `engineer`, and
`professional` — the only thing a `--json` payload may add is one key,
`"audience": "<profile>"`. No profile calls a model; each is a fixed lookup
table in `hyodo/verdict.py` and `hyodo/audience.py`. A profile never softens
a decision: `DENY` in vibe mode is still plainly a stop.

## The three profiles

### `engineer` (default)

Today's format, unchanged.

```text
$ hyodo check --quiet --audience engineer
HYODO PASS — 4/4 gates observed, all executed gates passed
```

### `vibe`

One plain sentence. Traffic-light word first (`GREEN` for PASS/ALLOW,
`YELLOW` for ASK, `RED` for DENY/FAIL, `GREY — could not see` for
UNOBSERVED), then what happened and what to do. No jargon, no `rule_id`s —
those stay in `--explain`.

```text
$ hyodo check --quiet --audience vibe
GREEN — all executed gates passed (4/4 gates checked). You're clear to move on.
```

### `professional`

Control language: `Control satisfied` (ALLOW/PASS), `Exception — approval
required` (ASK), `Control failure` (DENY/FAIL), `Scope limitation — evidence
not observed` (UNOBSERVED), followed by the same `n/m <unit> observed`
figures and detail every profile prints.

```text
$ hyodo check --quiet --audience professional
Control satisfied — 4/4 gates observed, all executed gates passed
```

An optional `domain` (`law` | `accounting` | `general`, professional only)
swaps three nouns in `--explain` text: `engagement` (law: `matter`),
`workpaper` (law: `exhibit`), `sign-off` (law: `counsel review`).
`accounting` and `general` keep the defaults.

## Resolution order

1. `--audience` flag (per command: `check`, `safe`, `policy check`,
   `event record --policy`)
2. `HYODO_AUDIENCE` environment variable
3. `[audience] profile` in `.hyodo/config.toml`
4. Default: `engineer`

An explicit `--audience`/`HYODO_AUDIENCE` value outside `vibe` / `engineer` /
`professional` exits 2 `UNOBSERVED` with reason `invalid_audience:<value>` —
that is a real error, because you asked for something specific and it does
not exist. A missing, unreadable, or malformed `.hyodo/config.toml`, or an
invalid value sitting inside it, is never an error: it silently falls
through to the next source in the list above.

## Config file

`.hyodo/config.toml`, schema `hyodo.config/v1`:

```toml
schema = "hyodo.config/v1"

[audience]
profile = "vibe"       # "vibe" | "engineer" | "professional"
domain = "law"          # optional, professional only
```

`hyodo start` writes this file for you: run interactively, it asks exactly
one question ("Who is reading these results? 1 vibe coder, 2 engineer,
3 professional (law/accounting)") and writes the file only on an explicit
answer. Run non-interactively (no TTY on stdin), it asks nothing and writes
nothing — it prints the flag/env/config alternatives instead.

## What a profile touches, and what it never touches

Touches wording only:

- the verdict line (`hyodo/verdict.py:render_verdict_line`)
- `--explain` text (`hyodo/verdict.py:explain_decision`,
  `EXPLANATIONS_VIBE`, `EXPLANATIONS_PROFESSIONAL`)
- the six-virtue label set exposed as data in
  `hyodo/audience.py:VIRTUE_LABELS` (for a future `--explain` header and
  dashboard column-header source — not wired into either surface by this
  change; `hyodo/dashboard.py:PILLAR_SPECS` is unmodified)

Never touches: the decision itself, exit codes, `rule_id`s, coverage
figures, evidence references, or (beyond the one added key) `--json`
payload content.
