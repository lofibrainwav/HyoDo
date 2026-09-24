# HyoDo documentation

Public documentation is written in English. Start with the product overview,
then use the focused reference that matches your task. Source version is in the
root `VERSION` file; the dated measured-state snapshot and published-package
limits are in [Current State](./CURRENT_STATE.md).

## Getting started

- [Product overview](../README.md) — purpose, main surfaces, and boundaries.
- [Quick Start](../QUICK_START.md) — install and run the first checks.
- [Onboarding](./ONBOARDING.md) — `hyodo start`, MCP host setup, and support status.
- [Node.js onboarding](./onboarding-nodejs.md) — Node project setup.
- [Gate syntax](./GATES_SYNTAX.md) — `.hyodo/gates.toml` fields and validation.

## Security and trust

- [Security policy](../SECURITY.md) — reporting and security commitments.
- [Trust boundary](./TRUST_BOUNDARY.md) — what HyoDo trusts in a checkout;
  upgrading to 4.21.7.
- [Product boundary](./PRODUCT_BOUNDARY.md) — HyoDo and host responsibilities.
- [Policy trust](./POLICY_TRUST.md) — policy sources and trust levels.
- [Misread guide](./MISREAD.md) — common incorrect interpretations.
- [Full-body consent](./FULL_BODY.md) — payload handling and consent limits.
- [Public claims](./CLAIMS.md) — scope of public product claims.
- [Security surface](./SECURITY_SURFACE.md) — exposed package and service surface.

## Integrations and evidence

- [Intent review](./INTENT_REVIEW_V1.md) — attributed requirement comparisons
  and their limits.

- [Connect](./CONNECT.md) — hooks, pre-commit, GitHub Actions, and shadow mode.
- [Host adapters](./HOST_ADAPTERS.md) — native adapter and live-canary boundary.
- [Host observation contract](./HOST_OBSERVATION_CONTRACT.md) — what the
  adapters record, what they leave unrecorded, and which gaps are closable.
- [MCP design](./HYODO_MCP_CONNECTOR_DESIGN.md) — local connector and remote contract.
- [MCP reader cutover](./MCP_READER_CUTOVER.md) — reader self-registration,
  stale-pin refusal, and the promotion census.
- [Remote MCP contract](./M5_REMOTE_CONNECTOR_CONTRACT.md) — hosted endpoint is
  contract-only; it is not `hyodo mcp stdio`.
- [Measurement provenance](./MEASUREMENT_PROVENANCE.md) — what measured which target.
- [Runtime identity](./RUNTIME_IDENTITY.md) — checkout-independent runtime identity.
- [Retrieval provenance](./RETRIEVAL_PROVENANCE.md) — bounded retrieval
  receipt contract.
- [Test integrity](./TEST_INTEGRITY.md) — strict test-integrity checks.
- [Score derivation](./SCORE_DERIVATION.md) — score inputs and coverage semantics.
- [Verification view](./VERIFICATION_VIEW_V0.md) — read-only investigation
  projection of one evidence graph; carries no score and no authority.

## Project status and contributor workflow

- [Current State](./CURRENT_STATE.md) — measured source and published status.
- [Remaining work and handoff](./REMAINING_WORK.md) — open work, responsible
  roles, completion evidence, and the external-host handoff boundary.
- [External Claim Audit](./EXTERNAL_CLAIM_AUDIT.md) — evidence for external claims.
- [Convergence workflow](./CONVERGENCE_WORKFLOW.md) — parallel research
  and safe integration.
- [Implementer notes](./CODEX_HANDOFF_NEXT.md) — current-truth notes, not a
  4.4.0 rebuild queue.
- [Release checklist](../RELEASE_CHECKLIST.md) — release gates and evidence.
- [Changelog](../CHANGELOG.md) — user-visible release history.
- [Research index](./research/README.md) — proposals, experiments, and
  historical receipts.
- [Release notes](./releases/) — detailed release records.

Other focused references, research notes, and historical plans remain in this
directory; browse by filename when you need a specialized topic.
