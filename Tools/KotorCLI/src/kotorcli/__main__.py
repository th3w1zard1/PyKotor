#!/usr/bin/env python3
"""KotorCLI - A build tool for KOTOR projects.

This is a 1:1 implementation of cli's syntax for KOTOR development.
"""
from __future__ import annotations

import pathlib
import sys
from argparse import ArgumentParser
from typing import TYPE_CHECKING

# Configure sys.path for development mode
if not getattr(sys, "frozen", False):

    def update_sys_path(path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    pykotor_path = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    utility_path = pathlib.Path(__file__).parents[4] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        update_sys_path(utility_path.parent)
    kotorcli_path = pathlib.Path(__file__).parent
    if kotorcli_path.exists():
        update_sys_path(kotorcli_path.parent)

from kotorcli.commands import (
    cmd_2da2csv,
    cmd_assemble,
    cmd_cat,
    cmd_compile,
    cmd_config,
    cmd_convert,
    cmd_create_archive,
    cmd_csv22da,
    cmd_decompile,
    cmd_diff,
    cmd_disassemble,
    cmd_extract,
    cmd_gff2json,
    cmd_gff2xml,
    cmd_grep,
    cmd_init,
    cmd_install,
    cmd_json2gff,
    cmd_key_pack,
    cmd_launch,
    cmd_list,
    cmd_list_archive,
    cmd_merge,
    cmd_model_convert,
    cmd_pack,
    cmd_search_archive,
    cmd_sound_convert,
    cmd_ssf2xml,
    cmd_stats,
    cmd_texture_convert,
    cmd_tlk2json,
    cmd_tlk2xml,
    cmd_unpack,
    cmd_validate,
    cmd_xml2gff,
    cmd_xml2ssf,
    cmd_xml2tlk,
)
from kotorcli.config import VERSION
from kotorcli.logger import setup_logger

if TYPE_CHECKING:
    from collections.abc import Sequence


def create_parser() -> ArgumentParser:
    """Create the main argument parser."""
    parser = ArgumentParser(
        prog="kotorcli",
        description="A build tool for KOTOR projects (cli-compatible syntax)",
    )

    # Global options
    parser.add_argument("--version", action="version", version=f"KotorCLI {VERSION}")
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    parser.add_argument("--yes", action="store_true", help="Automatically answer yes to all prompts")
    parser.add_argument("--no", action="store_true", help="Automatically answer no to all prompts")
    parser.add_argument("--default", action="store_true", help="Automatically accept the default answer to prompts")
    parser.add_argument("--verbose", action="store_true", help="Increase feedback verbosity")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging (implies --verbose)")
    parser.add_argument("--quiet", action="store_true", help="Disable all logging except errors")
    parser.add_argument("--no-color", action="store_true", dest="no_color", help="Disable color output")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # config command
    config_parser = subparsers.add_parser(
        "config",
        help="Get, set, or unset user-defined configuration options",
    )
    config_parser.add_argument("key", nargs="?", help="Configuration key")
    config_parser.add_argument("value", nargs="?", help="Configuration value")
    config_parser.add_argument("--global", action="store_true", dest="global_config", help="Apply to all packages (default)")
    config_parser.add_argument("--local", action="store_true", help="Apply to current package only")
    config_parser.add_argument("--get", action="store_true", help="Get the value of key (default when value not passed)")
    config_parser.add_argument("--set", action="store_true", help="Set key to value (default when value is passed)")
    config_parser.add_argument("--unset", action="store_true", help="Delete the key/value pair for key")
    config_parser.add_argument("--list", action="store_true", help="List all key/value pairs in the config file")

    # init command
    init_parser = subparsers.add_parser(
        "init",
        help="Create a new kotorcli package",
    )
    init_parser.add_argument("dir", nargs="?", default=".", help="Directory to initialize (default: current directory)")
    init_parser.add_argument("file", nargs="?", help="File to unpack into the new package")
    init_parser.add_argument("--default", action="store_true", help="Skip package generation dialog")
    init_parser.add_argument("--vcs", choices=["none", "git"], default="git", help="Version control system to use")
    init_parser.add_argument("--file", dest="init_file", help="File to unpack into the package")

    # list command
    list_parser = subparsers.add_parser(
        "list",
        help="List all targets defined in kotorcli.cfg",
    )
    list_parser.add_argument("targets", nargs="*", help="Specific targets to list")
    list_parser.add_argument("--quiet", action="store_true", help="List only target names")
    list_parser.add_argument("--verbose", action="store_true", help="List source files as well")

    # unpack command
    unpack_parser = subparsers.add_parser(
        "unpack",
        help="Unpack a file into the project source tree",
    )
    unpack_parser.add_argument("target", nargs="?", help="Target to unpack")
    unpack_parser.add_argument("file", nargs="?", help="File to unpack")
    unpack_parser.add_argument("--file", dest="unpack_file", help="File or directory to unpack into the target's source tree")
    unpack_parser.add_argument("--removeDeleted", action="store_true", help="Remove source files not present in the file being unpacked")
    unpack_parser.add_argument("--no-removeDeleted", action="store_false", dest="removeDeleted", help="Do not remove source files not present in the file being unpacked")

    # convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert all JSON sources to their GFF counterparts",
    )
    convert_parser.add_argument("targets", nargs="*", default=[], help="Targets to convert (use 'all' for all targets)")
    convert_parser.add_argument("--clean", action="store_true", help="Clear the cache before converting")
    convert_parser.add_argument("--modName", help="Set Mod_Name value in module.ifo")
    convert_parser.add_argument("--modMinGameVersion", help="Set Mod_MinGameVersion in module.ifo")
    convert_parser.add_argument("--modDescription", help="Set Mod_Description in module.ifo")

    # compile command
    compile_parser = subparsers.add_parser(
        "compile",
        help="Compile all nss sources for target",
    )
    compile_parser.add_argument("targets", nargs="*", default=[], help="Targets to compile (use 'all' for all targets)")
    compile_parser.add_argument("--clean", action="store_true", help="Clear the cache before compiling")
    compile_parser.add_argument("-f", "--file", action="append", dest="files", help="Compile specific file(s)")
    compile_parser.add_argument("--skipCompile", action="append", help="Don't compile specific file(s)")

    # pack command
    pack_parser = subparsers.add_parser(
        "pack",
        help="Convert, compile, and pack all sources for target",
    )
    pack_parser.add_argument("targets", nargs="*", default=[], help="Targets to pack (use 'all' for all targets)")
    pack_parser.add_argument("--clean", action="store_true", help="Clear the cache before packing")
    pack_parser.add_argument("--file", dest="pack_file", help="Specify the location for the output file")
    pack_parser.add_argument("--noConvert", action="store_true", help="Do not convert updated json files")
    pack_parser.add_argument("--noCompile", action="store_true", help="Do not recompile updated scripts")
    pack_parser.add_argument("--skipCompile", action="append", help="Don't compile specific file(s)")
    pack_parser.add_argument("--modName", help="Set Mod_Name value in module.ifo")
    pack_parser.add_argument("--modMinGameVersion", help="Set Mod_MinGameVersion in module.ifo")
    pack_parser.add_argument("--modDescription", help="Set Mod_Description in module.ifo")
    pack_parser.add_argument("--abortOnCompileError", action="store_true", help="Abort packing if errors encountered during compilation")
    pack_parser.add_argument("--packUnchanged", action="store_true", help="Continue packing if there are no changed files")
    pack_parser.add_argument("--overwritePackedFile", choices=["ask", "default", "always", "never"], help="How to handle existing packed file in project dir")

    # install command
    install_parser = subparsers.add_parser(
        "install",
        help="Convert, compile, pack, and install target",
    )
    install_parser.add_argument("targets", nargs="*", default=[], help="Targets to install (use 'all' for all targets)")
    install_parser.add_argument("--clean", action="store_true", help="Clear the cache before packing")
    install_parser.add_argument("--noConvert", action="store_true", help="Do not convert updated json files")
    install_parser.add_argument("--noCompile", action="store_true", help="Do not recompile updated scripts")
    install_parser.add_argument("--noPack", action="store_true", help="Do not re-pack the file (implies --noConvert and --noCompile)")
    install_parser.add_argument("--skipCompile", action="append", help="Don't compile specific file(s)")
    install_parser.add_argument("--file", dest="install_file", help="Specify the file to install")
    install_parser.add_argument("--installDir", help="The location of the KOTOR user directory")
    install_parser.add_argument("--modName", help="Set Mod_Name value in module.ifo")
    install_parser.add_argument("--modMinGameVersion", help="Set Mod_MinGameVersion in module.ifo")
    install_parser.add_argument("--modDescription", help="Set Mod_Description in module.ifo")
    install_parser.add_argument("--abortOnCompileError", action="store_true", help="Abort installation if errors encountered during compilation")
    install_parser.add_argument("--packUnchanged", action="store_true", help="Continue packing if there are no changed files")
    install_parser.add_argument("--overwritePackedFile", choices=["ask", "default", "always", "never"], help="How to handle existing packed file in project dir")
    install_parser.add_argument("--overwriteInstalledFile", choices=["ask", "default", "always", "never"], help="How to handle existing installed file in installDir")

    # launch command (with aliases)
    for launch_alias in ["launch", "serve", "play", "test"]:
        launch_parser = subparsers.add_parser(
            launch_alias,
            help="Convert, compile, pack, install, and launch target in-game",
        )
        launch_parser.add_argument("targets", nargs="*", default=[], help="Target to launch")
        launch_parser.add_argument("--clean", action="store_true", help="Clear the cache before packing")
        launch_parser.add_argument("--noConvert", action="store_true", help="Do not convert updated json files")
        launch_parser.add_argument("--noCompile", action="store_true", help="Do not recompile updated scripts")
        launch_parser.add_argument("--noPack", action="store_true", help="Do not re-pack the file")
        launch_parser.add_argument("--skipCompile", action="append", help="Don't compile specific file(s)")
        launch_parser.add_argument("--file", dest="launch_file", help="Specify the file to install")
        launch_parser.add_argument("--installDir", help="The location of the KOTOR user directory")
        launch_parser.add_argument("--modName", help="Set Mod_Name value in module.ifo")
        launch_parser.add_argument("--modMinGameVersion", help="Set Mod_MinGameVersion in module.ifo")
        launch_parser.add_argument("--modDescription", help="Set Mod_Description in module.ifo")
        launch_parser.add_argument("--abortOnCompileError", action="store_true", help="Abort launching if errors encountered during compilation")
        launch_parser.add_argument("--packUnchanged", action="store_true", help="Continue packing if there are no changed files")
        launch_parser.add_argument("--gameBin", help="Path to the swkotor binary file")
        launch_parser.add_argument("--serverBin", help="Path to the kotor server binary file (if applicable)")

    # extract command
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract resources from archive files (KEY/BIF, RIM, ERF, etc.)",
    )
    extract_parser.add_argument("--file", dest="file", required=True, help="Archive file to extract")
    extract_parser.add_argument("--output", "-o", dest="output", help="Output directory (default: archive_name)")
    extract_parser.add_argument("--filter", help="Filter resources by name pattern (supports wildcards)")
    extract_parser.add_argument("--key-file", help="KEY file for BIF extraction (default: chitin.key)")

    # list-archive command
    list_archive_parser = subparsers.add_parser(
        "list-archive",
        aliases=["ls-archive"],
        help="List contents of archive files (KEY/BIF, RIM, ERF, etc.)",
    )
    list_archive_parser.add_argument("--file", dest="file", required=True, help="Archive file to list")
    list_archive_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed resource information")
    list_archive_parser.add_argument("--filter", help="Filter resources by name pattern (supports wildcards)")
    list_archive_parser.add_argument("--key-file", help="KEY file for BIF listing (default: chitin.key)")
    list_archive_parser.add_argument("--bifs-only", action="store_true", help="List only BIF files (for KEY archives)")
    list_archive_parser.add_argument("--resources", action="store_true", help="List resources (for KEY archives)")

    # create-archive command
    create_archive_parser = subparsers.add_parser(
        "create-archive",
        aliases=["pack-archive"],
        help="Create archive (ERF, RIM) from directory",
    )
    create_archive_parser.add_argument("--directory", "-d", dest="directory", required=True, help="Directory to pack")
    create_archive_parser.add_argument("--output", "-o", dest="output", required=True, help="Output archive file")
    create_archive_parser.add_argument("--type", help="Archive type (ERF, MOD, SAV, RIM)")
    create_archive_parser.add_argument("--filter", help="Filter files by pattern (supports wildcards)")

    # Format conversion commands
    gff2xml_parser = subparsers.add_parser("gff2xml", help="Convert GFF to XML")
    gff2xml_parser.add_argument("input", help="Input GFF file")
    gff2xml_parser.add_argument("--output", "-o", dest="output", help="Output XML file")
    gff2xml_parser.add_argument("--compact", action="store_true", help="Compact output (no pretty-printing)")

    xml2gff_parser = subparsers.add_parser("xml2gff", help="Convert XML to GFF")
    xml2gff_parser.add_argument("input", help="Input XML file")
    xml2gff_parser.add_argument("--output", "-o", dest="output", help="Output GFF file")
    xml2gff_parser.add_argument("--type", help="GFF type (default: auto-detect)")

    gff2json_parser = subparsers.add_parser("gff2json", help="Convert GFF to JSON")
    gff2json_parser.add_argument("input", help="Input GFF file")
    gff2json_parser.add_argument("--output", "-o", dest="output", help="Output JSON file")
    gff2json_parser.add_argument("--compact", action="store_true", help="Compact output (no pretty-printing)")

    json2gff_parser = subparsers.add_parser("json2gff", help="Convert JSON to GFF")
    json2gff_parser.add_argument("input", help="Input JSON file")
    json2gff_parser.add_argument("--output", "-o", dest="output", help="Output GFF file")
    json2gff_parser.add_argument("--type", help="GFF type (default: auto-detect)")

    tlk2xml_parser = subparsers.add_parser("tlk2xml", help="Convert TLK to XML")
    tlk2xml_parser.add_argument("input", help="Input TLK file")
    tlk2xml_parser.add_argument("--output", "-o", dest="output", help="Output XML file")
    tlk2xml_parser.add_argument("--compact", action="store_true", help="Compact output (no pretty-printing)")
    tlk2xml_parser.add_argument("--encoding", default="windows-1252", help="Character encoding")

    xml2tlk_parser = subparsers.add_parser("xml2tlk", help="Convert XML to TLK")
    xml2tlk_parser.add_argument("input", help="Input XML file")
    xml2tlk_parser.add_argument("--output", "-o", dest="output", help="Output TLK file")
    xml2tlk_parser.add_argument("--encoding", default="windows-1252", help="Character encoding")

    tlk2json_parser = subparsers.add_parser("tlk2json", help="Convert TLK to JSON")
    tlk2json_parser.add_argument("input", help="Input TLK file")
    tlk2json_parser.add_argument("--output", "-o", dest="output", help="Output JSON file")
    tlk2json_parser.add_argument("--compact", action="store_true", help="Compact output (no pretty-printing)")

    ssf2xml_parser = subparsers.add_parser("ssf2xml", help="Convert SSF to XML")
    ssf2xml_parser.add_argument("input", help="Input SSF file")
    ssf2xml_parser.add_argument("--output", "-o", dest="output", help="Output XML file")
    ssf2xml_parser.add_argument("--compact", action="store_true", help="Compact output (no pretty-printing)")

    xml2ssf_parser = subparsers.add_parser("xml2ssf", help="Convert XML to SSF")
    xml2ssf_parser.add_argument("input", help="Input XML file")
    xml2ssf_parser.add_argument("--output", "-o", dest="output", help="Output SSF file")

    da2csv_parser = subparsers.add_parser("2da2csv", help="Convert 2DA to CSV")
    da2csv_parser.add_argument("input", help="Input 2DA file")
    da2csv_parser.add_argument("--output", "-o", dest="output", help="Output CSV file")
    da2csv_parser.add_argument("--delimiter", default=",", help="CSV delimiter")
    da2csv_parser.add_argument("--headers", action="store_true", default=True, help="Include headers")

    csv2da_parser = subparsers.add_parser("csv22da", help="Convert CSV to 2DA")
    csv2da_parser.add_argument("input", help="Input CSV file")
    csv2da_parser.add_argument("--output", "-o", dest="output", help="Output 2DA file")
    csv2da_parser.add_argument("--delimiter", default=",", help="CSV delimiter")
    csv2da_parser.add_argument("--headers", action="store_true", default=True, help="CSV has headers")

    # Script tools
    decompile_parser = subparsers.add_parser("decompile", help="Decompile NCS bytecode to NSS source")
    decompile_parser.add_argument("input", help="Input NCS file")
    decompile_parser.add_argument("--output", "-o", dest="output", help="Output NSS file")
    decompile_parser.add_argument("--tsl", action="store_true", help="Target TSL instead of KOTOR 1")

    disassemble_parser = subparsers.add_parser("disassemble", help="Disassemble NCS bytecode to text")
    disassemble_parser.add_argument("input", help="Input NCS file")
    disassemble_parser.add_argument("--output", "-o", dest="output", help="Output text file")
    disassemble_parser.add_argument("--game", choices=["k1", "k2"], help="Target game version")
    disassemble_parser.add_argument("--tsl", action="store_true", help="Target TSL instead of KOTOR 1")
    disassemble_parser.add_argument("--compact", action="store_true", help="Compact output")

    assemble_parser = subparsers.add_parser("assemble", help="Assemble/compile NSS source to NCS bytecode")
    assemble_parser.add_argument("input", help="Input NSS file")
    assemble_parser.add_argument("--output", "-o", dest="output", help="Output NCS file")
    assemble_parser.add_argument("--tsl", action="store_true", help="Target TSL instead of KOTOR 1")
    assemble_parser.add_argument("--include", "-I", action="append", dest="include", help="Include directory for #include files")
    assemble_parser.add_argument("--debug", action="store_true", help="Enable debug output")

    # Resource tools
    texture_parser = subparsers.add_parser("texture-convert", help="Convert texture files (TPC↔TGA)")
    texture_parser.add_argument("input", help="Input texture file (TPC or TGA)")
    texture_parser.add_argument("--output", "-o", dest="output", help="Output texture file")
    texture_parser.add_argument("--txi", help="TXI file path (for TPC↔TGA conversion)")
    texture_parser.add_argument("--format", help="TPC format type (for TGA→TPC)")

    sound_parser = subparsers.add_parser("sound-convert", help="Convert sound files (WAV↔clean WAV)")
    sound_parser.add_argument("input", help="Input WAV file")
    sound_parser.add_argument("--output", "-o", dest="output", help="Output WAV file")
    sound_parser.add_argument("--to-clean", action="store_true", help="Convert to clean (deobfuscated) WAV")
    sound_parser.add_argument("--type", default="SFX", help="WAV type (SFX, VO) for game format")

    model_parser = subparsers.add_parser("model-convert", help="Convert model files (MDL↔ASCII)")
    model_parser.add_argument("input", help="Input MDL file")
    model_parser.add_argument("--output", "-o", dest="output", help="Output MDL file")
    model_parser.add_argument("--to-ascii", action="store_true", help="Convert to ASCII format")
    model_parser.add_argument("--mdx", help="MDX file path (for MDL↔ASCII conversion)")

    # Utility commands
    diff_parser = subparsers.add_parser("diff", help="Compare two files and show differences")
    diff_parser.add_argument("file1", help="First file")
    diff_parser.add_argument("file2", help="Second file")
    diff_parser.add_argument("--output", "-o", dest="output", help="Output diff file")
    diff_parser.add_argument("--context", "-C", type=int, default=3, help="Number of context lines")

    grep_parser = subparsers.add_parser("grep", help="Search for patterns in files")
    grep_parser.add_argument("file", help="File to search")
    grep_parser.add_argument("pattern", help="Search pattern")
    grep_parser.add_argument("--case-sensitive", "-i", action="store_true", help="Case-sensitive search")
    grep_parser.add_argument("--line-numbers", "-n", action="store_true", help="Show line numbers")

    stats_parser = subparsers.add_parser("stats", help="Show statistics about a file")
    stats_parser.add_argument("file", help="File to analyze")

    validate_parser = subparsers.add_parser("validate", help="Validate file format and structure")
    validate_parser.add_argument("file", help="File to validate")

    merge_parser = subparsers.add_parser("merge", help="Merge two GFF files")
    merge_parser.add_argument("target", help="Target GFF file (will be modified)")
    merge_parser.add_argument("source", help="Source GFF file (fields to merge)")
    merge_parser.add_argument("--output", "-o", dest="output", help="Output GFF file (default: overwrite target)")

    # search-archive command
    search_archive_parser = subparsers.add_parser(
        "search-archive",
        aliases=["grep-archive"],
        help="Search for resources in archive files",
    )
    search_archive_parser.add_argument("--file", "-f", dest="file", required=True, help="Archive file to search")
    search_archive_parser.add_argument("pattern", help="Search pattern (supports wildcards)")
    search_archive_parser.add_argument("--case-sensitive", action="store_true", help="Case-sensitive search")
    search_archive_parser.add_argument("--content", action="store_true", dest="search_content", help="Search in resource content (not just names)")

    # cat command
    cat_parser = subparsers.add_parser("cat", help="Display resource contents to stdout")
    cat_parser.add_argument("archive", help="Archive file (ERF, RIM)")
    cat_parser.add_argument("resource", help="Resource reference name")
    cat_parser.add_argument("--type", "-t", help="Resource type extension (optional, will try to detect)")

    # key-pack command
    key_pack_parser = subparsers.add_parser(
        "key-pack",
        aliases=["create-key"],
        help="Create KEY file from directory containing BIF files",
    )
    key_pack_parser.add_argument("--directory", "-d", dest="directory", required=True, help="Directory containing BIF files")
    key_pack_parser.add_argument("--bif-dir", dest="bif_dir", help="Directory where BIF files are located (for relative paths in KEY)")
    key_pack_parser.add_argument("--output", "-o", dest="output", required=True, help="Output KEY file")
    key_pack_parser.add_argument("--filter", help="Filter BIF files by pattern (supports wildcards)")

    return parser


def main(argv: Sequence[str] | None = None):
    """Main entry point for KotorCLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Setup logging
    log_level = "DEBUG" if args.debug else ("ERROR" if args.quiet else ("INFO" if not args.verbose else "DEBUG"))
    use_color = not args.no_color
    logger = setup_logger(log_level, use_color)

    # Show help if no command specified
    if not args.command or (hasattr(args, "help") and args.help):
        parser.print_help()
        return 0

    # Dispatch to appropriate command handler
    try:
        if args.command == "config":
            return cmd_config(args, logger)
        if args.command == "init":
            return cmd_init(args, logger)
        if args.command == "list":
            return cmd_list(args, logger)
        if args.command == "unpack":
            return cmd_unpack(args, logger)
        if args.command == "convert":
            return cmd_convert(args, logger)
        if args.command == "compile":
            return cmd_compile(args, logger)
        if args.command == "pack":
            return cmd_pack(args, logger)
        if args.command == "install":
            return cmd_install(args, logger)
        if args.command in ("launch", "serve", "play", "test"):
            return cmd_launch(args, logger)
        if args.command == "extract":
            return cmd_extract(args, logger)
        if args.command in ("list-archive", "ls-archive"):
            return cmd_list_archive(args, logger)
        if args.command in ("create-archive", "pack-archive"):
            return cmd_create_archive(args, logger)
        # Format conversions
        if args.command == "gff2xml":
            return cmd_gff2xml(args, logger)
        if args.command == "xml2gff":
            return cmd_xml2gff(args, logger)
        if args.command == "gff2json":
            return cmd_gff2json(args, logger)
        if args.command == "json2gff":
            return cmd_json2gff(args, logger)
        if args.command == "tlk2xml":
            return cmd_tlk2xml(args, logger)
        if args.command == "xml2tlk":
            return cmd_xml2tlk(args, logger)
        if args.command == "tlk2json":
            return cmd_tlk2json(args, logger)
        if args.command == "ssf2xml":
            return cmd_ssf2xml(args, logger)
        if args.command == "xml2ssf":
            return cmd_xml2ssf(args, logger)
        if args.command == "2da2csv":
            return cmd_2da2csv(args, logger)
        if args.command == "csv22da":
            return cmd_csv22da(args, logger)
        # Script tools
        if args.command == "decompile":
            return cmd_decompile(args, logger)
        if args.command == "disassemble":
            return cmd_disassemble(args, logger)
        if args.command == "assemble":
            return cmd_assemble(args, logger)
        # Resource tools
        if args.command == "texture-convert":
            return cmd_texture_convert(args, logger)
        if args.command == "sound-convert":
            return cmd_sound_convert(args, logger)
        if args.command == "model-convert":
            return cmd_model_convert(args, logger)
        # Utility commands
        if args.command == "diff":
            return cmd_diff(args, logger)
        if args.command == "grep":
            return cmd_grep(args, logger)
        if args.command == "stats":
            return cmd_stats(args, logger)
        if args.command == "validate":
            return cmd_validate(args, logger)
        if args.command == "merge":
            return cmd_merge(args, logger)
        # Advanced archive utilities
        if args.command in ("search-archive", "grep-archive"):
            return cmd_search_archive(args, logger)
        if args.command == "cat":
            return cmd_cat(args, logger)
        if args.command in ("key-pack", "create-key"):
            return cmd_key_pack(args, logger)
        logger.error(f"Unknown command: {args.command}")
        parser.print_help()
        return 1
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.exception(f"Unhandled error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())



