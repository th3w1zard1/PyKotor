#!/usr/bin/env python3
"""Fix section links with -1 suffix in NSS-File-Format.md."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
NSS_FILE = WIKI_DIR / "NSS-File-Format.md"

def fix_section_links():
    """Fix section links with -1 suffix."""
    content = NSS_FILE.read_text(encoding='utf-8')
    original_content = content
    fixes = 0
    
    # Fix section links with -1 suffix (they should point to the actual section anchors)
    # Pattern: [Section Name](#section-name-1) -> [Section Name](#section-name)
    section_patterns = [
        (r'\[Actions\]\(#actions-1\)', '[Actions](#actions)'),
        (r'\[Class System\]\(#class-system-1\)', '[Class System](#class-system)'),
        (r'\[Combat Functions\]\(#combat-functions-1\)', '[Combat Functions](#combat-functions)'),
        (r'\[Dialog and Conversation Functions\]\(#dialog-and-conversation-functions-1\)', '[Dialog and Conversation Functions](#dialog-and-conversation-functions)'),
        (r'\[Effects System\]\(#effects-system-1\)', '[Effects System](#effects-system)'),
        (r'\[Global Variables\]\(#global-variables-1\)', '[Global Variables](#global-variables)'),
        (r'\[Item Management\]\(#item-management-1\)', '[Item Management](#item-management)'),
        (r'\[Other Functions\]\(#other-functions-1\)', '[Other Functions](#other-functions)'),
    ]
    
    for pattern, replacement in section_patterns:
        if pattern in content:
            content = re.sub(pattern, replacement, content)
            fixes += content.count(replacement) - original_content.count(replacement)
    
    # Fix function links that are just anchor links without file references
    # Pattern: [`FunctionName(params)`](#functionnameparams) should be fixed by the main fix script
    # But we can fix ones that are clearly TSL-only functions
    
    if content != original_content:
        NSS_FILE.write_text(content, encoding='utf-8')
        print(f"Fixed {fixes} section links in NSS-File-Format.md")
    else:
        print("No fixes needed")
    
    return fixes

if __name__ == "__main__":
    fix_section_links()

