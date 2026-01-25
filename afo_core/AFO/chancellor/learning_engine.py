# Trinity Score: 90.0 (Established by Chancellor)
"""
Real-time Learning Engine
Phase 7A: Architecture Evolution - Dynamic Intelligence

Implements continuous learning from user interactions and system feedback.
Uses reinforcement learning patterns to optimize decision-making rules.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from typing import Any, cast

from AFO.cache.manager import cache_manager

logger = logging.getLogger(__name__)


class DecisionPattern:
    """
    Represents a learned decision pattern
    """

    def __init__(self, situation_hash: str, decision_type: str, confidence: float) -> None:
        self.situation_hash = situation_hash
        self.decision_type = decision_type
        self.confidence = confidence
        self.occurrences = 1
        self.success_count = 0
        self.last_used = time.time()
        self.created_at = time.time()

    def update_success(self, success: bool) -> None:
        """Update success metrics"""
        self.occurrences += 1
        if success:
            self.success_count += 1
        self.last_used = time.time()

    def get_success_rate(self) -> float:
        """Calculate success rate"""
        return self.success_count / self.occurrences if self.occurrences > 0 else 0.0

    def get_confidence_score(self) -> float:
        """Calculate overall confidence score"""
        success_rate = self.get_success_rate()
        recency_factor = min(1.0, (time.time() - self.created_at) / 86400)  # 24시간 정규화
        return (success_rate * 0.7) + (self.confidence * 0.2) + (recency_factor * 0.1)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "situation_hash": self.situation_hash,
            "decision_type": self.decision_type,
            "confidence": self.confidence,
            "occurrences": self.occurrences,
            "success_count": self.success_count,
            "success_rate": self.get_success_rate(),
            "last_used": self.last_used,
            "created_at": self.created_at,
        }


class ABTestExperiment:
    """
    A/B Test Experiment for decision optimization
    """

    def __init__(
        self,
        experiment_id: str,
        variants: list[str],
        target_metric: str = "success_rate",
    ):
        self.experiment_id = experiment_id
        self.variants = variants
        self.target_metric = target_metric
        self.variant_stats: dict[str, dict[str, Any]] = {
            variant: {"trials": 0, "successes": 0, target_metric: 0.0} for variant in variants
        }
        self.start_time = time.time()
        self.is_active = True

    def record_trial(self, variant: str, success: bool, metric_value: float = 0.0) -> None:
        """Record a trial result"""
        if variant not in self.variant_stats:
            return

        stats = self.variant_stats[variant]
        stats["trials"] += 1
        stats["successes"] += 1 if success else 0
        stats[self.target_metric] = metric_value

    def get_best_variant(self) -> str | None:
        """Get the best performing variant"""
        if not self.variant_stats:
            return None

        best_variant = None
        best_score = 0.0

        for variant, stats in self.variant_stats.items():
            if stats["trials"] == 0:
                continue

            success_rate = stats["successes"] / stats["trials"]
            score = success_rate * 0.8 + (stats.get(self.target_metric, 0.0) * 0.2)

            if score > best_score:
                best_score = score
                best_variant = variant

        return best_variant

    def should_stop_experiment(self) -> bool:
        """Check if experiment should be stopped (statistical significance)"""
        # Simple check: minimum trials and clear winner
        total_trials = sum(stats["trials"] for stats in self.variant_stats.values())

        if total_trials < 50:  # Need minimum sample size
            return False

        best_variant = self.get_best_variant()
        if not best_variant:
            return False

        best_stats = self.variant_stats[best_variant]
        best_rate = best_stats["successes"] / best_stats["trials"]

        # Check if best variant is significantly better
        for variant, stats in self.variant_stats.items():
            if variant == best_variant:
                continue

            other_rate = stats["successes"] / stats["trials"]
            if abs(best_rate - other_rate) < 0.1:  # Less than 10% difference
                return False

        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize experiment data"""
        return {
            "experiment_id": self.experiment_id,
            "variants": self.variants,
            "target_metric": self.target_metric,
            "variant_stats": self.variant_stats,
            "start_time": self.start_time,
            "is_active": self.is_active,
            "best_variant": self.get_best_variant(),
        }


class LearningEngine:
    """
    Real-time Learning Engine for Chancellor Graphs
    Implements continuous learning and optimization
    """

    def __init__(self) -> None:
        self.decision_patterns: dict[str, DecisionPattern] = {}
        self.active_experiments: dict[str, ABTestExperiment] = {}
        self.learning_cache_key = "chancellor:learning"
        self.feedback_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        # Start background learning task
        self.learning_task = asyncio.create_task(self._continuous_learning())

    async def learn_from_decision(
        self,
        situation: dict[str, Any],
        decision: dict[str, Any],
        outcome: bool | None = None,
    ):
        """
        Learn from a decision outcome
        """
        situation_hash = self._hash_situation(situation)
        decision_type = decision.get("decision_type", "unknown")

        # Update or create decision pattern
        pattern_key = f"{situation_hash}:{decision_type}"
        if pattern_key not in self.decision_patterns:
            confidence = decision.get("confidence", 0.5)
            self.decision_patterns[pattern_key] = DecisionPattern(
                situation_hash, decision_type, confidence
            )
        else:
            success = outcome if outcome is not None else (decision.get("confidence", 0.5) > 0.7)
            self.decision_patterns[pattern_key].update_success(success)

        # Update learning cache
        await self._update_learning_cache()

        logger.debug(f"🧠 Learned from decision: {decision_type} (success: {outcome})")

    async def get_optimized_decision(
        self, situation: dict[str, Any], base_decision: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Get decision optimized by learning data
        """
        situation_hash = self._hash_situation(situation)
        base_decision_type = base_decision.get("decision_type", "unknown")

        # Look for similar situations in learning data
        similar_patterns = self._find_similar_patterns(situation_hash)

        if similar_patterns:
            # Use learning data to adjust confidence
            best_pattern = max(similar_patterns, key=lambda p: p.get_confidence_score())
            optimized_decision = base_decision.copy()

            # Adjust confidence based on learning
            learning_confidence = best_pattern.get_confidence_score()
            base_confidence = base_decision.get("confidence", 0.5)
            optimized_decision["confidence"] = min(1.0, (base_confidence + learning_confidence) / 2)
            optimized_decision["learning_boost"] = learning_confidence > base_confidence
            optimized_decision["pattern_used"] = best_pattern.decision_type

            logger.info(
                f"🎯 Applied learning optimization: {base_decision_type} → {optimized_decision['confidence']:.2f} confidence"
            )
            return optimized_decision

        return base_decision

    async def start_ab_test(
        self,
        experiment_id: str,
        variants: list[str],
        target_metric: str = "success_rate",
    ) -> bool:
        """
        Start an A/B test experiment
        """
        if experiment_id in self.active_experiments:
            logger.warning(f"Experiment {experiment_id} already exists")
            return False

        self.active_experiments[experiment_id] = ABTestExperiment(
            experiment_id, variants, target_metric
        )

        logger.info(f"🧪 Started A/B test: {experiment_id} with variants {variants}")
        return True

    async def record_ab_test_result(
        self, experiment_id: str, variant: str, success: bool, metric_value: float = 0.0
    ):
        """
        Record A/B test trial result
        """
        if experiment_id not in self.active_experiments:
            logger.warning(f"Experiment {experiment_id} not found")
            return

        experiment = self.active_experiments[experiment_id]
        experiment.record_trial(variant, success, metric_value)

        # Check if experiment should be stopped
        if experiment.should_stop_experiment():
            best_variant = experiment.get_best_variant()
            logger.info(f"🎯 A/B test {experiment_id} completed. Winner: {best_variant}")
            experiment.is_active = False

            # Apply winning variant as default
            await self._apply_experiment_results(experiment_id, cast("str", best_variant))

    def get_learning_insights(self) -> dict[str, Any]:
        """
        Get comprehensive learning insights
        """
        total_patterns = len(self.decision_patterns)
        successful_patterns = sum(
            1 for p in self.decision_patterns.values() if p.get_success_rate() > 0.7
        )
        avg_success_rate = (
            sum(p.get_success_rate() for p in self.decision_patterns.values()) / total_patterns
            if total_patterns > 0
            else 0.0
        )

        # Analyze decision type effectiveness
        decision_effectiveness: dict[str, Any] = defaultdict(lambda: {"total": 0, "successful": 0})
        for pattern in self.decision_patterns.values():
            decision_effectiveness[pattern.decision_type]["total"] += 1
            if pattern.get_success_rate() > 0.7:
                decision_effectiveness[pattern.decision_type]["successful"] += 1

        # Calculate effectiveness rates
        effectiveness_rates = {}
        for decision_type, stats in decision_effectiveness.items():
            if stats["total"] > 0:
                effectiveness_rates[decision_type] = stats["successful"] / stats["total"]

        return {
            "total_patterns": total_patterns,
            "successful_patterns": successful_patterns,
            "avg_success_rate": round(avg_success_rate, 3),
            "decision_effectiveness": dict(effectiveness_rates),
            "active_experiments": len([e for e in self.active_experiments.values() if e.is_active]),
            "learning_maturity": self._assess_learning_maturity(),
        }

    def _hash_situation(self, situation: dict[str, Any]) -> str:
        """Create hash for situation comparison"""
        # Normalize and sort keys for consistent hashing
        normalized = json.dumps(situation, sort_keys=True, default=str)
        return str(hash(normalized) % 1000000)  # Keep reasonable size

    def _find_similar_patterns(self, situation_hash: str) -> list[DecisionPattern]:
        """Find similar decision patterns"""
        similar = []
        for pattern in self.decision_patterns.values():
            # Simple similarity: same situation hash
            if pattern.situation_hash == situation_hash:
                similar.append(pattern)

        return similar

    async def _update_learning_cache(self):
        """Update learning data in cache"""
        learning_data = {
            "patterns": {k: v.to_dict() for k, v in self.decision_patterns.items()},
            "experiments": {k: v.to_dict() for k, v in self.active_experiments.items()},
            "last_updated": time.time(),
        }

        cache_key = f"{self.learning_cache_key}:data"
        await cache_manager.set(cache_key, learning_data, ttl=3600)  # 1 hour

    async def _continuous_learning(self):
        """Background continuous learning task"""
        while True:
            try:
                # Process feedback queue
                if not self.feedback_queue.empty():
                    feedback = await self.feedback_queue.get()
                    await self._process_feedback(feedback)

                # Clean up old patterns (keep only recent/active ones)
                await self._cleanup_old_patterns()

                # Check experiment status
                await self._check_experiment_status()

                await asyncio.sleep(60)  # Run every minute

            except Exception as e:
                logger.error(f"Continuous learning error: {e}")
                await asyncio.sleep(60)

    async def _process_feedback(self, feedback: dict[str, Any]):
        """Process feedback for learning"""
        situation = feedback.get("situation")
        decision = feedback.get("decision")
        outcome = feedback.get("outcome")

        if situation and decision:
            await self.learn_from_decision(situation, decision, outcome)

    async def _cleanup_old_patterns(self):
        """Clean up old/unused patterns"""
        current_time = time.time()
        to_remove = []

        for key, pattern in self.decision_patterns.items():
            # Remove patterns older than 30 days with low success rate
            age_days = (current_time - pattern.created_at) / 86400
            if age_days > 30 and pattern.get_success_rate() < 0.5:
                to_remove.append(key)

        for key in to_remove:
            del self.decision_patterns[key]

        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} old learning patterns")

    async def _check_experiment_status(self):
        """Check and update experiment status"""
        completed_experiments = []

        for exp_id, experiment in self.active_experiments.items():
            if not experiment.is_active:
                continue

            if experiment.should_stop_experiment():
                best_variant = experiment.get_best_variant()
                logger.info(f"🎯 A/B test {exp_id} auto-completed. Winner: {best_variant}")
                experiment.is_active = False
                completed_experiments.append((exp_id, best_variant))

        # Apply completed experiments
        for exp_id, winner in completed_experiments:
            await self._apply_experiment_results(exp_id, winner)

    async def _apply_experiment_results(self, experiment_id: str, winning_variant: str):
        """Apply winning experiment results to system defaults"""
        # This would update system configuration based on experiment results
        logger.info(
            f"📈 Applied experiment {experiment_id} results: {winning_variant} is now default"
        )

        # Cache the winning configuration
        config_key = f"{self.learning_cache_key}:experiment:{experiment_id}:winner"
        await cache_manager.set(config_key, winning_variant, ttl=86400 * 30)  # 30 days persistence

    def _assess_learning_maturity(self) -> str:
        """Assess the maturity of the learning engine"""
        total_patterns = len(self.decision_patterns)

        if total_patterns < 10:
            return "nascent"
        elif total_patterns < 50:
            return "developing"
        elif total_patterns < 200:
            return "maturing"
        else:
            return "established"


# Global Learning Engine Instance
learning_engine = LearningEngine()
