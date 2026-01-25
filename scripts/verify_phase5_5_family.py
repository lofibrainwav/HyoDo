"""
Verification Script for Phase 5.5 (Family Hub)
Tests the FamilyService flow:
1. Create Quest from Homework (Mock Intake)
2. Verify Quest in Hero System (Adapter Check)
3. Approve Quest (Parent Action)
4. Verify Rewards (Gold/XP Update)
"""

import asyncio
import sys

from application.family.service import family_service
from domain.family.models import QuestStatus
from infrastructure.external.hero_system import hero_adapter


async def verify_family_hub_flow():
    print("👨‍👩‍👧 Starting Phase 5.5 Verification: Family Hub Flow")

    # 1. Simulate Homework Detection
    print("\n📚 1. Simulating Homework Intake...")
    quest = await family_service.create_quest_from_homework(
        homework_title="Math Worksheet #42", xp_value=100
    )

    if quest.id in hero_adapter._quests:
        print(f"✅ Quest Created & Synced: {quest.title} (ID: {quest.id})")
    else:
        print("❌ FAIL: Quest not found in Hero System Adapter.")
        return False

    # 2. Check Dashboard Data
    print("\n📊 2. Checking Dashboard Data...")
    dashboard = await family_service.get_dashboard_data(user_id="parent_user")
    active_quests = dashboard["active_quests"]

    if len(active_quests) > 0 and active_quests[0].id == quest.id:
        print(f"✅ Dashboard shows active quest: {active_quests[0].title}")
    else:
        print("❌ FAIL: Dashboard data incorrect.")
        return False

    # 3. Approve Quest
    print("\n🏆 3. Approving Quest...")
    success = await family_service.approve_quest(quest.id, parent_id="dad_123")

    if success:
        print("✅ Quest Approved.")
    else:
        print("❌ FAIL: Approval failed.")
        return False

    # 4. Verify Rewards
    print("\n💰 4. Verifying Rewards...")
    final_stats = hero_adapter._hero_stats
    # Initial XP: 1250, Reward: 100 -> Expected: 1350
    if final_stats["xp"] == 1350:
        print(f"✅ XP Updated: {final_stats['xp']}")
    else:
        print(f"❌ FAIL: XP mismatch. Expected 1350, Got {final_stats['xp']}")
        return False

    print("\n🎉 Phase 5.5 Verification Complete!")
    return True


if __name__ == "__main__":
    success = asyncio.run(verify_family_hub_flow())
    sys.exit(0 if success else 1)
