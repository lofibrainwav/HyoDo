"""AST-based inspection to prevent AI agents from gaming quality gates."""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class GamingFinding:
    file_path: str
    line: int
    rule_id: str
    message: str
    severity: str = "HIGH"


class AntiGamingVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.findings: List[GamingFinding] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name.startswith("test_"):
            meaningful_stmts = [
                stmt
                for stmt in node.body
                if not (
                    isinstance(stmt, ast.Pass)
                    or (
                        isinstance(stmt, ast.Expr)
                        and isinstance(stmt.value, ast.Constant)
                        and isinstance(stmt.value.value, str)
                    )
                )
            ]
            if not meaningful_stmts:
                self.findings.append(
                    GamingFinding(
                        file_path=self.file_path,
                        line=node.lineno,
                        rule_id="HYO-SAFE-010",
                        message=f"Empty test function '{node.name}' provides no verification.",
                    )
                )
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        test = node.test

        if isinstance(test, ast.Constant) and bool(test.value) is True:
            self.findings.append(
                GamingFinding(
                    file_path=self.file_path,
                    line=node.lineno,
                    rule_id="HYO-SAFE-011",
                    message="Tautological assertion (always evaluates to True).",
                )
            )
        elif isinstance(test, ast.Compare):
            left = test.left
            if len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                comparator = test.comparators[0]
                if isinstance(left, ast.Constant) and isinstance(comparator, ast.Constant):
                    if left.value == comparator.value:
                        self.findings.append(
                            GamingFinding(
                                file_path=self.file_path,
                                line=node.lineno,
                                rule_id="HYO-SAFE-012",
                                message="Trivial literal comparison in assertion.",
                            )
                        )

        self.generic_visit(node)


def scan_test_file_ast(file_path: Path) -> List[GamingFinding]:
    """Inspects a Python test file and returns findings if evasive test patterns exist."""
    if not file_path.suffix == ".py":
        return []

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    visitor = AntiGamingVisitor(str(file_path))
    visitor.visit(tree)
    return visitor.findings
