# Independent Verifier v0.1

`hyodo.independent-verifier/v1` is a read-only attestation about one exact
artifact. It is evidence, not authority. It cannot push, merge, approve, or
authorize.

The verifier receives the canonical checkout, an exact artifact SHA, a
harness-assigned verifier nameplate, and raw verification evidence. It does
not receive a builder verdict or builder confidence. This is the blind first
pass boundary.

Verdicts are `PASS`, `BLOCK`, and `UNOBSERVED`:

- `PASS`: exact SHA, clean checkout, verifier identity/session, and evidence
  were observed.
- `BLOCK`: a contradiction or forbidden authority/builder input was observed.
- `UNOBSERVED`: a required identity, checkout, or evidence fact could not be
  observed.

The implementation only invokes read-only Git queries. Human authority remains
outside this contract and must be recorded separately by the host.
