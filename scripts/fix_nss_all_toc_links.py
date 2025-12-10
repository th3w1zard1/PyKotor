#!/usr/bin/env python3
"""Fix all NSS-File-Format.md TOC links to point to correct files."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
NSS_FILE = WIKI_DIR / "NSS-File-Format.md"

# Map function prefixes to their files
FUNCTION_FILE_MAP = {
    "GetAbility": "NSS-Shared-Functions-Abilities-and-Stats",
    "SetAbility": "NSS-Shared-Functions-Abilities-and-Stats",
    "GetNPC": "NSS-Shared-Functions-Abilities-and-Stats",
    "SetNPC": "NSS-Shared-Functions-Abilities-and-Stats",
    "SWMG_Start": "NSS-Shared-Functions-Abilities-and-Stats",
    "Action": "NSS-Shared-Functions-Actions",
    "Effect": "NSS-Shared-Functions-Effects-System",
    "GetEffect": "NSS-Shared-Functions-Effects-System",
    "SetEffect": "NSS-Shared-Functions-Effects-System",
    "RemoveEffect": "NSS-Shared-Functions-Effects-System",
    "GetGlobal": "NSS-Shared-Functions-Global-Variables",
    "SetGlobal": "NSS-Shared-Functions-Global-Variables",
    "GetItem": "NSS-Shared-Functions-Item-Management",
    "SetItem": "NSS-Shared-Functions-Item-Management",
    "CreateItem": "NSS-Shared-Functions-Item-Management",
    "DestroyItem": "NSS-Shared-Functions-Item-Management",
    "GetIsInCombat": "NSS-Shared-Functions-Combat-Functions",
    "GetLastAttack": "NSS-Shared-Functions-Combat-Functions",
    "GetLastAttacker": "NSS-Shared-Functions-Combat-Functions",
    "GetLastDamager": "NSS-Shared-Functions-Combat-Functions",
    "Get": "NSS-Shared-Functions-Other-Functions",  # Catch-all for Get* functions (must be last)
    "Set": "NSS-Shared-Functions-Other-Functions",  # Catch-all for Set* functions (must be last)
}

def get_function_file(func_name: str) -> str | None:
    """Get the file name for a function."""
    for prefix, file_name in FUNCTION_FILE_MAP.items():
        if func_name.startswith(prefix):
            return file_name
    return "NSS-Shared-Functions-Other-Functions"  # Default

def normalize_function_name(text: str) -> str:
    """Extract function name from TOC link text."""
    match = re.match(r'`([^(]+)\(', text)
    if match:
        return match.group(1)
    return ""

def fix_toc_links():
    """Fix TOC links in NSS-File-Format.md."""
    content = NSS_FILE.read_text(encoding='utf-8')
    original_content = content
    fixes = 0
    lines = content.splitlines()
    new_lines = []
    
    for line in lines:
        original_line = line
        # Match lines with function links: - [`Function(params)` - Routine N](#anchor or file)
        # Pattern: backtick, function name, backtick, optional routine, link
        if '`' in line and ('Routine' in line or '](NSS-' in line):
            # Extract function name
            func_match = re.search(r'`([^(]+)\(', line)
            if func_match:
                func_name = func_match.group(1)
                # Extract routine number if present
                routine_match = re.search(r'Routine\s+(\d+)', line)
                routine_num = routine_match.group(1) if routine_match else None
                # Extract the full function text in backticks
                func_text_match = re.search(r'`([^`]+)`', line)
                func_text = func_text_match.group(1) if func_text_match else func_name
                
                # Get target file
                file_name = get_function_file(func_name)
                routine_str = f" - Routine {routine_num}" if routine_num else ""
                
                # Create anchor from function name (lowercase, no special chars, matches HTML anchor format)
                anchor = func_name.lower().replace('_', '')
                
                # Check if link already points to a file without anchor
                if f']({file_name})' in line and '#' not in line:
                    # Add anchor to existing file link
                    line = line.replace(f']({file_name})', f']({file_name}#{anchor})')
                    fixes += 1
                elif '](#' in line:
                    # Replace anchor link with file link + anchor
                    line = re.sub(
                        r'\[`[^`]+`[^\]]*\]\([^\)]+\)',
                        f"[`{func_text}`{routine_str}]({file_name}#{anchor})",
                        line
                    )
                    fixes += 1
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # Fix the main document anchor
    content = re.sub(
        r'\[KotOR NSS File Format Documentation\]\(#kotor-nss-file-format-documentation\)',
        r'[KotOR NSS File Format Documentation](#kotor-nss-files-format-documentation)',
        content
    )
    
    if content != original_content:
        NSS_FILE.write_text(content, encoding='utf-8')
        print(f"Fixed TOC links in NSS-File-Format.md")
    
    return fixes

if __name__ == "__main__":
    fixes = fix_toc_links()
    print(f"Total fixes: {fixes}")

