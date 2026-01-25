"""Multi-Agent Code Review Node for Chancellor V2

Implements parallel/serial code validation system for comprehensive code quality assurance.
Inspired by human peer review processes and automated code analysis pipelines.

Trinity Score Integration:
- 眞 (Truth): Code correctness and bug detection
- 善 (Goodness): Code quality and maintainability
- 美 (Beauty): Code style and readability
- 孝 (Serenity): User experience and error handling
- 永 (Eternity): Documentation and long-term maintainability
"""

import ast
import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from AFO.chancellor_graph import ChancellorContext, ChancellorNode
from AFO.trinity_metric_wrapper import TrinityScore

logger = logging.getLogger(__name__)


@dataclass
class CodeReviewConfig:
    """Configuration for multi-agent code review"""

    parallel_agents: int = 3  # Number of parallel review agents
    serial_iterations: int = 2  # Number of serial verification rounds
    timeout_seconds: float = 60.0  # Timeout for each analysis
    min_confidence_threshold: float = 0.7  # Minimum confidence for approval
    max_complexity_score: int = 10  # Maximum acceptable complexity
    security_scan_enabled: bool = True  # Enable security scanning
    test_generation_enabled: bool = True  # Enable automated test generation


@dataclass
class CodeAnalysisResult:
    """Result of code analysis"""

    file_path: str
    language: str
    loc: int  # Lines of code
    complexity_score: int
    maintainability_index: float
    test_coverage: float | None
    security_issues: list[dict[str, Any]]
    bugs_detected: list[dict[str, Any]]
    style_violations: list[dict[str, Any]]
    performance_issues: list[dict[str, Any]]
    suggestions: list[str]


@dataclass
class CodeReviewResult:
    """Result of multi-agent code review"""

    is_approved: bool
    overall_score: float
    confidence_level: float
    execution_time: float
    agent_results: list[dict[str, Any]]
    consensus_ratio: float
    critical_issues: list[dict[str, Any]]
    recommendations: list[str]
    generated_tests: list[str] | None = None


class CodeReviewAgent:
    """Individual code review agent"""

    def __init__(self, agent_id: str, agent_type: str, specialization: str) -> None:
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.specialization = specialization  # "truth", "goodness", "beauty"
        self.review_count = 0

    async def review_code(
        self, code: str, file_path: str, config: CodeReviewConfig
    ) -> dict[str, Any]:
        """Review code with specialized analysis"""
        start_time = time.perf_counter()

        try:
            if self.specialization == "truth":
                result = await self._analyze_correctness(code, file_path)
            elif self.specialization == "goodness":
                result = await self._analyze_quality(code, file_path)
            elif self.specialization == "beauty":
                result = await self._analyze_style(code, file_path)
            else:
                result = await self._analyze_general(code, file_path)

            self.review_count += 1
            execution_time = time.perf_counter() - start_time

            return {
                "agent_id": self.agent_id,
                "specialization": self.specialization,
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "timestamp": time.time(),
            }

        except Exception as e:
            execution_time = time.perf_counter() - start_time
            logger.error(f"Agent {self.agent_id} review failed: {e}")
            return {
                "agent_id": self.agent_id,
                "specialization": self.specialization,
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "timestamp": time.time(),
            }

    async def _analyze_correctness(self, code: str, file_path: str) -> dict[str, Any]:
        """Analyze code correctness (Truth agent)"""
        issues = []

        # Parse AST for syntax and structural analysis
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            issues.append(
                {
                    "type": "syntax_error",
                    "severity": "critical",
                    "message": f"Syntax error: {e}",
                    "line": e.lineno,
                    "suggestion": "Fix syntax error before proceeding",
                }
            )
            return {
                "score": 0.0,
                "issues": issues,
                "recommendations": ["Fix syntax errors", "Run syntax checker"],
            }

        # Check for common bug patterns
        bug_patterns = self._get_bug_patterns()
        for pattern_name, pattern_info in bug_patterns.items():
            matches = re.findall(pattern_info["pattern"], code, re.MULTILINE)
            if matches:
                issues.append(
                    {
                        "type": "potential_bug",
                        "severity": pattern_info["severity"],
                        "message": pattern_info["message"],
                        "pattern": pattern_name,
                        "suggestion": pattern_info["suggestion"],
                    }
                )

        # Calculate correctness score
        critical_issues = sum(1 for issue in issues if issue["severity"] == "critical")
        high_issues = sum(1 for issue in issues if issue["severity"] == "high")

        base_score = 1.0
        penalty = (critical_issues * 0.5) + (high_issues * 0.2)
        score = max(0.0, base_score - penalty)

        return {
            "score": score,
            "issues": issues,
            "recommendations": [
                "Add comprehensive error handling",
                "Implement input validation",
                "Add type hints for better correctness checking",
            ],
        }

    async def _analyze_quality(self, code: str, file_path: str) -> dict[str, Any]:
        """Analyze code quality (Goodness agent)"""
        issues = []
        recommendations = []

        # Calculate complexity metrics
        complexity = self._calculate_complexity(code)
        if complexity > 10:
            issues.append(
                {
                    "type": "complexity",
                    "severity": "medium",
                    "message": f"High complexity score: {complexity}",
                    "suggestion": "Refactor to reduce complexity",
                }
            )

        # Check function lengths
        functions = self._extract_functions(code)
        for func in functions:
            if func["length"] > 50:
                issues.append(
                    {
                        "type": "long_function",
                        "severity": "low",
                        "message": f"Function '{func['name']}' is too long ({func['length']} lines)",
                        "suggestion": "Break down into smaller functions",
                    }
                )

        # Check for code duplication (simplified)
        duplicate_lines = self._check_duplication(code)
        if duplicate_lines > 10:
            issues.append(
                {
                    "type": "duplication",
                    "severity": "medium",
                    "message": f"Potential code duplication: {duplicate_lines} similar lines",
                    "suggestion": "Extract common functionality into shared functions",
                }
            )

        # Quality score calculation
        base_score = 1.0
        penalty = len(issues) * 0.1
        score = max(0.0, base_score - penalty)

        recommendations.extend(
            [
                "Improve function naming consistency",
                "Add docstrings to all public functions",
                "Consider using design patterns where appropriate",
            ]
        )

        return {
            "score": score,
            "issues": issues,
            "recommendations": recommendations,
            "metrics": {
                "complexity": complexity,
                "function_count": len(functions),
                "duplicate_lines": duplicate_lines,
            },
        }

    async def _analyze_style(self, code: str, file_path: str) -> dict[str, Any]:
        """Analyze code style (Beauty agent)"""
        issues = []
        recommendations = []

        lines = code.split("\n")
        line_length_issues = sum(1 for line in lines if len(line) > 100)
        if line_length_issues > 0:
            issues.append(
                {
                    "type": "line_length",
                    "severity": "low",
                    "message": f"{line_length_issues} lines exceed 100 characters",
                    "suggestion": "Break long lines for better readability",
                }
            )

        # Check naming conventions
        naming_issues = self._check_naming_conventions(code)
        issues.extend(naming_issues)

        # Check imports organization
        import_issues = self._check_imports(code)
        issues.extend(import_issues)

        # Style score
        base_score = 1.0
        penalty = len(issues) * 0.05
        score = max(0.0, base_score - penalty)

        recommendations.extend(
            [
                "Follow PEP 8 style guidelines",
                "Use consistent naming conventions",
                "Organize imports properly (standard, third-party, local)",
            ]
        )

        return {"score": score, "issues": issues, "recommendations": recommendations}

    async def _analyze_general(self, code: str, file_path: str) -> dict[str, Any]:
        """General code analysis"""
        return {
            "score": 0.8,
            "issues": [],
            "recommendations": ["Consider more specialized analysis"],
        }

    def _get_bug_patterns(self) -> dict[str, dict[str, Any]]:
        """Get common bug patterns to check"""
        return {
            "assert_in_production": {
                "pattern": r"\bassert\s+",
                "severity": "medium",
                "message": "Assert statements found - consider removing for production",
                "suggestion": "Replace asserts with proper error handling",
            },
            "print_statements": {
                "pattern": r"\bprint\s*\(",
                "severity": "low",
                "message": "Print statements found - consider using logging",
                "suggestion": "Replace print with appropriate logging calls",
            },
            "bare_except": {
                "pattern": r"except\s*:",
                "severity": "high",
                "message": "Bare except clause found",
                "suggestion": "Specify exception types to catch",
            },
        }

    def _calculate_complexity(self, code: str) -> int:
        """Calculate code complexity (simplified)"""
        complexity = 0
        complexity += code.count("if ")
        complexity += code.count("elif ")
        complexity += code.count("for ")
        complexity += code.count("while ")
        complexity += code.count("try:")
        complexity += code.count("except ")
        return complexity

    def _extract_functions(self, code: str) -> list[dict[str, Any]]:
        """Extract function definitions"""
        functions = []
        lines = code.split("\n")

        for i, line in enumerate(lines):
            if line.strip().startswith("def ") or line.strip().startswith("async def "):
                # Find function end
                func_start = i
                func_end = i
                indent_level = len(line) - len(line.lstrip())

                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == "":
                        continue
                    if len(lines[j]) - len(lines[j].lstrip()) <= indent_level:
                        break
                    func_end = j

                functions.append(
                    {
                        "name": line.split("def ")[1].split("(")[0].strip(),
                        "start_line": func_start + 1,
                        "end_line": func_end + 1,
                        "length": func_end - func_start + 1,
                    }
                )

        return functions

    def _check_duplication(self, code: str) -> int:
        """Simple duplication check"""
        lines = [line.strip() for line in code.split("\n") if line.strip()]
        duplicates = 0

        for i, line1 in enumerate(lines):
            for line2 in lines[i + 1 :]:
                if line1 == line2 and len(line1) > 20:  # Only check substantial lines
                    duplicates += 1

        return duplicates

    def _check_naming_conventions(self, code: str) -> list[dict[str, Any]]:
        """Check naming conventions"""
        issues = []

        # Check for camelCase in Python (should be snake_case)
        camel_case = re.findall(r"\b[a-z]+[A-Z][a-zA-Z]*\b", code)
        if camel_case:
            issues.append(
                {
                    "type": "naming",
                    "severity": "low",
                    "message": f"Found camelCase identifiers: {camel_case[:3]}",
                    "suggestion": "Use snake_case for Python variables and functions",
                }
            )

        return issues

    def _check_imports(self, code: str) -> list[dict[str, Any]]:
        """Check import organization"""
        issues = []
        lines = code.split("\n")

        # Simple check for import organization
        imports_section = False
        other_code_started = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                if other_code_started:
                    issues.append(
                        {
                            "type": "imports",
                            "severity": "low",
                            "message": "Imports found after other code",
                            "suggestion": "Move all imports to the top of the file",
                        }
                    )
                    break
                imports_section = True
            elif stripped and not stripped.startswith("#") and imports_section:
                other_code_started = True

        return issues


class CodeReviewCoordinator:
    """Coordinates multi-agent code review"""

    def __init__(self, config: CodeReviewConfig) -> None:
        self.config = config
        self.agents = self._create_agents()

    def _create_agents(self) -> list[CodeReviewAgent]:
        """Create review agents"""
        return (
            [
                CodeReviewAgent(f"truth_agent_{i}", "correctness", "truth")
                for i in range(self.config.parallel_agents // 3 + 1)
            ]
            + [
                CodeReviewAgent(f"goodness_agent_{i}", "quality", "goodness")
                for i in range(self.config.parallel_agents // 3 + 1)
            ]
            + [
                CodeReviewAgent(f"beauty_agent_{i}", "style", "beauty")
                for i in range(self.config.parallel_agents // 3 + 1)
            ]
        )

    async def review_code(self, code: str, file_path: str) -> CodeReviewResult:
        """Execute multi-agent code review"""
        start_time = time.perf_counter()

        # Parallel review
        parallel_results = await self._execute_parallel_review(code, file_path)

        # Consensus check
        _consensus_result, consensus_ratio = self._check_consensus(parallel_results)

        # Serial verification
        verification_result = await self._execute_serial_verification(code, file_path)

        # Overall assessment
        overall_score = self._calculate_overall_score(parallel_results, consensus_ratio)
        confidence_level = self._calculate_confidence(parallel_results, consensus_ratio)
        is_approved = (
            overall_score >= 0.7 and confidence_level >= self.config.min_confidence_threshold
        )

        # Extract critical issues and recommendations
        critical_issues = self._extract_critical_issues(parallel_results)
        recommendations = self._extract_recommendations(parallel_results)

        execution_time = time.perf_counter() - start_time

        return CodeReviewResult(
            is_approved=is_approved,
            overall_score=overall_score,
            confidence_level=confidence_level,
            execution_time=execution_time,
            agent_results=parallel_results,
            consensus_ratio=consensus_ratio,
            critical_issues=critical_issues,
            recommendations=recommendations,
        )

    async def _execute_parallel_review(self, code: str, file_path: str) -> list[dict[str, Any]]:
        """Execute parallel agent reviews"""
        tasks = []
        for agent in self.agents:
            task = asyncio.create_task(self._safe_agent_review(agent, code, file_path))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        agent_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_results.append(
                    {
                        "agent_id": self.agents[i].agent_id,
                        "success": False,
                        "error": str(result),
                        "execution_time": self.config.timeout_seconds,
                    }
                )
            else:
                agent_results.append(result)

        return agent_results

    async def _safe_agent_review(self, agent: CodeReviewAgent, code: str, file_path: str):
        """Safe agent review with timeout"""
        try:
            return await asyncio.wait_for(
                agent.review_code(code, file_path, self.config),
                timeout=self.config.timeout_seconds,
            )
        except TimeoutError:
            raise RuntimeError(f"Agent {agent.agent_id} timed out")
        except Exception as e:
            raise RuntimeError(f"Agent {agent.agent_id} failed: {e}")

    def _check_consensus(self, agent_results: list[dict[str, Any]]) -> tuple[float, float]:
        """Check consensus among agent results"""
        successful_results = [r for r in agent_results if r["success"]]

        if len(successful_results) < len(agent_results) * 0.5:
            return 0.0, 0.0

        # Extract scores
        scores = [r["result"]["score"] for r in successful_results if "result" in r]

        if not scores:
            return 0.0, 0.0

        # Find consensus score (weighted average)
        avg_score = sum(scores) / len(scores)
        consensus_ratio = sum(1 for score in scores if abs(score - avg_score) < 0.2) / len(scores)

        return avg_score, consensus_ratio

    async def _execute_serial_verification(self, code: str, file_path: str) -> bool:
        """Execute serial verification"""
        # For now, just run a simple syntax check
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def _calculate_overall_score(
        self, agent_results: list[dict[str, Any]], consensus_ratio: float
    ) -> float:
        """Calculate overall review score"""
        successful_results = [r for r in agent_results if r["success"]]
        scores = [r["result"]["score"] for r in successful_results if "result" in r]

        if not scores:
            return 0.0

        avg_score = sum(scores) / len(scores)
        # Weight by consensus
        return avg_score * consensus_ratio

    def _calculate_confidence(
        self, agent_results: list[dict[str, Any]], consensus_ratio: float
    ) -> float:
        """Calculate confidence level"""
        successful_agents = sum(1 for r in agent_results if r["success"])
        success_ratio = successful_agents / len(agent_results)

        return (consensus_ratio + success_ratio) / 2

    def _extract_critical_issues(self, agent_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract critical issues from all agents"""
        critical_issues = []

        for result in agent_results:
            if result["success"] and "result" in result:
                issues = result["result"].get("issues", [])
                critical_issues.extend(
                    [issue for issue in issues if issue.get("severity") in ["critical", "high"]]
                )

        return critical_issues

    def _extract_recommendations(self, agent_results: list[dict[str, Any]]) -> list[str]:
        """Extract recommendations from all agents"""
        all_recommendations = set()

        for result in agent_results:
            if result["success"] and "result" in result:
                recommendations = result["result"].get("recommendations", [])
                all_recommendations.update(recommendations)

        return list(all_recommendations)


class CodeReviewNode(ChancellorNode):
    """Chancellor V2 node for multi-agent code review"""

    def __init__(self, config: CodeReviewConfig | None = None) -> None:
        super().__init__(
            node_id="code_review_node",
            node_type="code_review",
            description="Multi-agent code review for comprehensive quality assurance",
        )
        self.config = config or CodeReviewConfig()
        self.coordinator = CodeReviewCoordinator(self.config)
        self.review_count = 0
        self.approval_count = 0

    async def execute(self, context: ChancellorContext) -> ChancellorContext:
        """Execute code review node"""
        logger.info("Starting multi-agent code review")

        # Extract code review parameters from context
        code = context.get("review_code", "")
        file_path = context.get("review_file_path", "unknown.py")

        if not code:
            context["review_error"] = "No code provided for review"
            return context

        # Execute code review
        review_result = await self.coordinator.review_code(code, file_path)

        self.review_count += 1
        if review_result.is_approved:
            self.approval_count += 1

        # Update context with results
        context.update(
            {
                "review_result": review_result,
                "review_approved": review_result.is_approved,
                "review_score": review_result.overall_score,
                "review_confidence": review_result.confidence_level,
                "review_execution_time": review_result.execution_time,
                "review_consensus_ratio": review_result.consensus_ratio,
                "review_critical_issues": review_result.critical_issues,
                "review_recommendations": review_result.recommendations,
            }
        )

        # Log review results
        await self._log_review_results(review_result, context)

        # Update Trinity score based on code review
        trinity_score = context.get("trinity_score", TrinityScore())
        review_score = self._calculate_review_trinity_score(review_result)
        trinity_score = trinity_score.combine(review_score)
        context["trinity_score"] = trinity_score

        logger.info(f"Code review completed in {review_result.execution_time:.2f} seconds")
        return context

    def _calculate_review_trinity_score(self, result: CodeReviewResult) -> TrinityScore:
        """Calculate Trinity score based on review results"""
        truth_score = result.overall_score
        goodness_score = result.confidence_level
        beauty_score = 1.0 if result.consensus_ratio >= 0.8 else 0.7
        serenity_score = max(0.5, 1.0 - len(result.critical_issues) * 0.1)
        eternity_score = 1.0  # Always logged for audit trail

        return TrinityScore(
            truth=truth_score,
            goodness=goodness_score,
            beauty=beauty_score,
            serenity=serenity_score,
            eternity=eternity_score,
        )

    async def _log_review_results(self, result: CodeReviewResult, context: ChancellorContext):
        """Log review results to artifacts"""
        log_dir = Path("artifacts/code_validation_logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time())
        log_file = log_dir / f"code_review_{timestamp}.json"

        log_data = {
            "timestamp": timestamp,
            "review_id": f"review_{self.review_count}",
            "is_approved": result.is_approved,
            "overall_score": result.overall_score,
            "confidence_level": result.confidence_level,
            "execution_time": result.execution_time,
            "consensus_ratio": result.consensus_ratio,
            "agent_results": result.agent_results,
            "critical_issues": result.critical_issues,
            "recommendations": result.recommendations,
            "context_summary": {
                "file_path": context.get("review_file_path"),
                "node_id": context.get("current_node_id"),
                "trinity_score": str(context.get("trinity_score")),
            },
        }

        with open(log_file, "w") as f:
            json.dump(log_data, f, indent=2, default=str)

        logger.info(f"Code review log saved to {log_file}")


# Global code review node instance
code_review_node = CodeReviewNode()
