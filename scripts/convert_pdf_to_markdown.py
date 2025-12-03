#!/usr/bin/env python3
"""
Convert Bioware Aurora PDF documentation to Markdown format for wiki integration.

This script converts PDF files from vendor/nwn-docs to markdown format,
preserving structure and formatting as much as possible.
"""

import sys
from pathlib import Path

try:
    import pymupdf  # PyMuPDF (fitz)  # type: ignore[import-not-found, note]
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pdfplumber  # type: ignore[import-not-found, note]
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


def convert_pdf_pymupdf(pdf_path: Path, output_path: Path) -> bool:
    """Convert PDF to markdown using PyMuPDF."""
    try:
        doc = pymupdf.open(pdf_path)  # type: ignore[attr-defined]
        markdown_content = []
        
        # Add header with title
        title = pdf_path.stem.replace("Bioware_Aurora_", "").replace("_Format", "").replace("_", " ")
        markdown_content.append(f"# {title}\n")
        markdown_content.append("*Official Bioware Aurora Documentation*\n\n")
        markdown_content.append("---\n\n")
        
        for page_num, page in enumerate(doc, 1):
            # Extract plain text
            text = page.get_text()
            # Basic markdown formatting: preserve line breaks and format headings
            if text.strip():
                lines = text.split('\n')
                formatted_lines = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        formatted_lines.append('')
                    elif line.isupper() and len(line) > 3 and len(line) < 80:  # Likely a heading
                        formatted_lines.append(f"### {line}\n")
                    else:
                        formatted_lines.append(line)
                text = '\n'.join(formatted_lines)
            
            if text.strip():
                markdown_content.append(f"## Page {page_num}\n\n")
                markdown_content.append(text)
                markdown_content.append("\n\n")
        
        doc.close()
        
        output_path.write_text("".join(markdown_content), encoding="utf-8")
        return True
    except Exception as e:
        print(f"Error converting {pdf_path} with PyMuPDF: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def convert_pdf_pdfplumber(pdf_path: Path, output_path: Path) -> bool:
    """Convert PDF to markdown using pdfplumber."""
    try:
        markdown_content = []
        
        # Add header with title
        title = pdf_path.stem.replace("Bioware_Aurora_", "").replace("_Format", "").replace("_", " ")
        markdown_content.append(f"# {title}\n")
        markdown_content.append("*Official Bioware Aurora Documentation*\n\n")
        markdown_content.append("---\n\n")
        
        with pdfplumber.open(pdf_path) as pdf:  # type: ignore[attr-defined]
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    markdown_content.append(f"## Page {page_num}\n\n")
                    # Basic text extraction - preserve line breaks
                    text = text.replace("\n\n", "\n\n")
                    markdown_content.append(text)
                    markdown_content.append("\n\n")
        
        output_path.write_text("".join(markdown_content), encoding="utf-8")
        return True
    except Exception as e:
        print(f"Error converting {pdf_path} with pdfplumber: {e}", file=sys.stderr)
        return False


def convert_pdf_simple(pdf_path: Path, output_path: Path) -> bool:
    """Fallback: Create a placeholder markdown file with instructions."""
    title = pdf_path.stem.replace("Bioware_Aurora_", "").replace("_Format", "").replace("_", " ")
    content = f"""# {title}

*Official Bioware Aurora Documentation*

---

**Note:** This document needs to be converted from PDF. The original PDF is available at `{pdf_path.relative_to(Path.cwd())}`.

To convert this PDF to markdown, install one of the following Python packages:

- `pip install pymupdf` (recommended - better formatting preservation)
- `pip install pdfplumber`

Then run: `python scripts/convert_pdf_to_markdown.py`
"""
    output_path.write_text(content, encoding="utf-8")
    return True


def main():
    """Main conversion function."""
    repo_root = Path(__file__).parent.parent
    nwn_docs_dir = repo_root / "vendor" / "nwn-docs"
    wiki_dir = repo_root / "wiki"
    
    if not nwn_docs_dir.exists():
        print(f"Error: {nwn_docs_dir} does not exist. Please initialize the submodule first:")
        print(f"  git submodule update --init --recursive vendor/nwn-docs")
        sys.exit(1)
    
    if not wiki_dir.exists():
        print(f"Error: {wiki_dir} does not exist.")
        sys.exit(1)
    
    # Find all PDF files
    pdf_files = list(nwn_docs_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {nwn_docs_dir}")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDF files to convert")
    
    # Determine which library to use
    converter = None
    if HAS_PYMUPDF:
        converter = convert_pdf_pymupdf
        print("Using PyMuPDF for conversion")
    elif HAS_PDFPLUMBER:
        converter = convert_pdf_pdfplumber
        print("Using pdfplumber for conversion")
    else:
        print("Warning: No PDF conversion library found. Creating placeholder files.")
        print("Install pymupdf or pdfplumber: pip install pymupdf")
        converter = convert_pdf_simple
    
    # Convert each PDF
    converted = 0
    for pdf_file in pdf_files:
        # Generate markdown filename
        md_name = pdf_file.stem.replace("Bioware_Aurora_", "").replace("_Format", "")
        md_name = "Bioware-Aurora-" + md_name.replace("_", "-") + ".md"
        md_path = wiki_dir / md_name
        
        print(f"Converting {pdf_file.name} -> {md_path.name}")
        
        if converter(pdf_file, md_path):
            converted += 1
        else:
            print(f"  Failed to convert {pdf_file.name}")
    
    print(f"\nConverted {converted}/{len(pdf_files)} files")
    
    if converted < len(pdf_files) and not HAS_PYMUPDF and not HAS_PDFPLUMBER:
        print("\nTo complete conversion, install a PDF library:")
        print("  pip install pymupdf")
        print("Then run this script again.")


if __name__ == "__main__":
    main()

