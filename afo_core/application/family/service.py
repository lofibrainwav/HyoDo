from datetime import datetime
from typing import Any

from domain.family.models import Quest, QuestReward, QuestStatus
from infrastructure.external.hero_system import hero_adapter


class FamilyService:
    """
    Orchestrates Family Hub Logic (L3).
    Bridges Scholar Bridge (Homework) and Hero System (Quests).
    """

    async def create_quest_from_homework(self, homework_title: str, xp_value: int) -> Quest:
        """
        Converts a detected homework item into a Hero Quest.
        Triggered by IntakeService (Phase 2).
        """
        quest_id = f"qst_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        new_quest = Quest(
            id=quest_id,
            title=f"Homework: {homework_title}",
            description="Complete this homework to earn XP!",
            assigned_to="jayden_hero",
            status=QuestStatus.PENDING,
            reward=QuestReward(xp=xp_value, gold=xp_value // 5),
            source_homework_id="hw_auto_detect",
        )

        # Auto-Sync to Hero System
        success = await hero_adapter.sync_quest(new_quest)
        if success:
            new_quest.status = QuestStatus.ACTIVE
            print(f"👨‍👩‍👧 [FamilyService] Created Quest: {new_quest.title}")

        return new_quest

    async def approve_quest(self, quest_id: str, parent_id: str) -> bool:
        """
        Parent approves a completed quest.
        Triggers XP reward in Hero System.
        """
        print(f"👨‍👩‍👧 [FamilyService] Parent {parent_id} approving quest {quest_id}...")

        # In a real app, we'd verify parent_id roles here.
        success = await hero_adapter.complete_quest(quest_id)

        if success:
            print("✅ Quest Approved & Rewards Granted!")

        return success

    async def get_dashboard_data(self, user_id: str) -> dict[str, Any]:
        """Aggregate data for the Dashboard UI."""
        hero_data = await hero_adapter.get_hero_status(user_id)

        return {
            "hero_status": hero_data["stats"],
            "active_quests": hero_data["active_quests"],
            "homework_pending": 3,  # Mock count for now
        }


family_service = FamilyService()
