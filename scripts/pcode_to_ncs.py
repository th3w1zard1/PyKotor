#!/usr/bin/env python3
"""Convert pcode disassembly files back to binary NCS.

This script parses the pcode text format produced by nwnnsscomp -d
and reconstructs the original binary NCS file.

Usage:
    python pcode_to_ncs.py <pcode_file> [--output <output_file>]
"""

from __future__ import annotations

import argparse
import re
import struct
from pathlib import Path
from typing import List, Tuple

# NCS opcode definitions
OPCODES = {
    "CPDOWNSP": 0x01, "CPTOPSP": 0x03, "CONST": 0x04, "ACTION": 0x05,
    "LOGANDII": 0x06, "LOGORII": 0x07, "INCORII": 0x08, "EXCORII": 0x09,
    "BOOLANDII": 0x0A, "EQII": 0x0B, "NEQII": 0x0C, "GEQII": 0x0D,
    "GTII": 0x0E, "LTII": 0x0F, "LEQII": 0x10, "SHLEFTII": 0x11,
    "SHRIGHTII": 0x12, "USHRIGHTII": 0x13, "ADDII": 0x14, "SUBII": 0x15,
    "MULII": 0x16, "DIVII": 0x17, "MODII": 0x18, "NEGII": 0x19,
    "COMPI": 0x1A, "MOVSP": 0x1B, "STORESTATEALL": 0x1C, "JMP": 0x1D,
    "JSR": 0x1E, "JZ": 0x1F, "RETN": 0x20, "DESTRUCT": 0x21,
    "NOTI": 0x22, "DECISP": 0x23, "INCISP": 0x24, "CPDOWNBP": 0x25,
    "CPTOPBP": 0x26, "DECIBP": 0x27, "INCIBP": 0x28, "SAVEBP": 0x2A,
    "RESTOREBP": 0x2B, "STORESTATE": 0x2C, "NOP": 0x2D, "T": 0x42,
    # Additional variants
    "RSADDI": (0x02, 0x03), "RSADDF": (0x02, 0x04), "RSADDS": (0x02, 0x05),
    "RSADDO": (0x02, 0x06), "RSADDEFF": (0x02, 0x10), "RSADDEVT": (0x02, 0x11),
    "RSADDLOC": (0x02, 0x12), "RSADDTAL": (0x02, 0x13),
    "CONSTI": (0x04, 0x03), "CONSTF": (0x04, 0x04), "CONSTS": (0x04, 0x05),
    "CONSTO": (0x04, 0x06),
    # Binary ops with type qualifiers
    "ADDFF": (0x14, 0x21), "ADDFI": (0x14, 0x26), "ADDIF": (0x14, 0x25),
    "ADDSS": (0x14, 0x23), "ADDVV": (0x14, 0x3A),
    "SUBFF": (0x15, 0x21), "SUBFI": (0x15, 0x26), "SUBIF": (0x15, 0x25),
    "SUBVV": (0x15, 0x3A),
    "MULFF": (0x16, 0x21), "MULFI": (0x16, 0x26), "MULIF": (0x16, 0x25),
    "MULFV": (0x16, 0x3B), "MULVF": (0x16, 0x3C),
    "DIVFF": (0x17, 0x21), "DIVFI": (0x17, 0x26), "DIVIF": (0x17, 0x25),
    "DIVVF": (0x17, 0x3C),
    "EQFF": (0x0B, 0x21), "EQSS": (0x0B, 0x23), "EQOO": (0x0B, 0x24),
    "EQEFFEFF": (0x0B, 0x30), "EQEVTEVT": (0x0B, 0x31), "EQLOCLOC": (0x0B, 0x32),
    "EQTALTAL": (0x0B, 0x33),
    "NEQFF": (0x0C, 0x21), "NEQSS": (0x0C, 0x23), "NEQOO": (0x0C, 0x24),
    "GEQFF": (0x0D, 0x21), "GTFF": (0x0E, 0x21), "LTFF": (0x0F, 0x21),
    "LEQFF": (0x10, 0x21),
    "NEGI": (0x19, 0x03), "NEGF": (0x19, 0x04),
    # RSADD without type - needs qualifier from pcode
    "RSADD": 0x02,
}


class Instruction:
    """Represents a single NCS instruction."""
    
    def __init__(self, offset: int, opcode: int, qualifier: int, args: bytes):
        self.offset = offset
        self.opcode = opcode
        self.qualifier = qualifier
        self.args = args
    
    def to_bytes(self) -> bytes:
        """Convert instruction to binary representation."""
        return bytes([self.opcode, self.qualifier]) + self.args
    
    def __repr__(self):
        return f"Instruction(off={self.offset:08X}, op={self.opcode:02X}, qual={self.qualifier:02X}, args={self.args.hex()})"


def parse_pcode_file(pcode_path: Path) -> Tuple[int, List[Instruction]]:
    """Parse a pcode file and return file size and instructions.
    
    Returns:
        Tuple of (file_size, list of Instructions)
    """
    instructions = []
    file_size = 0
    
    # Regex to match instruction lines
    # Format: OFFSET OPCODE QUALIFIER [ARGS...] INSTRUCTION_NAME [HUMAN_READABLE]
    line_pattern = re.compile(
        r'^\s*([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{2})\s+([0-9A-Fa-f]+)\s*(.*?)(?:\s{2,}|\s+[A-Z_])',
        re.IGNORECASE
    )
    
    # Simpler pattern for lines without much whitespace
    simple_pattern = re.compile(
        r'^\s*([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{2})\s+([0-9A-Fa-f]{2,})\s*',
        re.IGNORECASE
    )
    
    with open(pcode_path, 'r', encoding='latin-1') as f:
        for line in f:
            line = line.rstrip('\n\r')
            
            # Skip empty lines, comments, labels
            stripped = line.strip()
            if not stripped or stripped.startswith(';') or stripped.startswith('//'):
                continue
            if stripped.endswith(':') or stripped.startswith('_'):
                continue
            if stripped.startswith('---'):
                continue
                
            # Try to match instruction line
            match = simple_pattern.match(line)
            if not match:
                continue
                
            offset = int(match.group(1), 16)
            opcode = int(match.group(2), 16)
            rest_hex = match.group(3)
            
            # Handle size marker (offset 8, opcode 0x42)
            if offset == 8 and opcode == 0x42:
                # Rest is the file size in hex
                file_size = int(rest_hex, 16)
                continue
            
            # Parse qualifier (first 2 hex chars of rest)
            qualifier = int(rest_hex[:2], 16)
            args_hex = rest_hex[2:]  # Everything after qualifier
            
            # Parse remaining args from the line
            # Look for more hex values in the rest of the line
            remaining = line[match.end():].strip()
            
            # Extract any hex values before the instruction name
            hex_parts = []
            for part in remaining.split():
                # Stop at instruction name or human-readable args
                if part.upper() in OPCODES or part.startswith('"') or part == 'str':
                    break
                # Check if it's hex
                if re.match(r'^[0-9A-Fa-f]+$', part):
                    hex_parts.append(part)
                elif re.match(r'^[A-Z_]', part):
                    break
            
            # Combine all args
            all_args_hex = args_hex + ''.join(hex_parts)
            
            # Handle string constants specially
            if opcode == 0x04 and qualifier == 0x05:  # CONSTS
                # Extract string from the line
                string_match = re.search(r'"([^"]*)"', line)
                if string_match:
                    string_val = string_match.group(1)
                    # Handle escape sequences
                    string_val = string_val.encode('latin-1').decode('unicode_escape').encode('latin-1')
                    # Build args: 2-byte length + string bytes
                    length = len(string_val)
                    args = struct.pack('>H', length) + string_val
                else:
                    # Empty string
                    args = struct.pack('>H', 0)
            else:
                # Parse hex args
                if all_args_hex:
                    # Ensure even number of hex chars
                    if len(all_args_hex) % 2:
                        all_args_hex = '0' + all_args_hex
                    args = bytes.fromhex(all_args_hex)
                else:
                    args = b''
            
            instructions.append(Instruction(offset, opcode, qualifier, args))
    
    return file_size, instructions


def build_ncs_binary(file_size: int, instructions: List[Instruction]) -> bytes:
    """Build binary NCS from instructions.
    
    Args:
        file_size: Expected file size from pcode header
        instructions: List of parsed instructions
    
    Returns:
        Binary NCS data
    """
    # Calculate required size
    if instructions:
        max_end = max(i.offset + 2 + len(i.args) for i in instructions)
    else:
        max_end = 13  # Minimum: header + size marker
    
    # Use the larger of file_size and calculated max
    data_size = max(file_size, max_end)
    
    # Initialize with zeros
    data = bytearray(data_size)
    
    # Write NCS header
    data[0:8] = b'NCS V1.0'
    
    # Write size marker
    data[8] = 0x42
    struct.pack_into('>I', data, 9, data_size)
    
    # Write instructions at their offsets
    for inst in instructions:
        offset = inst.offset
        if offset < len(data):
            data[offset] = inst.opcode
            if offset + 1 < len(data):
                data[offset + 1] = inst.qualifier
            for i, b in enumerate(inst.args):
                if offset + 2 + i < len(data):
                    data[offset + 2 + i] = b
    
    return bytes(data)


def convert_pcode_to_ncs(pcode_path: Path, output_path: Path | None = None) -> Path:
    """Convert a pcode file to binary NCS.
    
    Args:
        pcode_path: Path to pcode text file
        output_path: Optional output path (defaults to same name with .ncs.bin)
    
    Returns:
        Path to output file
    """
    if output_path is None:
        output_path = pcode_path.with_suffix('.ncs.bin')
    
    file_size, instructions = parse_pcode_file(pcode_path)
    print(f"Parsed {len(instructions)} instructions from {pcode_path.name}")
    print(f"Expected file size: {file_size} bytes")
    
    ncs_data = build_ncs_binary(file_size, instructions)
    print(f"Generated binary size: {len(ncs_data)} bytes")
    
    output_path.write_bytes(ncs_data)
    print(f"Wrote {output_path}")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Convert pcode to binary NCS')
    parser.add_argument('pcode_file', type=Path, help='Input pcode file')
    parser.add_argument('--output', '-o', type=Path, help='Output NCS file')
    
    args = parser.parse_args()
    
    convert_pcode_to_ncs(args.pcode_file, args.output)


if __name__ == '__main__':
    main()

