import os
import pathlib
import sys

# Add package root to sys.path
# Using absolute path to packages/afo-core so we can import modules directly
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

try:
    from factories.skill_factory import AFO_SkillFactory, Skill
except ImportError:
    print("❌ Critical Import Error: Could not import 'factories.skill_factory'")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)


class MockSkill(Skill):
    def execute(self) -> str:
        return "New Skill Executed"


def test_factory_pattern() -> None:
    print("\n[Testing Factory Pattern]")

    factory = AFO_SkillFactory()

    # Test 1: Standard Creation
    print("Testing Standard Creation...")
    try:
        yt = factory.create_skill("youtube")
        print(f"✅ Created Youtube Skill: {yt.execute()}")

        rag = factory.create_skill("rag")
        print(f"✅ Created RAG Skill: {rag.execute()}")
    except Exception as e:
        print(f"❌ Creation Failed: {e}")
        sys.exit(1)

    # Test 2: Error Handling
    print("Testing Unknown Skill...")
    try:
        factory.create_skill("unknown")
        print("❌ Failed: Should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        print(f"✅ Correctly handled unknown skill: {e}")

    # Test 3: Extensibility (Open/Closed Principle)
    print("Testing Dynamic Extension...")
    AFO_SkillFactory._skills["new_skill"] = MockSkill
    try:
        new_skill = factory.create_skill("new_skill")
        res = new_skill.execute()
        if res == "New Skill Executed":
            print(f"✅ Dynamic Extension Success: {res}")
        else:
            print(f"❌ Dynamic Extension Wrong Output: {res}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Dynamic Extension Failed: {e}")
        sys.exit(1)

    print("🎉 Factory Pattern Verification Complete!")


if __name__ == "__main__":
    test_factory_pattern()
