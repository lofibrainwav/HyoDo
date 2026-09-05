# Discoverability Research — 2026-09-05

## Status

Recovered research notes from a parallel analysis lane. This document is
separate from runtime, test, and release-gate changes so incomplete research
cannot dilute code-review scope.

## Measured launch examples

The earlier research pass compared public launch patterns for developer and
security tools. The useful directional finding was that concrete, measurable
claims tend to communicate better than generic category labels.

Examples reviewed included agent-security scanners, secret scanners, and
pre-commit-style tooling. The takeaway for HyoDo is not a guaranteed growth
formula; it is a messaging hypothesis to test:

- Lead with a specific behavior HyoDo proves.
- Avoid unsupported percentage or cost-savings claims.
- Prefer reproducible demonstrations over category adjectives.
- Treat launch-channel performance as external evidence, not product truth.

## Candidate distribution surfaces

Potential surfaces identified for later validation:

- Show HN-style launch post with a concrete demo claim
- Python community newsletters and link roundups
- curated agent-security and Claude Code lists
- pre-commit integration discovery
- GitHub Action discovery
- PyPI metadata and classifier cleanup

## Research gaps

The original lane timed out before completing several areas. They remain
explicitly unresolved rather than being presented as conclusions:

- PyPI keyword and trove-classifier optimization
- GitHub social-preview guidance
- docs-site versus README conversion evidence
- a consolidated launch experiment with success criteria

## Next validation step

Before changing public positioning, convert each candidate channel into a small
experiment with a measurable outcome and record the result. HyoDo should not
promote a distribution tactic from research note to product claim without a
receipt.
