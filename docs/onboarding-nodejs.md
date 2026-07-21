# Onboarding a Node.js project with BYOG

HyoDo's Bring-Your-Own-Gates (BYOG) path lets a Node.js checkout absorb the
tools it already runs (`npm test`, ESLint, ShellCheck, and similar) as
first-class `hyodo check` gates. This guide is grounded in the current
implementation (`hyodo/gates.py`, `hyodo/cli/main.py`).

## 1. What `hyodo init` does in a Node project

```bash
hyodo init          # scan cwd, write .hyodo/gates.toml
hyodo init --force  # overwrite an existing .hyodo/gates.toml
```

### Behavior (source-backed)

1. Resolve the target path (cwd by default). Missing path → exit `2`.
2. If `.hyodo/gates.toml` already exists and `--force` was not passed →
   refuse and exit `1`.
3. Call `detect_project_gates(root)` and write either:
   - a **detected** schema v1 file (`render_gates_toml`), or
   - a **starter** template with commented-out examples when nothing is found.
4. Print next steps (`Review/edit`, `hyodo check`, `hyodo dashboard --open`)
   and exit `0`.

### What detection actually looks for (Node-related)

`detect_project_gates` merges several detectors. For Node/JS it is **not** a
full toolchain discovery pass:

| Source file | What gets absorbed | Pillar | Command written |
|-------------|--------------------|--------|-----------------|
| `package.json` `scripts.test` | only if the string is non-empty and does **not** contain `"no test specified"` | `goodness` | `npm test` |
| `package.json` `scripts.lint` | only if the string is non-empty | `beauty` | `npm run lint` |
| `tsconfig.json` (file exists) | always proposes `tsc` when the file is present | `truth` | `npx tsc --noEmit` |

Python detection (`pyproject.toml`) covers pytest / mypy / pyright / ruff by
name presence. Go and Cargo have dedicated detectors; Makefile only maps
`test:` and `lint:` targets.

### Honest limits — manual gates.toml is the Node default of record

Detection is **footprint-based and shallow**, especially for Node:

- It does **not** inspect `dependencies` / `devDependencies` for ESLint,
  Jest, Vitest, Mocha, Prettier, or ShellCheck.
- It does **not** invent an ESLint gate unless you already expose a `lint`
  script (then it writes `npm run lint`, not `npx eslint`).
- ShellCheck is **never** auto-detected.
- Empty or npm-default `"test": "echo \"Error: no test specified\" && exit 1"`
  style scripts are **skipped** (the `"no test specified"` substring filter).
- If no footprint is found, init still writes a starter file with
  **commented** Python-flavored examples (`pytest`, `ruff`) — not Node
  defaults.

**Practical recommendation for Node.js:** treat auto-detect as a convenience
when `package.json` already has real `test` / `lint` scripts (and optionally
`tsconfig.json`). For a deliberate Truth / Beauty / Goodness suite — for
example `npm test`, ESLint, and ShellCheck — **author `.hyodo/gates.toml`
yourself** (or run `hyodo init` then edit). Manual composition is the
reliable path; detection is a best-effort bootstrap, not a complete Node
onboarding.

## 2. Example `.hyodo/gates.toml` (schema `hyodo.gates/v1`)

Path: **`.hyodo/gates.toml`** under the project root  
Schema id: **`hyodo.gates/v1`** (required; any other value is a config error)

Valid pillars for command gates: `truth`, `goodness`, `beauty`,
`benevolence`, `hyo`, `eternity`. In practice BYOG absorbs quality tools under
**truth / goodness / beauty**. Benevolence, Hyo, and Eternity are measured
natively from the checkout (`hyodo/pillars.py`) and are not meant to be
filled with shell commands.

Each gate table needs:

| Field | Rules |
|-------|--------|
| `pillar` | one of the six names above |
| `command` | non-empty **string** (split with `shlex`) **or** array of strings |
| `timeout` | optional positive int; default **`120`** seconds |

### Node-oriented example

Maps a typical Node quality stack onto Truth / Beauty / Goodness:

```toml
schema = "hyodo.gates/v1"

# Bring-Your-Own-Gates for a Node.js checkout.
# Commands run with subprocess shell=False (no pipes, no shell globs).

[gates.npm-test]
pillar = "goodness"
command = "npm test"
timeout = 300

[gates.eslint]
pillar = "beauty"
command = "npx eslint ."
timeout = 120

[gates.shellcheck]
pillar = "truth"
command = ["shellcheck", "scripts/deploy.sh", "scripts/ci.sh"]
timeout = 60
```

Notes aligned with the runner:

- `command = "npm test"` becomes `("npm", "test")` after `shlex.split`.
- Array form is useful when you must pass fixed argv without shell parsing
  (recommended for ShellCheck file lists).
- Prefer listing ShellCheck targets explicitly; with `shell=False`, a literal
  `scripts/*.sh` token is **not** expanded by a shell.
- If you already have npm scripts, you may use `npm run lint` instead of
  `npx eslint .` — that is what `hyodo init` would write when
  `scripts.lint` exists.

## 3. How `hyodo check` decides PASS / FAIL / exit codes

### Resolution order (`hyodo check`)

From the `check` command docstring and body:

1. **`--general`** (explicit opt-in) — language-agnostic sampled syntax gates;
   then stop.
2. Else if **`.hyodo/gates.toml` is present** — load and run user gates
   (`load_gates_config` + `run_user_gates`); then stop.  
   Malformed config → error printed, **exit `2`** ("not a validation pass").
3. Else — **built-in HyoDo checkout preset**: Pyright → Ruff → pytest → SBOM
   (only meaningful inside a HyoDo package checkout). Outside that layout you
   get guidance to run `hyodo init` rather than a Node suite.

So: **a present `gates.toml` always wins over the built-in preset.**

### Per-gate status (`run_user_gates` / `_run_one_gate`)

| Outcome | Status | When |
|---------|--------|------|
| Binary on `PATH` missing | **`SKIP`** | `shutil.which(command[0])` is `None` (or `FileNotFoundError`) — never upgraded to PASS |
| Process finishes with exit code `0` | **`PASS`** | observed success |
| Non-zero exit code | **`FAIL`** | message from stderr/stdout tail, or `exit code N` |
| Wall-clock timeout | **`FAIL`** | message `"timeout"` (not SKIP) |

### Aggregate rules for user gates (and the same idea for built-in / general)

Only **`PASS` and `FAIL` count as executed**:

- `SKIP` and `UNSUPPORTED` are **unobserved**: they neither satisfy nor block
  all-PASS by themselves.
- **`user_executed` empty** (every gate SKIP, or no runnable outcomes) →
  **"No user gates were executed" / "This is not a validation pass."** →
  **exit `2`** (all-SKIP is not green).
- Any executed gate **`FAIL`** → **exit `1`**.
- At least one executed gate and **all of those PASS** → **exit `0`**
  (message form: `All executed gates passed (N/M gates ran)`).

Receipt / history logic uses the same contract: all-PASS requires a non-empty
set of executed (`PASS`/`FAIL`) statuses that are all `PASS` — pure skips never
count as all-PASS.

## 4. Three common traps

### 1. Timeout too short → false FAIL

Default timeout is **120** seconds per gate. If you set e.g. `timeout = 5` on
`npm test`, a healthy but slow suite hits `subprocess.TimeoutExpired` and is
recorded as **`FAIL` with message `"timeout"`**, not SKIP. Size timeouts to
worst-case CI duration, not the happy path.

### 2. `shell=False` — no pipes (and no shell expansion)

Gates always run as:

```text
subprocess.run(list(gate.command), ..., shell=False)
```

Therefore these do **not** work as shell pipelines:

```toml
# Broken under BYOG — "|" is just another argv token, not a pipe
command = "npm test | tee out.log"

# Fragile — "*.sh" is not expanded by a shell
command = "shellcheck scripts/*.sh"
```

Use discrete argv (`["shellcheck", "a.sh", "b.sh"]`), npm scripts that hide
complexity, or a small wrapper binary on `PATH`. Do not assume `/bin/sh -c`.

### 3. No `gates.toml` → built-in preset, not your Node tools

BYOG is **opt-in**. If `.hyodo/gates.toml` is absent, `load_gates_config`
returns `None` and `hyodo check` falls through to the **HyoDo checkout
preset** (Pyright, Ruff, pytest, SBOM) — not ESLint or `npm test`. On a plain
Node repo that is not the HyoDo package tree, those built-ins largely
SKIP/UNSUPPORTED and you are steered to `hyodo init`.

**Fix:** run `hyodo init` (then edit) or hand-write `.hyodo/gates.toml` with
schema `hyodo.gates/v1` before treating `hyodo check` as your project gate.

## Quick start checklist

1. From the Node project root: `hyodo init` (use `--force` only when you intend
   to replace an existing file).
2. Edit `.hyodo/gates.toml` so Truth / Beauty / Goodness match tools you
   actually install and run (see section 2).
3. Ensure gate binaries are on `PATH` (`npm`, `npx`, `shellcheck`, …); missing
   binaries become SKIP and can drive an all-SKIP **exit 2**.
4. `hyodo check` — expect exit `0` only when at least one gate executed and
   every executed gate PASSED.
5. Optional: `hyodo dashboard --open` for evidence surfaces.

## Source anchors

| Topic | Location |
|-------|----------|
| Schema id, timeout default, load/run, `shell=False`, SKIP/PASS/FAIL | `hyodo/gates.py` |
| Detect Node footprints; `render_gates_toml` | `hyodo/gates.py` (`_detect_package_json_gates`, `_detect_tsconfig_gates`, `detect_project_gates`) |
| `hyodo init` write path, exit 1/0/2 | `hyodo/cli/main.py` (`init`) |
| `hyodo check` resolution order, user-gate exit 0/1/2 | `hyodo/cli/main.py` (`check`) |
| all-PASS ignores SKIP/UNSUPPORTED | `hyodo/pillars.py` (`executed_all_pass`) |
