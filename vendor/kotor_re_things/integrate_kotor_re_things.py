#!/usr/bin/env python3
"""
Script to integrate Kotor RE Things reverse engineering data into Ghidra.

This script parses the XML export from Ghidra (GOG version) and applies:
- Function names and prototypes
- Symbol names
- Data type definitions
- Comments

Note: Addresses may need adjustment for Steam version differences.
"""

import xml.etree.ElementTree as ET
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports if needed
sys.path.insert(0, str(Path(__file__).parent.parent))


def parse_hex_address(addr_str: str) -> int:
    """Parse hex address string to int."""
    if addr_str.startswith("0x"):
        return int(addr_str, 16)
    return int(addr_str, 16)


def format_address_for_ghidra(addr: int) -> str:
    """Format address for Ghidra MCP (0x prefix)."""
    return f"0x{addr:08x}"


def parse_xml_functions(xml_path: Path) -> List[Dict]:
    """Parse FUNCTION entries from XML."""
    functions = []

    print(f"Parsing functions from {xml_path}...")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Find FUNCTIONS element
    functions_elem = root.find(".//FUNCTIONS")
    if functions_elem is None:
        print("Warning: No FUNCTIONS element found in XML")
        return functions

    for func_elem in functions_elem.findall("FUNCTION"):
        entry_point = func_elem.get("ENTRY_POINT")
        name = func_elem.get("NAME")

        if not entry_point or not name:
            continue

        try:
            addr = parse_hex_address(entry_point)
        except ValueError:
            continue

        # Parse return type
        return_type = None
        return_type_elem = func_elem.find("RETURN_TYPE")
        if return_type_elem is not None:
            return_type = return_type_elem.get("DATATYPE")

        # Parse parameters
        parameters = []
        for param_elem in func_elem.findall(".//PARAMETER"):
            param_name = param_elem.get("NAME", "")
            param_type = param_elem.get("DATATYPE", "")
            ordinal = param_elem.get("ORDINAL", "0")
            try:
                ordinal = int(ordinal, 16) if ordinal.startswith("0x") else int(ordinal)
            except ValueError:
                ordinal = 0
            parameters.append({"name": param_name, "type": param_type, "ordinal": ordinal})

        # Sort parameters by ordinal
        parameters.sort(key=lambda x: x["ordinal"])

        # Parse comments
        comments = []
        for comment_elem in func_elem.findall(".//REGULAR_CMT"):
            if comment_elem.text:
                comments.append(comment_elem.text)

        functions.append({"address": addr, "name": name, "return_type": return_type, "parameters": parameters, "comments": comments})

    print(f"Found {len(functions)} functions")
    return functions


def parse_xml_symbols(xml_path: Path) -> List[Dict]:
    """Parse SYMBOL entries from XML."""
    symbols = []

    print(f"Parsing symbols from {xml_path}...")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    symbol_table = root.find(".//SYMBOL_TABLE")
    if symbol_table is None:
        print("Warning: No SYMBOL_TABLE element found in XML")
        return symbols

    for symbol_elem in symbol_table.findall("SYMBOL"):
        address = symbol_elem.get("ADDRESS")
        name = symbol_elem.get("NAME")

        if not address or not name:
            continue

        try:
            addr = parse_hex_address(address)
        except ValueError:
            continue

        symbols.append({"address": addr, "name": name})

    print(f"Found {len(symbols)} symbols")
    return symbols


def parse_xml_data_definitions(xml_path: Path) -> List[Dict]:
    """Parse DEFINED_DATA entries from XML."""
    data_defs = []

    print(f"Parsing data definitions from {xml_path}...")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    data_elem = root.find(".//DATA")
    if data_elem is None:
        print("Warning: No DATA element found in XML")
        return data_defs

    for data_item in data_elem.findall("DEFINED_DATA"):
        address = data_item.get("ADDRESS")
        datatype = data_item.get("DATATYPE")
        size = data_item.get("SIZE")

        if not address or not datatype:
            continue

        try:
            addr = parse_hex_address(address)
            size_val = None
            if size:
                size_val = parse_hex_address(size)
        except ValueError:
            continue

        data_defs.append({"address": addr, "datatype": datatype, "size": size_val})

    print(f"Found {len(data_defs)} data definitions")
    return data_defs


def parse_xml_comments(xml_path: Path) -> List[Dict]:
    """Parse COMMENT entries from XML."""
    comments = []

    print(f"Parsing comments from {xml_path}...")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    comments_elem = root.find(".//COMMENTS")
    if comments_elem is None:
        print("Warning: No COMMENTS element found in XML")
        return comments

    for comment_elem in comments_elem.findall("COMMENT"):
        address = comment_elem.get("ADDRESS")
        comment_type = comment_elem.get("TYPE", "end-of-line")
        text = comment_elem.text

        if not address or not text:
            continue

        try:
            addr = parse_hex_address(address)
        except ValueError:
            continue

        comments.append({"address": addr, "type": comment_type, "text": text.strip()})

    print(f"Found {len(comments)} comments")
    return comments


def build_function_prototype(func: Dict) -> Optional[str]:
    """Build C function prototype string from function data."""
    if not func.get("return_type"):
        return None

    return_type = func["return_type"]
    name = func["name"]

    # Build parameter list
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

    return f"{return_type} {name}({', '.join(params)})"


def main():
    """Main integration function."""
    xml_path = Path(__file__).parent.parent / "vendor" / "Kotor RE Things" / "swkotor.exe.xml"

    if not xml_path.exists():
        print(f"Error: XML file not found at {xml_path}")
        return 1

    print("=" * 80)
    print("Kotor RE Things Integration Script")
    print("=" * 80)
    print()

    # Parse all data from XML
    functions = parse_xml_functions(xml_path)
    symbols = parse_xml_symbols(xml_path)
    data_defs = parse_xml_data_definitions(xml_path)
    comments = parse_xml_comments(xml_path)

    print()
    print("=" * 80)
    print("Summary:")
    print(f"  Functions: {len(functions)}")
    print(f"  Symbols: {len(symbols)}")
    print(f"  Data definitions: {len(data_defs)}")
    print(f"  Comments: {len(comments)}")
    print("=" * 80)
    print()
    print("NOTE: This script parses the data. Use the Ghidra MCP tools to apply it.")
    print("The parsed data is ready for integration via MCP server calls.")
    print()

    # Print sample of what we found
    if functions:
        print("Sample functions:")
        for func in functions[:5]:
            print(f"  {format_address_for_ghidra(func['address'])}: {func['name']}")
            prototype = build_function_prototype(func)
            if prototype:
                print(f"    {prototype}")
        print()

    if symbols:
        print("Sample symbols:")
        for sym in symbols[:5]:
            print(f"  {format_address_for_ghidra(sym['address'])}: {sym['name']}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
