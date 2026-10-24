# Exact-artifact handoff evidence gate (local candidate)

`hyodo report` READY means report rendering succeeded, NOT work verified. Use the separate read-only `hyodo handoff` command before delivering a verified result. It executes no agents and never authorizes sending, filing, signing, purchasing or deployment.

## Contract

A trusted caller supplies `--root`, `--plan`, an **out-of-band** `--plan-sha256`, a fresh `--run-id`, and a new `--receipt` path. Exit 0 requires `VERIFIED_EVIDENCE` in stdout AND the persisted/read-back receipt. Every other outcome is HOLD/exit 2. The caller must withhold the deliverable on any error, timeout, absent binary, absent/changed receipt, or incomplete checks. Re-run against the current bytes at the actual delivery boundary; do not authorize from an older receipt alone.

Plan schema `hyodo.handoff-plan/v1` has exactly: `schema`, `kind`, `run_id`, `created_at` (Unix seconds), `max_age_seconds` (positive, <=86400), `producer` (canonical nonempty identity), `artifacts`, `checks`. Artifact entries are exactly `{path, sha256, role}` where role is source or output; both roles are mandatory. Paths are relative to root and no symlinks or special files are followed. The gate does not read client files unless the caller explicitly includes them; prefer local approved sources and minimized aliases. Reads are bounded at 2 MB per file.

Check references are exactly `{id, path, sha256}`. Each observation is exactly `{schema:"hyodo.handoff-check/v1", id, run_id, status:"PASS", coverage:"OBSERVED", exit_code:0, observed_at, producer, artifact_digests}`. `artifact_digests` must equal the complete plan artifact map. Timestamps must follow plan creation, not exceed current time and remain within the configured age. Unknown/contradictory fields, duplicate JSON keys, booleans used as exit codes and nonfinite values are rejected. All inputs are read again before returning success. The CLI persists final HOLD if reinspection fails, then reads the receipt back.

Required IDs:
- code: tests, security, execution
- accounting: source, recalculation, reconciliation, review
- document: source, completeness, review

Additional checks are allowed but must also pass. Review producer must differ from plan producer. Whitespace identities are rejected. The trusted caller is responsible for authentic identities and professionally sufficient check scope; string differences are not identity authentication.

## Trust and limits

Checks must be observations of actual trusted tool runs. A builder writing PASS files and hashing them is NOT execution evidence. The plan pin and run id must come from a separate trusted caller, not an adjacent editable checksum file. Same-account writable files cannot supply a protected execution attestation or withstand a malicious operator replacing both verifier and trust anchor. This candidate makes no such claim. Arithmetic/source/review observations do not establish substantive tax/legal correctness by themselves.

There is **no built-in automatic Aside/Hermes final-message interception in this patch**. A host caller must invoke this command, inspect exit/stdout/receipt together and withhold the exact final artifact on HOLD. Existing scheduled safety scans are not this final handoff gate. Customer production handoff is not enabled merely by installing this CLI. No customer source or approved real document was supplied for production validation.

## Safety coverage changes

`safe --strict` now returns 2 for non-FULL coverage, in both text and JSON; advisory mode remains advisory. A capped `collect_scan_corpus` continues directory listing without reading later bodies and returns `error:partial:...` when entries were omitted. Unlistable subtrees after the cap return `error:read:...`. Omitted count is conservative and can include binary files, not a claim of text eligibility. Existing exclusions and bounded body reads are unchanged. Single-file scans retain the existing explicit user-named path contract. Text larger than the 200 KB body cap is now a read error/UNOBSERVED, not a silently truncated FULL scan. FULL coverage still does not claim a full SAST or professional review.

Regression tests cover 41st-file hazards, late listing errors, empty trees, outside links, missing/failed/timeout/partial observations, deleted/stale/replayed records, changed sources/output, missing review and sources, inconsistent reconciliation, duplicate keys, unknown failures, reviewer whitespace, FIFOs and mutation during final CLI reinspection.

## Deployment

This is a local candidate based on upstream 7b96cc61 (4.22.3), plus locally tested patches from open PRs 565, 566, 567 and 568. It is not a new official release and these PRs are not reported merged. The old editable 4.8.2 checkout and its four edits are preserved separately. Upgrade/binding and rollback must preserve existing professional and external-action approvals. No new service, provider or schedule is required.
