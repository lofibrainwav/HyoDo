# Lane 1 — Discoverability Playbook (Recovered from subagent transcript)

**Status:** research subagent timed out at 600s / 26 API calls; key findings below
were recovered directly from the live transcript log
(`deleg_50a210aa/task-0.log`). Sections the subagent did not reach are marked
INCOMPLETE. Companion reports: `LANE2_ONBOARDING_TERMINOLOGY_UX.md`,
`2026-09-05-integration-surface-research.md`.

---

## 1. Hacker News launch data (Algolia API, measured 2026-09-05)

| Show HN post | Points | Comments | Pattern |
|---|---|---|---|
| "MCP-Scanner – Scan MCP Servers for vulnerabilities" (cisco-ai-defense) | **168** | 50 | Specific, measurable claim, concrete artifact |
| "cut grep tokens 42%" | 39 | — | Numeric, verifiable claim |
| "Show HN: Blacklight – secret scanner…" | 3 | 0 | Generic category pitch |
| "Show HN: Sambaudit, a secrets scanner for SMB…" | 2 | 0 | Generic category pitch |
| "Show HN: A pluggable secret scanner for code…" | 1 | 0 | Generic category pitch |

**Subagent's measured conclusion:** generic "guardrails/scanner" pitches land
1–5 points; specific measurable claims front-page. Launch title must lead with
a concrete claim (e.g. "fail-closed gates that block AI agents from faking
green"), never the category word.

## 2. Comparable-tool traction baselines (GitHub API, measured 2026-09-05)

| Repo | Stars | Created | Note |
|---|---|---|---|
| gitleaks/gitleaks | 29,114 | 2018-01-27 | hook + Action + SARIF trio (see Lane 3) |
| pre-commit/pre-commit | 15,555 | 2014-03-13 | framework layer |
| guardrails-ai/guardrails | 7,358 | 2023-01-29 | runtime LLM guardrails, SaaS-adjacent |
| NVIDIA-NeMo/Guardrails | ~7,000 | — | same category as above |
| Yelp/detect-secrets | 4,631 | 2017-12-05 | pre-commit hook exemplar |
| **cisco-ai-defense/mcp-scanner** | **1,062** | **2025-09-24** | ~3 months to 1k★; same agent-security category as HyoDo; 168-pt HN launch was a trigger |

HyoDo baseline for comparison: 1 star, 0 forks, 8,898 total PyPI downloads,
recent-30d 2,050 vs first-30d 122 (self-release traffic dominant).

## 3. awesome-* list targets (verified to exist)

- `adventurewave-labs/awesome-agent-security` — "curated list for securing
  autonomous AI agents — configs, runtime, tools, MCP, red-teaming" (best fit)
- `awesome-ai-security` — broad AI-security collection
- `Awesome-LLMSecOps` — LLM security operations
- `hesreallyhim/awesome-claude-code` — already lists agent-governance tools
  (e.g. Node9 "execution security layer"); HyoDo's MCP adapter fits

## 4. Channel mechanics (partial — recovered)

- **Reddit r/Python**: 10% self-promotion rule enforced; pure link drops get
  removed. Participate with original content first (e.g. a writeup of the
  fail-closed scoring approach), then the project link inside it.
- **PyCoder's Weekly**: has an active "Submit a Link" channel (realpython.com).
- **phpstan case study** (phpstan.org blog "0→1000★ in 3 months"): growth was
  cumulative (search + list presence), not single-launch; author credits
  steady README/SEO polish. Full extraction INCOMPLETE (timeout).
- **pypistats.org**: hard rate-limits anonymous API (429s) — use pepy.tech
  API v2 instead for download analytics.

## 5. INCOMPLETE sections (subagent timed out before finishing)

- PyPI keyword/trove-classifier optimization specifics
- GitHub social preview image guidance
- docs-site-vs-README conversion impact
- Final consolidated 2-week action list (synthesized instead in the parent
  session from Lanes 1–3: Week 1 = pre-commit hook + SARIF + Action;
  Week 2 = terminology neutralization (Lane 2); Week 3 = launch using the
  specific-claim title formula above + awesome-list PRs).
