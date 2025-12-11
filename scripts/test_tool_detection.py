#!/usr/bin/env python3
"""Test script to verify tool detection logic."""

import json
from pathlib import Path

tools_dir = Path("Tools")
tools = []

def derive_build_name(name: str) -> str:
    lower = name.lower()
    special = {"holocrontoolset": "toolset"}
    return special.get(lower, lower)

def has_compile_script(build_name: str) -> bool:
    return any(Path(path).exists() for path in [
        f"compile/compile_{build_name}.ps1",
        f"compile/compile_{build_name}.sh",
        f"compile/compile_{build_name}.bat",
    ])

def has_main_entrypoint(tool_path: Path) -> bool:
    """Check if tool has a __main__.py entrypoint that can be compiled with compile_tool.py"""
    # Look for src/<toolname>/__main__.py pattern
    tool_name_lower = tool_path.name.lower()
    main_path = tool_path / "src" / tool_name_lower / "__main__.py"
    if main_path.exists():
        return True
    # Also check for alternative patterns (e.g., holocron_ai vs holocronai)
    src_dir = tool_path / "src"
    if src_dir.exists():
        for src_subdir in src_dir.iterdir():
            if src_subdir.is_dir() and (src_subdir / "__main__.py").exists():
                return True
    return False

if tools_dir.exists():
    for tool_path in sorted(tools_dir.iterdir()):
        if tool_path.is_dir() and not tool_path.name.startswith("."):
            # Skip 'tests' directory - it's not a tool
            if tool_path.name.lower() == "tests":
                print(f"Skipping {tool_path.name}: tests directory")
                continue
            
            build_name = derive_build_name(tool_path.name)
            
            # Check if tool has a compile script OR can use compile_tool.py
            if has_compile_script(build_name):
                # Has explicit compile script
                tools.append({
                    "tool_dir": tool_path.name,
                    "build_name": build_name,
                    "display_name": tool_path.name,
                    "use_compile_tool": False,
                })
            elif has_main_entrypoint(tool_path):
                # Can use compile_tool.py dynamically
                tools.append({
                    "tool_dir": tool_path.name,
                    "build_name": build_name,
                    "display_name": tool_path.name,
                    "use_compile_tool": True,
                })
            else:
                print(f"Skipping {tool_path.name}: no compile script found and no __main__.py entrypoint")
                continue

print("Detected tools:")
for t in tools:
    compile_method = "compile_tool.py" if t['use_compile_tool'] else "explicit script"
    print(f"  - {t['display_name']} (build: {t['build_name']}, method: {compile_method})")

print(f"\nTotal tools: {len(tools)}")

