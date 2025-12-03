#!/usr/bin/env python3
"""
Script to apply parsed Kotor RE Things data to Ghidra via MCP.

This script reads the parsed data and applies it to Ghidra.
Note: This requires the Ghidra MCP server to be running and connected.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List
import xml.etree.ElementTree as ET

# Import the parser functions
sys.path.insert(0, str(Path(__file__).parent))
from integrate_kotor_re_things import (
    parse_xml_functions,
    parse_xml_symbols,
    parse_xml_data_definitions,
    parse_xml_comments,
    format_address_for_ghidra,
    build_function_prototype
)


def save_parsed_data(output_path: Path, functions: List[Dict], symbols: List[Dict], 
                     data_defs: List[Dict], comments: List[Dict]):
    """Save parsed data to JSON for later processing."""
    data = {
        'functions': functions,
        'symbols': symbols,
        'data_definitions': data_defs,
        'comments': comments
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved parsed data to {output_path}")


def load_parsed_data(input_path: Path) -> Dict:
    """Load parsed data from JSON."""
    with open(input_path, 'r') as f:
        return json.load(f)


def main():
    """Main function to parse and save data."""
    xml_path = Path(__file__).parent.parent / "vendor" / "Kotor RE Things" / "swkotor.exe.xml"
    output_path = Path(__file__).parent.parent / "scripts" / "kotor_re_parsed.json"
    
    if not xml_path.exists():
        print(f"Error: XML file not found at {xml_path}")
        return 1
    
    print("Parsing XML data...")
    functions = parse_xml_functions(xml_path)
    symbols = parse_xml_symbols(xml_path)
    data_defs = parse_xml_data_definitions(xml_path)
    comments = parse_xml_comments(xml_path)
    
    print(f"\nSaving parsed data to {output_path}...")
    save_parsed_data(output_path, functions, symbols, data_defs, comments)
    
    print("\nParsed data summary:")
    print(f"  Functions: {len(functions)}")
    print(f"  Symbols: {len(symbols)}")
    print(f"  Data definitions: {len(data_defs)}")
    print(f"  Comments: {len(comments)}")
    print(f"\nData saved to: {output_path}")
    print("\nNext step: Use Ghidra MCP tools to apply this data.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

