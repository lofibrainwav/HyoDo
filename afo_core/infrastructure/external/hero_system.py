from typing import Any

from domain.family.models import Quest, QuestStatus


class HeroSystemAdapter:
    """
    Adapter for Jayden's External Hero System.
    Currently mocks the interaction with the Gamification DB.
    """

    def __init__(self, api_key: str = "mock_key") -> None:
        self.api_key = api_key
        # Mock In-Memory Store
        self._quests: dict[str, Quest] = {}
        self._hero_stats = {"level": 5, "xp": 1250, "xp_next": 2000, "gold": 500}

    async def sync_quest(self, quest: Quest) -> bool:
        """
        Push local Quest to Hero System.
        In reality, this would make a POST request to the Hero API.
        """
        print(f"🦸 [HeroSystem] Syncing Quest: {quest.title} ({quest.reward.xp} XP)")
        self._quests[quest.id] = quest
        quest.status = QuestStatus.ACTIVE
        return True

    async def get_hero_status(self, user_id: str) -> dict[str, Any]:
        """Fetch current XP/Level/Active Quests."""
        active_quests = [q for q in self._quests.values() if q.status == QuestStatus.ACTIVE]

        return {"stats": self._hero_stats, "active_quests": active_quests}

    async def complete_quest(self, quest_id: str) -> bool:
        """Mark quest as complete in Hero System and grant rewards."""
        if quest_id not in self._quests:
            return False

        quest = self._quests[quest_id]
        quest.status = QuestStatus.COMPLETED

        # Grant Rewards ( Mock )
        self._hero_stats["xp"] += quest.reward.xp
        self._hero_stats["gold"] += quest.reward.gold

        print(f"🦸 [HeroSystem] Quest Completed! Granted {quest.reward.xp} XP.")
        return True


# Singleton Instance
hero_adapter = HeroSystemAdapter()
