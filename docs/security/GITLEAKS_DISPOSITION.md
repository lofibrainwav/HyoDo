# Historical gitleaks disposition register

Status: **RECONCILED — historical residuals recorded; no unexplained current/active finding observed**
Scan date: **2026-09-13 PT**
Scanner: **gitleaks 8.30.1**
Scope: **603 reachable commits in the current checkout**
Secret values: **intentionally excluded**

This register preserves the 2026-09-13 scan snapshot while reconciling it with
the current 2026-09-20 `.gitleaksignore` disposition. It contains metadata only
and never raw secret values. The repository history is not clean: documented
historical matches remain reachable. The current working-tree/full-history
scan is green only because these narrow, documented historical baselines are
accepted; that does not make the history clean.

The current evidence is precise: no unexplained current or active credential
finding was observed. Historical residuals are not treated as active
credentials, and C2/C3 are not described as revoked because their owners and
validation endpoints are unavailable.

| Group | Findings | Disposition |
| --- | --- | --- |
| 13 historical test/fixture/non-secret matches | The fixture and identifier matches listed in the 2026-09-13 snapshot | Accepted narrow historical baseline; not current/active credentials |
| C1 | Historical Cloudflare credential in `scripts/cleanup/purge_dns.sh` | Revoked by the operator; historical residual remains reachable |
| C2 | Historical external credential in `scripts/monitor_bridge.py` | Decommissioned consumer/project; owner unavailable; cannot be revoked or validated from current control; permanently exposed historical residual, not active |
| C3 | Historical external credential in `scripts/verify_context_chain.py` | Decommissioned consumer/project; owner unavailable; cannot be revoked or validated from current control; permanently exposed historical residual, not active |

The exact redacted fingerprints, paths, commits, and line numbers remain in
`.gitleaksignore`, which is the current disposition source. The 2026-09-13
row-level snapshot is retained as historical evidence rather than as a
current blanket owner-confirmation queue.

## Closure protocol

For any newly discovered or unexplained finding, the owner must record one of:

- `SYNTHETIC` — demonstrably non-usable fixture, with the reason;
- `ROTATED` — credential was revoked/rotated, with a private receipt reference;
- `REMOVED_AND_VERIFIED` — history/artifacts were handled under explicit
  repository-owner approval and a fresh scan found no unexplained match.

Do not add raw values, populated environment files, or scanner JSON containing
secret material to this repository. The full redacted scanner receipt belongs
outside the repository and should be access-controlled.

The current scan is not described as history-clean. It is **reconciled** only
because the narrow historical baselines and the three historical credential
residuals have explicit dispositions, while unexplained current/active
findings remain actionable.
