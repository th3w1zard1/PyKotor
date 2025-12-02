"""Batch patching utilities for KOTOR resources.

This module provides functions for:
- Patching GFF files (translating LocalizedStrings, setting unskippable dialogs)
- Converting GFF files between K1 and TSL formats
- Converting TGA/TPC textures
- Processing TLK files
- Batch patching installations, folders, and files

References:
----------
    Tools/BatchPatcher/src/batchpatcher/__main__.py - Original implementation
"""
from __future__ import annotations

import concurrent.futures
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pykotor.common.alien_sounds import ALIEN_SOUNDS
from pykotor.common.language import Language, LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.common.stream import BinaryWriter
from pykotor.extract.capsule import Capsule, LazyCapsule
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.extract.installation import Installation
from pykotor.resource.formats.erf.erf_auto import write_erf
from pykotor.resource.formats.erf.erf_data import ERF, ERFType
from pykotor.resource.formats.gff import (
    GFF,
    GFFContent,
    GFFFieldType,
    GFFList,
    GFFStruct,
    read_gff,
)
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.rim.rim_auto import write_rim
from pykotor.resource.formats.rim.rim_data import RIM
from pykotor.resource.formats.tlk import read_tlk, write_tlk
from pykotor.resource.formats.tpc.io_tga import TPCTGAReader, TPCTGAWriter
from pykotor.resource.formats.tpc.io_tpc import TPCBinaryReader, TPCBinaryWriter
from pykotor.resource.formats.tpc.tpc_auto import bytes_tpc
from pykotor.resource.formats.tpc.tpc_data import TPC
from pykotor.resource.generics.are import read_are, write_are
from pykotor.resource.generics.dlg import read_dlg, write_dlg
from pykotor.resource.generics.git import read_git, write_git
from pykotor.resource.generics.jrl import read_jrl, write_jrl
from pykotor.resource.generics.pth import read_pth, write_pth
from pykotor.resource.generics.utc import read_utc, write_utc
from pykotor.resource.generics.utd import read_utd, write_utd
from pykotor.resource.generics.ute import read_ute, write_ute
from pykotor.resource.generics.uti import read_uti, write_uti
from pykotor.resource.generics.utm import read_utm, write_utm
from pykotor.resource.generics.utp import read_utp, write_utp
from pykotor.resource.generics.uts import read_uts, write_uts
from pykotor.resource.generics.utt import read_utt, write_utt
from pykotor.resource.generics.utw import read_utw, write_utw
from pykotor.resource.salvage import validate_capsule
from pykotor.resource.type import ResourceType
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from pykotor.tools.misc import is_any_erf_type_file, is_capsule_file
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    from pykotor.resource.formats.tlk import TLK
    from pykotor.resource.formats.tlk.tlk_data import TLKEntry


class PatchingConfig:
    """Configuration for batch patching operations."""

    def __init__(self):
        self.translate: bool = False
        self.set_unskippable: bool = False
        self.convert_tga: str | None = None  # "TGA to TPC", "TPC to TGA", or None
        self.k1_convert_gffs: bool = False
        self.tsl_convert_gffs: bool = False
        self.always_backup: bool = True
        self.max_threads: int = 2
        self.translator: Any = None  # Translator instance
        self.log_callback: Callable[[str], None] | None = None

    def is_patching(self) -> bool:
        """Check if any patching operation is enabled."""
        return bool(
            self.translate
            or self.set_unskippable
            or self.convert_tga
            or self.k1_convert_gffs
            or self.tsl_convert_gffs
        )


def log_message(config: PatchingConfig, message: str) -> None:
    """Log a message using the configured callback."""
    if config.log_callback:
        config.log_callback(message)


def patch_nested_gff(
    gff_struct: GFFStruct,
    gff_content: GFFContent,
    gff: GFF,
    config: PatchingConfig,
    current_path: Path | None = None,
    made_change: bool = False,
    alien_vo_count: int = -1,
) -> tuple[bool, int]:
    """Recursively patch GFF structures.

    Args:
    ----
        gff_struct: The GFF struct to patch
        gff_content: The GFF content type
        gff: The parent GFF object
        config: Patching configuration
        current_path: Current path in the GFF structure
        made_change: Whether any changes have been made
        alien_vo_count: Count of alien voice-overs found

    Returns:
    -------
        Tuple of (made_change: bool, alien_vo_count: int)
    """
    if gff_content != GFFContent.DLG and not config.translate:
        return False, alien_vo_count

    if gff_content == GFFContent.DLG and config.set_unskippable:
        sound_raw = gff_struct.acquire("Sound", None)  # type: ignore[arg-type]
        sound: ResRef | None = sound_raw if isinstance(sound_raw, ResRef) else None
        sound_str = "" if sound is None else str(sound).strip().lower()
        if sound and sound_str.strip() and sound_str in ALIEN_SOUNDS:
            alien_vo_count += 1

    current_path = current_path or Path("GFFRoot")
    for label, ftype, value in gff_struct:
        if label.lower() == "mod_name":
            continue
        child_path: Path = current_path / label

        if ftype == GFFFieldType.Struct:
            assert isinstance(value, GFFStruct), f"Not a GFFStruct instance: {value.__class__.__name__}: {value}"  # noqa: S101
            result_made_change, alien_vo_count = patch_nested_gff(
                value, gff_content, gff, config, child_path, made_change, alien_vo_count
            )
            made_change |= result_made_change
            continue

        if ftype == GFFFieldType.List:
            assert isinstance(value, GFFList), f"Not a GFFList instance: {value.__class__.__name__}: {value}"  # noqa: S101
            result_made_change, alien_vo_count = recurse_through_list(
                value, gff_content, gff, config, child_path, made_change, alien_vo_count
            )
            made_change |= result_made_change
            continue

        if ftype == GFFFieldType.LocalizedString and config.translate:
            assert isinstance(value, LocalizedString), f"{value.__class__.__name__}: {value}"  # noqa: S101
            log_message(
                config,
                f"Translating CExoLocString at {child_path} to {config.translator.to_lang.name if config.translator else 'unknown'}",
            )
            made_change |= translate_locstring(value, config)
    return made_change, alien_vo_count


def recurse_through_list(
    gff_list: GFFList,
    gff_content: GFFContent,
    gff: GFF,
    config: PatchingConfig,
    current_path: Path | None = None,
    made_change: bool = False,
    alien_vo_count: int = -1,
) -> tuple[bool, int]:
    """Recursively process GFF lists.

    Args:
    ----
        gff_list: The GFF list to process
        gff_content: The GFF content type
        gff: The parent GFF object
        config: Patching configuration
        current_path: Current path in the GFF structure
        made_change: Whether any changes have been made
        alien_vo_count: Count of alien voice-overs found

    Returns:
    -------
        Tuple of (made_change: bool, alien_vo_count: int)
    """
    current_path = current_path or Path("GFFListRoot")
    for list_index, gff_struct in enumerate(gff_list):
        result_made_change, alien_vo_count = patch_nested_gff(
            gff_struct, gff_content, gff, config, current_path / str(list_index), made_change, alien_vo_count
        )
        made_change |= result_made_change
    return made_change, alien_vo_count


def translate_locstring(locstring: LocalizedString, config: PatchingConfig) -> bool:
    """Translate a LocalizedString using the configured translator.

    Args:
    ----
        locstring: The LocalizedString to translate
        config: Patching configuration with translator

    Returns:
    -------
        True if changes were made, False otherwise
    """
    if not config.translator:
        return False

    made_change = False
    new_substrings: dict[int, str] = deepcopy(locstring._substrings)  # noqa: SLF001
    for lang, gender, text in locstring:
        if text is not None and text.strip():
            translated_text = config.translator.translate(text, from_lang=lang)
            log_message(config, f"Translated {text} --> {translated_text}")
            substring_id = LocalizedString.substring_id(config.translator.to_lang, gender)
            new_substrings[substring_id] = str(translated_text)
            made_change = True
    locstring._substrings = new_substrings  # noqa: SLF001
    return made_change


def fix_encoding(text: str, encoding: str) -> str:
    """Fix text encoding by re-encoding and decoding.

    Args:
    ----
        text: Text to fix
        encoding: Target encoding

    Returns:
    -------
        Fixed text
    """
    return text.encode(encoding=encoding, errors="ignore").decode(encoding=encoding, errors="ignore").strip()


def convert_gff_game(
    from_game: Game,
    resource: FileResource,
    config: PatchingConfig,
) -> None:
    """Convert a GFF resource from one game format to another.

    Args:
    ----
        from_game: Source game (K1 or K2)
        resource: The resource to convert
        config: Patching configuration
    """
    to_game = Game.K2 if from_game.is_k1() else Game.K1
    new_name = resource.filename()
    converted_data: Path | bytearray = bytearray()
    if not resource.inside_capsule:
        new_name = (
            f"{resource.resname()}_{to_game.name!s}.{resource.restype()!s}"
            if config.always_backup
            else resource.filename()
        )
        converted_data = resource.filepath().with_name(new_name)
        savepath = converted_data
    else:
        savepath = resource.filepath()

    log_message(config, f"Converting {resource.path_ident().parent}/{resource.path_ident().name} to {to_game.name}")
    generic: Any
    try:
        if resource.restype() is ResourceType.ARE:
            generic = read_are(resource.data(), offset=0, size=resource.size())
            write_are(generic, converted_data, to_game)

        elif resource.restype() is ResourceType.DLG:
            generic = read_dlg(resource.data(), offset=0, size=resource.size())
            write_dlg(generic, converted_data, to_game)

        elif resource.restype() is ResourceType.GIT:
            generic = read_git(resource.data(), offset=0, size=resource.size())
            write_git(generic, converted_data, to_game)

        elif resource.restype() is ResourceType.JRL:
            generic = read_jrl(resource.data(), offset=0, size=resource.size())
            write_jrl(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.PTH:
            generic = read_pth(resource.data(), offset=0, size=resource.size())
            write_pth(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTC:
            generic = read_utc(resource.data(), offset=0, size=resource.size())
            write_utc(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTD:
            generic = read_utd(resource.data(), offset=0, size=resource.size())
            write_utd(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTE:
            generic = read_ute(resource.data(), offset=0, size=resource.size())
            write_ute(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTI:
            generic = read_uti(resource.data(), offset=0, size=resource.size())
            write_uti(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTM:
            generic = read_utm(resource.data(), offset=0, size=resource.size())
            write_utm(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTP:
            generic = read_utp(resource.data(), offset=0, size=resource.size())
            write_utp(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTS:
            generic = read_uts(resource.data(), offset=0, size=resource.size())
            write_uts(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTT:
            generic = read_utt(resource.data(), offset=0, size=resource.size())
            write_utt(generic, converted_data, game=to_game)

        elif resource.restype() is ResourceType.UTW:
            generic = read_utw(resource.data(), offset=0, size=resource.size())
            write_utw(generic, converted_data, game=to_game)

        else:
            log_message(config, f"Unsupported gff: {resource.identifier()}")
    except (OSError, ValueError):
        log_message(config, f"Corrupted GFF: '{resource.path_ident()}', skipping...")
        if not resource.inside_capsule:
            return
        log_message(config, f"Corrupted GFF: '{resource.path_ident()}', will start validation process of '{resource.filepath().name}'...")
        new_erfrim = validate_capsule(resource.filepath(), strict=True, game=to_game)
        if isinstance(new_erfrim, ERF):
            log_message(config, f"Saving salvaged ERF to '{savepath}'")
            write_erf(new_erfrim, savepath)
            return
        if isinstance(new_erfrim, RIM):
            log_message(config, f"Saving salvaged RIM to '{savepath}'")
            write_rim(new_erfrim, savepath)
            return
        log_message(config, f"Whole erf/rim is corrupt: {resource!r}")
        return

    if isinstance(converted_data, bytearray):
        log_message(config, f"Saving conversions in ERF/RIM at '{savepath}'")
        lazy_capsule = LazyCapsule(savepath, create_nonexisting=True)
        lazy_capsule.delete(resource.resname(), resource.restype())
        lazy_capsule.add(resource.resname(), resource.restype(), bytes(converted_data))


def process_translations(
    tlk: TLK,
    from_lang: Language,
    config: PatchingConfig,
) -> None:
    """Process translations for a TLK file.

    Args:
    ----
        tlk: The TLK file to translate
        from_lang: Source language
        config: Patching configuration with translator
    """
    if not config.translator:
        return

    def translate_entry(tlkentry: TLKEntry, from_lang: Language) -> tuple[str, str]:
        text = tlkentry.text
        if not text.strip() or text.isdigit():
            return text, ""
        if "Do not translate this text" in text:
            return text, text
        if "actual text to be translated" in text:
            return text, text
        return text, config.translator.translate(text, from_lang=from_lang)

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.max_threads) as executor:
        future_to_strref: dict[concurrent.futures.Future[tuple[str, str]], int] = {
            executor.submit(translate_entry, tlkentry, from_lang): strref for strref, tlkentry in tlk
        }

        for future in concurrent.futures.as_completed(future_to_strref):
            strref: int = future_to_strref[future]
            try:
                original_text, translated_text = future.result()
                if translated_text.strip():
                    translated_text = fix_encoding(translated_text, config.translator.to_lang.get_encoding())
                    tlk.replace(strref, translated_text)
                    log_message(config, f"#{strref} Translated {original_text} --> {translated_text}")
            except Exception as exc:  # pylint: disable=W0718  # noqa: BLE001
                log_message(config, f"tlk strref {strref} generated an exception: {exc}")


def patch_resource(
    resource: FileResource,
    config: PatchingConfig,
    processed_files: set[Path] | None = None,
) -> GFF | TPC | None:
    """Patch a single resource (GFF, TPC, TLK).

    Args:
    ----
        resource: The resource to patch
        config: Patching configuration
        processed_files: Set to track processed files (optional)

    Returns:
    -------
        Patched GFF or TPC object, or None if no changes or error
    """
    if processed_files is None:
        processed_files = set()

    # Handle TLK translation
    if resource.restype().extension.lower() == "tlk" and config.translate and config.translator:
        tlk: TLK | None = None
        log_message(config, f"Loading TLK '{resource.filepath()}'")
        try:
            tlk = read_tlk(resource.data())
        except Exception:  # pylint: disable=W0718  # noqa: BLE001
            log_message(config, f"[Error] loading TLK '{resource.identifier()}' at '{resource.filepath()}'!")
            return None

        from_lang: Language = tlk.language
        new_filename_stem = f"{resource.resname()}_{config.translator.to_lang.get_bcp47_code() or 'UNKNOWN'}"
        new_file_path = resource.filepath().parent / f"{new_filename_stem}.{resource.restype().extension}"
        tlk.language = config.translator.to_lang
        log_message(config, f"Translating TalkTable resource at {resource.filepath()} to {config.translator.to_lang.name}")
        process_translations(tlk, from_lang, config)
        write_tlk(tlk, new_file_path)
        processed_files.add(new_file_path)

    # Handle TGA to TPC conversion
    if resource.restype().extension.lower() == "tga" and config.convert_tga == "TGA to TPC":
        log_message(config, f"Converting TGA at {resource.path_ident()} to TPC...")
        try:
            return TPCTGAReader(resource.data()).load()
        except Exception:  # pylint: disable=W0718  # noqa: BLE001
            log_message(config, f"[Error] loading TGA '{resource.identifier()}' at '{resource.filepath()}'!")
            return None

    # Handle TPC to TGA conversion
    if resource.restype().extension.lower() == "tpc" and config.convert_tga == "TPC to TGA":
        log_message(config, f"Converting TPC at {resource.path_ident()} to TGA...")
        try:
            return TPCBinaryReader(resource.data()).load()
        except Exception:  # pylint: disable=W0718  # noqa: BLE001
            log_message(config, f"[Error] loading TPC '{resource.identifier()}' at '{resource.filepath()}'!")
            return None

    # Handle GFF files
    if resource.restype().name.upper() in {x.name for x in GFFContent}:
        if config.k1_convert_gffs and not resource.inside_capsule:
            convert_gff_game(Game.K2, resource, config)
        if config.tsl_convert_gffs and not resource.inside_capsule:
            convert_gff_game(Game.K1, resource, config)

        gff: GFF | None = None
        try:
            gff = read_gff(resource.data())
            alien_owner: str | None = None
            if gff.content is GFFContent.DLG and config.set_unskippable:
                skippable = gff.root.acquire("Skippable", None)
                if skippable not in {0, "0"}:
                    conversationtype = gff.root.acquire("ConversationType", None)
                    if conversationtype not in {"1", 1}:
                        alien_owner = gff.root.acquire("AlienRaceOwner", None)  # TSL only

            made_change, alien_vo_count = patch_nested_gff(
                gff.root,
                gff_content=gff.content,
                gff=gff,
                config=config,
                current_path=resource.path_ident(),
            )

            if (
                config.set_unskippable
                and alien_owner in {0, "0", None}
                and alien_vo_count != -1
                and alien_vo_count < 3
                and gff.content is GFFContent.DLG
            ):
                skippable = gff.root.acquire("Skippable", None)
                if skippable not in {0, "0"}:
                    conversationtype = gff.root.acquire("ConversationType", None)
                    if conversationtype not in {"1", 1}:
                        log_message(config, f"Setting dialog {resource.path_ident()} as unskippable")
                        made_change = True
                        gff.root.set_uint8("Skippable", 0)

            if made_change:
                return gff
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            log_message(config, f"[Error] cannot load corrupted GFF '{resource.path_ident()}'!")
            if not isinstance(e, (OSError, ValueError)):
                log_message(config, f"[Error] loading GFF '{resource.path_ident()}'!")
            return None

    return None


def patch_and_save_noncapsule(
    resource: FileResource,
    config: PatchingConfig,
    savedir: Path | None = None,
) -> None:
    """Patch and save a non-capsule resource.

    Args:
    ----
        resource: The resource to patch
        config: Patching configuration
        savedir: Optional directory to save to
    """
    patched_data: GFF | TPC | None = patch_resource(resource, config)
    if patched_data is None:
        return

    capsule = Capsule(resource.filepath()) if resource.inside_capsule else None

    if isinstance(patched_data, GFF):
        new_data = bytes_gff(patched_data)

        new_gff_filename = resource.filename()
        if config.translate and config.translator:
            new_gff_filename = f"{resource.resname()}_{config.translator.to_lang.get_bcp47_code()}.{resource.restype().extension}"

        new_path = (savedir or resource.filepath().parent) / new_gff_filename
        if new_path.exists() and savedir:
            log_message(config, f"Skipping '{new_gff_filename}', already exists on disk")
        else:
            log_message(config, f"Saving patched gff to '{new_path}'")
            BinaryWriter.dump(new_path, new_data)

    elif isinstance(patched_data, TPC):
        if capsule is None:
            txi_file = resource.filepath().with_suffix(".txi")
            if txi_file.is_file():
                log_message(config, "Embedding TXI information...")
                data: bytes = txi_file.read_bytes()
                txi_text: str = decode_bytes_with_fallbacks(data)
                patched_data.txi = txi_text
        else:
            txi_data = capsule.resource(resource.resname(), ResourceType.TXI)
            if txi_data is not None:
                log_message(config, "Embedding TXI information from resource found in capsule...")
                txi_text = decode_bytes_with_fallbacks(txi_data)
                patched_data.txi = txi_text

        new_path = (savedir or resource.filepath().parent) / resource.resname()
        if config.convert_tga == "TGA to TPC":
            new_path = new_path.with_suffix(".tpc")
            TPCBinaryWriter(patched_data, new_path).write()
        else:
            new_path = new_path.with_suffix(".tga")
            TPCTGAWriter(patched_data, new_path).write()

        if new_path.exists():
            log_message(config, f"Skipping '{new_path}', already exists on disk")


def patch_capsule_file(
    c_file: Path,
    config: PatchingConfig,
    processed_files: set[Path] | None = None,
) -> None:
    """Patch a capsule file (ERF/RIM).

    Args:
    ----
        c_file: Path to the capsule file
        config: Patching configuration
        processed_files: Set to track processed files (optional)
    """
    if processed_files is None:
        processed_files = set()

    log_message(config, f"Load {c_file.name}")
    try:
        file_capsule = Capsule(c_file)
    except ValueError as e:
        log_message(config, f"Could not load '{c_file}'. Reason: {e}")
        return

    new_filepath: Path = c_file
    if config.translate and config.translator:
        new_filepath = c_file.parent / f"{c_file.stem}_{config.translator.to_lang.get_bcp47_code()}{c_file.suffix}"

    new_resources: list[tuple[str, ResourceType, bytes]] = []
    omitted_resources: list[ResourceIdentifier] = []
    for resource in file_capsule:
        if config.is_patching():
            patched_data: GFF | TPC | None = patch_resource(resource, config, processed_files)
            if isinstance(patched_data, GFF):
                new_data = bytes_gff(patched_data) if patched_data else resource.data()
                log_message(config, f"Adding patched GFF resource '{resource.identifier()}' to capsule {new_filepath.name}")
                new_resources.append((resource.resname(), resource.restype(), new_data))
                omitted_resources.append(resource.identifier())

            elif isinstance(patched_data, TPC):
                txi_resource = file_capsule.resource(resource.resname(), ResourceType.TXI)
                if txi_resource is not None:
                    patched_data.txi = txi_resource.decode("ascii", errors="ignore")
                    omitted_resources.append(ResourceIdentifier(resource.resname(), ResourceType.TXI))

        new_data = bytes_tpc(patched_data)
        log_message(config, f"Adding patched TPC resource '{resource.identifier()}' to capsule {new_filepath.name}")
        new_resources.append((resource.resname(), ResourceType.TPC, bytes(new_data)))
        omitted_resources.append(resource.identifier())

    if config.is_patching():
        erf_or_rim: ERF | RIM = ERF(ERFType.from_extension(new_filepath)) if is_any_erf_type_file(c_file) else RIM()
        for resource in file_capsule:
            if resource.identifier() not in omitted_resources:
                erf_or_rim.set_data(resource.resname(), resource.restype(), resource.data())
        for resinfo in new_resources:
            erf_or_rim.set_data(*resinfo)

        log_message(config, f"Saving back to {new_filepath.name}")
        if is_any_erf_type_file(c_file):
            write_erf(erf_or_rim, new_filepath)  # type: ignore[arg-type]
        else:
            write_rim(erf_or_rim, new_filepath)  # type: ignore[arg-type]


def patch_erf_or_rim(
    resources: list[FileResource],
    filename: str,
    erf_or_rim: RIM | ERF,
    config: PatchingConfig,
) -> Path:
    """Patch resources in an ERF or RIM.

    Args:
    ----
        resources: List of resources to patch
        filename: Original filename
        erf_or_rim: The ERF or RIM to patch
        config: Patching configuration

    Returns:
    -------
        New filename path
    """
    omitted_resources: list[ResourceIdentifier] = []
    new_filename = Path(filename)
    if config.translate and config.translator:
        new_filename = Path(f"{new_filename.stem}_{config.translator.to_lang.name}{new_filename.suffix}")

    for resource in resources:
        patched_data: GFF | TPC | None = patch_resource(resource, config)
        if isinstance(patched_data, GFF):
            log_message(config, f"Adding patched GFF resource '{resource.identifier()}' to {new_filename}")
            new_data: bytes = bytes_gff(patched_data) if patched_data else resource.data()
            erf_or_rim.set_data(resource.resname(), resource.restype(), new_data)
            omitted_resources.append(resource.identifier())

        elif isinstance(patched_data, TPC):
            log_message(config, f"Adding patched TPC resource '{resource.resname()}' to {new_filename}")
            txi_resource: FileResource | None = next(
                (res for res in resources if res.resname() == resource.resname() and res.restype() is ResourceType.TXI),
                None,
            )
            if txi_resource:
                patched_data.txi = txi_resource.data().decode("ascii", errors="ignore")
                omitted_resources.append(txi_resource.identifier())

            new_data = bytes_tpc(patched_data)
            erf_or_rim.set_data(resource.resname(), ResourceType.TPC, new_data)
            omitted_resources.append(resource.identifier())

    for resource in resources:
        if resource.identifier() not in omitted_resources:
            try:
                erf_or_rim.set_data(resource.resname(), resource.restype(), resource.data())
            except (OSError, ValueError):
                log_message(config, f"Corrupted resource: {resource!r}, skipping...")
            except Exception:
                log_message(config, f"Unexpected exception occurred for resource {resource!r}")

    return new_filename


def patch_file(
    file: Path | str,
    config: PatchingConfig,
    processed_files: set[Path] | None = None,
) -> None:
    """Patch a single file.

    Args:
    ----
        file: Path to file to patch
        config: Patching configuration
        processed_files: Set to track processed files (optional)
    """
    if processed_files is None:
        processed_files = set()

    c_file = Path(file)
    if c_file in processed_files:
        return

    if is_capsule_file(c_file):
        patch_capsule_file(c_file, config, processed_files)
    elif config.is_patching():
        patch_and_save_noncapsule(FileResource.from_path(c_file), config)


def patch_folder(
    folder_path: Path | str,
    config: PatchingConfig,
    processed_files: set[Path] | None = None,
) -> None:
    """Patch all files in a folder recursively.

    Args:
    ----
        folder_path: Path to folder to patch
        config: Patching configuration
        processed_files: Set to track processed files (optional)
    """
    if processed_files is None:
        processed_files = set()

    c_folderpath = Path(folder_path)
    log_message(config, f"Recursing through resources in the '{c_folderpath.name}' folder...")
    for file_path in c_folderpath.rglob("*"):
        patch_file(file_path, config, processed_files)


def is_kotor_install_dir(path: Path) -> bool:
    """Check if a path is a KOTOR installation directory.

    Args:
    ----
        path: Path to check

    Returns:
    -------
        True if path is a KOTOR installation directory
    """
    c_path: CaseAwarePath = CaseAwarePath(path)
    return bool(c_path.is_dir() and c_path.joinpath("chitin.key").is_file())


def patch_install(
    install_path: Path | str,
    config: PatchingConfig,
    processed_files: set[Path] | None = None,
) -> None:
    """Patch a KOTOR installation.

    Args:
    ----
        install_path: Path to KOTOR installation
        config: Patching configuration
        processed_files: Set to track processed files (optional)
    """
    if processed_files is None:
        processed_files = set()

    log_message(config, f"Using install dir for operations:\t{install_path}")

    k_install = Installation(install_path)
    if config.is_patching():
        log_message(config, "Patching modules...")
        if config.k1_convert_gffs or config.tsl_convert_gffs:
            for module_name in k_install._modules:  # noqa: SLF001
                log_message(config, f"Validating ERF/RIM in the Modules folder: '{module_name}'")
                module_path = k_install.module_path().joinpath(module_name)
                to_game = Game.K2 if config.tsl_convert_gffs else Game.K1
                erf_or_rim = validate_capsule(module_path, strict=True, game=to_game)
                if isinstance(erf_or_rim, ERF):
                    write_erf(erf_or_rim, module_path)
                elif isinstance(erf_or_rim, RIM):
                    write_rim(erf_or_rim, module_path)
                else:
                    log_message(config, f"Unknown ERF/RIM: '{module_path.relative_to(k_install.path().parent)}'")

        k_install.load_modules()
        for module_name, resources in k_install._modules.items():  # noqa: SLF001
            res_ident = ResourceIdentifier.from_path(module_name)
            filename = str(res_ident)
            filepath = k_install.path().joinpath("Modules", filename)
            if res_ident.restype is ResourceType.RIM:
                if filepath.with_suffix(".mod").is_file():
                    log_message(config, f"Skipping {filepath}, a .mod already exists at this path.")
                    continue
                new_rim = RIM()
                new_rim_filename = patch_erf_or_rim(resources, module_name, new_rim, config)
                log_message(config, f"Saving '{new_rim_filename}'")
                write_rim(new_rim, filepath.parent / new_rim_filename, res_ident.restype)

            elif res_ident.restype.name in (ResourceType.ERF, ResourceType.MOD, ResourceType.SAV):
                new_erf = ERF(ERFType.from_extension(filepath.suffix))
                if res_ident.restype is ResourceType.SAV:
                    new_erf.is_save = True
                new_erf_filename = patch_erf_or_rim(resources, module_name, new_erf, config)
                log_message(config, f"Saving '{new_erf_filename}'")
                write_erf(new_erf, filepath.parent / new_erf_filename, res_ident.restype)

            else:
                log_message(config, f"Unsupported module: {module_name} - cannot patch")

    if config.is_patching():
        log_message(config, "Patching Override...")
    override_path = k_install.override_path()
    override_path.mkdir(exist_ok=True, parents=True)
    for folder in k_install.override_list():
        for resource in k_install.override_resources(folder):
            if config.is_patching():
                patch_and_save_noncapsule(resource, config)

    if config.is_patching():
        log_message(config, "Extract and patch BIF data, saving to Override (will not overwrite)")
    for resource in k_install.core_resources():
        if config.translate or config.set_unskippable:
            patch_and_save_noncapsule(resource, savedir=override_path, config=config)

    patch_file(k_install.path().joinpath("dialog.tlk"), config, processed_files)


def determine_input_path(
    path: Path,
    config: PatchingConfig,
    processed_files: set[Path] | None = None,
) -> None:
    """Determine what type of path was provided and patch accordingly.

    Args:
    ----
        path: Path to patch
        config: Patching configuration
        processed_files: Set to track processed files (optional)
    """
    if not path.exists() or path.resolve() == Path.cwd().resolve():
        import errno
        raise FileNotFoundError(errno.ENOENT, f"No such file or directory: {path}")

    if is_kotor_install_dir(path):
        return patch_install(path, config, processed_files)

    if path.is_dir():
        return patch_folder(path, config, processed_files)

    if path.is_file():
        return patch_file(path, config, processed_files)

    return None

