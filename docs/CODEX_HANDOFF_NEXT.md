# Codex handoff — HyoDo FDE + MCP continuation

**For:** Codex (or any implementer) continuing after Grok 자룡 session  
**Date:** 2026-07-22  
**Repo:** `lofibrainwav/HyoDo` · path `/Users/brnestrm/HyoDo`  
**Public now:** PyPI **hyodo 4.4.0** · main tip at handoff: `39b6dc6` (re-read `git rev-parse origin/main`)  
**Authority:** Commander = final; implementers follow this queue + design SSOT  

---

## 0. START HERE (5 minutes)

```bash
cd /Users/brnestrm/HyoDo
git fetch origin && git checkout main && git pull --ff-only
git rev-parse HEAD
cat VERSION   # expect 4.4.0 until you cut a new release
.venv/bin/hyodo --version
.venv/bin/hyodo --help   # event + policy present; no mcp/schema/eval/report
```

**Read in this order:**

1. This file (queue + constraints)  
2. `docs/HYODO_MCP_CONNECTOR_DESIGN.md` (MCP M1–M4 full design)  
3. `docs/SECURITY_SURFACE.md` (claim + security bounds)  
4. `README.md` + `PHILOSOPHY.md` (public voice)  
5. Existing code: `hyodo/events.py`, `hyodo/policy.py`, `hyodo/cli/main.py`, `tests/test_agent_events.py`  
6. Optional PRD context (bb vault, may be gitignored):  
   `~/bb/01-Research/hyodo-fde-control-signoff-prd-tdd-2026-07-21.md`  
7. Kingdom skill: `~/.claude/skills/hyodo/SKILL.md`  

**Do not re-implement Phase 1.** It is shipped.

---

## 1. Honest status (what is done vs not)

| Item | Status |
| --- | --- |
| CLI quality gates (`safe`/`check`/`init`/`score`/`dashboard`) | Shipped long ago |
| **FDE Phase 1** — `event` / `policy`, digests, tests, examples | **Shipped in 4.4.0** |
| README FDE / agent-guardrail positioning | **Shipped in 4.4.0** |
| MCP connector **design** M0 | **Docs only** (PR #94) |
| **FDE Phase 2** `hyodo schema check` | **Not implemented** |
| **FDE Phase 3** `hyodo eval` | **Not implemented** |
| **FDE Phase 4** `hyodo report` | **Not implemented** |
| **MCP M1** stdio | **Not implemented** |
| **MCP M2** loopback URL | **Not implemented** |
| **MCP M3** Tailscale / private-net + token | **Not implemented** |
| **MCP M4** doctor / access ledger / agent-rules | **Not implemented** |
| Wallet / SixXon / EROS Redis / Vercel executor | **Out of scope v1** (design non-goals) |

---

## 2. Mandatory implementation order

Do **not** reorder without Commander approval. Dependencies:

```text
[done] P1 event/policy @ 4.4.0
           │
           ▼
    1) M1 stdio MCP          ← NEXT CODE
           │
           ▼
    2) P2 schema check
           │
           ▼
    3) M2 loopback serve
           │
           ▼
    4) M3 Tailscale bind
           │
           ▼
    5) P3 eval
           │
           ▼
    6) P4 report
           │
           ▼
    7) M4 polish
```

| # | ID | Deliverable | Depends on |
| --- | --- | --- | --- |
| 1 | **M1** | Optional MCP stdio adapter wrapping CLI | P1 |
| 2 | **P2** | `hyodo schema check` + fixtures | P1 |
| 3 | **M2** | `hyodo mcp serve --bind loopback` + URL print | M1 |
| 4 | **M3** | `--bind tailscale` / `--bind-ip` + **token required** | M2 |
| 5 | **P3** | `hyodo eval --dataset` | P1 (P2 nice-to-have) |
| 6 | **P4** | `hyodo report` HTML/MD | P1 (+ P2/P3 if present) |
| 7 | **M4** | `mcp doctor`, access ledger, `--agent-rules` | M3 |

**Suggested releases:** 4.5.0 = M1 (+P2 if fits) · 4.6.0 = M2+M3 · 4.7.0 = P3 · 4.8+/5.0 = P4+M4.

---

## 3. Hard constraints (do not violate)

1. **CLI is SSOT** — MCP never reimplements gate logic; subprocess or shared pure functions only.  
2. **Core wheel stays thin** — MCP behind `hyodo[mcp]` or optional import; `pip install hyodo` still works offline.  
3. **No default network listen** — serve is explicit.  
4. **No `0.0.0.0` in v1** — loopback or explicit Tailscale IP only.  
5. **T2 (remote) token fail-closed** — missing token = refuse listen / 401.  
6. **unobserved ≠ pass** — exit 2 / structured errors; never fake green.  
7. **Digest-default** for agent bodies; `--full-body` opt-in only.  
8. **No Wallet / OAuth / kingdom Redis** in public v1.  
9. **No Vercel as executor** — docs site only if ever.  
10. **No claim inflation** — forbidden phrases until true: “interceptor”, “auto philosophy”, “Zero-Prompt omniscience”, “cloud gates”.  
11. **Multi-machine = host workspace** — remote LLM does not magically see client-only files.  
12. **Do not bake** Commander Tailscale IP into package; dogfood IP is `100.109.255.2` (re-measure).  
13. **Tests + ruff + ruff format --check + pyright** before PR; version SSOT 3+1 only on release.  
14. **Commit/PR messages:** honest; Korean OK for kingdom style if hooks allow; no identity spoofing.  
15. **Single-file ownership** — do not edit same branch files as another agent without isolation.

---

## 4. Slice specs (copy into PR descriptions)

### 4.1 M1 — stdio MCP (NEXT)

**Intent:** LLM hosts attach via stdio; tools wrap existing CLI.

**Ship:**

- Packaging: `hyodo[mcp]` extra (MCP SDK) OR clear optional module  
- CLI: `hyodo mcp stdio` (or `python -m hyodo.mcp stdio`)  
- Tools (minimum):  
  - `get_local_context` — root, git status, short diff (read-only, root jail)  
  - `hyodo_safe` — `hyodo safe --json`  
  - `hyodo_check` — `hyodo check`  
  - `hyodo_event_record` / `hyodo_policy_check` — wrap 4.4.0 commands  

**Accept:**

1. Clean venv: `pip install -e '.[mcp]'` (or agreed extra)  
2. stdio server lists tools  
3. `hyodo_safe` JSON matches CLI contract  
4. Core install **without** mcp extra still runs CLI  
5. Tests for tool routing + path jail  
6. Docs: short “MCP stdio” section; claim audit clean  

**Design SSOT:** `docs/HYODO_MCP_CONNECTOR_DESIGN.md` §8, §10, Phase M1.

### 4.2 P2 — schema check

**Intent:** Deterministic JSON Schema validation for agent payloads.

**Ship:** `hyodo schema check --schema … --payload …` · exit 0/1/2 · machine JSON reasons.

**Accept:** fixture matrix (ok / type error / missing schema / empty) · CI tests · optional MCP tool wrap.

### 4.3 M2 — loopback URL

**Ship:** `hyodo mcp serve --bind loopback --port 8769` · print URL · token recommended.

**Accept:** port ≠ 8768 · no-token policy as designed · only 127.0.0.1.

### 4.4 M3 — Tailscale

**Ship:** `--bind tailscale` or `--bind-ip 100.x` · **token required** · print connector URL.

**Accept:** dogfood on Commander host Tailscale IP · second device call one tool · refuse without token.

**Dogfood host (re-measure):** `jays-macbook-pro` · Tailscale CLI via  
`/Applications/Tailscale.app/Contents/MacOS/Tailscale status`  
(CLI may not be on PATH).

### 4.5 P3 — eval

**Ship:** `hyodo eval --dataset golden.jsonl --runner …` · results under `.hyodo/eval-runs/`.

**Accept:** reproducible pass_rate · runner fail ≠ skip-as-pass · no cost-savings claims.

### 4.6 P4 — report

**Ship:** `hyodo report --format html|md` · residual risks · Not measured honesty · hash stability.

**Accept:** same inputs → same report hash · never paint unmeasured as PASS.

### 4.7 M4 — polish

**Ship:** `hyodo mcp doctor` · T2 access ledger default-on · `hyodo init --agent-rules` opt-in only.

---

## 5. Repo conventions (measured)

| Topic | Rule |
| --- | --- |
| Branch → PR → merge | No direct push to `main` without override |
| Beauty docs gate | MD013 line length 80 on README, ROADMAP, docs/README, etc. |
| README | ≤180 lines; no Hanja/HYOGOOK in top 15 lines; keep `HYOGOOK V5` somewhere |
| Release | VERSION + pyproject + `__init__` + CHANGELOG entry; `scripts/release/*` |
| Trusted Publishing | GitHub env `pypi`; approve pending_deployments with JSON body |
| Tests | `python -m pytest tests -q` · full suite before release |

---

## 6. Related PRs already merged (context)

| PR | What |
| --- | --- |
| #92 | FDE Phase 1 evidence spine |
| #93 | v4.4.0 release bump |
| #94 | MCP connector design v1 docs |

---

## 7. Out of scope / escalate to Commander

- Binding `0.0.0.0` / public internet MCP  
- Wallet / paid auth / SixXon as install default  
- Kingdom Redis EROS inside public package  
- Replacing Orca / kingdom-cmd with hyodo  
- Vercel as gate runtime  
- Any “AUTO approve deploy” from scores  

---

## 8. Suggested first Codex session script

```text
1. Read docs/CODEX_HANDOFF_NEXT.md + docs/HYODO_MCP_CONNECTOR_DESIGN.md
2. Confirm main clean + 4.4.0 CLI
3. Open issue: "feat: MCP M1 stdio adapter (hyodo[mcp])"
4. Branch feat/mcp-m1-stdio
5. TDD: tests for mcp tool list + safe wrap + no-extra regression
6. Implement thin adapter only
7. PR + CI green + merge
8. STOP and report — do not silently start M2 unless Commander said "continue all"
```

Default: **one phase per PR** unless Commander orders a stack.

---

## 9. Handoff completeness

| Need | Location |
| --- | --- |
| Product design | `docs/HYODO_MCP_CONNECTOR_DESIGN.md` |
| This queue | `docs/CODEX_HANDOFF_NEXT.md` |
| Kingdom skill | `~/.claude/skills/hyodo/SKILL.md` |
| Shared lesson (4 surfaces) | slug `hyodo-v440-fde-evidence-spine-release` |
| bb session residual | `bb/HANDOFF.md` Residual (Grok close + this handoff) |

Grok session ends here. Codex owns **M1 onward** under Commander direction.
