---
title: Runtime identity v1
description: The public runtime identity receipt schema and its exact digest pin.
---

# Runtime identity v1

HyoDo's dashboard identity receipt is defined by the public
[`runtime-identity-v1.schema.json`](/schemas/runtime-identity-v1.schema.json)
and its exact-byte
[`runtime-identity-v1.pin.json`](/schemas/runtime-identity-v1.pin.json).

Consumers can fetch those files directly from this site, compute SHA-256 over
the schema bytes, and compare the result with the pin. The pin is a schema
integrity check; it does not prove that a live dashboard is running or that a
receipt was observed.

The runtime endpoint is local/loopback infrastructure at `/api/identity` when
a HyoDo dashboard is running. A hosted site schema route and a local runtime
endpoint are separate surfaces: neither implies the other is live.
