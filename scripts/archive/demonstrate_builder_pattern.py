import os
import pathlib
import sys
from typing import Type

# Add package root to sys.path for direct imports if needed
sys.path.append(pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages")).resolve())

try:
    from afo_core.builders.trinity_query_builder import TrinityQueryBuilder
    from afo_core.factories.skill_factory import AFO_SkillFactory, Skill
except ImportError:
    # Adjust path if running from root relative to packages
    sys.path.append(
        pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
    )
    from builders.trinity_query_builder import TrinityQueryBuilder
    from factories.skill_factory import AFO_SkillFactory


def demonstrate_builder() -> None:
    print("👑 [Builder Pattern Demonstration]")

    # scenario: Constructing a complex query request for the CPA Widget
    print("\n--- 1. Using Builder (Assembly Elegance) ---")
    try:
        builder = TrinityQueryBuilder()
        complex_query = (
            builder.set_query("Deploy CPA Financial Widget")
            .with_context({"user_role": "Commander", "theme": "Glassmorphism"})
            .with_risk(0.05)
            .with_ux(8)
            .dry_run_mode(True)
            .build()
        )
        print(f"✅ Built Complex Object:\n{complex_query}")
        print(f"   Structure Type: {type(complex_query)}")
        print(f"   Verification: Risk={complex_query.risk_level}, DryRun={complex_query.dry_run}")

    except Exception as e:
        print(f"❌ Builder Failed: {e}")

    # scenario: Compare with Factory Method
    print("\n--- 2. Comparing with Factory Method (Creation Expansion) ---")
    print("   [Factory] Focus: Creating different *types* of objects (Polymorphism)")
    print("   [Builder] Focus: Creating *one* complex object with many *configurations*")

    factory = AFO_SkillFactory()
    skill = factory.create_skill("youtube")
    print(f"✅ Factory Created: {skill.execute()}")

    print("\n✅ Comparison Verified: Builder handles Configuration, Factory handles Polymorphism.")


if __name__ == "__main__":
    demonstrate_builder()
