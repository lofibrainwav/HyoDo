#!/usr/bin/env python3
"""
Optimize Node for Chancellor Graph V2
Implements DSPy MIPROv2 prompt optimization within the decision graph
"""

import asyncio
from typing import Any

from pydantic import BaseModel

from AFO.chancellor_graph import ChancellorContext, ChancellorNode
from AFO.trinity_metric_wrapper import TrinityMetricWrapper

# Try to import DSPy components
try:
    import dspy
    from dspy.teleprompt import MIPROv2

    from AFO.api.routes.dspy import MIPROv2Optimizer

    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    MIPROv2Optimizer = None


class OptimizeNodeConfig(BaseModel):
    """Configuration for Optimize Node"""

    task_description: str
    num_candidates: int = 10
    max_bootstrapped_demos: int = 4
    num_trials: int = 20
    use_context7: bool = True
    use_skills: bool = True
    min_trinity_score: float = 0.8
    timeout_seconds: int = 300


class OptimizeNode(ChancellorNode):
    """
    Optimize Node: Executes DSPy MIPROv2 prompt optimization

    This node integrates DSPy MIPROv2 for automatic prompt optimization
    within the Chancellor decision graph, using Trinity Score for evaluation.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.config = OptimizeNodeConfig(**config)
        self.trinity_metric = TrinityMetricWrapper()

        if DSPY_AVAILABLE and MIPROv2Optimizer:
            self.optimizer = MIPROv2Optimizer()
        else:
            self.optimizer = None

        self.node_type = "optimize"
        self.description = "DSPy MIPROv2 prompt optimization with Trinity Score evaluation"

    async def execute(self, context: ChancellorContext) -> dict[str, Any]:
        """
        Execute DSPy MIPROv2 optimization

        Args:
            context: Chancellor execution context

        Returns:
            Dict containing optimization results
        """
        try:
            # Check DSPy availability
            if not DSPY_AVAILABLE or self.optimizer is None:
                return {
                    "success": False,
                    "error": "DSPy MIPROv2 not available",
                    "node_type": self.node_type,
                    "trinity_score": {
                        "truth": 0.0,
                        "goodness": 0.0,
                        "beauty": 0.0,
                        "serenity": 0.0,
                        "eternity": 0.0,
                    },
                }

            # Prepare optimization data from context
            task_data = await self._prepare_task_data(context)

            if not task_data["dataset"]:
                return {
                    "success": False,
                    "error": "Insufficient data for optimization",
                    "node_type": self.node_type,
                    "trinity_score": self.trinity_metric.calculate_trinity_score(
                        {
                            "error": "insufficient_data",
                            "context_size": len(context.graph_state.get("data", [])),
                        }
                    ),
                }

            # Execute optimization with timeout
            try:
                result = await asyncio.wait_for(
                    self._run_optimization(task_data),
                    timeout=self.config.timeout_seconds,
                )
            except TimeoutError:
                return {
                    "success": False,
                    "error": f"Optimization timeout after {self.config.timeout_seconds}s",
                    "node_type": self.node_type,
                    "trinity_score": self.trinity_metric.calculate_trinity_score(
                        {
                            "error": "timeout",
                            "timeout_seconds": self.config.timeout_seconds,
                        }
                    ),
                }

            # Validate results against Trinity Score threshold
            trinity_scores = result.get("trinity_score", {})
            best_score = max(trinity_scores.values()) if trinity_scores else 0.0

            if best_score < self.config.min_trinity_score:
                return {
                    "success": False,
                    "error": f"Optimization result below Trinity threshold: {best_score:.3f} < {self.config.min_trinity_score}",
                    "node_type": self.node_type,
                    "optimization_result": result,
                    "trinity_score": trinity_scores,
                }

            # Success
            return {
                "success": True,
                "node_type": self.node_type,
                "optimization_result": result,
                "trinity_score": trinity_scores,
                "best_score": best_score,
                "execution_time": result.get("execution_time", 0),
                "trials_completed": result.get("trials_completed", 0),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Optimize node execution failed: {e!s}",
                "node_type": self.node_type,
                "trinity_score": self.trinity_metric.calculate_trinity_score(
                    {"error": str(e), "node_type": self.node_type}
                ),
            }

    async def _prepare_task_data(self, context: ChancellorContext) -> dict[str, Any]:
        """Prepare task data from Chancellor context"""
        # Extract task description
        task_description = self.config.task_description

        # Build dataset from context data
        dataset = []
        context_data = context.graph_state.get("data", [])
        context_examples = context.graph_state.get("examples", [])

        # Add context examples
        for example in context_examples:
            if isinstance(example, dict):
                dataset.append(example)

        # Add context data as examples
        for item in context_data:
            if isinstance(item, dict):
                # Convert various data formats to question-answer pairs
                if "question" in item and "answer" in item:
                    dataset.append(item)
                elif "input" in item and "output" in item:
                    dataset.append({"question": item["input"], "answer": item["output"]})
                elif "text" in item:
                    # Split text into Q&A pairs if possible
                    text = item["text"]
                    if "?" in text:
                        parts = text.split("?", 1)
                        if len(parts) == 2:
                            dataset.append({"question": parts[0] + "?", "answer": parts[1].strip()})
                    else:
                        # Use text as both question and answer
                        dataset.append(
                            {
                                "question": (text[:100] + "..." if len(text) > 100 else text),
                                "answer": text,
                            }
                        )

        # Enhance with Context7 if enabled
        if self.config.use_context7:
            try:
                context7_data = await self._get_context7_data(context)
                dataset.extend(context7_data)
            except Exception as e:
                print(f"Context7 integration failed: {e}")

        return {
            "task": task_description,
            "dataset": dataset[:100],  # Limit dataset size
        }

    async def _get_context7_data(self, context: ChancellorContext) -> list[dict[str, str]]:
        """Get relevant data from Context7"""
        try:
            from AFO.context7 import Context7Manager

            context7 = Context7Manager()

            # Get context relevant to the task
            relevant_data = await context7.get_relevant_context(
                self.config.task_description, limit=20
            )

            # Convert to dataset format
            dataset_items = []
            for item in relevant_data:
                content = item.get("content", "")
                if content:
                    dataset_items.append(
                        {
                            "question": f"Context information: {content[:100]}...",
                            "answer": content,
                        }
                    )

            return dataset_items

        except Exception as e:
            print(f"Context7 data retrieval failed: {e}")
            return []

    async def _run_optimization(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """Run MIPROv2 optimization"""

        # Create mock request object for the optimizer
        class MockRequest:
            def __init__(self, task: str, dataset: list, config) -> None:
                self.task = task
                self.dataset = dataset
                self.num_candidates = config.num_candidates
                self.max_bootstrapped_demos = config.max_bootstrapped_demos
                self.num_trials = config.num_trials
                self.use_context7 = config.use_context7
                self.use_skills = config.use_skills

        mock_request = MockRequest(task_data["task"], task_data["dataset"], self.config)

        # Execute optimization (simulate the API call)
        return await self._simulate_optimization(mock_request)

    async def _simulate_optimization(self, request) -> dict[str, Any]:
        """Simulate MIPROv2 optimization for Chancellor integration"""
        try:
            # Create task module
            task_module = self.optimizer.create_task_module(request.task)

            # Prepare dataset (without Context7 enhancement since we already did it)
            trainset = self.optimizer.prepare_dataset(request.dataset)

            if len(trainset) < 3:  # Minimum requirement for optimization
                raise ValueError("Insufficient training data for optimization")

            # Configure optimization
            config = {
                "num_candidates": request.num_candidates,
                "max_bootstrapped_demos": request.max_bootstrapped_demos,
                "num_trials": min(request.num_trials, 10),  # Limit for node execution
            }

            # Execute optimization
            result = self.optimizer.optimize_with_mipro(task_module, trainset, config)

            # Calculate Trinity Score for the result
            trinity_scores = self.trinity_metric.calculate_trinity_score(
                {
                    "task": request.task,
                    "dataset_size": len(request.dataset),
                    "optimization_result": result,
                }
            )

            return {
                "optimized_prompt": result.get("optimized_module", {}),
                "trinity_score": trinity_scores,
                "execution_time": result.get("execution_time", 0),
                "trials_completed": result.get("trials_completed", 0),
                "teleprompter_config": result.get("teleprompter_config", {}),
            }

        except Exception as e:
            raise Exception(f"MIPROv2 optimization failed: {e!s}")

    def get_node_info(self) -> dict[str, Any]:
        """Get node information for Chancellor Graph"""
        return {
            "type": self.node_type,
            "description": self.description,
            "config": self.config.model_dump(),
            "capabilities": [
                "dspy_mipro_optimization",
                "trinity_score_evaluation",
                "context7_integration",
                "bayesian_prompt_tuning",
            ],
            "inputs": ["task_description", "dataset", "optimization_config"],
            "outputs": ["optimized_prompt", "trinity_score", "performance_metrics"],
        }


# Factory function for Chancellor Graph integration
def create_optimize_node(config: dict[str, Any]) -> OptimizeNode:
    """Create Optimize Node instance"""
    return OptimizeNode(config)


# Export for Chancellor Graph
__all__ = ["OptimizeNode", "OptimizeNodeConfig", "create_optimize_node"]
