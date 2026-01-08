"""Argument parser for PyKotor CLI."""

from __future__ import annotations

import os
import sys
from argparse import Action, ArgumentParser, RawDescriptionHelpFormatter
from typing import Any

from pykotor.cli.version import VERSION


class PyKotorHelpFormatter(RawDescriptionHelpFormatter):
    """Custom help formatter with improved structure, colors, and readability."""

    def __init__(
        self,
        prog: str,
        *,
        width: int | None = None,
        max_help_position: int = 32,
    ) -> None:
        super().__init__(prog, width=width, max_help_position=max_help_position)

    def _get_help_string(
        self,
        action: Action,
    ) -> str:
        """Override to customize help text formatting."""
        help_text = action.help
        if help_text is None:
            return ""

        # Add color and formatting for better readability
        if self.supports_color():
            # Highlight important keywords in help text
            help_text = help_text.replace("required", "\033[1;31mrequired\033[0m")
            help_text = help_text.replace("default:", "\033[1;36mdefault:\033[0m")
            help_text = help_text.replace("optional", "\033[1;32moptional\033[0m")

        return help_text

    def supports_color(self) -> bool:
        """Check if terminal supports colors."""
        return (
            hasattr(sys.stdout, 'isatty') and
            sys.stdout.isatty() and
            (
                sys.platform != "win32" or
                "COLORTERM" in os.environ or
                os.environ.get("TERM", "").endswith("-color") or
                os.environ.get("FORCE_COLOR", "").lower() in ("1", "true")
            )
        )

    def start_section(
        self,
        heading: str,
    ) -> None:
        """Start a new section with proper formatting."""
        if heading:
            # Add color and formatting for section headers
            if self.supports_color():
                heading = f"\033[1;33m{heading}\033[0m"
            super().start_section(heading)

    def _format_usage(
        self,
        usage: str | None,
        actions: list[Any],
        groups: list[Any],
        prefix: str | None = None,
    ) -> str:
        """Format usage string with better styling."""
        if prefix is None:
            prefix = "Usage: "
        return super()._format_usage(usage, actions, groups, prefix)

    def format_help(self) -> str:
        """Override to provide custom help formatting with command categories."""
        help_text = super().format_help()

        # Find the subcommands section and reorganize it
        if "Available Commands" in help_text:
            # Extract the subcommands section
            lines = help_text.split('\n')
            subcommands_start = None
            subcommands_end = None

            for i, line in enumerate(lines):
                if "Available Commands" in line:
                    subcommands_start = i
                elif subcommands_start is not None and line.strip() == "" and i > subcommands_start + 2:
                    subcommands_end = i
                    break

            if subcommands_start is not None and subcommands_end is not None:
                # Extract subcommands and reorganize by category
                categories = _organize_commands_by_category()

                # Build categorized help
                categorized_help = []
                categorized_help.append("  \033[1;32mAvailable Commands\033[0m")

                for category, commands in categories.items():
                    categorized_help.append(f"\n{category}")
                    for cmd in commands:
                        # Find the command line in original help
                        for line in lines[subcommands_start:subcommands_end]:
                            if f"  {cmd}" in line or f"  {cmd} " in line:
                                categorized_help.append(f"    {line.strip()}")
                                break

                # Replace the subcommands section
                new_help = '\n'.join(lines[:subcommands_start]) + '\n'.join(categorized_help) + '\n'.join(lines[subcommands_end:])
                return new_help

        return help_text


def _organize_commands_by_category() -> dict[str, list[str]]:
    """Organize commands into logical categories for better help display."""
    categories = {
        "Build & Development": ["init", "list", "unpack", "convert", "compile", "pack", "install", "launch", "serve", "play", "test"],
        "Format Conversion": ["gff2xml", "xml2gff", "gff2json", "json2gff", "tlk2xml", "xml2tlk", "tlk2json", "ssf2xml", "xml2ssf", "2da2csv", "csv22da"],
        "Script Tools": ["decompile", "disassemble", "assemble"],
        "Resource Tools": ["texture-convert", "sound-convert", "model-convert"],
        "Archive Operations": [ "extract", "list-archive", "ls-archive", "create-archive", "pack-archive", "search-archive", "grep-archive", "cat", "key-pack", "create-key", ],
        "Analysis & Utilities": ["diff", "grep", "stats", "validate", "merge", "config"],
        "Validation & Investigation": [ "check-txi", "check-2da", "validate-installation", "investigate-module", "check-missing-resources", "module-resources", "kit-generate", "kit", ],
        "GUI & Interface": ["gui-convert", "gui", "indoor-build", "indoormap-build", "indoor-extract", "indoormap-extract"],
        "Patching": ["batch-patch", "patch-file", "patch-folder", "patch-installation"],
    }
    return categories


def _add_kotordiff_arguments_fallback(parser: ArgumentParser) -> ArgumentParser:
    """Fallback implementation of kotordiff arguments if kotordiff package is not available."""
    parser.add_argument("--path1", type=str, help="Path to compare")
    parser.add_argument("--path2", type=str, help="Additional path to compare")
    parser.add_argument("--path3", type=str, help="Additional path to compare")
    parser.add_argument("--path", action="append", dest="extra_paths", help="Additional paths for N-way comparison")
    parser.add_argument("--tslpatchdata", type=str, help="Path where tslpatchdata folder should be created")
    parser.add_argument("--ini", type=str, default="changes.ini", help="Filename for changes.ini")
    parser.add_argument("--output-log", type=str, help="Filepath of the desired output logfile")
    parser.add_argument("--log-level", type=str, default="info", choices=["debug", "info", "warning", "error", "critical"], help="Logging level")
    parser.add_argument("--output-mode", type=str, default="full", choices=["full", "diff_only", "quiet"], help="Output mode")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--compare-hashes", dest="compare_hashes", action="store_true", default=True, help="Compare hashes")
    parser.add_argument("--no-compare-hashes", dest="compare_hashes", action="store_false", help="Disable hash comparison")
    parser.add_argument("--filter", action="append", help="Filter specific files/modules")
    parser.add_argument("--logging", dest="logging", action="store_true", default=True, help="Whether to log results")
    parser.add_argument("--no-logging", dest="logging", action="store_false", help="Disable log file generation")
    parser.add_argument("--use-profiler", action="store_true", default=False, help="Use cProfile")
    parser.add_argument("--incremental", dest="use_incremental_writer", action="store_true", default=False, help="Write TSLPatcher data incrementally")
    parser.add_argument("--console", action="store_true", help="Show console window even in GUI mode")
    parser.add_argument("--gui", action="store_true", help="Force GUI mode even with paths provided")
    return parser


def create_parser() -> ArgumentParser:  # noqa: PLR0915
    """Create the main argument parser with custom formatting."""

    # Create enhanced description with usage examples
    description = """
\033[1;36mPyKotor CLI\033[0m - A comprehensive build tool for KOTOR projects

\033[1;33mQuick Start:\033[0m
  pykotor init                           # Initialize a new project
  pykotor unpack mymod.mod               # Extract module contents
  pykotor convert                        # Convert JSON sources to GFF
  pykotor compile                        # Compile NSS scripts
  pykotor pack                           # Build final module
  pykotor install                        # Install to game directory

\033[1;33mCommon Workflows:\033[0m
  pykotor unpack mymod.mod && pykotor convert && pykotor pack
  pykotor diff path1 path2 --output-mode diff_only
  pykotor extract --file chitin.key --filter "*.utc"

\033[1;32mGlobal Options:\033[0m
  --yes, --no, --default    Auto-answer prompts
  --verbose, --debug        Increase output detail
  --quiet                   Minimal output
  --no-color                Disable colored output
"""

    parser = ArgumentParser(
        prog="pykotor",
        description=description,
        formatter_class=PyKotorHelpFormatter,
        add_help=False,
    )

    # Global options
    parser.add_argument("--version", action="version", version=f"PyKotor {VERSION}")
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    parser.add_argument("--yes", action="store_true", help="Automatically answer yes to all prompts")
    parser.add_argument("--no", action="store_true", help="Automatically answer no to all prompts")
    parser.add_argument("--default", action="store_true", help="Automatically accept the default answer to prompts")
    parser.add_argument("--verbose", action="store_true", help="Increase feedback verbosity")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging (implies --verbose)")
    parser.add_argument("--quiet", action="store_true", help="Disable all logging except errors")
    parser.add_argument("--no-color", action="store_true", dest="no_color", help="Disable color output")

    # Create subparsers with better help text
    subparsers = parser.add_subparsers(
        dest="command",
        title="\033[1;32mAvailable Commands\033[0m",
        description="Choose a command to execute. Use 'pykotor <command> --help' for detailed help.",
        metavar="COMMAND",
        help="Command to execute"
    )

    # config command
    config_parser = subparsers.add_parser("config", help="Get, set, or unset user-defined configuration options")
    config_parser.add_argument("key", nargs="?", help="Configuration key")
    config_parser.add_argument("value", nargs="?", help="Configuration value")
    config_parser.add_argument("--global", action="store_true", dest="global_config", help="Apply to all packages (default)")
    config_parser.add_argument("--local", action="store_true", help="Apply to current package only")
    config_parser.add_argument("--get", action="store_true", help="Get the value of key (default when value not passed)")
    config_parser.add_argument("--set", action="store_true", help="Set key to value (default when value is passed)")
    config_parser.add_argument("--unset", action="store_true", help="Delete the key/value pair for key")
    config_parser.add_argument("--list", action="store_true", help="List all key/value pairs in the config file")

    # init command
    init_parser = subparsers.add_parser("init", help="Create a new kotorcli package")
    init_parser.add_argument("dir", nargs="?", default=".", help="Directory to initialize (default: current directory)")
    init_parser.add_argument("file", nargs="?", help="File to unpack into the new package")
    init_parser.add_argument("--default", action="store_true", help="Skip package generation dialog")
    init_parser.add_argument("--vcs", choices=["none", "git"], default="git", help="Version control system to use")
    init_parser.add_argument("--file", dest="init_file", help="File to unpack into the package")

    # list command
    list_parser = subparsers.add_parser("list", help="List all targets defined in kotorcli.cfg")
    list_parser.add_argument("targets", nargs="*", help="Specific targets to list")
    list_parser.add_argument("--quiet", action="store_true", help="List only target names")
    list_parser.add_argument("--verbose", action="store_true", help="List source files as well")

    # unpack command
    unpack_parser = subparsers.add_parser("unpack", help="Unpack a file into the project source tree")
    unpack_parser.add_argument("target", nargs="?", help="Target to unpack")
    unpack_parser.add_argument("file", nargs="?", help="File to unpack")
    unpack_parser.add_argument("--file", dest="unpack_file", help="File or directory to unpack into the target's source tree")
    unpack_parser.add_argument("--removeDeleted", action="store_true", help="Remove source files not present in the file being unpacked")
    unpack_parser.add_argument("--no-removeDeleted", action="store_false", dest="removeDeleted", help="Do not remove source files not present in the file being unpacked")

    # convert command
    convert_parser = subparsers.add_parser("convert", help="Convert all JSON sources to their GFF counterparts")
    convert_parser.add_argument("targets", nargs="*", default=[], help="Targets to convert (use 'all' for all targets)")
    convert_parser.add_argument("--clean", action="store_true", help="Clear the cache before converting")
    convert_parser.add_argument("--modName", help="Set Mod_Name value in module.ifo")
    convert_parser.add_argument("--modMinGameVersion", help="Set Mod_MinGameVersion in module.ifo")
    convert_parser.add_argument("--modDescription", help="Set Mod_Description in module.ifo")

    # compile command
    compile_parser = subparsers.add_parser("compile", help="Compile all nss sources for target")
    compile_parser.add_argument("targets", nargs="*", default=[], help="Targets to compile (use 'all' for all targets)")
    compile_parser.add_argument("--clean", action="store_true", help="Clear the cache before compiling")
    compile_parser.add_argument("-f", "--file", action="append", dest="files", help="Compile specific file(s)")
    compile_parser.add_argument("--skipCompile", action="append", help="Don't compile specific file(s)")

    # pack command
    pack_parser = subparsers.add_parser("pack", help="Convert, compile, and pack all sources for target")
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
    install_parser = subparsers.add_parser("install", help="Convert, compile, pack, and install target")
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
        launch_parser = subparsers.add_parser(launch_alias, help="Convert, compile, pack, install, and launch target in-game")
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
        help="Extract resources from Bioware archives",
        description="""
Extract files from Bioware archive formats including:
• ERF files (.erf, .mod, .sav)
• RIM files (.rim)
• KEY/BIF archives (chitin.key)

\033[1;36mExamples:\033[0m
  pykotor extract --file mymodule.mod
  pykotor extract --file chitin.key --filter "*.utc" --output extracted
  pykotor extract --file module.rim --filter p_* --key-file custom.key
"""
    )
    extract_parser.add_argument("--file", dest="file", required=True, help="Archive file to extract")
    extract_parser.add_argument("--output", "-o", dest="output", help="Output directory (default: archive_name)")
    extract_parser.add_argument("--filter", help="Filter resources by name (resref, resref.ext, or glob like p_cand* / p_cand.utc)")
    extract_parser.add_argument("--key-file", help="KEY file for BIF extraction (default: chitin.key)")

    # list-archive command
    list_archive_parser = subparsers.add_parser("list-archive", aliases=["ls-archive"], help="List contents of archive files (KEY/BIF, RIM, ERF, etc.)")
    list_archive_parser.add_argument("--file", dest="file", required=True, help="Archive file to list")
    list_archive_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed resource information")
    list_archive_parser.add_argument("--filter", help="Filter resources by name (resref, resref.ext, or glob like p_cand* / p_cand.utc)")
    list_archive_parser.add_argument("--key-file", help="KEY file for BIF listing (default: chitin.key)")
    list_archive_parser.add_argument("--bifs-only", action="store_true", help="List only BIF files (for KEY archives)")
    list_archive_parser.add_argument("--resources", action="store_true", help="List resources (for KEY archives)")

    # create-archive command
    create_archive_parser = subparsers.add_parser("create-archive", aliases=["pack-archive"], help="Create archive (ERF, RIM) from directory")
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
    texture_parser = subparsers.add_parser("texture-convert", help="Convert texture files (TPC<->TGA)")
    texture_parser.add_argument("input", help="Input texture file (TPC or TGA)")
    texture_parser.add_argument("--output", "-o", dest="output", help="Output texture file")
    texture_parser.add_argument("--txi", help="TXI file path (for TPC<->TGA conversion)")
    texture_parser.add_argument("--format", help="TPC format type (for TGA->TPC)")

    sound_parser = subparsers.add_parser("sound-convert", help="Convert sound files (WAV<->clean WAV)")
    sound_parser.add_argument("input", help="Input WAV file")
    sound_parser.add_argument("--output", "-o", dest="output", help="Output WAV file")
    sound_parser.add_argument("--to-clean", action="store_true", help="Convert to clean (deobfuscated) WAV")
    sound_parser.add_argument("--type", default="SFX", help="WAV type (SFX, VO) for game format")

    model_parser = subparsers.add_parser("model-convert", help="Convert model files (MDL<->ASCII)")
    model_parser.add_argument("input", help="Input MDL file")
    model_parser.add_argument("--output", "-o", dest="output", help="Output MDL file")
    model_parser.add_argument("--to-ascii", action="store_true", help="Convert to ASCII format")
    model_parser.add_argument("--mdx", help="MDX file path (for MDL<->ASCII conversion)")

    # Utility commands
    diff_parser = subparsers.add_parser(
        "diff",
        help="Compare files, folders, or KOTOR installations",
        description="""
Compare two paths and show differences. Supports any combination of:
• Individual files (GFF, 2DA, TLK, etc.)
• Folders containing game assets
• Complete KOTOR installations
• Bioware archives (.mod, .sav, .erf, .rim)

\033[1;36mExamples:\033[0m
  pykotor diff module1.mod module2.mod
  pykotor diff /path/to/kotor1 /path/to/kotor2 --output-mode diff_only
  pykotor diff file1.gff file2.gff --format side_by_side
  pykotor diff --generate-ini installation1 installation2
"""
    )
    diff_parser.add_argument("path1", help="First path (file, folder, installation, or archive)")
    diff_parser.add_argument("path2", help="Second path (file, folder, installation, or archive)")
    diff_parser.add_argument("--format", choices=["unified", "context", "side_by_side"], default="unified",
                           help="Output format: unified (default), context, or side_by_side")
    diff_parser.add_argument("--output-mode", choices=["full", "diff_only", "quiet"], default="full",
                           help="Output mode: full (with logging), diff_only (diffs only), quiet (minimal)")
    diff_parser.add_argument("--generate-ini", action="store_true",
                           help="Generate TSLPatcher changes.ini and tslpatchdata folder")
    diff_parser.add_argument("--output", "-o", dest="output", help="Write diff output to file")
    diff_parser.add_argument("--context", "-C", type=int, default=3, help="Lines of context around changes (default: 3)")

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
    search_archive_parser = subparsers.add_parser("search-archive", aliases=["grep-archive"], help="Search for resources in archive files")
    search_archive_parser.add_argument("--file", "-f", dest="file", required=True, help="Archive file to search")
    search_archive_parser.add_argument("pattern", help="Search pattern (supports wildcards)")
    search_archive_parser.add_argument("--key-file", help="KEY file for BIF searches (optional)")
    search_archive_parser.add_argument("--case-sensitive", action="store_true", help="Case-sensitive search")
    search_archive_parser.add_argument("--content", action="store_true", dest="search_content", help="Search in resource content (not just names)")

    # cat command
    cat_parser = subparsers.add_parser("cat", help="Display resource contents to stdout")
    cat_parser.add_argument("archive", help="Archive file (ERF, RIM)")
    cat_parser.add_argument("resource", help="Resource reference name")
    cat_parser.add_argument("--type", "-t", help="Resource type extension (optional, will try to detect)")

    # key-pack command
    key_pack_parser = subparsers.add_parser("key-pack", aliases=["create-key"], help="Create KEY file from directory containing BIF files")
    key_pack_parser.add_argument("--directory", "-d", dest="directory", required=True, help="Directory containing BIF files")
    key_pack_parser.add_argument("--bif-dir", dest="bif_dir", help="Directory where BIF files are located (for relative paths in KEY)")
    key_pack_parser.add_argument("--output", "-o", dest="output", required=True, help="Output KEY file")
    key_pack_parser.add_argument("--filter", help="Filter BIF files by pattern (supports wildcards)")

    # Validation and investigation commands
    check_txi_parser = subparsers.add_parser("check-txi", help="Check if TXI files exist for specific textures")
    check_txi_parser.add_argument("--installation", "-i", required=True, help="Path to KOTOR installation")
    check_txi_parser.add_argument("--textures", "-t", nargs="+", required=True, help="Texture names to check (without extension)")

    check_2da_parser = subparsers.add_parser("check-2da", help="Check if a 2DA file exists in installation")
    check_2da_parser.add_argument("--2da", dest="two_da_name", required=True, help="2DA file name (without extension)")
    check_2da_parser.add_argument("--installation", "-i", dest="two_da_installation", required=True, help="Path to KOTOR installation")

    validate_installation_parser = subparsers.add_parser("validate-installation", help="Validate a KOTOR installation")
    validate_installation_parser.add_argument("--installation", "-i", required=True, help="Path to KOTOR installation")
    validate_installation_parser.add_argument("--check-essential", action="store_true", default=True, help="Check for essential game files")

    investigate_module_parser = subparsers.add_parser("investigate-module", help="Investigate a module's structure")
    investigate_module_parser.add_argument("--module", "-m", required=True, help="Module name to investigate")
    investigate_module_parser.add_argument("--installation", "-i", required=True, help="Path to KOTOR installation")
    investigate_module_parser.add_argument("--json", help="Output results as JSON to file")
    investigate_module_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")

    check_missing_resources_parser = subparsers.add_parser("check-missing-resources", help="Check if missing resources are referenced by module models")
    check_missing_resources_parser.add_argument("--module", "-m", required=True, help="Module name to check")
    check_missing_resources_parser.add_argument("--installation", "-i", required=True, help="Path to KOTOR installation")
    check_missing_resources_parser.add_argument("--textures", "-t", nargs="+", help="Texture names to check")
    check_missing_resources_parser.add_argument("--lightmaps", "-l", nargs="+", help="Lightmap names to check")

    module_resources_parser = subparsers.add_parser("module-resources", help="Get all resources referenced by a module's models")
    module_resources_parser.add_argument("--module", "-m", required=True, help="Module name")
    module_resources_parser.add_argument("--installation", "-i", required=True, help="Path to KOTOR installation")
    module_resources_parser.add_argument("--output", "-o", help="Output JSON file")
    module_resources_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")

    kit_generate_parser = subparsers.add_parser("kit-generate", aliases=["kit"], help="Generate a Holocron-compatible kit from a module")
    kit_generate_parser.add_argument("--installation", "-i", help="Path to KOTOR installation")
    kit_generate_parser.add_argument("--module", "-m", help="Module name (e.g., danm13)")
    kit_generate_parser.add_argument("--output", "-o", help="Output directory for generated kit")
    kit_generate_parser.add_argument("--kit-id", help="Optional kit id (defaults to module name)")
    kit_generate_parser.add_argument("--log-level", choices=["debug", "info", "warning", "error", "critical"], default="info", help="Logging level for kit generation")

    gui_convert_parser = subparsers.add_parser("gui-convert", aliases=["gui"], help="Convert KotOR GUI layouts to target resolutions")
    gui_convert_parser.add_argument("--input", "-i", action="append", help="Input GUI file or folder (can be passed multiple times)")
    gui_convert_parser.add_argument("--output", "-o", help="Output directory for converted GUI files")
    gui_convert_parser.add_argument("--resolution", "-r", help="Resolution spec (WIDTHxHEIGHT, comma separated) or ALL")
    gui_convert_parser.add_argument("--log-level", choices=["debug", "info", "warning", "error", "critical"], default="info", help="Logging level for GUI conversion")

    # Indoor map building commands
    indoor_build_parser = subparsers.add_parser("indoor-build", aliases=["indoormap-build"], help="Build a .mod file from a .indoor file")
    indoor_build_parser.add_argument("--input", "-i", required=True, help="Input .indoor file")
    indoor_build_parser.add_argument("--output", "-o", required=True, help="Output .mod file")
    indoor_build_parser.add_argument("--installation", required=True, help="Path to KOTOR installation")
    indoor_build_parser.add_argument("--implicit-kit", action="store_true", help="Use implicit ModuleKit components derived from module resources (no external kits required)")
    indoor_build_parser.add_argument("--kits", "-k", required=False, help="(Deprecated) Path to kits directory. Only needed when NOT using --implicit-kit.")
    indoor_build_parser.add_argument("--game", "-g", choices=["k1", "k2", "kotor1", "kotor2", "tsl"], help="Target game version (default: auto-detect from installation)")
    indoor_build_parser.add_argument("--module-filename", help="Module filename (overrides .indoor module_id)")
    indoor_build_parser.add_argument("--loading-screen", help="Path to loading screen image (TPC/TGA format)")
    indoor_build_parser.add_argument("--log-level", choices=["debug", "info", "warning", "error", "critical"], default="info", help="Logging level")

    indoor_extract_parser = subparsers.add_parser("indoor-extract", aliases=["indoormap-extract"], help="Extract a .indoor file from a composite module")
    indoor_extract_parser.add_argument("--module", "-m", required=False, help="Module name (e.g., danm13). Required unless --module-file is provided.")
    indoor_extract_parser.add_argument("--module-file", required=False, help="Extract an indoor map from a specific module container file (.mod/.rim/.erf/.sav).")
    indoor_extract_parser.add_argument("--output", "-o", required=True, help="Output .indoor file")
    indoor_extract_parser.add_argument("--installation", required=True, help="Path to KOTOR installation")
    indoor_extract_parser.add_argument(
        "--implicit-kit", action="store_true", help="Extract using implicit ModuleKit components derived from module resources (no external kits required)"
    )
    indoor_extract_parser.add_argument("--kits", "-k", required=False, help="(Deprecated) Path to kits directory (only needed for reverse-extraction in non-implicit mode).")
    indoor_extract_parser.add_argument("--game", "-g", choices=["k1", "k2", "kotor1", "kotor2", "tsl"], help="Target game version (default: auto-detect from installation)")
    indoor_extract_parser.add_argument("--log-level", choices=["debug", "info", "warning", "error", "critical"], default="info", help="Logging level")

    # Batch patching commands
    batch_patch_parser = subparsers.add_parser("batch-patch", help="Batch patch files, folders, or installations")
    batch_patch_parser.add_argument("--path", "-p", required=True, help="Path to file, folder, or installation")
    batch_patch_parser.add_argument("--translate", action="store_true", help="Enable translation")
    batch_patch_parser.add_argument("--to-lang", help="Target language for translation (e.g., French, German)")
    batch_patch_parser.add_argument("--translation-option", help="Translation service to use")
    batch_patch_parser.add_argument("--set-unskippable", action="store_true", help="Set dialogs as unskippable")
    batch_patch_parser.add_argument("--convert-tga", choices=["TGA to TPC", "TPC to TGA"], help="Convert textures")
    batch_patch_parser.add_argument("--convert-gffs-to-k1", action="store_true", help="Convert GFFs to K1 format")
    batch_patch_parser.add_argument("--convert-gffs-to-tsl", action="store_true", help="Convert GFFs to TSL format")
    batch_patch_parser.add_argument("--always-backup", action="store_true", default=True, help="Always create backups")
    batch_patch_parser.add_argument("--max-threads", type=int, default=2, help="Maximum translation threads")

    patch_file_parser = subparsers.add_parser("patch-file", help="Patch a single file")
    patch_file_parser.add_argument("--file", "-f", required=True, help="File to patch")
    patch_file_parser.add_argument("--translate", action="store_true", help="Enable translation")
    patch_file_parser.add_argument("--to-lang", help="Target language for translation")
    patch_file_parser.add_argument("--set-unskippable", action="store_true", help="Set dialogs as unskippable")
    patch_file_parser.add_argument("--convert-tga", choices=["TGA to TPC", "TPC to TGA"], help="Convert textures")
    patch_file_parser.add_argument("--convert-gffs-to-k1", action="store_true", help="Convert GFFs to K1 format")
    patch_file_parser.add_argument("--convert-gffs-to-tsl", action="store_true", help="Convert GFFs to TSL format")
    patch_file_parser.add_argument("--always-backup", action="store_true", default=True, help="Always create backups")

    patch_folder_parser = subparsers.add_parser("patch-folder", help="Patch all files in a folder recursively")
    patch_folder_parser.add_argument("--folder", "-f", required=True, help="Folder to patch")
    patch_folder_parser.add_argument("--translate", action="store_true", help="Enable translation")
    patch_folder_parser.add_argument("--to-lang", help="Target language for translation")
    patch_folder_parser.add_argument("--set-unskippable", action="store_true", help="Set dialogs as unskippable")
    patch_folder_parser.add_argument("--convert-tga", choices=["TGA to TPC", "TPC to TGA"], help="Convert textures")
    patch_folder_parser.add_argument("--convert-gffs-to-k1", action="store_true", help="Convert GFFs to K1 format")
    patch_folder_parser.add_argument("--convert-gffs-to-tsl", action="store_true", help="Convert GFFs to TSL format")
    patch_folder_parser.add_argument("--always-backup", action="store_true", default=True, help="Always create backups")
    patch_folder_parser.add_argument("--max-threads", type=int, default=2, help="Maximum translation threads")

    patch_installation_parser = subparsers.add_parser("patch-installation", help="Patch a KOTOR installation")
    patch_installation_parser.add_argument("--installation", "-i", required=True, help="Path to KOTOR installation")
    patch_installation_parser.add_argument("--translate", action="store_true", help="Enable translation")
    patch_installation_parser.add_argument("--to-lang", help="Target language for translation")
    patch_installation_parser.add_argument("--set-unskippable", action="store_true", help="Set dialogs as unskippable")
    patch_installation_parser.add_argument("--convert-tga", choices=["TGA to TPC", "TPC to TGA"], help="Convert textures")
    patch_installation_parser.add_argument("--convert-gffs-to-k1", action="store_true", help="Convert GFFs to K1 format")
    patch_installation_parser.add_argument("--convert-gffs-to-tsl", action="store_true", help="Convert GFFs to TSL format")
    patch_installation_parser.add_argument("--always-backup", action="store_true", default=True, help="Always create backups")
    patch_installation_parser.add_argument("--max-threads", type=int, default=2, help="Maximum translation threads")

    return parser
