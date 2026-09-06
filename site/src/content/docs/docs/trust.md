---
title: Trust
description: HyoDo's honest boundaries, verbatim, plus what backs the release pipeline.
---

## Honest boundaries

HyoDo is deliberately narrow:

- It is **not** a runtime sandbox or process interceptor.
- `hyodo safe` is an early-warning scanner, not a full security audit.
- A DENY result must still be enforced by the caller.
- HYOGOOK V5 (formula; philosophy V6) is a review signal, never approval.
- The public MCP server supports loopback or authenticated Tailscale binding;
  public `0.0.0.0` listeners are not supported.
- Missing, unreadable, or unmeasured evidence is never reported as healthy.

That scope is intentional: the tool should be useful locally without requiring
a hosted service, model provider, or remote control plane.

## What backs the release

- **Local-first.** No hosted service and no model provider are required to
  run `hyodo safe`, `hyodo init`, or `hyodo check` against your repository.
- **PyPI Trusted Publishing.** Releases publish via OIDC — there is no
  long-lived PyPI API token stored as a repository secret — with build
  provenance/attestation generated for the published artifacts.
- **SBOM on release.** A CycloneDX SBOM of the public runtime surface is
  generated and checked for scope and reproducibility.
- **SARIF output.** `hyodo report --format sarif` writes a SARIF 2.1.0
  visibility report for measured DENY and unreadable-ledger conditions.
- **Pre-commit hooks.** `hyodo-check` and `hyodo-safe-strict` are available
  as pre-commit hooks on signed releases.
- **MCP loopback / Tailscale only.** The optional MCP adapter binds to
  `127.0.0.1` (loopback) or an authenticated private Tailscale address; no
  public `0.0.0.0` listener is supported.

See [SECURITY.md](https://github.com/lofibrainwav/HyoDo/blob/main/SECURITY.md)
for vulnerability reporting and keyword safety gates, and
[docs/SECURITY_SURFACE.md](https://github.com/lofibrainwav/HyoDo/blob/main/docs/SECURITY_SURFACE.md)
for the full security surface this page summarizes.

## Next

- [Why HyoDo](/docs/why-hyodo/)
- [Quickstart](/docs/quickstart/)
