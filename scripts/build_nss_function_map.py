#!/usr/bin/env python3
"""Build comprehensive function-to-file-and-anchor mapping from NSS function files."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"

# All NSS function files
FUNCTION_FILES = [
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

def extract_function_anchors(file_path: Path) -> dict[str, str]:
    """Extract function name to anchor mapping from a file.
    
    Returns: Dict mapping function name to HTML anchor ID
    """
    content = file_path.read_text(encoding='utf-8')
    mappings = {}
    
    # Find all HTML anchors and their following headings
    for match in re.finditer(r'<a id="([^"]+)"></a>\s*\n\s*##\s+`([^(]+)\(', content):
        anchor = match.group(1)
        func_name = match.group(2)
        mappings[func_name] = anchor
    
    return mappings

def build_function_map() -> dict[str, tuple[str, str]]:
    """Build mapping from function name to (file_name, anchor).
    
    Returns: Dict mapping function name to (file_name_without_ext, anchor)
    """
    function_map = {}
    
    for func_file in FUNCTION_FILES:
        file_path = WIKI_DIR / func_file
        if not file_path.exists():
            continue
        
        file_name = func_file.replace('.md', '')
        anchors = extract_function_anchors(file_path)
        
        for func_name, anchor in anchors.items():
            function_map[func_name] = (file_name, anchor)
    
    return function_map

def main():
    """Main entry point."""
    function_map = build_function_map()
    print(f"Found {len(function_map)} functions")
    
    # Print a sample
    for func_name, (file_name, anchor) in list(function_map.items())[:10]:
        print(f"{func_name} -> {file_name}#{anchor}")
    
    return function_map

if __name__ == "__main__":
    main()

