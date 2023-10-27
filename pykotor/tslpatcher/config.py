from __future__ import annotations

import shutil
from configparser import ConfigParser
from datetime import datetime, timezone
from enum import IntEnum
from typing import TYPE_CHECKING

from pykotor.common.misc import Game

try:
    import chardet
except ImportError:
    chardet = None

from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import (
    Installation,
    SearchLocation,
)
from pykotor.resource.formats.erf import ERF, read_erf, write_erf
from pykotor.resource.formats.erf.erf_data import ERFType
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.ncs.ncs_auto import bytes_ncs, compile_nss
from pykotor.resource.formats.rim import RIM, read_rim, write_rim
from pykotor.resource.formats.ssf import read_ssf, write_ssf
from pykotor.resource.formats.tlk import read_tlk, write_tlk
from pykotor.resource.formats.twoda import read_2da, write_2da
from pykotor.tools.misc import (
    is_capsule_file,
    is_erf_or_mod_file,
    is_rim_file,
)
from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.install import InstallFolder, create_backup
from pykotor.tslpatcher.mods.tlk import ModificationsTLK

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.tslpatcher.mods.gff import ModificationsGFF
    from pykotor.tslpatcher.mods.nss import ModificationsNSS
    from pykotor.tslpatcher.mods.ssf import ModificationsSSF
    from pykotor.tslpatcher.mods.twoda import Modifications2DA


class LogLevel(IntEnum):
    # Docstrings taken from ChangeEdit docs

    NOTHING = 0
    """No feedback at all. The text from "info.rtf" will continue to be displayed during installation"""

    GENERAL = 1
    """Only general progress information will be displayed. Not recommended."""

    ERRORS = 2
    """General progress information is displayed, along with any serious errors encountered."""

    WARNINGS = 3
    """General progress information, serious errors and warnings are displayed. This is
    recommended for the release version of your mod."""

    FULL = 4
    """Full feedback. On top of what is displayed at level 3, it also shows verbose progress
    information that may be useful for a Modder to see what is happening. Intended for
    Debugging."""


class PatcherConfig:
    def __init__(self):
        self.window_title: str = ""
        self.confirm_message: str = ""
        self.game_number: int | None = None

        self.required_file: str | None = None
        self.required_message: str = ""

        self.install_list: list[InstallFolder] = []
        self.patches_2da: list[Modifications2DA] = []
        self.patches_gff: list[ModificationsGFF] = []
        self.patches_ssf: list[ModificationsSSF] = []
        self.patches_nss: list[ModificationsNSS] = []
        self.patches_tlk: ModificationsTLK = ModificationsTLK()

    def load(self, ini_text: str, mod_path: os.PathLike | str, logger: PatchLogger | None = None) -> None:
        from pykotor.tslpatcher.reader import ConfigReader

        ini = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
        )
        ini.optionxform = lambda optionstr: optionstr  # use case sensitive keys
        ini.read_string(ini_text)

        ConfigReader(ini, CaseAwarePath(mod_path), logger).load(self)

    def patch_count(self) -> int:
        return (
            len(self.patches_2da)
            + len(self.patches_gff)
            + len(self.patches_ssf)
            + 1
            + len(self.install_list)
            + len(self.patches_nss)
        )


class PatcherNamespace:
    def __init__(self):
        self.namespace_id: str = ""
        self.ini_filename: str = ""
        self.info_filename: str = ""
        self.data_folderpath: str = ""
        self.name: str = ""
        self.description: str = ""

    def __str__(self):
        return self.name


class ModInstaller:
    def __init__(
        self,
        mod_path: os.PathLike | str,
        game_path: os.PathLike | str,
        changes_ini_path: os.PathLike | str,
        logger: PatchLogger | None = None,
    ):
        self.log: PatchLogger = logger or PatchLogger()
        self.game_path: CaseAwarePath = CaseAwarePath(game_path)
        self.mod_path: CaseAwarePath = CaseAwarePath(mod_path)
        self.changes_ini_path: CaseAwarePath = CaseAwarePath(changes_ini_path)
        if not self.changes_ini_path.exists():  # handle legacy syntax
            self.changes_ini_path = self.mod_path / self.changes_ini_path.name
            if not self.changes_ini_path.exists():
                self.changes_ini_path = self.mod_path / "tslpatchdata" / self.changes_ini_path.name
            if not self.changes_ini_path.exists():
                msg = f"Could not find the changes ini file {self.changes_ini_path} on disk! Could not start install!"
                raise FileNotFoundError(msg)

        self._config: PatcherConfig | None = None

    def config(self) -> PatcherConfig:
        """Returns the PatcherConfig object associated with the mod installer. The object is created when the method is
        first called then cached for future calls.
        """
        if self._config is not None:
            return self._config

        ini_file_bytes = BinaryReader.load_file(self.changes_ini_path)

        ini = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
        )
        ini.optionxform = lambda optionstr: optionstr  # use case sensitive keys

        encoding = "utf8"
        if chardet:
            encoding = (chardet.detect(ini_file_bytes) or {}).get("encoding") or encoding
        ini_data: str | None = None
        try:
            ini_data = ini_file_bytes.decode(encoding)
        except UnicodeDecodeError:
            try:
                ini_data = ini_file_bytes.decode("cp1252")
            except UnicodeDecodeError:
                try:
                    ini_data = ini_file_bytes.decode("windows-1252")
                except UnicodeDecodeError:
                    self.log.add_warning(
                        f"Could not determine encoding of '{self.changes_ini_path.name}'. Attempting to force load...",
                    )
                    ini_data = ini_file_bytes.decode(errors="replace")
        ini_text = ini_data

        self._config = PatcherConfig()
        self._config.load(ini_text, self.mod_path, self.log)

        return self._config

    def game(self) -> Game:
        if (self.game_path.joinpath("streamvoice").exists() or self.game_path.joinpath("swkotor2.exe")):
            return Game(2)
        if (self.game_path.joinpath("streamwaves").exists() or self.game_path.joinpath("swkotor.exe")):
            return Game(1)
        msg = "Could not determine which KOTOR game to load!"
        raise ValueError(msg)

    def initialize_backup(self) -> CaseAwarePath:
        backup_dir = self.mod_path
        timestamp = datetime.now(tz=timezone.utc).astimezone().strftime("%Y-%m-%d_%H.%M.%S")
        while not backup_dir.joinpath("tslpatchdata").exists() and backup_dir.parent.name:
            backup_dir = backup_dir.parent
        uninstall_dir = backup_dir.joinpath("uninstall")
        try:
            if uninstall_dir.exists():
                shutil.rmtree(uninstall_dir)
        except PermissionError as e:
            self.log.add_warning(f"Could not initialize backup folder: {e}")
        backup_dir = backup_dir / "backup" / timestamp
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            self.log.add_warning(f"Could not create backup folder: {e}")
        self.log.add_note(f"Using backup directory: '{backup_dir}'")
        return backup_dir

    def install(self) -> None:
        config = self.config()
        if config.required_file:
            requiredfile_path = self.game_path / "Override" / config.required_file
            if not requiredfile_path.exists():
                raise ImportError(config.required_message.strip() or "cannot install - missing a required mod")

        installation = Installation(self.game_path, self.log)
        memory = PatcherMemory()

        # Create a timestamped backup directory
        backup_dir = self.initialize_backup()
        processed_files = set()

        self.log.add_note(f"Applying {len(config.patches_tlk.modifiers)} patches from [TLKList]...")
        if len(config.patches_tlk.modifiers) > 0:  # skip if no patches need to be made (faster)
            # sourcery skip: extract-method, move-assign-in-block, use-fstring-for-concatenation
            dialog_tlk_path = self.game_path.joinpath("dialog.tlk")

            create_backup(self.log, dialog_tlk_path, backup_dir, processed_files)

            self.log.add_note("Patching 'dialog.tlk'...")
            dialog_tlk = read_tlk(dialog_tlk_path)

            config.patches_tlk.apply(dialog_tlk, memory)
            write_tlk(dialog_tlk, dialog_tlk_path, strip_soundlength=self.game() == Game.K2)
            self.log.complete_patch()

        # Move nwscript.nss to Override if there are any nss patches to do
        # if len(config.patches_nss) > 0:
        #    folder_install = InstallFolder("Override")  # noqa: ERA001
        #    if folder_install not in config.install_list:
        #        config.install_list.append(folder_install)  # noqa: ERA001
        #    file_install = InstallFile("nwscript.nss", replace_existing=True)  # noqa: ERA001
        #    folder_install.files.append(file_install)  # noqa: ERA001

        self.log.add_note(f"Applying {len(config.install_list)} patches from [InstallList]...")
        for folder in config.install_list:
            folder.apply(self.log, self.mod_path, self.game_path, backup_dir, processed_files)
            self.log.complete_patch()

        self.log.add_note(f"Applying {len(config.patches_2da)} patches from [2DAList]...")
        for twoda_patch in config.patches_2da:
            twoda_output_filepath = self.game_path / "Override" / twoda_patch.filename

            create_backup(self.log, twoda_output_filepath, backup_dir, processed_files, subdirectory_path="Override")

            self.log.add_note(f"Patching '{twoda_patch.filename}' in the 'Override' folder.")
            search = installation.resource(
                *ResourceIdentifier.from_path(twoda_patch.filename),
                [SearchLocation.OVERRIDE, SearchLocation.CUSTOM_FOLDERS],
                folders=[self.mod_path],
            )
            if search is None:
                continue
            twoda: TwoDA = read_2da(search.data)

            twoda_patch.apply(twoda, memory)
            write_2da(twoda, twoda_output_filepath)
            self.log.complete_patch()

        self.log.add_note(f"Applying {len(config.patches_gff)} patches from [GFFList]...")
        for gff_patch in config.patches_gff:
            gff_output_container_path = self.game_path / gff_patch.destination
            rel_output_container_path = gff_output_container_path.relative_to(self.game_path)
            capsule: Capsule | None = None

            if is_capsule_file(gff_patch.destination.name):
                capsule = Capsule(gff_output_container_path)
                create_backup(self.log, gff_output_container_path, backup_dir, processed_files, rel_output_container_path.parent)
                if not capsule._path.exists():
                    self.log.add_error(
                        f"The capsule '{rel_output_container_path}' did not exist when patching GFF '{gff_patch.filename}'."
                        " This most likely indicates a different problem existed beforehand, such as a missing mod dependency.",
                    )
            else:
                create_backup(self.log, gff_output_container_path.joinpath(gff_patch.filename), backup_dir, processed_files, rel_output_container_path)

            self.log.add_note(f"Patching '{gff_patch.filename}' in the '{rel_output_container_path}' folder.")
            search = installation.resource(
                *ResourceIdentifier.from_path(gff_patch.filename),
                [SearchLocation.CUSTOM_FOLDERS] if gff_patch.replace_file else [SearchLocation.CUSTOM_MODULES, SearchLocation.OVERRIDE, SearchLocation.CUSTOM_FOLDERS],
                capsules=[capsule] if capsule else [],
                folders=[self.mod_path],
            )
            if not search:
                continue
            template = read_gff(search.data)

            gff_patch.apply(template, memory, self.log)
            self.write(gff_output_container_path, gff_patch.filename, bytes_gff(template), replace=True)
            self.log.complete_patch()

        self.log.add_note(f"Applying {len(config.patches_nss)} patches from [CompileList]...")
        for nss_patch in config.patches_nss:
            nss_output_container_path: CaseAwarePath = self.game_path / nss_patch.destination
            rel_output_container_path: CaseAwarePath = nss_output_container_path.relative_to(self.game_path)
            ncs_compiled_filename = f"{nss_patch.filename.rsplit('.', 1)[0]}.ncs"

            if is_capsule_file(nss_output_container_path.name):
                create_backup(self.log, nss_output_container_path, backup_dir, processed_files, rel_output_container_path.parent)
                if not nss_output_container_path.exists():
                    self.log.add_error(
                        f"The capsule '{rel_output_container_path}' did not exist when compiling NSS '{nss_patch.filename}'."
                        " This most likely indicates a different problem existed beforehand, such as a missing mod dependency.",
                    )
            else:
                create_backup(self.log, nss_output_container_path.joinpath(nss_patch.filename), backup_dir, processed_files, rel_output_container_path)

            self.log.add_note(f"Compiling '{nss_patch.filename}' and saving to '{rel_output_container_path / ncs_compiled_filename}'")
            nss_bytes = BinaryReader.load_file(self.mod_path / nss_patch.filename)
            encoding: str = (chardet and chardet.detect(nss_bytes) or {}).get("encoding") or "utf8"
            nss: list[str] = [nss_bytes.decode(encoding=encoding, errors="replace")]

            nss_patch.apply(nss, memory, self.log)
            self.write(nss_output_container_path, ncs_compiled_filename, bytes_ncs(compile_nss(nss[0], installation.game())), nss_patch.replace_file)
            self.log.complete_patch()

        self.log.add_note(f"Applying {len(config.patches_ssf)} patches from [SSFList]...")
        for ssf_patch in config.patches_ssf:
            ssf_output_filepath: CaseAwarePath = self.game_path / "Override" / ssf_patch.filename

            create_backup(self.log, ssf_output_filepath, backup_dir, processed_files, "Override")

            self.log.add_note(f"Patching '{ssf_patch.filename}' in the 'Override' folder.")
            search = installation.resource(
                *ResourceIdentifier.from_path(ssf_patch.filename),
                [SearchLocation.CUSTOM_FOLDERS] if ssf_patch.replace_file else [SearchLocation.OVERRIDE, SearchLocation.CUSTOM_FOLDERS],
                folders=[self.mod_path],
            )
            if search is None:
                continue
            soundset = read_ssf(search.data)

            ssf_patch.apply(soundset, memory)
            write_ssf(soundset, ssf_output_filepath)
            self.log.complete_patch()

    def write(self, destination: CaseAwarePath, filename: str, data: bytes, replace: bool = False) -> None:
        resname, restype = ResourceIdentifier.from_path(filename)
        if is_rim_file(destination.name):
            rim = read_rim(BinaryReader.load_file(destination)) if destination.exists() else RIM()
            if not rim.get(resname, restype) or replace:
                rim.set_data(resname, restype, data)
                write_rim(rim, destination)
        elif is_erf_or_mod_file(destination.name):
            erf = (
                read_erf(BinaryReader.load_file(destination))
                if destination.exists()
                else ERF(ERFType.from_extension(destination.name))
            )
            if not erf.get(resname, restype) or replace:
                erf.set_data(resname, restype, data)
                write_erf(erf, destination)
        elif not (destination / filename).exists() or replace:
            BinaryWriter.dump(destination / filename, data)
