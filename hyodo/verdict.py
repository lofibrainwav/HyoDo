"""Deterministic presentation of measured command outcomes.

A profile (``engineer`` | ``vibe`` | ``professional``, see
``hyodo.audience``) changes wording only. Every profile renders the same
``observed``/``expected`` figures and the same ``detail`` text handed in by
the caller; only the decision-word vocabulary around them differs. Engineer
is exactly today's format, unchanged.
"""

from hyodo.audience import apply_domain_nouns

_VIBE_TRAFFIC_LIGHT: dict[str, str] = {
    "PASS": "GREEN",
    "ALLOW": "GREEN",
    "ASK": "YELLOW",
    "DENY": "RED",
    "FAIL": "RED",
    "UNOBSERVED": "GREY — could not see",
}

_VIBE_ACTION: dict[str, str] = {
    "PASS": "You're clear to move on.",
    "ALLOW": "You're clear to move on.",
    "ASK": "Stop and get a human's OK before continuing.",
    "DENY": "Stop — fix this before continuing.",
    "FAIL": "Stop — fix this before continuing.",
    "UNOBSERVED": "Stop — this isn't a pass; fix access and try again.",
}

_PROFESSIONAL_CONTROL: dict[str, str] = {
    "PASS": "Control satisfied",
    "ALLOW": "Control satisfied",
    "ASK": "Exception — approval required",
    "DENY": "Control failure",
    "FAIL": "Control failure",
    "UNOBSERVED": "Scope limitation — evidence not observed",
}


def render_verdict_line(
    decision: str,
    observed: int,
    expected: int | str,
    unit: str,
    detail: str,
    audience: str = "engineer",
) -> str:
    """Return one plain verdict line without changing a decision.

    ``audience`` selects wording only (see module docstring); an unknown
    value renders as ``engineer`` rather than raising, since a verdict line
    must always print something honest for the underlying decision.
    """
    if audience == "vibe":
        traffic = _VIBE_TRAFFIC_LIGHT.get(decision, "GREY — could not see")
        action = _VIBE_ACTION.get(decision, _VIBE_ACTION["UNOBSERVED"])
        return f"{traffic} — {detail} ({observed}/{expected} {unit} checked). {action}"
    if audience == "professional":
        control = _PROFESSIONAL_CONTROL.get(decision, "Scope limitation — evidence not observed")
        return f"{control} — {observed}/{expected} {unit} observed, {detail}"
    return f"HYODO {decision} — {observed}/{expected} {unit} observed, {detail}"


EXPLANATIONS: dict[tuple[str, str, str | None], str] = {
    (
        "check",
        "PASS",
        None,
    ): "Executed gates passed. This supports review readiness; human approval is still required.",
    (
        "check",
        "FAIL",
        None,
    ): "At least one executed gate failed. Fix the reported gate failures and run the check again.",
    (
        "check",
        "UNOBSERVED",
        None,
    ): "No gates could be executed or the input could not be loaded. Restore the required tools or configuration and rerun; this is not a validation pass.",
    (
        "safe",
        "PASS",
        None,
    ): "The scan completed without a blocking result. Findings are advisory unless strict mode blocks high-severity findings; review the scan details.",
    (
        "safe",
        "FAIL",
        None,
    ): "The scan found high-severity findings with strict mode enabled. Review and resolve those findings before rerunning.",
    (
        "safe",
        "UNOBSERVED",
        None,
    ): "The scan target could not be observed. Restore access to the target and rerun the scan.",
    (
        "policy check",
        "ALLOW",
        None,
    ): "The observed policy checks allow this event. Follow any ledger recording obligation before proceeding.",
    (
        "policy check",
        "ASK",
        None,
    ): "The event includes external variables requiring an operator decision. Review the declared boundaries before authorizing the action.",
    (
        "policy check",
        "DENY",
        None,
    ): "The event violates a configured policy boundary. Stop the action and correct the reported violation.",
    (
        "policy check",
        "UNOBSERVED",
        None,
    ): "Required policy evidence could not be observed. Restore the missing input or ledger evidence and reevaluate.",
    (
        "policy check",
        "DENY",
        "max_steps",
    ): "The recorded step count reached the configured limit. Stop this run or obtain an explicit policy revision.",
    (
        "policy check",
        "UNOBSERVED",
        "max_steps",
    ): "The ledger step count is unavailable. Restore the ledger before evaluating the step budget.",
    (
        "policy check",
        "ALLOW",
        "autorun_level2",
    ): "A level 2 trust grant covers the observed external variables. Record the decision in the ledger before proceeding.",
    (
        "policy check",
        "UNOBSERVED",
        "autorun_level2",
    ): "Level 2 requires an observed ledger step count. Restore ledger access and reevaluate.",
    (
        "policy check",
        "ALLOW",
        "autorun_level3",
    ): "Full delegation covers the observed external variables at level 3. Record the decision in the ledger before proceeding.",
    (
        "policy check",
        "UNOBSERVED",
        "autorun_level3",
    ): "Level 3 requires an observed ledger step count. Restore ledger access and reevaluate.",
    (
        "policy check",
        "DENY",
        "data_boundary",
    ): "A declared path matches a blocked path pattern. Stop the action and choose an allowed path.",
    (
        "policy check",
        "UNOBSERVED",
        "data_boundary_undeclared",
    ): "Paths needed for boundary checks were not declared. Supply the affected paths and reevaluate.",
    (
        "policy check",
        "ASK",
        "external_variable",
    ): "The event includes external variables requiring an operator decision. Review the declared boundaries before authorizing the action.",
    (
        "policy check",
        "DENY",
        "tool_not_allowed",
    ): "The declared tool is outside the configured allowlist. Choose an allowed tool or seek an explicit policy revision.",
    (
        "policy check",
        "DENY",
        "web_credential_path_denied",
    ): "A web path matches a credential boundary. Stop the request and remove the prohibited destination.",
    (
        "policy check",
        "UNOBSERVED",
        "web_credential_path_unobserved",
    ): "A web credential path could not be checked. Supply the required path evidence and reevaluate.",
    (
        "policy check",
        "DENY",
        "web_non_get_denied",
    ): "The declared HTTP method is prohibited by the web policy. Stop the request or seek an explicit policy revision.",
    (
        "policy check",
        "UNOBSERVED",
        "web_boundary_undeclared",
    ): "The configured web boundary lacks complete URL or method declarations. Declare both surfaces and reevaluate.",
    (
        "policy check",
        "UNOBSERVED",
        "trust_grant_unobserved",
    ): "The required trust grant is missing or unreadable. Restore an explicit operator grant and reevaluate.",
    (
        "event record --policy",
        "ALLOW",
        None,
    ): "The observed policy checks allow this event. Follow any ledger recording obligation before proceeding.",
    (
        "event record --policy",
        "ASK",
        None,
    ): "The event includes external variables requiring an operator decision. Review the declared boundaries before authorizing the action.",
    (
        "event record --policy",
        "DENY",
        None,
    ): "The event violates a configured policy boundary. Stop the action and correct the reported violation.",
    (
        "event record --policy",
        "UNOBSERVED",
        None,
    ): "Required policy evidence could not be observed. Restore the missing input or ledger evidence and reevaluate.",
    (
        "event record --policy",
        "DENY",
        "max_steps",
    ): "The recorded step count reached the configured limit. Stop this run or obtain an explicit policy revision.",
    (
        "event record --policy",
        "UNOBSERVED",
        "max_steps",
    ): "The ledger step count is unavailable. Restore the ledger before evaluating the step budget.",
    (
        "event record --policy",
        "ALLOW",
        "autorun_level2",
    ): "A level 2 trust grant covers the observed external variables. Record the decision in the ledger before proceeding.",
    (
        "event record --policy",
        "UNOBSERVED",
        "autorun_level2",
    ): "Level 2 requires an observed ledger step count. Restore ledger access and reevaluate.",
    (
        "event record --policy",
        "ALLOW",
        "autorun_level3",
    ): "Full delegation covers the observed external variables at level 3. Record the decision in the ledger before proceeding.",
    (
        "event record --policy",
        "UNOBSERVED",
        "autorun_level3",
    ): "Level 3 requires an observed ledger step count. Restore ledger access and reevaluate.",
    (
        "event record --policy",
        "DENY",
        "data_boundary",
    ): "A declared path matches a blocked path pattern. Stop the action and choose an allowed path.",
    (
        "event record --policy",
        "UNOBSERVED",
        "data_boundary_undeclared",
    ): "Paths needed for boundary checks were not declared. Supply the affected paths and reevaluate.",
    (
        "event record --policy",
        "ASK",
        "external_variable",
    ): "The event includes external variables requiring an operator decision. Review the declared boundaries before authorizing the action.",
    (
        "event record --policy",
        "DENY",
        "tool_not_allowed",
    ): "The declared tool is outside the configured allowlist. Choose an allowed tool or seek an explicit policy revision.",
    (
        "event record --policy",
        "DENY",
        "web_credential_path_denied",
    ): "A web path matches a credential boundary. Stop the request and remove the prohibited destination.",
    (
        "event record --policy",
        "UNOBSERVED",
        "web_credential_path_unobserved",
    ): "A web credential path could not be checked. Supply the required path evidence and reevaluate.",
    (
        "event record --policy",
        "DENY",
        "web_non_get_denied",
    ): "The declared HTTP method is prohibited by the web policy. Stop the request or seek an explicit policy revision.",
    (
        "event record --policy",
        "UNOBSERVED",
        "web_boundary_undeclared",
    ): "The configured web boundary lacks complete URL or method declarations. Declare both surfaces and reevaluate.",
    (
        "event record --policy",
        "UNOBSERVED",
        "trust_grant_unobserved",
    ): "The required trust grant is missing or unreadable. Restore an explicit operator grant and reevaluate.",
    (
        "policy check",
        "UNOBSERVED",
        "policy_missing",
    ): "The policy file is missing. Restore the policy and reevaluate; this is not a validation pass.",
    (
        "policy check",
        "UNOBSERVED",
        "policy_invalid",
    ): "The policy file could not be loaded. Correct the policy and reevaluate; this is not a validation pass.",
    (
        "event record --policy",
        "UNOBSERVED",
        "policy_missing",
    ): "The policy file is missing. Restore the policy and reevaluate; this is not a validation pass.",
    (
        "event record --policy",
        "UNOBSERVED",
        "policy_invalid",
    ): "The policy file could not be loaded. Correct the policy and reevaluate; this is not a validation pass.",
}


# --------------------------------------------------------------------------- #
# Per-profile explanation tables.
#
# Keyed identically to EXPLANATIONS (same (command, decision, rule_id)
# tuples) so tests/test_explain_flag.py's rule-coverage check applies to all
# three tables. The "policy check" and "event record --policy" entries share
# content (they always have, in EXPLANATIONS too) via _POLICY_VIBE /
# _POLICY_PROFESSIONAL below, keyed by (decision, rule_id) and expanded to
# both command names.
# --------------------------------------------------------------------------- #

_CHECK_SAFE_VIBE: dict[tuple[str, str], str] = {
    ("check", "PASS"): (
        "GREEN. Every check that actually ran said yes — like every smoke detector in "
        "the house staying quiet. A person should still look it over before you ship."
    ),
    ("check", "FAIL"): (
        "RED. Something you ran broke a rule, the way a smoke detector goes off. "
        "Fix what it flagged, then run the check again."
    ),
    ("check", "UNOBSERVED"): (
        "GREY — could not see. The checker couldn't even look, like inspecting a house "
        "with the lights off. Get the tools or settings working, then rerun; this is not "
        "a passing grade."
    ),
    ("safe", "PASS"): (
        "GREEN. The scan didn't find a stop-ship problem, like a home inspector giving a "
        "passing note. Still worth skimming what it flagged."
    ),
    ("safe", "FAIL"): (
        "RED. The scan found a high-risk issue and strict mode is on, so it's a stop "
        "sign. Fix what's listed, then scan again."
    ),
    ("safe", "UNOBSERVED"): (
        "GREY — could not see. The scanner couldn't reach what you asked it to check, "
        "like an inspector locked out of the house. Fix access and scan again."
    ),
}

_CHECK_SAFE_PROFESSIONAL: dict[tuple[str, str], str] = {
    ("check", "PASS"): (
        "Finding: all executed controls satisfied for this engagement. Evidence: the "
        "workpaper (gate results) below. Control: automated gate checks; human "
        "sign-off still required. Recommended action: proceed to review."
    ),
    ("check", "FAIL"): (
        "Finding: one or more executed controls failed. Evidence: failing gate names "
        "below. Control: automated gate checks. Recommended action: remediate the "
        "reported failures and re-run."
    ),
    ("check", "UNOBSERVED"): (
        "Finding: control evidence could not be captured. Evidence: no gates executed "
        "or input unreadable. Control: automated gate checks (not run). Recommended "
        "action: restore the required tooling or configuration and re-run; this is not "
        "a passing result."
    ),
    ("safe", "PASS"): (
        "Finding: no blocking result. Evidence: scan rows below. Control: early-warning "
        "safety scan, advisory unless strict mode is set. Recommended action: review "
        "findings; no gate action required."
    ),
    ("safe", "FAIL"): (
        "Finding: high-severity result under strict mode. Evidence: findings listed "
        "below. Control: early-warning safety scan (strict). Recommended action: "
        "resolve the listed findings before re-running."
    ),
    ("safe", "UNOBSERVED"): (
        "Finding: scan target not observed. Evidence: target path missing or "
        "unreadable. Control: early-warning safety scan (not run). Recommended action: "
        "restore access to the target and re-run."
    ),
}

# (decision, rule_id) -> text, shared by "policy check" and "event record --policy".
_POLICY_VIBE: dict[tuple[str, str | None], str] = {
    ("ALLOW", None): (
        "This action got a green light — the rules you set up say it's fine to go. If "
        "your setup asks for a log entry, make it before moving on."
    ),
    ("ASK", None): (
        "This one needs a human's OK first, like asking before borrowing the car. Look "
        "at what's unusual about it, then decide."
    ),
    ("DENY", None): (
        "This is a stop — the action crosses a line you drew for it. Don't do it; fix "
        "whatever tripped the rule."
    ),
    ("UNOBSERVED", None): (
        "The checker couldn't tell what's going on here, like refereeing a game you "
        "can't see. Get the missing information back, then check again."
    ),
    ("DENY", "max_steps"): (
        "This run has taken as many steps as you allowed, like a timer running out. "
        "Stop here, or explicitly raise the limit."
    ),
    ("UNOBSERVED", "max_steps"): (
        "The system can't tell how many steps have happened, so it can't check the "
        "limit. Fix the ledger, then try again."
    ),
    ("ALLOW", "autorun_level2"): (
        "You've given this a level-2 hall pass, so it's allowed to go without asking "
        "each time. Still write it down in the ledger."
    ),
    ("UNOBSERVED", "autorun_level2"): (
        "Level 2 needs to know the step count first, like checking your odometer "
        "before a long trip. Fix ledger access, then check again."
    ),
    ("ALLOW", "autorun_level3"): (
        "You've given this full trust at level 3, so it's allowed to go on its own. "
        "Still write it down in the ledger."
    ),
    ("UNOBSERVED", "autorun_level3"): (
        "Level 3 also needs the step count first. Fix ledger access, then check again."
    ),
    ("DENY", "data_boundary"): (
        "This touches a file or folder you specifically fenced off. Don't go there — "
        "pick a place that's allowed."
    ),
    ("UNOBSERVED", "data_boundary_undeclared"): (
        "The action didn't say which files it touches, so the fence can't be checked. "
        "Say which paths are involved, then check again."
    ),
    ("ASK", "external_variable"): (
        "Something about this action is outside the ordinary, so a human should weigh "
        "in — like a bank flagging an unusual purchase. Look at what's different, then "
        "decide."
    ),
    ("DENY", "tool_not_allowed"): (
        "This tool isn't on your approved list. Use one that is, or add it to the list on purpose."
    ),
    ("DENY", "web_credential_path_denied"): (
        "This web address looks like it leads to a login or secret page. Don't go "
        "there — remove that destination."
    ),
    ("UNOBSERVED", "web_credential_path_unobserved"): (
        "The system couldn't tell if this web address is safe. Give it the missing "
        "details, then check again."
    ),
    ("DENY", "web_non_get_denied"): (
        "This tries to change something on the web (not just read it), and that's "
        "against the rules here. Stop, or explicitly allow it."
    ),
    ("UNOBSERVED", "web_boundary_undeclared"): (
        "The web rule doesn't fully know the address or the method used. Fill in both, "
        "then check again."
    ),
    ("UNOBSERVED", "trust_grant_unobserved"): (
        "There's no readable permission slip for this trust level. Get an explicit "
        "human grant, then check again."
    ),
    ("UNOBSERVED", "policy_missing"): (
        "There's no rulebook here to check against — the policy file is missing. Add it "
        "back before trying again; this doesn't count as a pass."
    ),
    ("UNOBSERVED", "policy_invalid"): (
        "The rulebook exists but is broken or unreadable. Fix the policy file before "
        "trying again; this doesn't count as a pass."
    ),
}

_POLICY_PROFESSIONAL: dict[tuple[str, str | None], str] = {
    ("ALLOW", None): (
        "Finding: the event satisfies configured policy controls for this engagement. "
        "Evidence: coverage figures below. Control: agent policy gate. Recommended "
        "action: proceed; satisfy any ledger recording obligation."
    ),
    ("ASK", None): (
        "Finding: the event contains external variables requiring operator judgment. "
        "Evidence: declared boundaries below. Control: agent policy gate (discretionary "
        "review). Recommended action: review the declared boundaries and authorize or "
        "decline."
    ),
    ("DENY", None): (
        "Finding: the event violates a configured policy boundary. Evidence: the "
        "reported violation. Control: agent policy gate. Recommended action: halt the "
        "action and correct the violation."
    ),
    ("UNOBSERVED", None): (
        "Finding: required policy evidence is not observed. Evidence: missing input or "
        "ledger data. Control: agent policy gate (not evaluable). Recommended action: "
        "restore the missing evidence and re-evaluate."
    ),
    ("DENY", "max_steps"): (
        "Finding: recorded step count reached the configured ceiling. Evidence: ledger "
        "step count. Control: max_steps limit. Recommended action: stop the run, or "
        "obtain an explicit policy revision raising the limit."
    ),
    ("UNOBSERVED", "max_steps"): (
        "Finding: ledger step count unavailable. Evidence: ledger read failure. "
        "Control: max_steps limit (not evaluable). Recommended action: restore ledger "
        "access before re-evaluating."
    ),
    ("ALLOW", "autorun_level2"): (
        "Finding: an operator-granted level 2 trust grant covers the observed "
        "variables. Evidence: trust grant record. Control: autorun_level2. Recommended "
        "action: record the decision in the ledger."
    ),
    ("UNOBSERVED", "autorun_level2"): (
        "Finding: level 2 evaluation requires an observed ledger step count. Evidence: "
        "ledger read failure. Control: autorun_level2 (not evaluable). Recommended "
        "action: restore ledger access before re-evaluating."
    ),
    ("ALLOW", "autorun_level3"): (
        "Finding: full delegation is granted at level 3 for the observed variables. "
        "Evidence: trust grant record. Control: autorun_level3. Recommended action: "
        "record the decision in the ledger."
    ),
    ("UNOBSERVED", "autorun_level3"): (
        "Finding: level 3 evaluation requires an observed ledger step count. Evidence: "
        "ledger read failure. Control: autorun_level3 (not evaluable). Recommended "
        "action: restore ledger access before re-evaluating."
    ),
    ("DENY", "data_boundary"): (
        "Finding: a declared path matches a blocked path pattern. Evidence: the matched "
        "glob. Control: data_boundary. Recommended action: halt the action and select "
        "an allowed path."
    ),
    ("UNOBSERVED", "data_boundary_undeclared"): (
        "Finding: paths required for the boundary check were not declared. Evidence: "
        "absent path declarations. Control: data_boundary (strict mode, not "
        "evaluable). Recommended action: supply the affected paths and re-evaluate."
    ),
    ("ASK", "external_variable"): (
        "Finding: the event includes external variables requiring operator judgment. "
        "Evidence: declared boundaries below. Control: agent policy gate (discretionary "
        "review). Recommended action: review the declared boundaries before "
        "authorizing."
    ),
    ("DENY", "tool_not_allowed"): (
        "Finding: the declared tool is outside the configured allowlist. Evidence: the "
        "declared tool name. Control: tool allowlist. Recommended action: select an "
        "allowed tool or obtain an explicit policy revision."
    ),
    ("DENY", "web_credential_path_denied"): (
        "Finding: a requested web path matches a credential boundary. Evidence: the "
        "matched path. Control: web credential boundary. Recommended action: halt the "
        "request and remove the prohibited destination."
    ),
    ("UNOBSERVED", "web_credential_path_unobserved"): (
        "Finding: a web credential path could not be checked. Evidence: missing path "
        "evidence. Control: web credential boundary (not evaluable). Recommended "
        "action: supply the required path evidence and re-evaluate."
    ),
    ("DENY", "web_non_get_denied"): (
        "Finding: the declared HTTP method is prohibited by the web policy. Evidence: "
        "the declared method. Control: web method restriction. Recommended action: "
        "halt the request or obtain an explicit policy revision."
    ),
    ("UNOBSERVED", "web_boundary_undeclared"): (
        "Finding: the configured web boundary lacks complete URL or method "
        "declarations. Evidence: absent declarations. Control: web boundary (not "
        "evaluable). Recommended action: declare both surfaces and re-evaluate."
    ),
    ("UNOBSERVED", "trust_grant_unobserved"): (
        "Finding: the required trust grant is missing or unreadable. Evidence: trust "
        "grant read failure. Control: trust grant requirement. Recommended action: "
        "restore an explicit operator grant and re-evaluate."
    ),
    ("UNOBSERVED", "policy_missing"): (
        "Finding: the policy file is missing. Evidence: policy path lookup failure. "
        "Control: agent policy gate (not evaluable). Recommended action: restore the "
        "policy file; this is not a passing result."
    ),
    ("UNOBSERVED", "policy_invalid"): (
        "Finding: the policy file could not be loaded. Evidence: TOML parse or "
        "structural failure. Control: agent policy gate (not evaluable). Recommended "
        "action: correct the policy file; this is not a passing result."
    ),
}

_POLICY_COMMANDS = ("policy check", "event record --policy")


def _expand_policy_table(
    check_safe: dict[tuple[str, str], str], policy: dict[tuple[str, str | None], str]
) -> dict[tuple[str, str, str | None], str]:
    """Build a full EXPLANATIONS-shaped table from the check/safe and policy pieces."""
    table: dict[tuple[str, str, str | None], str] = {
        (command, decision, None): text for (command, decision), text in check_safe.items()
    }
    for command in _POLICY_COMMANDS:
        for (decision, rule_id), text in policy.items():
            table[(command, decision, rule_id)] = text
    return table


EXPLANATIONS_VIBE: dict[tuple[str, str, str | None], str] = _expand_policy_table(
    _CHECK_SAFE_VIBE, _POLICY_VIBE
)
EXPLANATIONS_PROFESSIONAL: dict[tuple[str, str, str | None], str] = _expand_policy_table(
    _CHECK_SAFE_PROFESSIONAL, _POLICY_PROFESSIONAL
)

_EXPLANATION_TABLES: dict[str, dict[tuple[str, str, str | None], str]] = {
    "vibe": EXPLANATIONS_VIBE,
    "professional": EXPLANATIONS_PROFESSIONAL,
}


def explain_decision(
    command: str,
    decision: str,
    rule_id: str | None = None,
    audience: str = "engineer",
    domain: str | None = None,
) -> str:
    """Look up a stored explanation for *audience*, falling back to engineer text.

    Lookup order: the profile's own (command, decision, rule_id) entry, then
    the profile's (command, decision, None) entry, then the engineer table's
    equivalent pair -- never a fabricated string. ``domain`` (professional
    only) swaps a handful of nouns via :func:`hyodo.audience.apply_domain_nouns`.
    """
    table = _EXPLANATION_TABLES.get(audience)
    text = None
    if table is not None:
        text = table.get((command, decision, rule_id))
        if text is None:
            text = table.get((command, decision, None))
    if text is None:
        text = EXPLANATIONS.get(
            (command, decision, rule_id),
            EXPLANATIONS.get(
                (command, decision, None),
                "No stored explanation for this rule yet — see README exit contracts",
            ),
        )
    if audience == "professional" and domain:
        text = apply_domain_nouns(text, domain)
    return text
