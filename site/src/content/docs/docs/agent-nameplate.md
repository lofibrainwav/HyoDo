---
title: Agent Nameplate v1
description: Provenance-only identity for a harness-assigned agent activity.
---

# Agent Nameplate v1

HyoDo's agent nameplate is a provenance receipt, not an authority credential.
It identifies the harness-assigned role and binds the observation to one exact
artifact SHA.

The public schema is available at
[`agent-nameplate-v1.schema.json`](/schemas/agent-nameplate-v1.schema.json),
with its exact-byte digest in
[`agent-nameplate-v1.pin.json`](/schemas/agent-nameplate-v1.pin.json).

The nameplate keeps `actor_id` compatible with `hyodo.agent-event/v1` and keeps
it as an opaque correlation label. It does not authenticate an actor. Runtime
identity, GitHub actor, and human authority remain separate concepts.
