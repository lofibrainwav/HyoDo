"""``hyodo eye`` — ephemeral visual evidence (Stage 2 package 2-D).

An external screen-capture tool (BYOM; HyoDo does not ship one) is invoked
under policy as ``tool_call`` ``eye.capture``. HyoDo never stores pixels: it
records an exact digest and a perceptual hash, shows the capture to the
operator with a visible countdown, deletes the file after a TTL, and records
a second event proving destruction. Proof of existence and proof of
destruction are a pair — see ``docs/EYE.md``.

This module is pure where possible; the one function that shells out to the
BYOM capture command (:func:`run_capture_command`) is isolated so tests can
monkeypatch it without a real screen-capture tool installed.
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hyodo.audience import load_config
from hyodo.events import (
    AGENT_EVENT_SCHEMA_VERSION,
    append_agent_event,
    content_digest,
    unevaluated_policy,
    validate_event,
)
from hyodo.phash import UnsupportedImageError, decode_image_grayscale, phash_dct64
from hyodo.policy import (
    PolicyConfig,
    apply_decision_to_event,
    evaluate_policy,
)
from hyodo.policy_trust import effective_trust_level, load_policy_trust

#: Default time-to-live, in seconds, before a capture is destroyed.
DEFAULT_TTL_S = 5
#: Env var carrying a JSON array of argv strings, overriding ``.hyodo/config.toml``.
CAPTURE_COMMAND_ENV_VAR = "HYODO_EYE_COMMAND"
#: Placeholder in the configured command template, replaced with the chosen
#: output path before the command runs.
OUT_PLACEHOLDER = "{out}"
_CAPTURE_TIMEOUT_S = 30

_EXIT_CODES = {"ALLOW": 0, "DENY": 1, "UNOBSERVED": 2, "ASK": 3}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_event(
    *, kind: str, actor: str, run_id: str, step_index: int, tool: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build a minimal, unvalidated ``hyodo.agent-event/v1`` shell."""
    raw: dict[str, Any] = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "run_id": run_id,
        "ts": _now_iso(),
        "kind": kind,
        "step_index": step_index,
        "actor": actor,
    }
    if tool is not None:
        raw["tool"] = tool
    return raw


def load_capture_command(root: Path) -> list[str] | None:
    """Resolve the configured BYOM capture command.

    Resolution order: ``HYODO_EYE_COMMAND`` (a JSON array of strings) first,
    then ``.hyodo/config.toml``'s ``[eye] command`` array. The env var wins
    so a one-off override (CI, a test) never requires touching a tracked
    file. Returns ``None`` when neither is configured or either is
    malformed — a malformed config is treated the same as "absent" because
    the outcome (``eye_tool_absent``) is identical either way: there is no
    usable tool to run.
    """
    env_value = os.environ.get(CAPTURE_COMMAND_ENV_VAR)
    if env_value:
        try:
            parsed = json.loads(env_value)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, list) and all(isinstance(item, str) and item for item in parsed):
            return list(parsed)
        return None

    config = load_config(root)
    if not isinstance(config, dict):
        return None
    eye_table = config.get("eye")
    if not isinstance(eye_table, dict):
        return None
    command = eye_table.get("command")
    if isinstance(command, list) and all(isinstance(item, str) and item for item in command):
        return list(command)
    return None


def run_capture_command(argv: list[str]) -> subprocess.CompletedProcess[bytes]:
    """Run the BYOM capture command. No shell, a bounded timeout.

    Isolated from :func:`capture` so tests can monkeypatch this one
    function instead of needing a real screen-capture tool installed.
    """
    return subprocess.run(argv, timeout=_CAPTURE_TIMEOUT_S, capture_output=True, check=False)


def best_effort_open(path: Path) -> None:
    """Best-effort ``open``/``xdg-open`` on *path*. Never raises."""
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    with contextlib.suppress(OSError, subprocess.SubprocessError):
        subprocess.run([opener, str(path)], timeout=_CAPTURE_TIMEOUT_S, check=False)


def print_countdown(ttl_s: int, path: Path, *, sleep=time.sleep) -> None:
    """Print the capture path, then a per-second countdown line to stderr.

    ``sleep`` is a parameter so tests can pass a no-op and use ``--ttl 0``
    without a real wait; production code always passes the real
    :func:`time.sleep`.
    """
    print(f"eye: captured {path}", file=sys.stderr)
    for remaining in range(ttl_s, 0, -1):
        print(f"eye: destroying in {remaining}s ...", file=sys.stderr)
        sleep(1)


def _effective_trust_level(policy: PolicyConfig, root: Path) -> int:
    """Resolve the effective trust level for the ``--keep`` gate.

    An unreadable or missing trust grant resolves to level 0 here (fail
    closed): ``--keep`` is exactly the kind of retention decision that must
    never default-open on an unobservable grant.
    """
    if policy.trust is None:
        return 1
    state, error = load_policy_trust(root)
    if error is not None:
        return 0
    return effective_trust_level(policy.trust.max_level, state)


@dataclass(frozen=True)
class CaptureResult:
    """Outcome of one ``hyodo eye capture`` (or a verify re-capture)."""

    decision: str  # ALLOW | DENY | ASK | UNOBSERVED
    rule_id: str | None
    reason: str | None
    exit_code: int
    tool_call_event_id: str | None = None
    approval_event_id: str | None = None
    capture_event_id: str | None = None
    destroy_event_id: str | None = None
    digest: str | None = None
    phash: str | None = None
    ttl_s: int = DEFAULT_TTL_S
    destroyed_at: str | None = None
    kept: bool = False
    ledger_write_required: bool = False

    def as_dict(self) -> dict[str, Any]:
        """Serialize this result for ``--json`` output and the CLI receipt."""
        return {
            "decision": self.decision,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "exit_code": self.exit_code,
            "tool_call_event_id": self.tool_call_event_id,
            "approval_event_id": self.approval_event_id,
            "capture_event_id": self.capture_event_id,
            "destroy_event_id": self.destroy_event_id,
            "digest": self.digest,
            "phash": self.phash,
            "ttl_s": self.ttl_s,
            "destroyed_at": self.destroyed_at,
            "kept": self.kept,
            "ledger_write_required": self.ledger_write_required,
        }


def capture(
    root: Path,
    policy: PolicyConfig,
    *,
    ttl_s: int = DEFAULT_TTL_S,
    keep: bool = False,
    yes: bool = False,
    open_after: bool = False,
    sleep=time.sleep,
) -> CaptureResult:
    """Run one ``eye.capture`` under policy: gate, capture, show, destroy.

    Mirrors the evaluation order in the design spec: (1) the ``eye.capture``
    tool_call is policy-gated first — ``eye.capture`` is an unconditional
    external variable, softened to ``ALLOW`` only at trust level 3; (2) only
    once the decision proceeds does an absent capture tool become
    ``UNOBSERVED``; (3) a real capture records the proof-of-existence event
    before the countdown; (4)-(5) the countdown and deletion produce the
    proof-of-destruction event; (6) ``--keep`` is gated on trust level >= 2
    *before* anything else runs, since it is refused with no capture at all
    below that level.
    """
    if keep and _effective_trust_level(policy, root) < 2:
        return CaptureResult(
            decision="DENY",
            rule_id="eye_keep_insufficient_trust",
            reason="--keep requires trust level >= 2",
            exit_code=_EXIT_CODES["DENY"],
        )

    run_id = str(uuid.uuid4())
    tool_call_raw = _new_event(
        kind="tool_call",
        actor="hyodo",
        run_id=run_id,
        step_index=0,
        tool={"name": "eye.capture", "args_digest": None, "paths": [], "method": None, "urls": []},
    )
    ok, reasons, normalized = validate_event(tool_call_raw)
    if not ok or normalized is None:  # pragma: no cover - internal construction guard
        return CaptureResult(
            decision="UNOBSERVED",
            rule_id="internal_error",
            reason=f"could not build eye.capture event: {reasons}",
            exit_code=_EXIT_CODES["UNOBSERVED"],
        )

    decision = evaluate_policy(normalized, policy, observed_steps=0, root=root)
    stamped = apply_decision_to_event(normalized, decision)
    append_agent_event(root, stamped)
    tool_call_event_id = stamped["event_id"]

    effective_decision = decision.decision
    approval_event_id: str | None = None
    if decision.decision == "ASK" and yes:
        approval_raw = _new_event(kind="decision", actor="human", run_id=run_id, step_index=1)
        ok2, _reasons2, approval_normalized = validate_event(approval_raw)
        if ok2 and approval_normalized is not None:
            approval_normalized["policy"] = unevaluated_policy(
                claimed={
                    "decision": "ALLOW",
                    "rule_id": "operator_approval",
                    "reason": "operator approved via --yes",
                }
            )
            if append_agent_event(root, approval_normalized):
                approval_event_id = approval_normalized["event_id"]
                effective_decision = "ALLOW"

    if effective_decision == "DENY":
        return CaptureResult(
            decision="DENY",
            rule_id=decision.rule_id,
            reason=decision.reason,
            exit_code=_EXIT_CODES["DENY"],
            tool_call_event_id=tool_call_event_id,
        )
    if effective_decision == "ASK":
        return CaptureResult(
            decision="ASK",
            rule_id=decision.rule_id,
            reason=decision.reason,
            exit_code=_EXIT_CODES["ASK"],
            tool_call_event_id=tool_call_event_id,
        )
    if effective_decision == "UNOBSERVED":
        return CaptureResult(
            decision="UNOBSERVED",
            rule_id=decision.rule_id,
            reason=decision.reason,
            exit_code=_EXIT_CODES["UNOBSERVED"],
            tool_call_event_id=tool_call_event_id,
        )

    # effective_decision == "ALLOW" from here.
    command = load_capture_command(root)
    if command is None:
        return CaptureResult(
            decision="UNOBSERVED",
            rule_id="eye_tool_absent",
            reason="no BYOM capture tool configured ([eye] command / HYODO_EYE_COMMAND)",
            exit_code=_EXIT_CODES["UNOBSERVED"],
            tool_call_event_id=tool_call_event_id,
            approval_event_id=approval_event_id,
        )

    capture_dir = root / ".hyodo" / "eye"
    capture_dir.mkdir(parents=True, exist_ok=True)
    out_path = capture_dir / f"{uuid.uuid4()}.png"
    argv = [token.replace(OUT_PLACEHOLDER, str(out_path)) for token in command]
    try:
        proc = run_capture_command(argv)
    except (OSError, subprocess.SubprocessError):
        proc = None

    if proc is None or proc.returncode != 0 or not out_path.exists():
        return CaptureResult(
            decision="UNOBSERVED",
            rule_id="eye_capture_failed",
            reason="capture command failed or produced no output file",
            exit_code=_EXIT_CODES["UNOBSERVED"],
            tool_call_event_id=tool_call_event_id,
            approval_event_id=approval_event_id,
        )

    image_bytes = out_path.read_bytes()
    digest = content_digest(image_bytes)
    unsupported = False
    phash: str | None
    try:
        gray = decode_image_grayscale(out_path)
        phash = phash_dct64(gray)
    except UnsupportedImageError:
        phash = None
        unsupported = True

    if open_after:
        best_effort_open(out_path)

    ephemeral: dict[str, Any] = {
        "ttl_s": ttl_s,
        "phash_algo": "dct64",
        "phash": phash,
        "destroyed_at": None,
        "kept": keep,
    }
    if unsupported:
        ephemeral["unsupported"] = True

    capture_raw = _new_event(kind="tool_result", actor="hyodo", run_id=run_id, step_index=2)
    capture_raw["parent_event_id"] = tool_call_event_id
    capture_raw["io"] = {"output_digest": digest}
    capture_raw["meta"] = {"tags": ["eye-capture"], "ephemeral": ephemeral}
    ok3, reasons3, capture_normalized = validate_event(capture_raw)
    if not ok3 or capture_normalized is None:  # pragma: no cover - internal construction guard
        return CaptureResult(
            decision="UNOBSERVED",
            rule_id="internal_error",
            reason=f"could not build eye-capture event: {reasons3}",
            exit_code=_EXIT_CODES["UNOBSERVED"],
            tool_call_event_id=tool_call_event_id,
            approval_event_id=approval_event_id,
        )
    append_agent_event(root, capture_normalized)
    capture_event_id = capture_normalized["event_id"]

    ledger_write_required = decision.trust_level >= 2

    if keep:
        return CaptureResult(
            decision="ALLOW",
            rule_id=decision.rule_id,
            reason="kept: no destruction step ran",
            exit_code=_EXIT_CODES["ALLOW"],
            tool_call_event_id=tool_call_event_id,
            approval_event_id=approval_event_id,
            capture_event_id=capture_event_id,
            digest=digest,
            phash=phash,
            ttl_s=ttl_s,
            destroyed_at=None,
            kept=True,
            ledger_write_required=ledger_write_required,
        )

    print_countdown(ttl_s, out_path, sleep=sleep)

    try:
        out_path.unlink()
        deleted = True
    except OSError:
        deleted = False

    if deleted:
        destroyed_at = _now_iso()
        destroy_ephemeral = dict(ephemeral)
        destroy_ephemeral["destroyed_at"] = destroyed_at
        destroy_raw = _new_event(kind="tool_result", actor="hyodo", run_id=run_id, step_index=3)
        destroy_raw["parent_event_id"] = capture_event_id
        destroy_raw["meta"] = {"tags": ["eye-destroy"], "ephemeral": destroy_ephemeral}
        ok4, _reasons4, destroy_normalized = validate_event(destroy_raw)
        destroy_event_id: str | None = None
        if ok4 and destroy_normalized is not None:
            append_agent_event(root, destroy_normalized)
            destroy_event_id = destroy_normalized["event_id"]

        if unsupported:
            return CaptureResult(
                decision="UNOBSERVED",
                rule_id="eye_image_unsupported",
                reason="captured image format is not decodable for a perceptual hash",
                exit_code=_EXIT_CODES["UNOBSERVED"],
                tool_call_event_id=tool_call_event_id,
                approval_event_id=approval_event_id,
                capture_event_id=capture_event_id,
                destroy_event_id=destroy_event_id,
                digest=digest,
                phash=None,
                ttl_s=ttl_s,
                destroyed_at=destroyed_at,
                kept=False,
                ledger_write_required=ledger_write_required,
            )
        return CaptureResult(
            decision="ALLOW",
            rule_id=decision.rule_id,
            reason=decision.reason,
            exit_code=_EXIT_CODES["ALLOW"],
            tool_call_event_id=tool_call_event_id,
            approval_event_id=approval_event_id,
            capture_event_id=capture_event_id,
            destroy_event_id=destroy_event_id,
            digest=digest,
            phash=phash,
            ttl_s=ttl_s,
            destroyed_at=destroyed_at,
            kept=False,
            ledger_write_required=ledger_write_required,
        )

    # Deletion failed: HyoDo cannot prove destruction, so the gate fails
    # closed even though the capture itself succeeded.
    failure_ephemeral = dict(ephemeral)
    failure_ephemeral["kept"] = True
    failure_raw = _new_event(kind="tool_result", actor="hyodo", run_id=run_id, step_index=3)
    failure_raw["parent_event_id"] = capture_event_id
    failure_raw["meta"] = {"tags": ["evidence_destruction_failed"], "ephemeral": failure_ephemeral}
    ok5, _reasons5, failure_normalized = validate_event(failure_raw)
    destroy_event_id = None
    if ok5 and failure_normalized is not None:
        append_agent_event(root, failure_normalized)
        destroy_event_id = failure_normalized["event_id"]
    return CaptureResult(
        decision="UNOBSERVED",
        rule_id="evidence_destruction_failed",
        reason="capture file could not be deleted; destruction cannot be proven",
        exit_code=_EXIT_CODES["UNOBSERVED"],
        tool_call_event_id=tool_call_event_id,
        approval_event_id=approval_event_id,
        capture_event_id=capture_event_id,
        destroy_event_id=destroy_event_id,
        digest=digest,
        phash=phash,
        ttl_s=ttl_s,
        destroyed_at=None,
        kept=True,
        ledger_write_required=ledger_write_required,
    )
