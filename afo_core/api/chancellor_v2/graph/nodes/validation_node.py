"""Multi-Agent Calculation Validation Node for Chancellor V2

Implements parallel/serial agent validation system for hallucination-free calculations.
Inspired by human double-checking behavior and scientific verification protocols.

Trinity Score Integration:
- 眞 (Truth): Calculation accuracy validation
- 善 (Goodness): Reliability and error detection
- 美 (Beauty): Clean validation architecture
- 孝 (Serenity): User trust through verification
- 永 (Eternity): Audit trail and reproducibility
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import numpy as np
from numpy.typing import NDArray

from AFO.trinity_metric_wrapper import TrinityScore

# from AFO.chancellor_graph import ChancellorContext, ChancellorNode # REMOVED: Circular/Missing import
# Define alias for ChancellorContext (Dict based context)
ChancellorContext = dict[str, Any]


class ChancellorNode:
    """Base class for Chancellor Nodes."""

    def __init__(self, node_id: str, node_type: str, description: str) -> None:
        self.node_id = node_id
        self.node_type = node_type
        self.description = description


# Local definition removed (SSOT restored)


logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """Configuration for multi-agent validation"""

    parallel_agents: int = 3  # Number of parallel agents
    serial_iterations: int = 2  # Number of serial verification iterations
    timeout_seconds: float = 30.0  # Timeout for each calculation
    tolerance: float = 1e-9  # Numerical tolerance for result comparison
    max_retries: int = 3  # Maximum retry attempts on failure
    consensus_threshold: float = 0.67  # Required consensus ratio


@dataclass
class ValidationResult:
    """Result of multi-agent validation"""

    is_valid: bool
    final_result: Any
    confidence_score: float
    execution_time: float
    agent_results: list[dict[str, Any]]
    consensus_ratio: float
    retry_count: int
    error_details: str | None = None


class CalculationAgent:
    """Individual calculation agent for validation"""

    def __init__(self, agent_id: str, agent_type: str) -> None:
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.calculation_count = 0
        self.error_count = 0

    async def calculate(self, operation: str, *args, **kwargs) -> tuple[Any, float]:
        """Execute calculation with timing"""
        start_time = time.perf_counter()

        try:
            if operation == "matrix_multiply":
                result = await self._matrix_multiply(*args, **kwargs)
            elif operation == "bayesian_update":
                result = await self._bayesian_update(*args, **kwargs)
            else:
                raise ValueError(f"Unsupported operation: {operation}")

            self.calculation_count += 1
            execution_time = time.perf_counter() - start_time
            return result, execution_time

        except Exception as e:
            self.error_count += 1
            execution_time = time.perf_counter() - start_time
            raise RuntimeError(f"Agent {self.agent_id} calculation failed: {e}") from e

    async def _matrix_multiply(
        self, A: NDArray[np.float64], B: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """Matrix multiplication with NumPy BLAS"""
        # Simulate slight variations to test consensus (in real implementation, this would be identical)
        await asyncio.sleep(0.001)  # Simulate computation time
        return np.dot(A, B)

    async def _bayesian_update(
        self, prior: dict[str, float], likelihood: dict[str, float]
    ) -> dict[str, float]:
        """Bayesian probability update"""
        await asyncio.sleep(0.001)
        # Simplified Bayesian update
        posterior = {}
        for key in prior:
            prior_prob = prior[key]
            like_prob = likelihood.get(key, 1.0)
            posterior[key] = prior_prob * like_prob
        # Normalize
        total = sum(posterior.values())
        return {k: v / total for k, v in posterior.items()}


class ValidationCoordinator:
    """Coordinates multi-agent validation"""

    def __init__(self, config: ValidationConfig) -> None:
        self.config = config
        self.agents = self._create_agents()

    def _create_agents(self) -> list[CalculationAgent]:
        """Create validation agents"""
        return [
            CalculationAgent(f"truth_agent_{i}", "truth")
            for i in range(self.config.parallel_agents)
        ]

    async def validate_calculation(self, operation: str, *args, **kwargs) -> ValidationResult:
        """Execute multi-agent validation"""
        start_time = time.perf_counter()
        retry_count = 0

        while retry_count < self.config.max_retries:
            try:
                # Parallel execution
                parallel_results = await self._execute_parallel(operation, *args, **kwargs)

                # Consensus check
                consensus_result, consensus_ratio = self._check_consensus(parallel_results)

                if consensus_result is None:
                    retry_count += 1
                    logger.warning(f"Consensus failed, retry {retry_count}")
                    continue

                # Serial verification
                verification_result = await self._execute_serial_verification(
                    operation, consensus_result, *args, **kwargs
                )

                if not verification_result:
                    retry_count += 1
                    logger.warning(f"Serial verification failed, retry {retry_count}")
                    continue

                # Success
                execution_time = time.perf_counter() - start_time
                confidence_score = self._calculate_confidence_score(
                    parallel_results, consensus_ratio, retry_count
                )

                return ValidationResult(
                    is_valid=True,
                    final_result=consensus_result,
                    confidence_score=confidence_score,
                    execution_time=execution_time,
                    agent_results=parallel_results,
                    consensus_ratio=consensus_ratio,
                    retry_count=retry_count,
                )

            except Exception as e:
                retry_count += 1
                logger.error(f"Validation attempt {retry_count} failed: {e}")

        # All retries exhausted
        execution_time = time.perf_counter() - start_time
        return ValidationResult(
            is_valid=False,
            final_result=None,
            confidence_score=0.0,
            execution_time=execution_time,
            agent_results=[],
            consensus_ratio=0.0,
            retry_count=retry_count,
            error_details=f"Validation failed after {retry_count} retries",
        )

    async def _execute_parallel(self, operation: str, *args, **kwargs) -> list[dict[str, Any]]:
        """Execute parallel agent calculations"""
        tasks = []
        for agent in self.agents:
            task = asyncio.create_task(
                self._safe_agent_calculation(agent, operation, *args, **kwargs)
            )
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
                result_data, exec_time = result
                agent_results.append(
                    {
                        "agent_id": self.agents[i].agent_id,
                        "success": True,
                        "result": result_data,
                        "execution_time": exec_time,
                    }
                )

        return agent_results

    async def _safe_agent_calculation(
        self, agent: CalculationAgent, operation: str, *args, **kwargs
    ):
        """Safe agent calculation with timeout"""
        try:
            return await asyncio.wait_for(
                agent.calculate(operation, *args, **kwargs),
                timeout=self.config.timeout_seconds,
            )
        except TimeoutError:
            raise RuntimeError(f"Agent {agent.agent_id} timed out")
        except Exception as e:
            raise RuntimeError(f"Agent {agent.agent_id} failed: {e}")

    def _check_consensus(self, agent_results: list[dict[str, Any]]) -> tuple[Any, float]:
        """Check consensus among agent results"""
        successful_results = [r for r in agent_results if r["success"]]

        if len(successful_results) < self.config.parallel_agents * self.config.consensus_threshold:
            return None, 0.0

        # Extract results
        results = [r["result"] for r in successful_results]

        # For numpy arrays, use allclose comparison
        if isinstance(results[0], np.ndarray):
            # Find consensus result
            consensus_result = results[0]  # Use first as reference
            consensus_count = 1

            for result in results[1:]:
                if np.allclose(result, consensus_result, rtol=0, atol=self.config.tolerance):
                    consensus_count += 1
                else:
                    # Try this result as new consensus
                    new_consensus_count = sum(
                        1
                        for r in results
                        if np.allclose(r, result, rtol=0, atol=self.config.tolerance)
                    )
                    if new_consensus_count > consensus_count:
                        consensus_result = result
                        consensus_count = new_consensus_count

            consensus_ratio = consensus_count / len(results)
            if consensus_ratio >= self.config.consensus_threshold:
                return consensus_result, consensus_ratio

        else:
            # For other types, use exact equality
            result_counts = {}
            for result in results:
                key = str(result)  # Simple string representation
                result_counts[key] = result_counts.get(key, 0) + 1

            max_count = max(result_counts.values())
            consensus_ratio = max_count / len(results)

            if consensus_ratio >= self.config.consensus_threshold:
                # Find the consensus result
                for result in results:
                    if str(result) == max(result_counts.keys(), key=result_counts.get):
                        return result, consensus_ratio

        return None, 0.0

    async def _execute_serial_verification(
        self, operation: str, consensus_result: Any, *args, **kwargs
    ) -> bool:
        """Execute serial verification iterations"""
        reference_agent = self.agents[0]  # Use first agent for verification

        for iteration in range(self.config.serial_iterations):
            try:
                verification_result, _ = await asyncio.wait_for(
                    reference_agent.calculate(operation, *args, **kwargs),
                    timeout=self.config.timeout_seconds,
                )

                # Compare with consensus
                if isinstance(consensus_result, np.ndarray):
                    if not np.allclose(
                        verification_result,
                        consensus_result,
                        rtol=0,
                        atol=self.config.tolerance,
                    ):
                        logger.warning(f"Serial verification iteration {iteration + 1} failed")
                        return False
                else:
                    if verification_result != consensus_result:
                        logger.warning(f"Serial verification iteration {iteration + 1} failed")
                        return False

            except Exception as e:
                logger.warning(f"Serial verification iteration {iteration + 1} error: {e}")
                return False

        return True

    def _calculate_confidence_score(
        self,
        agent_results: list[dict[str, Any]],
        consensus_ratio: float,
        retry_count: int,
    ) -> float:
        """Calculate confidence score for validation result"""
        successful_agents = sum(1 for r in agent_results if r["success"])
        success_ratio = successful_agents / len(agent_results)

        # Base confidence from consensus and success
        base_confidence = (consensus_ratio + success_ratio) / 2

        # Penalty for retries
        retry_penalty = retry_count * 0.1
        confidence = max(0.0, base_confidence - retry_penalty)

        return confidence


class ValidationNode(ChancellorNode):
    """Chancellor V2 node for multi-agent calculation validation"""

    def __init__(self, config: ValidationConfig | None = None) -> None:
        super().__init__(
            node_id="validation_node",
            node_type="validation",
            description="Multi-agent calculation validation for hallucination-free results",
        )
        self.config = config or ValidationConfig()
        self.coordinator = ValidationCoordinator(self.config)
        self.validation_count = 0
        self.success_count = 0

    async def execute(self, context: ChancellorContext) -> ChancellorContext:
        """Execute validation node"""
        logger.info("Starting multi-agent calculation validation")

        # Extract calculation parameters from context
        operation = context.get("validation_operation", "matrix_multiply")
        args = context.get("validation_args", [])
        kwargs = context.get("validation_kwargs", {})

        # Execute validation
        validation_result = await self.coordinator.validate_calculation(operation, *args, **kwargs)

        self.validation_count += 1
        if validation_result.is_valid:
            self.success_count += 1

        # Update context with results
        context.update(
            {
                "validation_result": validation_result,
                "validation_success": validation_result.is_valid,
                "validation_confidence": validation_result.confidence_score,
                "validation_execution_time": validation_result.execution_time,
                "validation_consensus_ratio": validation_result.consensus_ratio,
                "validation_retry_count": validation_result.retry_count,
            }
        )

        # Log validation results
        await self._log_validation_results(validation_result, context)

        # Update Trinity score based on validation
        trinity_score = context.get("trinity_score", TrinityScore())
        validation_score = self._calculate_validation_trinity_score(validation_result)
        trinity_score = trinity_score.combine(validation_score)
        context["trinity_score"] = trinity_score

        logger.info(f"Validation completed. Score: {validation_score}")
        return context

    def _calculate_validation_trinity_score(self, result: ValidationResult) -> TrinityScore:
        """Calculate Trinity score based on validation results"""
        truth_score = 1.0 if result.is_valid else 0.5
        goodness_score = result.confidence_score
        beauty_score = 1.0 if result.consensus_ratio >= 0.8 else 0.7
        serenity_score = max(0.5, 1.0 - (result.retry_count * 0.1))
        eternity_score = 1.0  # Always logged for audit trail

        return TrinityScore(
            truth=truth_score,
            goodness=goodness_score,
            beauty=beauty_score,
            serenity=serenity_score,
            eternity=eternity_score,
        )

    async def _log_validation_results(self, result: ValidationResult, context: ChancellorContext):
        """Log validation results to artifacts"""
        log_dir = Path("artifacts/multi_agent_validation_logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time())
        log_file = log_dir / f"validation_{timestamp}.json"

        log_data = {
            "timestamp": timestamp,
            "validation_id": f"validation_{self.validation_count}",
            "is_valid": result.is_valid,
            "confidence_score": result.confidence_score,
            "execution_time": result.execution_time,
            "consensus_ratio": result.consensus_ratio,
            "retry_count": result.retry_count,
            "agent_results": result.agent_results,
            "error_details": result.error_details,
            "context_summary": {
                "operation": context.get("validation_operation"),
                "node_id": context.get("current_node_id"),
                "trinity_score": str(context.get("trinity_score")),
            },
        }

        with open(log_file, "w") as f:
            json.dump(log_data, f, indent=2, default=str)

        logger.info(f"Validation log saved to {log_file}")


# Global validation node instance
validation_node = ValidationNode()
