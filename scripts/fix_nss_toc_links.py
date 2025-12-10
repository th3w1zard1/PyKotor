#!/usr/bin/env python3
"""Fix NSS-File-Format.md TOC links to point to correct files and anchors."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
NSS_FILE = WIKI_DIR / "NSS-File-Format.md"

# Map function names to their file and anchor
FUNCTION_MAPPINGS = {
    # Abilities and Stats
    "GetAbilityModifier": ("NSS-Shared-Functions-Abilities-and-Stats", "getabilitymodifier"),
    "GetAbilityScore": ("NSS-Shared-Functions-Abilities-and-Stats", "getabilityscore"),
    "GetNPCSelectability": ("NSS-Shared-Functions-Abilities-and-Stats", "getnpcselectability"),
    "SetNPCSelectability": ("NSS-Shared-Functions-Abilities-and-Stats", "setnpcselectability"),
    "SWMG_StartInvulnerability": ("NSS-Shared-Functions-Abilities-and-Stats", "swmg_startinvulnerability"),
    # Actions - map to Actions file
    "ActionAttack": ("NSS-Shared-Functions-Actions", None),
    "ActionBarkString": ("NSS-Shared-Functions-Actions", None),
    "ActionCastFakeSpellAtLocation": ("NSS-Shared-Functions-Actions", None),
    "ActionCastFakeSpellAtObject": ("NSS-Shared-Functions-Actions", None),
    "ActionCastSpellAtLocation": ("NSS-Shared-Functions-Actions", None),
    "ActionCastSpellAtObject": ("NSS-Shared-Functions-Actions", None),
    "ActionCloseDoor": ("NSS-Shared-Functions-Actions", None),
    "ActionDoCommand": ("NSS-Shared-Functions-Actions", None),
    "ActionEquipItem": ("NSS-Shared-Functions-Actions", None),
    "ActionEquipMostDamagingMelee": ("NSS-Shared-Functions-Actions", None),
    "ActionEquipMostDamagingRanged": ("NSS-Shared-Functions-Actions", None),
    "ActionFollowLeader": ("NSS-Shared-Functions-Actions", None),
    "ActionForceFollowObject": ("NSS-Shared-Functions-Actions", None),
    "ActionForceMoveToLocation": ("NSS-Shared-Functions-Actions", None),
    "ActionForceMoveToObject": ("NSS-Shared-Functions-Actions", None),
}

def normalize_function_name(text: str) -> str:
    """Extract function name from TOC link text."""
    # Pattern: `FunctionName(params)` - Routine N
    match = re.match(r'`([^(]+)\(', text)
    if match:
        return match.group(1)
    return ""

def fix_toc_links():
    """Fix TOC links in NSS-File-Format.md."""
    content = NSS_FILE.read_text(encoding='utf-8')
    original_content = content
    fixes = 0
    
    # Pattern matches TOC links like [`FunctionName(params)` - Routine N](#anchor)
    def fix_link(match):
        nonlocal fixes
        full_link_text = match.group(0)
        link_text = match.group(1)  # The text inside backticks
        routine_num = match.group(2)  # Routine number (optional, can be None)
        link_url = match.group(3)  # URL
        
        # Only fix same-file anchors that look like function references
        if link_url and link_url.startswith('#') and len(link_url) > 20:  # Function anchors are long
            func_name = normalize_function_name(link_text)
            if func_name and func_name in FUNCTION_MAPPINGS:
                file_name, anchor = FUNCTION_MAPPINGS[func_name]
                routine_part = f" - Routine {routine_num}" if routine_num else ""
                if anchor:
                    fixes += 1
                    # Preserve the full link text format
                    return f"[`{link_text}`{routine_part}]({file_name}#{anchor})"
                else:
                    # Just point to the file
                    fixes += 1
                    return f"[`{link_text}`{routine_part}]({file_name})"
        
        return full_link_text
    
    # Fix function links in TOC - match pattern: [`Function(params)` - Routine N](#anchor)
    # Group 1: function name, Group 2: routine number (optional), Group 3: anchor URL
    pattern = r'\[`([^`]+)`(?:\s+-\s+Routine\s+(\d+))?\]\(([^\)]+)\)'
    content = re.sub(pattern, fix_link, content)
    
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

