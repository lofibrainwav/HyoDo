---
title: Graph Export
description: Write the agent-event ledger's structure out as a Zettelkasten-shaped bridge file — ids, links, and clusters, never bodies.
---

## What it does

`hyodo graph export` writes the ledger's structure — atomic event ids,
parent chains, evidence links, and pillar clusters — as one JSON file an
external note system can turn into permanent notes. It mirrors `hyodo
report --format graph`'s own node/edge shape and adds a `backlinks` index
(the reverse of every `evidence_refs` entry) and pillar `clusters`. It also
powers the local evidence-graph viewer's per-actor "rings" drill-down
(skills, memory, routines, tools) for each row.

```bash
hyodo graph export --out .hyodo/graph.json --yes
```

By default the command asks before writing, mirroring `hyodo connect`'s
consent pattern; `--yes` skips the prompt for scripted callers.

## What is stored

- Node/edge ids, `actor_id` labels, and pillar `clusters` — the same shape
  `hyodo report --format graph` already emits.
- A `backlinks` map of `{cited_event_id: [citing_event_id, ...]}`.
- Per-actor rings built only from the local ledger and local manifests
  (`.hyodo/skills/manifest.json`, `.hyodo/chunks-manifest.json`,
  `.hyodo/connect.json`) — never the network.

## What is never stored

- Event bodies, chunk text, or embeddings — only ids, parents, refs,
  claims, and clusters cross this bridge.
- A score, probability, or confidence value in any node, edge, or cluster.
- Anything read back from an external note system — this is a one-way
  export, not a sync target.

## Exit codes

| Outcome | Exit |
| --- | --- |
| Export written | 0 |
| Confirmation declined without `--yes` | 1 |
| Ledger unreadable, or the write itself failed | 2 |

An empty or pre-1-B ledger still exports successfully with empty
`nodes`/`edges`/`backlinks` — an honestly empty graph is a valid graph.

## Full reference

[docs/GRAPH_EXPORT.md](https://github.com/lofibrainwav/HyoDo/blob/main/docs/GRAPH_EXPORT.md)
covers the actor-rings shape and cluster-assignment rules in full.

## Next

- [Evidence Graph](/docs/evidence-graph/)
- [Eye](/docs/eye/)
