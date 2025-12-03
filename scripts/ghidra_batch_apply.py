#!/usr/bin/env python3
"""
Generate batched Ghidra MCP commands from Kotor RE Things data.

This script outputs the data in a format ready for batch application.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def load_data() -> dict[str, list[dict[str, Any]]]:
    """Load parsed data."""
    json_path = Path(__file__).parent / "kotor_re_parsed.json"
    with open(json_path, "r") as f:
        return json.load(f)


def format_addr(addr: int) -> str:
    """Format address for Ghidra."""
    return f"0x{addr:08x}"


def get_function_batches(data: dict, batch_size: int = 100) -> list[list[dict]]:
    """Split functions into batches."""
    funcs = data.get("functions", [])
    batches = []
    for i in range(0, len(funcs), batch_size):
        batches.append(funcs[i:i + batch_size])
    return batches


def get_comment_batches(data: dict, batch_size: int = 100) -> list[list[dict]]:
    """Split comments into batches."""
    comments = data.get("comments", [])
    batches = []
    for i in range(0, len(comments), batch_size):
        batches.append(comments[i:i + batch_size])
    return batches


def print_function_batch(batch: list[dict], batch_num: int):
    """Print a batch of functions for MCP application."""
    print(f"\n# Function Batch {batch_num} ({len(batch)} functions)")
    print("# Format: address|name|return_type")
    for func in batch:
        addr = format_addr(func["address"])
        name = func["name"]
        ret_type = func.get("return_type", "")
        print(f"{addr}|{name}|{ret_type}")


def print_comment_batch(batch: list[dict], batch_num: int):
    """Print a batch of comments for MCP application."""
    print(f"\n# Comment Batch {batch_num} ({len(batch)} comments)")
    print("# Format: address|type|text")
    for comment in batch:
        addr = format_addr(comment["address"])
        ctype = comment.get("type", "pre")
        text = comment["text"].replace("\n", " ").replace("\r", "")[:100]
        print(f"{addr}|{ctype}|{text}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python ghidra_batch_apply.py <command> [batch_num]")
        print("Commands:")
        print("  functions [batch] - Print function batch (default: all)")
        print("  comments [batch]  - Print comment batch (default: all)")
        print("  summary           - Print summary of data")
        return 1
    
    data = load_data()
    cmd = sys.argv[1]
    batch_num = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if cmd == "summary":
        funcs = data.get("functions", [])
        comments = data.get("comments", [])
        symbols = data.get("symbols", [])
        data_defs = data.get("data_definitions", [])
        
        print(f"Functions: {len(funcs)}")
        print(f"  Batches (100/batch): {(len(funcs) + 99) // 100}")
        print(f"Comments: {len(comments)}")
        print(f"  Batches (100/batch): {(len(comments) + 99) // 100}")
        print(f"Symbols: {len(symbols)}")
        print(f"Data definitions: {len(data_defs)}")
        
    elif cmd == "functions":
        batches = get_function_batches(data)
        if batch_num is not None:
            if 0 <= batch_num < len(batches):
                print_function_batch(batches[batch_num], batch_num)
            else:
                print(f"Error: Batch {batch_num} out of range (0-{len(batches)-1})")
                return 1
        else:
            for i, batch in enumerate(batches):
                print_function_batch(batch, i)
                
    elif cmd == "comments":
        batches = get_comment_batches(data)
        if batch_num is not None:
            if 0 <= batch_num < len(batches):
                print_comment_batch(batches[batch_num], batch_num)
            else:
                print(f"Error: Batch {batch_num} out of range (0-{len(batches)-1})")
                return 1
        else:
            for i, batch in enumerate(batches):
                print_comment_batch(batch, i)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

