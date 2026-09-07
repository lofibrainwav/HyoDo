"""Stored explanations cover literal and computed policy rule identifiers."""

import ast
import inspect

import hyodo.policy
from hyodo.verdict import EXPLANATIONS, explain_decision


def test_rule_coverage():
    tree = ast.parse(inspect.getsource(hyodo.policy))
    rules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "rule_id":
            rules.update(
                n.value
                for n in ast.walk(node.value)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
            )
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in {"rule_id", "unobserved_boundary"}
            for t in node.targets
        ):
            rules.update(
                n.value
                for n in ast.walk(node.value)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
            )
        if isinstance(node, ast.Return) and node.value is not None:
            for value in ast.walk(node.value):
                if isinstance(value, ast.Tuple):
                    rules.update(
                        item.value
                        for item in value.elts
                        if isinstance(item, ast.Constant)
                        and isinstance(item.value, str)
                        and item.value.isidentifier()
                    )
    for command in ("policy check", "event record --policy"):
        assert rules <= {rule for cmd, _, rule in EXPLANATIONS if cmd == command}
        for decision in ("ALLOW", "ASK", "DENY", "UNOBSERVED"):
            assert (command, decision, None) in EXPLANATIONS
    for command in ("check", "safe"):
        for decision in ("PASS", "FAIL", "UNOBSERVED"):
            assert (command, decision, None) in EXPLANATIONS


def test_fallback():
    assert explain_decision("check", "PASS", "future_rule") == EXPLANATIONS["check", "PASS", None]
    assert explain_decision("unknown", "UNOBSERVED") == (
        "No stored explanation for this rule yet — see README exit contracts"
    )
