#!/usr/bin/env python3
"""Generate help contents.xml from wiki and xoreos-docs files."""
from __future__ import annotations

import os
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom


def prettify(elem: ET.Element):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, encoding="unicode")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")


def get_wiki_files():
    """Get all markdown files from wiki directory."""
    wiki_path = Path("wiki")
    if not wiki_path.exists():
        return []
    return sorted([f.name for f in wiki_path.glob("*.md")])


def get_xoreos_docs():
    """Get all markdown files from vendor/xoreos-docs."""
    xoreos_path = Path("vendor/xoreos-docs")
    if not xoreos_path.exists():
        return []
    files: list[str] = []
    for md_file in xoreos_path.rglob("*.md"):
        # Get relative path from vendor/xoreos-docs
        rel_path = md_file.relative_to(xoreos_path)
        files.append(str(rel_path).replace("\\", "/"))
    return sorted(files)


def categorize_wiki_files(files: list[str]):
    """Categorize wiki files into logical groups."""
    categories: dict[str, list[str]] = {
        "File Formats": [],
        "2DA Files": [],
        "GFF Files": [],
        "NSS Scripting - Shared Constants": [],
        "NSS Scripting - Shared Functions": [],
        "NSS Scripting - K1 Only": [],
        "NSS Scripting - TSL Only": [],
        "TSLPatcher": [],
        "HoloPatcher": [],
        "Other": [],
    }
    
    for file in files:
        if file.startswith("2DA-") and file != "2DA-File-Format.md":
            categories["2DA Files"].append(file)
        elif file.startswith("GFF-"):
            categories["GFF Files"].append(file)
        elif file.startswith("NSS-Shared-Constants-"):
            categories["NSS Scripting - Shared Constants"].append(file)
        elif file.startswith("NSS-Shared-Functions-"):
            categories["NSS Scripting - Shared Functions"].append(file)
        elif file.startswith("NSS-K1-Only-"):
            categories["NSS Scripting - K1 Only"].append(file)
        elif file.startswith("NSS-TSL-Only-"):
            categories["NSS Scripting - TSL Only"].append(file)
        elif file.startswith("TSLPatcher"):
            categories["TSLPatcher"].append(file)
        elif file.startswith("HoloPatcher") or "HoloPatcher" in file:
            categories["HoloPatcher"].append(file)
        elif any(
            file.startswith(prefix)
            for prefix in [
                "BIF-", "BWM-", "ERF-", "KEY-", "LIP-", "LTR-", "LYT-",
                "MDL-", "NCS-", "NSS-File-Format", "SSF-", "TLK-", "TPC-",
                "TXI-", "VIS-", "WAV-", "Bioware-Aurora-", "Rendering-",
                "Kit-", "Mod-", "Indoor-", "Home.md", "Explanations-",
                "Installing-"
            ]
        ):
            categories["File Formats"].append(file)
        else:
            categories["Other"].append(file)
    
    return categories


def create_document(name: str, file_path: str):
    """Create a Document XML element."""
    doc = ET.Element("Document")
    doc.set("name", name)
    doc.set("file", file_path)
    return doc


def create_folder(name: str, items: list[tuple[str, str]]):
    """Create a Folder XML element with documents."""
    folder = ET.Element("Folder")
    folder.set("name", name)
    for item_name, item_file in items:
        folder.append(create_document(item_name, item_file))
    return folder


def generate_contents_xml():
    """Generate the contents.xml file."""
    root = ET.Element("Contents")
    root.set("version", "4")
    
    # Introduction (existing)
    intro_folder = ET.Element("Folder")
    intro_folder.set("name", "Introduction")
    intro_folder.append(create_document("Getting Started", "introduction1-gettingStarted.md"))
    intro_folder.append(create_document("Core Tab", "introduction2-coreResources.md"))
    intro_folder.append(create_document("Modules Tab", "introduction3-moduleResources.md"))
    intro_folder.append(create_document("Override Tab", "introduction4-overrideResources.md"))
    root.append(intro_folder)
    
    # Tools (existing)
    tools_folder = ET.Element("Folder")
    tools_folder.set("name", "Tools")
    tools_folder.append(create_document("Module Editor", "tools/1-moduleEditor.md"))
    tools_folder.append(create_document("Map Builder", "tools/2-mapBuilder.md"))
    root.append(tools_folder)
    
    # Tutorials (existing)
    tutorials_folder = ET.Element("Folder")
    tutorials_folder.set("name", "Tutorials")
    tutorials_folder.append(create_document("Custom Robes", "tutorials/1-creatingCustomRobes.md"))
    tutorials_folder.append(create_document("New Store", "tutorials/2-creatingANewStore.md"))
    tutorials_folder.append(create_document("Area Transitions", "tutorials/3-areaTransition.md"))
    tutorials_folder.append(create_document("DLG Static Cameras", "tutorials/4-creatingStaticCameras.md"))
    root.append(tutorials_folder)
    
    # Get and categorize wiki files
    wiki_files: list[str] = get_wiki_files()
    categories: dict[str, list[str]] = categorize_wiki_files(wiki_files)
    
    # File Formats
    if categories["File Formats"]:
        formats_folder = ET.Element("Folder")
        formats_folder.set("name", "File Formats")
        for file in sorted(categories["File Formats"]):
            # Create a readable name from filename
            name = file.replace(".md", "").replace("-", " ")
            # Capitalize first letter of each word
            name = " ".join(word.capitalize() for word in name.split())
            formats_folder.append(create_document(name, file))
        root.append(formats_folder)
    
    # 2DA Files
    if categories["2DA Files"]:
        twoda_folder = ET.Element("Folder")
        twoda_folder.set("name", "2DA Files")
        for file in sorted(categories["2DA Files"]):
            name = file.replace(".md", "").replace("2DA-", "").replace("-", " ").title()
            twoda_folder.append(create_document(name, file))
        root.append(twoda_folder)
    
    # GFF Files
    if categories["GFF Files"]:
        gff_folder = ET.Element("Folder")
        gff_folder.set("name", "GFF Files")
        for file in sorted(categories["GFF Files"]):
            name = file.replace(".md", "").replace("GFF-", "").replace("-", " ")
            gff_folder.append(create_document(name, file))
        root.append(gff_folder)
    
    # NSS Scripting folders
    if categories["NSS Scripting - Shared Constants"]:
        nss_const_folder = ET.Element("Folder")
        nss_const_folder.set("name", "NSS Scripting - Shared Constants")
        for file in sorted(categories["NSS Scripting - Shared Constants"]):
            name = file.replace(".md", "").replace("NSS-Shared-Constants-", "").replace("-", " ")
            nss_const_folder.append(create_document(name, file))
        root.append(nss_const_folder)
    
    if categories["NSS Scripting - Shared Functions"]:
        nss_func_folder = ET.Element("Folder")
        nss_func_folder.set("name", "NSS Scripting - Shared Functions")
        for file in sorted(categories["NSS Scripting - Shared Functions"]):
            name = file.replace(".md", "").replace("NSS-Shared-Functions-", "").replace("-", " ")
            nss_func_folder.append(create_document(name, file))
        root.append(nss_func_folder)
    
    if categories["NSS Scripting - K1 Only"]:
        nss_k1_folder = ET.Element("Folder")
        nss_k1_folder.set("name", "NSS Scripting - K1 Only")
        for file in sorted(categories["NSS Scripting - K1 Only"]):
            name = file.replace(".md", "").replace("NSS-K1-Only-", "").replace("-", " ")
            nss_k1_folder.append(create_document(name, file))
        root.append(nss_k1_folder)
    
    if categories["NSS Scripting - TSL Only"]:
        nss_tsl_folder = ET.Element("Folder")
        nss_tsl_folder.set("name", "NSS Scripting - TSL Only")
        for file in sorted(categories["NSS Scripting - TSL Only"]):
            name = file.replace(".md", "").replace("NSS-TSL-Only-", "").replace("-", " ")
            nss_tsl_folder.append(create_document(name, file))
        root.append(nss_tsl_folder)
    
    # TSLPatcher
    if categories["TSLPatcher"]:
        tslpatcher_folder = ET.Element("Folder")
        tslpatcher_folder.set("name", "TSLPatcher")
        for file in sorted(categories["TSLPatcher"]):
            name = file.replace(".md", "").replace("TSLPatcher-", "").replace("TSLPatcher_", "").replace("-", " ").replace("'s", "'s")
            tslpatcher_folder.append(create_document(name, file))
        root.append(tslpatcher_folder)
    
    # HoloPatcher
    if categories["HoloPatcher"]:
        holopatcher_folder = ET.Element("Folder")
        holopatcher_folder.set("name", "HoloPatcher")
        for file in sorted(categories["HoloPatcher"]):
            name = file.replace(".md", "").replace("HoloPatcher-", "").replace("-", " ")
            holopatcher_folder.append(create_document(name, file))
        root.append(holopatcher_folder)
    
    # Other
    if categories["Other"]:
        other_folder = ET.Element("Folder")
        other_folder.set("name", "Other")
        for file in sorted(categories["Other"]):
            name = file.replace(".md", "").replace("-", " ")
            other_folder.append(create_document(name, file))
        root.append(other_folder)
    
    # Xoreos Docs
    xoreos_doc_files: list[os.PathLike] | list[str] = get_xoreos_docs()
    if xoreos_doc_files:
        xoreos_folder = ET.Element("Folder")
        xoreos_folder.set("name", "Xoreos Documentation")
        for file in xoreos_doc_files:
            # Create path relative to help system
            help_path = f"vendor/xoreos-docs/{file}"
            name = Path(file).stem.replace("-", " ").replace("_", " ").title()
            xoreos_folder.append(create_document(name, help_path))
        root.append(xoreos_folder)
    
    return root


def main():
    """Main function."""
    root = generate_contents_xml()
    
    # Write to file
    output_path = Path("Tools/HolocronToolset/src/toolset/help/contents.xml")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prettify and write
    xml_str = prettify(root)
    # Remove the XML declaration line that minidom adds
    lines = xml_str.split("\n")
    if lines[0].startswith("<?xml"):
        lines = lines[1:]
    xml_str = "\n".join(lines).strip()
    
    output_path.write_text(xml_str, encoding="utf-8")
    print(f"Generated {output_path} with {len(list(root))} top-level folders")


if __name__ == "__main__":
    main()

