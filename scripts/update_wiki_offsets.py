#!/usr/bin/env python3
"""Update all offset values in wiki files to include both decimal and hex.

This script systematically goes through all wiki markdown files and ensures
that all offset values in tables include both decimal and hexadecimal representations.
"""
import re
import sys
from pathlib import Path

def dec_to_hex(dec_str: str) -> str:
    """Convert decimal string to hex string with 0x prefix."""
    try:
        dec_val = int(dec_str)
        if dec_val < 0:
            # Handle negative offsets (e.g., -1)
            return f"-0x{abs(dec_val):X}"
        return f"0x{dec_val:X}"
    except ValueError:
        return dec_str

def update_offsets_in_file(filepath: Path) -> tuple[bool, list[str]]:
    """Update all offset values in a markdown file.
    
    Returns:
        (modified, changes): Tuple of (bool indicating if file was modified, list of change descriptions)
    """
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        return False, [f"Error reading {filepath}: {e}"]
    
    original_content = content
    changes = []
    
    # Find all table blocks
    lines = content.split('\n')
    modified_lines = []
    in_table = False
    table_headers = []
    header_line_idx = -1
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check if this is a table row
        if stripped.startswith('|') and '|' in stripped[1:]:
            # Check if this is a header row (next line is separator)
            is_separator = False
            if i + 1 < len(lines):
                next_stripped = lines[i + 1].strip()
                if next_stripped.startswith('|') and re.match(r'^\|[\s\-:]+(\|[\s\-:]+)*\|$', next_stripped):
                    is_separator = True
                    # This is the header row
                    table_headers = [h.strip() for h in stripped.split('|')[1:-1]]
                    header_line_idx = i
                    in_table = True
                    modified_lines.append(line)
                    continue
            
            if in_table:
                # This is a data row in a table
                parts = [p.strip() for p in line.split('|')]
                
                # Find offset column index
                offset_col_idx = None
                for idx, header in enumerate(table_headers):
                    if header and 'offset' in header.lower():
                        offset_col_idx = idx
                        break
                
                if offset_col_idx is not None and len(parts) > offset_col_idx + 1:
                    offset_val = parts[offset_col_idx + 1].strip()
                    
                    # Skip if it's an expression (contains operators like +, -, *, /)
                    if re.search(r'[+\-*/]', offset_val):
                        modified_lines.append(line)
                        continue
                    
                    # Check if it already has hex for all numbers
                    # Pattern: number followed by (0x...) - if all numbers have this, skip
                    if re.search(r'\(0x[0-9A-Fa-f-]+\)', offset_val):
                        # Check if ALL numbers have hex
                        all_numbers = re.findall(r'\b(-?\d+)\b', offset_val)
                        all_have_hex = True
                        for num in all_numbers:
                            # Check if this number has a corresponding hex
                            num_pattern = re.escape(num)
                            # Look for pattern: num (0x...)
                            if not re.search(rf'\b{num_pattern}\s*\(0x[0-9A-Fa-f-]+\)', offset_val):
                                all_have_hex = False
                                break
                        
                        if all_have_hex:
                            modified_lines.append(line)
                            continue
                    
                    # Update offset value to include hex for standalone numbers only
                    # Only update if the entire value is just a number (possibly with spaces)
                    if re.match(r'^\s*(-?\d+)\s*$', offset_val):
                        dec_str = offset_val.strip()
                        hex_val = dec_to_hex(dec_str)
                        new_offset_val = f"{dec_str} ({hex_val})"
                        
                        # Preserve original spacing in the line
                        # Find the offset column in the original line
                        pipe_positions = [m.start() for m in re.finditer(r'\|', line)]
                        if len(pipe_positions) > offset_col_idx + 1:
                            # Get the original spacing
                            col_start = pipe_positions[offset_col_idx] + 1
                            col_end = pipe_positions[offset_col_idx + 1]
                            original_col = line[col_start:col_end]
                            
                            # Preserve left spacing, update the value, preserve right spacing
                            left_spaces = len(original_col) - len(original_col.lstrip())
                            right_spaces = len(original_col) - len(original_col.rstrip()) - left_spaces
                            
                            new_col = ' ' * left_spaces + new_offset_val + ' ' * right_spaces
                            new_line = line[:col_start] + new_col + line[col_end:]
                            
                            modified_lines.append(new_line)
                            changes.append(f"Line {i+1}: Updated offset '{offset_val}' -> '{new_offset_val}'")
                            continue
            
            modified_lines.append(line)
        else:
            # Not a table row
            if in_table:
                in_table = False
                table_headers = []
                header_line_idx = -1
            modified_lines.append(line)
    
    new_content = '\n'.join(modified_lines)
    
    if new_content != original_content:
        filepath.write_text(new_content, encoding='utf-8')
        return True, changes
    
    return False, []

def main():
    """Main entry point."""
    wiki_dir = Path(__file__).parent.parent / 'wiki'
    
    if not wiki_dir.exists():
        print(f"Error: {wiki_dir} does not exist")
        sys.exit(1)
    
    total_modified = 0
    total_changes = 0
    
    # Process all markdown files
    for md_file in sorted(wiki_dir.glob('*.md')):
        modified, changes = update_offsets_in_file(md_file)
        if modified:
            total_modified += 1
            total_changes += len(changes)
            print(f"Modified: {md_file.name} ({len(changes)} changes)")
            for change in changes[:10]:  # Show first 10 changes
                print(f"  {change}")
            if len(changes) > 10:
                print(f"  ... and {len(changes) - 10} more")
        else:
            print(f"Skipped: {md_file.name} (no changes needed)")
    
    print(f"\nTotal files modified: {total_modified}")
    print(f"Total changes: {total_changes}")

if __name__ == '__main__':
    main()

