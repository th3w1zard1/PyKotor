#!/usr/bin/env python3
"""Fix all NSS-File-Format.md TOC links to point to correct files."""

from __future__ import annotations

import re

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
NSS_FILE = WIKI_DIR / "NSS-File-Format.md"

# Map function prefixes to their files (order matters - more specific first)
FUNCTION_FILE_MAP = {
    # Abilities and Stats
    "GetAbility": "NSS-Shared-Functions-Abilities-and-Stats",
    "SetAbility": "NSS-Shared-Functions-Abilities-and-Stats",
    "GetNPC": "NSS-Shared-Functions-Abilities-and-Stats",
    "SetNPC": "NSS-Shared-Functions-Abilities-and-Stats",
    "SWMG_Start": "NSS-Shared-Functions-Abilities-and-Stats",
    # Actions
    "Action": "NSS-Shared-Functions-Actions",
    # Alignment
    "AdjustAlignment": "NSS-Shared-Functions-Alignment-System",
    "GetAlignment": "NSS-Shared-Functions-Alignment-System",
    "GetFactionAverageGoodEvil": "NSS-Shared-Functions-Alignment-System",
    "VersusAlignment": "NSS-Shared-Functions-Alignment-System",
    # Class System
    "AddMultiClass": "NSS-Shared-Functions-Class-System",
    "GetClass": "NSS-Shared-Functions-Class-System",
    "GetFactionMostFrequentClass": "NSS-Shared-Functions-Class-System",
    "GetLevelByClass": "NSS-Shared-Functions-Class-System",
    # Combat
    "CancelCombat": "NSS-Shared-Functions-Combat-Functions",
    "CutsceneAttack": "NSS-Shared-Functions-Combat-Functions",
    "GetAttack": "NSS-Shared-Functions-Combat-Functions",
    "GetAttemptedAttack": "NSS-Shared-Functions-Combat-Functions",
    "GetFirstAttacker": "NSS-Shared-Functions-Combat-Functions",
    "GetGoingToBeAttackedBy": "NSS-Shared-Functions-Combat-Functions",
    "GetIsInCombat": "NSS-Shared-Functions-Combat-Functions",
    "GetLastAttack": "NSS-Shared-Functions-Combat-Functions",
    "GetLastAttacker": "NSS-Shared-Functions-Combat-Functions",
    "GetLastDamager": "NSS-Shared-Functions-Combat-Functions",
    # Dialog and Conversation
    "BarkString": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "BeginConversation": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "CancelPostDialog": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "EventConversation": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "GetIsConversation": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "GetIsInConversation": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "GetLastConversation": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "GetLastSpeaker": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "HoldWorldFadeInForDialog": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "ResetDialog": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "SetDialog": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "SetLockHeadFollowInDialog": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "SetLockOrientationInDialog": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "SpeakOneLinerConversation": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    "SpeakString": "NSS-Shared-Functions-Dialog-and-Conversation-Functions",
    # Module and Area (more specific patterns first)
    "GetAreaOfEffectCreator": "NSS-Shared-Functions-Module-and-Area-Functions",
    "GetModuleItemAcquired": "NSS-Shared-Functions-Module-and-Area-Functions",
    "GetModuleItemAcquiredFrom": "NSS-Shared-Functions-Module-and-Area-Functions",
    "GetModuleItemLost": "NSS-Shared-Functions-Module-and-Area-Functions",
    "GetModuleItemLostBy": "NSS-Shared-Functions-Module-and-Area-Functions",
    "GetModule": "NSS-Shared-Functions-Module-and-Area-Functions",
    "SetModule": "NSS-Shared-Functions-Module-and-Area-Functions",
    "GetArea": "NSS-Shared-Functions-Module-and-Area-Functions",
    # Object Query and Manipulation
    "GetObject": "NSS-Shared-Functions-Object-Query-and-Manipulation",
    "SetObject": "NSS-Shared-Functions-Object-Query-and-Manipulation",
    # Party Management
    "GetParty": "NSS-Shared-Functions-Party-Management",
    "SetParty": "NSS-Shared-Functions-Party-Management",
    # Player Character
    "GetPC": "NSS-Shared-Functions-Player-Character-Functions",
    "SetPC": "NSS-Shared-Functions-Player-Character-Functions",
    # Skills and Feats
    "GetSkill": "NSS-Shared-Functions-Skills-and-Feats",
    "SetSkill": "NSS-Shared-Functions-Skills-and-Feats",
    "GetFeat": "NSS-Shared-Functions-Skills-and-Feats",
    # Sound and Music
    "GetSound": "NSS-Shared-Functions-Sound-and-Music-Functions",
    "SetSound": "NSS-Shared-Functions-Sound-and-Music-Functions",
    "PlaySound": "NSS-Shared-Functions-Sound-and-Music-Functions",
    # Effects (more specific patterns first)
    "EnableVideoEffect": "NSS-Shared-Functions-Effects-System",
    "DisableVideoEffect": "NSS-Shared-Functions-Effects-System",
    "GetFirstEffect": "NSS-Shared-Functions-Effects-System",
    "GetHasFeatEffect": "NSS-Shared-Functions-Effects-System",
    "GetHasSpellEffect": "NSS-Shared-Functions-Effects-System",
    "GetIsEffectValid": "NSS-Shared-Functions-Effects-System",
    "GetNextEffect": "NSS-Shared-Functions-Effects-System",
    "GetIsWeaponEffective": "NSS-Shared-Functions-Effects-System",
    "PlayVisualAreaEffect": "NSS-Shared-Functions-Effects-System",
    "MagicalEffect": "NSS-Shared-Functions-Effects-System",
    "SupernaturalEffect": "NSS-Shared-Functions-Effects-System",
    "ExtraordinaryEffect": "NSS-Shared-Functions-Effects-System",
    "VersusRacialTypeEffect": "NSS-Shared-Functions-Effects-System",
    "VersusTrapEffect": "NSS-Shared-Functions-Effects-System",
    "GetEffect": "NSS-Shared-Functions-Effects-System",
    "SetEffect": "NSS-Shared-Functions-Effects-System",
    "RemoveEffect": "NSS-Shared-Functions-Effects-System",
    "Effect": "NSS-Shared-Functions-Effects-System",
    # Global Variables
    "GetGlobal": "NSS-Shared-Functions-Global-Variables",
    "SetGlobal": "NSS-Shared-Functions-Global-Variables",
    # Item Management (more specific patterns first)
    "ChangeItemCost": "NSS-Shared-Functions-Item-Management",
    "EventActivateItem": "NSS-Shared-Functions-Item-Management",
    "GetBaseItemType": "NSS-Shared-Functions-Item-Management",
    "GetFirstItemInInventory": "NSS-Shared-Functions-Item-Management",
    "GetNextItemInInventory": "NSS-Shared-Functions-Item-Management",
    "GetInventoryDisturbItem": "NSS-Shared-Functions-Item-Management",
    "GetLastItemEquipped": "NSS-Shared-Functions-Item-Management",
    "GetNumStackedItems": "NSS-Shared-Functions-Item-Management",
    "GetSpellCastItem": "NSS-Shared-Functions-Item-Management",
    "GetItem": "NSS-Shared-Functions-Item-Management",
    "SetItem": "NSS-Shared-Functions-Item-Management",
    "CreateItem": "NSS-Shared-Functions-Item-Management",
    "DestroyItem": "NSS-Shared-Functions-Item-Management",
    # SWMG functions in specific files
    "SWMG_GetPlayer": "NSS-Shared-Functions-Player-Character-Functions",
    "SWMG_SetPlayer": "NSS-Shared-Functions-Player-Character-Functions",
    "SWMG_IsPlayer": "NSS-Shared-Functions-Player-Character-Functions",
    "SWMG_GetSound": "NSS-Shared-Functions-Sound-and-Music-Functions",
    "SWMG_SetSound": "NSS-Shared-Functions-Sound-and-Music-Functions",
    "SWMG_PlayAnimation": "NSS-Shared-Functions-Sound-and-Music-Functions",
    "SWMG_GetObject": "NSS-Shared-Functions-Object-Query-and-Manipulation",
    "SWMG_SetSpeedBlur": "NSS-Shared-Functions-Effects-System",
    # Other (catch-all - must be last)
    "Get": "NSS-Shared-Functions-Other-Functions",
    "Set": "NSS-Shared-Functions-Other-Functions",
}

# Build comprehensive function mapping
def build_function_map() -> dict[str, tuple[str, str]]:
    """Build mapping from function name to (file_name, anchor)."""
    function_map: dict[str, tuple[str, str]] = {}
    FUNCTION_FILES: list[str] = [
        "NSS-Shared-Functions-Abilities-and-Stats.md",
        "NSS-Shared-Functions-Actions.md",
        "NSS-Shared-Functions-Alignment-System.md",
        "NSS-Shared-Functions-Class-System.md",
        "NSS-Shared-Functions-Combat-Functions.md",
        "NSS-Shared-Functions-Dialog-and-Conversation-Functions.md",
        "NSS-Shared-Functions-Effects-System.md",
        "NSS-Shared-Functions-Global-Variables.md",
        "NSS-Shared-Functions-Item-Management.md",
        "NSS-Shared-Functions-Item-Properties.md",
        "NSS-Shared-Functions-Local-Variables.md",
        "NSS-Shared-Functions-Module-and-Area-Functions.md",
        "NSS-Shared-Functions-Object-Query-and-Manipulation.md",
        "NSS-Shared-Functions-Other-Functions.md",
        "NSS-Shared-Functions-Party-Management.md",
        "NSS-Shared-Functions-Player-Character-Functions.md",
        "NSS-Shared-Functions-Skills-and-Feats.md",
        "NSS-Shared-Functions-Sound-and-Music-Functions.md",
    ]
    
    for func_file in FUNCTION_FILES:
        file_path = WIKI_DIR / func_file
        if not file_path.exists():
            continue
        
        content = file_path.read_text(encoding='utf-8')
        file_name = func_file.replace('.md', '')
        
        # Find all HTML anchors and their following headings
        for match in re.finditer(r'<a id="([^"]+)"></a>\s*\n\s*##\s+`([^(]+)\(', content):
            anchor = match.group(1)
            func_name = match.group(2)
            function_map[func_name] = (file_name, anchor)
    
    return function_map

FUNCTION_MAP = build_function_map()

def get_function_file_and_anchor(func_name: str) -> tuple[str, str] | None:
    """Get the file name and anchor for a function.
    
    Returns: (file_name, anchor) or None if not found
    """
    # First try exact match from comprehensive map
    if func_name in FUNCTION_MAP:
        return FUNCTION_MAP[func_name]
    
    # Fallback to prefix-based mapping (for functions not yet indexed)
    for prefix, file_name in FUNCTION_FILE_MAP.items():
        if func_name.startswith(prefix):
            # Generate anchor from function name
            return file_name, func_name.lower()
    
    return None


def normalize_function_name(text: str) -> str:
    """Extract function name from TOC link text."""
    match = re.match(r"`([^(]+)\(", text)
    if match:
        return match.group(1)
    return ""


def fix_toc_links():
    """Fix TOC links in NSS-File-Format.md."""
    content: str = NSS_FILE.read_text(encoding="utf-8")
    original_content: str = content
    fixes: int = 0
    lines: list[str] = content.splitlines()
    new_lines: list[str] = []

    for line_num, line in enumerate(lines, 1):
        parsed_line = line
        # Match lines with function links: - [`Function(params)` - Routine N](#anchor or file)
        # Pattern: backtick, function name, backtick, optional routine, link
        if "`" in parsed_line and ("Routine" in parsed_line or "](NSS-" in parsed_line):
            # Extract function name
            func_match: re.Match[str] | None = re.search(r"`([^(]+)\(", parsed_line)
            if func_match:
                func_name: str = func_match.group(1)
                # Extract routine number if present
                routine_match: re.Match[str] | None = re.search(r"Routine\s+(\d+)", parsed_line)
                routine_num: str | None = routine_match.group(1) if routine_match else None
                # Extract the full function text in backticks
                func_text_match: re.Match[str] | None = re.search(r"`([^`]+)`", parsed_line)
                func_text: str = func_text_match.group(1) if func_text_match else func_name

                # Get target file and anchor
                result: tuple[str, str] | None = get_function_file_and_anchor(func_name)
                if result:
                    file_name: str = result[0]
                    anchor: str = result[1]
                    routine_str: str = f" - Routine {routine_num}" if routine_num else ""

                    # Check if link already points to a file with wrong anchor or wrong file
                    # Match pattern: [text](file#anchor)
                    link_pattern: str = r"\[`[^`]+`[^\]]*\]\(([^#\)]+)(?:#([^\)]+))?\)"
                    match: re.Match[str] | None = re.search(link_pattern, parsed_line)
                    if match:
                        current_file: str = match.group(1)
                        current_anchor: str | None = match.group(2) if match.lastindex and match.lastindex >= 2 else None

                        # Fix if file is wrong or anchor is wrong
                        if current_file != file_name or (current_anchor and current_anchor != anchor):
                            parsed_line = re.sub(link_pattern, f"[`{func_text}`{routine_str}]({file_name}#{anchor})", parsed_line)
                            fixes += 1
                    elif "](#" in parsed_line:
                        # Replace anchor link with file link + anchor
                        parsed_line = re.sub(r"\[`[^`]+`[^\]]*\]\([^\)]+\)", f"[`{func_text}`{routine_str}]({file_name}#{anchor})", parsed_line)
                        fixes += 1
                    elif f"]({file_name})" in parsed_line:
                        # Add anchor to existing file link
                        parsed_line = parsed_line.replace(f"]({file_name})", f"]({file_name}#{anchor})")
                        fixes += 1
                # If result is None, keep the original line unchanged (no continue)

        new_lines.append(parsed_line)

    content = "\n".join(new_lines)

    # Fix the main document anchor
    content = re.sub(
        r"\[KotOR NSS File Format Documentation\]\(#kotor-nss-file-format-documentation\)",
        r"[KotOR NSS File Format Documentation](#kotor-nss-files-format-documentation)",
        content,
    )

    if content != original_content:
        NSS_FILE.write_text(content, encoding="utf-8")
        print("Fixed TOC links in NSS-File-Format.md")

    return fixes


if __name__ == "__main__":
    fixes = fix_toc_links()
    print(f"Total fixes: {fixes}")
