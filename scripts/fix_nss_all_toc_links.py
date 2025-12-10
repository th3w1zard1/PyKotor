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
    # Module and Area
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
    # Effects
    "Effect": "NSS-Shared-Functions-Effects-System",
    "GetEffect": "NSS-Shared-Functions-Effects-System",
    "SetEffect": "NSS-Shared-Functions-Effects-System",
    "RemoveEffect": "NSS-Shared-Functions-Effects-System",
    # Global Variables
    "GetGlobal": "NSS-Shared-Functions-Global-Variables",
    "SetGlobal": "NSS-Shared-Functions-Global-Variables",
    # Item Management
    "GetItem": "NSS-Shared-Functions-Item-Management",
    "SetItem": "NSS-Shared-Functions-Item-Management",
    "CreateItem": "NSS-Shared-Functions-Item-Management",
    "DestroyItem": "NSS-Shared-Functions-Item-Management",
    # Other (catch-all - must be last)
    "Get": "NSS-Shared-Functions-Other-Functions",
    "Set": "NSS-Shared-Functions-Other-Functions",
}


def get_function_file(func_name: str) -> str | None:
    """Get the file name for a function."""
    for prefix, file_name in FUNCTION_FILE_MAP.items():
        if func_name.startswith(prefix):
            return file_name
    return "NSS-Shared-Functions-Other-Functions"  # Default


def normalize_function_name(text: str) -> str:
    """Extract function name from TOC link text."""
    match = re.match(r"`([^(]+)\(", text)
    if match:
        return match.group(1)
    return ""


def fix_toc_links():
    """Fix TOC links in NSS-File-Format.md."""
    content = NSS_FILE.read_text(encoding="utf-8")
    original_content = content
    fixes = 0
    lines = content.splitlines()
    new_lines = []

    for line in lines:
        original_line = line
        # Match lines with function links: - [`Function(params)` - Routine N](#anchor or file)
        # Pattern: backtick, function name, backtick, optional routine, link
        if "`" in line and ("Routine" in line or "](NSS-" in line):
            # Extract function name
            func_match = re.search(r"`([^(]+)\(", line)
            if func_match:
                func_name = func_match.group(1)
                # Extract routine number if present
                routine_match = re.search(r"Routine\s+(\d+)", line)
                routine_num = routine_match.group(1) if routine_match else None
                # Extract the full function text in backticks
                func_text_match = re.search(r"`([^`]+)`", line)
                func_text = func_text_match.group(1) if func_text_match else func_name

                # Get target file
                file_name = get_function_file(func_name)
                routine_str = f" - Routine {routine_num}" if routine_num else ""

                # Create anchor from function name (lowercase, preserve underscores to match HTML anchor format)
                anchor = func_name.lower()

                # Check if link already points to a file with wrong anchor or wrong file
                # Match pattern: [text](file#anchor)
                link_pattern = r"\[`[^`]+`[^\]]*\]\(([^#\)]+)(?:#([^\)]+))?\)"
                match = re.search(link_pattern, line)
                if match:
                    current_file = match.group(1)
                    current_anchor = match.group(2) if match.lastindex >= 2 else None

                    # Fix if file is wrong or anchor is wrong
                    if current_file != file_name or (current_anchor and current_anchor != anchor):
                        line = re.sub(link_pattern, f"[`{func_text}`{routine_str}]({file_name}#{anchor})", line)
                        fixes += 1
                elif "](#" in line:
                    # Replace anchor link with file link + anchor
                    line = re.sub(r"\[`[^`]+`[^\]]*\]\([^\)]+\)", f"[`{func_text}`{routine_str}]({file_name}#{anchor})", line)
                    fixes += 1
                elif f"]({file_name})" in line:
                    # Add anchor to existing file link
                    line = line.replace(f"]({file_name})", f"]({file_name}#{anchor})")
                    fixes += 1

        new_lines.append(line)

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
