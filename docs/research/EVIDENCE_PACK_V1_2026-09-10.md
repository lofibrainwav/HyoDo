# Evidence Pack v1 — local candidate seal

## Status

`MEASURED / RELATION-CORRECTED / RELEASE-CHAIN-CLOSED`

This pack seals the Run #3 measurement artifacts by content hash. The
release-chain rows were `HOLD` when it was written, because 4.18.0 had not
been published yet. It has since been published, and the closeout below is
appended rather than written over the local measurements -- the sealing rule
at the end of this document requires exactly that.

The original Run #3 receipt is preserved for historical comparison. The
corrected-v2 receipt is the canonical relationship readback for this pack.

## Sealed inputs

- HyoDo candidate HEAD: `034a189610c0b237a18fcb17a9fafbe4a89098b6`
- KINGDOM source HEAD: `17fc4f5eccc1cebd14f023a15981c740a60b8f7c`
- Run receipt: `docs/research/MEASURED_RUN_3_2026-09-10.md`
- Corrected relationship receipt: `docs/research/MEASURED_RUN_3_CORRECTED_V2_2026-09-10.md`
- Ledger SHA-256: `579123cd1edc0a7246c0941cb87b9f087178ed0dbf26dacdb3a03d08d4c05ae7`
- Graph SHA-256: `fe0d082a42cd941bd297a5c706cd83927fbe3c202047d414e504d9355ce4c9fb`
- Candidate wheel SHA-256: `a853ac36c784049a98e6c7d3120644160aea3a47c2d8c7016e0819922b42272d`
- Corrected-v2 ledger SHA-256: `3bf6f4d9e5b765efa45b96863f01f97be860aaa2579cdaebb7dacd35144f99aa`
- Corrected-v2 graph SHA-256: `14532fac355814aa98c728a718d057214ba285fd1f0bff7e621ae732a408b992`

## Acceptance readback

| Contract | Status | Readback |
| --- | --- | --- |
| HyoDo candidate installed | MEASURED | `HyoDo v4.18.0` from isolated venv |
| KINGDOM Run #3 | MEASURED | original 16-event receipt preserved |
| Run #3 corrected relationships | MEASURED | 17 events, 21 edges, 16 parent links |
| serial / parallel / join | MEASURED | tags and join evidence refs present |
| retry / wait / rework | MEASURED | exit 1→0, 204 ms wait, rework tag |
| human intervention | MEASURED | actor `human` event present |
| unresolved observation | MEASURED | sidecar unresolved dependency preserved |
| graph fidelity | MEASURED | corrected-v2 renders 17 events and 21 edges |
| signed tag | HOLD | not created |
| public wheel/sdist | HOLD | not published |
| SBOM | HOLD | not attached to a public release |
| PyPI provenance | HOLD | no public artifact provenance readback |
| clean install from PyPI | HOLD | only local candidate wheel was installed |

## Public release closeout — 4.18.0

Appended 2026-09-10. The five `HOLD` rows above were measured against the
published artifacts; the local candidate measurements are untouched.

| Contract | Status | Readback |
| --- | --- | --- |
| signed tag | MEASURED | `v4.18.0` verifies: good signature for `lofibrainwav`, ED25519 key `SHA256:nae7KdoWdukaCa/+ZIGphTwapOI3bAJzJOOEvFFdAwE` |
| public wheel/sdist | MEASURED | PyPI `4.18.0` — wheel `9b7fc1a1a5546760290f9b9bde1872b0e6706d259ac22b2835ac927d1fea64a3`, sdist `274c715e47c61eec0d9017b76494c436d6fed4a5a8567197fcc842fd2ad4a40f` |
| SBOM | MEASURED | Release `v4.18.0` carries `sbom.cyclonedx.json` (21860 bytes) and `sbom.cyclonedx.json.sha256` recording `d3dbbfb1f8f99c1c0718962f98dfbc103ddf95b8662051edef659e780e468c2a` |
| PyPI provenance | MEASURED | attestation bundle, publisher GitHub `lofibrainwav/HyoDo` workflow `publish.yml` |
| clean install from PyPI | MEASURED | `pip install --no-cache-dir hyodo==4.18.0` in an empty venv reads back `HyoDo v4.18.0` from a neutral working directory |

The install readback was taken from outside any checkout on purpose. Running
it inside the repository puts the source tree on `sys.path` ahead of the
installed package, which measures the checkout rather than the artifact.

The candidate wheel hash recorded under "Sealed inputs" is the locally built
wheel and is not expected to equal the published wheel hash; the two were
produced by different builds.

## Sealing rule

The local pack is valid for review because every included runtime artifact has
a SHA-256 readback and the graph renderer was tested against the exact graph
JSON. A future public-release closeout must append the signed tag, release
asset hashes, SBOM hash, PyPI provenance URLs/attestations, and a clean-install
receipt; it must not overwrite these local measurements.
