import pathlib
import sys

# Check AntiGravity Configuration
try:
    sys.path.append(str(Path(__file__).parent.parent / "packages" / "afo-core"))
    from config.antigravity import antigravity

    # 1. Check DRY_RUN_DEFAULT
    if not antigravity.DRY_RUN_DEFAULT:
        print("❌ FAIL: DRY_RUN_DEFAULT should be True")
        sys.exit(1)

    # 2. Check LOG_LEVEL
    expected_log_level = "DEBUG" if antigravity.ENVIRONMENT == "dev" else "INFO"
    if expected_log_level != antigravity.LOG_LEVEL:
        print(
            f"❌ FAIL: LOG_LEVEL mismatch. Got {antigravity.LOG_LEVEL}, expected {expected_log_level}"
        )
        sys.exit(1)

    print("✅ AntiGravity Config Checked: Safe Mode Active")

except ImportError as e:
    print(f"❌ FAIL: Could not import antigravity config: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ FAIL: Unexpected error checking config: {e}")
    sys.exit(1)

# Check AGENTS.md
agents_md_path = str(Path(__file__).parent.parent) + "/AGENTS.md"
if not pathlib.Path(agents_md_path).exists():
    print("❌ FAIL: AGENTS.md not found")
    sys.exit(1)

with pathlib.Path(agents_md_path).open(encoding="utf-8") as f:
    lines = f.readlines()

    # 3. Check Line Count
    if len(lines) > 500:
        print(f"❌ FAIL: AGENTS.md is too long ({len(lines)} lines). Limit is 500.")
        sys.exit(1)

    content = "".join(lines)

    # 4. Check Key Pillars (Korean)
    required_keywords = ["眞", "善", "美", "孝", "永", "35%", "20%", "8%", "2%"]
    for kw in required_keywords:
        if kw not in content:
            print(f"❌ FAIL: AGENTS.md missing keyword '{kw}'")
            sys.exit(1)

print("✅ AGENTS.md Checked: Constitution Valid")
print("🎉 Phase 0 & 1 Verification Complete!")
sys.exit(0)
