from __future__ import annotations

from pathlib import Path

from utility.system.os_helper import is_frozen


def get_help_file_path(relative_path: str) -> Path | None:
    """Resolve a help file path from multiple possible locations.
    
    Searches in the following order:
    1. ./help (for packaged help files)
    2. ./wiki (for wiki documentation)
    3. ./vendor/xoreos-docs (for xoreos documentation)
    
    Also handles frozen/packaged scenarios where files may be in different locations.
    
    Args:
        relative_path: Relative path to the help file (e.g., "bioware-docs/Bioware_Aurora_Conversation_Format.md" or "GFF-File-Format.md")
    
    Returns:
        Resolved Path to the file if found, None otherwise.
    """
    # Normalize the path (handle both forward and backslashes)
    relative_path = relative_path.replace("\\", "/")
    
    # Get base paths to search
    search_paths: list[Path] = []
    
    if is_frozen():
        # When frozen, check relative to executable
        import sys
        exe_path = Path(sys.executable).parent
        search_paths.extend([
            exe_path / "help",
            exe_path / "wiki",
            exe_path / "vendor" / "xoreos-docs",
        ])
    
    # Development mode: check multiple locations
    # Try to find the repository root
    current_file = Path(__file__)
    # From help_paths.py: Tools/HolocronToolset/src/toolset/gui/windows/help_paths.py
    # Go up to repo root: Tools/HolocronToolset/src/toolset/gui/windows -> repo root
    repo_root = current_file.parent.parent.parent.parent.parent.parent
    
    search_paths.extend([
        repo_root / "Tools" / "HolocronToolset" / "src" / "toolset" / "help",
        repo_root / "wiki",
        repo_root / "vendor" / "xoreos-docs",
        # Also check relative to current working directory
        Path("./help"),
        Path("./wiki"),
        Path("./vendor/xoreos-docs"),
    ])
    
    # Try each search path
    for base_path in search_paths:
        if not base_path.exists():
            continue
        
        # Try direct path
        file_path = base_path / relative_path
        if file_path.exists() and file_path.is_file():
            return file_path
        
        # If relative_path contains a subdirectory (e.g., "bioware-docs/file.md"),
        # also try just the filename in the base directory
        if "/" in relative_path or "\\" in relative_path:
            filename = Path(relative_path).name
            file_path = base_path / filename
            if file_path.exists() and file_path.is_file():
                return file_path
    
    return None


def get_help_base_paths() -> list[Path]:
    """Get all base paths where help files might be located.
    
    Returns:
        List of Path objects for help file base directories.
    """
    base_paths: list[Path] = []
    
    if is_frozen():
        import sys
        exe_path = Path(sys.executable).parent
        base_paths.extend([
            exe_path / "help",
            exe_path / "wiki",
            exe_path / "vendor" / "xoreos-docs",
        ])
    
    # Development mode
    current_file = Path(__file__)
    repo_root = current_file.parent.parent.parent.parent.parent.parent
    
    base_paths.extend([
        repo_root / "Tools" / "HolocronToolset" / "src" / "toolset" / "help",
        repo_root / "wiki",
        repo_root / "vendor" / "xoreos-docs",
        Path("./help"),
        Path("./wiki"),
        Path("./vendor/xoreos-docs"),
    ])
    
    # Return only existing paths
    return [p for p in base_paths if p.exists()]

