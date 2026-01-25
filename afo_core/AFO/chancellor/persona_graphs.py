# Trinity Score: 90.0 (Established by Chancellor)
"""
Persona-based Chancellor Graphs
Phase 7A: Architecture Evolution - Multi-Persona Intelligence

Implements separate Chancellor Graphs for different personas,
each with specialized decision-making capabilities.
"""

import asyncio
import logging
from typing import Any

from AFO.cache.manager import cache_manager


# Node configuration class for Phase 7A
class NodeConfig:
    """Configuration object for graph nodes"""

    focus_areas: list[str] | None
    analysis_depth: str | None
    decision_style: str | None

    def __init__(self, **kwargs) -> None:
        # Initialize with defaults
        self.focus_areas = None
        self.analysis_depth = None
        self.decision_style = None

        # Override with provided values
        for key, value in kwargs.items():
            setattr(self, key, value)


# Base ChancellorGraph class for Phase 7A
class ChancellorGraph:
    """
    Base Chancellor Graph class for persona inheritance
    """

    def __init__(self) -> None:
        self.nodes = {
            "observe": NodeConfig(focus_areas=[]),
            "analyze": NodeConfig(analysis_depth="standard"),
            "deliberate": NodeConfig(decision_style="balanced"),
        }

    async def make_decision(self, situation: dict[str, Any]) -> dict[str, Any]:
        """
        Base decision making logic - to be overridden by subclasses
        """
        return {
            "decision_type": "pending",
            "confidence": 0.5,
            "reasoning": "Base ChancellorGraph decision",
            "persona": "base",
        }


logger = logging.getLogger(__name__)


class PersonaChancellorGraph(ChancellorGraph):
    """
    Persona-specific Chancellor Graph
    Inherits base functionality with persona-specific optimizations
    """

    def __init__(self, persona_name: str, persona_config: dict[str, Any]) -> None:
        super().__init__()
        self.persona_name = persona_name
        self.persona_config = persona_config
        self.persona_cache_key = f"persona:{persona_name.lower()}"
        self.decision_history: list[dict[str, Any]] = []

        # Persona-specific node customizations
        self._customize_nodes_for_persona()

    def _customize_nodes_for_persona(self) -> None:
        """Customize graph nodes based on persona characteristics"""
        persona_type = self.persona_config.get("type", "general")

        if persona_type == "commander":
            # 형님 페르소나: 더 보수적이고 전략적
            self.nodes["observe"].focus_areas = ["strategy", "risk", "long_term"]
            self.nodes["analyze"].analysis_depth = "deep"
            self.nodes["deliberate"].decision_style = "conservative"

        elif persona_type == "developer":
            # 개발자 페르소나: 기술적 세부사항에 집중
            self.nodes["observe"].focus_areas = ["code", "architecture", "performance"]
            self.nodes["analyze"].analysis_depth = "technical"
            self.nodes["deliberate"].decision_style = "pragmatic"

        elif persona_type == "analyst":
            # 분석가 페르소나: 데이터와 메트릭스 중심
            self.nodes["observe"].focus_areas = ["metrics", "data", "trends"]
            self.nodes["analyze"].analysis_depth = "quantitative"
            self.nodes["deliberate"].decision_style = "data_driven"

        elif persona_type == "growth":
            # 성장/교육 페르소나 (Jayden): 지지적이고 정성적인 루틴
            self.nodes["observe"].focus_areas = ["habits", "emotions", "learning"]
            self.nodes["analyze"].analysis_depth = "qualitative"
            self.nodes["deliberate"].decision_style = "supportive"

    async def make_decision(self, situation: dict[str, Any]) -> dict[str, Any]:
        """
        Make persona-specific decision with caching and learning
        """
        # Check persona-specific cache first
        cache_key = f"{self.persona_cache_key}:decision:{hash(str(situation))}"
        cached_decision: dict[str, Any] | None = await cache_manager.get(cache_key)

        if cached_decision:
            logger.info(f"💾 {self.persona_name} Persona Cache Hit")
            return cached_decision

        # Make decision using base graph logic
        decision = await super().make_decision(situation)

        # Add persona-specific enhancements
        decision["persona"] = self.persona_name
        decision["persona_confidence"] = self._calculate_persona_confidence(decision, situation)

        # Cache the enhanced decision
        await cache_manager.set(cache_key, decision, ttl=1800)  # 30분 TTL

        # Record for learning
        self.decision_history.append(
            {
                "situation": situation,
                "decision": decision,
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

        # Keep history manageable
        if len(self.decision_history) > 100:
            self.decision_history.pop(0)

        return decision

    def _calculate_persona_confidence(
        self, decision: dict[str, Any], situation: dict[str, Any]
    ) -> float:
        """
        Calculate persona-specific confidence score
        """
        base_confidence: float = decision.get("confidence", 0.5)
        persona_expertise: list[str] = self.persona_config.get("expertise_areas", [])

        # Boost confidence if situation matches persona expertise
        situation_tags = situation.get("tags", [])
        expertise_match = len(set(persona_expertise) & set(situation_tags))

        if expertise_match > 0:
            confidence_boost = min(0.2, expertise_match * 0.1)
            base_confidence = min(1.0, base_confidence + confidence_boost)

        return base_confidence

    def get_persona_insights(self) -> dict[str, Any]:
        """
        Get persona-specific insights from decision history
        """
        if not self.decision_history:
            return {"insights": "No decision history available"}

        # Analyze decision patterns
        total_decisions = len(self.decision_history)
        avg_confidence = (
            sum(d["decision"]["persona_confidence"] for d in self.decision_history)
            / total_decisions
        )

        decision_types: dict[str, int] = {}
        for record in self.decision_history:
            decision_type = record["decision"].get("decision_type", "unknown")
            decision_types[decision_type] = decision_types.get(decision_type, 0) + 1

        return {
            "persona_name": self.persona_name,
            "total_decisions": total_decisions,
            "avg_confidence": round(avg_confidence, 3),
            "decision_distribution": decision_types,
            "learning_insights": self._extract_learning_insights(),
        }

    def _extract_learning_insights(self) -> list[str]:
        """
        Extract learning insights from decision history
        """
        insights = []

        if len(self.decision_history) < 10:
            return ["Insufficient data for learning insights"]

        # Analyze confidence trends
        recent_confidence = [
            d["decision"]["persona_confidence"] for d in self.decision_history[-10:]
        ]
        older_confidence = (
            [d["decision"]["persona_confidence"] for d in self.decision_history[-20:-10]]
            if len(self.decision_history) >= 20
            else []
        )

        if older_confidence and sum(recent_confidence) / len(recent_confidence) > sum(
            older_confidence
        ) / len(older_confidence):
            insights.append("Confidence increasing - learning effectively")

        # Analyze decision consistency
        recent_decisions = [d["decision"]["decision_type"] for d in self.decision_history[-10:]]
        if len(set(recent_decisions)) <= 2:
            insights.append("Developing decision consistency")

        return insights or ["Learning in progress"]


class MultiPersonaChancellor:
    """
    Multi-Persona Chancellor System
    Manages multiple persona-specific graphs
    """

    def __init__(self) -> None:
        self.persona_graphs: dict[str, PersonaChancellorGraph] = {}
        self._initialize_personas()

    def _initialize_personas(self) -> None:
        """Initialize default personas"""

        default_personas = {
            "commander": {
                "type": "commander",
                "description": "Strategic commander focused on high-level decisions and risk management",
                "expertise_areas": ["strategy", "risk", "leadership", "long_term"],
                "decision_style": "conservative",
                "risk_tolerance": "low",
            },
            "developer": {
                "type": "developer",
                "description": "Technical expert focused on implementation and code quality",
                "expertise_areas": ["code", "architecture", "performance", "debugging"],
                "decision_style": "pragmatic",
                "risk_tolerance": "medium",
            },
            "analyst": {
                "type": "analyst",
                "description": "Data-driven analyst focused on metrics and optimization",
                "expertise_areas": ["metrics", "data", "analysis", "optimization"],
                "decision_style": "data_driven",
                "risk_tolerance": "medium",
            },
            "julie": {
                "type": "analyst",
                "description": "Julie (CPA/Risk): Expert in document accuracy, financial logic, and strategic risk assessment",
                "expertise_areas": [
                    "risk",
                    "compliance",
                    "finance",
                    "audit",
                    "accuracy",
                ],
                "decision_style": "precise",
                "risk_tolerance": "low",
            },
            "jayden": {
                "type": "growth",
                "description": "Jayden (Growth/Routine): Focused on education, habit formation, and emotional stability",
                "expertise_areas": [
                    "education",
                    "habits",
                    "psychology",
                    "learning",
                    "routine",
                ],
                "decision_style": "supportive",
                "risk_tolerance": "medium",
            },
        }

        for persona_name, config in default_personas.items():
            self.persona_graphs[persona_name] = PersonaChancellorGraph(persona_name, config)

    def add_persona(self, persona_name: str, persona_config: dict[str, Any]) -> None:
        """Add a new persona graph"""
        if persona_name in self.persona_graphs:
            logger.warning(f"Persona {persona_name} already exists, updating...")
        self.persona_graphs[persona_name] = PersonaChancellorGraph(persona_name, persona_config)
        logger.info(f"✅ Added persona: {persona_name}")

    def remove_persona(self, persona_name: str) -> None:
        """Remove a persona graph"""
        if persona_name in self.persona_graphs:
            del self.persona_graphs[persona_name]
            logger.info(f"✅ Removed persona: {persona_name}")
        else:
            logger.warning(f"Persona {persona_name} not found")

    async def make_decision(
        self, situation: dict[str, Any], preferred_persona: str | None = None
    ) -> dict[str, Any]:
        """
        Make decision using appropriate persona
        """
        if preferred_persona and preferred_persona in self.persona_graphs:
            persona_graph = self.persona_graphs[preferred_persona]
        else:
            # Auto-select persona based on situation
            persona_graph = self._select_persona_for_situation(situation)

        logger.info(f"🎭 Using persona: {persona_graph.persona_name}")
        return await persona_graph.make_decision(situation)

    def _select_persona_for_situation(self, situation: dict[str, Any]) -> PersonaChancellorGraph:
        """
        Auto-select most appropriate persona for the situation
        """
        situation_tags = situation.get("tags", [])
        best_persona = None
        best_score = 0

        for _persona_name, persona_graph in self.persona_graphs.items():
            expertise_areas = persona_graph.persona_config.get("expertise_areas", [])
            match_score = len(set(expertise_areas) & set(situation_tags))

            if match_score > best_score:
                best_score = match_score
                best_persona = persona_graph

        return best_persona or self.persona_graphs["commander"]  # Default fallback

    async def get_consensus_decision(self, situation: dict[str, Any]) -> dict[str, Any]:
        """
        Get consensus decision from all personas
        """
        decisions = []
        for persona_name, persona_graph in self.persona_graphs.items():
            decision = await persona_graph.make_decision(situation)
            decision["persona"] = persona_name
            decisions.append(decision)

        # Simple consensus logic: majority vote with confidence weighting
        decision_types = {}
        for decision in decisions:
            decision_type = decision.get("decision_type", "unknown")
            confidence = decision.get("confidence", 0.5)
            if decision_type not in decision_types:
                decision_types[decision_type] = {"count": 0, "total_confidence": 0}
            decision_types[decision_type]["count"] += 1
            decision_types[decision_type]["total_confidence"] += confidence

        # Find decision with highest weighted score
        best_decision_type = max(
            decision_types.keys(),
            key=lambda x: decision_types[x]["count"] * decision_types[x]["total_confidence"],
        )

        return {
            "consensus_decision": best_decision_type,
            "individual_decisions": decisions,
            "agreement_level": decision_types[best_decision_type]["count"] / len(decisions),
            "avg_confidence": sum(d.get("confidence", 0.5) for d in decisions) / len(decisions),
        }

    def get_system_insights(self) -> dict[str, Any]:
        """
        Get insights from all persona graphs
        """
        persona_insights = {}
        for persona_name, persona_graph in self.persona_graphs.items():
            persona_insights[persona_name] = persona_graph.get_persona_insights()

        return {
            "total_personas": len(self.persona_graphs),
            "persona_insights": persona_insights,
            "system_health": self._assess_system_health(persona_insights),
        }

    def _assess_system_health(self, persona_insights: dict[str, Any]) -> str:
        """
        Assess overall system health based on persona insights
        """
        total_personas = len(persona_insights)
        healthy_personas = 0

        for insights in persona_insights.values():
            avg_confidence = insights.get("avg_confidence", 0)
            total_decisions = insights.get("total_decisions", 0)

            if avg_confidence > 0.7 and total_decisions > 10:
                healthy_personas += 1

        health_ratio = healthy_personas / total_personas

        if health_ratio >= 0.8:
            return "excellent"
        elif health_ratio >= 0.6:
            return "good"
        elif health_ratio >= 0.4:
            return "fair"
        else:
            return "needs_attention"


# Global multi-persona chancellor instance
multi_persona_chancellor = MultiPersonaChancellor()
