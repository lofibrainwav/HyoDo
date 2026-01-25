from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class FamilyRole(str, Enum):
    PARENT = "parent"
    CHILD = "child"
    SYSTEM = "system"


class FamilyMember(BaseModel):
    id: str
    name: str
    role: FamilyRole
    avatar_url: str | None = None
    email: str | None = None


class QuestStatus(str, Enum):
    PENDING = "PENDING"  # Created from homework, waiting sync
    ACTIVE = "ACTIVE"  # Synced to Hero System
    COMPLETED = "COMPLETED"  # Marked done by Child
    VERIFIED = "VERIFIED"  # Approved by Parent
    REJECTED = "REJECTED"  # Rejected by Parent


class QuestReward(BaseModel):
    xp: int = Field(..., description="Experience Points")
    gold: int = Field(0, description="Virtual Currency")
    item_id: str | None = None


class Quest(BaseModel):
    id: str
    title: str
    description: str
    assigned_to: str  # FamilyMember ID (Jayden)
    status: QuestStatus = QuestStatus.PENDING
    reward: QuestReward
    source_homework_id: str | None = None  # Link back to Scholar Bridge
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "qst_12345",
                "title": "Math Worksheet: Fractions",
                "description": "Complete the worksheet on page 42.",
                "assigned_to": "jayden_hero",
                "status": "ACTIVE",
                "reward": {"xp": 50, "gold": 10},
                "source_homework_id": "hw_98765",
            }
        }
