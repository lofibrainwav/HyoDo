#!/usr/bin/env python3
"""
Comprehensive Python Compatibility Fixer
Fixes both union syntax and import ordering issues for Python < 3.10 compatibility

Usage: python fix_all_python_compatibility.py [file_or_directory]
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def fix_union_syntax(content: str) -> Tuple[str, int]:
    """Convert X | Y syntax to Union[X, Y] or Optional[X] for None"""

    conversion_count = 0

    # Split into lines to process line by line (avoid regex flag confusion)
    lines = content.split("\n")
    new_lines = []

    for line in lines:
        # Skip lines that are likely regex patterns or imports
        if "re." in line and ("|" in line):
            new_lines.append(line)
            continue

        # Skip comment lines
        if line.strip().startswith("#"):
            new_lines.append(line)
            continue

        # Pattern 0: Generic function syntax func[T](...) → func(...)
        pattern0 = re.compile(r"\bdef\s+(\w+)\[([A-Za-z_][A-Za-z0-9_]*)\]\s*\(")
        line, count0 = pattern0.subn(r"def \1(", line)
        conversion_count += count0

        # Pattern 1: (type) | None → Optional[type]
        pattern1 = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])?)\s*\|\s*None\b")
        line, count1 = pattern1.subn(r"Optional[\1]", line)
        conversion_count += count1

        # Pattern 2: None | (type) → Optional[type]
        pattern2 = re.compile(r"\bNone\s*\|\s*([A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])?)\b")
        line, count2 = pattern2.subn(r"Optional[\1]", line)
        conversion_count += count2

        # Pattern 3: (type1) | (type2) → Union[type1, type2]
        pattern3 = re.compile(
            r"\b([A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])?)\s*\|\s*([A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])?)\b"
        )
        line, count3 = pattern3.subn(r"Union[\1, \2]", line)
        conversion_count += count3

        new_lines.append(line)

    return "\n".join(new_lines), conversion_count


def fix_import_ordering(content: str) -> Tuple[str, bool]:
    """Fix import ordering for __future__ imports"""
    lines = content.split("\n")

    # Find __future__ imports and other imports
    future_imports = []
    other_imports = []
    non_imports = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Handle multi-line imports
        if line.startswith("from __future__ import"):
            future_imports.append(line)
        elif line.startswith(("from ", "import ")) and not line.startswith("from __future__"):
            # Check if this is a multi-line import
            if line.endswith("(") or (line.endswith(",") and i + 1 < len(lines)):
                # Multi-line import, collect all lines
                import_lines = [line]
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    import_lines.append(lines[j])
                    if next_line.endswith(")"):
                        break
                    j += 1
                other_imports.append("".join(import_lines))
                i = j
            else:
                other_imports.append(line)
        else:
            non_imports.append(lines[i])
        i += 1

    # If no __future__ imports, no changes needed
    if not future_imports:
        return content, False

    # Reconstruct file with proper ordering
    new_content = []

    # Add __future__ imports first
    for future_import in future_imports:
        new_content.append(future_import)

    # Add empty line if there are other imports
    if other_imports:
        new_content.append("")

    # Add other imports
    for other_import in other_imports:
        new_content.append(other_import)

    # Add empty line before non-imports if there were imports
    if future_imports or other_imports:
        new_content.append("")

    # Add rest of file
    new_content.extend(non_imports)

    return "\n".join(new_content), True


def ensure_imports(content: str) -> Tuple[str, bool]:
    """Ensure Union and Optional are imported if needed"""
    has_union = "Union[" in content
    has_optional = "Optional[" in content

    if not (has_union or has_optional):
        return content, False

    lines = content.split("\n")

    # Find existing typing imports
    typing_imports = []
    future_import_pos = 0

    for i, line in enumerate(lines):
        if line.strip().startswith("from __future__ import"):
            future_import_pos = i + 1
        elif line.strip().startswith("from typing import"):
            typing_imports.append(i)

    # If no typing imports, add one
    if not typing_imports:
        imports_to_add = []
        if has_optional:
            imports_to_add.append("Optional")
        if has_union:
            imports_to_add.append("Union")

        if imports_to_add:
            import_line = f"from typing import {', '.join(imports_to_add)}"
            lines.insert(future_import_pos, import_line)
            lines.insert(future_import_pos + 1, "")
            return "\n".join(lines), True

    return content, False


def process_file(file_path: Path) -> Tuple[bool, int]:
    """Process a single Python file"""
    try:
        # Read content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        changes_made = 0

        # Fix import ordering first
        content, import_order_changed = fix_import_ordering(content)
        if import_order_changed:
            changes_made += 1

        # Convert union syntax
        content, conversions = fix_union_syntax(content)
        changes_made += conversions

        # Ensure imports
        content, imports_added = ensure_imports(content)
        if imports_added:
            changes_made += 1

        if changes_made > 0:
            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ {file_path}: {changes_made} changes ({conversions} union conversions)")
            return True, changes_made
        else:
            return True, 0

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False, 0


def find_python_files(root_path: Path) -> List[Path]:
    """Find all Python files recursively"""
    python_files = []
    exclude_dirs = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        "venv",
        ".venv",
        "env",
        ".env",
        "build",
        "dist",
        ".next",
        ".nuxt",
        "coverage",
        "htmlcov",
    }

    for root, dirs, files in os.walk(root_path):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    return python_files


def main() -> None:
    """Main conversion process"""
    if len(sys.argv) < 2:
        print("Usage: python fix_all_python_compatibility.py <file_or_directory>")
        print("Example: python fix_all_python_compatibility.py packages/afo-core/")
        print("Example: python fix_all_python_compatibility.py specific_file.py")
        sys.exit(1)

    target_path = Path(sys.argv[1])

    if not target_path.exists():
        print(f"❌ Path does not exist: {target_path}")
        sys.exit(1)

    # Get files to process
    if target_path.is_file():
        if not target_path.suffix == ".py":
            print(f"❌ Not a Python file: {target_path}")
            sys.exit(1)
        python_files = [target_path]
    else:
        python_files = find_python_files(target_path)

    print(f"🔍 Found {len(python_files)} Python files to process")

    total_changes = 0
    processed_files = 0
    failed_files = 0

    for file_path in python_files:
        success, changes = process_file(file_path)
        if success:
            processed_files += 1
            total_changes += changes
        else:
            failed_files += 1

    print("\n📊 Summary:")
    print(f"   Processed: {processed_files} files")
    print(f"   Failed: {failed_files} files")
    print(f"   Total changes: {total_changes}")

    if failed_files > 0:
        print(f"⚠️  {failed_files} files failed to process")
        sys.exit(1)
    elif total_changes == 0:
        print("ℹ️  No changes needed")
    else:
        print("🎉 All compatibility fixes completed successfully!")


if __name__ == "__main__":
    main()
