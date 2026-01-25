from abc import ABC, abstractmethod


# ==========================================
# 1. Common Product Interface (5 Pillars)
# ==========================================
class Skill(ABC):
    @abstractmethod
    def execute(self) -> str:
        pass


class YoutubeSkill(Skill):
    def execute(self) -> str:
        return "YouTube Skill Executed (Truth)"


class RAGSkill(Skill):
    def execute(self) -> str:
        return "RAG Skill Executed (Truth)"


# ==========================================
# 2. Variant 1: Simple Factory (Static)
# ==========================================
class SimpleSkillFactory:
    @staticmethod
    def create_skill(skill_type: str) -> Skill:
        if skill_type == "youtube":
            return YoutubeSkill()
        if skill_type == "rag":
            return RAGSkill()
        msg = "Unknown Skill"
        raise ValueError(msg)


# ==========================================
# 3. Variant 2: Factory Method (Inheritance)
# ==========================================
class BaseSkillFactory(ABC):
    @abstractmethod
    def create_skill(self) -> Skill:
        pass

    def operate(self) -> str:
        # Template method using the factory method
        skill = self.create_skill()
        return f"Factory Method Operation: {skill.execute()}"


class YoutubeFactory(BaseSkillFactory):
    def create_skill(self) -> Skill:
        return YoutubeSkill()


class RAGFactory(BaseSkillFactory):
    def create_skill(self) -> Skill:
        return RAGSkill()


# ==========================================
# 4. Variant 3: Abstract Factory (Families)
# ==========================================
class MCP(ABC):
    @abstractmethod
    def connect(self) -> str:
        pass


class UltimateMCP(MCP):
    def connect(self) -> str:
        return "Connected to Ultimate MCP"


class AbstractKingdomFactory(ABC):
    @abstractmethod
    def create_skill(self) -> Skill:
        pass

    @abstractmethod
    def create_mcp(self) -> MCP:
        pass


class AFO_KingdomFactory(AbstractKingdomFactory):
    def create_skill(self) -> Skill:
        return YoutubeSkill()  # Default family skill

    def create_mcp(self) -> MCP:
        return UltimateMCP()


# ==========================================
# 5. Demonstration / Dry Run
# ==========================================
def run_demonstration() -> None:
    print("👑 [Factory Variants Demonstration]")

    # 1. Simple Factory
    print("\n--- 1. Simple Factory (Beauty/Efficiency) ---")
    s_skill = SimpleSkillFactory.create_skill("youtube")
    print(f"Result: {s_skill.execute()}")

    # 2. Factory Method
    print("\n--- 2. Factory Method (Goodness/Extensibility) ---")
    yt_factory = YoutubeFactory()
    print(f"Result: {yt_factory.operate()}")

    # 3. Abstract Factory
    print("\n--- 3. Abstract Factory (Truth/Integrity) ---")
    kingdom_factory = AFO_KingdomFactory()
    k_skill = kingdom_factory.create_skill()
    k_mcp = kingdom_factory.create_mcp()
    print(f"Skill: {k_skill.execute()}")
    print(f"MCP: {k_mcp.connect()}")

    print("\n✅ All Variants Verified Successfully.")


if __name__ == "__main__":
    run_demonstration()
