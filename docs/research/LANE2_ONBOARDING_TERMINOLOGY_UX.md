# Lane 2 — Onboarding & Terminology UX Research

**Question:** How do niche-branded developer tools handle unusual naming/philosophy without losing international adoption? What should HyoDo change?

**Date:** 2026-09-05 · Research via web survey of top Python tool READMEs/CLIs + CLI UX literature (clig.dev, Typer docs, gh CLI design discussions).

---

## 1. Unusual names/philosophy: what succeeded vs. what created friction

### Successes

| Tool | Name type | Above-the-fold treatment | Why it worked |
|---|---|---|---|
| **ruff / uv** (Astral) | Short, meaningless, pronounceable | "An extremely fast Python linter and code formatter, written in Rust." + benchmark chart, then bullet benefits | Name is a *label*, never a *concept*. Zero seconds spent explaining etymology; first sentence is pure utility. uv: 126M downloads/month — the name never mattered. |
| **Black** | Metaphor WITH philosophy | Tagline "The Uncompromising Code Formatter" — the philosophy word describes *formatter behavior*, then 2 paragraphs convert it to concrete benefits: "speed, determinism, and freedom from `pycodestyle` nagging" | The philosophy is expressed **as** the feature ("uncompromising" = no config options), not beside it. Quirky humor ("Any color you like", the fish dance) appears *after* the value prop. |
| **semgrep** | Descriptive portmanteau | "Code scanning at ludicrous speed." | Name encodes function (semantic + grep). No translation needed by anyone. |
| **poetry** | Pure metaphor | "Poetry helps you declare, manage and install dependencies of Python projects" | Metaphor never appears again after the title. Docs are entirely utilitarian. 34k stars. |
| **Kubernetes** | Foreign (Greek) word | Immediate functional framing + the **K8s** abbreviation was embraced as the daily-use name | Greek for "helmsman" — but nobody needs to know that. Google shipped a pronounceable abbreviation so the exotic name never sat in the hot path. |
| **Anki** | Foreign (Japanese 暗記) word | Flashcard app; docs say "spaced repetition flashcards" | Japanese for "memorization" — short, globally pronounceable, and meaning aligns with function. The etymology is trivia, not a prerequisite. |
| **Ubuntu** | Foreign (African philosophy) word | "Linux for human beings" | Philosophy was the *product differentiator* for its audience, backed by a company. Even so, tagline is functional. |

### What distinguishes winners from friction cases

Evidence from naming literature (opensource.com "Choosing project names", HN discussions, Network World survey of OSS naming) and the README survey:

1. **Name-as-label vs. name-as-curriculum.** Successful tools' names are opaque labels; the docs never require you to learn them. Friction starts when the *interface vocabulary* (commands, scores, statuses) inherits the metaphor — the user must translate before every action. GNU Hurd (recursive acronym inside recursive acronym) is the canonical joke case; it's notable that its docs lead with the acronym unpacking rather than a capability.
2. **Philosophy is amortized, never front-loaded.** Black's philosophy IS the feature. Poetry/Kubernetes/Anki park the metaphor at the door and lead with capability. None of the 5 surveyed READMEs explains the name above the fold.
3. **One neutral escape hatch.** Kubernetes → "K8s". Python tools keep quirky CLI names but every output column is standard English ("error", "warning", "fixed 3 files"). International users judge by *machine-facing strings* (exit codes, JSON keys, statuses) far more than by the brand.
4. **Descriptive names get a free pass; metaphorical names must buy trust with proof first** (benchmark chart, install count badge, "used by X" logos). Ruff leads with a bar chart precisely because it needs to earn the right to be a meaningless word.

**Bottom line:** unusual *brand* is fine and even memorable; unusual *operational vocabulary* (what you must type/read to get work done) is the adoption tax. HyoDo's reviewers are reacting to the second, not the first.

---

## 2. CLI progressive disclosure for 12+ command tools

Sources: clig.dev (Command Line Interface Guidelines), Typer docs (`hidden=True`), gh CLI design issues (#4506, #6047), Thoughtworks CLI guidelines, "10 CLI UX Patterns".

### Command grouping

- **noun-verb or resource grouping**: `gh pr list`, `gh repo clone`. Once you pass ~8 top-level commands, group by resource. gh surfaces ~15 groups but each group has a single obvious verb set (create/list/view/edit).
- **Reserve top level for daily verbs** (deploy/status/check). Everything else becomes a subcommand or flag. clig.dev: avoid ambiguous siblings ("update" vs "upgrade").
- Typer: `app.add_typer(event_app, name="event")` — HyoDo already does this correctly for `event/policy/schema/mcp/rules`.

### `--help` hierarchy

- Full help at **every** level: `hyodo --help`, `hyodo event --help`, `hyodo event record --help`. Typer gives this for free — verify docstrings read as task descriptions, not philosophy.
- Show help on typo/missing-args (clig.dev "Errors" section) with "did you mean" suggestions.
- Put a **persistent "start here" pointer in the epilog**: e.g. `Getting started? Try: hyodo safe`. gh does this — any unauthenticated command prints "To get started with GitHub CLI, please run: gh auth login". This is the single highest-value pattern for HyoDo: every error path should end with the next command to run.

### Interactive onboarding (gh style)

- `gh auth login` is a **wizard**: sequential prompts, sensible defaults, web-browser fallback. Crucially, gh later added **flag equivalents** for every prompt (`--git-protocol`, `--with-token`) because scripters/CI revolted (issue #4506). Lesson: wizard-first for humans, flags for machines, from day one.
- A `first-run experience` command that detects context and does the right thing beats a README: `hyodo start` (already exists at line 2397 of cli/main.py!) should be the advertised entry: detect tools → suggest `safe` → offer `init` → print the 3-command happy path.

### Hiding advanced commands

- Typer supports `@app.command(hidden=True)` (and `typer.Argument(hidden=True)`). Hidden commands still run (scripts/docs can rely on them) but vanish from `--help`, shrinking cognitive load.
- Rule of thumb: **≤ 8-9 visible top-level commands**. HyoDo currently registers ~13 visible top-level commands (safe, init, check, score, dashboard, report, eval, start, trinity, version + groups event/policy/schema/mcp/rules).

---

## 3. Concrete recommendations for HyoDo

The reviewers' complaint maps exactly to the §1 finding: the *brand* (HyoDo, 悖道/孝道) is fine; the **operational vocabulary** (pillar names as output labels, "HYOGOOK V5 F-score", "Trinity review") is the tax. Keep the brand, neutralize the interface. The repo already contains the right instinct — the README's "Engineering map" table leads with the "DevSecOps label" column and puts the pillar in parentheses. Extend that pattern everywhere.

### 3a. Six pillars → "six quality dimensions" with bilingual labels

Everywhere a pillar appears in CLI output/dashboard, **lead with the technical term, pillar in parens** (README already does this — make CLI/dashboard match):

```
# Dashboard / score table column headers
Type safety (Truth · 眞)     Tests & safety (Goodness · 善)
Lint & format (Beauty · 美)  Public surface (Benevolence · 仁)
Data consent (Hyo · 孝)      Audit continuity (Yeong · 永)
```

The parenthetical is then *flavor*, not *required reading* — the Kubernetes/Anki pattern. International users parse "Type safety" instantly; Korean speakers get the resonance for free. Never the reverse order ("Truth (types)") in machine-adjacent output.

### 3b. Neutral score name; HYOGOOK becomes an alias

- Public name: **"HyoDo score"** or plain **"composite quality score"**. Keep "HYOGOOK V5 F-score" as a documented alias for reproducibility (it's already version-pinned in PHILOSOPHY.md).
- `hyodo score --help` should say: *"Composite review signal across six dimensions. Geometric mean: any dimension at 0 collapses the score to 0. Optional — review signals never auto-approve."* The fail-closed math is a *selling point* when stated in engineering terms; PHILOSOPHY.md already correctly says "Document this as engineering, not only 'harmony'".

### 3c. `trinity` → functional name, philosophy in help epilog only

Rename or alias to `hyodo review` / `hyodo checklist`. Current output prints "Truth - technical accuracy" first; flip it:

```
$ hyodo review "add S3 upload"
Review checklist:

Technical accuracy (Truth) — types, contracts, failure modes checked?
Security & stability (Goodness) — secrets, destructive commands, prod impact?
Clarity (Beauty) — diff readable? naming understandable?

Checklist only — no automatic approval.
Next: hyodo check && hyodo safe, then human review.
```

Keep `trinity` as a hidden alias so existing scripts don't break.

### 3d. README stays utilitarian; philosophy in PHILOSOPHY.md (already the architecture — finish it)

- README first screen: name + one-line functional description + badges + **why-table + `hyodo safe` 3-liner**. Move the "Engineering map (branding kept, terms first)" section below the fold or into docs; above the fold it still forces every reader through 6 Hanja characters before the install command. Replace with one sentence: *"Quality is measured across six dimensions (types, tests, lint, public surface, data consent, audit trail); any unmeasured or failing dimension fails closed."* Link `[How the six dimensions map to our philosophy →](PHILOSOPHY.md)`.
- PHILOSOPHY.md keeps the full 眞善美仁孝永 treatment — this is exactly where Kubernetes keeps κυβερνήτης.

### 3e. CLI surface restructure (progressive disclosure)

Target visible top-level set (≤ 9), gh-style epilog on every path:

```
Visible:   safe  init  check  score  dashboard  start  report  version
Groups:    event  policy  schema  mcp
Hidden:    trinity (alias), eval, rules *, mcp access-log, start internals
```

- `hyodo start` = interactive onboarding wizard (gh pattern): detect repo tools → run `safe` → offer `init` → print happy path. Add `--no-input` flags from day one (gh lesson).
- Every error and the bare `hyodo` invocation ends with: `New here? Run: hyodo start  (or: hyodo safe for a no-setup scan)`.

### 3f. What NOT to change

- The **name HyoDo** — short, pronounceable globally, distinguishable on PyPI. Consistent with ruff/uv/Anki precedent.
- The **fail-closed / unobserved-is-never-green** framing — this is Black-style "philosophy as feature" and reads perfectly in English. Lead every pitch with it.
- `--json` machine keys should be neutral snake_case (`type_safety`, `tests`) even if display labels keep the bilingual parens — international CI consumers never see Hanja in their jq pipelines.

---

## 4. README above-the-fold survey — 5 popular Python tools (first ~30 lines, fetched from raw.githubusercontent)

| Tool | Line 1-3 pattern | Badges | Visual | First functional claim |
|---|---|---|---|---|
| **ruff** | `# Ruff` + 6 badges + Docs/Playground links | PyPI, license, pyversions, CI, Discord | **benchmark bar chart** ("Linting the CPython codebase from scratch") | "An extremely fast Python linter and code formatter, written in Rust." then 5 emoji bullets (⚡ 10-100x faster, installable via pip, pyproject.toml support, drop-in parity) |
| **uv** | `# uv` + 3 badges | PyPI, pyversions, Discord | benchmark chart | "An extremely fast Python package and project manager, written in Rust." + Highlights bullets ("replaces pip, pip-tools, pipx, poetry, pyenv, twine, virtualenv") |
| **Black** | centered logo + `The Uncompromising Code Formatter` | 10 badges incl. downloads/conda | logo only | 2 paragraphs: "speed, determinism, and freedom from pycodestyle nagging… smallest diffs possible" — philosophy-as-benefit, zero config talk |
| **poetry** | `# Poetry: Python packaging and dependency management made easy` + 6 badges | version, pyversions, downloads, Discord | **install.gif demo** | "Poetry helps you declare, manage and install dependencies… replaces setup.py, requirements.txt… with pyproject.toml" + TOML example |
| **mypy** | logo + `Mypy: Static Typing for Python` + 8 badges | version, downloads, CI, docs, chat, *including "Checked with mypy" and "code style: black" badges* | logo | Immediately answers "Got a question?" → docs links, cheat sheet, common-issues page. Unusually support-forward. |
| **semgrep** | centered logo + "Code scanning at ludicrous speed." + 9 badges | brew, PyPI, docs, Slack, stars, docker pulls | logo | One-line value prop; everything else is links. |

**Common template distilled:**

1. `# Name` (or logo) — 1 line
2. Badges row (3-10) — install-credibility signals
3. **One functional sentence** naming the category + differentiator ("extremely fast", "uncompromising", "made easy")
4. One visual: benchmark chart (ruff/uv), demo GIF (poetry), or logo (Black/semgrep)
5. 3-6 bullet highlights in the tool's own vocabulary-**as-benefits**
6. Install one-liner + minimal quick start ( RepoClip: "time-to-first-success measured in seconds")

None of the six explains its name or philosophy above the fold. HyoDo's current README already has the right skeleton (value-prop bold line, why-table, `hyodo safe` quick start); the deltas are: (a) move the pillar/Hanja table below the fold, (b) add a demo GIF or terminal-asciinema of `hyodo safe` output, (c) keep "Unobserved is never green" as the Black-style philosophy-as-feature line — it's the strongest sentence in the README.

---

## Appendix: specific rewrite examples

**CLI top-level help (proposed):**

```
Usage: hyodo [OPTIONS] COMMAND [ARGS]...

  AI agent guardrails: audit evidence, policy DENY, fail-closed quality
  gates. Unobserved is never green.

  Quality is measured across six dimensions; any unmeasured dimension
  fails closed. Details: hyodo score --help

Commands:
  safe       No-setup early-warning scan (start here)
  init       Detect existing tools → .hyodo/gates.toml
  check      Run absorbed gates (pytest/ruff/mypy/...)
  score      Composite quality signal (fail-closed)
  dashboard  Local evidence panel (127.0.0.1)
  report     Export evidence bundle
  start      Guided setup wizard
  event      Agent event ledger        [advanced]
  policy     Policy gate (ALLOW/DENY)  [advanced]
  schema     JSON Schema validation    [advanced]
  mcp        Local MCP adapter         [advanced]

  New here? Run: hyodo start   (or: hyodo safe)
```

**JSON keys (proposed, neutral for CI consumers):**

```json
{"dimensions": {"type_safety": 0.9, "tests_and_safety": 0.8,
                "lint_and_format": 1.0, "public_surface": "not_measured",
                "data_consent": 0.7, "audit_continuity": 0.5},
 "composite": 0.0, "reason": "geometric_mean_collapse: public_surface=0"}
```

**README above-the-fold (proposed first 30 lines):**

```markdown
# HyoDo

**Local AI agent guardrails: audit evidence, policy DENY, fail-closed
quality gates. Unobserved is never green.**

[badges: CI · PyPI · Python · License]

| Need | HyoDo |
| --- | --- |
| Agent step audit trail | `event record` → `.hyodo/agent-events.jsonl` |
| Tool/path/step policy | `policy check` (ALLOW/DENY; missing = exit 2) |
| Keep existing CI tools | `init` absorbs pytest/ruff/npm/go/… |
| Fake-green resistance | fail-closed score, SKIP ≠ PASS |

pipx install hyodo
hyodo safe                # no-setup scan — first success in <60s
```

(then below the fold: six-dimension table with bilingual labels, MCP, FDE evidence spine, PHILOSOPHY.md link.)
