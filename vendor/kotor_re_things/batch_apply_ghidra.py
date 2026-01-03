#!/usr/bin/env python3
"""
Batch apply Kotor RE Things data to Ghidra.

This script processes the JSON and generates batches of MCP calls.
Since MCP tools must be called through the AI interface, this script
outputs the data in a format that can be systematically applied.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict


def load_data(json_path: Path) -> Dict:
    """Load parsed data."""
    with open(json_path, "r") as f:
        return json.load(f)


def get_important_comments(data: Dict, limit: int = 100) -> List[Dict]:
    """Get important comments (pre/plate types with meaningful text)."""
    comments = data.get("comments", [])
    important = []
    for c in comments:
        if c.get("type") in ["pre", "plate"] and len(c.get("text", "")) > 10:
            important.append(c)
            if len(important) >= limit:
                break
    return important


def get_functions_with_names(data: Dict, limit: int = 1000) -> List[Dict]:
    """Get functions that have meaningful names (not just FUN_ addresses)."""
    functions = data.get("functions", [])
    named = []
    for f in functions:
        name = f.get("name", "")
        # Skip if name looks like an auto-generated name
        if name and not name.startswith("FUN_") and "::" in name:
            named.append(f)
            if len(named) >= limit:
                break
    return named


def format_address(addr: int) -> str:
    """Format address for Ghidra."""
    return f"0x{addr:08x}"


def generate_comment_batch(comments: List[Dict], batch_num: int) -> str:
    """Generate a batch of comment applications."""
    lines = [f"# Comment Batch {batch_num}"]
    lines.append("")
    for i, comment in enumerate(comments):
        addr = format_address(comment["address"])
        text = comment["text"].replace("\n", " ").replace("\r", "")[:200]
        lines.append(f"# {i + 1}. {addr}: {text[:60]}...")
    return "\n".join(lines)


def generate_function_batch(functions: List[Dict], batch_num: int) -> str:
    """Generate a batch of function applications."""
    lines = [f"# Function Batch {batch_num}"]
    lines.append("")
    for i, func in enumerate(functions):
        addr = format_address(func["address"])
        name = func["name"]
        lines.append(f"# {i + 1}. {addr}: {name}")
        if func.get("return_type"):
            lines.append(f"#    Return: {func['return_type']}")
        if func.get("parameters"):
            lines.append(f"#    Params: {len(func['parameters'])}")
    return "\n".join(lines)


def main():
    """Main function."""
    json_path = Path(__file__).parent / "kotor_re_parsed.json"

    if not json_path.exists():
        print(f"Error: {json_path} not found")
        return 1

    print("Loading data...")
    data = load_data(json_path)

    print("\nGenerating batches...")

    # Get important comments
    important_comments = get_important_comments(data, limit=200)
    print(f"Important comments: {len(important_comments)}")

    # Get functions with names
    named_functions = get_functions_with_names(data, limit=500)
    print(f"Named functions: {len(named_functions)}")

    # Generate output
    output = []
    output.append("=" * 80)
    output.append("Kotor RE Things - Ghidra Integration Batches")
    output.append("=" * 80)
    output.append("")
    output.append("Total items to apply:")
    output.append(f"  Comments: {len(important_comments)}")
    output.append(f"  Functions: {len(named_functions)}")
    output.append("")

    # Comment batches (20 per batch)
    batch_size = 20
    for i in range(0, len(important_comments), batch_size):
        batch = important_comments[i : i + batch_size]
        output.append(generate_comment_batch(batch, i // batch_size + 1))
        output.append("")

    # Function batches (50 per batch)
    batch_size = 50
    for i in range(0, len(named_functions), batch_size):
        batch = named_functions[i : i + batch_size]
        output.append(generate_function_batch(batch, i // batch_size + 1))
        output.append("")

    output_path = Path(__file__).parent / "ghidra_batches.txt"
    with open(output_path, "w") as f:
        f.write("\n".join(output))

    print(f"\nGenerated batch file: {output_path}")
    print(f"  Comment batches: {(len(important_comments) + 19) // 20}")
    print(f"  Function batches: {(len(named_functions) + 49) // 50}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
