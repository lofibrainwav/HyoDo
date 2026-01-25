import os
import re
from pathlib import Path


def heal_file(file_path) -> None:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    modified = False

    # 1. Fix datetime.now(UTC) -> datetime.now(UTC)
    if "now(UTC)" in content:
        # Avoid double fixing
        if "now(UTC)" not in content:
            # Add UTC import if missing
            if "from datetime import" in content:
                if "UTC" not in content:
                    # Append UTC to existing from datetime import ...
                    content = re.sub(r"(from datetime import [^\n]+)", r"\1, UTC", content)
                    content = content.replace(
                        ", UTC, UTC", ", UTC"
                    )  # Clean up if accidentally double added
            elif "import datetime" in content:
                content = content.replace(
                    "import datetime", "import datetime\nfrom datetime import UTC"
                )
            else:
                # No datetime import found? Add it at the top
                content = "from datetime import UTC\n" + content

            content = content.replace(".now(UTC)", ".now(UTC)")
            modified = True

    # 2. Fix .model_dump() -> .model_dump() for Pydantic/SQLModel
    if ".model_dump()" in content:
        # Target files that likely use Pydantic/SQLModel
        if any(x in content.lower() for x in ["pydantic", "sqlmodel", "base_model"]):
            content = content.replace(".model_dump()", ".model_dump()")
            modified = True

    # 3. Fix utcnow without prefix if any
    if " now(UTC)" in content or "(now(UTC)" in content:
        content = content.replace("now(UTC)", "now(UTC)")
        modified = True

    if modified and content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main() -> None:
    # Widening scope to target all packages
    target_dirs = [Path("packages/afo-core"), Path("packages/trinity-os"), Path("scripts")]
    healed_count = 0
    for target_dir in target_dirs:
        if not target_dir.exists():
            continue
        print(f"🔍 Scanning {target_dir}...")
        for root, _, files in os.walk(target_dir):
            if "node_modules" in root or ".venv" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    full_path = Path(root) / file
                    try:
                        if heal_file(full_path):
                            print(f"✅ Healed: {full_path}")
                            healed_count += 1
                    except Exception as e:
                        print(f"❌ Error healing {full_path}: {e}")

    print(f"\n✨ Total files healed: {healed_count}")


if __name__ == "__main__":
    main()
