# Safe HyoDo change integration

Use one coordinator and one writer per checkout. A successful scan, report READY or old CI run is not evidence for a different tree.

1. Read the live default command, immutable package binding, current upstream main SHA, open pull requests and child/base relationships. Preserve local edits and the previous working runtime. Never reset or overwrite another writer's checkout.
2. Develop and merge in a separate checkout. Integrate the latest main without force-pushing shared branches. Preserve compatible work; resolve conflicts explicitly and review the resulting diff, not just each original patch.
3. Run targeted negative tests, full regression tests, lint, formatting and type checks against the exact candidate. Obtain an independent review. Record exact source/artifact hashes and distinguish skipped, unavailable and passed checks.
4. Before publishing, fetch main again. If it moved, integrate and retest; do not reuse a success receipt for the old tree. Keep branch protection and required CI checks enabled. The existing strict required-status policy rejects an out-of-date merge candidate.
5. Publish only the reviewed scope after the operator's required confirmation. Use an exact head SHA for merging, with no admin override. Merge only after required checks pass on that head/current base. Re-read the resulting main and verify its tests and actual code after merge.
6. **Do not delete a merged branch while an open pull request still uses it as its base.** Retarget and verify dependent PRs first. Deleting their base can automatically close them without merging their fixes. A closed PR is not evidence that its code landed. Repository automatic branch deletion should remain off unless a separately reviewed dependency-aware process exists.
7. Close a superseded issue/PR only after reading back the equivalent code and regression tests in main. Keep the replacement link and distinguish superseded closure from an actual merge. Do not delete source branches as routine cleanup.
8. Build an immutable runtime from verified source. Promote only the approved command/config bindings, then re-read the default command and package hashes and run the existing strict checker without delivery. Keep source pins, findings baselines, schedules and unrelated settings unchanged.
9. Check a fresh task and minimal noninteractive environment. A dry run is not a naturally scheduled execution. Keep unresolved source/professional/host enforcement gaps explicit, and retain rollback evidence.

## Final-delivery boundary

`hyodo handoff` is a read-only exact-evidence checker. A trusted caller must withhold the exact output on missing, stale, partial or failed evidence and must not infer authority from `report` READY, scanner PASS or a receipt alone. Hashes in the same writable account are not authenticated execution attestation.

A host's streaming, intermediate messages, attachments, speech, retry and replay paths must all pass through a supported fail-closed delivery gate before any work payload is released. A post-generation transform that can fail open cannot meet that contract. Instructions, transcript polling or wrapping a CLI do not intercept a native application's separate chat renderer. If the host lacks a supported pre-publication interface, report that capability as blocked; do not patch signed apps or weaken protections to claim completion.
