#!/usr/bin/env python3
"""Remove empty TYPE_CHECKING blocks and unused TYPE_CHECKING imports."""

from __future__ import annotations

import re

from pathlib import Path


def fix_file(file_path: Path) -> bool:
    """Fix a single Python file.
    
    Returns True if the file was modified.
    """
    content = file_path.read_text(encoding="utf-8")
    original_content = content
    
    # Pattern to match empty TYPE_CHECKING blocks
    # Matches: if TYPE_CHECKING: followed by only whitespace then a class/def/non-indented line
    pattern = re.compile(
        r'if TYPE_CHECKING:\s*\n\n',
        re.MULTILINE
    )
    
    content = pattern.sub('', content)
    
    # Also remove "from typing import TYPE_CHECKING" if there's no TYPE_CHECKING block
    if "if TYPE_CHECKING:" not in content:
        content = re.sub(r'from typing import TYPE_CHECKING\s*\n', '', content)
    
    # Clean up multiple blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    if content != original_content:
        file_path.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    """Main function to fix all dencs files."""
    dencs_path = Path("G:/GitHub/PyKotor/Libraries/PyKotor/src/pykotor/resource/formats/ncs/dencs")
    
    fixed_count = 0
    for py_file in sorted(dencs_path.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        try:
            if fix_file(py_file):
                print(f"Fixed: {py_file.relative_to(dencs_path)}")
                fixed_count += 1
        except Exception as e:
            print(f"Error in {py_file.relative_to(dencs_path)}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\nTotal files fixed: {fixed_count}")


if __name__ == "__main__":
    main()
