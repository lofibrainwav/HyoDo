# Evidence Pack v1 — local candidate seal

## Status

`MEASURED / LOCAL-CANDIDATE / RELEASE-CHAIN-HOLD`

This pack seals the Run #3 measurement artifacts by content hash. It does not
claim that HyoDo 4.18.0 has been published. The release-chain status stays
explicitly separate until a signed verified tag, published wheel/sdist, SBOM,
and PyPI provenance are read back.

## Sealed inputs

- HyoDo candidate HEAD: `034a189610c0b237a18fcb17a9fafbe4a89098b6`
- KINGDOM source HEAD: `17fc4f5eccc1cebd14f023a15981c740a60b8f7c`
- Run receipt: `docs/research/MEASURED_RUN_3_2026-09-10.md`
- Ledger SHA-256: `579123cd1edc0a7246c0941cb87b9f087178ed0dbf26dacdb3a03d08d4c05ae7`
- Graph SHA-256: `fe0d082a42cd941bd297a5c706cd83927fbe3c202047d414e504d9355ce4c9fb`
- Candidate wheel SHA-256: `a853ac36c784049a98e6c7d3120644160aea3a47c2d8c7016e0819922b42272d`

## Acceptance readback

| Contract | Status | Readback |
| --- | --- | --- |
| HyoDo candidate installed | MEASURED | `HyoDo v4.18.0` from isolated venv |
| KINGDOM Run #3 | MEASURED | 16 ledger events, 0 corrupt lines |
| serial / parallel / join | MEASURED | tags and join evidence refs present |
| retry / wait / rework | MEASURED | exit 1→0, 204 ms wait, rework tag |
| human intervention | MEASURED | actor `human` event present |
| unresolved observation | MEASURED | sidecar unresolved dependency preserved |
| graph fidelity | MEASURED | 16/16 rendered, 9/9 edges, 0 collisions |
| signed tag | HOLD | not created |
| public wheel/sdist | HOLD | not published |
| SBOM | HOLD | not attached to a public release |
| PyPI provenance | HOLD | no public artifact provenance readback |
| clean install from PyPI | HOLD | only local candidate wheel was installed |

## Sealing rule

The local pack is valid for review because every included runtime artifact has
a SHA-256 readback and the graph renderer was tested against the exact graph
JSON. A future public-release closeout must append the signed tag, release
asset hashes, SBOM hash, PyPI provenance URLs/attestations, and a clean-install
receipt; it must not overwrite these local measurements.
