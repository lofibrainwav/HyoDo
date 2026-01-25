#!/usr/bin/env python3
import re
from pathlib import Path

# Configuration
DOCS_DIR = Path("docs")
LOCAL_USER_PATH = "/Users/brnestrm"
MASK_PLACEHOLDER = "<LOCAL_WORKSPACE>"

# Patterns to match file:/// absolute paths
PATH_PATTERN = re.compile(re.escape(LOCAL_USER_PATH))


def mask_file(file_path: Path) -> None:
    try:
        # Try reading as UTF-8
        content = Path(file_path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback to latin-1
        try:
            content = Path(file_path).read_text(encoding="latin-1")
        except Exception as e:
            print(f"❌ Failed to read {file_path}: {e}")
            return False

    masked_content = PATH_PATTERN.sub(MASK_PLACEHOLDER, content)

    if content != masked_content:
        Path(file_path).write_text(masked_content, encoding="utf-8")
        return True
    return False


def main() -> None:
    print(f"🚀 Masking local paths ({LOCAL_USER_PATH}) in {DOCS_DIR}...")
    modified_count = 0
    if not DOCS_DIR.exists():
        print(f"❌ {DOCS_DIR} not found.")
        return
    for md_file in DOCS_DIR.rglob("*.md"):
        if mask_file(md_file):
            print(f"✅ Masked: {md_file}")
            modified_count += 1

    print(f"🎉 Done. Modified {modified_count} files.")


if __name__ == "__main__":
    main()
