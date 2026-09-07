"""Deterministic presentation of measured command outcomes."""


def render_verdict_line(decision: str, observed: int, expected: int, unit: str, detail: str) -> str:
    """Return one plain verdict line without changing a decision."""
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
}


def explain_decision(command: str, decision: str, rule_id: str | None = None) -> str:
    """Look up a stored explanation, then the decision-level fallback."""
    return EXPLANATIONS.get(
        (command, decision, rule_id),
        EXPLANATIONS.get(
            (command, decision, None),
            "No stored explanation for this rule yet — see README exit contracts",
        ),
    )
