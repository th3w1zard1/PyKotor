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
from pykotor.tools.path import CaseAwarePath, PurePath
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.install import InstallFolder, create_backup
from pykotor.tslpatcher.mods.tlk import ModificationsTLK

if TYPE_CHECKING:
    import os

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
        self._installation: Installation | None = None
        self._backup: CaseAwarePath | None = None
        self._processed_backup_files: set = set()

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

        if self._config.required_file:
            requiredfile_path = self.game_path / "Override" / self._config.required_file
            if not requiredfile_path.exists():
                raise ImportError(self._config.required_message.strip() or "cannot install - missing a required mod")
        return self._config

    def installation(self):
        if self._installation:
            return self._installation
        self._installation = Installation(self.game_path, self.log)
        return self._installation

    def game(self) -> Game:
        if (self.game_path.joinpath("streamvoice").exists() or self.game_path.joinpath("swkotor2.exe")):
            return Game(2)
        if (self.game_path.joinpath("streamwaves").exists() or self.game_path.joinpath("swkotor.exe")):
            return Game(1)
        msg = "Could not determine which KOTOR game to load!"
        raise ValueError(msg)

    def backup(self) -> tuple[CaseAwarePath, set]:
        if self._backup:
            return (self._backup, self._processed_backup_files)
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
        self._backup = backup_dir
        self._processed_backup_files = set()
        return (self._backup, self._processed_backup_files)

    def handle_capsule_and_backup(self, patch, output_container_path: CaseAwarePath) -> Capsule | None:
        capsule = None
        if is_capsule_file(patch.destination):
            capsule = Capsule(output_container_path)
            create_backup(self.log, output_container_path, *self.backup(), patch.destination.parent)
        else:
            create_backup(self.log, output_container_path.joinpath(patch.filename), *self.backup(), patch.destination)
        return capsule

    def lookup_resource(self, patch, capsule=None):
        return self.installation().resource(
            *ResourceIdentifier.from_path(patch.filename),
            [SearchLocation.CUSTOM_FOLDERS] if hasattr(patch, "replace_file") and patch.replace_file else [SearchLocation.CUSTOM_MODULES, SearchLocation.OVERRIDE, SearchLocation.CUSTOM_FOLDERS],
            capsules=[capsule] if capsule else [],
            folders=[self.mod_path],
        )

    def do_patchlist(self, patch_list, section_name, game=None):
        self.log.add_note(f"Applying {len(patch_list)} patches from [{section_name}]...")
        for patch in patch_list:
            output_container_path = self.game_path / patch.destination
            capsule = self.handle_capsule_and_backup(patch, output_container_path)
            search = self.lookup_resource(patch, capsule)
            if not search:
                continue
            data = self.load_data(search, patch)
            self.save_data(data, patch, memory, output_container_path, game)
            self.log.complete_patch()


    def install(self) -> None:
        config = self.config()
        installation = self.installation()
        memory = PatcherMemory()

        def should_patch(
            patch,
            exists: bool = False,
            capsule: Capsule | None = None,
            no_replacefile_check: bool | None = None,  # !ReplaceFile handled differently in lookup_resource for GFFList and SSFList
            action: str = "Patching",
        ):
            local_folder = self.game_path.name if patch.destination == "." else patch.destination
            container_type = "folder" if capsule is None else "archive"
            is_replaceable = hasattr(patch, "replace_file")
            replace_file = is_replaceable and patch.replace_file

            if (replace_file or no_replacefile_check) and exists:
                if capsule:
                    self.log.add_note(f"{action} '{patch.filename}' and replacing existing resource in the '{local_folder}' archive")
                else:
                    self.log.add_note(f"{action} '{patch.filename}' and replacing existing file in the '{local_folder}' folder")
            elif exists and is_replaceable:
                if capsule and not capsule._path.exists():
                    self.log.add_error(f"The capsule '{patch.destination}' did not exist when attempting to patch GFF '{patch.filename}'. Skipping file...")
                else:
                    self.log.add_warning(f"'{patch.filename}' already exists in the '{local_folder}' {container_type}. Skipping file...")
                return False
            else:
                self.log.add_note(f"{action} '{patch.filename}' and {'adding' if capsule else 'saving'} to the '{local_folder}' {container_type}")
            return True

        self.log.add_note(f"Applying {len(config.patches_tlk.modifiers)} patches from [TLKList]...")
        if len(config.patches_tlk.modifiers) > 0:  # skip if no patches need to be made (faster)
            # def get_patch_paths
            dialog_tlk_path = self.game_path.joinpath(config.patches_tlk.filename)

            # def handle_encapsulated
            create_backup(self.log, dialog_tlk_path, *self.backup())
            should_patch(config.patches_tlk)

            # def lookup_resource --> returns search (None for patches_tlk)
            # def load_data --> returns dialog_tlk
            dialog_tlk = read_tlk(dialog_tlk_path)

            # def save_data
            config.patches_tlk.apply(dialog_tlk, memory)
            write_tlk(dialog_tlk, dialog_tlk_path)
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
            folder.apply(self.log, self.mod_path, self.game_path, *self.backup())
            self.log.complete_patch()

        self.log.add_note(f"Applying {len(config.patches_2da)} patches from [2DAList]...")
        for patch in config.patches_2da:
            output_container_path = self.game_path / patch.destination
            output_file_path = output_container_path.joinpath(patch.filename)

            create_backup(self.log, output_file_path, *self.backup(), patch.destination)
            should_patch(patch, output_file_path.exists())

            search = self.lookup_resource(patch)
            if not search:
                continue

            template = read_2da(search.data)
            patch.apply(template, memory)
            write_2da(template, output_file_path)
            self.log.complete_patch()

        self.log.add_note(f"Applying {len(config.patches_gff)} patches from [GFFList]...")
        for patch in config.patches_gff:
            output_container_path = self.game_path / patch.destination
            capsule: Capsule | None = None
            exists: bool | None = None

            if is_capsule_file(patch.destination):
                capsule = Capsule(output_container_path)
                create_backup(self.log, output_container_path, *self.backup(), PurePath(patch.destination).parent)
                exists = capsule.exists(*ResourceIdentifier.from_path(patch.filename))
            else:
                create_backup(self.log, output_container_path.joinpath(patch.filename), *self.backup(), patch.destination)
                exists = output_container_path.joinpath(patch.filename).exists()

            should_patch(patch, exists, capsule, no_replacefile_check=True)

            search = self.lookup_resource(patch, capsule)
            if not search:
                continue

            template = read_gff(search.data)
            patch.apply(template, memory, self.log)
            self.write(output_container_path, patch.filename, bytes_gff(template))
            self.log.complete_patch()

        self.log.add_note(f"Applying {len(config.patches_nss)} patches from [CompileList]...")
        for patch in config.patches_nss:
            output_container_path = self.game_path / patch.destination
            ncs_compiled_filename = f"{patch.filename.rsplit('.', 1)[0]}.ncs"

            create_backup(self.log, output_container_path.joinpath(patch.filename), *self.backup(), patch.destination)
            if not should_patch(
                patch,
                output_container_path.joinpath(ncs_compiled_filename).exists(),
                action="Compiling",
            ):
                continue

            nss_bytes = BinaryReader.load_file(self.mod_path / patch.filename)
            encoding: str = (chardet and chardet.detect(nss_bytes) or {}).get("encoding") or "utf8"
            template = [nss_bytes.decode(encoding=encoding, errors="replace")]

            patch.apply(template, memory, self.log)
            self.write(output_container_path, ncs_compiled_filename, bytes_ncs(compile_nss(template[0], installation.game())))
            self.log.complete_patch()

        self.log.add_note(f"Applying {len(config.patches_ssf)} patches from [SSFList]...")
        for patch in config.patches_ssf:
            output_container_path = self.game_path / patch.destination
            output_file_path = output_container_path.joinpath(patch.filename)

            create_backup(self.log, output_file_path, *self.backup(), patch.destination)
            should_patch(patch, output_file_path.exists(), no_replacefile_check=True)

            search = self.lookup_resource(patch)
            if not search:
                continue

            template = read_ssf(search.data)
            patch.apply(template, memory)
            write_ssf(template, output_file_path)
            self.log.complete_patch()

        self.log.add_note(f"Successfully completed {self.log.patches_completed} total patches.")

    def write(self, destination: CaseAwarePath, filename: str, data: bytes) -> None:
        if is_rim_file(destination.name):
            rim = (
                read_rim(BinaryReader.load_file(destination))
                if destination.exists()
                else RIM()
            )
            rim.set_data(*ResourceIdentifier.from_path(filename), data)
            write_rim(rim, destination)
        elif is_erf_or_mod_file(destination.name):
            erf = (
                read_erf(BinaryReader.load_file(destination))
                if destination.exists()
                else ERF(ERFType.from_extension(destination.name))
            )
            erf.set_data(*ResourceIdentifier.from_path(filename), data)
            write_erf(erf, destination)
        else:
            BinaryWriter.dump(destination / filename, data)
