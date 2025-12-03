#!/usr/bin/env python3
"""
Script to apply Kotor RE Things data to Ghidra via MCP tools.

This script reads the parsed JSON and applies:
- Function names and prototypes
- Symbol names
- Data type definitions
- Comments

Note: Addresses may differ between GOG and Steam versions.
"""

from __future__ import annotations

import json
import sys

from pathlib import Path
from typing import Any

# This script is meant to be run interactively or integrated with MCP calls
# The actual MCP tool calls need to be made through the AI assistant


def load_parsed_data(json_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load parsed data from JSON."""
    with open(json_path, "r") as f:
        return json.load(f)


def format_address(addr: int) -> str:
    """Format address as hex string for Ghidra."""
    return f"0x{addr:08x}"


def generate_ghidra_commands(data: dict[str, list[dict[str, Any]]], output_file: Path, batch_size: int = 100):
    """Generate a script with Ghidra MCP commands to apply the data."""

    commands: list[str] = []
    commands.append("# Generated Ghidra MCP integration commands")
    commands.append("# Apply these using the Ghidra MCP server")
    commands.append("")

    # Apply functions
    functions: list[dict[str, Any]] = data.get("functions", [])
    commands.append(f"# Functions: {len(functions)}")
    commands.append("")

    for i, func in enumerate(functions):
        addr = format_address(func["address"])
        name = func["name"]

        # Escape name for shell
        name_escaped = name.replace('"', '\\"')  # noqa: F841

        # Build prototype if available
        prototype = None
        if func.get("return_type"):
            return_type = func["return_type"]
            params = []
            for param in func.get("parameters", []):
                param_type = param.get("type", "void")
                param_name = param.get("name", "")
                if param_name:
                    params.append(f"{param_type} {param_name}")
                else:
                    params.append(param_type)
            if not params:
                params = ["void"]
            prototype = f"{return_type} {name}({', '.join(params)})"

        commands.append(f"# Function {i + 1}/{len(functions)}: {name}")
        commands.append(f"# Address: {addr}")
        if prototype:
            commands.append(f"# Prototype: {prototype}")
        commands.append("")

        if (i + 1) % batch_size == 0:
            commands.append(f"# Batch {i // batch_size + 1} complete")
            commands.append("")

    # Apply symbols
    symbols: list[dict[str, Any]] = data.get("symbols", [])
    commands.append(f"# Symbols: {len(symbols)}")
    commands.append("")

    for i, sym in enumerate(symbols[:1000]):  # Limit for now
        addr = format_address(sym["address"])
        name = sym["name"]
        commands.append(f"# Symbol {i + 1}: {name} at {addr}")
        if (i + 1) % batch_size == 0:
            commands.append("")

    # Apply comments
    comments: list[dict[str, Any]] = data.get("comments", [])
    commands.append(f"# Comments: {len(comments)}")
    commands.append("")

    for i, comment in enumerate(comments):
        addr = format_address(comment["address"])
        text = comment["text"].replace("\n", " ").replace("\r", "")
        comment_type = comment.get("type", "end-of-line")
        commands.append(f"# Comment {i + 1}: {text[:50]}... at {addr} (type: {comment_type})")
        if (i + 1) % batch_size == 0:
            commands.append("")

    # Write to file
    with open(output_file, "w") as f:
        f.write("\n".join(commands))

    print(f"Generated command file: {output_file}")
    print(f"  Functions: {len(functions)}")
    print(f"  Symbols: {len(symbols)}")
    print(f"  Comments: {len(comments)}")


def main():
    """Main function."""
    json_path = Path(__file__).parent / "kotor_re_parsed.json"
    output_path = Path(__file__).parent / "ghidra_commands.txt"

    if not json_path.exists():
        print(f"Error: JSON file not found at {json_path}")
        print("Run apply_ghidra_integration.py first to generate the JSON file.")
        return 1

    print("Loading parsed data...")
    data: dict[str, list[dict[str, Any]]] = load_parsed_data(json_path)

    print("Generating Ghidra command file...")
    generate_ghidra_commands(data, output_path)

    print("\nNote: This script generates a reference file.")
    print("The actual integration must be done through Ghidra MCP tool calls.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
