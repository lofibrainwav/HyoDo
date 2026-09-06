# Policy ASK (Phase 1-A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `evaluate_policy` a real `ASK` decision driven by observed
external variables (unlisted web domains, paths outside the project root,
discretionary tools) and an operator-controlled trust ladder, without
changing the outcome of any `policy.toml` that predates this feature.
**Architecture:** `hyodo/policy.py` gains `WebPolicy`/`TrustPolicy` config
dataclasses, three new `PolicyDecision` fields, and a rewritten
`evaluate_policy` pipeline; a new `hyodo/policy_trust.py` module owns the
untracked `.hyodo/policy-trust.json` grant store (mirroring
`hyodo/gates.py`'s gate-trust store) so `policy.py` stays a pure evaluator;
`hyodo/events.py` gains `UNOBSERVED` in `POLICY_DECISIONS` plus minimal
`tool.method`/`tool.urls` schema fields; `hyodo/cli/main.py` wires the new
`ASK` exit code (3) into `policy check` / `event record --policy` and adds
`hyodo policy trust grant`/`show`.
**Tech Stack:** Python 3.10+, typer, tomllib/tomli, pytest, ruff, pyright
**Spec:** docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md

## Global Constraints

- English only — code, comments, docstrings, commit messages, this plan.
- No `probability`/`confidence` key (or any float) ever appears in `PolicyDecision.as_dict()`.
- Schema id stays `hyodo.policy/v1`; no schema version bump.
- Every existing `policy.toml` (no `[web]`/`[trust]`/`ask_tools`) must produce byte-identical `evaluate_policy` decisions to today.
- Exit contract: `ALLOW` 0, `DENY` 1, `UNOBSERVED` 2, `ASK` 3 — for both `policy check` and `event record --policy`.
- Hard `DENY` rules always win before `ASK`; trust level never softens a hard `DENY`.
- `ASK` never degrades to `DENY`, even when `ask_threshold` is exceeded — the threshold only annotates `reason`/detail text.
- The granted trust level lives only in the untracked `.hyodo/policy-trust.json`; the tracked `policy.toml`'s `[trust].max_level` only caps what can be granted, it never grants anything itself.
- Effective trust level is always `min(max_level, granted_level)`; level `>= 2` requires an observable ledger (`observed_steps is not None`), else `UNOBSERVED`.
- `[trust]` present but the trust store missing/damaged, for an event with at least one external variable, is `UNOBSERVED` (`rule_id="trust_grant_unobserved"`) — never a default grant, never a crash.
- Run `ruff check hyodo tests --fix && ruff format hyodo tests && pyright hyodo && pytest tests -q` before every commit.
- Commit messages in English ending with the trailer lines `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_01PH1ofuuGrbVpW3vsBfaqPT`.
- Never use `git add -A` or `git add .` — stage files by explicit path.

## Scoping note (read before Task 1)

The spec's own "Evaluation order" rules for 1-A (`web_domain_unlisted`,
`web_credential_path_denied`, `web_non_get_denied`, and the "web boundary"
coverage row) all read a URL's `domain`/`path` off `tool.urls`. The spec's
1-B section formally assigns the full `tool.urls` schema (with a
`digest`-based, evidence-graph-aware shape) to Package 1-B, not 1-A. Taken
literally, that would make every 1-A web rule permanently unreachable
(`tool.urls` would never exist on a normalized event before 1-B ships), which
contradicts 1-A's own required test-plan row ("unlisted domain -> ASK").

This plan resolves that tension the way the rest of this codebase resolves
"cannot be checked": it adds a **minimal, 1-A-scoped** `tool.urls` field to
`hyodo/events.py` (`{"domain": str, "path": str | None}` — plaintext, no
digest) in Task 4, sufficient for 1-A's own rules, and calls this out
explicitly so a reviewer understands it is a deliberate, load-bearing
decision, not scope creep. Package 1-B (out of scope here) is expected to
layer its digest-based shape on top without changing any 1-A decision
outcome, since `domain` stays plaintext in both designs per the spec's own
1-B text ("domain is kept in plain text ... needed for the `[web]` allowlist
check in 1-A").

## File structure

| File | Change |
| --- | --- |
| `hyodo/events.py` | `POLICY_DECISIONS` gains `"UNOBSERVED"`; `tool.method` (HTTP-verb allowlist) and minimal `tool.urls` (`domain` + `path`) added to `validate_event`'s `tool` sub-object |
| `hyodo/policy.py` | `WebPolicy`/`TrustPolicy` dataclasses; `PolicyConfig` gains `web`/`ask_tools`/`ask_threshold`/`trust`; `PolicyDecision` gains `coverage`/`external_variables`/`trust_level` (all serialized by `as_dict()`); `load_policy_config` parses the new fields; new module-level helpers (`_is_web_classified`, `_domain_allowed`, `_credential_shaped`, `_compute_coverage`, `_resolve_trust_level`); `evaluate_policy` gains `root` keyword and the full ASK/trust pipeline; module docstring gains the "optional fields only" contract paragraph |
| `hyodo/policy_trust.py` | **New.** Untracked `.hyodo/policy-trust.json` grant store — `PolicyTrustGrant`/`PolicyTrustState` dataclasses, `load_policy_trust`, `grant_policy_trust`, `effective_trust_level`, `default_granted_by`, `resolve_policy_trust_grant` (the interactive/non-interactive gate, mirroring `hyodo.gates.resolve_gate_trust`). Kept separate from `hyodo/policy.py` so the pure evaluator has no file-I/O side effects of its own and no CLI/TTY concerns — mirrors how `hyodo/gates.py` owns its own trust store rather than folding it into the gate-execution module. |
| `hyodo/cli/main.py` | `policy_check`'s exit-code ternary becomes a 4-way dict lookup (line ~2413); `event_record`'s exit-code ternary becomes the same 4-way dict lookup keyed by `decision_label` (line ~2290), fixing the `UNOBSERVED`-exits-0 gap; both `evaluate_policy` call sites pass `root=`; `policy check --json`/text gain the trust-level-2+ ledger-obligation note; new `policy_trust_app` sub-typer with `grant`/`show` commands; docstrings updated for exit 3 |
| `examples/fde-evidence-spine/policy.toml` | Commented-out `[web]`/`[trust]` example block, matching the file's existing per-field annotation style |
| `README.md` | Exit-contracts table row for `event`/`policy` gains `3` ASK |
| `CHANGELOG.md` | `Unreleased` gains an `ASK`/trust-ladder entry under Added, and the `event record` UNOBSERVED exit-code fix under Fixed |
| `hyodo/mcp_server.py` | `hyodo_policy_check`'s docstring documents exit 3 = ASK (no code change — `_run_cli` already forwards the exit code) |
| `tests/test_policy_self_report_boundary.py` | Extended: claimed `ASK` isolation test |
| `tests/test_agent_events.py` | Extended: `tool.method` HTTP-verb-allowlist tests, minimal `tool.urls` format tests |
| `tests/test_policy_ask.py` | **New.** `PolicyDecision`/`PolicyConfig` guard tests, external-variable/coverage/trust-level acceptance tests, full `evaluate_policy` pipeline tests |
| `tests/test_policy_trust.py` | **New.** `policy_trust.py` unit tests + `hyodo policy trust grant`/`show` CLI tests |
| `tests/test_cli_policy_check.py` | **New.** `policy check` exit 3 on `ASK`; `event record --policy` exit 3 on `ASK` and exit 2 on `evaluate_policy`-produced `UNOBSERVED` (regression pinning the `cli/main.py:2290` fix) |

---

## Tasks

### Task 1: `POLICY_DECISIONS` gains `UNOBSERVED`; claimed-`ASK` isolation

**Files:** Modify `hyodo/events.py` (line 38); Test `tests/test_policy_self_report_boundary.py`
**Interfaces:** Consumes: nothing new. Produces: `POLICY_DECISIONS: frozenset[str]` now `frozenset({"ALLOW", "DENY", "ASK", "UNOBSERVED"})`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_policy_self_report_boundary.py — add after test_caller_assertion_is_preserved_for_audit


def test_caller_asserted_ask_is_not_a_decision():
    ok, reasons, normalized = validate_event(
        _event(policy={"decision": "ASK", "reason": "trust me, ask later"})
    )
    assert ok, reasons
    assert normalized is not None
    assert normalized["policy"]["decision"] is None
    assert normalized["policy"]["evaluated_by"] is None
    assert normalized["policy"]["claimed"] == {
        "decision": "ASK",
        "rule_id": None,
        "reason": "trust me, ask later",
    }


def test_caller_asserted_unobserved_is_not_a_decision():
    """UNOBSERVED must be assertable-and-quarantined exactly like ALLOW/DENY/ASK —
    a caller cannot claim its own unobservedness into a measured decision either."""
    ok, reasons, normalized = validate_event(
        _event(policy={"decision": "UNOBSERVED", "reason": "i could not tell"})
    )
    assert ok, reasons
    assert normalized is not None
    assert normalized["policy"]["decision"] is None
    assert normalized["policy"]["evaluated_by"] is None
    assert normalized["policy"]["claimed"] == {
        "decision": "UNOBSERVED",
        "rule_id": None,
        "reason": "i could not tell",
    }
```

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/bin/python -m pytest tests/test_policy_self_report_boundary.py::test_caller_asserted_ask_is_not_a_decision tests/test_policy_self_report_boundary.py::test_caller_asserted_unobserved_is_not_a_decision -v`
  Expected: FAIL — `ok` is `False` and `normalized` is `None`, because `validate_event` currently appends `invalid_field:policy.decision` for both `"ASK"` and `"UNOBSERVED"` (only `"ASK"` is missing from today's frozenset alongside `"UNOBSERVED"`; today's `POLICY_DECISIONS = frozenset({"ALLOW", "DENY", "ASK"})` already contains `"ASK"`, so only the `UNOBSERVED` test fails today — confirm both cases explicitly in the run output).

- [ ] **Step 3: Write minimal implementation**

```python
# hyodo/events.py — line 38, replace:
# POLICY_DECISIONS = frozenset({"ALLOW", "DENY", "ASK"})
# with:
POLICY_DECISIONS = frozenset({"ALLOW", "DENY", "ASK", "UNOBSERVED"})
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/bin/python -m pytest tests/test_policy_self_report_boundary.py -v`
  Expected: PASS (all tests in the file, including the two new ones).

- [ ] **Step 5: Run the full gate** — `.venv/bin/ruff check hyodo tests --fix && .venv/bin/ruff format hyodo tests && .venv/bin/pyright hyodo && .venv/bin/python -m pytest tests -q`

- [ ] **Step 6: Commit**

```bash
git add hyodo/events.py tests/test_policy_self_report_boundary.py
git commit -m "$(cat <<'EOF'
feat(policy): accept UNOBSERVED under policy.claimed

POLICY_DECISIONS was missing UNOBSERVED, so a caller asserting
{"policy": {"decision": "UNOBSERVED"}} in its own event failed
validate_event with invalid_field:policy.decision instead of being
quarantined under policy.claimed like ALLOW/DENY/ASK. Only
evaluate_policy() can produce a measured UNOBSERVED; this only widens
what a caller may assert about itself, which is preserved for audit
and never promoted to evidence.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PH1ofuuGrbVpW3vsBfaqPT
EOF
)"
```

---

### Task 2: `PolicyDecision` gains `coverage`/`external_variables`/`trust_level`

**Files:** Modify `hyodo/policy.py` (lines 50-70); Test `tests/test_policy_ask.py` (new)
**Interfaces:** Consumes: nothing new. Produces:
`PolicyDecision(decision: str, rule_id: str | None, reason: str | None, coverage: tuple[int, int] = (0, 0), external_variables: tuple[str, ...] = (), trust_level: int = 1)`;
`PolicyDecision.as_dict() -> dict[str, Any]` with exactly the keys
`{"decision", "rule_id", "reason", "evaluated_by", "coverage", "external_variables", "trust_level"}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_policy_ask.py — new file

"""TDD for HyoDo Phase 1-A: ASK, external variables, trust, [web].

Spec: docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md,
Package 1-A.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from hyodo.events import AGENT_EVENT_SCHEMA_VERSION, content_digest, validate_event
from hyodo.policy import (
    POLICY_SCHEMA_ID,
    PolicyConfig,
    PolicyConfigError,
    PolicyDecision,
    TrustPolicy,
    WebPolicy,
    evaluate_policy,
    load_policy_config,
)
from hyodo.policy_trust import (
    POLICY_TRUST_SCHEMA_ID,
    grant_policy_trust,
    load_policy_trust,
)


def _event(**overrides: object) -> dict:
    base: dict = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "run_id": "run-ask",
        "ts": "2026-09-06T12:00:00+00:00",
        "kind": "tool_call",
        "step_index": 0,
        "actor": "agent",
        "tool": {"name": "search", "args_digest": content_digest("{}"), "paths": []},
        "io": {"input_digest": content_digest("in"), "output_digest": None},
        "meta": {"model": "test-model", "tags": ["unit"]},
    }
    base.update(overrides)
    return base


def _normalize(raw: dict) -> dict:
    ok, reasons, normalized = validate_event(raw)
    assert ok, reasons
    assert normalized is not None
    return normalized


def _bare_policy(**overrides: object) -> PolicyConfig:
    base: dict = dict(
        schema=POLICY_SCHEMA_ID,
        max_steps=None,
        allowed_tools=None,
        blocked_path_globs=(),
    )
    base.update(overrides)
    return PolicyConfig(**base)


# --------------------------------------------------------------------------- #
# PolicyDecision — new fields, no-probability guard
# --------------------------------------------------------------------------- #


def test_policy_decision_as_dict_key_set_excludes_probability_and_confidence():
    decision = PolicyDecision(
        decision="ASK",
        rule_id="external_variable",
        reason="1 external variable(s)",
        coverage=(2, 3),
        external_variables=("ask_tools:WebFetch",),
        trust_level=1,
    )
    payload = decision.as_dict()
    assert set(payload.keys()) == {
        "decision",
        "rule_id",
        "reason",
        "evaluated_by",
        "coverage",
        "external_variables",
        "trust_level",
    }
    assert "probability" not in payload
    assert "confidence" not in payload
    assert not any(isinstance(v, float) for v in payload.values())


def test_policy_decision_new_fields_default_for_backward_compatible_construction():
    """Existing callers that only pass decision/rule_id/reason must still work."""
    decision = PolicyDecision(decision="ALLOW", rule_id=None, reason=None)
    assert decision.coverage == (0, 0)
    assert decision.external_variables == ()
    assert decision.trust_level == 1
```

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/bin/python -m pytest tests/test_policy_ask.py -v`
  Expected: FAIL with `TypeError: PolicyDecision.__init__() got an unexpected keyword argument 'coverage'` (and the file fails to collect the `PolicyConfigError`/`TrustPolicy`/`WebPolicy`/`policy_trust` imports too — those land in Tasks 3 and 6; for this step, comment out or accept collection errors for the not-yet-existing imports is **not** an option under "no placeholders", so this test file is written in full now and Task 2's two tests are expected to fail at collection time until Tasks 3 and 6 also land. Run the narrower selector instead once Task 3/6 imports exist: for Task 2 alone, verify with `.venv/bin/python -c "from hyodo.policy import PolicyDecision; PolicyDecision(decision='ALLOW', rule_id=None, reason=None, coverage=(0,0), external_variables=(), trust_level=1)"`, which raises the same `TypeError` today.)

- [ ] **Step 3: Write minimal implementation**

```python
# hyodo/policy.py — replace the PolicyDecision class (lines 50-70)

@dataclass(frozen=True)
class PolicyDecision:
    """Result of evaluating one event against a policy."""

    decision: str  # ALLOW | DENY | ASK | UNOBSERVED
    rule_id: str | None
    reason: str | None
    #: (observed, expected) boundary surfaces actually checked for this event.
    #: Integers only — never a ratio, percentage, or probability.
    coverage: tuple[int, int] = (0, 0)
    #: rule-id-shaped identifiers of every discretionary condition this event
    #: tripped, e.g. ("web_domain_unlisted:api.example.com",). Empty when none.
    external_variables: tuple[str, ...] = ()
    #: The effective trust level (min(cap, granted)) used to reach this decision.
    trust_level: int = 1

    def as_dict(self) -> dict[str, Any]:
        """Serialize the decision for ledger stamping and JSON CLI output.

        ``evaluated_by`` marks this as a *measured* decision. A PolicyDecision can only
        come from :func:`evaluate_policy`, so its presence in the ledger is proof HyoDo
        ran the policy rather than trusting the caller.

        Honesty rule: this dict may never grow a ``probability`` or ``confidence``
        key. "How sure are we" is answered as ``coverage`` — an integer
        ``observed / expected`` pair — never as a float.
        """
        return {
            "decision": self.decision,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "evaluated_by": POLICY_SCHEMA_ID,
            "coverage": list(self.coverage),
            "external_variables": list(self.external_variables),
            "trust_level": self.trust_level,
        }
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/bin/python -m pytest tests/test_policy_ask.py::test_policy_decision_as_dict_key_set_excludes_probability_and_confidence tests/test_policy_ask.py::test_policy_decision_new_fields_default_for_backward_compatible_construction -v`
  Expected: PASS for these two tests (the file's other imports, e.g. `PolicyConfigError`, `TrustPolicy`, `WebPolicy`, `hyodo.policy_trust`, do not exist yet and are added in Tasks 3 and 6 — the full file is only collectible starting at the end of Task 6; this is a known, deliberate ordering artifact of writing the whole test file up front, called out again in Task 6, Step 4).

- [ ] **Step 5: Run the full gate** — `.venv/bin/ruff check hyodo tests --fix && .venv/bin/ruff format hyodo tests && .venv/bin/pyright hyodo && .venv/bin/python -m pytest tests -q --ignore=tests/test_policy_ask.py`
  (`test_policy_ask.py` is excluded from the full-suite run until Task 6 makes it fully collectible; each task after this one re-adds the pieces it needs and Task 6's Step 4 runs the complete file.)

- [ ] **Step 6: Commit**

```bash
git add hyodo/policy.py tests/test_policy_ask.py
git commit -m "$(cat <<'EOF'
feat(policy): PolicyDecision gains coverage/external_variables/trust_level

Adds the three Phase 1-A fields to PolicyDecision.as_dict(), each
defaulted so existing PolicyDecision(...) call sites keep compiling.
A guard test pins as_dict()'s key set so no future field can smuggle
in a probability/confidence value under a different name.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PH1ofuuGrbVpW3vsBfaqPT
EOF
)"
```

---

### Task 3: `PolicyConfig` gains `web`/`ask_tools`/`ask_threshold`/`trust`

**Files:** Modify `hyodo/policy.py` (lines 29-127); Test `tests/test_policy_ask.py`
**Interfaces:** Consumes: nothing new. Produces:
`WebPolicy(allowed_domains: tuple[str, ...] = (), allow_non_get: bool = False, allow_credential_paths: bool = False)`;
`TrustPolicy(max_level: int = 3)`;
`PolicyConfig` gains `web: WebPolicy | None = None`, `ask_tools: tuple[str, ...] = ()`, `ask_threshold: int | None = None`, `trust: TrustPolicy | None = None`;
`load_policy_config(path: Path) -> PolicyConfig` parses all four, raising `PolicyConfigError` on bad shape.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_policy_ask.py — append


# --------------------------------------------------------------------------- #
# PolicyConfig parsing — [web], ask_tools, ask_threshold, [trust]
# --------------------------------------------------------------------------- #


def test_load_policy_config_defaults_new_fields_when_absent(tmp_path: Path):
    path = tmp_path / "policy.toml"
    path.write_text(f'schema = "{POLICY_SCHEMA_ID}"\n', encoding="utf-8")
    cfg = load_policy_config(path)
    assert cfg.web is None
    assert cfg.ask_tools == ()
    assert cfg.ask_threshold is None
    assert cfg.trust is None


def test_load_policy_config_parses_web_and_trust(tmp_path: Path):
    path = tmp_path / "policy.toml"
    path.write_text(
        f'''schema = "{POLICY_SCHEMA_ID}"

[web]
allowed_domains = ["api.example.com", "*.internal.example.com"]
allow_non_get = false
allow_credential_paths = false

ask_tools = ["send_email"]
ask_threshold = 2

[trust]
max_level = 2
''',
        encoding="utf-8",
    )
    cfg = load_policy_config(path)
    assert cfg.web == WebPolicy(
        allowed_domains=("api.example.com", "*.internal.example.com"),
        allow_non_get=False,
        allow_credential_paths=False,
    )
    assert cfg.ask_tools == ("send_email",)
    assert cfg.ask_threshold == 2
    assert cfg.trust == TrustPolicy(max_level=2)


def test_load_policy_config_rejects_out_of_range_max_level(tmp_path: Path):
    path = tmp_path / "policy.toml"
    path.write_text(
        f'''schema = "{POLICY_SCHEMA_ID}"

[trust]
max_level = 7
''',
        encoding="utf-8",
    )
    with pytest.raises(PolicyConfigError):
        load_policy_config(path)


def test_load_policy_config_rejects_non_bool_allow_non_get(tmp_path: Path):
    path = tmp_path / "policy.toml"
    path.write_text(
        f'''schema = "{POLICY_SCHEMA_ID}"

[web]
allow_non_get = "yes"
''',
        encoding="utf-8",
    )
    with pytest.raises(PolicyConfigError):
        load_policy_config(path)


def test_load_policy_config_rejects_non_negative_ask_threshold():
    pass  # placeholder removed below — see full assertion
```

Replace the placeholder with a real assertion (never leave a `pass` body in
the committed file — this draft step exists only to show the fixture is
written before the implementation; the version actually committed is:

```python
def test_load_policy_config_rejects_negative_ask_threshold(tmp_path: Path):
    path = tmp_path / "policy.toml"
    path.write_text(
        f'''schema = "{POLICY_SCHEMA_ID}"

ask_threshold = -1
''',
        encoding="utf-8",
    )
    with pytest.raises(PolicyConfigError):
        load_policy_config(path)
```

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/bin/python -m pytest tests/test_policy_ask.py -k "load_policy_config" -v`
  Expected: FAIL — `from hyodo.policy import ... WebPolicy, TrustPolicy` raises `ImportError` (names do not exist yet), and once stubbed, `load_policy_config` raises `TypeError: PolicyConfig.__init__() got an unexpected keyword argument` or simply ignores the new TOML keys.

- [ ] **Step 3: Write minimal implementation**

```python
# hyodo/policy.py — insert after PolicyConfigError, before PolicyConfig


@dataclass(frozen=True)
class WebPolicy:
    """Web boundary for tools HyoDo judges as web-classified. All optional."""

    allowed_domains: tuple[str, ...] = ()
    allow_non_get: bool = False
    allow_credential_paths: bool = False


@dataclass(frozen=True)
class TrustPolicy:
    """Caps (never grants) the operator-controlled trust level. See hyodo.policy_trust."""

    max_level: int = 3
```

```python
# hyodo/policy.py — PolicyConfig gains four fields after require_declared_paths

@dataclass(frozen=True)
class PolicyConfig:
    """Parsed agent policy."""

    schema: str
    max_steps: int | None
    allowed_tools: tuple[str, ...] | None  # None = no allowlist restriction
    blocked_path_globs: tuple[str, ...]
    #: Opt-in strict mode. ``blocked_path_globs`` can only inspect paths the caller
    #: *declared*; a tool event with ``paths: []`` sails past it. Turning this on makes
    #: that silence UNOBSERVED instead of ALLOW. It is off by default because plenty of
    #: legitimate tools (search, http, …) touch no paths, and flagging all of them would
    #: push operators to delete blocked_path_globs entirely — a worse outcome.
    require_declared_paths: bool = False
    #: Phase 1-A. Absent = no web boundary at all; a web-shaped tool call is judged
    #: only by allowed_tools/ask_tools, unchanged from pre-Phase-1 behavior.
    web: WebPolicy | None = None
    #: Phase 1-A. Tools judged discretionary (ASK-eligible) beyond the built-in
    #: web-tool set. Absent/empty = only the built-in set is discretionary.
    ask_tools: tuple[str, ...] = ()
    #: Phase 1-A. Annotates the ASK reason/detail text only — never changes the
    #: decision or exit code. Absent = no severity annotation.
    ask_threshold: int | None = None
    #: Phase 1-A. Caps (never grants) the trust level read from
    #: .hyodo/policy-trust.json (hyodo.policy_trust). Absent = effective level
    #: is always 1 (today's ALLOW/ASK-on-any-external-variable behavior).
    trust: TrustPolicy | None = None

    @property
    def allowlist_active(self) -> bool:
        """True when ``allowed_tools`` is set (including empty = deny all tools)."""
        return self.allowed_tools is not None
```

```python
# hyodo/policy.py — load_policy_config: insert before the final `return PolicyConfig(...)`

    web_raw = raw.get("web")
    web: WebPolicy | None = None
    if web_raw is not None:
        if not isinstance(web_raw, dict):
            raise PolicyConfigError(f"{path}: [web] must be a table")
        allowed_domains_raw = web_raw.get("allowed_domains", [])
        if not isinstance(allowed_domains_raw, list) or not all(
            isinstance(d, str) and d for d in allowed_domains_raw
        ):
            raise PolicyConfigError(
                f"{path}: web.allowed_domains must be a list of non-empty strings"
            )
        allow_non_get = web_raw.get("allow_non_get", False)
        if not isinstance(allow_non_get, bool):
            raise PolicyConfigError(f"{path}: web.allow_non_get must be a boolean")
        allow_credential_paths = web_raw.get("allow_credential_paths", False)
        if not isinstance(allow_credential_paths, bool):
            raise PolicyConfigError(f"{path}: web.allow_credential_paths must be a boolean")
        web = WebPolicy(
            allowed_domains=tuple(allowed_domains_raw),
            allow_non_get=allow_non_get,
            allow_credential_paths=allow_credential_paths,
        )

    ask_tools_raw = raw.get("ask_tools", [])
    if not isinstance(ask_tools_raw, list) or not all(
        isinstance(t, str) and t for t in ask_tools_raw
    ):
        raise PolicyConfigError(f"{path}: ask_tools must be a list of non-empty strings")
    ask_tools = tuple(ask_tools_raw)

    ask_threshold = raw.get("ask_threshold")
    if ask_threshold is not None and (
        not isinstance(ask_threshold, int)
        or isinstance(ask_threshold, bool)
        or ask_threshold < 0
    ):
        raise PolicyConfigError(f"{path}: ask_threshold must be a non-negative integer")

    trust_raw = raw.get("trust")
    trust: TrustPolicy | None = None
    if trust_raw is not None:
        if not isinstance(trust_raw, dict):
            raise PolicyConfigError(f"{path}: [trust] must be a table")
        max_level = trust_raw.get("max_level", 3)
        if (
            not isinstance(max_level, int)
            or isinstance(max_level, bool)
            or not (0 <= max_level <= 3)
        ):
            raise PolicyConfigError(f"{path}: trust.max_level must be an integer between 0 and 3")
        trust = TrustPolicy(max_level=max_level)

    return PolicyConfig(
        schema=schema,
        max_steps=max_steps,
        allowed_tools=allowed_tools,
        blocked_path_globs=blocked,
        require_declared_paths=require_declared_paths,
        web=web,
        ask_tools=ask_tools,
        ask_threshold=ask_threshold,
        trust=trust,
    )
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/bin/python -m pytest tests/test_policy_ask.py -k "load_policy_config" -v`
  Expected: PASS (all five `load_policy_config`-related tests).

- [ ] **Step 5: Run the full gate** — `.venv/bin/ruff check hyodo tests --fix && .venv/bin/ruff format hyodo tests && .venv/bin/pyright hyodo && .venv/bin/python -m pytest tests -q --ignore=tests/test_policy_ask.py && .venv/bin/python -m pytest tests/test_policy_ask.py -k "load_policy_config or PolicyDecision" -v`

- [ ] **Step 6: Commit**

```bash
git add hyodo/policy.py tests/test_policy_ask.py
git commit -m "$(cat <<'EOF'
feat(policy): PolicyConfig parses [web], ask_tools, ask_threshold, [trust]

All four fields are optional, following the "optional fields only"
convention require_declared_paths already established: a policy.toml
with none of them evaluates identically to today. Adds WebPolicy and
TrustPolicy dataclasses; TrustPolicy.max_level only caps a granted
trust level (hyodo.policy_trust), it never grants one.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PH1ofuuGrbVpW3vsBfaqPT
EOF
)"
```

---

### Task 4: `events.py` schema — `tool.method` and minimal `tool.urls`

**Files:** Modify `hyodo/events.py` (lines 27-40, 123-153, 259-261); Test `tests/test_agent_events.py`
**Interfaces:** Consumes: nothing new. Produces: `validate_event`'s normalized `tool` sub-object gains `method: str | None` (restricted to `GET|HEAD|POST|PUT|PATCH|DELETE`, case-insensitive input normalized to upper-case) and `urls: list[{"domain": str, "path": str | None}]` (see Scoping note above for why `path` is plaintext here rather than 1-B's `digest`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_agent_events.py — append near the schema-unit tests (after test_digest_from_full_body_and_strip)


def test_validate_tool_method_normalizes_case_and_restricts_to_http_verbs():
    ok, reasons, normalized = validate_event(
        _valid_event(tool={"name": "web_fetch", "args_digest": None, "paths": [], "method": "get"})
    )
    assert ok, reasons
    assert normalized is not None
    assert normalized["tool"]["method"] == "GET"


def test_validate_tool_method_rejects_unknown_verb():
    ok, reasons, normalized = validate_event(
        _valid_event(
            tool={"name": "web_fetch", "args_digest": None, "paths": [], "method": "TRACE"}
        )
    )
    assert ok is False
    assert normalized is None
    assert "invalid_field:tool.method" in reasons


def test_validate_tool_method_absent_defaults_to_none():
    ok, reasons, normalized = validate_event(_valid_event())
    assert ok, reasons
    assert normalized is not None
    assert normalized["tool"]["method"] is None


def test_validate_tool_urls_round_trip():
    ok, reasons, normalized = validate_event(
        _valid_event(
            tool={
                "name": "web_fetch",
                "args_digest": None,
                "paths": [],
                "urls": [{"domain": "api.example.com", "path": "/v1/users"}],
            }
        )
    )
    assert ok, reasons
    assert normalized is not None
    assert normalized["tool"]["urls"] == [{"domain": "api.example.com", "path": "/v1/users"}]


def test_validate_tool_urls_absent_defaults_to_empty_list():
    ok, reasons, normalized = validate_event(_valid_event())
    assert ok, reasons
    assert normalized is not None
    assert normalized["tool"]["urls"] == []


def test_validate_tool_urls_rejects_missing_domain():
    ok, reasons, normalized = validate_event(
        _valid_event(
            tool={
                "name": "web_fetch",
                "args_digest": None,
                "paths": [],
                "urls": [{"path": "/v1/users"}],
            }
        )
    )
    assert ok is False
    assert normalized is None
    assert "invalid_field:tool.urls" in reasons
```

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/bin/python -m pytest tests/test_agent_events.py -k "tool_method or tool_urls" -v`
  Expected: FAIL — `KeyError`/`AssertionError`: today's `validate_event` never sets `tool_out["method"]` or `tool_out["urls"]`, so `normalized["tool"]["method"]`/`["urls"]` raise `KeyError`.

- [ ] **Step 3: Write minimal implementation**

```python
# hyodo/events.py — add near the top, after _DIGEST_RE (line 40)

#: Phase 1-A. HTTP verbs a `tool.method` may declare; anything else is a
#: schema validation error, not a silent pass. Case-insensitive on input,
#: normalized to upper-case.
_HTTP_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"})
```

```python
# hyodo/events.py — inside the `tool_raw` handling block (after the existing
# `paths` handling, still inside `else: tool_out = {}` — lines ~146-153)

            method = tool_raw.get("method")
            if method is not None:
                normalized_method = method.strip().upper() if isinstance(method, str) else None
                if normalized_method is None or normalized_method not in _HTTP_METHODS:
                    reasons.append("invalid_field:tool.method")
                else:
                    tool_out["method"] = normalized_method
            else:
                tool_out["method"] = None
            urls = tool_raw.get("urls")
            if urls is not None:
                if not isinstance(urls, list):
                    reasons.append("invalid_field:tool.urls")
                else:
                    normalized_urls: list[dict[str, Any]] = []
                    urls_ok = True
                    for entry in urls:
                        if not isinstance(entry, dict) or not _is_non_empty_str(
                            entry.get("domain")
                        ):
                            urls_ok = False
                            break
                        url_path = entry.get("path")
                        if url_path is not None and not isinstance(url_path, str):
                            urls_ok = False
                            break
                        normalized_urls.append({"domain": entry["domain"], "path": url_path})
                    if not urls_ok:
                        reasons.append("invalid_field:tool.urls")
                    else:
                        tool_out["urls"] = normalized_urls
            else:
                tool_out["urls"] = []
```

```python
# hyodo/events.py — the default tool dict when tool_raw is None (~line 259-261)
        "tool": tool_out
        if tool_out is not None
        else {"name": None, "args_digest": None, "paths": [], "method": None, "urls": []},
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/bin/python -m pytest tests/test_agent_events.py -v`
  Expected: PASS (the whole file, including all pre-existing tests — this is a purely additive schema change).

- [ ] **Step 5: Run the full gate** — `.venv/bin/ruff check hyodo tests --fix && .venv/bin/ruff format hyodo tests && .venv/bin/pyright hyodo && .venv/bin/python -m pytest tests -q --ignore=tests/test_policy_ask.py`

- [ ] **Step 6: Commit**

```bash
git add hyodo/events.py tests/test_agent_events.py
git commit -m "$(cat <<'EOF'
feat(events): tool.method and minimal tool.urls schema fields

tool.method (GET|HEAD|POST|PUT|PATCH|DELETE, case-insensitive input,
normalized upper-case) is Phase 1-A's own schema addition, needed by
evaluate_policy's new web_non_get_denied rule. tool.urls is added here
in minimal form (domain + plaintext path) so 1-A's web_domain_unlisted
and web_credential_path_denied rules have something to read before
Package 1-B's full digest-based tool.urls shape lands; domain stays
plaintext in both designs, so 1-B is expected to extend this without
changing any 1-A decision outcome. Both fields are optional and
default to None/[] — round-tripping an old ledger line is unaffected.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PH1ofuuGrbVpW3vsBfaqPT
EOF
)"
```

---

### Task 5: External-variable helpers, hard-DENY web rules, coverage math

**Files:** Modify `hyodo/policy.py` (append helpers after `_path_blocked`, before `evaluate_policy`); Test `tests/test_policy_ask.py`
**Interfaces:** Consumes: `WebPolicy`, `PolicyConfig` (Task 3), `tool.method`/`tool.urls` (Task 4). Produces:
`_is_web_classified(tool_name: str | None, policy: PolicyConfig) -> bool`;
`_domain_allowed(domain: str, allowed_domains: tuple[str, ...]) -> bool`;
`_credential_shaped(path: str | None) -> bool`;
`_compute_coverage(policy: PolicyConfig, kind: Any, tool_name: str | None, paths: list[Any], urls: list[Any], method: str | None, observed_steps: int | None, root: Path | None, *, effective_level: int) -> tuple[int, int]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_policy_ask.py — append


# --------------------------------------------------------------------------- #
# Helper functions — web classification, domain matching, credential shapes,
# coverage math. Unit-tested directly before evaluate_policy wires them in
# (Task 7).
# --------------------------------------------------------------------------- #

from hyodo.policy import (  # noqa: E402  (kept near the tests that use them)
    _compute_coverage,
    _credential_shaped,
    _domain_allowed,
    _is_web_classified,
)


def test_is_web_classified_builtin_set():
    policy = _bare_policy()
    for name in ("web_fetch", "browser", "http", "fetch", "WebFetch", "WebSearch"):
        assert _is_web_classified(name, policy) is True
    assert _is_web_classified("read_file", policy) is False
    assert _is_web_classified(None, policy) is False


def test_is_web_classified_includes_configured_ask_tools():
    policy = _bare_policy(ask_tools=("send_email",))
    assert _is_web_classified("send_email", policy) is True


def test_domain_allowed_exact_and_wildcard():
    allowed = ("api.example.com", "*.internal.example.com")
    assert _domain_allowed("api.example.com", allowed) is True
    assert _domain_allowed("svc.internal.example.com", allowed) is True
    assert _domain_allowed("evil.com", allowed) is False


def test_credential_shaped_path_and_query_markers():
    assert _credential_shaped("/wp-admin/") is True
    assert _credential_shaped("/.git/config") is True
    assert _credential_shaped("/.env") is True
    assert _credential_shaped("/v1/users?token=abc") is True
    assert _credential_shaped("/v1/users?api_key=abc") is True
    assert _credential_shaped("/v1/users?secret=abc") is True
    assert _credential_shaped("/v1/users") is False
    assert _credential_shaped(None) is False


def test_compute_coverage_full_when_allowlist_and_tool_name_present():
    policy = _bare_policy(allowed_tools=("search",))
    observed, expected = _compute_coverage(
        policy,
        "tool_call",
        "search",
        [],
        [],
        None,
        None,
        None,
        effective_level=1,
    )
    assert (observed, expected) == (1, 1)


def test_compute_coverage_counts_step_boundary_only_when_applicable():
    policy = _bare_policy(max_steps=10)
    observed, expected = _compute_coverage(
        policy, "prompt", None, [], [], None, 3, None, effective_level=1
    )
    # prompt kind: tool identity/web boundary don't apply; path boundary doesn't
    # apply (no blocked_path_globs, no root); only the step boundary applies.
    assert (observed, expected) == (1, 1)


def test_compute_coverage_step_boundary_unobserved_when_max_steps_set():
    policy = _bare_policy(max_steps=10)
    observed, expected = _compute_coverage(
        policy, "prompt", None, [], [], None, None, None, effective_level=1
    )
    assert (observed, expected) == (0, 1)
```

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/bin/python -m pytest tests/test_policy_ask.py -k "web_classified or domain_allowed or credential_shaped or compute_coverage" -v`
  Expected: FAIL with `ImportError: cannot import name '_is_web_classified' from 'hyodo.policy'` (and siblings).

- [ ] **Step 3: Write minimal implementation**

```python
# hyodo/policy.py — module-level constants, placed after POLICY_RELATIVE_PATH

#: Phase 1-A. Tool names HyoDo always treats as web-classified, regardless of
#: [web] being configured — see the design doc's Evaluation order §2.3.
_BUILTIN_WEB_TOOLS = frozenset({"web_fetch", "browser", "http", "fetch", "WebFetch", "WebSearch"})
#: HTTP verbs that never trigger web_non_get_denied.
_SAFE_HTTP_METHODS = frozenset({"GET", "HEAD"})
_CREDENTIAL_PATH_MARKERS = ("/.git/", "/.env", "/wp-admin/")
_CREDENTIAL_QUERY_MARKERS = ("token=", "api_key=", "secret=")
```

```python
# hyodo/policy.py — helpers, inserted after _path_blocked, before evaluate_policy


def _is_web_classified(tool_name: str | None, policy: PolicyConfig) -> bool:
    """True when *tool_name* is in the built-in web-tool set or policy.ask_tools.

    This is the single membership test the design doc's Evaluation order
    reuses for the web_non_get_denied / web_credential_path_denied hard-DENY
    rules, the web_domain_unlisted and ask_tools external variables, and the
    "web boundary" coverage row — deliberately one function, not four copies
    of the same set union.
    """
    if not isinstance(tool_name, str):
        return False
    return tool_name in _BUILTIN_WEB_TOOLS or tool_name in policy.ask_tools


def _domain_allowed(domain: str, allowed_domains: tuple[str, ...]) -> bool:
    """Exact match or fnmatch wildcard, reusing the same approach as _path_blocked."""
    return any(fnmatch.fnmatch(domain, pattern) for pattern in allowed_domains)


def _credential_shaped(path: str | None) -> bool:
    """True when *path* (URL path + query) looks like it targets credentials."""
    if not path:
        return False
    lowered = path.lower()
    if any(marker in lowered for marker in _CREDENTIAL_PATH_MARKERS):
        return True
    return any(marker in lowered for marker in _CREDENTIAL_QUERY_MARKERS)


def _compute_coverage(
    policy: PolicyConfig,
    kind: Any,
    tool_name: str | None,
    paths: list[Any],
    urls: list[Any],
    method: str | None,
    observed_steps: int | None,
    root: Path | None,
    *,
    effective_level: int,
) -> tuple[int, int]:
    """Return ``(observed, expected)`` over the four boundary surfaces this
    policy applies to *this* event. See the design doc's coverage table.
    """
    is_tool_event = kind in ("tool_call", "tool_result")
    expected = 0
    observed = 0

    tool_identity_expected = is_tool_event and (
        policy.allowlist_active
        or bool(policy.ask_tools)
        or (isinstance(tool_name, str) and tool_name in _BUILTIN_WEB_TOOLS)
    )
    if tool_identity_expected:
        expected += 1
        if isinstance(tool_name, str) and tool_name:
            observed += 1

    path_boundary_expected = bool(policy.blocked_path_globs) or root is not None
    if path_boundary_expected:
        expected += 1
        if paths or not policy.require_declared_paths:
            observed += 1

    web_boundary_expected = policy.web is not None and _is_web_classified(tool_name, policy)
    if web_boundary_expected:
        expected += 1
        urls_fully_declared = bool(urls) and all(
            isinstance(u, dict) and isinstance(u.get("domain"), str) and u.get("domain")
            for u in urls
        )
        if urls_fully_declared and method is not None:
            observed += 1

    step_boundary_expected = policy.max_steps is not None or effective_level >= 2
    if step_boundary_expected:
        expected += 1
        if observed_steps is not None:
            observed += 1

    return observed, expected
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/bin/python -m pytest tests/test_policy_ask.py -k "web_classified or domain_allowed or credential_shaped or compute_coverage" -v`
  Expected: PASS (all 8 tests).

- [ ] **Step 5: Run the full gate** — `.venv/bin/ruff check hyodo tests --fix && .venv/bin/ruff format hyodo tests && .venv/bin/pyright hyodo && .venv/bin/python -m pytest tests -q --ignore=tests/test_policy_ask.py`

- [ ] **Step 6: Commit**

```bash
git add hyodo/policy.py tests/test_policy_ask.py
git commit -m "$(cat <<'EOF'
feat(policy): web-classification, domain, credential-path, coverage helpers

Pure, directly-unit-tested building blocks for the evaluate_policy
pipeline (Task 7): _is_web_classified is the one membership test every
web-related rule reuses, _domain_allowed mirrors _path_blocked's
fnmatch approach, _credential_shaped checks the built-in
credential-shaped pattern set, and _compute_coverage implements the
four-surface (observed, expected) table from the design doc.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PH1ofuuGrbVpW3vsBfaqPT
EOF
)"
```

---

### Task 6: `hyodo/policy_trust.py` — untracked trust grant store

**Files:** Create `hyodo/policy_trust.py`; Test `tests/test_policy_trust.py` (new)
**Interfaces:** Consumes: nothing new. Produces:
`POLICY_TRUST_SCHEMA_ID = "hyodo.policy-trust/v1"`; `POLICY_TRUST_RELATIVE_PATH = Path(".hyodo") / "policy-trust.json"`; `POLICY_TRUST_ENV_VAR = "HYODO_POLICY_TRUST_ALL"`;
`PolicyTrustGrant(level: int, granted_at: str, granted_by: str)`;
`PolicyTrustState(level: int, granted_at: str, granted_by: str, history: tuple[PolicyTrustGrant, ...] = ())`;
`load_policy_trust(root: Path) -> tuple[PolicyTrustState | None, str | None]`;
`grant_policy_trust(root: Path, level: int, *, by: str) -> PolicyTrustState`;
`effective_trust_level(max_level: int, granted: PolicyTrustState | None) -> int`;
`default_granted_by() -> str`;
`PolicyTrustGrantDecision(approved: bool, reason: str, via: str)`;
`resolve_policy_trust_grant(level: int, *, by: str, yes: bool) -> PolicyTrustGrantDecision`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_policy_trust.py — new file

"""Tests for hyodo.policy_trust — the untracked .hyodo/policy-trust.json store.

Mirrors tests/test_byog_trust.py's structure for hyodo.gates's gate-trust
store: same non-interactive/env-var/interactive-prompt split, same
malformed-store-is-treated-as-missing posture.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import hyodo.policy_trust as policy_trust
from hyodo.policy_trust import (
    POLICY_TRUST_ENV_VAR,
    POLICY_TRUST_RELATIVE_PATH,
    POLICY_TRUST_SCHEMA_ID,
    PolicyTrustState,
    default_granted_by,
    effective_trust_level,
    grant_policy_trust,
    load_policy_trust,
    resolve_policy_trust_grant,
)


def _force_noninteractive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(policy_trust, "_is_noninteractive", lambda: True)


def _force_interactive(monkeypatch: pytest.MonkeyPatch, answer: str) -> None:
    monkeypatch.setattr(policy_trust, "_is_noninteractive", lambda: False)
    monkeypatch.setattr("builtins.input", lambda prompt="": answer)


def test_load_policy_trust_missing_file_is_trust_missing(tmp_path: Path):
    state, err = load_policy_trust(tmp_path)
    assert state is None
    assert err == "trust_missing"


def test_grant_and_load_round_trip(tmp_path: Path):
    state = grant_policy_trust(tmp_path, 2, by="human:brnestrm")
    assert state.level == 2
    assert state.granted_by == "human:brnestrm"
    assert state.history == ()

    loaded, err = load_policy_trust(tmp_path)
    assert err is None
    assert loaded is not None
    assert loaded.level == 2
    assert loaded.granted_by == "human:brnestrm"

    on_disk = json.loads((tmp_path / POLICY_TRUST_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert on_disk["schema"] == POLICY_TRUST_SCHEMA_ID


def test_grant_accumulates_history():
    pass  # replaced by the tmp_path version below to avoid a stateless test


def test_grant_accumulates_history_across_calls(tmp_path: Path):
    grant_policy_trust(tmp_path, 1, by="human:a")
    second = grant_policy_trust(tmp_path, 2, by="human:b")
    assert second.level == 2
    assert len(second.history) == 1
    assert second.history[0].level == 1
    assert second.history[0].granted_by == "human:a"

    third = grant_policy_trust(tmp_path, 3, by="human:c")
    assert len(third.history) == 2
    assert [h.level for h in third.history] == [1, 2]


def test_malformed_trust_file_is_trust_invalid(tmp_path: Path):
    hyodo_dir = tmp_path / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "policy-trust.json").write_text("{not json", encoding="utf-8")
    state, err = load_policy_trust(tmp_path)
    assert state is None
    assert err == "trust_invalid"


def test_trust_file_with_out_of_range_level_is_trust_invalid(tmp_path: Path):
    hyodo_dir = tmp_path / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "policy-trust.json").write_text(
        json.dumps(
            {
                "schema": POLICY_TRUST_SCHEMA_ID,
                "level": 9,
                "granted_at": "2026-01-01T00:00:00+00:00",
                "granted_by": "human:x",
            }
        ),
        encoding="utf-8",
    )
    state, err = load_policy_trust(tmp_path)
    assert state is None
    assert err == "trust_invalid"


def test_trust_file_with_wrong_schema_is_trust_invalid(tmp_path: Path):
    hyodo_dir = tmp_path / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "policy-trust.json").write_text(
        json.dumps(
            {
                "schema": "not-the-right-schema",
                "level": 1,
                "granted_at": "2026-01-01T00:00:00+00:00",
                "granted_by": "human:x",
            }
        ),
        encoding="utf-8",
    )
    state, err = load_policy_trust(tmp_path)
    assert state is None
    assert err == "trust_invalid"


def test_effective_trust_level_is_min_of_cap_and_granted():
    granted = PolicyTrustState(level=3, granted_at="t", granted_by="human:x")
    assert effective_trust_level(2, granted) == 2
    assert effective_trust_level(3, granted) == 3


def test_effective_trust_level_with_no_grant_is_zero():
    assert effective_trust_level(3, None) == 0


def test_default_granted_by_falls_back_to_unknown(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("USER", raising=False)
    monkeypatch.delenv("USERNAME", raising=False)
    assert default_granted_by() == "unknown"


def test_default_granted_by_prefers_user_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("USER", "brnestrm")
    assert default_granted_by() == "brnestrm"


# --------------------------------------------------------------------------- #
# resolve_policy_trust_grant — non-interactive refusal, env pre-approval,
# interactive prompt (mirrors tests/test_byog_trust.py's resolve_gate_trust
# coverage for hyodo.gates).
# --------------------------------------------------------------------------- #


def test_resolve_grant_noninteractive_without_env_var_refuses(monkeypatch: pytest.MonkeyPatch):
    _force_noninteractive(monkeypatch)
    monkeypatch.delenv(POLICY_TRUST_ENV_VAR, raising=False)
    decision = resolve_policy_trust_grant(2, by="human:x", yes=True)
    assert decision.approved is False
    assert POLICY_TRUST_ENV_VAR in decision.reason


def test_resolve_grant_noninteractive_with_env_var_approves(monkeypatch: pytest.MonkeyPatch):
    _force_noninteractive(monkeypatch)
    monkeypatch.setenv(POLICY_TRUST_ENV_VAR, "1")
    decision = resolve_policy_trust_grant(2, by="human:x", yes=False)
    assert decision.approved is True
    assert decision.via == f"env:{POLICY_TRUST_ENV_VAR}"


def test_resolve_grant_interactive_yes_flag_skips_prompt(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(policy_trust, "_is_noninteractive", lambda: False)

    def _fail_if_called(prompt: str = "") -> str:
        raise AssertionError("input() must not be called when --yes is given")

    monkeypatch.setattr("builtins.input", _fail_if_called)
    decision = resolve_policy_trust_grant(2, by="human:x", yes=True)
    assert decision.approved is True
    assert decision.via == "prompt"


def test_resolve_grant_interactive_prompt_declined(monkeypatch: pytest.MonkeyPatch):
    _force_interactive(monkeypatch, "n")
    decision = resolve_policy_trust_grant(2, by="human:x", yes=False)
    assert decision.approved is False
    assert decision.via == "declined"


def test_resolve_grant_interactive_prompt_eof_declines_without_crashing(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(policy_trust, "_is_noninteractive", lambda: False)

    def _raise_eof(prompt: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise_eof)
    decision = resolve_policy_trust_grant(2, by="human:x", yes=False)
    assert decision.approved is False
```

(Remove the stray `test_grant_accumulates_history` no-op stub before committing — it exists in this draft only to show the replacement reasoning; the committed file contains only `test_grant_accumulates_history_across_calls`.)

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/bin/python -m pytest tests/test_policy_trust.py -v`
  Expected: FAIL with `ModuleNotFoundError: No module named 'hyodo.policy_trust'`.

- [ ] **Step 3: Write minimal implementation**

```python
# hyodo/policy_trust.py — new file

"""Untracked, TOFU-style trust ledger for policy ASK escalation (Phase 1-A).

Mirrors ``hyodo.gates``'s gate-trust store (``_load_gate_trust_store`` /
``_save_gate_trust_store`` / ``GATES_TRUST_ENV_VAR``, hyodo/gates.py:265-296)
but is deliberately a separate file and a separate on-disk store: gate trust
says "I already reviewed this exact command set"; policy trust says "I
already reviewed this project enough to let some ASK decisions auto-resolve."
Conflating the two stores would let approving a lint command silently also
approve autonomous web access.

The granted level here is never read from the tracked ``policy.toml`` --
that file only ever *caps* what can be granted (``hyodo.policy.TrustPolicy``).
This module owns the untracked, operator-controlled half of that contract.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

POLICY_TRUST_SCHEMA_ID = "hyodo.policy-trust/v1"
POLICY_TRUST_RELATIVE_PATH = Path(".hyodo") / "policy-trust.json"
#: Escape hatch for automation that already reviewed this project out-of-band
#: -- mirrors hyodo.gates.GATES_TRUST_ENV_VAR exactly (hyodo/gates.py:71).
POLICY_TRUST_ENV_VAR = "HYODO_POLICY_TRUST_ALL"
_TRUTHY_ENV_VALUES = frozenset({"1", "true", "yes", "on"})
_MIN_LEVEL = 0
_MAX_LEVEL = 3


@dataclass(frozen=True)
class PolicyTrustGrant:
    """One historical grant entry."""

    level: int
    granted_at: str
    granted_by: str


@dataclass(frozen=True)
class PolicyTrustState:
    """The current grant plus its history, as read from disk."""

    level: int
    granted_at: str
    granted_by: str
    history: tuple[PolicyTrustGrant, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PolicyTrustGrantDecision:
    """Outcome of deciding whether a ``hyodo policy trust grant`` call may proceed."""

    approved: bool
    reason: str
    via: str  # "env:<VAR>" | "prompt" | "declined"


def _env_truthy(name: str) -> bool:
    """Same truthy-value convention as hyodo.gates._env_truthy (hyodo/gates.py:245-246)."""
    return os.environ.get(name, "").strip().lower() in _TRUTHY_ENV_VALUES


def _is_noninteractive() -> bool:
    """Same CI/no-TTY detection as hyodo.gates._is_noninteractive (hyodo/gates.py:249-262).

    Duplicated rather than imported: this module is standalone by the same
    design choice hyodo.gates states for itself in its own module docstring.
    """
    if _env_truthy("CI"):
        return True
    try:
        return not (sys.stdin.isatty() and sys.stdout.isatty())
    except (AttributeError, ValueError):
        return True


def default_granted_by() -> str:
    """Best-effort human name for an interactive grant: $USER, then $USERNAME, else 'unknown'."""
    return os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"


def _parse_grant(raw: Any) -> PolicyTrustGrant | None:
    if (
        isinstance(raw, dict)
        and isinstance(raw.get("level"), int)
        and not isinstance(raw.get("level"), bool)
        and _MIN_LEVEL <= raw["level"] <= _MAX_LEVEL
        and isinstance(raw.get("granted_at"), str)
        and raw["granted_at"]
        and isinstance(raw.get("granted_by"), str)
        and raw["granted_by"]
    ):
        return PolicyTrustGrant(
            level=raw["level"], granted_at=raw["granted_at"], granted_by=raw["granted_by"]
        )
    return None


def load_policy_trust(root: Path) -> tuple[PolicyTrustState | None, str | None]:
    """Load ``.hyodo/policy-trust.json``. Returns ``(state, error_code)``.

    ``error_code`` is ``"trust_missing"`` when the file does not exist and
    ``"trust_invalid"`` for anything else that keeps it from being trusted --
    bad JSON, wrong schema id, an out-of-range level, or a missing required
    field. Both are treated identically by evaluate_policy's
    ``trust_grant_unobserved`` rule: a level that cannot be verified must
    never be trusted to soften an ASK, whether it is absent or damaged.
    """
    path = root / POLICY_TRUST_RELATIVE_PATH
    if not path.exists():
        return None, "trust_missing"
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError:
        return None, "trust_invalid"
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError:
        return None, "trust_invalid"
    if not isinstance(raw, dict) or raw.get("schema") != POLICY_TRUST_SCHEMA_ID:
        return None, "trust_invalid"
    current = _parse_grant(raw)
    if current is None:
        return None, "trust_invalid"
    history_raw = raw.get("history", [])
    history: list[PolicyTrustGrant] = []
    if isinstance(history_raw, list):
        for entry in history_raw:
            parsed = _parse_grant(entry)
            if parsed is not None:
                history.append(parsed)
    return (
        PolicyTrustState(
            level=current.level,
            granted_at=current.granted_at,
            granted_by=current.granted_by,
            history=tuple(history),
        ),
        None,
    )


def _save_policy_trust(root: Path, state: PolicyTrustState) -> bool:
    """Write the trust store. Best-effort: a read-only checkout still returns
    the already-decided grant for this call, it just cannot remember it for
    the next one -- same posture as hyodo.gates._save_gate_trust_store
    (hyodo/gates.py:278-287).
    """
    path = root / POLICY_TRUST_RELATIVE_PATH
    payload = {
        "schema": POLICY_TRUST_SCHEMA_ID,
        "level": state.level,
        "granted_at": state.granted_at,
        "granted_by": state.granted_by,
        "history": [
            {"level": h.level, "granted_at": h.granted_at, "granted_by": h.granted_by}
            for h in state.history
        ],
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return True
    except OSError:
        return False


def grant_policy_trust(root: Path, level: int, *, by: str) -> PolicyTrustState:
    """Record a new grant, moving the previous grant (if any) into ``history``.

    Does not itself decide whether granting is *allowed* right now -- that is
    ``resolve_policy_trust_grant``'s job, matching how hyodo.gates keeps
    ``_remember_gate_trust`` a pure recorder separate from the policy
    decision in ``resolve_gate_trust``.
    """
    if not (_MIN_LEVEL <= level <= _MAX_LEVEL):
        raise ValueError(f"level must be between {_MIN_LEVEL} and {_MAX_LEVEL}, got {level}")
    previous, _err = load_policy_trust(root)
    history: tuple[PolicyTrustGrant, ...] = previous.history if previous is not None else ()
    if previous is not None:
        history = (
            *history,
            PolicyTrustGrant(
                level=previous.level,
                granted_at=previous.granted_at,
                granted_by=previous.granted_by,
            ),
        )
    state = PolicyTrustState(
        level=level,
        granted_at=datetime.now(timezone.utc).isoformat(),
        granted_by=by,
        history=history,
    )
    _save_policy_trust(root, state)
    return state


def effective_trust_level(max_level: int, granted: PolicyTrustState | None) -> int:
    """``min(max_level, granted.level)``; ``0`` (observe-only) when nothing was granted yet."""
    return min(max_level, granted.level if granted is not None else 0)


def _prompt_policy_trust_grant(level: int, by: str) -> bool:
    """Show what is about to be granted and ask an operator to approve.

    Plain print/input (no Rich/Typer), matching hyodo.gates._prompt_gate_trust's
    reason for staying dependency-free (hyodo/gates.py:298-313).
    """
    print(f"About to grant policy trust level {level} to {by!r}.")
    print(
        "Levels 2-3 let some ASK decisions auto-resolve to ALLOW in exchange "
        "for a mandatory ledger record (see `hyodo event record --policy`)."
    )
    try:
        answer = input("Proceed? [y/N] ")
    except EOFError:
        return False
    return answer.strip().lower() in {"y", "yes"}


def resolve_policy_trust_grant(level: int, *, by: str, yes: bool) -> PolicyTrustGrantDecision:
    """Decide whether granting *level* to *by* may proceed right now.

    Mirrors hyodo.gates.resolve_gate_trust's non-interactive/interactive
    split exactly: non-interactively (CI, or no attached terminal) a grant is
    refused unless POLICY_TRUST_ENV_VAR pre-approves it; interactively,
    --yes skips the confirmation prompt but is not itself a bypass for a
    non-interactive environment.
    """
    if _is_noninteractive():
        if _env_truthy(POLICY_TRUST_ENV_VAR):
            return PolicyTrustGrantDecision(
                True, f"pre-approved via {POLICY_TRUST_ENV_VAR}", f"env:{POLICY_TRUST_ENV_VAR}"
            )
        return PolicyTrustGrantDecision(
            False,
            f"refusing to grant trust non-interactively; set {POLICY_TRUST_ENV_VAR}=1 to "
            "pre-approve, or run this command interactively once",
            "refused-noninteractive",
        )
    if yes or _prompt_policy_trust_grant(level, by):
        return PolicyTrustGrantDecision(True, "approved interactively", "prompt")
    return PolicyTrustGrantDecision(False, "declined interactively", "declined")
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/bin/python -m pytest tests/test_policy_trust.py tests/test_policy_ask.py -v`
  Expected: PASS for every test in `test_policy_trust.py`, and now `test_policy_ask.py` fully collects (its `from hyodo.policy_trust import ...` line resolves) — all tests written in Tasks 2, 3, 5 should PASS too. This is the point where `test_policy_ask.py` is no longer excluded from the full-suite run.

- [ ] **Step 5: Run the full gate** — `.venv/bin/ruff check hyodo tests --fix && .venv/bin/ruff format hyodo tests && .venv/bin/pyright hyodo && .venv/bin/python -m pytest tests -q`
  (No more `--ignore` — every test file is now collectible.)

- [ ] **Step 6: Commit**

```bash
git add hyodo/policy_trust.py tests/test_policy_trust.py
git commit -m "$(cat <<'EOF'
feat(policy): untracked .hyodo/policy-trust.json trust grant store

New hyodo/policy_trust.py, mirroring hyodo.gates's gate-trust store
(same schema-per-file philosophy, same HYODO_*_TRUST_ALL env-var
escape hatch, same CI/no-TTY refusal). Kept separate from hyodo.policy
so the pure evaluator has no file I/O or TTY concerns; separate from
hyodo.gates's own store because "I reviewed this command set" and "I
trust this project's autonomous ASK escalation" must never conflate.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PH1ofuuGrbVpW3vsBfaqPT
EOF
)"
```

---

### Task 7: `evaluate_policy` — the full ASK/trust decision pipeline

**Files:** Modify `hyodo/policy.py` (rewrite `evaluate_policy`, lines 162-239); Test `tests/test_policy_ask.py`
**Interfaces:** Consumes: everything from Tasks 2-6. Produces:
`evaluate_policy(event: dict[str, Any], policy: PolicyConfig, *, observed_steps: int | None = None, root: Path | None = None) -> PolicyDecision`;
new private helper `_resolve_trust_level(trust_policy: TrustPolicy | None, root: Path | None, external_variables: tuple[str, ...]) -> tuple[int, str | None]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_policy_ask.py — append


# --------------------------------------------------------------------------- #
# evaluate_policy — full pipeline
# --------------------------------------------------------------------------- #


def _web_tool_event(**overrides: object) -> dict:
    return _event(
        tool={
            "name": "web_fetch",
            "args_digest": None,
            "paths": [],
            "method": overrides.pop("method", "GET"),
            "urls": overrides.pop(
                "urls", [{"domain": "unlisted.example.com", "path": "/v1/data"}]
            ),
        },
        **overrides,
    )


def test_evaluate_policy_unlisted_domain_is_ask_at_default_trust():
    policy = _bare_policy(web=WebPolicy(allowed_domains=("api.example.com",)))
    event = _normalize(_web_tool_event())
    decision = evaluate_policy(event, policy)
    assert decision.decision == "ASK"
    assert "web_domain_unlisted:unlisted.example.com" in decision.external_variables
    assert decision.trust_level == 1


def test_evaluate_policy_non_get_without_allow_non_get_is_hard_deny():
    policy = _bare_policy(web=WebPolicy(allowed_domains=("api.example.com",)))
    event = _normalize(
        _web_tool_event(method="POST", urls=[{"domain": "api.example.com", "path": "/v1/data"}])
    )
    decision = evaluate_policy(event, policy)
    assert decision.decision == "DENY"
    assert decision.rule_id == "web_non_get_denied"


def test_evaluate_policy_credential_shaped_path_is_hard_deny():
    policy = _bare_policy(web=WebPolicy(allowed_domains=("api.example.com",)))
    event = _normalize(
        _web_tool_event(urls=[{"domain": "api.example.com", "path": "/wp-admin/"}])
    )
    decision = evaluate_policy(event, policy)
    assert decision.decision == "DENY"
    assert decision.rule_id == "web_credential_path_denied"


def test_evaluate_policy_credential_shaped_path_allowed_when_configured():
    policy = _bare_policy(
        web=WebPolicy(allowed_domains=("api.example.com",), allow_credential_paths=True)
    )
    event = _normalize(
        _web_tool_event(urls=[{"domain": "api.example.com", "path": "/wp-admin/"}])
    )
    decision = evaluate_policy(event, policy)
    assert decision.decision != "DENY"


def test_evaluate_policy_full_coverage_zero_external_variables_is_allow():
    policy = _bare_policy(allowed_tools=("search",))
    event = _normalize(_event())
    decision = evaluate_policy(event, policy)
    assert decision.decision == "ALLOW"
    assert decision.external_variables == ()
    assert decision.coverage == (1, 1)


def test_evaluate_policy_ask_threshold_never_degrades_ask_to_deny():
    policy = _bare_policy(ask_tools=("send_email",), ask_threshold=0)
    event = _normalize(
        _event(tool={"name": "send_email", "args_digest": None, "paths": []})
    )
    decision = evaluate_policy(event, policy)
    assert decision.decision == "ASK"
    assert "above configured threshold" in (decision.reason or "")


def test_evaluate_policy_path_outside_root_is_ask(tmp_path: Path):
    policy = _bare_policy()
    event = _normalize(
        _event(tool={"name": "read_file", "args_digest": None, "paths": ["/etc/passwd"]})
    )
    decision = evaluate_policy(event, policy, root=tmp_path)
    assert decision.decision == "ASK"
    assert "path_outside_root:/etc/passwd" in decision.external_variables


def test_evaluate_policy_path_inside_root_is_not_flagged(tmp_path: Path):
    policy = _bare_policy()
    inside = tmp_path / "src" / "file.py"
    event = _normalize(
        _event(tool={"name": "read_file", "args_digest": None, "paths": [str(inside)]})
    )
    decision = evaluate_policy(event, policy, root=tmp_path)
    assert not any(v.startswith("path_outside_root:") for v in decision.external_variables)


# --------------------------------------------------------------------------- #
# Trust levels 0-3 on the same fixture event
# --------------------------------------------------------------------------- #


def test_evaluate_policy_trust_level_0_is_always_ask(tmp_path: Path):
    policy = _bare_policy(ask_tools=("send_email",), trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp_path, 0, by="human:test")
    event = _normalize(_event(tool={"name": "send_email", "args_digest": None, "paths": []}))
    decision = evaluate_policy(event, policy, observed_steps=1, root=tmp_path)
    assert decision.decision == "ASK"
    assert decision.trust_level == 0


def test_evaluate_policy_trust_level_1_is_ask():
    policy = _bare_policy(ask_tools=("send_email",))  # no [trust] -> level 1
    event = _normalize(_event(tool={"name": "send_email", "args_digest": None, "paths": []}))
    decision = evaluate_policy(event, policy, observed_steps=1)
    assert decision.decision == "ASK"
    assert decision.trust_level == 1


def test_evaluate_policy_trust_level_2_allows_inside_boundary(tmp_path: Path):
    policy = _bare_policy(ask_tools=("send_email",), trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp_path, 2, by="human:test")
    event = _normalize(_event(tool={"name": "send_email", "args_digest": None, "paths": []}))
    decision = evaluate_policy(event, policy, observed_steps=1, root=tmp_path)
    assert decision.decision == "ALLOW"
    assert decision.rule_id == "autorun_level2"
    assert decision.trust_level == 2


def test_evaluate_policy_trust_level_2_still_asks_for_unlisted_web_domain(tmp_path: Path):
    policy = _bare_policy(
        web=WebPolicy(allowed_domains=("api.example.com",)), trust=TrustPolicy(max_level=3)
    )
    grant_policy_trust(tmp_path, 2, by="human:test")
    event = _normalize(_web_tool_event())
    decision = evaluate_policy(event, policy, observed_steps=1, root=tmp_path)
    assert decision.decision == "ASK"
    assert decision.trust_level == 2


def test_evaluate_policy_trust_level_3_allows_unlisted_web_domain(tmp_path: Path):
    policy = _bare_policy(
        web=WebPolicy(allowed_domains=("api.example.com",)), trust=TrustPolicy(max_level=3)
    )
    grant_policy_trust(tmp_path, 3, by="human:test")
    event = _normalize(_web_tool_event())
    decision = evaluate_policy(event, policy, observed_steps=1, root=tmp_path)
    assert decision.decision == "ALLOW"
    assert decision.rule_id == "autorun_level3"
    assert decision.trust_level == 3


def test_evaluate_policy_trust_level_2_without_observed_steps_is_unobserved(tmp_path: Path):
    policy = _bare_policy(ask_tools=("send_email",), trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp_path, 2, by="human:test")
    event = _normalize(_event(tool={"name": "send_email", "args_digest": None, "paths": []}))
    decision = evaluate_policy(event, policy, observed_steps=None, root=tmp_path)
    assert decision.decision == "UNOBSERVED"
    assert decision.rule_id == "autorun_level2"


def test_evaluate_policy_damaged_trust_file_is_unobserved_when_ask_eligible(tmp_path: Path):
    hyodo_dir = tmp_path / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "policy-trust.json").write_text("{not json", encoding="utf-8")
    policy = _bare_policy(ask_tools=("send_email",), trust=TrustPolicy(max_level=3))
    event = _normalize(_event(tool={"name": "send_email", "args_digest": None, "paths": []}))
    decision = evaluate_policy(event, policy, observed_steps=1, root=tmp_path)
    assert decision.decision == "UNOBSERVED"
    assert decision.rule_id == "trust_grant_unobserved"


def test_evaluate_policy_missing_trust_file_with_zero_external_variables_still_allows(
    tmp_path: Path,
):
    """[trust] configured but never granted must not block an otherwise-clean ALLOW."""
    policy = _bare_policy(allowed_tools=("search",), trust=TrustPolicy(max_level=3))
    event = _normalize(_event())
    decision = evaluate_policy(event, policy, root=tmp_path)
    assert decision.decision == "ALLOW"


def test_evaluate_policy_existing_policy_toml_is_byte_identical_without_new_fields(tmp_path: Path):
    """Backward-compatibility pin: a pre-Phase-1 PolicyConfig (no web/ask_tools/
    ask_threshold/trust) must evaluate identically whether or not `root` is passed."""
    policy = PolicyConfig(
        schema=POLICY_SCHEMA_ID,
        max_steps=10,
        allowed_tools=("search",),
        blocked_path_globs=(),
    )
    event = _normalize(_event())
    without_root = evaluate_policy(event, policy, observed_steps=1)
    with_root = evaluate_policy(event, policy, observed_steps=1, root=tmp_path)
    assert without_root.decision == with_root.decision == "ALLOW"
    assert without_root.trust_level == with_root.trust_level == 1
```

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/bin/python -m pytest tests/test_policy_ask.py -k "evaluate_policy" -v`
  Expected: FAIL — today's `evaluate_policy` accepts no `root` keyword and never returns `ASK`, so most of these raise `TypeError: evaluate_policy() got an unexpected keyword argument 'root'` and the rest assert on a decision that is always `ALLOW`/`DENY`/`UNOBSERVED`.

- [ ] **Step 3: Write minimal implementation**

```python
# hyodo/policy.py — replace evaluate_policy (lines 162-239) in full


def _resolve_trust_level(
    trust_policy: TrustPolicy | None, root: Path | None, external_variables: tuple[str, ...]
) -> tuple[int, str | None]:
    """Resolve the effective trust level for this decision.

    Returns ``(level, error_rule_id)``. ``error_rule_id`` is only set when a
    level cannot be verified *and it would matter* -- ``[trust]`` is
    configured, the event has at least one external variable, and the grant
    store is missing or unreadable. An event with no external variables is
    never blocked by a missing grant: there is nothing discretionary for a
    trust level to soften.
    """
    if trust_policy is None:
        return 1, None
    lookup_root = root if root is not None else Path.cwd()
    state, err = load_policy_trust(lookup_root)
    if err is not None:
        if external_variables:
            return 0, "trust_grant_unobserved"
        return 0, None
    return effective_trust_level(trust_policy.max_level, state), None


def evaluate_policy(
    event: dict[str, Any],
    policy: PolicyConfig,
    *,
    observed_steps: int | None = None,
    root: Path | None = None,
) -> PolicyDecision:
    """Evaluate a **validated** event against *policy*. Never returns silent pass on tools.

    ``observed_steps`` is how many events this run already has **in the ledger**. It is
    the only authoritative step count: ``event["step_index"]`` is self-reported by the
    caller and a caller that keeps sending ``step_index: 0`` would otherwise run forever.
    When ``max_steps`` is configured but the ledger was not observed, the result is
    ``UNOBSERVED`` rather than ``ALLOW`` — unenforceable is not permitted.

    ``root`` is new in Phase 1-A and keyword-only with a ``None`` default, so every
    existing caller keeps today's behavior unless it opts in. It is used for the
    ``path_outside_root`` external variable (skipped entirely when ``root`` is
    ``None``, and not counted toward ``coverage``'s expected total), and as the
    lookup base for the untracked ``.hyodo/policy-trust.json`` store when
    ``policy.trust`` is configured (falling back to ``Path.cwd()`` when ``root``
    is not given — the same cwd basis ``hyodo policy check`` already uses for
    its own ledger step count).
    """
    if (
        policy.max_steps is not None
        and observed_steps is not None
        and observed_steps >= policy.max_steps
    ):
        return PolicyDecision(
            decision="DENY",
            rule_id="max_steps",
            reason=(
                f"run already has {observed_steps} recorded step(s); "
                f"max_steps {policy.max_steps} would be exceeded"
            ),
        )

    kind = event.get("kind")
    tool = event.get("tool") if isinstance(event.get("tool"), dict) else {}
    tool_name = tool.get("name") if isinstance(tool, dict) else None
    paths = tool.get("paths") if isinstance(tool, dict) else None
    if not isinstance(paths, list):
        paths = []
    method = tool.get("method") if isinstance(tool, dict) else None
    urls = tool.get("urls") if isinstance(tool, dict) else None
    if not isinstance(urls, list):
        urls = []
    is_tool_event = kind in ("tool_call", "tool_result")
    web_classified = is_tool_event and _is_web_classified(tool_name, policy)

    # --- 1. Hard DENY (absolute; trust level never softens these) -----------

    if is_tool_event and policy.allowlist_active:
        allowed = policy.allowed_tools or ()
        if not isinstance(tool_name, str) or tool_name not in allowed:
            return PolicyDecision(
                decision="DENY",
                rule_id="tool_not_allowed",
                reason=f"tool {tool_name!r} not in allowed_tools",
            )

    if (
        policy.require_declared_paths
        and policy.blocked_path_globs
        and is_tool_event
        and not paths
    ):
        return PolicyDecision(
            decision="UNOBSERVED",
            rule_id="data_boundary_undeclared",
            reason="tool declared no paths; blocked_path_globs cannot be checked",
        )

    if policy.blocked_path_globs and paths:
        for p in paths:
            if not isinstance(p, str):
                continue
            matched = _path_blocked(p, policy.blocked_path_globs)
            if matched is not None:
                return PolicyDecision(
                    decision="DENY",
                    rule_id="data_boundary",
                    reason=f"path {p!r} matched blocked glob {matched!r}",
                )

    if policy.max_steps is not None and observed_steps is None:
        # A step budget exists but we could not count the ledger. Refusing to call
        # this ALLOW is the whole point: unobserved is not healthy.
        return PolicyDecision(
            decision="UNOBSERVED",
            rule_id="max_steps",
            reason="ledger step count unavailable; max_steps cannot be enforced",
        )

    if web_classified and policy.web is not None:
        if (
            isinstance(method, str)
            and method not in _SAFE_HTTP_METHODS
            and not policy.web.allow_non_get
        ):
            return PolicyDecision(
                decision="DENY",
                rule_id="web_non_get_denied",
                reason=f"method {method!r} is not GET/HEAD and allow_non_get is false",
            )
        if not policy.web.allow_credential_paths:
            for entry in urls:
                if isinstance(entry, dict) and _credential_shaped(entry.get("path")):
                    return PolicyDecision(
                        decision="DENY",
                        rule_id="web_credential_path_denied",
                        reason=(
                            f"url path {entry.get('path')!r} matches a credential-shaped "
                            "pattern and allow_credential_paths is false"
                        ),
                    )

    # --- 2. External-variable aggregation (never denies) ---------------------

    external_variables: list[str] = []
    unobserved_boundary: str | None = None

    if web_classified and policy.web is not None:
        if not urls:
            unobserved_boundary = "web_boundary_undeclared"
        else:
            for entry in urls:
                if not isinstance(entry, dict):
                    continue
                domain = entry.get("domain")
                if not isinstance(domain, str) or not domain:
                    unobserved_boundary = "web_boundary_undeclared"
                    continue
                if not _domain_allowed(domain, policy.web.allowed_domains):
                    external_variables.append(f"web_domain_unlisted:{domain}")
            if method is None:
                unobserved_boundary = "web_boundary_undeclared"

    if root is not None:
        for p in paths:
            if not isinstance(p, str) or not p:
                continue
            candidate = Path(p)
            resolved = candidate if candidate.is_absolute() else (root / candidate)
            try:
                resolved.resolve().relative_to(root.resolve())
            except ValueError:
                external_variables.append(f"path_outside_root:{p}")

    if is_tool_event and _is_web_classified(tool_name, policy):
        # Fires on tool-name membership alone -- independent of whether [web]
        # is configured (design doc, Evaluation order §2.3).
        external_variables.append(f"ask_tools:{tool_name}")

    if unobserved_boundary is not None:
        return PolicyDecision(
            decision="UNOBSERVED",
            rule_id=unobserved_boundary,
            reason="web boundary configured but tool.urls/tool.method were not fully declared",
            coverage=_compute_coverage(
                policy, kind, tool_name, paths, urls, method, observed_steps, root,
                effective_level=1,
            ),
            external_variables=tuple(external_variables),
            trust_level=1,
        )

    # --- 3. Trust gate ---------------------------------------------------

    trust_level, trust_error = _resolve_trust_level(
        policy.trust, root, tuple(external_variables)
    )
    if trust_error is not None:
        return PolicyDecision(
            decision="UNOBSERVED",
            rule_id=trust_error,
            reason=(
                "trust grant missing or unreadable; cannot verify the level "
                "needed to soften ASK"
            ),
            coverage=_compute_coverage(
                policy, kind, tool_name, paths, urls, method, observed_steps, root,
                effective_level=0,
            ),
            external_variables=tuple(external_variables),
            trust_level=0,
        )

    coverage = _compute_coverage(
        policy, kind, tool_name, paths, urls, method, observed_steps, root,
        effective_level=trust_level,
    )

    if external_variables:
        detail = f"{len(external_variables)} external variable(s): {', '.join(external_variables)}"
        if policy.ask_threshold is not None:
            if len(external_variables) > policy.ask_threshold:
                detail += f" (above configured threshold {policy.ask_threshold})"
            else:
                detail += f" (at/below configured threshold {policy.ask_threshold})"

        if trust_level >= 2 and observed_steps is None:
            rule_id = "autorun_level3" if trust_level >= 3 else "autorun_level2"
            return PolicyDecision(
                decision="UNOBSERVED",
                rule_id=rule_id,
                reason=f"trust level {trust_level} requires an observed ledger step count",
                coverage=coverage,
                external_variables=tuple(external_variables),
                trust_level=trust_level,
            )
        if trust_level >= 3 and observed_steps is not None:
            return PolicyDecision(
                decision="ALLOW",
                rule_id="autorun_level3",
                reason=f"trust level 3 (full delegation): {detail}",
                coverage=coverage,
                external_variables=tuple(external_variables),
                trust_level=trust_level,
            )
        if trust_level >= 2 and observed_steps is not None:
            only_boundary_vars = all(
                v.startswith("path_outside_root:") or v.startswith("ask_tools:")
                for v in external_variables
            )
            if only_boundary_vars:
                return PolicyDecision(
                    decision="ALLOW",
                    rule_id="autorun_level2",
                    reason=f"trust level 2 (inside configured boundary): {detail}",
                    coverage=coverage,
                    external_variables=tuple(external_variables),
                    trust_level=trust_level,
                )
        return PolicyDecision(
            decision="ASK",
            rule_id="external_variable",
            reason=detail,
            coverage=coverage,
            external_variables=tuple(external_variables),
            trust_level=trust_level,
        )

    # --- 4. ALLOW -------------------------------------------------------

    return PolicyDecision(
        decision="ALLOW",
        rule_id=None,
        reason=None,
        coverage=coverage,
        external_variables=(),
        trust_level=trust_level,
    )
```

Add the one new import this task needs:

```python
# hyodo/policy.py — imports, alongside the existing tomllib fallback block

from hyodo.policy_trust import effective_trust_level, load_policy_trust
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/bin/python -m pytest tests/test_policy_ask.py -v`
  Expected: PASS (every test in the file, including the ones written in Tasks 2, 3, 5).

- [ ] **Step 5: Run the full gate** — `.venv/bin/ruff check hyodo tests --fix && .venv/bin/ruff format hyodo tests && .venv/bin/pyright hyodo && .venv/bin/python -m pytest tests -q`
  This must also re-confirm `tests/test_policy_self_report_boundary.py` and the pre-existing `evaluate_policy`-based tests in `tests/test_agent_events.py` still pass unchanged (backward compatibility).

- [ ] **Step 6: Commit**

```bash
git add hyodo/policy.py tests/test_policy_ask.py
git commit -m "$(cat <<'EOF'
feat(policy): evaluate_policy gains ASK, trust levels 0-3, root param

evaluate_policy now runs the full Phase 1-A pipeline: existing hard-DENY
rules unchanged, two new hard-DENY web rules (web_non_get_denied,
web_credential_path_denied), external-variable aggregation
(web_domain_unlisted, path_outside_root, ask_tools) that never denies
on its own, a trust gate that maps trust level + observed_steps to
ALLOW/ASK/UNOBSERVED per the design doc's table, and coverage math on
every ASK/ALLOW/trust-related UNOBSERVED path. root is keyword-only
with a None default so no existing caller's behavior changes.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PH1ofuuGrbVpW3vsBfaqPT
EOF
)"
```

---

### Task 8: CLI — `policy check` / `event record --policy` exit 3

**Files:** Modify `hyodo/cli/main.py` (lines 2160-2202 `event_record`, 2231-2255, 2290, 2319-2427 `policy_check`, 2408-2427); Test `tests/test_cli_policy_check.py` (new)
**Interfaces:** Consumes: `evaluate_policy` (Task 7). Produces: no new public functions — `policy_check` and `event_record` exit 3 on `ASK`; `event_record`'s `evaluate_policy`/`policy_check`'s `evaluate_policy` calls pass `root=`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli_policy_check.py — new file

"""CLI-level regression tests for Phase 1-A's fourth exit code (ASK = 3) and
the event_record UNOBSERVED-exits-0 fix the design doc names explicitly.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.events import AGENT_EVENT_SCHEMA_VERSION, content_digest
from hyodo.policy import POLICY_SCHEMA_ID

runner = CliRunner()


def _event(**overrides: object) -> dict:
    base: dict = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "run_id": str(uuid.uuid4()),
        "ts": "2026-09-06T12:00:00+00:00",
        "kind": "tool_call",
        "step_index": 0,
        "actor": "agent",
        "tool": {"name": "send_email", "args_digest": content_digest("{}"), "paths": []},
        "io": {"input_digest": content_digest("in"), "output_digest": None},
        "meta": {"model": "test-model", "tags": ["unit"]},
    }
    base.update(overrides)
    return base


def _write_policy(root: Path, body: str) -> Path:
    path = root / ".hyodo" / "policy.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_policy_check_exits_3_on_ask(tmp_path: Path):
    _write_policy(
        tmp_path,
        f'''schema = "{POLICY_SCHEMA_ID}"
ask_tools = ["send_email"]
''',
    )
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(_event()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "policy",
            "check",
            "--file",
            str(event_path),
            "--config",
            str(tmp_path / ".hyodo" / "policy.toml"),
        ],
    )
    assert result.exit_code == 3
    assert "ASK" in result.output


def test_policy_check_json_includes_ledger_write_required_at_trust_level_2(tmp_path: Path):
    _write_policy(
        tmp_path,
        f'''schema = "{POLICY_SCHEMA_ID}"
ask_tools = ["send_email"]

[trust]
max_level = 3
''',
    )
    from hyodo.policy_trust import grant_policy_trust

    grant_policy_trust(tmp_path, 2, by="human:test")
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(_event()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "policy",
            "check",
            "--file",
            str(event_path),
            "--config",
            str(tmp_path / ".hyodo" / "policy.toml"),
            "--json",
        ],
    )
    payload = json.loads(result.output)
    assert payload["decision"] == "ALLOW"
    assert payload["ledger_write_required"] is True
    assert payload["ledger_written"] is False


def test_event_record_with_policy_exits_3_on_ask(tmp_path: Path):
    _write_policy(
        tmp_path,
        f'''schema = "{POLICY_SCHEMA_ID}"
ask_tools = ["send_email"]
''',
    )
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(_event()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "event",
            "record",
            "--file",
            str(event_path),
            "--root",
            str(tmp_path),
            "--policy",
            str(tmp_path / ".hyodo" / "policy.toml"),
        ],
    )
    assert result.exit_code == 3


def test_event_record_with_policy_exits_2_on_unobserved_not_0(tmp_path: Path):
    """Regression pin for the cli/main.py:2290 fix: UNOBSERVED must not exit
    like a plain ALLOW (0)."""
    _write_policy(
        tmp_path,
        f'''schema = "{POLICY_SCHEMA_ID}"
max_steps = 5

[trust]
max_level = 3
''',
    )
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            _event(tool={"name": "send_email", "args_digest": None, "paths": []})
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "event",
            "record",
            "--file",
            str(event_path),
            "--root",
            str(tmp_path),
            "--policy",
            str(tmp_path / ".hyodo" / "policy.toml"),
        ],
    )
    # [trust] is configured but never granted; ask_tools is empty and
    # allowed_tools is unset, so this event's own tool identity carries no
    # external variable here -- max_steps is set but observed_steps is
    # available (first event), so this specific fixture actually resolves to
    # ALLOW. The exit-2 guarantee is exercised directly below against a
    # hand-built UNOBSERVED PolicyDecision instead, since evaluate_policy's
    # own UNOBSERVED paths are already covered end-to-end in test_policy_ask.py.
    assert result.exit_code in (0, 2, 3)
```

Replace the last, deliberately-hedged test with a direct, unambiguous
regression pin instead — the version actually committed:

```python
def test_event_record_with_policy_exits_2_on_unobserved_not_0(tmp_path: Path):
    """Regression pin for the cli/main.py:2290 fix: UNOBSERVED must not exit
    like a plain ALLOW (0). Uses data_boundary_undeclared, an UNOBSERVED rule
    that fires deterministically regardless of trust configuration."""
    _write_policy(
        tmp_path,
        f'''schema = "{POLICY_SCHEMA_ID}"
require_declared_paths = true
blocked_path_globs = ["**/.env"]
''',
    )
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(_event(tool={"name": "read_file", "args_digest": None, "paths": []})),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "event",
            "record",
            "--file",
            str(event_path),
            "--root",
            str(tmp_path),
            "--policy",
            str(tmp_path / ".hyodo" / "policy.toml"),
        ],
    )
    assert result.exit_code == 2
```

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/bin/python -m pytest tests/test_cli_policy_check.py -v`
  Expected: FAIL — `policy_check`'s exit-code ternary (`0 if ALLOW else (2 if UNOBSERVED else 1)`) maps `ASK` to `1`, so `test_policy_check_exits_3_on_ask` asserts `3 == 1` and fails; `event_record`'s ternary (`1 if DENY else 0`) maps both `ASK` and `UNOBSERVED` to `0`, so both `event_record` tests fail; the `--json` test fails with `KeyError: 'ledger_write_required'`.

- [ ] **Step 3: Write minimal implementation**

```python
# hyodo/cli/main.py — imports (alongside the existing `from hyodo.policy import (...)`)

from hyodo.policy_trust import effective_trust_level, load_policy_trust
```

```python
# hyodo/cli/main.py — event_record's evaluate_policy call site (~line 2253)
# replace:
#     decision = evaluate_policy(normalized, cfg, observed_steps=observed)
# with:
        decision = evaluate_policy(normalized, cfg, observed_steps=observed, root=root_path)
```

```python
# hyodo/cli/main.py — event_record's exit-code line (~line 2290)
# replace:
#     exit_code = 1 if decision_label == "DENY" else 0
# with:
    exit_code = (
        {"ALLOW": 0, "DENY": 1, "UNOBSERVED": 2, "ASK": 3}[decision_label]
        if decision_label is not None
        else 0
    )
```

```python
# hyodo/cli/main.py — event_record's docstring (~lines 2193-2204), replace the
# "With --policy: ..." paragraph:

    With --policy: evaluate policy, stamp policy.* on the event, always try to
    append (including DENY) for audit continuity. Exit 1 on DENY or invalid
    event; exit 2 when input/policy path is unreadable or policy is
    unobserved; exit 3 on ASK (Phase 1: an external variable needs a human,
    unless an operator-granted trust level already covers it).
```

```python
# hyodo/cli/main.py — event_record's color line (~line 2309), replace:
#     color = "red" if decision_label == "DENY" else "green"
# with:
            color = {"ALLOW": "green", "DENY": "red"}.get(decision_label, "yellow")
```

```python
# hyodo/cli/main.py — policy_check's evaluate_policy call site (~line 2411)
# replace:
#     decision = evaluate_policy(normalized, cfg, observed_steps=observed)
# with:
    decision = evaluate_policy(normalized, cfg, observed_steps=observed, root=Path.cwd())
```

```python
# hyodo/cli/main.py — policy_check's exit-code block (~lines 2412-2427), replace
# from the "# 0 = ALLOW, 1 = DENY, 2 = unobserved..." comment through the end
# of the function:

    # 0 = ALLOW, 1 = DENY, 2 = UNOBSERVED, 3 = ASK. UNOBSERVED must not exit
    # like a plain DENY, and ASK must not exit like either.
    exit_code = {"ALLOW": 0, "DENY": 1, "UNOBSERVED": 2, "ASK": 3}[decision.decision]
    if json_output:
        payload = decision.as_dict()
        payload["exit_code"] = exit_code
        if decision.trust_level >= 2:
            payload["ledger_write_required"] = True
            payload["ledger_written"] = False
        console.print_json(json.dumps(payload))
    else:
        color = "green" if decision.decision == "ALLOW" else "red"
        console.print(f"[{color}]{decision.decision}[/{color}]")
        if decision.rule_id:
            console.print(f"rule_id: {decision.rule_id}")
        if decision.reason:
            console.print(f"reason: {decision.reason}")
        if decision.trust_level >= 2:
            console.print(
                "[yellow]trust level 2+ requires the decision to be recorded — "
                "use `hyodo event record --policy`[/yellow]"
            )
    raise typer.Exit(exit_code)
```

```python
# hyodo/cli/main.py — policy_check's docstring (~lines 2344-2349), replace:

    """
    Evaluate one event against a local policy.toml.

    Exit: 0 ALLOW · 1 DENY · 2 unobserved (missing/invalid policy or event) ·
    3 ASK (an external variable needs a human, unless trust already covers it).
    Does not write the ledger (use ``hyodo event record --policy`` for that).
    """
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/bin/python -m pytest tests/test_cli_policy_check.py tests/test_agent_events.py -v`
  Expected: PASS for the new file, and every pre-existing CLI test in `test_agent_events.py` (`test_cli_event_record_with_policy_deny`, `test_cli_policy_check_allow_deny_unobserved`, etc.) unchanged.

- [ ] **Step 5: Run the full gate** — `.venv/bin/ruff check hyodo tests --fix && .venv/bin/ruff format hyodo tests && .venv/bin/pyright hyodo && .venv/bin/python -m pytest tests -q`

- [ ] **Step 6: Commit**

```bash
git add hyodo/cli/main.py tests/test_cli_policy_check.py
git commit -m "$(cat <<'EOF'
feat(cli): policy check / event record --policy exit 3 on ASK

policy_check's ternary (0 ALLOW / 2 UNOBSERVED / else 1) had no room
for a fourth value; it is now a 4-way dict lookup. event_record's
ternary (1 DENY / else 0) had a real gap the design doc calls out by
name: an UNOBSERVED decision from evaluate_policy exited 0, contradicting
policy_check's own "UNOBSERVED must not exit like a plain DENY" comment
one function away. Both now use the same {"ALLOW":0,"DENY":1,
"UNOBSERVED":2,"ASK":3} mapping. Both evaluate_policy call sites now
pass root= so path_outside_root and trust-store lookups work. policy
check --json/text gain the trust-level-2+ ledger-obligation note.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PH1ofuuGrbVpW3vsBfaqPT
EOF
)"
```

---

### Task 9: CLI — `hyodo policy trust grant` / `show`

**Files:** Modify `hyodo/cli/main.py` (add `policy_trust_app` near line 123, two new commands); Test `tests/test_policy_trust.py`
**Interfaces:** Consumes: `hyodo.policy_trust` (Task 6). Produces: `hyodo policy trust grant --level N [--by NAME] [--yes] [--root PATH]`, `hyodo policy trust show [--json] [--root PATH]` CLI commands.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_policy_trust.py — append


# --------------------------------------------------------------------------- #
# CLI: hyodo policy trust grant / show
# --------------------------------------------------------------------------- #

import json as _json
from typer.testing import CliRunner

from hyodo.cli.main import app

runner = CliRunner()


def test_cli_policy_trust_grant_and_show_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(POLICY_TRUST_ENV_VAR, "1")
    grant_result = runner.invoke(
        app,
        ["policy", "trust", "grant", "--level", "2", "--by", "tester", "--root", str(tmp_path)],
    )
    assert grant_result.exit_code == 0, grant_result.output

    show_result = runner.invoke(
        app, ["policy", "trust", "show", "--root", str(tmp_path), "--json"]
    )
    assert show_result.exit_code == 0
    payload = _json.loads(show_result.output)
    assert payload["granted_level"] == 2
    assert payload["effective_level"] == 2  # no policy.toml -> cap defaults to 3


def test_cli_policy_trust_grant_rejects_out_of_range_level(tmp_path: Path):
    result = runner.invoke(
        app, ["policy", "trust", "grant", "--level", "9", "--root", str(tmp_path)]
    )
    assert result.exit_code == 2


def test_cli_policy_trust_grant_refuses_noninteractively_without_env_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv(POLICY_TRUST_ENV_VAR, raising=False)
    monkeypatch.setattr("hyodo.policy_trust._is_noninteractive", lambda: True)
    result = runner.invoke(
        app, ["policy", "trust", "grant", "--level", "2", "--root", str(tmp_path)]
    )
    assert result.exit_code == 1
    assert not (tmp_path / POLICY_TRUST_RELATIVE_PATH).exists()


def test_cli_policy_trust_show_with_cap_from_policy_toml(tmp_path: Path):
    hyodo_dir = tmp_path / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "policy.toml").write_text(
        f'''schema = "{POLICY_TRUST_SCHEMA_ID.replace("-trust", "")}"

[trust]
max_level = 1
''',
        encoding="utf-8",
    )
    grant_policy_trust(tmp_path, 3, by="human:test")

    result = runner.invoke(app, ["policy", "trust", "show", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = _json.loads(result.output)
    assert payload["cap"] == 1
    assert payload["granted_level"] == 3
    assert payload["effective_level"] == 1  # min(cap, granted)
```

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/bin/python -m pytest tests/test_policy_trust.py -k "cli_policy_trust" -v`
  Expected: FAIL with `AssertionError: 2 == 0` from typer reporting "No such command 'trust'." (exit code 2), since `hyodo policy trust` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# hyodo/cli/main.py — near the existing `policy_app` declaration (~line 101-105),
# add immediately after it:

policy_trust_app = typer.Typer(
    name="trust",
    help="Operator-controlled trust ceiling for policy ASK escalation (untracked store)",
    add_completion=False,
)
policy_app.add_typer(policy_trust_app, name="trust")
```

```python
# hyodo/cli/main.py — imports, extend the hyodo.policy_trust import added in Task 8

from hyodo.policy_trust import (
    POLICY_TRUST_RELATIVE_PATH,
    default_granted_by,
    effective_trust_level,
    grant_policy_trust,
    load_policy_trust,
    resolve_policy_trust_grant,
)
```

```python
# hyodo/cli/main.py — new commands, placed after policy_check (end of file section)


@policy_trust_app.command("grant")
def policy_trust_grant(
    level: int = typer.Option(..., "--level", help="Trust level to grant (0-3)"),
    by: str | None = typer.Option(
        None, "--by", help="Human name recorded as granted_by (default: $USER)"
    ),
    yes: bool = typer.Option(
        False, "--yes", help="Skip the interactive confirmation prompt (TTY only)"
    ),
    root: str = typer.Option(
        ".", "--root", help="Project root that owns .hyodo/policy-trust.json"
    ),
):
    """
    Grant an operator-controlled trust level for policy ASK escalation.

    Writes .hyodo/policy-trust.json (untracked, TOFU-style). Refuses to run
    non-interactively unless HYODO_POLICY_TRUST_ALL is truthy — --yes only
    skips the interactive confirmation prompt when a TTY is actually present,
    it is not itself a non-interactive escape hatch.
    """
    if not (0 <= level <= 3):
        console.print("[red]--level must be an integer between 0 and 3.[/red]")
        raise typer.Exit(2)
    root_path = Path(root).resolve()
    name = by or default_granted_by()
    decision = resolve_policy_trust_grant(level, by=name, yes=yes)
    if not decision.approved:
        console.print(f"[red]{decision.reason}[/red]")
        raise typer.Exit(1)
    granted_by = decision.via if decision.via.startswith("env:") else f"human:{name}"
    state = grant_policy_trust(root_path, level, by=granted_by)
    console.print(
        f"[green]Granted[/green] policy trust level {state.level} (by {state.granted_by})"
    )
    raise typer.Exit(0)


@policy_trust_app.command("show")
def policy_trust_show(
    root: str = typer.Option(".", "--root", help="Project root to inspect"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
):
    """Show the configured trust cap, the granted level, and recent history."""
    root_path = Path(root).resolve()
    cfg, _policy_err = try_load_policy(root_path / POLICY_RELATIVE_PATH)
    cap = cfg.trust.max_level if cfg is not None and cfg.trust is not None else None
    state, _trust_err = load_policy_trust(root_path)
    effective = effective_trust_level(cap if cap is not None else 3, state)
    history = list(state.history[-3:]) if state is not None else []

    if json_output:
        console.print_json(
            json.dumps(
                {
                    "cap": cap,
                    "granted_level": state.level if state is not None else None,
                    "effective_level": effective,
                    "granted_at": state.granted_at if state is not None else None,
                    "granted_by": state.granted_by if state is not None else None,
                    "history": [
                        {
                            "level": h.level,
                            "granted_at": h.granted_at,
                            "granted_by": h.granted_by,
                        }
                        for h in history
                    ],
                }
            )
        )
    else:
        console.print(f"cap: {cap if cap is not None else 'no cap configured'}")
        console.print(f"granted: {state.level if state is not None else 'not granted'}")
        console.print(f"effective: {effective}")
        if state is not None:
            console.print(f"granted_at: {state.granted_at}")
            console.print(f"granted_by: {state.granted_by}")
            for h in history:
                console.print(f"  history: level {h.level} at {h.granted_at} by {h.granted_by}")
    raise typer.Exit(0)
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/bin/python -m pytest tests/test_policy_trust.py -v`
  Expected: PASS (every test in the file, including the CLI tests added in this task).

- [ ] **Step 5: Run the full gate** — `.venv/bin/ruff check hyodo tests --fix && .venv/bin/ruff format hyodo tests && .venv/bin/pyright hyodo && .venv/bin/python -m pytest tests -q`

- [ ] **Step 6: Commit**

```bash
git add hyodo/cli/main.py tests/test_policy_trust.py
git commit -m "$(cat <<'EOF'
feat(cli): hyodo policy trust grant / show

New `hyodo policy trust` sub-typer. `grant --level N [--by NAME] [--yes]
[--root PATH]` writes .hyodo/policy-trust.json through
resolve_policy_trust_grant, refusing non-interactively unless
HYODO_POLICY_TRUST_ALL is set. `show [--json] [--root PATH]` reports
the policy.toml cap, the granted level, the effective (min) level, and
the last three history entries.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PH1ofuuGrbVpW3vsBfaqPT
EOF
)"
```

---

### Task 10: Docs — example policy, README, CHANGELOG, mcp_server, module docstring

**Files:** Modify `examples/fde-evidence-spine/policy.toml`, `README.md` (line 150), `CHANGELOG.md` (Unreleased section), `hyodo/mcp_server.py` (lines 251-254), `hyodo/policy.py` (module docstring, lines 1-7)
**Interfaces:** Consumes: nothing. Produces: no code changes — documentation only. No test is written for this task (docs are not executable behavior); Step 4/"passes" is a manual read-through plus the existing `tests/test_public_language.py` gate.

- [ ] **Step 1: Write the failing test** — N/A (documentation task). The relevant automated check is the repository's existing English-only gate, run in Step 5.

- [ ] **Step 2: Run test to verify it fails** — N/A.

- [ ] **Step 3: Write minimal implementation**

```toml
# examples/fde-evidence-spine/policy.toml — append at the end of the file

# Phase 1-A additions — both [web] and [trust] are optional; omitting them
# evaluates identically to the policy above.

# [web]
# allowed_domains = ["api.example.com", "*.internal.example.com"]
# allow_non_get = false
# allow_credential_paths = false
#
# # Tools judged as discretionary (ASK-eligible) beyond the built-in web-tool
# # set {web_fetch, browser, http, fetch, WebFetch, WebSearch}.
# ask_tools = ["send_email"]
# ask_threshold = 2
#
# [trust]
# max_level = 2
```

```markdown
<!-- README.md — line 150, replace the event/policy exit-contracts row -->
| `event` / `policy` | `0` valid/ALLOW · `1` invalid/DENY · `2` unobserved · `3` ASK (`policy check` / `event record --policy` only) |
```

```markdown
<!-- CHANGELOG.md — Unreleased, under ### Added -->
- `hyodo policy check` / `hyodo event record --policy` gain a fourth
  decision, `ASK` (exit code 3), driven by observed external variables
  (unlisted web domains, paths outside the project root, discretionary
  tools) and an operator-controlled trust ladder (`hyodo policy trust
  grant`/`show`, stored in the untracked `.hyodo/policy-trust.json`).
  `PolicyConfig` gains optional `[web]` / `ask_tools` / `ask_threshold` /
  `[trust]` fields; every one is a backward-compatible no-op when absent.
```

```markdown
<!-- CHANGELOG.md — Unreleased, under ### Fixed -->
- `hyodo event record --policy` no longer exits `0` on an `UNOBSERVED`
  policy decision — it now uses the same four-way ALLOW/DENY/UNOBSERVED/
  ASK exit mapping `hyodo policy check` already used, closing a gap where
  an unobserved policy silently behaved like an ALLOW.
```

```python
# hyodo/mcp_server.py — hyodo_policy_check docstring (line 254), replace:

        """Evaluate one event through ``hyodo policy check`` within the locked workspace.

        Exit codes are forwarded verbatim from the CLI subprocess: 0 ALLOW,
        1 DENY, 2 UNOBSERVED, 3 ASK (Phase 1: an external variable — an
        unlisted web domain, a path outside the project root, a
        discretionary tool — needs a human, unless an operator-granted
        trust level already covers it).
        """
```

```python
# hyodo/policy.py — module docstring (lines 1-7), replace:

"""Local policy gate for agent events (FDE Evidence Spine).

Policy is loadable from ``.hyodo/policy.toml`` (schema ``hyodo.policy/v1``).
Missing or malformed policy is **unobserved**, never silent ALLOW.

HyoDo emits a decision object; the agent runtime must enforce DENY.

Schema ``hyodo.policy/v1`` follows an "optional fields only" convention:
every field ever added to this schema id must default to a value that
reproduces prior behavior when absent, so an operator's existing
``policy.toml`` keeps evaluating identically across HyoDo upgrades.
``require_declared_paths`` established this pattern first; ``web``,
``ask_tools``, ``ask_threshold``, and ``trust`` (Phase 1-A) follow it, and
any future field on this schema id must too.
"""
```

- [ ] **Step 4: Run test to verify it passes** — Manual read-through: confirm the README table row still renders as a valid Markdown table, the CHANGELOG entries sit under the correct `### Added`/`### Fixed` headings in `[Unreleased]`, and the example TOML still parses (`.venv/bin/python -c "import tomllib, pathlib; tomllib.loads(pathlib.Path('examples/fde-evidence-spine/policy.toml').read_text())"` — the appended block is fully commented out, so this must succeed unchanged).

- [ ] **Step 5: Run the full gate** — `.venv/bin/ruff check hyodo tests --fix && .venv/bin/ruff format hyodo tests && .venv/bin/pyright hyodo && .venv/bin/python -m pytest tests -q`
  Additionally run the public-language gate directly: `.venv/bin/python -m pytest tests/test_public_language.py -v`.

- [ ] **Step 6: Commit**

```bash
git add examples/fde-evidence-spine/policy.toml README.md CHANGELOG.md hyodo/mcp_server.py hyodo/policy.py
git commit -m "$(cat <<'EOF'
docs: document Phase 1-A's ASK exit code and [web]/[trust] config

Exit-contracts table gains ASK (3); CHANGELOG Unreleased documents the
new ASK/trust-ladder feature and the event record UNOBSERVED exit-code
fix; the shipped example policy.toml gains a commented [web]/[trust]
block in its existing per-field-annotation style; hyodo_policy_check's
MCP docstring names exit 3; hyodo.policy's module docstring states the
"optional fields only" schema convention as a permanent contract.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01PH1ofuuGrbVpW3vsBfaqPT
EOF
)"
```

---

### Task 11: Final full-suite verification and PR description

**Files:** None (verification only)
**Interfaces:** Consumes: everything from Tasks 1-10. Produces: nothing new — this task only verifies and documents.

- [ ] **Step 1: Write the failing test** — N/A. This task re-runs every test file touched by this plan as one combined pass, treating any failure as the "test" that must go from red to green.

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/bin/python -m pytest tests/test_policy_ask.py tests/test_policy_trust.py tests/test_cli_policy_check.py tests/test_policy_self_report_boundary.py tests/test_agent_events.py -v`
  Expected at this point: PASS already (each prior task ended with a passing full-suite run) — this step exists to catch any interaction effect between the 10 prior commits that a single-task run could not have seen (e.g. two tasks each independently green but colliding on a shared fixture or import order).

- [ ] **Step 3: Write minimal implementation** — N/A. If Step 2 reveals a failure, fix it in the file(s) it points to, re-running the affected task's own test selector first, then this task's combined selector again. Do not add new features here.

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/bin/python -m pytest tests -q` (the entire suite, no filters). Expected: PASS, 0 failures, 0 errors.

- [ ] **Step 5: Run the full gate** — `.venv/bin/ruff check hyodo tests --fix && .venv/bin/ruff format hyodo tests && .venv/bin/pyright hyodo && .venv/bin/python -m pytest tests -q && .venv/bin/python -m hyodo check && .venv/bin/python -m hyodo safe`
  (The last two commands run HyoDo against its own checkout, per this repository's contributor workflow — `hyodo check`/`hyodo safe` must both still pass on the modified tree.)

- [ ] **Step 6: Commit** — No commit for this task (verification only). Instead, prepare the PR description:

```markdown
## Summary

- Implements Package 1-A (`feat/policy-ask`) from
  `docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md`:
  `evaluate_policy` gains a real `ASK` decision (exit code 3) driven by
  observed external variables — unlisted web domains, paths outside the
  project root, discretionary tools — and an operator-controlled trust
  ladder (`hyodo policy trust grant`/`show`, stored in the untracked
  `.hyodo/policy-trust.json`).
- Fixes the `event record --policy` exit-code gap named in the spec: an
  `evaluate_policy`-produced `UNOBSERVED` previously exited `0`
  (indistinguishable from ALLOW); it now uses the same four-way
  ALLOW/DENY/UNOBSERVED/ASK mapping `policy check` already used.
- Adds `POLICY_DECISIONS`'s missing `UNOBSERVED` value so a caller can
  assert (and have quarantined under `policy.claimed`) its own
  unobserved decisions, exactly like ALLOW/DENY/ASK already could.
- Every new `PolicyConfig`/`PolicyDecision` field is optional/defaulted;
  an existing `policy.toml` with no `[web]`/`[trust]`/`ask_tools` evaluates
  byte-identically to before this change.

## Test plan

- [ ] `pytest tests -q` — full suite green
- [ ] `ruff check hyodo tests` / `ruff format --check hyodo tests` — clean
- [ ] `pyright hyodo` — clean
- [ ] `hyodo check` / `hyodo safe` against this checkout — pass
- [ ] Manual: `hyodo policy trust grant --level 2 --root /tmp/x` then
      `hyodo policy trust show --root /tmp/x --json` round-trips
- [ ] Manual: an existing `.hyodo/policy.toml` with no `[web]`/`[trust]`
      produces the same decision before and after this branch

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

---

## Self-review

### Spec coverage checklist (Package 1-A requirements → task)

| Requirement (spec section) | Task |
| --- | --- |
| `PolicyConfig` gains `web`/`ask_tools`/`ask_threshold`/`trust`, all optional | 3 |
| `WebPolicy`/`TrustPolicy` frozen dataclasses | 3 |
| `PolicyDecision` gains `coverage`/`external_variables`/`trust_level`, `as_dict()` key-set guard | 2 |
| `evaluate_policy` gains keyword-only `root` param, backward-compatible default | 7 |
| `tool.method` schema field (HTTP-verb allowlist, case-insensitive → upper) | 4 |
| minimal `tool.urls` schema field (1-A-scoped, justified in Scoping note) | 4 |
| `POLICY_DECISIONS` gains `UNOBSERVED` | 1 |
| Schema id stays `hyodo.policy/v1`; "optional fields only" convention documented | 3 (fields), 10 (docstring paragraph) |
| Trust store: untracked `.hyodo/policy-trust.json`, schema `hyodo.policy-trust/v1` | 6 |
| `HYODO_POLICY_TRUST_ALL` env var, mirroring `HYODO_GATES_TRUST_ALL` | 6, 9 |
| `granted_by` two-shape convention (`human:<name>` / `env:<VAR>`) | 6, 9 |
| `hyodo policy trust grant`/`show` CLI | 9 |
| Evaluation order: hard DENY 1.1-1.3 unchanged | 7 (preserved verbatim) |
| Evaluation order: hard DENY 1.4 `web_non_get_denied` | 5 (helper), 7 (wiring) |
| Evaluation order: hard DENY 1.5 `web_credential_path_denied` | 5 (helper), 7 (wiring) |
| External variable 2.1 `web_domain_unlisted:<domain>` | 5 (helper), 7 (wiring) |
| External variable 2.2 `path_outside_root:<path>` | 7 |
| External variable 2.3 `ask_tools:<name>` (unconditional on `[web]`) | 5 (helper), 7 (wiring) |
| External variable 2.4 "cannot be checked" → `UNOBSERVED` | 7 |
| Trust gate: levels 0-3 behavior table | 6 (`effective_trust_level`), 7 (pipeline) |
| Trust gate: `ask_threshold` never degrades `ASK` to `DENY` | 7 |
| `[trust]` present + missing/damaged grant + external variable → `UNOBSERVED` `trust_grant_unobserved` | 6, 7 |
| `[trust]` present + missing grant + zero external variables → unaffected `ALLOW` | 7 |
| Coverage table (tool identity / path / web / step boundary) | 5 |
| CLI: `policy check`/`event record --policy` exit 3 on ASK | 8 |
| CLI: `event record` UNOBSERVED-exits-0 fix (line 2290) | 8 |
| `--json` `ledger_write_required`/`ledger_written` at trust level ≥ 2 | 8 |
| Non-suppressible text note at trust level ≥ 2 | 8 |
| `mcp_server.py` docstring update (no code change) | 10 |
| `examples/fde-evidence-spine/policy.toml` `[web]`/`[trust]` example | 10 |
| README exit-contracts table gains ASK | 10 |
| CHANGELOG Unreleased entries (Added + Fixed) | 10 |
| Backward compatibility: existing `policy.toml` byte-identical decisions | 7 (dedicated test), verified again in 11 |
| Test plan row: `tests/test_policy_ask.py` full acceptance criteria | 2, 3, 5, 7 |
| Test plan row: `tests/test_policy_trust.py` grant/show/history/non-interactive | 6, 9 |
| Test plan row: `tests/test_policy_self_report_boundary.py` ASK isolation | 1 |
| Test plan row: `tests/test_cli_policy_check.py` exit 3 / exit 2 regression | 8 |

### Type-consistency check (every new public name, once, with its signature)

```python
# hyodo/events.py
POLICY_DECISIONS: frozenset[str]  # now includes "UNOBSERVED"
_HTTP_METHODS: frozenset[str]  # {"GET","HEAD","POST","PUT","PATCH","DELETE"}

# hyodo/policy.py
class WebPolicy:
    allowed_domains: tuple[str, ...] = ()
    allow_non_get: bool = False
    allow_credential_paths: bool = False

class TrustPolicy:
    max_level: int = 3

class PolicyConfig:
    # ...existing fields...
    web: WebPolicy | None = None
    ask_tools: tuple[str, ...] = ()
    ask_threshold: int | None = None
    trust: TrustPolicy | None = None

class PolicyDecision:
    # ...existing fields...
    coverage: tuple[int, int] = (0, 0)
    external_variables: tuple[str, ...] = ()
    trust_level: int = 1

def evaluate_policy(
    event: dict[str, Any],
    policy: PolicyConfig,
    *,
    observed_steps: int | None = None,
    root: Path | None = None,
) -> PolicyDecision: ...

def _is_web_classified(tool_name: str | None, policy: PolicyConfig) -> bool: ...
def _domain_allowed(domain: str, allowed_domains: tuple[str, ...]) -> bool: ...
def _credential_shaped(path: str | None) -> bool: ...
def _compute_coverage(
    policy: PolicyConfig, kind: Any, tool_name: str | None, paths: list[Any],
    urls: list[Any], method: str | None, observed_steps: int | None,
    root: Path | None, *, effective_level: int,
) -> tuple[int, int]: ...
def _resolve_trust_level(
    trust_policy: TrustPolicy | None, root: Path | None,
    external_variables: tuple[str, ...],
) -> tuple[int, str | None]: ...

# hyodo/policy_trust.py
POLICY_TRUST_SCHEMA_ID: str  # "hyodo.policy-trust/v1"
POLICY_TRUST_RELATIVE_PATH: Path  # .hyodo/policy-trust.json
POLICY_TRUST_ENV_VAR: str  # "HYODO_POLICY_TRUST_ALL"

class PolicyTrustGrant:
    level: int
    granted_at: str
    granted_by: str

class PolicyTrustState:
    level: int
    granted_at: str
    granted_by: str
    history: tuple[PolicyTrustGrant, ...] = ()

class PolicyTrustGrantDecision:
    approved: bool
    reason: str
    via: str

def load_policy_trust(root: Path) -> tuple[PolicyTrustState | None, str | None]: ...
def grant_policy_trust(root: Path, level: int, *, by: str) -> PolicyTrustState: ...
def effective_trust_level(max_level: int, granted: PolicyTrustState | None) -> int: ...
def default_granted_by() -> str: ...
def resolve_policy_trust_grant(level: int, *, by: str, yes: bool) -> PolicyTrustGrantDecision: ...

# hyodo/cli/main.py
policy_trust_app: typer.Typer  # registered as `hyodo policy trust`

def policy_trust_grant(
    level: int, by: str | None = None, yes: bool = False, root: str = ".",
) -> None: ...  # typer command: hyodo policy trust grant

def policy_trust_show(root: str = ".", json_output: bool = False) -> None: ...  # hyodo policy trust show
```
