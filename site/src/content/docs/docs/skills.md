---
title: Skills
description: Ingest a project's own skill files as a lens over the six pillars — deterministic, no model, no embeddings.
---

## What it does

`hyodo skills` treats a skill (a Markdown file with `- ` rule bullets) as a
lens rather than a menu. `ingest` records a source and compiles its rules
into `.hyodo/skills/manifest.json`; `lens` re-parses every ingested source
live and reports, per pillar, an integer `observed / expected` coverage
count and a `passed / observed` coherence count; `propose` renders a
tailored skill made of the rules that currently pass. Everything is pure
stdlib, re-derived from the source file each run — no model, no RAG, no
embeddings, no vector store anywhere in this feature.

```bash
hyodo skills ingest my-team/SKILL.md
hyodo skills lens
```

Only four rule-text prefixes compile into a mechanical, executed check
(`require file:`, `forbid pattern:`, `require pattern:`, `ruff:`); anything
else is advisory and listed under `unobserved`.

## What is stored

- Compiled rule ids, pillar assignment, and pass/fail state in
  `.hyodo/skills/manifest.json`.
- A `content_digest` and `status` (`"unreadable"` when a source cannot be
  read) for every ingested source.

## What is never stored

- A skill's raw body, unless `--store-body` is passed on `ingest`.
- A `url:` source's contents — only its domain is recorded; HyoDo never
  fetches a URL over the network in this package.
- A percentage, probability, or confidence value anywhere in a lens report.
- A vector or embedding from a `--from-node` research-node hand-off — only
  rule text, digests, and an ordinal `score_rank` are accepted; a `score` or
  `probability` field on a retrieved item is rejected outright.

## Exit codes

| Command | ALLOW | DENY | UNOBSERVED | ASK |
| --- | --- | --- | --- | --- |
| `skills ingest` | 0 | 1 | 2 | 3 |
| `skills lens` | 0 | n/a | 2 (malformed manifest) | n/a |
| `skills propose` | 0 | n/a | n/a | n/a |

Ingesting a skill is an unconditional external variable, like a web fetch —
it stays `ASK` at trust level 2 and only clears automatically at trust
level 3.

## Full reference

[docs/SKILLS.md](https://github.com/lofibrainwav/HyoDo/blob/main/docs/SKILLS.md)
in the repository covers rule ids, pillar keyword mapping, and the
research-node contract in full.

## Next

- [Inspect](/docs/inspect/)
- [Evidence Graph](/docs/evidence-graph/)
