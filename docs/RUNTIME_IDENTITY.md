# Runtime identity v1 contract

HyoDo's dashboard identity receipt uses the public schema
[`schemas/runtime-identity-v1.schema.json`](../schemas/runtime-identity-v1.schema.json).
The schema already rejects unknown fields and invalid protocol values; its
existing contract tests cover both a generated receipt and representative
drift.

## Verify the pinned schema

[`schemas/runtime-identity-v1.pin.json`](../schemas/runtime-identity-v1.pin.json)
is a checkout-independent verification surface. A consumer can fetch the two
JSON files, compute SHA-256 over the exact bytes of
`runtime-identity-v1.schema.json`, and compare it with the pin's `digest`.
No HyoDo Python import or runtime process is required.

```python
import hashlib
from pathlib import Path

schema = Path("runtime-identity-v1.schema.json")
expected = "41c5b35fc8a163c51cdbb3fa5a8f4e4099f59b6d5887eb799660e976d94e9961"
assert hashlib.sha256(schema.read_bytes()).hexdigest() == expected
```

The pin is for the exact schema bytes, not a parsed/re-serialized JSON value.
When the schema changes, update the digest and the focused contract tests in
the same change. This is a schema pin, not proof that a live dashboard is
running or that a receipt was observed; consumers must still validate the
receipt and assess its `observed_at`, provenance, and runtime fields.
