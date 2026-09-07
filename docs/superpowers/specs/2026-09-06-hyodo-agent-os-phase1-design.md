# HyoDo Agent OS — Phase 1 design: judgment completion

## Status

Draft for owner review. Nothing in this document is implemented yet. It is the
gate before `writing-plans` and before any of the five PRs below open.

## Context

HyoDo's public identity is becoming larger than the current CLI: hyodo.app
frames
HyoDo as an open-source Agent OS, and the shipped `hyodo` package is its first
organ — the part that turns an agent's actions into observed, gated evidence.
The chain the project is committing to is philosophy -> math -> code: the six
review pillars (Truth, Goodness, Beauty, Benevolence, Hyo, Eternity) resolve to
the HYOGOOK geometric-mean formula, which resolves to a specific exit code. If
any link in that chain is unmeasured, the honest answer is UNOBSERVED, never a
silent ALLOW.

Today's `hyodo/policy.py` already declares an `ASK` value in `POLICY_DECISIONS`
(`hyodo/events.py:38`) but `evaluate_policy` (`hyodo/policy.py:162-239`) never
returns it — every event is currently `ALLOW`, `DENY`, or `UNOBSERVED`.
Phase 1
closes that gap: it gives HyoDo real judgment under uncertainty (`ASK`),
attaches that judgment to an operator-controlled trust ladder, links agent
events into a real evidence graph instead of a flat ledger, prints that
judgment as one calm line instead of scattered panels, makes onboarding a
single command, moves enforcement from after-the-fact reporting to a real
pre-action gate inside supported harnesses, and gives the Truth pillar a
native, unshellable signal for whether a project's own tests observe anything.

Honesty rule for this whole document and the code it describes: a probability
is never printed as evidence. Any "how sure are we" question is answered as
`observed / expected` — an integer coverage ratio — never as a confidence or
probability field. `PolicyDecision.as_dict()` (`hyodo/policy.py:58-70`) must
never grow a `probability` or `confidence` key, and a guard test enforces that
for every phase-1 package that touches it.

## Goals

- Give `evaluate_policy` a real `ASK` outcome driven by observed external
  variables, with `UNOBSERVED` reserved for what cannot be observed at all
  (missing policy, unreadable ledger, missing or damaged trust grant) and
  `DENY` reserved for rules that are absolute regardless of trust.
- Let an operator raise a trust ceiling that turns some `ASK` outcomes into
  `ALLOW`, in exchange for a stronger, non-optional evidence obligation.
- Turn the flat agent-event ledger into a graph: decisions can point at the
  events and gates that produced them, and a run can declare its own intent.
- Replace scattered per-command output with one calibrated verdict line,
  backed by a deterministic, model-free explanation table.
- Make wiring HyoDo into a harness (Claude Code, Cursor, pre-commit, GitHub
  Actions, Codex) a single reviewable command instead of hand-edited config,
  and — where the harness supports it — make that wiring a real pre-action
  gate, not only a post-hoc report.
- Give the Truth pillar a fourth native, unshellable signal: whether a
  project's own tests observe anything at all.

## Non-goals

- Phase 1 does not add a model call anywhere in the decision path. `ASK`,
  `--explain`, and the test-integrity scan are all rule-based and
  deterministic; two runs against the same input must produce byte-identical
  output.
- Phase 1 does not make HyoDo an agent runtime. Even where a harness hook can
  block a tool call (package 1-D), HyoDo is still invoked by the harness, not
  the other way around, and the CLI/MCP contracts are unchanged in shape.
- Phase 1 does not add BYOM (Bring-Your-Own-Model) execution, cross-source
  corroboration, or an intent loop. Those are Agent OS stages 2-4 and are out
  of scope here.
- Phase 1 does not add a JavaScript/TypeScript test-integrity scanner. 1-E is
  scoped to Python/pytest; the module shape leaves room for a second scanner
  later (see Non-goals under 1-E).
- Phase 1 does not change the MCP tool signatures in `hyodo/mcp_server.py`.
  The MCP layer shells out to the CLI (`_run_cli`) and returns its exit code
  and stdout/stderr verbatim, so a new CLI exit code (3 = `ASK`) reaches an
  MCP client with no server-side code change — only docstring updates.

---

## Package 1-A — `feat/policy-ask`: ASK, external variables, trust, `[web]`

### Data model

`PolicyConfig` (`hyodo/policy.py:29-47`) gains four optional fields. All are
optional so that a `policy.toml` written before Phase 1 evaluates identically
to today — this is the same "optional fields only" convention the module
docstring already states for `require_declared_paths`
(`hyodo/policy.py:37-42`), and it is written out explicitly for the new fields
too:

| Field | Type | Default | Effect when absent |
| --- | --- | --- | --- |
| `web` | `WebPolicy \| None` | `None` | no web boundary at all — a web-shaped tool call is judged only by `allowed_tools`/`ask_tools`, unchanged from today |
| `ask_tools` | `tuple[str, ...]` | `()` | no additional discretionary tools beyond the built-in web-tool set |
| `ask_threshold` | `int \| None` | `None` | no severity annotation on the `ASK` detail text |
| `trust` | `TrustPolicy \| None` | `None` | effective trust level is 1 (today's behavior — see Trust levels) |

`WebPolicy` (new frozen dataclass):

```python
@dataclass(frozen=True)
class WebPolicy:
    allowed_domains: tuple[str, ...] = ()
    allow_non_get: bool = False
    allow_credential_paths: bool = False
```

`TrustPolicy` (new frozen dataclass):

```python
@dataclass(frozen=True)
class TrustPolicy:
    max_level: int = 3  # caps the *granted* level; does not itself grant one
```

`PolicyDecision` (`hyodo/policy.py:50-70`) gains three fields, all included in
`as_dict()`:

| Field | Type | Meaning |
| --- | --- | --- |
| `coverage` | `tuple[int, int]` | `(observed, expected)` boundary surfaces for this event — integers only, never a ratio or percentage |
| `external_variables` | `tuple[str, ...]` | rule-id-shaped identifiers of every discretionary condition this event tripped, e.g. `("web_domain_unlisted:api.example.com",)`; empty when none |
| `trust_level` | `int` | the effective trust level (`min(cap, granted)`) used to reach this decision |

`as_dict()` must keep exactly these keys plus the existing four
(`decision`, `rule_id`, `reason`, `evaluated_by`) — no `probability`, no
`confidence`, no float anywhere. `tests/test_policy_ask.py` asserts this by
key-set, not by absence-of-name, so a differently spelled probability field
cannot slip past it.

`evaluate_policy` gains one new field on its `tool` sub-object it reads (via
`hyodo/events.py` — see below) and one new keyword parameter:

```python
def evaluate_policy(
    event: dict[str, Any],
    policy: PolicyConfig,
    *,
    observed_steps: int | None = None,
    root: Path | None = None,
) -> PolicyDecision:
```

`root` is new and keyword-only with a `None` default, so every existing
caller — including any third party importing `hyodo.policy` directly — keeps
today's behavior unless it opts in. `root` is only used for the
`path_outside_root` external variable (below); when it is `None`, that check
is skipped entirely and does not count toward `coverage`'s expected total.
Both in-repo call sites (`hyodo/cli/main.py`'s `policy_check` and
`event_record`) already resolve a root/cwd for other purposes and pass it
through.

`hyodo/events.py` schema addition: a new optional field `tool.method: str |
None` on the `tool` sub-object validated by `validate_event`
(`hyodo/events.py:123-153`), restricted to a small allowlist
(`GET, HEAD, POST, PUT, PATCH, DELETE`, case-insensitive, normalized to
upper-case) when present. This field is new — the design input for 1-A names
a hard-DENY rule for "non-GET web without `allow_non_get`", and that rule is
only enforceable if HyoDo can see the HTTP method. Without a declared method,
the rule cannot fire one way or the other, so an undeclared method on a
`[web]`-classified tool call is treated the same as every other undeclared
boundary in this codebase: `UNOBSERVED`, never a silent pass (see Evaluation
order, step 1c).

`hyodo/events.py:38` — `POLICY_DECISIONS` becomes
`frozenset({"ALLOW", "DENY", "ASK", "UNOBSERVED"})`. This is the one
asymmetric fix the design input calls out explicitly: today it is missing
`UNOBSERVED`, which means a caller asserting `{"policy": {"decision":
"UNOBSERVED"}}` in its own event currently fails `validate_event` with
`invalid_field:policy.decision` — an assertion the schema should be able to
quarantine under `policy.claimed` like the other three values, even though
`evaluate_policy` itself is the only path allowed to produce a *measured*
`UNOBSERVED` (`hyodo/policy.py:242-255`, `hyodo/events.py:46-62`).

Schema id stays `hyodo.policy/v1`. `hyodo/policy.py`'s module docstring is
extended with one paragraph documenting the "optional fields only" convention
as a permanent contract for this schema id, not just a one-off note next to
`require_declared_paths`.

### Config example (`.hyodo/policy.toml`)

```toml
schema = "hyodo.policy/v1"

max_steps = 20
allowed_tools = ["search", "read_file", "list_dir", "web_fetch"]
blocked_path_globs = ["**/.env", "**/.env.*", "**/secrets/**",
  "**/*credential*"]

# New in Phase 1 — every key below is optional; omitting [web] and [trust]
# entirely reproduces today's ALLOW/DENY/UNOBSERVED behavior byte-for-byte.

[web]
allowed_domains = ["api.example.com", "*.internal.example.com"]
allow_non_get = false
allow_credential_paths = false

# Tools judged as discretionary (ASK-eligible) beyond the built-in web-tool
# set {web_fetch, browser, http, fetch, WebFetch, WebSearch}.
ask_tools = ["send_email"]

[trust]
max_level = 2
```

`examples/fde-evidence-spine/policy.toml` gains the same `[web]`/`[trust]`
block as commented-out guidance, consistent with its existing style of
annotating each field with what triggers what.

### Trust levels

The granted trust level is **not** stored in `policy.toml`. It lives in a new,
untracked, TOFU-style store — `.hyodo/policy-trust.json`, schema
`hyodo.policy-trust/v1` — that mirrors the existing gate-trust store in
`hyodo/gates.py` (`GATES_TRUST_RELATIVE_PATH`, `_load_gate_trust_store`,
`_save_gate_trust_store` at `hyodo/gates.py:265-282`, which already writes
`json.dumps(store, indent=2, sort_keys=True)` best-effort and tolerates a
read-only checkout). `[trust].max_level` in the tracked `policy.toml` only
**caps** what can be granted; it never grants anything by itself. The
effective level for a decision is always `min(max_level, granted_level)`.

```json
{
  "schema": "hyodo.policy-trust/v1",
  "level": 2,
  "granted_at": "2026-09-06T12:00:00+00:00",
  "granted_by": "human:brnestrm",
  "history": [
    {"level": 1, "granted_at": "2026-08-01T09:00:00+00:00", "granted_by":
      "human:brnestrm"}
  ]
}
```

`granted_by` follows the same two-shape convention as
`gates.py`'s trust-approval `via` field (`hyodo/gates.py:290-296`):
`human:<name>` for an interactive grant, `env:HYODO_POLICY_TRUST_ALL` for
automation that pre-approved itself — the new environment variable mirrors
`GATES_TRUST_ENV_VAR = "HYODO_GATES_TRUST_ALL"` (`hyodo/gates.py:71`) and is
checked the same way, including `hyodo/gates.py`'s existing
`_is_noninteractive()` CI/non-TTY detection (`hyodo/gates.py:246-254`).

| Level | Name | Behavior | Precondition |
| --- | --- | --- | --- |
| 0 | observe-only | every `tool_call`/`tool_result` is `ASK` unless a hard `DENY` rule already fires | none |
| 1 (default when `[trust]` absent) | ask-on-any-external-variable | `external_variables` non-empty -> `ASK`; empty -> `ALLOW`; hard `DENY` unaffected | none — byte-identical to today's `evaluate_policy` for a `policy.toml` with no `[web]`/`ask_tools` configured |
| 2 | autorun-inside-boundary | an event whose only external variables are inside the configured boundary (listed domain range, declared paths, etc. — never a hard-`DENY` condition) becomes `ALLOW` instead of `ASK` | `observed_steps is not None`; else `UNOBSERVED`, `rule_id="autorun_level2"` |
| 3 | full-delegation | no `ASK` at all for external variables; only hard `DENY` and `UNOBSERVED` remain possible | same precondition as level 2, `rule_id="autorun_level3"` |

Levels 2 and 3 do not weaken any hard `DENY` — the owner decision is explicit
that trust raises the ceiling on discretionary judgment, never on absolute
rules. They also raise the ledger obligation: at level >= 2, `policy check
--json` adds `"ledger_write_required": true` and `"ledger_written": false`
(the CLI process that only evaluates, never persists) to its payload; the
text renderer prints a non-suppressible note ("trust level 2+ requires the
decision to be recorded — use `hyodo event record --policy`"), and `hyodo
event record --policy` is the sanctioned atomic evaluate-and-persist path
that satisfies the obligation in one step.

`[trust]` present in `policy.toml` but the trust store missing or unreadable,
for an event that has at least one external variable, is `UNOBSERVED` with
`rule_id="trust_grant_unobserved"` — a level cannot be verified, so it cannot
be trusted to soften an `ASK`. An event with zero external variables is
unaffected by this check: there is nothing discretionary to gate on trust, so
a missing trust file does not turn a clean `ALLOW` into `UNOBSERVED`.

### CLI surface (trust)

```text
hyodo policy trust grant --level N [--by NAME] [--yes]
hyodo policy trust show [--json]
```

`grant` writes `.hyodo/policy-trust.json`, appending the previous entry (if
any) to `history`. It refuses to run non-interactively
(`_is_noninteractive()`-equivalent check) unless
`HYODO_POLICY_TRUST_ALL` is truthy, mirroring `hyodo/gates.py:339-341`
exactly — `--yes` only skips the interactive confirmation prompt when a TTY
is actually present; it is not itself a non-interactive escape hatch, so a CI
script cannot self-grant trust by passing `--yes` alone. `--by` sets the
human name in `granted_by`; omitted, it defaults to `$USER`/`whoami`.

`show` prints the cap (from `policy.toml`, or "no cap configured"), the
granted level, the effective level, `granted_at`/`granted_by`, and the last
three `history` entries.

### Evaluation order

`evaluate_policy` becomes a strict, numbered pipeline. Each step either
returns immediately or falls through:

1. **Hard `DENY`** (absolute; trust level never softens these):
   1. `max_steps` exceeded (existing, `hyodo/policy.py:176-188`, unchanged).
   2. `tool_not_allowed` — `allowed_tools` is a closed allowlist and the tool
      is not in it (existing, `hyodo/policy.py:197-204`, unchanged).
   3. `data_boundary` — a declared path matches `blocked_path_globs`
      (existing, `hyodo/policy.py:218-228`, unchanged); `data_boundary
      _undeclared` stays `UNOBSERVED` when `require_declared_paths=true` and
      no path was declared (existing, `hyodo/policy.py:206-216`, unchanged).
   4. **New:** `web_non_get_denied` — `[web]` is configured, the tool is
      web-classified (see below), `tool.method` is declared and is not `GET`
      or `HEAD`, and `allow_non_get` is `false`.
   5. **New:** `web_credential_path_denied` — `[web]` is configured, the
      tool is web-classified, a URL's path component matches a small
      built-in credential-shaped pattern set (e.g. `/.git/`, `/.env`,
      `/wp-admin/`, query strings containing `token=`/`api_key=`/`secret=`),
      and `allow_credential_paths` is `false`.
2. **External-variable aggregation** (never denies; only ever populates
   `external_variables`):
   1. `web_domain_unlisted:<domain>` — the tool is web-classified, `[web]`
      is configured, and a declared URL's domain does not match any entry
      in `allowed_domains` (exact match or `fnmatch` wildcard, reusing
      `hyodo/policy.py`'s existing `fnmatch.fnmatch` approach from
      `_path_blocked`, `hyodo/policy.py:140-159`).
   2. `path_outside_root:<path>` — a declared path, resolved against `root`,
      is not a descendant of `root`. This closes the gap the design input
      names explicitly: today `evaluate_policy` has no concept of a project
      root at all, so a path like `/etc/passwd` that does not happen to
      match any `blocked_path_globs` entry sails through as a silent
      `ALLOW`. It becomes a discretionary external variable, not a hard
      `DENY`, because escaping the declared root is not automatically
      malicious (a tool may legitimately need to read a shared config
      outside the checkout) — it is exactly the kind of thing a human
      should be asked about once, not blocked outright.
   3. `ask_tools:<name>` — the tool's name is in the combined set
      `{web_fetch, browser, http, fetch, WebFetch, WebSearch} | ask_tools`.
      This set is the same one used to decide "is this event
      web-classified" for steps 1.4, 1.5, and 2.1.
   4. Whenever a boundary this policy cares about cannot actually be
      checked — `tool.method` undeclared on a web-classified call while
      `[web]` is configured, or `tool.urls` empty on a web-classified call
      while `[web]` is configured — the event is `UNOBSERVED`, not `ASK`
      and not silently `ALLOW`. This is a direct extension of the existing
      `data_boundary_undeclared` philosophy (`hyodo/policy.py:206-216`):
      "cannot be checked" is never treated as "checked and clean."
3. **Trust gate.** If `external_variables` is non-empty:
   - level 0: `ASK` (level 0 ignores whether the variables are "inside
     boundary"; every tool event with anything discretionary about it is
     `ASK`).
   - level 1: `ASK`.
   - level 2, `observed_steps is not None`, and every external variable
     present is one of `path_outside_root` or `ask_tools` (never
     `web_domain_unlisted`): `ALLOW` with the ledger obligation set. This is
     "autorun *inside the boundary*" — `path_outside_root` and `ask_tools`
     are categories the operator already anticipated by configuring them at
     all; an unlisted web domain was never inside any boundary, so it stays
     `ASK` at level 2 regardless of how it arose.
   - level 2, `observed_steps is not None`, but at least one external
     variable is `web_domain_unlisted`: stays `ASK` — level 2 only widens
     the boundary it already knows about, it does not remove asking about a
     domain nobody configured.
   - level 3, `observed_steps is not None`: `ALLOW` with the ledger
     obligation set, for **any** combination of external variables,
     including `web_domain_unlisted`. This is "full delegation": the
     operator has chosen to stop being asked about anything discretionary
     in exchange for every step being ledger-required, and level 3 is the
     only level where that trade includes web domains.
   - level 2 or 3 with `observed_steps is None`: `UNOBSERVED`,
     `rule_id="autorun_level2"` / `"autorun_level3"` respectively.
   - **The threshold never degrades `ASK` to `DENY`.** `ask_threshold`, if
     set, only annotates the `reason`/detail text (e.g. "3 external
     variables, above the configured threshold of 2") for `--explain` and
     the verdict line — it never changes the decision or the exit code.
     This is an explicit owner decision, not an oversight: HyoDo's job is to
     surface uncertainty, not to guess that "a lot of uncertainty" means
     "reject."
4. **`ALLOW`.** `external_variables` empty and `coverage == (expected,
   expected)` (full coverage — every applicable boundary was actually
   checked, not skipped for lack of information).

`coverage` is computed alongside steps 1-3 as `(observed, expected)` over
four possible surfaces, each counted in `expected` only when it applies to
this event and this policy:

| Surface | Counted in `expected` when | Counted in `observed` when |
| --- | --- | --- |
| tool identity | kind is `tool_call`/`tool_result` and (`allowed_tools` is set, `ask_tools` non-empty, or the built-in web-tool set applies) | `tool.name` is a non-empty string |
| path boundary | `blocked_path_globs` non-empty, or `root` is given (for `path_outside_root`) | `tool.paths` non-empty, or `require_declared_paths` is `false` (an explicit empty declaration is itself information under the default policy) |
| web boundary | `[web]` configured and the tool is web-classified | `tool.urls` non-empty with every entry's `domain` present, and `tool.method` declared |
| step boundary | `max_steps` set, or effective trust level >= 2 | `observed_steps is not None` |

### CLI surface

`hyodo policy check` gains no new flags in 1-A (it already has `--file`,
`--stdin`, `--config`, `--json`). `hyodo event record` gains no new flags
either — `--policy` already exists (`hyodo/cli/main.py:2177-2181`).

### Exit contracts

| Command | `ALLOW` | `DENY` | `UNOBSERVED` | `ASK` |
| --- | --- | --- | --- | --- |
| `policy check` | 0 | 1 | 2 | **3 (new)** |
| `event record --policy` | 0 | 1 | 2 | **3 (new)** |

Two existing lines of code must change to add the fourth branch:

- `hyodo/cli/main.py:2413` (`policy_check`) currently reads
  `exit_code = 0 if decision.decision == "ALLOW" else (2 if decision.decision
  == "UNOBSERVED" else 1)` — a ternary with no room for a fourth value. It
  becomes a dict lookup: `{"ALLOW": 0, "DENY": 1, "UNOBSERVED": 2, "ASK":
  3}[decision.decision]`.
- `hyodo/cli/main.py:2290` (`event_record`) currently reads `exit_code = 1 if
  decision_label == "DENY" else 0` when `decision_label` is not `None`. This
  is a real gap Phase 1 fixes, not a hypothetical one: as written today, an
  `evaluate_policy` result of `UNOBSERVED` (for example from `max_steps`
  being configured but the ledger being unreadable) currently exits **0**
  through `event record --policy`, even though `hyodo/cli/main.py:2412`'s own
  comment says "UNOBSERVED must not exit like a plain DENY" for the sibling
  `policy_check` command. `event_record` must use the same four-way mapping,
  keyed by `decision_label`, with `None` (no `--policy` given at all,
  validate-only mode) still mapping to 0 as it does today.

`hyodo/mcp_server.py:251-267` (`hyodo_policy_check`) and the `--policy`
docstring on `event_record` (`hyodo/cli/main.py:2160-2202`) get their
docstrings updated to name exit 3 = `ASK`; no code change, since `_run_cli`
already forwards whatever exit code the subprocess produces
(`hyodo/mcp_server.py:236-238`).

### Failure modes

- Malformed `.hyodo/policy-trust.json` (bad JSON, wrong schema id, `level`
  outside 0-3): treated exactly like "missing" for the purposes of the
  `trust_grant_unobserved` rule above — never a crash, never a default grant.
- `[web]` configured with an empty `allowed_domains` list is a closed
  allowlist for web calls, exactly like `allowed_tools = []` today
  (`hyodo/policy.py:105`) — every domain becomes `web_domain_unlisted`.
- A policy file that sets `[trust].max_level` outside 0-3, or a non-integer,
  fails `load_policy_config` with `PolicyConfigError`
  (`hyodo/policy.py:73-127` pattern), which surfaces as `UNOBSERVED` through
  `try_load_policy` (`hyodo/policy.py:130-137`) — a bad cap is unobserved
  policy, not a silent default.

### Backward compatibility

- Every new `PolicyConfig`/`WebPolicy`/`TrustPolicy` field is optional; a
  `policy.toml` with `schema = "hyodo.policy/v1"` and no `[web]`/`[trust]`/
  `ask_tools` evaluates identically to the current `evaluate_policy`, for
  every existing test in `tests/test_policy_self_report_boundary.py`.
- `evaluate_policy`'s new `root` parameter is keyword-only with a `None`
  default that disables the one new check that needs it
  (`path_outside_root`); no existing call site (in-repo or third-party)
  breaks by not passing it.
- `POLICY_DECISIONS` gaining `UNOBSERVED` only *widens* what
  `validate_event` accepts under `policy.claimed`; it does not change what a
  *measured* decision can be, since only `evaluate_policy` can produce one.

---

## Package 1-B — `feat/evidence-graph`: ledger edges, mission, URLs, graph export

Status: shipped on main by PR #160 and the completion PR that carries this note;
the public prototype page still renders fixture data.

### Data model

`hyodo/events.py` schema stays `hyodo.agent-event/v1` — no version bump,
same "optional fields only" convention as 1-A. Three additions:

1. `parent_event_id: str | None` — an optional non-empty string naming the
   event this one causally follows (e.g. a `decision` event pointing back at
   the `tool_result` it judged).
2. `evidence_refs: list[str] | None` — an optional list of references this
   event cites as its evidence. Each entry is either an `event_id`-shaped
   string (opaque, same "any non-empty string" rule `event_id`/`run_id`
   already use, `hyodo/events.py:120-122`) or a gate reference of the shape
   `gate:<name>@<hash>` (a fixed-format string pointing at a
   `hyodo/gates.py` `UserGate`/preset gate result, not another ledger event).
3. `tool.urls: list[{"domain": str, "digest": str | None}]` on the existing
   `tool` sub-object (`hyodo/events.py:123-153`), alongside the new
   `tool.method` from 1-A. `domain` is kept in plain text (needed for the
   `[web]` allowlist check in 1-A); the path and query of a URL are digest-
   only by default (`digest`, 12 hex chars via `content_digest`,
   `hyodo/events.py:65-76`) unless the caller supplies a full body under
   `io.input_text`, matching the ledger's existing digest-by-default,
   full-body-opt-in posture (`hyodo/events.py:1-6`, `182-198`).

**Validation is two-phase, matching the way 1-A separates "format is wrong"
from "cannot be checked without the ledger":**

- **Stateless** (inside `validate_event`, `hyodo/events.py:83-271`):
  `parent_event_id` must be a non-empty string if present;
  `evidence_refs` must be a list of non-empty strings, each either matching
  the `gate:<name>@<hash>` shape or treated as an opaque event-id reference;
  `tool.urls` entries must each have a non-empty `domain` and, if present, a
  12-hex `digest`. None of this touches the ledger.
- **Ledger-aware** (new function `validate_event_edges(root: Path, event:
  dict) -> tuple[bool, list[str]]`): for `parent_event_id` and every
  non-`gate:` entry in `evidence_refs`, confirm the referenced `event_id`
  already exists in `.hyodo/agent-events.jsonl` (via `read_agent_events`,
  `hyodo/events.py:374-406`, or an equivalent indexed lookup for large
  ledgers). A `gate:` reference is checked only for shape, not existence, in
  Phase 1 — resolving it against an actual gate-run record is deferred (see
  Open questions).

**Mission.** No new `kind` value is added to `EVENT_KINDS`
(`hyodo/events.py:27-36`) — a "mission" is not a schema-level concept but a
*structural* one: the event in a run with the lowest `step_index` whose
`kind == "prompt"` and `actor == "human"`. `PolicyConfig` gains one more
optional field, `require_mission_prompt: bool = False`, following the exact
opt-in pattern `require_declared_paths` already established
(`hyodo/policy.py:37-42`). This flag is read by `hyodo/report.py`, not by
`evaluate_policy` — a missing mission is a reporting concern (was this run's
intent ever declared?), not a per-event `ALLOW`/`DENY`/`ASK` question.

### Config example

```toml
schema = "hyodo.policy/v1"

# Phase 1-B: when true, the graph report flags any run without
# a human prompt as "intent unobserved". Off by default — mirrors
# require_declared_paths (hyodo/policy.py:37-42): most existing ledgers were
# never asked to declare an opening intent, so turning this on unconditionally
# would flag every pre-1-B run as a false positive.
require_mission_prompt = false
```

### Evaluation order (edge validation, inside `event_record`)

1. Load payload, run `validate_event` (stateless) — unchanged, exit 1 on
   structural failure (`hyodo/cli/main.py:2213-2225`).
2. **New:** if the normalized event carries `parent_event_id` or
   `evidence_refs`, call `validate_event_edges(root_path, normalized)`
   immediately — before `strip_full_bodies`, before `try_load_policy`, and
   before the idempotency check. A dangling reference means this event's own
   claim about its evidence is false; there is no reason to spend a policy
   evaluation or a ledger write on it. `ok=False` -> exit 1,
   `reasons=["unknown_edge_target:parent_event_id"]` or
   `["unknown_edge_target:evidence_refs"]` (one reason per offending field,
   not per offending id) — **not recorded**, matching the design input's
   instruction verbatim.
3. Continue the existing pipeline (full-body strip, `--policy` evaluation if
   given, idempotency check, append) unchanged from today.

### `hyodo report --format graph`

`hyodo/report.py` gains a third render path alongside `md`/`html`/`sarif`
(currently gated at `hyodo/cli/main.py:2069`, `"if report_format not in
{"md", "html", "sarif"}"` — that set grows to include `"graph"`). New schema
id `hyodo.evidence-graph/v1`. The output path is
`.hyodo/reports/hyodo-report.graph.json`.

```json
{
  "schema_version": "hyodo.evidence-graph/v1",
  "status": "READY",
  "reason": null,
  "nodes": [{"id": "evt-1", "type": "event", "run_id": "run-1"}],
  "edges": [{
    "type": "evidence_ref",
    "kind": "evidence",
    "source": "gate:pytest@a1b2c3d4e5f6",
    "target": "evt-1",
    "target_kind": "gate",
    "label": "decided_from"
  }],
  "unresolved_refs": [],
  "missions": {"run-1": "evt-1"},
  "summary": {
    "events": 1,
    "edges": 1,
    "parent_links": 0,
    "evidence_refs": 1,
    "gate_refs": 1,
    "unresolved_refs": 0,
    "corrupt_event_lines": 0,
    "intent_unobserved_runs": []
  }
}
```

Nodes also carry the observed event metadata, policy, and tool fields.
Parent edges use `type: parent_event_id`, the parent as `source`, the child
as `target`, and `label: result_of`. Evidence edges keep the referenced
id as `source` and the citing event as `target`; `target_kind` classifies
the reference (`event` or `gate`), retaining the shipped edge direction.
Gate references are shape-checked only and never enter `unresolved_refs`.

`missions` maps each run to its lowest-step human prompt, or null.
`summary.intent_unobserved_runs` always lists missing missions, sorted.
It is informational unless `require_mission_prompt` is true, when a clean
graph becomes `UNOBSERVED` with `mission_unobserved:<first run_id>`.
Missing or invalid policy preserves the existing graph behavior.

### Exit contracts

`report --format graph`: **0** for `READY`; **2** for `UNOBSERVED`
(unreadable ledger, corrupt lines, edge issues, or a required missing
mission) and write failures. Existing observation errors take precedence
over mission absence. `md`/`html`/`sarif` keep their existing contracts.

### Failure modes

- A `gate:<name>@<hash>` evidence reference with a malformed hash (not hex)
  fails the *stateless* check in `validate_event` (format error, exit 1) —
  it never reaches ledger-aware validation.
- `evidence_refs` referencing an event in a *different* `run_id` is allowed
  structurally in Phase 1 (cross-run evidence is a legitimate case — one run
  citing a shared setup event from another) but is called out under Open
  questions as a place a future phase may want to add its own rule.

### Backward compatibility

- Every ledger written before 1-B has no `parent_event_id`/`evidence_refs`/
  `tool.urls`; `validate_event` treats their absence as `None`/`[]`/`[]`
  exactly like every other optional field, and re-validating an old line
  round-trips unchanged.
- `read_agent_events`/`count_run_events` are unchanged; `validate_event_edges`
  is purely additive.
- `report`'s existing three formats are untouched in output shape; only the
  format allowlist grows.

---

## Evidence graph — 5W1H mapping

| Question | Field(s) today | Field(s) after Phase 1 | Status |
| --- | --- | --- | --- |
| Who | `actor`, `run_id`, `meta.model` | unchanged | present |
| When | `ts`, `step_index` | unchanged | present |
| What | `kind`, `tool.name` | unchanged | present |
| Where | `tool.paths` | `tool.paths` + `tool.urls[].domain` | extended (1-B) |
| How | `tool.args_digest`, `io.*` | + `tool.method` | extended (1-A) |
| Why | — | `parent_event_id`, `evidence_refs`, mission (structural: lowest-`step_index` `prompt`/`human` event) | **new (1-B)** — this is the one axis the current schema has no answer for at all today |

---

## Package 1-C — `feat/verdict-line`: one calm line, `--explain`, `--quiet`, `check --json`

Status: Implemented in `feat/verdict-line`; see the verification handoff.

### Data model

New module `hyodo/verdict.py`:

```python
def render_verdict_line(
    decision: str, observed: int, expected: int, unit: str, detail: str
) -> str:
    """Return 'HYODO {DECISION} — {n}/{m} {unit} observed, {detail}'."""

EXPLANATIONS: dict[tuple[str, str, str | None], str]
```

`EXPLANATIONS` is a plain dict literal keyed by `(command, decision,
rule_id)` — `rule_id` is `None` for a decision that has no single triggering
rule (e.g. a clean `ALLOW`). Lookup falls back to `(command, decision, None)`
for a decision whose specific `rule_id` is not separately documented. No
network call, no model, no randomness — `tests/test_explain_flag.py` asserts
two consecutive invocations of the same command against the same input
produce byte-identical `--explain` output.

### CLI surface

- `check`, `safe`, `policy check` each gain `--explain` (bool) and `--quiet`
  (bool). `--quiet` prints only the verdict line and still sets the same
  exit code the command would set without it. `--explain` prints the
  verdict line, then an "Explanation:" block from `EXPLANATIONS`; combining
  `--quiet --explain` prints the verdict line plus the explanation block and
  nothing else (the two flags are independent, not mutually exclusive).
- `check` gains `--json` (bool), reusing `safe --json`'s existing shape
  (`hyodo/cli/main.py:1540-1548`) as its template: `{"status": ..., "gates_
  ran": n, "gates_total": m, "failed": [...], "exit_code": c}`. This is the
  item already named on HyoDo's own `ROADMAP.md:51` ("Add machine-readable
  `hyodo check` results for CI consumers") — Phase 1 is where it lands.

### Integration points

`check` currently renders its pass/fail summary three separate times with
near-identical code — `--general` mode (`hyodo/cli/main.py:1139-1152`), the
Bring-Your-Own-Gates path (`hyodo/cli/main.py:1182-1193`), and the
HyoDo-checkout preset (`hyodo/cli/main.py:1248-1264`). All three collapse to
one call to `render_verdict_line("PASS" or "FAIL", ran, total, "gates",
detail)`, where `detail` is the existing failed-gate-name summary text.
`safe`'s existing summary line (`hyodo/cli/main.py:1591` area) and
`policy_check`'s decision print (`hyodo/cli/main.py:2402-2408` area) get the
same treatment, with `unit="files"` (using `scanned_files`/`total_scannable`,
already computed at `hyodo/cli/main.py:1595-1599`) for `safe` and
`unit="surfaces"` (using `PolicyDecision.coverage` from 1-A) for
`policy check`/`event record --policy`.

Example verdict lines:

```text
HYODO PASS — 4/4 gates observed, all executed gates passed
HYODO ASK — trust=1, 3/4 surfaces observed, 1 external variable
HYODO UNOBSERVED — 0/1 surfaces observed, ledger unreadable
```

### Exit contracts

Unchanged from 1-A/existing contracts — `render_verdict_line` and
`--explain`/`--quiet` are presentation only and never influence
`typer.Exit(...)` codes. `check --json`'s `exit_code` field mirrors whatever
`typer.Exit` the command already raises.

### Failure modes

- A `(command, decision, rule_id)` tuple with no entry in `EXPLANATIONS` and
  no `(command, decision, None)` fallback prints a fixed, honest default
  ("No stored explanation for this rule yet — see README exit contracts")
  rather than raising `KeyError` or fabricating a rationale.

### Backward compatibility

- Commands behave exactly as today when `--explain`/`--quiet`/`--json` are
  not passed; gate-by-gate details stream live so slow gates show progress.
  The verdict replaces the final summary as the last line in default mode
  and is the only line under `--quiet`. `--explain` appends its explanation
  after the verdict.
- `check`'s existing exit codes (0/1/2) are unchanged; `--json` only adds a
  machine-readable mirror of what text mode already communicates.

---

## Package 1-D — `feat/connect`: one click to wire a harness, and a real pre-action gate

### Data model

No new ledger/policy schema. New module `hyodo/connect.py` mirrors the
`_detect_X` pattern already established for gate detection
(`hyodo/gates.py:460-560`: `_detect_pyproject_gates`,
`_detect_package_json_gates`, `_detect_tsconfig_gates`, `_detect_go_gates`,
`_detect_cargo_gates`, `_detect_makefile_gates`) — one `_detect_<harness>`
function per target file, each returning "what would be written" without
writing anything, so dry-run and `--write` share one code path.

### Harness targets

| Harness | File | Scope | Action |
| --- | --- | --- | --- |
| Claude Code (MCP) | `.mcp.json` | project | add `mcpServers.hyodo` (same shape as `.claude-plugin/plugin.json`'s existing `mcpServers.hyodo` entry: `{"command": "hyodo", "args": ["mcp", "stdio", "--root", "."]}`) |
| Claude Code (hooks) | `~/.claude/settings.json` | **global only** | add `PreToolUse`/`PostToolUse` hook entries (see below) |
| Cursor | `.cursor/mcp.json` | project | same `mcpServers.hyodo` shape |
| pre-commit | `.pre-commit-config.yaml` | project | add a `repo: https://github.com/lofibrainwav/HyoDo` entry pinned to the latest signed tag, hook id `hyodo-check` (from HyoDo's own shipped `.pre-commit-hooks.yaml`) |
| GitHub Actions | `.github/workflows/hyodo.yml` | project | new workflow calling HyoDo's existing composite Action |
| Codex | `~/.codex/config.toml` | **global only** | add `[mcp_servers.hyodo]`, plus a hooks entry if the operator's Codex version supports it (see below) |

Project-local files are the default scope; `$HOME` files
(`~/.claude/settings.json`, `~/.codex/config.toml`) are touched only with an
explicit `--global` flag, per the owner's decision that a project-scoped
command should not silently reach outside the project. All merges are
key-level (`mcpServers.hyodo`, one `hooks.PreToolUse[]` entry, one
`hooks.PostToolUse[]` entry, one `[gates.hyodo-check]`-shaped block) — never
a whole-file overwrite — and the first write to any file `connect` did not
create itself produces a `.bak` alongside it.

### Shadow mode (owner decision, 2026-09-06)

`hyodo connect --shadow` installs the same hooks in *shadow* mode: the
pre-action hook evaluates policy and records the decision it *would* have
returned (`ALLOW`, `ASK`, `DENY`, `UNOBSERVED`) to the ledger, but always
exits 0 so nothing is blocked. Shadow mode is the on-ramp for trust level 0
and the dry run of governance itself: the operator keeps working undisturbed
while the evidence graph fills with the decisions the gate would have made.
Dry run answers "what would happen" before an action (time); a sandbox
contains what does happen (space); shadow mode is a dry run of the gate
running alongside real work. Leaving shadow mode is an explicit
`hyodo connect --write` without `--shadow`; shadow decisions are stamped
`policy.shadow: true` so they are never mistaken for enforced ones.

### Claude Code hooks: from post-hoc report to pre-action gate

This is the change that answers the "HyoDo is a passive observer" critique
directly. Everything before 1-D reports on what an agent already did; the
hook installed here runs **before** a tool call executes and can stop it.

Per Claude Code's hooks reference (`code.claude.com/docs/en/hooks`, verified
2026-09-06): a `PreToolUse` hook receives a JSON payload on stdin —
`session_id`, `cwd`, `permission_mode`, `hook_event_name`, `tool_name`,
`tool_input`, `tool_use_id` among its fields — and its **exit code** decides
the outcome regardless of any JSON it prints: exit 0 lets the tool call
proceed through normal permission handling; **exit 2 blocks the tool call**,
and Claude sees the hook's stderr as the reason. `PostToolUse` receives the
same payload shape but fires after the tool already ran, so it **cannot
block** — a non-zero exit there only surfaces a warning notice.

`.claude/settings.json` (project) or `~/.claude/settings.json` (`--global`)
gains:

Run this example from the project root with `POLICY=.hyodo/policy.toml`
exported in the hook environment.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command":
              "hyodo policy check --stdin --hook claude-code --root ."
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command":
              "hyodo event record --stdin --hook claude-code --policy $POLICY"
          }
        ]
      }
    ]
  }
}
```

`policy check` and `event record` both gain a new `--hook claude-code` flag.
When set, the command reads the Claude Code hook JSON from stdin instead of
a `hyodo.agent-event/v1` payload, and maps it into one internally before
running the existing pipeline unchanged:

| Hook field | Mapped to |
| --- | --- |
| `tool_use_id` | `event_id` |
| `session_id` | `run_id` |
| (none in the payload) | `ts` — synthesized at receipt time (current UTC instant); the hook payload carries no timestamp |
| `hook_event_name` | drives `kind`: always `"tool_call"` for `PreToolUse` |
| (derived) | `step_index` — `count_run_events(root, run_id)`, the same ledger-derived count `evaluate_policy` already trusts over any caller-supplied value (`hyodo/policy.py:170-172`) |
| (fixed) | `actor = "agent"` |
| `tool_name` | `tool.name` (Claude Code's own `WebFetch`/`WebSearch` tool names are two of the six literal strings already in the built-in web-tool set from 1-A — no separate mapping table needed for those two) |
| `tool_input.file_path` (Edit/Write/Read-shaped tools) | `tool.paths` |
| `tool_input.url` (`WebFetch`) | `tool.urls` (domain extracted, path/query digested) |
| `tool_input.command` (`Bash`) | folded into `tool.args_digest` only — not a path or URL |
| `cwd` | both the effective `root` for `evaluate_policy` and the `.hyodo/policy.toml` lookup base (unless `--config` overrides it) |

Decision-to-exit-code mapping for this mode is deliberately narrower than the
normal CLI contract, because the harness itself only understands "proceed"
or "block":

| HyoDo decision | Hook exit code | stderr |
| --- | --- | --- |
| `ALLOW` | 0 | (none) |
| `DENY` | 2 | `rule_id` + `reason` |
| `ASK` | 2 | "HYODO ASK: <detail>. Stop and ask the human before retrying this tool call." |
| `UNOBSERVED` | 2 | "HYODO UNOBSERVED: <reason>. Not a green light — stop and ask the human." |
| malformed/unparseable stdin | 2 | "HYODO UNOBSERVED: malformed hook payload; treating as blocked, not allowed." |

**`ASK` and `UNOBSERVED` are enforced as a hard block in this harness today**
because Claude Code's `PreToolUse` contract has only two outcomes (proceed
or block) — there is no native "pause and ask a human" signal yet. This is a
real behavior change worth stating plainly: the moment this hook is
installed, `ASK` stops being merely a signal a report can show later and
starts being an actual stop, indistinguishable from `DENY` to the harness
(only the stderr text tells a human which one happened). Whether future
harness versions add a genuine third outcome, and whether HyoDo should then
special-case it, is called out under Open questions.

`event record`'s `PostToolUse` hook is fire-and-forget: it always exits 0
regardless of the recorded decision (matching the harness's own "cannot
block" contract for this event), except when the ledger append itself fails,
where it exits 2 to surface a warning notice (tool already ran; this is
purely a "your audit trail may be incomplete" signal, never a retroactive
block).

**Codex.** Per `developers.openai.com/codex/hooks` (verified 2026-09-06,
redirects to `learn.chatgpt.com/docs/hooks`), Codex CLI documents an
equivalent `PreToolUse`/`PostToolUse` contract — the same `exit 2` /
`hookSpecificOutput.permissionDecision: "deny"` shape, covering Bash,
`apply_patch`, and MCP/local function tools (hosted tools like `WebSearch`
are explicitly excluded from hooks in that documentation). `connect --only
codex --global` installs the same `hyodo policy check --stdin --hook
claude-code`/`event record ... --hook claude-code` pair into
`~/.codex/hooks.json`, reusing the `--hook claude-code` payload shape as-is
since the documented field names (`tool_name`, `tool_use_id`, `tool_input`)
match. This is flagged under Open questions rather than treated as fully
settled: it is verified against documentation, not against a running Codex
CLI install, and the exact field name for the Codex `PostToolUse` tool
result (needed for `io.output_digest`) is not confirmed.

**Cursor**, at time of writing, exposes MCP but no documented pre-tool-call
hook; `connect` installs only `.cursor/mcp.json` for it, unchanged from the
plan before this addition, and stays a post-hoc surface there until Cursor
ships an equivalent contract.

### CLI surface (connect)

```text
hyodo connect [--only HARNESS ...] [--write] [--yes] [--global]
```

Default is dry-run: prints a diff-style preview of every file it would
create or modify, for every detected harness, and writes nothing. `--write`
performs the writes, prompting once per harness unless `--yes` is also
given. `--only` restricts to one or more harness names. `--global` is
required in addition to `--write` for any `$HOME` file; omitting it silently
skips global-scoped targets (still shown in the dry-run preview, marked
"requires --global").

### Exit contracts

`connect` (dry-run, default): always 0 — a preview cannot fail. `connect
--write`: 0 on success (including "nothing changed, already up to date" —
the idempotency case), 1 if any per-harness confirmation was declined and
`--yes` was not given, 2 on a write error (permission denied, disk full).

### Failure modes

- A target file that already exists but was not created by `connect` (no
  `.bak` and no prior HyoDo marker comment) still gets a `.bak` on its first
  `connect`-driven write — "first write of foreign files" applies regardless
  of who authored the file originally.
- Running `connect --write` twice in a row with no other change to the
  project produces a second dry-run-identical preview and, per the owner
  decision, **no file changes on the second run** — this is the idempotency
  contract `tests/test_connect.py` checks directly.

### Backward compatibility

- `connect` is a wholly new command; it does not change any existing CLI
  surface, ledger schema, or policy schema.
- Existing `.mcp.json`/`.cursor/mcp.json`/`.pre-commit-config.yaml`/workflow
  files with unrelated content are only ever merged at the key level HyoDo
  owns (`mcpServers.hyodo`, the one hyodo pre-commit repo entry, the one
  hyodo workflow file, the one pair of hyodo hook entries) — nothing else in
  those files is touched.

---

## Package 1-E — `feat/test-integrity`: a native, unshellable signal for the Truth pillar

`hyodo/safe/anti_gaming.py` (PR #161) is the AST visitor 1-E will consume.

### Why this is the honest form of "semantic test quality"

HyoDo already has two pillars whose evidence cannot be faked by pointing
`gates.toml` at an arbitrary shell command — Benevolence (native AST scan of
public-surface claims) and Hyo (native consent/data-protection scan), per
`README.md`'s own engineering-model table (`README.md:157-164`). Truth today
is entirely a shelled-out `pyright` run (`run_pyright_check`,
`hyodo/cli/main.py:327`-area) — real evidence, but it answers "does the type
checker pass," not "do the tests that are supposed to prove correctness
actually observe anything." 1-E does not attempt to judge whether a test is
*semantically* meaningful — that would require modeling intent, which this
project's honesty rule forbids doing without a model and without the
authority to say so. What it can measure, with zero judgment and zero model
calls, is the **observable absence of observation**: a test function with no
assertion in it cannot have caught a regression no matter what it asserts
about the code under test, because it asserts nothing. That is a fact about
the AST, not an opinion about intent, and it is exactly the same "unenforced
is not the same as passing" principle the rest of HyoDo already applies to
policy and ledger evidence.

### Data model

New module `hyodo/test_integrity.py`:

```python
@dataclass(frozen=True)
class VacuousTestFinding:
    path: str
    line: int
    function: str
    # no_assertion | constant_assertion | no_target_reference | unexplained_skip
    category: str
    detail: str

@dataclass(frozen=True)
class TestIntegrityReport:
    scanned_files: int
    total_files: int
    total_tests: int
    # no_assertion + constant_assertion, deduplicated per function
    vacuous_tests: int
    findings: tuple[VacuousTestFinding, ...]
```

Discovery follows pytest's own default convention: files matching
`test_*.py`/`*_test.py`, functions named `test_*` at module level or inside a
`Test*`-named class, under the project root — mirroring `safety.py`'s
existing directory-walk exclusions (`_SKIPPED_DIR_NAMES`,
`hyodo/safety.py:86-99`: `.venv`, `node_modules`, `__pycache__`, `dist`,
`build`, the various tool caches) so the scan does not read vendored or
generated code.

Per test function, walked via `ast.walk` on the function's `FunctionDef`
node:

| Category | Trigger |
| --- | --- |
| `no_assertion` | zero `ast.Assert` nodes, and zero calls to a name/attribute matching `assert*` (covers `self.assertEqual`, `pytest.raises`/`pytest.warns` used as a context manager, `np.testing.assert_*`) anywhere in the function body |
| `constant_assertion` | every `ast.Assert` node's test expression is a literal truthy constant (`assert True`, `assert 1`) or a comparison between two `ast.Constant` nodes with equal value — flagged only when it is *every* assertion in the function, never when a real assertion coexists with a sanity-check constant one |
| `no_target_reference` | the function body never names a symbol the module imported from the project's own package (`import hyodo` / `from hyodo...`); this is a heuristic with a known false-positive shape (fixture-driven tests that only reference the package through a fixture parameter), so a `# hyodo: allow-vacuous` comment on the `def` line suppresses it for that function, the same escape-hatch shape `ruff`'s `# noqa` already trains every contributor to look for |
| `unexplained_skip` | `@pytest.mark.skip`, `@pytest.mark.skipif`, or `@pytest.mark.xfail` with no `reason=` keyword argument |

### CLI surface

`check` (HyoDo-checkout preset path only — see Non-goals) runs the scan
unconditionally as a fifth, report-only computation alongside its four
existing gates, and adds one new flag:

```text
hyodo check --strict-tests
```

Without `--strict-tests`, the scan result is purely additive: one line in
text mode ("Test integrity: 12/40 tests assert nothing — see `hyodo check
--json`"), and a `test_integrity` object in `check --json`'s payload
(`total_tests`, `vacuous_tests`, `findings`). It does **not** join the
`results`/`executed`/`failed` gate list, so the existing "4/4 gates ran"
counting and the existing pass/fail exit contract for `check` are unchanged
by default.

With `--strict-tests`, the existing Truth gate result (`hyodo/cli/main.py`'s
`run_pyright_check` step) is amended in place: if `pyright` passes but
`vacuous_tests > 0`, that gate's status flips from `PASS` to `FAIL` with a
combined message ("pyright: pass; test-integrity: 12/40 tests assert
nothing"). This is what makes vacuous tests "fail the Truth gate," per the
owner decision, without inventing a fifth named gate that would change the
`ran/total` counts every existing test and CI consumer already relies on.

### Exit contracts

`check` (no `--strict-tests`): unchanged 0/1/2 contract; the scan cannot
change the exit code. `check --strict-tests`: exit 1 exactly when the Truth
gate would otherwise pass but `vacuous_tests > 0` (all other exit-code paths
unchanged).

### Failure modes

- A file that fails to parse as Python (syntax error) is counted in
  `total_files` but not `scanned_files`, and does not raise — consistent
  with `_scan_directory`'s existing "never crash on an unreadable file"
  posture (`hyodo/safety.py:608-641`).
- `no_target_reference` false positives on fixture-only tests are the known,
  documented limitation above; they are not a bug to "fix" by trying to
  trace fixture bodies (that would require import-graph resolution well
  beyond a single-file AST walk) — they are an accepted heuristic cost with
  a one-line, `noqa`-shaped escape hatch.

### Backward compatibility

- Scoped to the HyoDo-checkout preset path in `check`; `--general` and
  Bring-Your-Own-Gates are untouched by 1-E in this phase (see Non-goals).
- No ledger, policy, or event schema is touched.
- Without `--strict-tests`, `check`'s exit code for every existing checkout
  is unchanged, even a checkout whose tests are all vacuous — the new signal
  is opt-in to enforce, on by default only to *observe*.

### Mutation testing as a BYOG gate (documentation, not new code)

HyoDo's own repository already treats mutation testing as real, if advisory,
evidence: `.github/workflows/mutation.yml` runs `cosmic-ray baseline` /
`init` / `exec` against `cosmic-ray.scoring.toml` and `cosmic-ray.toml`, then
`cr-rate`/`cr-report`/`cr-xml` to produce a survival-rate readout — its own
step summary says the lane is "advisory until a measured baseline is
reviewed and a threshold is explicitly adopted." Separately,
`scripts/mutation-score.py` (covered by `tests/test_mutation_score.py`)
summarizes `mutmut` 3.7.x metadata into the same killed/survived/no-tests/
timeout status vocabulary. 1-E does not ship either tool as new public API —
it documents, in `docs/` (README's "Engineering model" section gains one
paragraph and a `.hyodo/gates.toml` example), how an adopter absorbs the
*same* signal as a Bring-Your-Own-Gate:

```toml
schema = "hyodo.gates/v1"

[gates.mutation-score]
pillar = "goodness"
# Wrap cr-rate (or mutmut's own summary) in a small script that exits
# non-zero when the surviving-mutant share is above the threshold the
# operator has explicitly adopted for this project.
command = "scripts/mutation-gate.sh --max-survived-pct 15"
timeout = 1800
```

This keeps mutation testing exactly where HyoDo's own CI keeps it today —
advisory, operator-owned, and never silently converted into a threshold
HyoDo invented on the adopter's behalf.

### Non-goals (1-E specific)

- No Jest/Vitest or other non-Python scanner ships in Phase 1.
  `TestIntegrityReport`'s shape (files/tests/findings counts) is written so
  a second, regex-based scanner for another ecosystem can populate the same
  shape later without a breaking change.
- No attempt to resolve `evidence_refs`-style provenance between a test and
  the mutation-testing receipt that exercised it — that is a natural, but
  unbuilt, bridge to 1-B's evidence graph, named again under Open questions.

---

## Test plan per package

| Package | Test file | Asserts |
| --- | --- | --- |
| 1-A | `tests/test_policy_ask.py` | unlisted domain -> `ASK`; non-GET without `allow_non_get` -> hard `DENY`; full coverage + zero external variables -> `ALLOW`; `ask_threshold` never degrades `ASK` to `DENY`; `path_outside_root` -> `ASK`; all four trust levels produce their documented decision on the same fixture event; damaged/missing trust file -> `UNOBSERVED`; `as_dict()` key set excludes `probability`/`confidence` |
| 1-A | `tests/test_policy_trust.py` | `grant`/`show` round-trip; `min(cap, granted)` effective-level math; non-interactive `grant` without `HYODO_POLICY_TRUST_ALL` refuses; `history` accumulates prior grants |
| 1-A | `tests/test_policy_self_report_boundary.py` (extended) | a caller cannot assert its own `ASK` any more than it could assert `ALLOW`/`DENY` today — `policy.claimed` isolation holds for the new value |
| 1-A | `tests/test_cli_policy_check.py` (new) | `policy check` exit 3 on `ASK`; `event record --policy` exit 3 on `ASK` and exit 2 on an `evaluate_policy`-produced `UNOBSERVED` (regression pinning the `cli/main.py:2290` fix) |
| 1-B | `tests/test_agent_events.py` (extended) | `UNOBSERVED` accepted under `policy.claimed`; `tool.urls` format validation (domain required, digest optional 12-hex); `tool.method` restricted to the HTTP-verb allowlist |
| 1-B | `tests/test_event_edges.py` (new) | valid parent/evidence edges pass; a dangling `parent_event_id` or `evidence_refs` entry is rejected at `event record` time with exit 1 and is **not** appended to the ledger; a malformed `gate:` reference fails the stateless check before any ledger read |
| 1-B | `tests/test_report_graph.py` (new) | a mission-less run with `require_mission_prompt=true` shows "intent unobserved"; `broken_edges` from a corrupted ledger line -> exit 1; a clean graph snapshot matches a fixed JSON fixture byte-for-byte (determinism) |
| 1-C | `tests/test_verdict_line.py` (new) | `render_verdict_line` output format exactly matches the documented template for several `(decision, observed, expected, unit, detail)` combinations |
| 1-C | `tests/test_explain_flag.py` (new) | two consecutive `--explain` runs against the same fixture produce identical output; exit codes are unchanged by `--explain`/`--quiet`; `check --json` schema matches `safe --json`'s field-naming convention |
| 1-D | `tests/test_connect.py` (new) | dry-run output for each detected harness matches a fixture without writing any file; `--write` is idempotent (a second `--write` changes nothing); no `$HOME` file is touched without `--global`; first write of a pre-existing foreign file produces a `.bak` |
| 1-D | `tests/test_connect_hooks.py` (new) | Claude Code hook payload -> `hyodo.agent-event/v1` field mapping (`tool_use_id`->`event_id`, `session_id`->`run_id`, `tool_input.file_path`->`tool.paths`, `tool_input.url`->`tool.urls`); exit-code table (`ALLOW`->0, `DENY`->2, `ASK`->2 with the "ask the human" stderr text, `UNOBSERVED`->2); malformed/empty stdin -> exit 2 with an `UNOBSERVED` stderr message, never exit 0 |
| 1-E | `tests/test_test_integrity.py` (new) | a fixture file with a no-op test body is flagged `no_assertion`; a fixture with `assert 1 == 1` only is flagged `constant_assertion`; a fixture with a real `assert` on a computed value is not flagged; `@pytest.mark.skip` without `reason=` is flagged, with `reason=` it is not; `# hyodo: allow-vacuous` suppresses `no_target_reference` for that function; `check --strict-tests` against a vacuous-only fixture project exits 1, and the same fixture without the flag exits 0 |

---

## Rollout order and non-breakage constraints

1. **1-A** (`feat/policy-ask`) lands first — everything else in Phase 1 reads
   `PolicyConfig`/`PolicyDecision`. Must not break: any existing
   `policy.toml` (no `[web]`/`[trust]`), the 0/1/2 exit contract for every
   decision that predates `ASK`, and `tests/test_policy_self_report_
   boundary.py` as it exists today.
2. **1-B** (`feat/evidence-graph`) lands second — it extends the same event
   schema 1-A's `tool.method`/`tool.urls` fields already touch. Must not
   break: every existing ledger line's re-validation round-trip, and
   `report`'s existing `md`/`html`/`sarif` output byte-for-byte.
3. **1-C** (`feat/verdict-line`) lands third — it wraps `check`/`safe`/
   `policy check` output but must not change any of their exit codes,
   including the new ones 1-A introduced. Must not break: every test that
   greps `check`/`safe` stdout for today's phrasing (the verdict line is
   additive, the detail lines it summarizes stay unless `--quiet`).
4. **1-D** (`feat/connect`) lands fourth — its Claude Code hook shells out to
   `policy check --hook claude-code` and `event record --hook claude-code`,
   both introduced here for the first time; it depends on 1-A's exit
   contract and 1-B's `tool.urls`/`tool.method` mapping already existing.
   Must not break: nothing pre-existing, since `connect` is a wholly new,
   opt-in command and default dry-run mode never writes.
5. **1-E** (`feat/test-integrity`) lands last — independent of 1-A through
   1-D in data model, but ordered last because it is the only package that
   can change `check`'s exit code for an existing checkout (via
   `--strict-tests`), and that flag should ship once the verdict-line/
   `--json` surface from 1-C exists to report it through. Must not break:
   `check`'s default (no `--strict-tests`) behavior for every existing
   checkout, including HyoDo's own.

Each PR is TDD (tests open the PR, per package above), and must pass `ruff
check hyodo/ --fix && ruff format hyodo/`, `pytest tests -q`, `pyright
hyodo`, `hyodo check`, and `hyodo safe --strict` before merge, per this
repository's existing contributor workflow.

---

## Open questions

- Whether `require_mission_prompt` should ever become default-`true`. It is
  opt-in in this design specifically because most ledgers recorded before
  1-B never declared an opening intent, and flipping the default would
  retroactively flag them; the owner may choose to make it mandatory once
  enough adopters have migrated, per the design input's own note ("owner may
  later make mandatory").
- Canonical web tool names per harness beyond the built-in six
  (`web_fetch, browser, http, fetch, WebFetch, WebSearch`). Claude Code's
  `WebFetch`/`WebSearch` are already covered; Codex's and Cursor's own
  built-in tool names for web access are not yet confirmed against a live
  install, so `ask_tools` remains the escape hatch for whatever a given
  harness calls its web tool until each is verified.
- Codex's hook contract for 1-D is verified against
  `developers.openai.com/codex/hooks` documentation only, not against a
  running Codex CLI. Before the Codex adapter ships, the exact `PostToolUse`
  payload field carrying a tool's result (for `io.output_digest`) needs
  confirmation against a real install; the `PreToolUse` mapping is expected
  to need no changes.
- Whether `ASK` should ever be distinguished from `DENY` at the harness
  level once a harness supports a genuine third outcome (pause and ask a
  human, rather than proceed/block). Today's design accepts "`ASK` enforces
  as blocked" as the honest current limit of Claude Code's and Codex's
  documented hook contracts, not as HyoDo's own preference.
- Whether a `gate:<name>@<hash>` evidence reference should be resolved
  against an actual persisted gate-run record in a future phase (Phase 1
  only checks its shape, not its existence) — this is the natural bridge
  between 1-B's evidence graph and 1-E's/mutation-testing's gate results,
  left unbuilt here.
- Whether `evidence_refs` pointing across `run_id`s should carry any
  additional constraint (e.g. the referenced run must have completed) —
  Phase 1 allows it unconditionally.
