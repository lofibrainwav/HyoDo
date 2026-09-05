# HyoDo Lane 3 — Ecosystem Stability & Integration Surface Research

**Date:** 2026-09-05 · **Scope:** governance/audit tool landscape, pre-commit + GitHub Action packaging, fast-moving-SDK dep strategy, prioritized integration roadmap

---

## 1. Landscape: AI agent governance/audit tools (2025–2026)

### 1.1 What the incumbents expose

| Tool | Model | Integration surfaces | CI/gate story |
|---|---|---|---|
| **guardrails-ai** (~7.4k★) | Runtime interceptor: `Guard()` wraps LLM calls, validators from a hub | Python SDK, validator hub (`guardrails hub install`), deployment server; MLflow-scorer integration added Jan 2026 (issue #1389) | **None native** — no pre-commit hook, no first-party GitHub Action; CI integrations arrive as community PRs (e.g. MLflow) |
| **LangSmith** (SaaS) | Tracing + evals platform; OTel-based; deepest zero-config with LangChain/LangGraph | SDKs, OTel, GitHub-deploy integration for LangGraph deployments, CI/CD example repo (`langchain-samples/cicd-pipeline-example`) | Eval results land in **dashboards only** — no native PR-gating action (Braintrust's 2026 comparison markets exactly this gap as its differentiator) |
| **Arize Phoenix** (10k+★, ELv2) | OSS tracing/evals on OpenInference + OTel | `px setup` one-liner auto-installs instrumentation, Python/JS instrumentation packages, Docker/Helm self-host, notebook-to-platform arc | Eval harness exists; CI gating is DIY — no pre-commit/Action surface |
| **AgentOps / Portkey / Langfuse** | SDK instrumentation / gateway governance | 2-line SDK (AgentOps), gateway policies (Portkey), prompt versioning + eval harness that "plugs into CI" (Langfuse) | Instrumentation-first; governance is a dashboard feature, not a repo-local gate |
| **OTel GenAI semantic conventions** | Standard, not a tool | `gen_ai.*` spans/agent-spans/MCP conventions; `OTEL_SEMCONV_STABILITY_OPT_IN` dual-emission flag | N/A — but stability status matters (below) |

### 1.2 Which surfaces drive adoption

- **The gitleaks trio is the canonical pattern for gate tools** (27.7k★): pre-commit hook (local, fast) + official GitHub Action (`gitleaks/gitleaks-action@v2`) + **SARIF output** that surfaces in GitHub's Security tab. All three surfaces reinforce each other; docs consistently prescribe "pre-commit locally, CI as the enforcement layer, SARIF for visibility."
- **CI-native gating is a proven differentiator in the agent space**: Braintrust's 2026 positioning wins on "Native GitHub Action with PR gating and automatic merge blocking" vs LangSmith's dashboards. A check that blocks a PR is stickier than a dashboard.
- **One-liner setup drives instrumentation tools** (Phoenix's `px setup`, AgentOps' 2-line SDK) — but those are runtime tools; HyoDo's category (repo-local gate) is closer to gitleaks/pre-commit, where the *hook + Action + SARIF* surfaces are what matter.
- **Gap HyoDo occupies**: policy-as-code + evidence ledger for agents that runs *in the repo/CI*, with no SaaS. The incumbents are either SDK-instrumentation (runtime) or SaaS dashboards. Nothing surveyed ships an agent-policy pre-commit hook or a fail-closed Action. Niche is real and unoccupied.

### 1.3 OTel GenAI stability (relevant if HyoDo ever exports traces)

- All `gen_ai.*` attributes remain **Development** status as of mid/late 2026 (Praesidia, ClickHouse, TrueFoundry).
- June 2026: GenAI conventions were **deprecated out of the main `semantic-conventions` repo (v1.42.0)** into a dedicated `semantic-conventions-genai` repo; **no tagged release as of Aug 21, 2026**. The ClickHouse writeup notes "three attribute renames in a single 2026 release cycle."
- **Implication:** do not hard-code `gen_ai.*` names anywhere user-visible; if trace export is ever added, isolate attribute names behind one module and treat the semconv dep as optional/experimental.

---

## 2. Packaging surfaces for a Python CLI like hyodo

### 2.1 pre-commit hook (`.pre-commit-hooks.yaml`)

**Requirements** (pre-commit.com docs):
- File at repo root listing hook entries: `id`, `name`, `description`, `entry`, `language`, plus optional `types_or`/`files`, `require_serial`, `pass_filenames`, `always_run`, `minimum_pre_commit_version`.
- Repo must be an installable package (`language: python` → pre-commit pip-installs the repo at the pinned `rev`). Hook must **exit nonzero on failure or modify files**.
- `rev` must be an immutable ref (tag/SHA); users update via `pre-commit autoupdate`.

**Exemplars (fetched, not imagined):**
- `Yelp/detect-secrets` — entire file is 7 lines (`entry: detect-secrets-hook`, `files: .*`).
- `astral-sh/ruff-pre-commit` — separate wrapper repo, ~40 lines: `types_or: [python, pyi, jupyter]`, `require_serial: true`, `minimum_pre_commit_version: "2.9.2"`, legacy `id` alias kept for migration.
- `gitleaks` — 3 variants in one file (`language: golang`, `docker_image`, `system`) with `pass_filenames: false`.

**HyoDo shape** (in-repo, no wrapper repo needed since hyodo is already pip-installable):
```yaml
- id: hyodo-safe
  name: hyodo safe
  description: Early-warning scan for agent-unsafe commits (policy DENY, hooks hygiene, secrets risk)
  entry: hyodo safe --strict
  language: python
  pass_filenames: false   # repo-level scan, not per-file
  require_serial: true
  stages: [pre-commit]
```
Decisions to make: `pass_filenames: false` vs file-filtered mode; whether to also expose a `manual`-stage `hyodo check` hook (BYOG gates are slow → `stages: [manual]` or `pre-push`). Note the hook env installs only base deps — hyodo's `mcp` is already an optional extra, so the hook stays lightweight (validated against pyproject.toml: base deps are jsonschema/referencing/typer/rich/tomli only).

**Effort: ~half a day** — file + README section + one CI job running `pre-commit run --all-files` against a fixture repo. detect-secrets-sized tools did it in a single commit. Highest adoption-impact-per-effort of anything surveyed: hook repos are discovered via pre-commit's own search indexes (`path:.pre-commit-hooks.yaml` sourcegraph/github searches).

### 2.2 GitHub Action (`action.yml` + Marketplace)

**Requirements** (GitHub Docs):
- `action.yml` with `name`, `description`, `runs`; add `branding` (icon+color) — required for a clean Marketplace listing; `inputs`/`outputs` as needed.
- Three runtimes: **composite** (recommended here — no image build, runs on the host), Docker (cold-start cost every run), JavaScript (needs Node build toolchain).
- **Marketplace publishing is instant, no review**: tag a release, check "Publish this Action to the GitHub Marketplace", accept ToS once. (Contrast: VS Code Marketplace has publisher accounts + review friction.) Marketplace guidance says the repo should contain only action-relevant files — in practice actions also ship fine from a subdirectory (`uses: owner/repo/subdir@v1`), so an `action/` subdir in the HyoDo repo keeps the listing clean without a new repo.

**HyoDo shape** (composite, ~40 lines):
```yaml
inputs: {version: {default: ''}, strict: {default: 'true'}, sarif: {default: 'true'}}
runs:
  using: composite
  steps:
    - uses: actions/setup-python@v5  # or pipx, matching README
    - run: pipx install hyodo${{ inputs.version && format('=={0}', inputs.version) || '' }}
      shell: bash
    - run: hyodo safe --strict --json
      shell: bash
    - if: ${{ inputs.sarif == 'true' }}
      uses: github/codeql-action/upload-sarif@v3
      with: {sarif_file: hyodo.sarif}
```
Known composite pitfalls from research: inputs aren't auto-injected as env for shell steps (write to `$GITHUB_ENV` if needed); no top-level `env:` key inside composite `runs:`; distinct `category` per SARIF run or uploads get dropped (GitHub changelog 2024-05-06).

**Effort: ~1 day** including a self-test workflow (the repo's existing `smoke.yml` pattern extends naturally). README already documents the raw `pipx install hyodo` + `hyodo safe --strict --json` pattern — the Action just wraps it, so v1 is a thin convenience that also unlocks Marketplace discovery.

### 2.3 SARIF output (the multiplier)

- GitHub ingests third-party SARIF via `github/codeql-action/upload-sarif@v3`; `partialFingerprints` are auto-generated for third-party files; alerts render in the Security tab and can block PRs (this is gitleaks' visibility channel).
- **Effort: ~half a day** — map `hyodo safe` findings (rule id, severity, file/line) to the SARIF schema; needs `hyodo safe --sarif` (JSON output already exists as the base).

### 2.4 Surfaces researched and deprioritized

- **VS Code extension**: publisher account + PAT + `vsce`/`ovsx` publish; realistic effort 3–5 days for a decent CLI-wrapper extension. Defer.
- **Docs site**: MkDocs-material on GitHub Pages, ~1–2 days minimum; significant for credibility/SEO (ruff, Phoenix pattern) but not a gate surface. Mid priority.

---

## 3. Handling fast-moving SDK deps (the MCP problem)

### 3.1 What the ecosystem actually does

- **Upstream MCP python-sdk is explicit**: v2 is now what `pip install mcp` gives you; the README instructs dependents to "keep a `<2` upper bound on your requirement (for example `mcp>=1.28,<2`) until you've migrated." v1.x lives on a maintenance branch with critical fixes only. langchain-mcp-adapters hit the same wall (issue #578, v2 prerelease breaking changes) — HyoDo is not alone.
- **HyoDo's current posture is ahead of upstream's minimal advice**: `mcp>=1.27,<3` optional extra + `hyodo._mcp_compat` dual-compat shim + separate CI pins per SDK major (confirmed in pyproject comments). This matches where the ecosystem is converging (adapter-shim packages).
- **Python packaging best practice** (pyOpenSci guide, iscinumpy, Hynek, Nijholt):
  - Base install minimal; heavy/fast-moving deps as **optional extras** — already done.
  - Lower bounds = tested minimum; **upper bounds only at *known* breaking majors** (missing caps are fixable by anyone; over-restrictive caps create solver errors users can't fix). HyoDo's `<3` cap is exactly a known-major cap — correct.
  - Declare even transitive-but-imported deps explicitly (hyodo already does this for `referencing` — validated by the pyproject comment).
- **OTel semconv churn** (three renames in one cycle, repo split) is the cautionary tale: unstable *vocabularies* should sit behind one adapter module, optional extras, or a flag — never in the core data model.

### 3.2 Rules to keep (stability contract)

1. Core (`event ledger`, `policy`, `schema`, `gates`) stays SDK-agnostic and dep-light — it already is; guard it with an import-lint/test that `hyodo.policy`/`hyodo.schema` never import `mcp`.
2. MCP surface stays an extra with a bounded range + shim module; widen only after CI has run both majors (already the pattern — keep it).
3. Any future OTel/GenAI export goes behind an `[otel]` extra + versioned attribute-name module until semconv-genai ships a tagged stable release.

---

## 4. Recommended integration roadmap (ranked by impact-per-effort)

| # | Deliverable | Effort | Why this rank |
|---|---|---|---|
| 1 | **`.pre-commit-hooks.yaml`** (`hyodo-safe` id; optional `hyodo-check` manual-stage hook) | 0.5 d | Table stakes for the category HyoDo sits in; discovered via pre-commit's search ecosystem; zero infra; exemplars are 7–40 lines |
| 2 | **SARIF output for `hyodo safe`** (`--sarif`) | 0.5–1 d | Makes findings visible in GitHub's Security tab; the visibility channel gitleaks rode to 27k★; JSON output already exists as the base |
| 3 | **Composite GitHub Action** (`action/` subdir) + Marketplace publish | 1 d | One-line adoption (`uses: lofibrainwav/HyoDo/action@v1`); Marketplace listing is free discovery, instant publish, pairs with #2; PR-gating is the proven differentiator in agent governance |
| 4 | **Starter workflow template + docs snippets page** | 0.5 d | GitHub's starter-workflow surface + copy-paste blocks for hook/Action/SARIF; multiplies #1–3 |
| 5 | **Docs site** (MkDocs-material, GH Pages) | 1–2 d | Credibility + SEO; ruff/Phoenix pattern; after surfaces exist so docs have something to document |
| 6 | *(ongoing)* **SDK-stability contract** — keep `[mcp]` extra bounded, `_mcp_compat` shim, dual-major CI pins, SDK-agnostic core test | continuous | Already in place; this report validates it against upstream guidance; add the core-no-mcp-import guard test |
| 7 | **VS Code extension** | 3–5 d | Defer until CLI surfaces prove pull; publisher/review friction; lowest impact-per-effort today |
| 8 | **OTel GenAI trace export** (`[otel]` extra, flagged) | 2–3 d | Defer: semconv-genai has no tagged release and attributes are renaming; export story would differentiate vs gitleaks-class tools but only when the vocabulary stabilizes |

**Week-one package:** items 1–3 (~2–3 focused days) turn HyoDo from "pip install + hope" into a tool that appears in pre-commit search, the Actions Marketplace, and the GitHub Security tab — the three surfaces every comparator in the gate-tool category used to grow.

---

## Sources

- pre-commit.com — hooks/plugins/config docs; `.pre-commit-hooks.yaml` spec; `rev` immutability; hook discovery searches
- github.com/pre-commit, Yelp/detect-secrets, astral-sh/ruff-pre-commit, gitleaks/gitleaks — `.pre-commit-hooks.yaml` exemplars (raw fetches)
- docs.github.com — composite actions, publishing to Marketplace (instant, ToS-only), SARIF support for code scanning, `upload-sarif`
- guardrails-ai/guardrails — repo, discussions, MLflow-scorer integration (#1389)
- braintrust.dev LangSmith-alternatives 2026 — CI/CD gating comparison; langchain docs CI/CD pipeline example
- arize.com/blog/phoenix-10k; Arize-ai/phoenix README — growth-by-community arc, `px setup`
- Praesidia / ClickHouse / Greptime / TrueFoundry — OTel GenAI semconv Development status, June 2026 repo split, no tagged release as of 2026-08-21
- modelcontextprotocol/python-sdk — v2 stable, `<2` upper-bound guidance, v1.x maintenance branch; langchain-mcp-adapters#578
- pyopensci dependency guide; iscinumpy "Should You Use Upper Bound Version Constraints?"; hynek.me optional-dependency extras; nijho.lt dependency post
- appsecsanta/gitleaks overview (surfaces trio); oneuptime secret-detection guide (pre-commit bypassable → CI second layer)
