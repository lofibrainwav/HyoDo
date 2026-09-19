# Unified doctrine: adversarial review receipt

Scope: the [replacement runbook](./hyodo-unified-doctrine-orchestration-runbook.md),
its offline state contract and the existing evidence/release consumers it names.
This is a dated review record, not a new operational state source or authority.
Measured on 2026-09-19 UTC (2026-09-18 America/Los_Angeles).
Base inspected: `629531279357f762df868e4bf2ffca4e924d0a65` in `hyung-2`,
branch `feat/five-lens-aperture`. Changes are local and have not been published.

## Reproduced defects and repairs

The tests were first run against the existing code, then rerun after fixes.

| Finding | Before | Repair / regression evidence |
| --- | --- | --- |
| Admission decision type | Array/object caused an uncaught TypeError | Reject non-string enum inputs; CLI returns structured exit 2 and creates no ledger. |
| Admission numeric/opaque payload | NaN/infinity accepted; non-JSON identity failed during append | Reject non-finite scores and serialize with strict JSON before opening a file; existing ledger bytes remain unchanged. |
| Orchestration enum types | Array/object in execution/state/join policy raised TypeError | Validate type before membership; invalid observations return false without writes. |
| Placeholder authorization | Whitespace/UNKNOWN/UNOBSERVED could authorize; identical missing heads looked matched | Reject absence markers independently of verifier approval and head equality. Host grant authentication remains outside this gate. |
| Skipped CI promotion | All-skipped CI returned PASS; skipped counted as passed | Count skipped separately; require an observed successful check. This does not substitute for the host's required-check policy. |
| Campaign dependency ambiguity | Diagram suggested fix and verification could run together | Serialize dependent L5 → L6; scope-required checks cannot be skipped. |

Red controls: admission tests reproduced **7 failures**, orchestration enum
tests **6 failures**, release gate/CI tests **12 failures**. These 25 failing
regression cases are not 25 distinct vulnerabilities.
Removing each of the offline schema's eight semantic guards independently
allows at least one negative fixture through; the mutation controls catch all
eight removals. No mutable production schema or new host resolver was added.

## Original finding reconciliation

| Original finding | Local reconciliation | Remaining boundary |
| --- | --- | --- |
| AV-01 | Seven separate reporting axes; no shared status; missing axes rejected | Existing product formats are not silently migrated. |
| AV-02 | Inventory of observations, evidence plate, attestation and release receipt/consumer | No new decision-bearing primitive. |
| AV-03 | Four-step default; dependent campaign fix/verify serialized | Campaign is opt-in, not a default tax. |
| AV-04 | Concern-specific triggers; no mandatory issue number or cleanup | Host selector automation is not implemented here. |
| AV-05 | Five conjunctive projection conditions; no consumer means DO NOT BUILD | No new public-state producer or consumer. |
| AV-06 | Reuse valid authority; reject placeholder references and changed heads in existing release gate | General delegated-host resolver unobserved. |
| AV-07 | Product/research lifecycle separation stated and preserved by this change | No research validation or release publication claimed. |
| AV-08 | Resolution/disposition separated; unresolved/held ordinary execution rejected | Exception references still require host authentication. |
| AV-09 | Dictionary/schema consistency, positive/negative fixtures, eight guard mutation controls | Offline schema only; no live adoption inferred. |
| AV-10 | Five named owner-specific record meanings; verifier cannot replace authority | Adoption, execution and served-target readback remain separate. |

## Twelve-case readback

AUTOMATED means a local executable test of the named boundary. REVIEWED means
the rule was checked in the document and applied to this task, not that a
production host selector was executed. UNOBSERVED remains an explicit limit.

| Case | Disposition and evidence |
| --- | --- |
| Partial evidence | AUTOMATED: PARTIAL fixture is representable; missing supporting reference is rejected. No authority is synthesized. |
| Conflicting observations | AUTOMATED: CONFLICTING needs two distinct references; duplicate/missing references rejected. Cause remains unspecified. |
| Derived claim | AUTOMATED: DERIVED stays on its own axis; a separately observed public surface requires its own reference. Validation does not transform the input. |
| Human decision required | AUTOMATED: HUMAN_REQUIRED with executable disposition rejected; approved verifier alone cannot satisfy the release authority gate. |
| Existing delegated authority | PARTIAL: explicit exact-head release reference is reused; mismatch/placeholders rejected. General owner/scope/expiry/revocation resolver **UNOBSERVED**. Fixture expired/revoked references remain structurally valid to expose this limit. |
| No public-state consumer | REVIEWED: no new public-state format/file/job built. The sole consumer of the runbook schema is its offline test. |
| No issue input | REVIEWED: no issue-specific lane was activated or issue number made mandatory. |
| No privacy concern | REVIEWED: no privacy specialist lane activated for this bounded repair. No private content was gathered. |
| Unknown stale-branch owner | REVIEWED: worktree/ref identity inspected; no cleanup, reset, rebase or ownership claim. |
| Incomplete research | REVIEWED: no research milestone or release version changed; product and research closure remain separate. |
| External reproduction unavailable | AUTOMATED representation: UNOBSERVED/HOLD/BLOCKED is accepted; HOLD cannot use ordinary execution disposition. Live host reproduction remains **UNOBSERVED**. |
| Another seat has dirty changes | AUTOMATED isolated Git fixture: independent verifier blocks a dirty candidate and preserves tracked/untracked bytes and Git status. Full package checks run in a separate owned copy. No production seat is cleaned. |

## Small-change walkthrough

OBSERVE: the campaign diagram forked L5/L6 despite prose requiring ordered
verification. RECONCILE: acceptance is an unambiguous fix-then-verify edge.
SMALLEST SAFE FIX: change that edge and clarify required checks. READBACK:
inspect the revised diagram, local links and state dictionary test. This uses
the existing user instruction for local repair; no duplicate approval, issue,
specialist, branch cleanup or research dependency is introduced.

## Verification and closure

| Check actually run | Observed result |
| --- | --- |
| Focused nine-file regression suite listed in the runbook | 164 passed, no skips |
| `bash scripts/verify-public.sh` in the isolated copy | Exit 0; final `PASS: public package verify` marker |
| Full public pytest with `HYODO_SBOM_INTEGRATION=1` | 1,748 passed in 93.09 seconds; no skips |
| Full Ruff / format / Pyright | Passed; Pyright 0 errors and 0 warnings |
| Version sync, shell syntax, wheel/sdist build, Twine, distribution scope | Passed; source version remains 4.19.8, no publication |
| Wheel installation and import smoke | Passed from its separate installation |
| Installed-wheel admission attacks | Five invalid inputs rejected with exit 2 and no target directory; valid input recorded with exit 0 and no execution claim |
| CLI checkout / empty-project / safety / claim checks | Passed; four checkout gates executed; empty project returned exit 2 |
| CLI's separate pytest invocation | 1,747 passed, 1 skipped; SBOM integration is opt-in in this invocation and was executed in the full run above |
| Local documentation links / diff whitespace | 22 links resolve; tracked and new-file whitespace checks passed |
| Candidate identity | Tested code, schema and fixture hashes still match the local files; base HEAD and branch unchanged |

The full log and tested-file manifest are retained in the owned temporary
verification directory:
`/var/folders/mp/7m5m295d1jb17rnk1j9761xh0000gn/T/hyodo-doctrine-verify-ezvmjj24/`.
`verify-public.log` is the command log; `candidate-manifest.json` binds the code
and fixtures to the inspected base. This report and PR prose were finalized
after that run; they do not alter tested executable behavior.

Local repair and review preparation are complete. General delegated-host
integration, live external reproduction and SSOT promotion remain explicitly
unobserved/not adopted. The [PR draft](./hyodo-unified-doctrine-pr-draft.md) is
prepared locally; no GitHub PR, push, merge or deployment was performed.

Contract adoption, remote PR/CI, deployment and general delegated-host behavior
are separate from this local repair. Do not infer SSOT_GREEN, published package
state or research validation from this review.
