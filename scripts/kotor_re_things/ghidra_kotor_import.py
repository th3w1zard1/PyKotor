#!/usr/bin/env python3
"""
Ghidra Import Script for KOTOR RE Things

This script imports reverse engineering data from the KOTOR RE Things project
into Ghidra. It parses the XML export and header file to apply:
- Function names and signatures
- Data type definitions (structs, enums)
- Comments
- Symbol names

USAGE:
1. For Ghidra GUI: Run via Script Manager (copy to ghidra_scripts folder)
2. For Ghidra Headless: ghidraRun analyzeHeadless ... -postScript ghidra_kotor_import.py

REQUIREMENTS:
- The target binary must be the GOG version OR an unpacked Steam dump
- The Kotor RE Things files must be in vendor/Kotor RE Things/

NOTE ON STEAM VERSION:
The Steam version of KOTOR has DRM/packing that encrypts the .text section.
To use this script with Steam KOTOR:
1. Run the game
2. Use a memory dumper (like Scylla, pe-sieve, or x64dbg) to dump the unpacked EXE
3. Import the dumped EXE into Ghidra
4. Run this script

Author: PyKotor Project
"""

import xml.etree.ElementTree as ET
import re
import os
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field

# Check if running in Ghidra
try:
    from ghidra.program.model.symbol import SourceType
    from ghidra.program.model.listing import Function
    from ghidra.program.model.data import DataTypeManager
    from ghidra.app.cmd.function import CreateFunctionCmd
    from ghidra.program.flatapi import FlatProgramAPI
    IN_GHIDRA = True
except ImportError:
    IN_GHIDRA = False
    print("Not running in Ghidra - generating standalone data")


@dataclass
class FunctionInfo:
    """Information about a function from KOTOR RE Things."""
    address: int
    name: str
    return_type: Optional[str] = None
    calling_convention: Optional[str] = None
    parameters: list = field(default_factory=list)
    local_vars: list = field(default_factory=list)
    register_vars: list = field(default_factory=list)
    address_ranges: list = field(default_factory=list)
    typeinfo_comment: Optional[str] = None
    regular_comment: Optional[str] = None
    repeatable_comment: Optional[str] = None


@dataclass 
class SymbolInfo:
    """Information about a symbol."""
    address: int
    name: str
    namespace: Optional[str] = None
    symbol_type: Optional[str] = None
    source_type: Optional[str] = None
    is_primary: bool = False


@dataclass
class DataDefinition:
    """Information about a data definition."""
    address: int
    datatype: str
    datatype_namespace: Optional[str] = None
    size: Optional[int] = None


@dataclass
class CommentInfo:
    """Information about a comment."""
    address: int
    comment_type: str
    text: str


@dataclass
class StructField:
    """A field in a struct."""
    name: str
    datatype: str
    offset: int
    size: int


@dataclass
class StructInfo:
    """Information about a struct/class."""
    name: str
    size: int
    fields: list = field(default_factory=list)
    namespace: Optional[str] = None


class KotorREParser:
    """Parser for KOTOR RE Things data files."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.xml_path = self.base_path / "swkotor.exe.xml"
        self.header_path = self.base_path / "swkotor.exe.h"
        
        self.functions: list[FunctionInfo] = []
        self.symbols: list[SymbolInfo] = []
        self.data_definitions: list[DataDefinition] = []
        self.comments: list[CommentInfo] = []
        self.structs: list[StructInfo] = []
        
    def parse_all(self):
        """Parse all available data files."""
        print(f"Parsing KOTOR RE Things from: {self.base_path}")
        
        if self.xml_path.exists():
            print(f"Parsing XML: {self.xml_path}")
            self._parse_xml()
        else:
            print(f"WARNING: XML file not found: {self.xml_path}")
            
        if self.header_path.exists():
            print(f"Parsing header: {self.header_path}")
            self._parse_header()
        else:
            print(f"WARNING: Header file not found: {self.header_path}")
            
        print(f"\nParsed:")
        print(f"  - {len(self.functions)} functions")
        print(f"  - {len(self.symbols)} symbols")
        print(f"  - {len(self.data_definitions)} data definitions")
        print(f"  - {len(self.comments)} comments")
        print(f"  - {len(self.structs)} structs")
        
    def _parse_xml(self):
        """Parse the Ghidra XML export."""
        # Use iterparse for memory efficiency with large files
        context = ET.iterparse(str(self.xml_path), events=('end',))
        
        current_function = None
        
        for event, elem in context:
            tag = elem.tag
            
            if tag == 'FUNCTION':
                func = self._parse_function_element(elem)
                if func:
                    self.functions.append(func)
                elem.clear()
                    
            elif tag == 'SYMBOL':
                sym = self._parse_symbol_element(elem)
                if sym:
                    self.symbols.append(sym)
                elem.clear()
                    
            elif tag == 'DEFINED_DATA':
                data = self._parse_data_element(elem)
                if data:
                    self.data_definitions.append(data)
                elem.clear()
                    
            elif tag == 'COMMENT':
                comment = self._parse_comment_element(elem)
                if comment:
                    self.comments.append(comment)
                elem.clear()
                    
    def _parse_function_element(self, elem) -> Optional[FunctionInfo]:
        """Parse a FUNCTION XML element."""
        entry_point = elem.get('ENTRY_POINT')
        name = elem.get('NAME')
        
        if not entry_point or not name:
            return None
            
        try:
            address = int(entry_point, 16)
        except ValueError:
            return None
            
        func = FunctionInfo(address=address, name=name)
        
        # Parse return type
        ret_type = elem.find('RETURN_TYPE')
        if ret_type is not None:
            func.return_type = ret_type.get('DATATYPE')
            
        # Parse address ranges
        for addr_range in elem.findall('ADDRESS_RANGE'):
            start = addr_range.get('START')
            end = addr_range.get('END')
            if start and end:
                func.address_ranges.append((int(start, 16), int(end, 16)))
                
        # Parse typeinfo comment (contains signature)
        typeinfo = elem.find('TYPEINFO_CMT')
        if typeinfo is not None and typeinfo.text:
            func.typeinfo_comment = typeinfo.text.strip()
            # Extract calling convention
            if '__thiscall' in func.typeinfo_comment:
                func.calling_convention = '__thiscall'
            elif '__stdcall' in func.typeinfo_comment:
                func.calling_convention = '__stdcall'
            elif '__fastcall' in func.typeinfo_comment:
                func.calling_convention = '__fastcall'
            elif '__cdecl' in func.typeinfo_comment:
                func.calling_convention = '__cdecl'
                
        # Parse regular comment
        regular_cmt = elem.find('REGULAR_CMT')
        if regular_cmt is not None and regular_cmt.text:
            func.regular_comment = regular_cmt.text.strip()
            
        # Parse stack frame variables
        stack_frame = elem.find('STACK_FRAME')
        if stack_frame is not None:
            for stack_var in stack_frame.findall('STACK_VAR'):
                var_info = {
                    'name': stack_var.get('NAME'),
                    'offset': stack_var.get('STACK_PTR_OFFSET'),
                    'datatype': stack_var.get('DATATYPE'),
                    'size': stack_var.get('SIZE')
                }
                if var_info['offset'] and var_info['offset'].startswith('-'):
                    func.local_vars.append(var_info)
                else:
                    func.parameters.append(var_info)
                    
        # Parse register variables
        for reg_var in elem.findall('REGISTER_VAR'):
            func.register_vars.append({
                'name': reg_var.get('NAME'),
                'register': reg_var.get('REGISTER'),
                'datatype': reg_var.get('DATATYPE')
            })
            
        return func
        
    def _parse_symbol_element(self, elem) -> Optional[SymbolInfo]:
        """Parse a SYMBOL XML element."""
        address = elem.get('ADDRESS')
        name = elem.get('NAME')
        
        if not address or not name:
            return None
            
        try:
            addr_int = int(address, 16)
        except ValueError:
            return None
            
        return SymbolInfo(
            address=addr_int,
            name=name,
            namespace=elem.get('NAMESPACE'),
            symbol_type=elem.get('TYPE'),
            source_type=elem.get('SOURCE_TYPE'),
            is_primary=elem.get('PRIMARY') == 'y'
        )
        
    def _parse_data_element(self, elem) -> Optional[DataDefinition]:
        """Parse a DEFINED_DATA XML element."""
        address = elem.get('ADDRESS')
        datatype = elem.get('DATATYPE')
        
        if not address or not datatype:
            return None
            
        try:
            addr_int = int(address, 16)
        except ValueError:
            return None
            
        size = elem.get('SIZE')
        size_int = int(size, 16) if size else None
        
        return DataDefinition(
            address=addr_int,
            datatype=datatype,
            datatype_namespace=elem.get('DATATYPE_NAMESPACE'),
            size=size_int
        )
        
    def _parse_comment_element(self, elem) -> Optional[CommentInfo]:
        """Parse a COMMENT XML element."""
        address = elem.get('ADDRESS')
        comment_type = elem.get('TYPE')
        text = elem.text
        
        if not address or not text:
            return None
            
        try:
            addr_int = int(address, 16)
        except ValueError:
            return None
            
        return CommentInfo(
            address=addr_int,
            comment_type=comment_type or 'end-of-line',
            text=text.strip()
        )
        
    def _parse_header(self):
        """Parse the C header file for struct definitions."""
        with open(self.header_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Parse struct definitions
        struct_pattern = re.compile(
            r'struct\s+(\w+)\s*\{([^}]+)\}',
            re.MULTILINE | re.DOTALL
        )
        
        for match in struct_pattern.finditer(content):
            struct_name = match.group(1)
            body = match.group(2)
            
            struct = StructInfo(name=struct_name, size=0, fields=[])
            
            # Parse fields
            field_pattern = re.compile(
                r'(\w+(?:\s*\*)*)\s+(\w+)(?:\[(\d+)\])?;'
            )
            
            offset = 0
            for field_match in field_pattern.finditer(body):
                datatype = field_match.group(1).strip()
                name = field_match.group(2)
                array_size = field_match.group(3)
                
                # Estimate size based on type
                size = self._estimate_type_size(datatype)
                if array_size:
                    size *= int(array_size)
                    
                struct.fields.append(StructField(
                    name=name,
                    datatype=datatype,
                    offset=offset,
                    size=size
                ))
                offset += size
                
            struct.size = offset
            self.structs.append(struct)
            
    def _estimate_type_size(self, datatype: str) -> int:
        """Estimate the size of a data type."""
        # Pointer types
        if '*' in datatype:
            return 4  # 32-bit pointers
            
        # Basic types
        type_sizes = {
            'byte': 1, 'char': 1, 'uchar': 1, 'sbyte': 1, 'bool': 1,
            'undefined': 1, 'undefined1': 1,
            'short': 2, 'ushort': 2, 'word': 2, 'wchar_t': 2,
            'undefined2': 2,
            'int': 4, 'uint': 4, 'long': 4, 'ulong': 4, 'dword': 4,
            'float': 4, 'undefined4': 4, 'DWORD': 4, 'ULONG': 4,
            'double': 8, 'longlong': 8, 'ulonglong': 8,
            'undefined8': 8,
        }
        
        base_type = datatype.replace('struct ', '').replace('enum ', '').strip()
        return type_sizes.get(base_type, 4)  # Default to 4 bytes
        
    def get_functions_by_class(self, class_name: str) -> list[FunctionInfo]:
        """Get all functions belonging to a specific class."""
        return [f for f in self.functions if f.name.startswith(f"{class_name}::")]
        
    def get_function_by_name(self, name: str) -> Optional[FunctionInfo]:
        """Find a function by exact name."""
        for f in self.functions:
            if f.name == name:
                return f
        return None
        
    def search_functions(self, pattern: str) -> list[FunctionInfo]:
        """Search functions by regex pattern."""
        regex = re.compile(pattern, re.IGNORECASE)
        return [f for f in self.functions if regex.search(f.name)]


def create_ghidra_script_output(parser: KotorREParser, output_path: str):
    """Generate a Ghidra Python script that can be run inside Ghidra."""
    
    script = '''# Auto-generated Ghidra script from KOTOR RE Things
# Run this script inside Ghidra's Script Manager

from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import CodeUnit
from ghidra.app.cmd.function import CreateFunctionCmd
from ghidra.program.model.address import AddressSet

def create_function_at(addr_str, name):
    """Create or rename a function."""
    addr = toAddr(addr_str)
    func = getFunctionAt(addr)
    
    if func is None:
        # Try to create the function
        cmd = CreateFunctionCmd(addr)
        if cmd.applyTo(currentProgram):
            func = getFunctionAt(addr)
            
    if func is not None:
        func.setName(name, SourceType.USER_DEFINED)
        return True
    return False

def set_comment(addr_str, comment, comment_type="EOL"):
    """Set a comment at an address."""
    addr = toAddr(addr_str)
    listing = currentProgram.getListing()
    cu = listing.getCodeUnitAt(addr)
    
    if cu is not None:
        if comment_type == "EOL":
            cu.setComment(CodeUnit.EOL_COMMENT, comment)
        elif comment_type == "PRE":
            cu.setComment(CodeUnit.PRE_COMMENT, comment)
        elif comment_type == "POST":
            cu.setComment(CodeUnit.POST_COMMENT, comment)
        elif comment_type == "PLATE":
            cu.setComment(CodeUnit.PLATE_COMMENT, comment)

# Function definitions from KOTOR RE Things
functions = [
'''
    
    # Add function definitions
    for func in parser.functions:
        escaped_name = func.name.replace('\\', '\\\\').replace('"', '\\"')
        script += f'    (0x{func.address:08x}, "{escaped_name}"),\n'
        
    script += ''']

# Apply function names
print("Applying {} function names...".format(len(functions)))
success_count = 0
for addr, name in functions:
    addr_str = "0x{:08x}".format(addr)
    if create_function_at(addr_str, name):
        success_count += 1
        
print("Successfully applied {} of {} function names".format(success_count, len(functions)))

# Comments
comments = [
'''
    
    # Add comments (limit to prevent huge script)
    for comment in parser.comments[:10000]:
        escaped_text = comment.text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        script += f'    (0x{comment.address:08x}, "{comment.comment_type}", "{escaped_text}"),\n'
        
    script += ''']

print("Applying {} comments...".format(len(comments)))
for addr, ctype, text in comments:
    addr_str = "0x{:08x}".format(addr)
    ghidra_type = "EOL"
    if ctype == "pre":
        ghidra_type = "PRE"
    elif ctype == "post":
        ghidra_type = "POST"
    elif ctype == "plate":
        ghidra_type = "PLATE"
    set_comment(addr_str, text, ghidra_type)
    
print("Done!")
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(script)
        
    print(f"Generated Ghidra script: {output_path}")


def create_json_export(parser: KotorREParser, output_path: str):
    """Export parsed data to JSON for use with Ghidra MCP or other tools."""
    import json
    
    data = {
        'functions': [
            {
                'address': f.address,
                'address_hex': f'0x{f.address:08x}',
                'name': f.name,
                'return_type': f.return_type,
                'calling_convention': f.calling_convention,
                'typeinfo_comment': f.typeinfo_comment,
                'regular_comment': f.regular_comment,
                'parameters': f.parameters,
                'local_vars': f.local_vars,
                'register_vars': f.register_vars,
                'address_ranges': [(f'0x{s:08x}', f'0x{e:08x}') for s, e in f.address_ranges]
            }
            for f in parser.functions
        ],
        'symbols': [
            {
                'address': s.address,
                'address_hex': f'0x{s.address:08x}',
                'name': s.name,
                'namespace': s.namespace,
                'type': s.symbol_type,
                'source_type': s.source_type,
                'is_primary': s.is_primary
            }
            for s in parser.symbols
        ],
        'data_definitions': [
            {
                'address': d.address,
                'address_hex': f'0x{d.address:08x}',
                'datatype': d.datatype,
                'namespace': d.datatype_namespace,
                'size': d.size
            }
            for d in parser.data_definitions
        ],
        'comments': [
            {
                'address': c.address,
                'address_hex': f'0x{c.address:08x}',
                'type': c.comment_type,
                'text': c.text
            }
            for c in parser.comments
        ],
        'structs': [
            {
                'name': s.name,
                'size': s.size,
                'namespace': s.namespace,
                'fields': [
                    {
                        'name': f.name,
                        'datatype': f.datatype,
                        'offset': f.offset,
                        'size': f.size
                    }
                    for f in s.fields
                ]
            }
            for s in parser.structs
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    print(f"Exported JSON: {output_path}")
    

def main():
    """Main entry point."""
    import argparse
    
    arg_parser = argparse.ArgumentParser(
        description='Parse KOTOR RE Things and generate Ghidra import data'
    )
    arg_parser.add_argument(
        '--input', '-i',
        default='vendor/Kotor RE Things',
        help='Path to KOTOR RE Things directory'
    )
    arg_parser.add_argument(
        '--output-script', '-s',
        default='scripts/ghidra_kotor_apply.py',
        help='Output path for Ghidra Python script'
    )
    arg_parser.add_argument(
        '--output-json', '-j',
        default='kotor_re_full.json',
        help='Output path for JSON export'
    )
    arg_parser.add_argument(
        '--json-only',
        action='store_true',
        help='Only generate JSON, skip Ghidra script'
    )
    
    args = arg_parser.parse_args()
    
    # Parse the data
    parser = KotorREParser(args.input)
    parser.parse_all()
    
    # Generate outputs
    if not args.json_only:
        create_ghidra_script_output(parser, args.output_script)
        
    create_json_export(parser, args.output_json)
    
    # Print some statistics
    print("\n=== KOTOR RE Things Statistics ===")
    print(f"Total functions: {len(parser.functions)}")
    print(f"Total symbols: {len(parser.symbols)}")
    print(f"Total data definitions: {len(parser.data_definitions)}")
    print(f"Total comments: {len(parser.comments)}")
    print(f"Total structs: {len(parser.structs)}")
    
    # Show class breakdown
    class_counts = {}
    for func in parser.functions:
        if '::' in func.name:
            class_name = func.name.split('::')[0]
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
    print(f"\nTop 20 classes by function count:")
    for class_name, count in sorted(class_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"  {class_name}: {count} functions")


if __name__ == '__main__':
    main()

