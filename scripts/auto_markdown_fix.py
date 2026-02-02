#!/usr/bin/env python3
"""
AFO Kingdom Auto Markdown Fixer
Truth (眞): Automates MD032 and Table Alignment to ensure pristine documentation.
"""

import re
import sys


def fix_md032_list_spacing(lines) -> None:
    """
    MD032: Lists should be surrounded by blank lines.
    """
    fixed_lines = []
    in_list = False

    # List markers: - * + 1.
    list_pattern = re.compile(r"^(\s*)([-*+]|\d+\.)\s+")

    for i, line in enumerate(lines):
        match = list_pattern.match(line)
        is_list_item = match is not None
        is_blank = line.strip() == ""

        # Start of a list
        if is_list_item and not in_list:
            # Check previous line
            if i > 0 and not lines[i - 1].strip() == "" and not lines[i - 1].strip().endswith(":"):
                # Insert blank line if previous is not a header ending in : or blank
                # But usually headers don't end in : in MD unless it's a specific style.
                # Let's be safe: If previous line is text, add blank.
                # Headers (#) usually don't need blank before list if strictly following some loose styles,
                # but standard is nice.
                # Wait, looking at common patterns: "Header\n- Item" is MD032 violation. "Header\n\n- Item" is correct.
                if not fixed_lines[-1].strip() == "":
                    fixed_lines.append("")
            in_list = True

        # End of a list (transition to non-list, non-blank)
        if not is_list_item and not is_blank and in_list:
            # We just exited a list block into text
            if not fixed_lines[-1].strip() == "":
                fixed_lines.append("")
            in_list = False

        # Reset in_list if blank line
        if is_blank:
            in_list = False

        fixed_lines.append(line)

    return fixed_lines


def fix_table_alignment(lines) -> None:
    """
    Aligns markdown tables.
    """
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect table start (naive: starts and ends with |)
        if stripped.startswith("|") and stripped.endswith("|"):
            # Look ahead to see if it's a table (must have separator line)
            if i + 1 < len(lines) and "---" in lines[i + 1]:
                # It is a table. Collect all rows.
                table_rows = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_rows.append(lines[i])
                    i += 1

                # Process table
                # 1. Parse cells
                parsed_rows = []
                max_cols = 0
                for r in table_rows:
                    # Split by pipe, ignore first and last empty from split('|')
                    cells = [c.strip() for c in r.strip().split("|")]
                    if cells and cells[0] == "":
                        cells.pop(0)
                    if cells and cells[-1] == "":
                        cells.pop()
                    parsed_rows.append(cells)
                    max_cols = max(max_cols, len(cells))

                # 2. Calculate max width per column
                col_widths = [0] * max_cols
                for r_idx, cells in enumerate(parsed_rows):
                    if r_idx == 1:
                        continue  # Skip separator row for width calc usually? No, separator needs to be aligned too (at least 3 dashes)
                    for c_idx, cell in enumerate(cells):
                        if c_idx < max_cols:
                            col_widths[c_idx] = max(col_widths[c_idx], len(cell))

                # Ensure separator has at least 3 dashes
                for c_idx in range(max_cols):
                    col_widths[c_idx] = max(col_widths[c_idx], 3)

                # 3. Reconstruct
                for r_idx, cells in enumerate(parsed_rows):
                    # Pad cells if row is short
                    while len(cells) < max_cols:
                        cells.append("")

                    if r_idx == 1:
                        # Separator row
                        row_str = "|"
                        for c_idx in range(max_cols):
                            row_str += " " + "-" * col_widths[c_idx] + " |"
                        fixed_lines.append(row_str)
                    else:
                        # Normal row
                        row_str = "|"
                        for c_idx, cell in enumerate(cells):
                            padding = col_widths[c_idx] - len(cell)
                            row_str += " " + cell + " " * padding + " |"
                        fixed_lines.append(row_str)

                continue  # Main loop continues
            else:
                fixed_lines.append(line)
                i += 1
        else:
            fixed_lines.append(line)
            i += 1

    return fixed_lines


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python auto_markdown_fix.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        # Apply Fixes
        step1 = fix_md032_list_spacing(lines)
        step2 = fix_table_alignment(step1)

        # Write back
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(step2) + "\n")

        print(f"✅ Automatically fixed: {file_path}")

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
