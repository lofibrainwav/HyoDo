import json
import logging
import time
from typing import Any, Dict

import redis

logger = logging.getLogger(__name__)

REDIS_AGENTS_KEY = "afo:agents:registry"


class AgentRegistryService:
    """에이전트 레지스트리 서비스 (Redis)"""

    def __init__(self) -> None:
        self._registered_agents: dict[str, dict[str, Any]] = self._load_agents_from_redis()

    def _get_redis_client(self) -> None:
        """Redis 클라이언트 가져오기"""
        try:
            host = "localhost"
            port = 6379
            return redis.Redis(host=host, port=port, decode_responses=True)
        except Exception:
            return None

    def _load_agents_from_redis(self) -> dict[str, dict[str, Any]]:
        """Redis에서 에이전트 목록 로드"""
        try:
            client = self._get_redis_client()
            if client:
                data = client.get(REDIS_AGENTS_KEY)
                if data:
                    return json.loads(data)
        except Exception as e:
            logger.warning(f"[AgentSync] Redis load failed: {e}")
        return {}

    def _save_agents_to_redis(self, agents: dict[str, dict[str, Any]]) -> bool:
        """Redis에 에이전트 목록 저장"""
        try:
            client = self._get_redis_client()
            if client:
                client.set(REDIS_AGENTS_KEY, json.dumps(agents))
                return True
        except Exception as e:
            logger.warning(f"[AgentSync] Redis save failed: {e}")
        return False

    def register_agent(
        self, agent_id: str, agent_type: str, capabilities: list[str], version: str
    ) -> bool:
        """에이전트 등록"""
        agent_info = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "capabilities": capabilities,
            "version": version,
            "registered_at": time.time(),
            "last_active": time.time(),
            "knowledge_count": 0,
        }

        self._registered_agents[agent_id] = agent_info
        self._save_agents_to_redis(self._registered_agents)
        logger.info(f"[AgentSync] Registered agent: {agent_id} ({agent_type})")
        return True

    def get_all_agents(self) -> list[dict[str, Any]]:
        """모든 에이전트 반환"""
        if not self._registered_agents:
            self._registered_agents = self._load_agents_from_redis()
        return list(self._registered_agents.values())

    def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        """에이전트 조회"""
        return self._registered_agents.get(agent_id)

    def update_agent_activity(self, agent_id: str) -> None:
        """에이전트 활동 시간 업데이트"""
        if agent_id in self._registered_agents:
            self._registered_agents[agent_id]["last_active"] = time.time()
            # Redis에는 성능을 위해 가끔 저장하거나, 여기서는 일단 메모리만 업데이트하고
            # 주기적으로 저장하는 로직이 필요할 수 있지만, 일단은 매번 저장하지 않음 (메모리 우선)

    def increment_knowledge_count(self, agent_id: str) -> None:
        """지식 카운트 증가"""
        if agent_id in self._registered_agents:
            self._registered_agents[agent_id]["knowledge_count"] += 1
            self._registered_agents[agent_id]["last_active"] = time.time()
            self._save_agents_to_redis(self._registered_agents)


# Global Instance
agent_registry = AgentRegistryService()
