import os
import sys

# 1. Strict Path Priority
local_path = os.path.abspath("packages/afo-core")
if local_path in sys.path:
    sys.path.remove(local_path)
sys.path.insert(0, local_path)

# Dependency path
user_site_packages = os.path.expanduser("~/Library/Python/3.12/lib/python/site-packages")
if user_site_packages not in sys.path:
    sys.path.append(user_site_packages)


def absolute_audit() -> None:
    print("💎 AFOI Final Absolute Audit (Truth 100%)")

    # Reload to ensure no cache interference
    modules = [
        "AFO",
        "AFO.domain.skills.core",
        "AFO.domain.skills.models",
        "AFO.domain.skills.definitions.context7_bridge",
    ]
    for m in modules:
        if m in sys.modules:
            del sys.modules[m]

    try:
        from AFO.domain.skills.core import register_core_skills
        from AFO.domain.skills.models import SkillCategory

        registry = register_core_skills()
        all_skills = registry.list_all()
        skill_count = len(all_skills)
        intel_count = len([s for s in all_skills if s.category == SkillCategory.INTELLIGENCE])

        print(f"📊 Registered Skills: {skill_count}")
        print(f"🧠 Intelligence Skills: {intel_count}")

        # Verify Critical Intelligence Items
        critical_ids = ["skill_041_royal_library", "skill_101_active_directory_attacks"]
        for cid in critical_ids:
            s = registry.get(cid)
            if s:
                print(f"✅ Found Critical Skill: {cid}")
            else:
                print(f"❌ MISSING Critical Skill: {cid}")
                sys.exit(1)

        if skill_count >= 139:
            print("✅ Bit-level Skill Verification: PASSED")
        else:
            print(f"❌ Bit-level Skill Verification: FAILED (Expected >=139, got {skill_count})")
            sys.exit(1)

    except Exception as e:
        print(f"💥 Audit Runtime ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    absolute_audit()
