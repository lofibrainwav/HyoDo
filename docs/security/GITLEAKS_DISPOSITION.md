# Historical gitleaks disposition register

Status: **OPEN — owner confirmation required**
Scan date: **2026-09-13 PT**
Scanner: **gitleaks 8.30.1**
Scope: **603 reachable commits in the current checkout**
Secret values: **intentionally excluded**

This register is the safe review index for the current 16 gitleaks findings.
It contains metadata only. A row may be closed only after the credential owner
confirms whether the match is synthetic, was rotated, or requires removal and
fresh history/artifact verification.

| ID | Rule | Path | Commit | Line | Provisional review note | Owner disposition |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `aws-access-token` | `tests/test_inspect.py` | `ca18cf43cbfd656a36783aa84c3b60be7ef95096` | 29 | Test fixture; owner-authorized synthetic classification | `SYNTHETIC` |
| 2 | `aws-access-token` | `tests/test_observability_contracts.py` | `caa88250b5786689667d936e3e375ace1c0f5a57` | 45 | Test fixture; owner-authorized synthetic classification | `SYNTHETIC` |
| 3 | `aws-access-token` | `tests/test_observability_contracts.py` | `caa88250b5786689667d936e3e375ace1c0f5a57` | 49 | Test fixture; owner-authorized synthetic classification | `SYNTHETIC` |
| 4 | `aws-access-token` | `tests/test_observability_contracts.py` | `caa88250b5786689667d936e3e375ace1c0f5a57` | 62 | Test fixture; owner-authorized synthetic classification | `SYNTHETIC` |
| 5 | `aws-access-token` | `tests/test_observability_contracts.py` | `caa88250b5786689667d936e3e375ace1c0f5a57` | 66 | Test fixture; owner-authorized synthetic classification | `SYNTHETIC` |
| 6 | `aws-access-token` | `tests/test_mcp_stdio.py` | `931be769b8d0f526b15af977d4a8bc6fb7611d56` | 109 | Test fixture; owner-authorized synthetic classification | `SYNTHETIC` |
| 7 | `generic-api-key` | `hyodo/cli/main.py` | `e7c6ba7c3a83a1aedcbde65fc72758a744138d96` | 350 | Non-secret identifier; owner-authorized synthetic classification | `SYNTHETIC` |
| 8 | `aws-access-token` | `tests/test_safe_json.py` | `d8c5df139a63aaacf1cb82fe63c72683dad6b40e` | 22 | Test fixture; owner-authorized synthetic classification | `SYNTHETIC` |
| 9 | `generic-api-key` | `afo_core/.env.example` | `f897f82253862ca6b2e27ba8e78cc17014205dfa` | 50-51 | Historical advisory tree; validity unknown | `PENDING_OWNER` |
| 10 | `generic-api-key` | `afo_core/data/api_wallet.json` | `f897f82253862ca6b2e27ba8e78cc17014205dfa` | 6 | Historical wallet material; validity unknown | `PENDING_OWNER` |
| 11 | `generic-api-key` | `afo_core/data/api_wallet.json` | `f897f82253862ca6b2e27ba8e78cc17014205dfa` | 19 | Historical wallet material; validity unknown | `PENDING_OWNER` |
| 12 | `generic-api-key` | `afo_core/tests/test_api_wallet.py` | `f897f82253862ca6b2e27ba8e78cc17014205dfa` | 41 | Historical test fixture; owner-authorized synthetic classification | `SYNTHETIC` |
| 13 | `generic-api-key` | `afo_core/tests/infrastructure/test_messaging.py` | `f897f82253862ca6b2e27ba8e78cc17014205dfa` | 115 | Historical test fixture; owner-authorized synthetic classification | `SYNTHETIC` |
| 14 | `generic-api-key` | `scripts/cleanup/purge_dns.sh` | `f897f82253862ca6b2e27ba8e78cc17014205dfa` | 3 | Historical script material; validity unknown | `PENDING_OWNER` |
| 15 | `generic-api-key` | `scripts/monitor_bridge.py` | `f897f82253862ca6b2e27ba8e78cc17014205dfa` | 61 | Historical script material; validity unknown | `PENDING_OWNER` |
| 16 | `generic-api-key` | `scripts/verify_context_chain.py` | `f897f82253862ca6b2e27ba8e78cc17014205dfa` | 6 | Historical script material; validity unknown | `PENDING_OWNER` |

## Closure protocol

For each row, the owner must record one of:

- `SYNTHETIC` — demonstrably non-usable fixture, with the reason;
- `ROTATED` — credential was revoked/rotated, with a private receipt reference;
- `REMOVED_AND_VERIFIED` — history/artifacts were handled under explicit
  repository-owner approval and a fresh scan found no unexplained match.

Do not add raw values, populated environment files, or scanner JSON containing
secret material to this repository. The full redacted scanner receipt belongs
outside the repository and should be access-controlled.

The current scan is **not clean** until all rows have an owner disposition and
the appropriate fresh-ref/artifact scans have been performed.
