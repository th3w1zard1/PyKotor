#!/usr/bin/env python3
"""Script to replace CSS variables in QSS files with actual values."""
from __future__ import annotations

import re

from pathlib import Path


def extract_variables(content: str) -> dict[str, str]:
    """Extract CSS variable definitions from content."""
    variables = {}
    
    # Match :root { ... } or * { ... } blocks
    root_pattern = r'(?::root|\*)\s*\{([^}]+)\}'
    root_match = re.search(root_pattern, content, re.DOTALL)
    
    if root_match:
        var_block = root_match.group(1)
        # Match --variable-name: value;
        var_pattern = r'--([\w-]+)\s*:\s*([^;]+);'
        for match in re.finditer(var_pattern, var_block):
            var_name = match.group(1)
            var_value = match.group(2).strip()
            variables[var_name] = var_value
    
    return variables

def replace_variables(content: str, variables: dict[str, str]) -> str:
    """Replace all var(--variable-name) with actual values."""
    # Remove the variable definition block
    content = re.sub(r'(?::root|\*)\s*\{[^}]+\}', '', content, flags=re.DOTALL)
    
    # Replace all var(--variable-name) with actual values
    for var_name, var_value in variables.items():
        pattern = rf'var\(--{re.escape(var_name)}\)'
        content = re.sub(pattern, var_value, content)
    
    # Remove transition properties (Qt doesn't support CSS transitions)
    content = re.sub(r'transition\s*:[^;]+;', '', content)
    
    # Remove @media queries (Qt doesn't support media queries)
    content = re.sub(r'@media[^{]*\{[^}]*\}', '', content, flags=re.DOTALL)
    
    return content

def fix_qss_file(file_path: Path) -> bool:
    """Fix a single QSS file by replacing CSS variables."""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check if file uses CSS variables
        if 'var(--' not in content:
            return False  # No variables to fix
        
        variables = extract_variables(content)
        if not variables:
            return False
        
        fixed_content = replace_variables(content, variables)
        
        # Clean up extra blank lines
        fixed_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', fixed_content)
        
        file_path.write_text(fixed_content, encoding='utf-8')
        print(f"Fixed: {file_path.name}")
        return True
    except Exception as e:
        print(f"Error fixing {file_path.name}: {e}")
        return False

if __name__ == '__main__':
    qss_dir = Path(__file__).parent.parent / 'Tools' / 'HolocronToolset' / 'src' / 'resources' / 'other'
    
    if not qss_dir.exists():
        print(f"Directory not found: {qss_dir}")
        exit(1)
    
    fixed_count = 0
    for qss_file in qss_dir.glob('*.qss'):
        if fix_qss_file(qss_file):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} QSS files.")

