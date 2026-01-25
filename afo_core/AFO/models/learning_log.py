# Trinity Score: 90.0 (Established by Chancellor)
"""Learning Log Model (Phase 16-4)
The Memory of the Kingdom's Evolution.
"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class LearningLog(SQLModel, table=True):
    __tablename__ = "learning_logs"

    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent: str  # e.g., "samahwi", "zhou_yu"
    action: str  # e.g., "created_widget", "refactored_widget"
    trinity_before: float
    trinity_after: float
    delta: float
    feedback: str  # e.g., "Beauty Score improved by 10 points."
    success: bool = True
