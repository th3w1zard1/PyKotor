"""Script to fix indentation errors in help test functions."""

from __future__ import annotations

import re

from pathlib import Path


def fix_file(test_file_path: Path):
    """Fix indentation errors in a test file."""
    content = test_file_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Find and fix incomplete function definitions followed by help test
    i = 0
    while i < len(lines) - 1:
        # Look for function definition with no body followed by help test
        if re.match(r"^def test_\w+\(.*\):$", lines[i]) and lines[i + 1].strip() == "":
            # Check if next non-empty line is a help test
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and "help_dialog" in lines[j]:
                # Remove the incomplete function definition
                lines.pop(i)
                i -= 1
        i += 1

    new_content = "\n".join(lines)
    if new_content != content:
        test_file_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main():
    """Main function."""
    repo_root = Path(__file__).parent.parent
    test_dir = repo_root / "tests" / "test_toolset" / "gui" / "editors"

    print("Fixing indentation errors in help test files...")

    test_files = list(test_dir.glob("test_*_editor.py"))
    fixed_count = 0

    for test_file_path in test_files:
        if fix_file(test_file_path):
            print(f"  Fixed {test_file_path.name}")
            fixed_count += 1

    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()
