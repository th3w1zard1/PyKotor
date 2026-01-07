"""Command implementations for PyKotor CLI."""

from __future__ import annotations

from pykotor.cli.commands.cat import cmd_cat
from pykotor.cli.commands.compile import cmd_compile
from pykotor.cli.commands.config import cmd_config
from pykotor.cli.commands.convert import cmd_convert
from pykotor.cli.commands.create_archive import cmd_create_archive
from pykotor.cli.commands.extract import cmd_extract
from pykotor.cli.commands.format_convert import (
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
from pykotor.cli.commands.gui_convert import cmd_gui_convert
from pykotor.cli.commands.init import cmd_init
from pykotor.cli.commands.install import cmd_install
from pykotor.cli.commands.key_pack import cmd_key_pack
from pykotor.cli.commands.kit_generate import cmd_kit_generate
from pykotor.cli.commands.launch import cmd_launch
from pykotor.cli.commands.list import cmd_list
from pykotor.cli.commands.list_archive import cmd_list_archive
from pykotor.cli.commands.pack import cmd_pack
from pykotor.cli.commands.patching import (
    cmd_batch_patch,
    cmd_patch_file,
    cmd_patch_folder,
    cmd_patch_installation,
)
from pykotor.cli.commands.resource_tools import (
    cmd_model_convert,
    cmd_sound_convert,
    cmd_texture_convert,
)
from pykotor.cli.commands.script_tools import (
    cmd_assemble,
    cmd_decompile,
    cmd_disassemble,
)
from pykotor.cli.commands.search_archive import cmd_search_archive
from pykotor.cli.commands.unpack import cmd_unpack
from pykotor.cli.commands.utility_commands import (
    cmd_diff,
    cmd_grep,
    cmd_merge,
    cmd_stats,
    cmd_validate,
)
from pykotor.cli.commands.validation import (
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
    "cmd_gui_convert",
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
