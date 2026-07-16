# Security Patch Log

> **Status banner (2026-07-16):** This file is a **historical patch log**, not a live
> inventory. GitHub Dependabot open alerts on `afo_core/` lockfiles remain the
> operational SSOT for extended-tree vulnerabilities. Do not read older "all
> patched" sentences as current truth without a fresh readback.
>
> Public package surface (`hyodo/` + root `pyproject.toml`) is intentionally thin
> (`typer`, `rich`). See [`docs/SECURITY_SURFACE.md`](docs/SECURITY_SURFACE.md).

## How to verify current posture

```bash
# Public package
pip install -e ".[dev]"
hyodo check
hyodo safe

# Extended tree (advisory; noisy; not public release gate)
# pip-audit -r afo_core/requirements.txt
```

## 2026-07-16: Surface clarification (process)

| Action | Status |
|--------|--------|
| Separate public vs `afo_core` security surface in docs | Done |
| Replace score/CLI "auto-approve" overclaims with review-signal language | Done |
| Implement real early-warning `hyodo safe` scan (not fixed green output) | Done |
| Add Dependabot grouping for `afo_core` | Done |
| Mass upgrade of entire `afo_core` lock (litellm/chromadb/nltk/...) | **In progress / partial** |

## 2026-07-16: afo_core P0 lock refresh

| Package | From | To | Notes |
|---------|------|----|-------|
| litellm | 1.72.0 | 1.92.0 | Critical/high auth fixes |
| nltk | 3.9.2 | 3.10.0 | Critical path/zip issues |
| json-repair | 0.55.0 | 0.61.5 | High DoS |
| transformers | 4.57.6 | 5.12.1 | High RCE-class advisories |
| pypdf | 6.6.0 | 6.14.2 | Medium/high parser issues |
| python-multipart | 0.0.21 | 0.0.32 | High path/DoS |
| urllib3 | 2.6.3 | 2.7.0 | High proxy/header issues |
| cryptography | 46.0.3 | 49.0.0 | High openssl/wheel issues |
| langchain-core | 1.2.7 | 1.4.9 | High deserialization/path |

Structural:
- poetry.lock regenerated (SSOT)
- requirements.txt re-exported from lock
- requirements-lock.txt removed (duplicate surface)
- crewai / moviepy removed from optional stack (security pin conflicts)

Residual: chromadb 1.4.1 may still carry unpatched critical advisory until upstream ships a safe release.

## 2026-02-10: Critical Vulnerability Updates (historical)

### Updated Packages

| Package | CVE | Severity | From | To | Status (as of 2026-02-10) |
|---------|-----|----------|------|-----|---------------------------|
| langsmith | CVE-2026-25528 | Medium | 0.5.2 | 0.6.3 | Recorded patched |
| pypdf | CVE-2026-24688, CVE-2026-22691, CVE-2026-22690 | Medium/Low | 6.5.0 | 6.6.2 | Recorded patched |
| python-multipart | CVE-2026-24486 | High | 0.0.21 | 0.0.22 | Recorded patched |
| protobuf | CVE-2026-0994 | High | < 5.29.6 | 5.29.6 | Recorded patched |
| urllib3 | CVE-2026-21441 | High | < 2.6.3 | 2.6.3 | Recorded already patched |

### Notes

Later Dependabot findings may re-open or supersede these rows (new CVEs, new
transitive deps, or lockfile drift). Always re-check GitHub Security alerts
before claiming a clean tree.
