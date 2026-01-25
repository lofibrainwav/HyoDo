#!/usr/bin/env python3
"""
Optimization Scanner based on 'refactor-clean' Skill.
Scans the codebase for code smells and complexity metrics defined in the skill guide.

Metrics:
- Function Length > 30 lines (Warning)
- Class Length > 200 lines (Warning)
- Argument Count > 5 (Warning)
- Cyclomatic Complexity (proxy: if/for/while count) > 10 (Warning)
"""

import ast
import os
import sys
from collections import defaultdict
from pathlib import Path

# Thresholds from refactor-clean.md
THRESHOLDS = {
    "param_count": 5,
    "function_lines": 30,
    "class_lines": 200,
    "complexity": 10,  # Proxy
}


class MetrictsVisitor(ast.NodeVisitor):
    def __init__(self, filename) -> None:
        self.filename = filename
        self.issues = []
        self.current_class = None

    def visit_ClassDef(self, node) -> None:
        self.current_class = node.name
        # Class Length Check
        start = node.lineno
        end = node.end_lineno or start
        length = end - start
        if length > THRESHOLDS["class_lines"]:
            self.issues.append(
                {
                    "type": "Large Class",
                    "name": node.name,
                    "value": length,
                    "threshold": THRESHOLDS["class_lines"],
                    "file": self.filename,
                    "line": start,
                }
            )

        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def _check_function(self, node) -> None:
        name = f"{self.current_class}.{node.name}" if self.current_class else node.name

        # 1. Argument Count
        args_count = len(node.args.args)
        if args_count > THRESHOLDS["param_count"]:
            self.issues.append(
                {
                    "type": "Too Many Params",
                    "name": name,
                    "value": args_count,
                    "threshold": THRESHOLDS["param_count"],
                    "file": self.filename,
                    "line": node.lineno,
                }
            )

        # 2. Function Length
        start = node.lineno
        end = node.end_lineno or start
        length = end - start
        if length > THRESHOLDS["function_lines"]:
            self.issues.append(
                {
                    "type": "Long Function",
                    "name": name,
                    "value": length,
                    "threshold": THRESHOLDS["function_lines"],
                    "file": self.filename,
                    "line": start,
                }
            )

        # 3. Complexity (Simple Proxy)
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler)):
                complexity += 1
            if isinstance(child, (ast.BoolOp)):
                complexity += len(child.values) - 1

        if complexity > THRESHOLDS["complexity"]:
            self.issues.append(
                {
                    "type": "High Complexity",
                    "name": name,
                    "value": complexity,
                    "threshold": THRESHOLDS["complexity"],
                    "file": self.filename,
                    "line": start,
                }
            )


def scan_file(filepath) -> None:
    try:
        with open(filepath, encoding="utf-8") as f:
            code = f.read()
        tree = ast.parse(code)
        visitor = MetrictsVisitor(filepath)
        visitor.visit(tree)
        return visitor.issues
    except Exception:
        # print(f"Error parsing {filepath}: {e}")
        return []


def main() -> None:
    target_dir = Path("packages/afo-core")
    all_issues = []

    # Exclude external and migration paths
    excludes = ["migrations", "external", "tests", "legacy", "examples", ".venv"]

    print(f"🔍 Scanning {target_dir} for optimization hotspots...")
    print(
        f"   Thresholds: Func>{THRESHOLDS['function_lines']}L, Class>{THRESHOLDS['class_lines']}L, Params>{THRESHOLDS['param_count']}, Complexity>{THRESHOLDS['complexity']}"
    )

    count = 0
    for root, _, files in os.walk(target_dir):
        if any(ex in root for ex in excludes):
            continue

        for file in files:
            if file.endswith(".py"):
                path = Path(root) / file
                issues = scan_file(str(path))
                all_issues.extend(issues)
                count += 1

    print(f"✅ Scanned {count} files. Found {len(all_issues)} issues.\n")

    # Group by type
    by_type = defaultdict(list)
    for issue in all_issues:
        by_type[issue["type"]].append(issue)

    # Report Top Issues
    for issue_type, issues in by_type.items():
        print(f"📌 {issue_type}: {len(issues)} found")
        # Sort by value descending
        issues.sort(key=lambda x: x["value"], reverse=True)
        for i, issue in enumerate(issues[:5]):
            rel_path = os.path.relpath(issue["file"], os.getcwd())
            print(f"   {i + 1}. {issue['name']} ({issue['value']}) - {rel_path}:{issue['line']}")
        print()


if __name__ == "__main__":
    main()
