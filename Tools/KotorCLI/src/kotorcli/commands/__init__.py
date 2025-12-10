"""Command implementations for KotorCLI."""
from __future__ import annotations

from kotorcli.commands.cat import cmd_cat
from kotorcli.commands.compile import cmd_compile
from kotorcli.commands.config import cmd_config
from kotorcli.commands.convert import cmd_convert
from kotorcli.commands.create_archive import cmd_create_archive
from kotorcli.commands.extract import cmd_extract
from kotorcli.commands.format_convert import (
    cmd_2da2csv,
    cmd_csv22da,
    cmd_gff2json,
    cmd_gff2xml,
    cmd_json2gff,
    cmd_ssf2xml,
    cmd_tlk2json,
    cmd_tlk2xml,
    cmd_xml2gff,
    cmd_xml2ssf,
    cmd_xml2tlk,
)
from kotorcli.commands.init import cmd_init  # type: ignore[module-not-found]
from kotorcli.commands.install import cmd_install  # type: ignore[module-not-found]
from kotorcli.commands.key_pack import cmd_key_pack  # type: ignore[module-not-found]
from kotorcli.commands.kit_generate import cmd_kit_generate
from kotorcli.commands.launch import cmd_launch  # type: ignore[module-not-found]
from kotorcli.commands.list import cmd_list  # type: ignore[module-not-found]
from kotorcli.commands.list_archive import cmd_list_archive  # type: ignore[module-not-found]
from kotorcli.commands.pack import cmd_pack  # type: ignore[module-not-found]
from kotorcli.commands.patching import (  # type: ignore[module-not-found]
    cmd_batch_patch,
    cmd_patch_file,
    cmd_patch_folder,
    cmd_patch_installation,
)
from kotorcli.commands.resource_tools import (  # type: ignore[module-not-found]
    cmd_model_convert,
    cmd_sound_convert,
    cmd_texture_convert,
)
from kotorcli.commands.script_tools import (  # type: ignore[module-not-found]
    cmd_assemble,
    cmd_decompile,
    cmd_disassemble,
)
from kotorcli.commands.search_archive import cmd_search_archive  # type: ignore[module-not-found]
from kotorcli.commands.unpack import cmd_unpack  # type: ignore[module-not-found]
from kotorcli.commands.utility_commands import (  # type: ignore[module-not-found]
    cmd_diff,
    cmd_grep,
    cmd_merge,
    cmd_stats,
    cmd_validate,
)
from kotorcli.commands.validation import (  # type: ignore[module-not-found]
    cmd_check_2da,
    cmd_check_missing_resources,
    cmd_check_txi,
    cmd_investigate_module,
    cmd_module_resources,
    cmd_validate_installation,
)

__all__ = [
    "cmd_2da2csv",
    "cmd_assemble",
    "cmd_batch_patch",
    "cmd_cat",
    "cmd_check_2da",
    "cmd_check_missing_resources",
    "cmd_check_txi",
    "cmd_compile",
    "cmd_config",
    "cmd_convert",
    "cmd_create_archive",
    "cmd_csv22da",
    "cmd_decompile",
    "cmd_diff",
    "cmd_disassemble",
    "cmd_extract",
    "cmd_gff2json",
    "cmd_gff2xml",
    "cmd_grep",
    "cmd_init",
    "cmd_install",
    "cmd_investigate_module",
    "cmd_json2gff",
    "cmd_key_pack",
    "cmd_kit_generate",
    "cmd_launch",
    "cmd_list",
    "cmd_list_archive",
    "cmd_merge",
    "cmd_model_convert",
    "cmd_module_resources",
    "cmd_pack",
    "cmd_patch_file",
    "cmd_patch_folder",
    "cmd_patch_installation",
    "cmd_search_archive",
    "cmd_sound_convert",
    "cmd_ssf2xml",
    "cmd_stats",
    "cmd_texture_convert",
    "cmd_tlk2json",
    "cmd_tlk2xml",
    "cmd_unpack",
    "cmd_validate",
    "cmd_validate_installation",
    "cmd_xml2gff",
    "cmd_xml2ssf",
    "cmd_xml2tlk",
]



