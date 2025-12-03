"""Mapping of editors to their wiki documentation files."""

# Editor class name -> wiki markdown filename
EDITOR_WIKI_MAP: dict[str, str | None] = {
    "AREEditor": "GFF-ARE.md",
    "BWMEditor": "BWM-File-Format.md",
    "DLGEditor": "GFF-DLG.md",
    "ERFEditor": "ERF-File-Format.md",
    "GFFEditor": "GFF-File-Format.md",  # Generic GFF editor uses general format doc
    "GITEditor": "GFF-GIT.md",
    "IFOEditor": "GFF-IFO.md",
    "JRLEditor": "GFF-JRL.md",
    "LTREditor": "LTR-File-Format.md",
    "LYTEditor": "LYT-File-Format.md",
    "LIPEditor": "LIP-File-Format.md",
    "MDLEditor": "MDL-MDX-File-Format.md",
    "NSSEditor": "NSS-File-Format.md",
    "NSEditor": "NCS-File-Format.md",  # NCS compiled from NSS
    "PTHEditor": "GFF-PTH.md",
    "SAVEditor": "GFF-File-Format.md",  # Save game uses general GFF format doc
    "SSFEditor": "SSF-File-Format.md",
    "TLKEditor": "TLK-File-Format.md",
    "TPCEditor": "TPC-File-Format.md",
    "TXTEditor": None,  # Plain text, no specific format
    "TwoDAEditor": "2DA-File-Format.md",
    "UTCEditor": "GFF-UTC.md",
    "UTDEditor": "GFF-UTD.md",
    "UTEEditor": "GFF-UTE.md",
    "UTIEditor": "GFF-UTI.md",
    "UTMEditor": "GFF-UTM.md",
    "UTPEditor": "GFF-UTP.md",
    "UTSEditor": "GFF-UTS.md",
    "UTTEditor": "GFF-UTT.md",
    "UTWEditor": "GFF-UTW.md",
    "WAVEditor": "WAV-File-Format.md",  # WAV/Audio file format
    "SaveGameEditor": "GFF-File-Format.md",  # Save game uses general GFF format doc
    "MetadataEditor": "GFF-File-Format.md",  # Metadata uses general GFF format doc
}

