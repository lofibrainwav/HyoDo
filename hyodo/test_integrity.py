"""Phase 1-E: a native, unshellable signal for the Truth pillar.

`hyodo/safe/anti_gaming.py` (PR #161) already inspects a Python test file's AST
for evasive test bodies. This module widens that same idea into a project-level
report: it walks every discovered test file, flags test functions that execute
but never observe anything, and cites the anti-gaming rule ids
(HYO-SAFE-010/011/012) where its own findings overlap with that visitor's.

Zero model calls, zero judgment about intent. The only claim made here is
about the AST: a test function with no assertion in it cannot have caught a
regression no matter what it asserts about the code under test, because it
asserts nothing. A project with no discoverable tests is UNOBSERVED (see
`scanned_files`/`total_tests` both `0`), never treated as a failure by this
module — `hyodo check --strict-tests` is what turns a positive count of
vacuous tests into a failing Truth gate; this module only counts.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from hyodo.safe.anti_gaming import GamingFinding, scan_test_file_ast

#: Mirrors `hyodo/safety.py`'s `_SKIPPED_DIR_NAMES` (build/test caches: machine
#: -written, never reviewed, and not part of the project's own test suite).
#: Duplicated rather than imported so this module does not reach into another
#: module's private names across a package boundary.
_SKIPPED_DIR_NAMES = frozenset(
    {
        ".hypothesis",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
    }
)

#: The escape hatch for `no_target_reference`, the one heuristic category with a
#: known false-positive shape (fixture-driven tests). The same trailing-comment
#: escape-hatch shape ruff's own suppression comment already trains contributors
#: to look for.
ALLOW_VACUOUS_MARKER = "hyodo: allow-vacuous"

_ASSERT_LIKE_CALL_NAMES = {"raises", "warns"}


@dataclass(frozen=True)
class VacuousTestFinding:
    """One test function whose AST shows it cannot have observed a regression."""

    path: str
    line: int
    function: str
    # no_assertion | constant_assertion | no_target_reference | unexplained_skip
    category: str
    detail: str


@dataclass(frozen=True)
class TestIntegrityReport:
    """Project-level rollup of the vacuous-test scan."""

    #: Tells pytest this is a data class, not a `Test*`-named test class to collect
    #: (its name is fixed by the Phase 1-E spec's data model).
    __test__: ClassVar[bool] = False

    scanned_files: int
    total_files: int
    total_tests: int
    # no_assertion + constant_assertion, deduplicated per function
    vacuous_tests: int
    findings: tuple[VacuousTestFinding, ...]


def _is_test_file(path: Path) -> bool:
    name = path.name
    return (name.startswith("test_") and name.endswith(".py")) or name.endswith("_test.py")


def _discover_test_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if _is_test_file(root) else []
    candidates = [
        p
        for p in sorted(root.rglob("*.py"))
        if p.is_file()
        and _is_test_file(p)
        and not any(part.startswith(".git") or part in _SKIPPED_DIR_NAMES for part in p.parts)
    ]
    return candidates


def _call_target_name(func: ast.expr) -> str | None:
    """Return the trailing identifier of a call target (`x.assertEqual` -> `assertEqual`)."""
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _has_direct_observation(node: ast.FunctionDef) -> bool:
    """True when *node*'s own body contains an assertion-shaped statement.

    Covers a plain `assert`, a call to anything named `assert*` (`self.assertEqual`,
    `np.testing.assert_almost_equal`), and `pytest.raises`/`pytest.warns` used as a
    context manager (the standard exception-observation idiom that never contains a
    bare `assert`).
    """
    for sub in ast.walk(node):
        if sub is node:
            continue
        if isinstance(sub, ast.Assert):
            return True
        if isinstance(sub, ast.Call):
            name = _call_target_name(sub.func)
            if name and name.startswith("assert"):
                return True
        if isinstance(sub, ast.With):
            for item in sub.items:
                ctx = item.context_expr
                if isinstance(ctx, ast.Call):
                    name = _call_target_name(ctx.func)
                    if name in _ASSERT_LIKE_CALL_NAMES:
                        return True
    return False


_MAX_HELPER_DEPTH = 3


def _calls_asserting_helper(
    node: ast.FunctionDef,
    module_functions: dict[str, ast.FunctionDef],
    depth: int = _MAX_HELPER_DEPTH,
    _visited: frozenset[str] = frozenset(),
) -> bool:
    """True when *node* calls (transitively, up to `_MAX_HELPER_DEPTH` hops) a
    module-level function defined in the same module whose own body observes
    something. This is the helper-function carve-out: a test that delegates its
    assertions to a same-module helper is not "asserts nothing" just because the
    `assert` statement itself lives one function away."""
    if depth <= 0:
        return False
    for sub in ast.walk(node):
        if sub is node:
            continue
        if isinstance(sub, ast.Call):
            name = _call_target_name(sub.func)
            if name and name in module_functions and name not in _visited:
                helper = module_functions[name]
                if _has_direct_observation(helper):
                    return True
                if _calls_asserting_helper(helper, module_functions, depth - 1, _visited | {name}):
                    return True
    return False


def _has_observation(node: ast.FunctionDef, module_functions: dict[str, ast.FunctionDef]) -> bool:
    """True when *node* itself asserts something, or delegates to a same-module
    helper function that does (see `_calls_asserting_helper`)."""
    return _has_direct_observation(node) or _calls_asserting_helper(node, module_functions)


def _module_level_functions(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    """Map name -> def for every module-level (non-nested, non-class-method)
    function in *tree*, the universe `_calls_asserting_helper` may resolve a
    call into. Deliberately excludes methods and nested functions: the brief's
    "same module only" carve-out is for free functions a test calls directly."""
    return {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}


def _collect_asserts(node: ast.FunctionDef) -> list[ast.Assert]:
    return [sub for sub in ast.walk(node) if isinstance(sub, ast.Assert)]


def _is_trivial_assert(assert_node: ast.Assert) -> bool:
    """True when *assert_node*'s test expression can never fail (HYO-SAFE-011/012 shape)."""
    test = assert_node.test
    if isinstance(test, ast.Constant) and bool(test.value):
        return True
    if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
        left = test.left
        comparator = test.comparators[0]
        if (
            isinstance(left, ast.Constant)
            and isinstance(comparator, ast.Constant)
            and left.value == comparator.value
        ):
            return True
    return False


def _import_bound_names(tree: ast.Module) -> set[str]:
    """Names this module bound from the project's own `hyodo` package."""
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "hyodo" or alias.name.startswith("hyodo."):
                    bound.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "hyodo" or module.startswith("hyodo."):
                for alias in node.names:
                    bound.add(alias.asname or alias.name)
    return bound


def _references_target(node: ast.FunctionDef, bound_names: set[str]) -> bool:
    if not bound_names:
        return False
    return any(isinstance(sub, ast.Name) and sub.id in bound_names for sub in ast.walk(node))


def _skip_marker(decorator: ast.expr) -> tuple[str, ast.Call | None] | None:
    """Return (`skip`/`skipif`/`xfail`, the Call node if any) when *decorator* is a
    `@pytest.mark.<marker>` decorator, else None."""
    call = decorator if isinstance(decorator, ast.Call) else None
    target = call.func if call is not None else decorator
    if isinstance(target, ast.Attribute) and target.attr in {"skip", "skipif", "xfail"}:
        owner = target.value
        if isinstance(owner, ast.Attribute) and owner.attr == "mark":
            return target.attr, call
    return None


def _has_reason(call: ast.Call | None) -> bool:
    if call is None:
        return False
    return any(kw.arg == "reason" for kw in call.keywords)


def _def_has_allow_vacuous(source_lines: list[str], node: ast.FunctionDef) -> bool:
    """Return True when the `def` line (or its decorators) carries the escape hatch."""
    start = min([node.lineno] + [d.lineno for d in node.decorator_list])
    end = node.lineno
    for lineno in range(start, end + 1):
        if 1 <= lineno <= len(source_lines) and ALLOW_VACUOUS_MARKER in source_lines[lineno - 1]:
            return True
    return False


def _iter_test_functions(tree: ast.Module) -> list[ast.FunctionDef]:
    """Discover pytest-convention test functions: module-level `test_*`, or `test_*`
    methods inside a `Test*`-named class."""
    functions: list[ast.FunctionDef] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            functions.append(node)
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name.startswith("test_"):
                    functions.append(child)
    return functions


def _rule_citation(gaming_findings: list[GamingFinding], node: ast.FunctionDef) -> str:
    """Cite HYO-SAFE-01x rule ids from `anti_gaming` findings whose line falls inside
    *node*'s body, when any do."""
    lines = {
        lineno for sub in ast.walk(node) if isinstance(lineno := getattr(sub, "lineno", None), int)
    }
    ids = sorted({f.rule_id for f in gaming_findings if f.line in lines})
    if not ids:
        return ""
    return " (see " + ", ".join(ids) + ")"


def _scan_file(path: Path, root: Path) -> tuple[int, list[VacuousTestFinding]]:
    """Return (test function count, findings) for one file.

    Raises `SyntaxError`/`UnicodeDecodeError`/`OSError` on an unparsable or
    unreadable file; the caller (`scan_test_integrity`) is responsible for the
    "never crash on an unreadable file" posture, matching `_scan_directory`.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    source_lines = source.splitlines()
    gaming_findings = scan_test_file_ast(path)
    bound_names = _import_bound_names(tree)
    module_functions = _module_level_functions(tree)
    display_path = str(path.relative_to(root)) if _is_relative(path, root) else str(path)

    findings: list[VacuousTestFinding] = []
    functions = _iter_test_functions(tree)
    for node in functions:
        if not _has_observation(node, module_functions):
            citation = _rule_citation(gaming_findings, node)
            findings.append(
                VacuousTestFinding(
                    path=display_path,
                    line=node.lineno,
                    function=node.name,
                    category="no_assertion",
                    detail=f"'{node.name}' asserts nothing observable{citation}",
                )
            )
        else:
            asserts = _collect_asserts(node)
            if asserts and all(_is_trivial_assert(a) for a in asserts):
                citation = _rule_citation(gaming_findings, node)
                findings.append(
                    VacuousTestFinding(
                        path=display_path,
                        line=node.lineno,
                        function=node.name,
                        category="constant_assertion",
                        detail=(
                            f"'{node.name}' only asserts literal-constant expressions{citation}"
                        ),
                    )
                )

        if not _references_target(node, bound_names) and not _def_has_allow_vacuous(
            source_lines, node
        ):
            findings.append(
                VacuousTestFinding(
                    path=display_path,
                    line=node.lineno,
                    function=node.name,
                    category="no_target_reference",
                    detail=(
                        f"'{node.name}' never names a symbol imported from the "
                        f"project's own package (suppress with `# {ALLOW_VACUOUS_MARKER}`)"
                    ),
                )
            )

        for decorator in node.decorator_list:
            marker = _skip_marker(decorator)
            if marker is not None:
                marker_name, call = marker
                if not _has_reason(call):
                    findings.append(
                        VacuousTestFinding(
                            path=display_path,
                            line=node.lineno,
                            function=node.name,
                            category="unexplained_skip",
                            detail=f"'{node.name}' uses @pytest.mark.{marker_name} with no reason=",
                        )
                    )

    return len(functions), findings


def _is_relative(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def scan_test_integrity(root: Path) -> TestIntegrityReport:
    """Scan *root* for pytest-convention test files and report vacuous tests.

    Never raises: a file that fails to parse is counted in ``total_files`` but
    not ``scanned_files``, matching `_scan_directory`'s "never crash on an
    unreadable file" posture (`hyodo/safety.py:608-641`). A project with no
    discoverable tests reports all-zero counts (UNOBSERVED), not a failure.
    """
    candidates = _discover_test_files(root)
    total_files = len(candidates)
    scanned_files = 0
    total_tests = 0
    findings: list[VacuousTestFinding] = []

    for path in candidates:
        try:
            count, file_findings = _scan_file(path, root)
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        scanned_files += 1
        total_tests += count
        findings.extend(file_findings)

    vacuous_functions = {
        (f.path, f.function)
        for f in findings
        if f.category in {"no_assertion", "constant_assertion"}
    }

    return TestIntegrityReport(
        scanned_files=scanned_files,
        total_files=total_files,
        total_tests=total_tests,
        vacuous_tests=len(vacuous_functions),
        findings=tuple(findings),
    )
