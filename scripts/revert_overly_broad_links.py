#!/usr/bin/env python3
"""Revert overly broad hyperlinks that were incorrectly added to common words."""

from __future__ import annotations

import re
from pathlib import Path

# All replacement patterns from REVERT_OVERLY_BROAD_LINKS.md
REPLACEMENTS = [
    # type
    (r"\[type\]\(GFF-File-Format#data-types\)", "type"),
    (r"\[type\]\(GFF-File-Format#gff-data-types\)", "type"),
    # value
    (r"\[value\]\(GFF-File-Format#data-types\)", "value"),
    (r"\[value\]\(GFF-File-Format#gff-data-types\)", "value"),
    # values
    (r"\[values\]\(GFF-File-Format#data-types\)", "values"),
    (r"\[values\]\(GFF-File-Format#gff-data-types\)", "values"),
    # field
    (r"\[field\]\(GFF-File-Format#file-structure\)", "field"),
    # fields
    (r"\[fields\]\(GFF-File-Format#file-structure\)", "fields"),
    # format
    (r"\[format\]\(GFF-File-Format\)", "format"),
    # formats
    (r"\[formats\]\(GFF-File-Format\)", "formats"),
    # file
    (r"\[file\]\(GFF-File-Format\)", "file"),
    # files
    (r"\[files\]\(GFF-File-Format\)", "files"),
    # data
    (r"\[data\]\(GFF-File-Format#file-structure\)", "data"),
    # structure
    (r"\[structure\]\(GFF-File-Format#file-structure\)", "structure"),
    # structures
    (r"\[structures\]\(GFF-File-Format#file-structure\)", "structures"),
    # string
    (r"\[string\]\(GFF-File-Format#cexostring\)", "string"),
    (r"\[string\]\(GFF-File-Format#gff-data-types\)", "string"),
    # strings
    (r"\[strings\]\(GFF-File-Format#cexostring\)", "strings"),
    (r"\[strings\]\(GFF-File-Format#gff-data-types\)", "strings"),
    # array
    (r"\[array\]\(2DA-File-Format\)", "array"),
    # arrays
    (r"\[arrays\]\(2DA-File-Format\)", "arrays"),
    # index
    (r"\[index\]\(2DA-File-Format#row-labels\)", "index"),
    # indexes
    (r"\[indexes\]\(2DA-File-Format#row-labels\)", "indexes"),
    # indices
    (r"\[indices\]\(2DA-File-Format#row-labels\)", "indices"),
    # vector
    (r"\[vector\]\(GFF-File-Format#vector\)", "vector"),
    (r"\[vector\]\(GFF-File-Format#gff-data-types\)", "vector"),
    # vectors
    (r"\[vectors\]\(GFF-File-Format#vector\)", "vectors"),
    (r"\[vectors\]\(GFF-File-Format#gff-data-types\)", "vectors"),
    # color
    (r"\[color\]\(GFF-File-Format#color\)", "color"),
    (r"\[color\]\(GFF-File-Format#gff-data-types\)", "color"),
    # colors
    (r"\[colors\]\(GFF-File-Format#color\)", "colors"),
    (r"\[colors\]\(GFF-File-Format#gff-data-types\)", "colors"),
    # count
    (r"\[count\]\(GFF-File-Format#file-structure\)", "count"),
    # size
    (r"\[size\]\(GFF-File-Format#file-structure\)", "size"),
    # offset
    (r"\[offset\]\(GFF-File-Format#file-structure\)", "offset"),
    # offsets
    (r"\[offsets\]\(GFF-File-Format#file-structure\)", "offsets"),
    # pointer
    (r"\[pointer\]\(GFF-File-Format#file-structure\)", "pointer"),
    # pointers
    (r"\[pointers\]\(GFF-File-Format#file-structure\)", "pointers"),
    # header
    (r"\[header\]\(GFF-File-Format#file-header\)", "header"),
    # headers
    (r"\[headers\]\(GFF-File-Format#file-header\)", "headers"),
    # flag
    (r"\[flag\]\(GFF-File-Format#data-types\)", "flag"),
    # flags
    (r"\[flags\]\(GFF-File-Format#data-types\)", "flags"),
    # bit
    (r"\[bit\]\(GFF-File-Format#data-types\)", "bit"),
    # bits
    (r"\[bits\]\(GFF-File-Format#data-types\)", "bits"),
    # mask
    (r"\[mask\]\(GFF-File-Format#data-types\)", "mask"),
    # masks
    (r"\[masks\]\(GFF-File-Format#data-types\)", "masks"),
    # bitmask
    (r"\[bitmask\]\(GFF-File-Format#data-types\)", "bitmask"),
    # bitmasks
    (r"\[bitmasks\]\(GFF-File-Format#data-types\)", "bitmasks"),
    # matrix
    (r"\[matrix\]\(BWM-File-Format#vertex-data-processing\)", "matrix"),
    # matrices
    (r"\[matrices\]\(BWM-File-Format#vertex-data-processing\)", "matrices"),
    # coordinate
    (r"\[coordinate\]\(GFF-File-Format#are-area\)", "coordinate"),
    # coordinates
    (r"\[coordinates\]\(GFF-File-Format#are-area\)", "coordinates"),
    # position
    (r"\[position\]\(MDL-MDX-File-Format#node-header\)", "position"),
    # positions
    (r"\[positions\]\(MDL-MDX-File-Format#node-header\)", "positions"),
    # orientation
    (r"\[orientation\]\(MDL-MDX-File-Format#node-header\)", "orientation"),
    # orientations
    (r"\[orientations\]\(MDL-MDX-File-Format#node-header\)", "orientations"),
    # rotation
    (r"\[rotation\]\(MDL-MDX-File-Format#node-header\)", "rotation"),
    # rotations
    (r"\[rotations\]\(MDL-MDX-File-Format#node-header\)", "rotations"),
    # transformation
    (r"\[transformation\]\(BWM-File-Format#vertex-data-processing\)", "transformation"),
    # transformations
    (r"\[transformations\]\(BWM-File-Format#vertex-data-processing\)", "transformations"),
    # scale
    (r"\[scale\]\(MDL-MDX-File-Format#node-header\)", "scale"),
    # types
    (r"\[types\]\(GFF-File-Format#data-types\)", "types"),
    (r"\[types\]\(GFF-File-Format#gff-data-types\)", "types"),
    # Additional variations with different anchors
    (r"\[data\]\(GFF-File-Format#file-structure-overview\)", "data"),
    (r"\[field\]\(GFF-File-Format#file-structure-overview\)", "field"),
    (r"\[fields\]\(GFF-File-Format#file-structure-overview\)", "fields"),
    (r"\[count\]\(GFF-File-Format#file-structure-overview\)", "count"),
    (r"\[size\]\(GFF-File-Format#file-structure-overview\)", "size"),
    (r"\[offset\]\(GFF-File-Format#file-structure-overview\)", "offset"),
    (r"\[offsets\]\(GFF-File-Format#file-structure-overview\)", "offsets"),
    (r"\[structure\]\(GFF-File-Format#file-structure-overview\)", "structure"),
    (r"\[structures\]\(GFF-File-Format#file-structure-overview\)", "structures"),
]


def should_skip_file(filename: str) -> bool:
    """Skip certain files."""
    skip_patterns = ["Bioware-Aurora-"]
    return any(pattern in filename for pattern in skip_patterns)


def process_file(filepath: Path) -> int:
    """Process a single file."""
    try:
        content = filepath.read_text(encoding="utf-8")
        original = content
        changes = 0

        for pattern, replacement in REPLACEMENTS:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                count = len(re.findall(pattern, content))
                changes += count
                content = new_content

        if content != original:
            filepath.write_text(content, encoding="utf-8")
            return changes
        return 0
    except Exception as e:
        print(f"Error processing {filepath.name}: {e}")
        import traceback

        traceback.print_exc()
        return 0


def main() -> None:
    """Main entry point."""
    wiki_dir = Path("wiki")
    if not wiki_dir.exists():
        print(f"Error: {wiki_dir} does not exist")
        return

    total_changes = 0
    processed_files = 0

    for md_file in sorted(wiki_dir.glob("*.md")):
        if should_skip_file(md_file.name):
            continue

        changes = process_file(md_file)
        if changes > 0:
            print(f"Processed {md_file.name}: {changes} replacements")
            processed_files += 1
            total_changes += changes

    print(f"\nTotal: {processed_files} file(s) processed, {total_changes} replacement(s) made")


if __name__ == "__main__":
    main()

