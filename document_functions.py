#!/usr/bin/env python3
"""
Script to generate function documentation commands for Ghidra REVA MCP.
This processes swkotor2.exe.re.txt and generates manage-comments calls.
"""

import re

def parse_function_file(filepath):
    """Parse the function list file."""
    functions = []
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                name = parts[0]
                addr = parts[1]
                sig = parts[2]
                line_count = parts[3]
                functions.append((name, addr, sig, line_count))
    return functions

def generate_comment_calls(functions, start_idx=0, batch_size=50):
    """Generate MCP manage-comments calls for functions."""
    calls = []
    for i in range(start_idx, min(start_idx + batch_size, len(functions))):
        name, addr, sig, line_count = functions[i]
        # Format address with 0x prefix
        addr_hex = f"0x{addr}"
        comment = f"Function signature: {sig} | Line count: {line_count}"
        calls.append((addr_hex, comment))
    return calls

if __name__ == "__main__":
    filepath = r"c:\Users\boden\OneDrive\Documents\swkotor2.exe.re.txt"
    functions = parse_function_file(filepath)
    print(f"Total functions: {len(functions)}")
    
    # Generate first batch
    batch = generate_comment_calls(functions, 0, 50)
    print(f"\nFirst batch (0-49): {len(batch)} functions")
    for addr, comment in batch[:5]:
        print(f"  {addr}: {comment[:60]}...")
