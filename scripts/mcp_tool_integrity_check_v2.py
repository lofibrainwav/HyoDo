import asyncio
import os
import sys

# Setup paths
package_root = "./packages/afo-core"
if package_root not in sys.path:
    sys.path.append(package_root)

try:
    from afo_skills_registry import skills_registry
    from domain.skills import SkillFilterParams
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)


async def verify_registry():
    print("🏰 AFO Skill Registry Audit")
    print("-" * 30)

    count = skills_registry.count()
    print(f"Total skills registered: {count}")

    all_skills = skills_registry.filter(SkillFilterParams())
    print("\nRegistered Skills List:")
    for skill in all_skills:
        mcp_status = "✅ MCP Ready" if skill.mcp_config else "❌ No MCP Config"
        print(f"  - [{skill.category.value}] {skill.name} ({skill.skill_id}): {mcp_status}")
        if skill.mcp_config:
            # MCPConfig doesn't have .tools, it has .capabilities
            print(f"    MCP Version: {skill.mcp_config.mcp_version}")
            print(f"    Capabilities: {', '.join(skill.mcp_config.capabilities)}")

        # Check Philosophy Alignment
        print(f"    Philosophy: {skill.philosophy_scores.summary}")

    # Check Skills Directory
    print("\n" + "-" * 30)
    print("📂 Skills Directory Synchronization Check")
    skills_dir = "./skills"
    physical_skills = [
        d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))
    ]
    print(f"Physical skill directories found: {len(physical_skills)}")

    for ps in physical_skills:
        # Match by ID or folder name
        is_registered = any(
            skill.skill_id == ps or skill.skill_id.endswith(ps.replace("-", "_"))
            for skill in all_skills
        )
        status = "✅ Registered" if is_registered else "⚠️ NOT REGISTERED"
        print(f"  - {ps}: {status}")


if __name__ == "__main__":
    asyncio.run(verify_registry())
