#!/usr/bin/env python3
"""Fix DeNCS node imports that have base classes inside TYPE_CHECKING blocks.

This script finds all files where a class inherits from a base class that is only
imported inside a TYPE_CHECKING block, and moves that import outside the block.
"""

from __future__ import annotations

import re

from pathlib import Path


def fix_file(file_path: Path) -> bool:
    """Fix a single Python file.

    Returns True if the file was modified.
    """
    content = file_path.read_text(encoding="utf-8")
    original_content = content
    lines = content.splitlines(keepends=True)

    # Find all class definitions and their base classes using regex
    class_pattern = re.compile(r"^class\s+(\w+)\s*\((\w+)\)\s*:", re.MULTILINE)
    class_matches = class_pattern.findall(content)

    if not class_matches:
        return False

    base_classes = set(base for _, base in class_matches)

    # Find imports in TYPE_CHECKING block
    in_type_checking = False
    type_checking_imports = {}  # name -> (line_index, full_import_statement)
    type_checking_start = None
    type_checking_end = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped == "if TYPE_CHECKING:":
            in_type_checking = True
            type_checking_start = i
            continue

        if in_type_checking:
            # Check if we're leaving the TYPE_CHECKING block
            if stripped and not stripped.startswith("#") and not line.startswith(" ") and not line.startswith("\t"):
                in_type_checking = False
                type_checking_end = i
                continue

            # Parse import statement
            import_match = re.match(r"\s*from\s+[\w.]+\s+import\s+(\w+)", stripped)
            if import_match:
                imported_name = import_match.group(1)
                type_checking_imports[imported_name] = (i, stripped)

    # If TYPE_CHECKING block continues to end of file
    if in_type_checking:
        type_checking_end = len(lines)

    # Find which base classes need to be moved
    imports_to_move = {}
    for base_class in base_classes:
        if base_class in type_checking_imports:
            imports_to_move[base_class] = type_checking_imports[base_class]

    if not imports_to_move:
        return False

    # Find insertion point (after TYPE_CHECKING import line)
    insert_pos = 0
    for i, line in enumerate(lines):
        if "from typing import" in line or "import typing" in line:
            insert_pos = i + 1
            break
        if "from __future__ import" in line:
            insert_pos = i + 1

    # Build new content
    new_lines = []
    lines_to_remove = set(idx for idx, _ in imports_to_move.values())

    for i, line in enumerate(lines):
        if i == insert_pos:
            # Insert imports to move
            new_lines.append("\n")
            for name, (_, stmt) in sorted(imports_to_move.items(), key=lambda x: x[1][0]):
                new_lines.append(stmt + "\n")

        if i not in lines_to_remove:
            new_lines.append(line)

    content = "".join(new_lines)

    # Clean up multiple blank lines
    content = re.sub(r"\n{3,}", "\n\n", content)

    if content != original_content:
        file_path.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    """Main function to fix all dencs node files."""
    dencs_node_path = Path("G:/GitHub/PyKotor/Libraries/PyKotor/src/pykotor/resource/formats/ncs/dencs/node")

    fixed_count = 0
    for py_file in sorted(dencs_node_path.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        try:
            if fix_file(py_file):
                print(f"Fixed: {py_file.name}")
                fixed_count += 1
        except Exception as e:
            print(f"Error in {py_file.name}: {e}")
            import traceback

            traceback.print_exc()

    print(f"\nTotal files fixed: {fixed_count}")


if __name__ == "__main__":
    main()
