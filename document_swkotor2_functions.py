#!/usr/bin/env python3
"""
Script to document functions from swkotor2.exe.re.txt in Ghidra project.

This script parses the reverse engineering text file and prepares documentation
commands for the Ghidra MCP server. It can be run once the Ghidra MCP server
is connected and the project is open.

Usage:
    python document_swkotor2_functions.py
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional


def parse_function_line(line: str) -> Optional[Tuple[str, str, str, int]]:
    """
    Parse a line from the reverse engineering file.
    
    Format: function_name\taddress\tsignature\tline_count
    
    Returns:
        Tuple of (function_name, address, signature, line_count) or None if invalid
    """
    parts = line.strip().split('\t')
    if len(parts) < 4:
        return None
    
    func_name = parts[0].strip()
    address = parts[1].strip()
    signature = parts[2].strip()
    try:
        line_count = int(parts[3].strip())
    except ValueError:
        line_count = 0
    
    return (func_name, address, signature, line_count)


def format_address(address: str) -> str:
    """Format address to 0x format if needed."""
    if address.startswith('0x'):
        return address
    # Assume it's a hex string without 0x prefix
    return f"0x{address}"


def create_comment(func_name: str, signature: str, line_count: int) -> str:
    """Create a documentation comment for the function."""
    comment = f"Function: {func_name}\n"
    comment += f"Signature: {signature}\n"
    comment += f"Lines: {line_count}"
    return comment


def main():
    """Main function to process the reverse engineering file."""
    # Path to the reverse engineering file
    re_file = Path(r"c:\Users\boden\OneDrive\Documents\swkotor2.exe.re.txt")
    
    if not re_file.exists():
        print(f"Error: File not found: {re_file}")
        return
    
    functions: List[Tuple[str, str, str, int]] = []
    
    print(f"Reading {re_file}...")
    with open(re_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            parsed = parse_function_line(line)
            if parsed:
                functions.append(parsed)
            else:
                print(f"Warning: Could not parse line {line_num}: {line[:80]}")
    
    print(f"\nParsed {len(functions)} functions")
    
    # Generate documentation commands
    print("\nGenerating documentation commands...")
    
    # Create output file with commands
    output_file = Path("ghidra_documentation_commands.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Ghidra MCP Documentation Commands\n")
        f.write("# Generated from swkotor2.exe.re.txt\n")
        f.write("# These commands should be executed via Ghidra MCP server\n\n")
        
        for func_name, address, signature, line_count in functions:
            formatted_addr = format_address(address)
            comment = create_comment(func_name, signature, line_count)
            
            # Write command to set decompiler comment
            f.write(f"# Function: {func_name} @ {formatted_addr}\n")
            f.write(f"# Signature: {signature}\n")
            f.write(f"# Lines: {line_count}\n")
            f.write(f"# mcp_ghidra_set_decompiler_comment(address=\"{formatted_addr}\", comment=\"{comment}\")\n")
            f.write(f"# mcp_ghidra_set_function_prototype(function_address=\"{formatted_addr}\", prototype=\"{signature}\")\n")
            f.write("\n")
    
    print(f"\nDocumentation commands written to: {output_file}")
    
    # Also create a Python script that can be used with the MCP server
    script_file = Path("apply_ghidra_documentation.py")
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write("#!/usr/bin/env python3\n")
        f.write('"""\n')
        f.write("Script to apply documentation to Ghidra project via MCP server.\n")
        f.write("This requires the Ghidra MCP server to be running and connected.\n")
        f.write('"""\n\n')
        f.write("from typing import List, Tuple\n\n")
        f.write("# Function data: (name, address, signature, line_count)\n")
        f.write("FUNCTIONS: List[Tuple[str, str, str, int]] = [\n")
        
        for func_name, address, signature, line_count in functions:
            formatted_addr = format_address(address)
            # Escape quotes in strings
            escaped_name = func_name.replace('"', '\\"')
            escaped_sig = signature.replace('"', '\\"')
            f.write(f'    ("{escaped_name}", "{formatted_addr}", "{escaped_sig}", {line_count}),\n')
        
        f.write("]\n\n")
        f.write("""
def format_address(address: str) -> str:
    \"\"\"Format address to 0x format if needed.\"\"\"
    if address.startswith('0x'):
        return address
    return f"0x{address}"


def create_comment(func_name: str, signature: str, line_count: int) -> str:
    \"\"\"Create a documentation comment for the function.\"\"\"
    comment = f"Function: {func_name}\\n"
    comment += f"Signature: {signature}\\n"
    comment += f"Lines: {line_count}"
    return comment


# Example usage:
# This would be called via the MCP server once connected
# for func_name, address, signature, line_count in FUNCTIONS:
#     formatted_addr = format_address(address)
#     comment = create_comment(func_name, signature, line_count)
#     # mcp_ghidra_set_decompiler_comment(address=formatted_addr, comment=comment)
#     # mcp_ghidra_set_function_prototype(function_address=formatted_addr, prototype=signature)
""")
    
    print(f"Python script written to: {script_file}")
    print(f"\nTotal functions to document: {len(functions)}")
    print("\nNext steps:")
    print("1. Ensure Ghidra MCP server is running and connected")
    print("2. Open the 'Andastra Ghidra Project.gpr' project in Ghidra")
    print("3. Run the documentation commands or use the Python script")


if __name__ == "__main__":
    main()
