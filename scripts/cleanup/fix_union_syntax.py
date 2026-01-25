#!/usr/bin/env python3
"""
Python Union Syntax Compatibility Fixer
Converts Python 3.10+ union syntax to Python 3.9- compatible syntax

Usage: python fix_union_syntax.py [file_or_directory]
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Union


def convert_union_syntax(content: str) -> Tuple[str, int]:
    """Convert X | Y syntax to Union[X, Y] or Optional[X] for None"""

    # Track conversion count
    conversion_count = 0

    # Split into lines to process line by line (avoid regex flag confusion)
    lines = content.split("\n")
    new_lines = []

    for line in lines:
        # Skip lines that are likely regex patterns or imports
        if "re." in line and ("|" in line):
            # This might be regex flags like re.MULTILINE | re.IGNORECASE
            new_lines.append(line)
            continue

        # Skip comment lines
        if line.strip().startswith("#"):
            new_lines.append(line)
            continue

        # Pattern 0: Generic function syntax func[T](...) → func(...)
        # This handles Python 3.12+ generic function syntax
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
        # Only for simple type unions, avoid complex cases
        pattern3 = re.compile(
            r"\b([A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])?)\s*\|\s*([A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])?)\b"
        )
        line, count3 = pattern3.subn(r"Union[\1, \2]", line)
        conversion_count += count3

        new_lines.append(line)

    return "\n".join(new_lines), conversion_count


def ensure_imports(content: str) -> str:
    """Ensure Union and Optional are imported if needed"""

    # Check if Union/Optional are used
    has_union = "Union[" in content
    has_optional = "Optional[" in content

    if not (has_union or has_optional):
        return content

    # Find existing typing imports
    typing_imports: List[Union[int, Tuple[int, int]]] = []
    lines = content.split("\n")

    # Find the position after __future__ imports
    future_import_pos = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("from __future__ import"):
            future_import_pos = i + 1
        elif line.strip() and not line.strip().startswith("#"):
            break

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("from typing import"):
            typing_imports.append(i)
        elif line.startswith("import typing"):
            typing_imports.append(i)
        elif line.startswith("from typing"):
            # Handle multi-line imports
            if "," in line or "(" in line:
                # Multi-line import, find the end
                j = i + 1
                while j < len(lines) and (lines[j].strip().startswith(")") or "," in lines[j]):
                    j += 1
                typing_imports.append((i, j))
            else:
                typing_imports.append(i)

    # If no typing imports, add at the top after any __future__ imports
    if not typing_imports:
        insert_pos = future_import_pos

        imports_to_add = []
        if has_optional:
            imports_to_add.append("Optional")
        if has_union:
            imports_to_add.append("Union")

        if imports_to_add:
            import_line = f"from typing import {', '.join(imports_to_add)}"
            lines.insert(insert_pos, import_line)
            lines.insert(insert_pos + 1, "")  # Empty line

    return "\n".join(lines)


def process_file(file_path: Path) -> Tuple[bool, int]:
    """Process a single Python file"""
    try:
        # Read content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Convert syntax
        new_content, conversions = convert_union_syntax(content)

        # Ensure imports
        if conversions > 0:
            new_content = ensure_imports(new_content)

        if conversions > 0:
            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ {file_path}: {conversions} conversions")
            return True, conversions
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
        print("Usage: python fix_union_syntax.py <file_or_directory>")
        print("Example: python fix_union_syntax.py packages/afo-core/")
        print("Example: python fix_union_syntax.py specific_file.py")
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

    total_conversions = 0
    processed_files = 0
    failed_files = 0

    for file_path in python_files:
        success, conversions = process_file(file_path)
        if success:
            processed_files += 1
            total_conversions += conversions
        else:
            failed_files += 1

    print("\n📊 Summary:")
    print(f"   Processed: {processed_files} files")
    print(f"   Failed: {failed_files} files")
    print(f"   Total conversions: {total_conversions}")

    if failed_files > 0:
        print(f"⚠️  {failed_files} files failed to process")
        sys.exit(1)
    elif total_conversions == 0:
        print("ℹ️  No union syntax found to convert")
    else:
        print("🎉 All conversions completed successfully!")


if __name__ == "__main__":
    main()
