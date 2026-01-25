# Trinity Score: 90.0 (Established by Chancellor)
from abc import ABC, abstractmethod


class Skill(ABC):
    """Abstract Product: Skill Interface (5 Pillars)
    All skills must implement execute()
    """

    @abstractmethod
    def execute(self) -> str:
        pass


class YoutubeSkill(Skill):
    """Concrete Product A"""

    def execute(self) -> str:
        return "YouTube 스킬 실행 - 진실 검증 완료"


class RAGSkill(Skill):
    """Concrete Product B"""

    def execute(self) -> str:
        return "Ultimate RAG 실행 - 지식 검색"


class SkillFactory(ABC):
    """Abstract Creator"""

    @abstractmethod
    def create_skill(self, skill_type: str) -> Skill:
        pass


class AFO_SkillFactory(SkillFactory):
    """Concrete Creator: Manages AFO Kingdom Skills
    [Factory Pattern Benefit]:
    - Decoupling: Client doesn't need to know specific Skill classes.
    - Extensibility: Add new skills to _skills map without changing client code.
    """

    _skills: dict[str, type[Skill]] = {
        "youtube": YoutubeSkill,
        "rag": RAGSkill,
        # Future expansion...
    }

    def create_skill(self, skill_type: str) -> Skill:
        if skill_type not in self._skills:
            raise ValueError(f"[Factory] 미등록 스킬 '{skill_type}' - 등록 필요")
        return self._skills[skill_type]()
