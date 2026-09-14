# Gitleaks owner disposition form

Status: **INPUT REQUIRED — not a closure receipt**

This form turns the findings in [`GITLEAKS_DISPOSITION.md`](./GITLEAKS_DISPOSITION.md)
into owner decisions. It does not classify a finding on the owner's behalf and
does not close the historical-secret gate.

## Allowed dispositions

- `SYNTHETIC`: the owner confirms the value is deliberately unusable fixture
  data and records the reason.
- `ROTATED`: the owner confirms revocation or rotation and records a private
  receipt reference. Do not paste the credential or private receipt here.
- `REMOVED_AND_VERIFIED`: the owner explicitly approves history/artifact
  handling and records the fresh scan and artifact verification receipt.

If validity is uncertain, use the `ROTATED` path first. A likely false positive
is still `PENDING_OWNER` until the owner confirms it.

## Decision queue

| ID | Finding | Location | Owner decision | Required evidence |
| --- | --- | --- | --- | --- |
| 1 | `aws-access-token` | `tests/test_inspect.py:29` | `PENDING_OWNER` | Fixture reason or private rotation receipt |
| 2 | `aws-access-token` | `tests/test_observability_contracts.py:45` | `PENDING_OWNER` | Fixture reason or private rotation receipt |
| 3 | `aws-access-token` | `tests/test_observability_contracts.py:49` | `PENDING_OWNER` | Fixture reason or private rotation receipt |
| 4 | `aws-access-token` | `tests/test_observability_contracts.py:62` | `PENDING_OWNER` | Fixture reason or private rotation receipt |
| 5 | `aws-access-token` | `tests/test_observability_contracts.py:66` | `PENDING_OWNER` | Fixture reason or private rotation receipt |
| 6 | `aws-access-token` | `tests/test_mcp_stdio.py:109` | `PENDING_OWNER` | Fixture reason or private rotation receipt |
| 7 | `generic-api-key` | `hyodo/cli/main.py:350` | `PENDING_OWNER` | Identifier confirmation or private rotation receipt |
| 8 | `aws-access-token` | `tests/test_safe_json.py:22` | `PENDING_OWNER` | Fixture reason or private rotation receipt |
| 9 | `generic-api-key` | `afo_core/.env.example:50-51` | `PENDING_OWNER` | Rotation/verification receipt; historical validity unknown |
| 10 | `generic-api-key` | `afo_core/data/api_wallet.json:6` | `PENDING_OWNER` | Rotation/verification receipt; historical validity unknown |
| 11 | `generic-api-key` | `afo_core/data/api_wallet.json:19` | `PENDING_OWNER` | Rotation/verification receipt; historical validity unknown |
| 12 | `generic-api-key` | `afo_core/tests/test_api_wallet.py:41` | `PENDING_OWNER` | Fixture reason or private rotation receipt |
| 13 | `generic-api-key` | `afo_core/tests/infrastructure/test_messaging.py:115` | `PENDING_OWNER` | Fixture reason or private rotation receipt |
| 14 | `generic-api-key` | `scripts/cleanup/purge_dns.sh:3` | `PENDING_OWNER` | Rotation/verification receipt; historical validity unknown |
| 15 | `generic-api-key` | `scripts/monitor_bridge.py:61` | `PENDING_OWNER` | Rotation/verification receipt; historical validity unknown |
| 16 | `generic-api-key` | `scripts/verify_context_chain.py:6` | `PENDING_OWNER` | Rotation/verification receipt; historical validity unknown |

## Owner response

Return one disposition per ID, for example:

```text
1=SYNTHETIC — unit-test fixture; never issued and intentionally invalid
2=ROTATED — private receipt: <reference>
...
```

After all 16 decisions are recorded, update the disposition register, run a
fresh redacted historical scan on the exact candidate SHA, and attach the
resulting receipt. Until that sequence completes, the security gate remains
`HOLD`.
