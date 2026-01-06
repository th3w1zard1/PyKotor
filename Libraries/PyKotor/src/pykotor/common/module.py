from __future__ import annotations

import errno
import os

from contextlib import suppress
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Collection, Generic, TypeVar, TypedDict, cast

from loggerplus import RobustLogger

from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import FileResource, LocationResult, ResourceIdentifier
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm.bwm_auto import bytes_bwm, read_bwm, write_bwm
from pykotor.resource.formats.erf.erf_auto import read_erf, write_erf
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.formats.gff.gff_data import GFF, GFFFieldType
from pykotor.resource.formats.lyt.lyt_auto import bytes_lyt, read_lyt, write_lyt
from pykotor.resource.formats.lyt.lyt_data import LYT
from pykotor.resource.formats.ncs.ncs_auto import write_ncs
from pykotor.resource.formats.rim.rim_auto import read_rim, write_rim
from pykotor.resource.formats.tpc.tpc_auto import bytes_tpc, read_tpc, write_tpc
from pykotor.resource.formats.vis.vis_auto import bytes_vis, read_vis, write_vis
from pykotor.resource.formats.vis.vis_data import VIS
from pykotor.resource.generics.are import bytes_are, read_are, write_are
from pykotor.resource.generics.dlg import bytes_dlg, read_dlg, write_dlg
from pykotor.resource.generics.git import GIT, bytes_git, read_git, write_git
from pykotor.resource.generics.ifo import IFO, bytes_ifo, read_ifo, write_ifo
from pykotor.resource.generics.pth import bytes_pth, read_pth, write_pth
from pykotor.resource.generics.utc import UTC, bytes_utc, read_utc, write_utc
from pykotor.resource.generics.utd import UTD, bytes_utd, read_utd, write_utd
from pykotor.resource.generics.ute import UTE, bytes_ute, read_ute, write_ute
from pykotor.resource.generics.uti import bytes_uti, read_uti, write_uti
from pykotor.resource.generics.utm import UTM, bytes_utm, read_utm, write_utm
from pykotor.resource.generics.utp import UTP, bytes_utp, read_utp, write_utp
from pykotor.resource.generics.uts import UTS, bytes_uts, read_uts, write_uts
from pykotor.resource.generics.utt import UTT, bytes_utt, read_utt, write_utt
from pykotor.resource.generics.utw import UTW, bytes_utw, read_utw, write_utw
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_rim_file
from pykotor.tools.model import iterate_lightmaps, iterate_textures
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Iterable

    from typing_extensions import Self  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.misc import Game
    from pykotor.extract.file import LocationResult, ResourceResult
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.erf.erf_data import ERF
    from pykotor.resource.formats.gff.gff_data import GFF, GFFList
    from pykotor.resource.formats.mdl.mdl_data import MDL
    from pykotor.resource.formats.rim.rim_data import RIM
    from pykotor.resource.formats.tpc.tpc_data import TPC
    from pykotor.resource.generics.are import ARE
    from pykotor.resource.generics.ifo import IFO
    from pykotor.resource.generics.pth import PTH
    from pykotor.resource.generics.uti import UTI
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES

T = TypeVar("T")
SEARCH_ORDER: list[SearchLocation] = [
    SearchLocation.OVERRIDE,
    SearchLocation.CUSTOM_MODULES,
    SearchLocation.CHITIN,
]


class KModuleType(Enum):
    """Module file type enumeration.
    
    KotOR modules are split across multiple archive files. The module system
    uses different file extensions to organize resources by type and priority.
    
    References:
    ----------
        Original BioWare Odyssey Engine (module archive structure)
        Note: Module file organization varies between KotOR 1 and KotOR 2
    
    File Organization:
    -----------------
        - MAIN (.rim): Contains core module files (IFO, ARE, GIT) - only loaded in simple mode
        - AREA (_a.rim): Area-specific RIM (complex mode) - replaces .rim
        - AREA_EXTENDED (_adx.rim): Extended area RIM (complex mode) - replaces .rim if _a.rim not found
        - DATA (_s.rim): Contains module data (creatures, items, placeables, etc.)
        - K2_DLG (_dlg.erf): KotOR 2 only - contains dialog files
        - MOD (.mod): Community override format, replaces all above files
    
    Reverse Engineering Notes:
    -------------------------
        Based on swkotor.exe: FUN_004094a0 and swkotor2.exe: FUN_004096b0
        - Simple Mode (flag at offset 0x54 == 0): Loads .rim directly
        - Complex Mode (flag != 0): Checks for _a.rim, _adx.rim, .mod, _s.rim, _dlg.erf
        - _a.rim and _adx.rim REPLACE .rim in complex mode
        - .mod REPLACES all other files if it exists
    """
    MAIN = ".rim"  # Contains the IFO/ARE/GIT
    """Main module archive containing core module files.
    
    Reference: Original BioWare Odyssey Engine module structure
    Contains: IFO (module info), ARE (area data), GIT (dynamic area info)
    File naming: <modulename>.rim
    Note: Only loaded in simple mode (flag at offset 0x54 == 0)
    swkotor.exe: FUN_004094a0 line 32-42
    """
    
    AREA = "_a.rim"  # Area-specific RIM (complex mode)
    """Area-specific module archive (complex mode).
    
    Reference: swkotor.exe: FUN_004094a0 line 61, 159
    Contains: ARE (area data) and related area resources
    File naming: <modulename>_a.rim
    Behavior: REPLACES .rim in complex mode
    """
    
    AREA_EXTENDED = "_adx.rim"  # Extended area RIM (complex mode)
    """Extended area module archive (complex mode).
    
    Reference: swkotor.exe: FUN_004094a0 line 74, 85
    Contains: ARE (area data) and extended area resources
    File naming: <modulename>_adx.rim
    Behavior: REPLACES .rim if _a.rim not found
    """
    
    DATA = "_s.rim"  # Contains everything else
    """Data module archive containing module resources.
    
    Reference: Original BioWare Odyssey Engine module structure
    Contains: UTC, UTD, UTE, UTI, UTM, UTP, UTS, UTT, UTW, FAC, LYT, NCS, PTH
    File naming: <modulename>_s.rim
    Note: In KotOR 2, DLG files are NOT in _s.rim (see K2_DLG)
    """
    
    K2_DLG = "_dlg.erf"  # In TSL, DLGs are here instead of _s.rim.
    """KotOR 2 dialog archive containing dialog files.
    
    Reference: Original BioWare Odyssey Engine (KotOR 2 only)
    Contains: DLG (dialog) files
    File naming: <modulename>_dlg.erf
    Note: KotOR 1 stores DLG files in _s.rim, KotOR 2 uses separate _dlg.erf
    """
    
    MOD = ".mod"  # Community-standard override, takes priority over the above 3 files. This extension overrides all 3 of the above, while the other 3 are complementary to each other.
    """Community override module archive (single-file format).
    
    Reference: TSLPatcher modding community standard
    Contains: All module resources in a single ERF archive
    File naming: <modulename>.mod
    Priority: Takes precedence over .rim/_s.rim/_dlg.erf files
    Note: This is a modding convention, not used by the original game engine
    """

    def contains(  # noqa: PLR0911
        self,
        restype: ResourceType,
        *,
        game: Game | None = None,
    ) -> bool:
        """Whether this ModuleType, if not modified, would contain the specified ResourceType or not.

        Args:
        ----
            restype (ResourceType): The type of resource to check.
            game (Game | None = None): Optional game to determine whether to invalidate _s.rim if they contain DLGs.

        Returns:
        -------
            bool: Whether this ModuleType should contain the ResourceType or not.
        """
        if restype.target_type() is not restype:
            return False
        if restype is ResourceType.DLG:
            if game is None:
                return self is self.DATA or self is self.K2_DLG
            if game.is_k1():
                return self is self.DATA
            if game.is_k2():
                return self is self.K2_DLG

        if self is self.MOD:
            return self is not ResourceType.TwoDA
        if self is self.MAIN:
            return restype in {ResourceType.ARE, ResourceType.IFO, ResourceType.GIT}
        # _a.rim and _adx.rim contain ARE resources (swkotor.exe: FUN_004094a0 line 61, 74 - checks for ARE type 0xbba)
        if self is self.AREA or self is self.AREA_EXTENDED:
            return restype in {ResourceType.ARE, ResourceType.IFO, ResourceType.GIT}
        if self is self.DATA:
            return restype in {
                ResourceType.FAC,
                ResourceType.LYT,
                ResourceType.NCS,
                ResourceType.PTH,
                ResourceType.UTC,
                ResourceType.UTD,
                ResourceType.UTE,
                ResourceType.UTI,
                ResourceType.UTM,
                ResourceType.UTP,
                ResourceType.UTS,
                ResourceType.UTT,
                ResourceType.UTW,
            }
        raise RuntimeError(f"Invalid ModuleType enum: {self!r}")


@dataclass(frozen=True)
class ModulePieceInfo:
    root: str
    modtype: KModuleType

    @classmethod
    def from_filename(
        cls,
        filename: str | ResourceIdentifier,
    ) -> Self:
        if isinstance(filename, ResourceIdentifier):
            filename = str(filename)
        root = Module.name_to_root(filename)
        return cls(root, KModuleType(filename[len(root) :]))

    def filename(self) -> str:
        return self.root + self.modtype.value

    def res_ident(self) -> ResourceIdentifier:
        return ResourceIdentifier.from_path(self.filename())

    def resname(self) -> str:
        filename = self.filename()
        return filename[: filename.index(".")]

    def restype(self) -> ResourceType:
        return ResourceType.from_extension(self.modtype.value)


class ModulePieceResource(Capsule):
    def __new__(
        cls,
        path: os.PathLike | str,
        *args,
        **kwargs,
    ):
        new_cls = cls
        if new_cls is ModulePieceResource:
            path_obj = CaseAwarePath(path)
            piece_info = ModulePieceInfo.from_filename(path_obj.name)
            if piece_info.modtype is KModuleType.DATA:
                new_cls = ModuleDataPiece
            elif piece_info.modtype is KModuleType.MAIN:
                new_cls = ModuleLinkPiece
            elif piece_info.modtype is KModuleType.AREA:
                new_cls = ModuleLinkPiece  # _a.rim uses same structure as .rim
            elif piece_info.modtype is KModuleType.AREA_EXTENDED:
                new_cls = ModuleLinkPiece  # _adx.rim uses same structure as .rim
            elif piece_info.modtype is KModuleType.K2_DLG:
                new_cls = ModuleDLGPiece
            elif piece_info.modtype is KModuleType.MOD:
                new_cls = ModuleFullOverridePiece
        return object.__new__(new_cls)  # pyright: ignore[reportArgumentType]

    def __init__(
        self,
        path: os.PathLike | str,
        *args,
        **kwargs,
    ):
        path_obj = CaseAwarePath(path)
        self.piece_info: ModulePieceInfo = ModulePieceInfo.from_filename(path_obj.name)
        self.missing_resources: list[FileResource] = []  # TODO(th3w1zard1):
        super().__init__(path_obj, *args, **kwargs)

    def __reduce__(self):
        # Return a tuple with the callable, arguments, and state
        return (self.__class__, (str(self.filepath()),), self.__getstate__())

    def __getstate__(self):
        state = self.__dict__.copy()
        # Remove or modify any non-picklable attributes if necessary
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)


class ModuleLinkPiece(ModulePieceResource):
    def ifo(self) -> GFF:
        lookup = self.resource("module", ResourceType.IFO)
        if lookup is None:
            import errno

            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(self.filepath().joinpath("module.ifo")))
        return read_gff(lookup)

    def module_id(self) -> ResRef | None:
        """Get the module id, attempt to just check resrefs, fallback to the Mod_Area_list."""
        link_resources: set[FileResource] = {resource for resource in self._resources if resource.restype() is not ResourceType.IFO and KModuleType.MAIN.contains(resource.restype())}
        if link_resources:
            check_resname = next(iter(link_resources)).identifier().lower_resname
            if all(check_resname == res.identifier().lower_resname for res in link_resources):
                print(f"Module ID, Check 1: All link resources have the same resref of '{check_resname}'")
                return ResRef(check_resname)

        gff_ifo: GFF = self.ifo()
        if gff_ifo.root.exists("Mod_Area_list"):
            actual_ftype: GFFFieldType = gff_ifo.root.what_type("Mod_Area_list")
            if actual_ftype != GFFFieldType.List:
                RobustLogger().warning(f"{self.filename()} has IFO with incorrect field 'Mod_Area_list' type '{actual_ftype.name}', expected 'List'")
            else:
                area_list: GFFList | None = gff_ifo.root.get_list("Mod_Area_list")
                if area_list is None:
                    RobustLogger().error(f"{self.filename()}: Module.IFO has a Mod_Area_list field, but it is not a valid list.")
                    return None
                area_localized_name: ResRef | None = next((gff_struct.get_resref("Area_Name") for gff_struct in area_list if gff_struct.exists("Area_Name")), None)
                if area_localized_name is not None and str(area_localized_name).strip():
                    print(f"Module ID, Check 2: Found in Mod_Area_list: '{area_localized_name}'")
                    return area_localized_name
            print(f"{self.filename()}: Module.IFO does not contain a valid Mod_Area_list. Could not get the module id!")
        else:
            RobustLogger().error(f"{self.filename()}: Module.IFO does not have an existing Mod_Area_list.")
        return None

    def area_name(self) -> LocalizedString | ResRef:
        """See if the ARE is already cached, otherwise use the fallback."""
        area_file_res: FileResource | None = next((resource for resource in self._resources if resource.restype() is ResourceType.ARE), None)
        if area_file_res is not None:
            gff_are: GFF = read_gff(area_file_res.data())
            if gff_are.root.exists("Name"):
                actual_ftype: GFFFieldType = gff_are.root.what_type("Name")
                if actual_ftype != GFFFieldType.LocalizedString:
                    raise ValueError(f"{self.filename()} has IFO with incorrect field 'Name' type '{actual_ftype.name}', expected 'LocalizedString'")
                result: LocalizedString | None = gff_are.root.get_locstring("Name")
                if result is None:
                    RobustLogger().error(f"{self.filename()}: ARE has a Name field, but it is not a valid LocalizedString.")
                    return LocalizedString.from_invalid()
                print(f"Check 1 result: '{result}'")
                return result
        raise ValueError(f"Failed to find an ARE for module '{self.piece_info.filename()}'")


class ModuleDataPiece(ModulePieceResource): ...


class ModuleDLGPiece(ModulePieceResource): ...


class ModuleFullOverridePiece(ModuleDLGPiece, ModuleDataPiece, ModuleLinkPiece): ...


class _CapsuleDictTypes(TypedDict, total=False):
    MAIN: ModuleLinkPiece | None
    AREA: ModuleLinkPiece | None
    AREA_EXTENDED: ModuleLinkPiece | None
    DATA: ModuleDataPiece | None
    K2_DLG: ModuleDLGPiece | None
    MOD: ModuleFullOverridePiece | None


class Module:  # noqa: PLR0904
    """Represents a KotOR game module with its resources and archives.
    
    A Module aggregates resources from multiple archive files (.rim, _s.rim, _dlg.erf)
    or a single override archive (.mod). It manages resource loading, activation,
    and provides access to module-specific resources like areas, creatures, items, etc.
    
    References:
    ----------
        Original BioWare Odyssey Engine (module resource management)
    
    Attributes:
    ----------
        resources: Dictionary mapping ResourceIdentifier to ModuleResource.
            All resources available in this module, keyed by identifier for uniqueness.
        
        dot_mod: Whether this module uses .mod override format.
            Reference: TSLPatcher modding convention
            If True, uses <root>.mod archive; if False, uses .rim/_s.rim/_dlg.erf archives.
        
        _installation: Cached Installation instance for resource lookups.
            Used to resolve resources from chitin, override, and other locations.
        
        _root: Root module name (without extensions).
            Extracted from filename, used to construct archive filenames.
        
        _cached_mod_id: Cached module ResRef identifier.
            Module identifier extracted from IFO or archive filenames.
        
        _cached_sort_id: Cached sort identifier for module ordering.
            PyKotor-specific: Used for module sorting/ordering in tools.
        
        _capsules: Dictionary of module archive capsules.
            Contains ModuleLinkPiece, ModuleDataPiece, ModuleDLGPiece, or ModuleFullOverridePiece
            depending on module type and available files.
    """
    def __init__(
        self,
        filename_or_root: str,  # The root name of the module.
        installation: Installation,  # Cached installation instance.
        *,
        use_dot_mod: bool = True,  # Should this Module instance represent the .rim/_s.rim/._dlg.erf vanilla archives, or the singular `root`.mod override archive?
        load_textures: bool = True,  # Whether to crawl model references to locate textures/lightmaps.
    ):
        self.resources: dict[ResourceIdentifier, ModuleResource] = {}  # The keys are only used for ensured uniqueness.
        self.dot_mod: bool = use_dot_mod
        self._installation: Installation = installation
        self._root: str = self.name_to_root(filename_or_root.lower())
        self._cached_mod_id: ResRef | None = None
        self._cached_sort_id: str | None = None
        self._load_textures: bool = load_textures

        # Build all capsules relevant to this root in the provided installation
        # Based on swkotor.exe: FUN_004094a0 and swkotor2.exe: FUN_004096b0
        self._capsules: _CapsuleDictTypes = {
            KModuleType.MAIN.name: None,
            KModuleType.AREA.name: None,
            KModuleType.AREA_EXTENDED.name: None,
            KModuleType.DATA.name: None,
            KModuleType.K2_DLG.name: None,
            KModuleType.MOD.name: None,
        }
        module_path = installation.module_path()
        
        if self.dot_mod:
            # .mod file overrides all rim-like files
            # swkotor.exe: FUN_004094a0 line 136: Loads .mod, skips _s.rim
            mod_filepath = module_path.joinpath(self._root + KModuleType.MOD.value)
            if mod_filepath.is_file():
                self._capsules[KModuleType.MOD.name] = ModuleFullOverridePiece(mod_filepath)  # pyright: ignore[reportGeneralTypeIssues]
            else:
                self.dot_mod = False
                # Fallback to rim files when .mod doesn't exist
                self._capsules[KModuleType.MAIN.name] = ModuleLinkPiece(module_path.joinpath(self._root + KModuleType.MAIN.value))  # pyright: ignore[reportGeneralTypeIssues]
                self._capsules[KModuleType.DATA.name] = ModuleDataPiece(module_path.joinpath(self._root + KModuleType.DATA.value))  # pyright: ignore[reportGeneralTypeIssues]
                if self._installation.game().is_k2():
                    self._capsules[KModuleType.K2_DLG.name] = ModuleDLGPiece(module_path.joinpath(self._root + KModuleType.K2_DLG.value))  # pyright: ignore[reportGeneralTypeIssues]
        else:
            # Complex mode: Check for _a.rim or _adx.rim (replaces .rim), then _s.rim and _dlg.erf
            # swkotor.exe: FUN_004094a0 line 49-216
            area_rim_path = module_path.joinpath(self._root + KModuleType.AREA.value)
            area_extended_rim_path = module_path.joinpath(self._root + KModuleType.AREA_EXTENDED.value)
            
            # Step 1: Load _a.rim if exists (REPLACES .rim)
            # swkotor.exe: FUN_004094a0 line 159
            if area_rim_path.is_file():
                self._capsules[KModuleType.AREA.name] = ModuleLinkPiece(area_rim_path)  # pyright: ignore[reportGeneralTypeIssues]
            # Step 2: Load _adx.rim if _a.rim not found (REPLACES .rim)
            # swkotor.exe: FUN_004094a0 line 85
            elif area_extended_rim_path.is_file():
                self._capsules[KModuleType.AREA_EXTENDED.name] = ModuleLinkPiece(area_extended_rim_path)  # pyright: ignore[reportGeneralTypeIssues]
            else:
                # Simple mode: Just load .rim file directly
                # swkotor.exe: FUN_004094a0 line 32-42
                self._capsules[KModuleType.MAIN.name] = ModuleLinkPiece(module_path.joinpath(self._root + KModuleType.MAIN.value))  # pyright: ignore[reportGeneralTypeIssues]
            
            # Step 3: Load _s.rim if exists (ADDS to base)
            # swkotor.exe: FUN_004094a0 line 118 (only if .mod not found)
            data_rim_path = module_path.joinpath(self._root + KModuleType.DATA.value)
            if data_rim_path.is_file():
                self._capsules[KModuleType.DATA.name] = ModuleDataPiece(data_rim_path)  # pyright: ignore[reportGeneralTypeIssues]
            
            # Step 4: Load _dlg.erf if exists (K2 only, ADDS to base)
            # swkotor2.exe: FUN_004096b0 line 147 (only if .mod not found)
            if self._installation.game().is_k2():
                dlg_erf_path = module_path.joinpath(self._root + KModuleType.K2_DLG.value)
                if dlg_erf_path.is_file():
                    self._capsules[KModuleType.K2_DLG.name] = ModuleDLGPiece(dlg_erf_path)  # pyright: ignore[reportGeneralTypeIssues]

        self.reload_resources()

    @classmethod
    def get_capsules_dict_matching(
        cls,
        install_or_path: Installation | Path,
        filename: str,
    ) -> _CapsuleDictTypes:
        from pykotor.extract.installation import Installation

        root = cls.name_to_root(filename)
        # Build all capsules relevant to this root in the provided installation
        # Based on swkotor.exe: FUN_004094a0 and swkotor2.exe: FUN_004096b0
        capsules: _CapsuleDictTypes = {
            KModuleType.MAIN.name: None,
            KModuleType.AREA.name: None,
            KModuleType.AREA_EXTENDED.name: None,
            KModuleType.DATA.name: None,
            KModuleType.K2_DLG.name: None,
            KModuleType.MOD.name: None,
        }
        module_path: Path = install_or_path if isinstance(install_or_path, Path) else install_or_path.module_path()
        
        if filename.lower().endswith(".mod"):
            mod_filepath = module_path.joinpath(root + KModuleType.MOD.value)
            if mod_filepath.is_file():
                capsules[KModuleType.MOD.name] = ModuleFullOverridePiece(mod_filepath)  # pyright: ignore[reportGeneralTypeIssues]
            else:
                # Engine is permissive: fall back to rim files when .mod doesn't exist
                capsules[KModuleType.MAIN.name] = ModuleLinkPiece(module_path.joinpath(root + KModuleType.MAIN.value))  # pyright: ignore[reportGeneralTypeIssues]
                capsules[KModuleType.DATA.name] = ModuleDataPiece(module_path.joinpath(root + KModuleType.DATA.value))  # pyright: ignore[reportGeneralTypeIssues]
                if not isinstance(install_or_path, Installation) or install_or_path.game().is_k2():
                    capsules[KModuleType.K2_DLG.name] = ModuleDLGPiece(module_path.joinpath(root + KModuleType.K2_DLG.value))  # pyright: ignore[reportGeneralTypeIssues]
        else:
            # Complex mode: Check for _a.rim or _adx.rim (replaces .rim), then _s.rim and _dlg.erf
            area_rim_path = module_path.joinpath(root + KModuleType.AREA.value)
            area_extended_rim_path = module_path.joinpath(root + KModuleType.AREA_EXTENDED.value)
            
            # Load _a.rim if exists (REPLACES .rim)
            if area_rim_path.is_file():
                capsules[KModuleType.AREA.name] = ModuleLinkPiece(area_rim_path)  # pyright: ignore[reportGeneralTypeIssues]
            # Load _adx.rim if _a.rim not found (REPLACES .rim)
            elif area_extended_rim_path.is_file():
                capsules[KModuleType.AREA_EXTENDED.name] = ModuleLinkPiece(area_extended_rim_path)  # pyright: ignore[reportGeneralTypeIssues]
            else:
                # Simple mode: Just .rim file
                capsules[KModuleType.MAIN.name] = ModuleLinkPiece(module_path.joinpath(root + KModuleType.MAIN.value))  # pyright: ignore[reportGeneralTypeIssues]
            
            # Load _s.rim if exists (ADDS to base)
            data_rim_path = module_path.joinpath(root + KModuleType.DATA.value)
            if data_rim_path.is_file():
                capsules[KModuleType.DATA.name] = ModuleDataPiece(data_rim_path)  # pyright: ignore[reportGeneralTypeIssues]
            
            # Load _dlg.erf if exists (K2 only, ADDS to base)
            if not isinstance(install_or_path, Installation) or install_or_path.game().is_k2():
                dlg_erf_path = module_path.joinpath(root + KModuleType.K2_DLG.value)
                if dlg_erf_path.is_file():
                    capsules[KModuleType.K2_DLG.name] = ModuleDLGPiece(dlg_erf_path)  # pyright: ignore[reportGeneralTypeIssues, reportUnknownReturnType]
        return capsules

    @classmethod
    def get_capsules_tuple_matching(
        cls,
        install_or_path: Installation | Path,
        filename: str,
    ) -> tuple[Capsule, ...]:
        capsules: _CapsuleDictTypes = cls.get_capsules_dict_matching(install_or_path, filename)
        return tuple(capsule for capsule in capsules.values() if isinstance(capsule, Capsule))

    def get_capsules(self) -> list[ModulePieceResource]:
        """Returns all relevant ERFs/RIMs for this module."""
        return list(self._capsules.values())  # pyright: ignore[reportReturnType]  # type: ignore[arg-type]

    def root(self) -> str:
        return self._root.strip()

    def lookup_main_capsule(self) -> ModuleFullOverridePiece | ModuleLinkPiece:
        """Returns main capsule either from the override or the module."""
        relevant_capsule: ModuleFullOverridePiece | ModuleLinkPiece | None
        if self.dot_mod:
            # .mod overrides all
            if KModuleType.MOD.name in self._capsules:
                relevant_capsule = self._capsules[KModuleType.MOD.name]
            else:
                relevant_capsule = self._capsules[KModuleType.MAIN.name]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        else:
            # Complex mode: Check for _a.rim or _adx.rim first (replaces .rim)
            # Simple mode: Just .rim
            if KModuleType.AREA.name in self._capsules and self._capsules[KModuleType.AREA.name] is not None:
                relevant_capsule = self._capsules[KModuleType.AREA.name]
            elif KModuleType.AREA_EXTENDED.name in self._capsules and self._capsules[KModuleType.AREA_EXTENDED.name] is not None:
                relevant_capsule = self._capsules[KModuleType.AREA_EXTENDED.name]
            else:
                relevant_capsule = self._capsules[KModuleType.MAIN.name]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        assert relevant_capsule is not None
        return relevant_capsule

    def lookup_data_capsule(self) -> ModuleFullOverridePiece | ModuleDataPiece:
        """Returns data capsule either from the override or the module."""
        relevant_capsule: ModuleFullOverridePiece | ModuleDataPiece | None
        if self.dot_mod:
            if KModuleType.MOD.name in self._capsules:
                relevant_capsule = self._capsules[KModuleType.MOD.name]
            else:
                relevant_capsule = self._capsules[KModuleType.DATA.name]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        else:
            relevant_capsule = self._capsules[KModuleType.DATA.name]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        assert relevant_capsule is not None
        return relevant_capsule

    def lookup_dlg_capsule(self) -> ModuleFullOverridePiece | ModuleDLGPiece:
        """Returns dlg capsule either from the override or the module."""
        relevant_capsule: ModuleFullOverridePiece | ModuleDLGPiece | None
        if self.dot_mod:
            if KModuleType.MOD.name in self._capsules:
                relevant_capsule = self._capsules[KModuleType.MOD.name]
            else:
                relevant_capsule = self._capsules[KModuleType.K2_DLG.name]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        else:
            relevant_capsule = self._capsules[KModuleType.K2_DLG.name]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        assert relevant_capsule is not None
        return relevant_capsule

    def module_id(self) -> ResRef | None:
        """Returns the module id from the main capsule."""
        if self._cached_mod_id is not None:
            return self._cached_mod_id
        data_capsule: ModuleFullOverridePiece | ModuleLinkPiece = self.lookup_main_capsule()
        found_id: ResRef | None = data_capsule.module_id()
        print(f"Found module id '{found_id}' for module '{data_capsule.filename()}'")
        self._cached_mod_id = found_id
        return found_id

    @staticmethod
    @lru_cache(maxsize=5000)
    def name_to_root(name: str) -> str:
        """Extracts the root module name from a string path or filename.

        This method strips any path components, file extensions, and common module suffixes
        (_s, _dlg) to get the base module name. The result is cached for performance.

        Args:
        ----
            name: A string containing a path or filename to extract the module name from.
                 Can be a full path or just a filename.

        Returns:
        -------
            str: The root module name with suffixes and extensions removed.
                 For example "danm13_s.rim" becomes "danm13".

        Example:
        -------
            >>> Module.name_to_root("c:/games/kotor/modules/danm13_s.rim")
            'danm13'
            >>> Module.name_to_root("danm13_dlg.dlg")
            'danm13'
        """
        split_path: list[str] = name.rsplit("/", 1)
        parsed_name = split_path[-1]
        name_without_ext: str = parsed_name.rsplit(".", 1)[0]
        root: str = name_without_ext.strip()
        casefold_root: str = root.casefold()
        root = root[:-2] if casefold_root.endswith("_s") else root
        root = root[:-4] if casefold_root.endswith("_dlg") else root
        root = root[:-2] if casefold_root.endswith("_a") else root
        root = root[:-4] if casefold_root.endswith("_adx") else root
        return root  # noqa: RET504

    @staticmethod
    def filepath_to_root(filepath: os.PathLike | str) -> str:
        """Converts a filesystem path to a module root name.

        This is a convenience wrapper around name_to_root() that handles PathLike objects.
        It converts the path to a string before extracting the module name.

        Args:
        ----
            filepath: A path-like object pointing to a module file.
                     Can be a `pathlib.Path`, `str`, or other path-like object.

        Returns:
        -------
            str: The root module name with suffixes and extensions removed.
                 For example `pathlib.Path("danm13_s.rim")` becomes `"danm13"`.

        See Also:
        --------
            name_to_root: The underlying implementation that does the actual conversion.
        """
        assert not isinstance(filepath, bytes)
        filepath_str: str = os.fspath(filepath)
        return Module.name_to_root(filepath_str)

    def capsules(self) -> list[ModulePieceResource]:
        """Returns a copy of the capsules used by the module.

        Returns:
        -------
            A tuple of linked capsules.
        """
        return [cast("ModulePieceResource", cap) for cap in self._capsules.values() if cap is not None]

    def reload_resources(self):
        """Reloads and updates the module's resources.

        Responsible for loading and updating the resources associated with the module.
        It processes the resources from various locations such as the module's own files, override directories,
        and core resources. The method also handles the identification and activation of resources linked
        through GIT, LYT, and VIS files.

        Processing Logic:
        ----------------
        1. Determine the display name of the module based on its type (.mod or.rim).
        2. Log the start of the resource loading process.
        3. Identify the main capsule to search for resources.
        4. Define the search order for resources (OVERRIDE, CUSTOM_MODULES, CHITIN).
        5. Create queries for GIT, LYT, and VIS resources using the module ID.
        6. Iterate through the module's capsules to add initial resource locations from the module files.
        7. Find references to resources in GIT, LYT, and VIS files:
            a. Process each query (GIT, LYT, VIS) to add locations and collect resource identifiers
            b. Track all resources referenced by GIT, LYT, VIS
            c. Add locations for all found resources
        8. Process core resources and override directories to add and activate resource locations:
            a. Check chitin/core resources first
            b. Prioritize override resources by checking/activating last
        9. Identify and activate texture resources linked in models:
            a. Iterate through all models in the module
            b. Find textures and lightmaps referenced in each model
            c. Create search queries for TPC and TGA textures
            d. Add locations for found texture resources
        10. Iterate through all resources to ensure all are activated, skipping duplicates:
            a. Skip TPC resources if the TGA equivalent is already found and activated
            b. Skip TGA resources if the TPC equivalent is already found and activated

        Raises:
        ------
            FileNotFoundError: If a required resource is not found in the expected locations.
            RuntimeError: If a resource type is unexpectedly None.
        """
        display_name = f"{self._root}.mod" if self.dot_mod else f"{self._root}.rim"
        RobustLogger().info("Loading module resources needed for '%s'", display_name)
        capsules_to_search: list[ModuleFullOverridePiece | ModuleLinkPiece] = [self.lookup_main_capsule()]
        # Lookup the GIT and LYT first.
        order: tuple[SearchLocation, ...] = (
            SearchLocation.OVERRIDE,
            SearchLocation.CUSTOM_MODULES,
            SearchLocation.CHITIN,
        )
        link_resname: str = str(self.module_id())
        lyt_query: ResourceIdentifier = ResourceIdentifier(link_resname, ResourceType.LYT)
        git_query: ResourceIdentifier = ResourceIdentifier(link_resname, ResourceType.GIT)
        vis_query: ResourceIdentifier = ResourceIdentifier(link_resname, ResourceType.VIS)

        # Start in our module resources, needs to happen first so we can determine what resources are part of our module.
        for capsule in self._capsules.values():
            if capsule is None:
                continue
            # No idea why static types aren't working here as that's the whole point of the TypedDict...
            typed_capsule: ModulePieceResource = cast("ModulePieceResource", capsule)
            for resource in typed_capsule:
                #RobustLogger().debug("Adding location '%s' for resource '%s' from erf/rim '%s'", typed_capsule.filepath(), resource.identifier(), typed_capsule.identifier())
                self.add_locations(resource.resname(), resource.restype(), [typed_capsule.filepath()])

        # Any resource referenced by the GIT/LYT/VIS not present in the module files
        # To be looked up elsewhere in the installation.
        main_search_results: dict[ResourceIdentifier, list[LocationResult]] = self._installation.locations(
            [lyt_query, git_query, vis_query],
            list(order),
            capsules=capsules_to_search,
        )

        # Track all resources referenced by GIT/LYT/VIS
        git_search: set[ResourceIdentifier] = set()
        lyt_search: set[ResourceIdentifier] = set()
        vis_search: set[ResourceIdentifier] = set()

        # Process each query (GIT, LYT, VIS) in sequence
        loop_iter_data: list[tuple[ResourceIdentifier, type[GIT | LYT | VIS], set[ResourceIdentifier]]] = [
            (git_query, GIT, git_search),
            (lyt_query, LYT, lyt_search),
            (vis_query, VIS, vis_search),
        ]
        for query, useable_type, search_set in loop_iter_data:
            if not main_search_results.get(query):
                if useable_type is VIS:
                    continue  # VIS is optional
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.lookup_main_capsule().filepath() / str(query))

            # Add locations and get the resource wrapper
            resource_wrapper = self.add_locations(
                query.resname,
                query.restype,
                (loc.filepath for loc in main_search_results[query]),
            )
            # Activate each GIT/LYT location for this module, and fill this module with all of their resources (all of the resources their instances point to).
            # Store original path to restore later
            original_path: Path = resource_wrapper.locations()[0]

            # Check each location for referenced resources
            for location in resource_wrapper.locations():
                resource_wrapper.activate(location)
                loaded_resource: type[GIT | LYT | VIS] | None = resource_wrapper.resource()

                # VIS is optional and some installations ship malformed VIS. If parsing fails, treat as absent.
                if useable_type is VIS and loaded_resource is None:
                    continue
                if not isinstance(loaded_resource, (GIT, LYT, VIS)):
                    raise RuntimeError(f"{useable_type.__name__} is somehow None even though we know the path there.")  # noqa: TRY004

                # Only GIT/LYT have resource identifiers to collect
                if not isinstance(loaded_resource, VIS):
                    search_set.update(loaded_resource.iter_resource_identifiers())

            resource_wrapper.activate(original_path)

        # From GIT/LYT references, find them in the installation.
        search_results: dict[ResourceIdentifier, list[LocationResult]] = self._installation.locations(
            list({*git_search, *lyt_search, *vis_search}),
            list(order),
            capsules=capsules_to_search,
        )
        # Add locations for all found resources
        for identifier, locations in search_results.items():
            search_result_filepaths: tuple[Path, ...] = tuple(location.filepath for location in locations)
            self.add_locations(
                identifier.resname,
                identifier.restype,
                search_result_filepaths,
            )

        # Third. Since we now have a known full list of resources that make up this module, we can now process Override and chitin in one fell swoop.
        # Realistically we'll do this at the end, but right now we're interested in enumerating the models so we can find textures.
        # Check chitin first.
        for resource in self._installation.core_resources():
            if resource.identifier() in self.resources or resource.identifier() in git_search:
                RobustLogger().info("Found chitin/core location '%s' for resource '%s' for module '%s'", resource.filepath(), resource.identifier(), display_name)
                git_search_result_filepaths: tuple[Path, ...] = (resource.filepath(),)
                self.add_locations(resource.resname(), resource.restype(), git_search_result_filepaths).activate()

        # Prioritize Override by checking/activating last.
        for directory in self._installation.override_list():
            for resource in self._installation.override_resources(directory):
                if (
                    resource.identifier() not in self.resources  # irrelevant resources in override are skipped
                    and resource.identifier() not in git_search
                ):
                    continue
                RobustLogger().info("Found override location '%s' for module '%s'", resource.filepath(), display_name)
                self.add_locations(resource.resname(), resource.restype(), [resource.filepath()]).activate()

        # Also try get paths for textures in models
        if not self._load_textures:
            # Fast mode: skip model texture/lightmap crawling. This is the largest bottleneck in practice
            # and is unnecessary for workflows that only need module-local resources (e.g. IndoorMap/ModuleKit extraction).
            return

        lookup_texture_queries: set[str] = set()
        lookup_lightmap_queries: set[str] = set()
        for model in self.models():
            print(f"Finding textures/lightmaps for model '{model.identifier()}'...")
            try:
                model_data: bytes | None = model.data()
            except OSError:
                RobustLogger().warning(
                    "Suppressed known exception while executing %s.reload_resources() while getting model data '%s': %s",
                    repr(self),
                    model.identifier(),
                    exc_info=True,
                    extra={"detailed": False},
                )
                continue
            else:
                if model_data is None:
                    RobustLogger().warning(f"Missing model '{model.identifier()}', needed by module '{display_name}'")
                    continue
                if not model_data:
                    RobustLogger().warning(f"model '{model.identifier()}' was unexpectedly empty, but is needed by module '{display_name}'")
                    continue
            model_textures: set[str] = set()
            model_lightmaps: set[str] = set()
            with suppress(Exception):
                model_textures.update(iterate_textures(model_data))
                lookup_texture_queries.update(model_textures)
            with suppress(Exception):
                model_lightmaps.update(iterate_lightmaps(model_data))
                lookup_lightmap_queries.update(model_lightmaps)
            if model_textures:
                print(f"    Textures: {', '.join(sorted(model_textures))}")
            if model_lightmaps:
                print(f"    Lightmaps: {', '.join(sorted(model_lightmaps))}")

        texlm_queries: set[str] = lookup_texture_queries | lookup_lightmap_queries
        texture_queries: list[ResourceIdentifier] = [
            ResourceIdentifier(texture, res_type)  # create the search queries for TPC/TGA textures
            for texture in texlm_queries
            for res_type in (ResourceType.TPC, ResourceType.TGA)
        ]
        texture_search: dict[ResourceIdentifier, list[LocationResult]] = self._installation.locations(
            texture_queries,
            [
                SearchLocation.OVERRIDE,
                SearchLocation.CHITIN,
                SearchLocation.TEXTURES_TPA,  # tpa is the highest quality texture location (rather than tpb/tpc)
            ],
        )
        for identifier, locations in texture_search.items():
            if not locations:
                continue
            #location_paths = [str(loc.filepath) for loc in locations]
            #if len(location_paths) <= 3:
            #    paths_str = ', '.join(location_paths)
            #else:
            #    paths_str = ', '.join(location_paths[:3]) + f', ... and {len(location_paths) - 3} more'
            #RobustLogger().debug(f"Adding {len(locations)} texture location(s) for '{identifier.resname}.{identifier.restype.extension}' to '{display_name}': {paths_str}")
            self.add_locations(identifier.resname, identifier.restype, (location.filepath for location in locations)).activate()

        # Finally iterate through all resources we may have missed.
        for ident, module_resource in self.resources.items():
            if module_resource.isActive():
                continue
            if ident.restype is ResourceType.TPC and ResourceIdentifier(ident.resname, ResourceType.TGA) in self.resources:
                continue  # Skip TPC resources if the TGA equivalent resource is already found and activated.
            if ident.restype is ResourceType.TGA and ResourceIdentifier(ident.resname, ResourceType.TPC) in self.resources:
                continue  # Skip TGA resources if the TPC equivalent resource is already found and activated.
            module_resource.activate()

    def _handle_git_lyt_reloads(
        self,
        main_search_results: dict[ResourceIdentifier, list[LocationResult]],
        query: ResourceIdentifier,
        useable_type: type[GIT | LYT | VIS],
        errmsg: str,
    ) -> set[ResourceIdentifier]:
        if not main_search_results.get(query):
            if useable_type == VIS:
                return set()  # make vis optional I guess
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    self.lookup_main_capsule().filepath() / str(query))
        original_git_or_lyt = self.add_locations(
            query.resname, query.restype,
            (loc.filepath for loc in main_search_results[query]),
        )
        # Activate each GIT/LYT location for this module, and fill this module with all of their resources (all of the resources their instances point to).
        original_path: Path = original_git_or_lyt.locations()[0]
        result: set[ResourceIdentifier] = set()
        for location in original_git_or_lyt.locations():
            original_git_or_lyt.activate(location)
            try:
                loaded_git_or_lyt: type[GIT | LYT | VIS] | None = original_git_or_lyt.resource()
                if loaded_git_or_lyt is None:
                    RobustLogger().warning("Failed to load resource '%s' from location '%s'", original_git_or_lyt.identifier(), location)
                    if useable_type != VIS:
                        raise RuntimeError(errmsg)  # noqa: TRY004, TRY301
                    continue  # VIS is optional, so we can skip if it fails to load
                if isinstance(loaded_git_or_lyt, VIS):
                    RobustLogger().debug("Loaded VIS resource '%s' from location '%s'", original_git_or_lyt.identifier(), location)
                    # VIS files don't have resource identifiers to iterate, so just skip
                    continue
                if isinstance(loaded_git_or_lyt, (GIT, LYT)):
                    result.update(loaded_git_or_lyt.iter_resource_identifiers())
                else:
                    RobustLogger().error(
                        "Unexpected resource type '%s' for '%s' (expected GIT, LYT, or VIS)",
                        type(loaded_git_or_lyt).__name__,
                        original_git_or_lyt.identifier(),
                    )
                    if useable_type != VIS:
                        raise RuntimeError(errmsg)  # noqa: TRY004, TRY301
            except RuntimeError:
                raise
            except Exception:  # noqa: BLE001
                RobustLogger().error("Unexpected exception when executing %s._handle_git_lyt_reloads() with resource '%s'",
                                           repr(self), original_git_or_lyt.identifier())
        original_git_or_lyt.activate(original_path)  # reactivate the main one.

        return result

    def add_locations(
        self,
        resname: str,
        restype: ResourceType,
        locations: Iterable[Path],
    ) -> ModuleResource:
        """Creates or extends a ModuleResource keyed by the resname/restype with additional locations.

        This is how Module.resources dict gets filled.

        Args:
        ----
            resname: The resource name.
            restype: The resource type.
            locations: The locations of the resource files.

        Processing Logic:
        ----------------
            - Checks if the resource already exists in the dictionary
            - If it doesn't exist, creates a new ModuleResource object
            - Adds the locations to the existing or newly created ModuleResource
            - Does not return anything, modifies the dictionary in-place.
        """
        if not isinstance(locations, Collection):
            locations = list(locations)
        if (
            not locations  # vvv skip dirt.tpc, some constant from the model-ascii data vvv
            and (resname != "dirt" or restype != ResourceType.TPC)
        ):
            RobustLogger().warning("No locations found for '%s.%s' which are intended to add to module '%s'", resname, restype, self._root)
        module_resource: ModuleResource | None = self.resource(resname, restype)
        if module_resource is None:
            module_resource = ModuleResource(resname, restype, self._installation, self._root)
            self.resources[module_resource.identifier()] = module_resource
        module_resource.add_locations(locations)
        return module_resource

    def installation(self) -> Installation:
        return self._installation

    def resource(
        self,
        resname: str,
        restype: ResourceType,
    ) -> ModuleResource | None:
        """Returns the resource with the given name and type from the module.

        Args:
        ----
            resname (str): The name of the resource.
            restype (ResourceType): The type of the resource.

        Returns:
        -------
            ModuleResource | None: The resource with the given name and type, or None if it does not exist.
        """
        ident = ResourceIdentifier(resname, restype)
        return self.resources.get(ident, None)

    def layout(self) -> ModuleResource[LYT] | None:
        """Returns the LYT layout resource with a matching ID if it exists.

        Args:
        ----
            self: The Module instance

        Returns:
        -------
            ModuleResource[LYT] | None: The layout resource or None if not found

        Processing Logic:
        ----------------
            - Iterates through all resources in self.resources
            - Checks if resource name matches self._id and type is LYT
            - Returns first matching resource or None if not found.
        """
        return next(
            (resource for resource in self.resources.values() if (resource.restype() is ResourceType.LYT and resource.resname() == self.module_id())),
            None,
        )

    def vis(self) -> ModuleResource[VIS] | None:
        """Finds the VIS resource with matching ID.

        Args:
        ----
            self: The Module object.

        Returns:
        -------
            ModuleResource[VIS] | None: The VIS resource object or None.

        Finds the VIS resource object from the Module's resources:
            - Iterates through the resources dictionary values
            - Checks if the resource name matches self._id in lowercase and type is VIS
            - Returns the first matching resource or None.
        """
        return next((resource for resource in self.resources.values() if (resource.restype() is ResourceType.VIS and resource.resname() == self.module_id())), None)

    def are(self) -> ModuleResource[ARE] | None:
        """Returns the ARE resource with the given ID if it exists.

        Args:
        ----
            self: The Module object

        Returns:
        -------
            ModuleResource[ARE] | None: The ARE resource or None if not found

        Processing Logic:
        ----------------
            - Iterate through all resources in self.resources
            - Check if resource name matches self._id in lowercase and resource type is ARE
            - Return first matching resource or None if no match.
        """
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.ARE and resource.resname() == self.module_id()),
            None,
        )

    def git(self) -> ModuleResource[GIT] | None:
        """Returns the git resource with matching id if found.

        Args:
        ----
            self: The module object

        Returns:
        -------
            ModuleResource[GIT] | None: The git resource or None

        Processing Logic:
        ----------------
            - Iterate through all resources in module
            - Check if resource name matches id in lowercase and type is GIT
            - Return matching resource or None if not found.
        """
        result = next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.GIT and resource.resname() == self.module_id()),
            None,
        )
        if result is None:  # noqa: RET503
            fallback = next(
                (resource for resource in self.resources.values() if resource.restype() is ResourceType.GIT),
                None,
            )
            if fallback is not None:  # noqa: RET503
                RobustLogger().warning("This module '%s' has an incorrect GIT resname/resref! Expected '%s', found '%s'", self._root, self.module_id(), fallback.resname())  # noqa: RET503
        return result  # noqa: RET504

    def pth(self) -> ModuleResource[PTH] | None:
        """Finds the PTH resource with matching ID.

        Args:
        ----
            self: The Module object.

        Returns:
        -------
            ModuleResource[PTH] | None: The PTH resource or None if not found.

        Finds the PTH resource:
            - Iterates through all resources
            - Checks if resource name matches self._id and type is PTH
            - Returns first matching resource or None.
        """
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.PTH and resource.resname() == self.module_id()),
            None,
        )

    def ifo(self) -> ModuleResource[IFO] | None:
        return self.info()

    def info(self) -> ModuleResource[IFO] | None:
        """Returns the ModuleResource with type IFO if it exists.

        Args:
        ----
            self: The object instance

        Returns:
        -------
            ModuleResource[IFO] | None: The ModuleResource with type IFO or None

        Processing Logic:
        ----------------
            - Iterate through self.resources values
            - Check if resource name is 'module' and type is IFO
            - Return first matching resource
            - Return None if no match found.
        """
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.IFO and resource.identifier().lower_resname == "module"),
            None,
        )

    def creature(
        self,
        resname: str,
    ) -> ModuleResource[UTC] | None:
        """Returns a UTC resource by name if it exists.

        Args:
        ----
            resname: Name of the resource to search for

        Returns:
        -------
            ModuleResource[UTC]: The UTC resource or None if not found

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary values
            - Check if resname matches resource name and type is UTC
            - Return matching resource or None if not found.
        """
        lower_resname: str = resname.lower()
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.UTC and lower_resname == resource.identifier().lower_resname),
            None,
        )

    def creatures(self) -> list[ModuleResource[UTC]]:
        """Returns a list of UTC resources.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTC]]: A list of UTC resources

        Processing Logic:
        ----------------
            - Iterate through all resources in self.resources
            - Check if each resource's type is UTC
            - Add matching resources to the return list.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTC]

    def placeable(
        self,
        resname: str,
    ) -> ModuleResource[UTP] | None:
        """Check if a placeable UTP resource with the given resname exists.

        Args:
        ----
            resname (str): Name of the resource to check

        Returns:
        -------
            resource: Found resource or None

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary
            - Check if resource name matches given name and type is UTP
            - Return matching resource if found, else return None.
        """
        lower_resname: str = resname.lower()
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.UTP and lower_resname == resource.identifier().lower_resname),
            None,
        )

    def placeables(self) -> list[ModuleResource[UTP]]:
        """Returns a list of UTP resources for this module.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTP]]: List of UTP resources

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary
            - Check if resource type is UTP
            - Add matching resources to the return list.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTP]

    def door(
        self,
        resname: str,
    ) -> ModuleResource[UTD] | None:
        """Returns a UTD resource matching the provided resname from this module.

        Args:
        ----
            resname (str): The name of the resource

        Returns:
        -------
            ModuleResource[UTD] | None: The UTD resource or None if not found

        Processing Logic:
        ----------------
            - Iterate through self.resources values
            - Check if resname matches resource name and type is UTD
            - Return matching resource or None if not found.
        """
        lower_resname: str = resname.lower()
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.UTD and lower_resname == resource.identifier().lower_resname),
            None,
        )

    def doors(self) -> list[ModuleResource[UTD]]:
        """Returns a list of all UTD resources for this module.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTD]]: List of UTD resources

        Processing Logic:
        ----------------
            - Iterate through all resources stored in self.resources
            - Check if each resource's type is UTD
            - Add matching resources to the return list.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTD]

    def item(
        self,
        resname: str,
    ) -> ModuleResource[UTI] | None:
        """Returns a UTI resource matching the provided resname from this module if it exists.

        Args:
        ----
            resname (str): Name of the resource to lookup

        Returns:
        -------
            ModuleResource[UTI] | None: The matching UTI resource or None

        Processing Logic:
        ----------------
            - Iterates through self.resources dictionary values
            - Returns the first resource where resname matches resource.resname() and resource type is UTI
            - Returns None if no matching resource found.
        """
        lower_resname: str = resname.lower()
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.UTI and lower_resname == resource.identifier().lower_resname),
            None,
        )

    def items(self) -> list[ModuleResource[UTI]]:
        """Returns a list of UTI resources for this module.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTI]]: A list of UTI resources

        Processing Logic:
        ----------------
            - Iterate through self.resources which is a dictionary of all resources
            - Check if each resource's restype is equal to ResourceType.UTD
            - If equal, add it to the return list
            - Return the list of UTI resources.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTD]

    def encounter(
        self,
        resname: str,
    ) -> ModuleResource[UTE] | None:
        """Find UTE resource by the specified resname.

        Args:
        ----
            resname: Resource name to search for

        Returns:
        -------
            resource: Found UTE resource or None

        Processing Logic:
        ----------------
            - Iterate through self.resources values
            - Check if resname matches resource name and type is UTE
            - Return first matching resource or None.
        """
        lower_resname: str = resname.lower()
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.UTE and lower_resname == resource.identifier().lower_resname),
            None,
        )

    def encounters(self) -> list[ModuleResource[UTE]]:
        """Returns a list of UTE resources for this module.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTE]]: A list of UTE resources

        Processing Logic:
        ----------------
            - Iterate through all resources stored in self.resources
            - Check if each resource's type is UTE
            - If type matches, add it to the return list
            - Return the list of UTE resources.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTE]

    def store(self, resname: str) -> ModuleResource[UTM] | None:
        """Looks up a material (UTM) resource by the specified resname from this module and returns the resource data.

        Args:
        ----
            resname(str): Name of the resource to look up

        Returns:
        -------
            resource: The looked up resource or None if not found

        Processing Logic:
        ----------------
            - Loops through all resources stored in self.resources
            - Checks if the resource name matches the given name and type is UTM
            - Returns the first matching resource
            - Returns None if no match found.
        """
        lower_resname: str = resname.lower()
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.UTM and lower_resname == resource.identifier().lower_resname),
            None,
        )

    def stores(self) -> list[ModuleResource[UTM]]:
        """Returns a list of material (UTM) resources for this module."""
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTM]

    def trigger(
        self,
        resname: str,
    ) -> ModuleResource[UTT] | None:
        """Returns a trigger (UTT) resource by the specified resname if it exists.

        Args:
        ----
            resname: Name of the resource to retrieve

        Returns:
        -------
            resource: The requested UTT resource or None

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary values
            - Check if resname matches resource name and type is UTT
            - Return first matching resource
            - Return None if no match found.
        """
        lower_resname: str = resname.lower()
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.UTT and lower_resname == resource.identifier().lower_resname),
            None,
        )

    def triggers(self) -> list[ModuleResource[UTT]]:
        """Returns a list of UTT resources for this module.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTT]]: A list of UTT resources

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary
            - Check if each resource's restype is UTT
            - Add matching resources to a list
            - Return the list of UTT resources.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTT]

    def waypoint(
        self,
        resname: str,
    ) -> ModuleResource[UTW] | None:
        """Returns the UTW resource with the given name if it exists.

        Args:
        ----
            resname: The name of the UTW resource

        Returns:
        -------
            resource: The UTW resource or None if not found

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary values
            - Check if resname matches resource name and type is UTW
            - Return first matching resource
            - Return None if no match found.
        """
        lower_resname: str = resname.lower()
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.UTW and lower_resname == resource.identifier().lower_resname),
            None,
        )

    def waypoints(self) -> list[ModuleResource[UTW]]:
        """Returns list of UTW resources from resources dict.

        Returns:
        -------
            list[ModuleResource[UTW]]: List of UTW resources

        Processing Logic:
        ----------------
            - Iterate through self.resources dict values
            - Check if resource type is UTW
            - Add matching resources to return list
            - Return list of UTW resources.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTW]

    def model(
        self,
        resname: str,
    ) -> ModuleResource[MDL] | None:
        """Returns a ModuleResource object for the given resource name if it exists in this module.

        Args:
        ----
            resname: The name of the resource to lookup.

        Returns:
        -------
            resource: The ModuleResource object if found, None otherwise.

        Processing Logic:
        ----------------
            - Loops through all resources stored in self.resources
            - Checks if the resource name matches the given name and the resource type is MDL
            - Returns the matching resource if found, None otherwise.
        """
        lower_resname: str = resname.lower()
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.MDL and lower_resname == resource.identifier().lower_resname),
            None,
        )

    def model_ext(
        self,
        resname: str,
    ) -> ModuleResource | None:
        """Finds a MDX module resource by name from this module.

        Args:
        ----
            resname: The name of the resource to find.

        Returns:
        -------
            ModuleResource|None: The matching resource or None if not found.

        Processes the resources dictionary:
            - Iterates through resources.values()
            - Checks if resname matches resource.resname() and resource type is MDX
            - Returns first matching resource or None.
        """
        lower_resname: str = resname.lower()
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.MDX and lower_resname == resource.identifier().lower_resname),
            None,
        )

    def models(self) -> list[ModuleResource[MDL]]:
        """Returns a list of MDL model resources.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[MDL]]: A list of MDL model resources

        Processes the resources dictionary:
            - Loops through each value in the resources dictionary
            - Checks if the resource type is MDL
            - Adds matching resources to the return list.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.MDL]

    def model_exts(self) -> list[ModuleResource]:
        """Returns a list of MDX model resources.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource]: A list of MDX model resources

        Processes the resources dictionary:
            - Loops through each value in the resources dictionary
            - Checks if the resource type is MDX
            - Adds matching resources to the return list.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.MDX]

    def texture(
        self,
        resname: str,
    ) -> ModuleResource[TPC] | None:
        """Looks up a texture resource by resname from this module.

        Args:
        ----
            resname: Name of the texture resource to look up.

        Returns:
        -------
            resource: Found texture resource or None.

        Processing Logic:
        ----------------
            - Loops through all resources stored in self.resources
            - Checks if resname matches the resource name in any case-insensitive way
            - Checks if the resource type is a texture format like TPC or TGA
            - Returns the first matching resource or None if not found.
        """
        lower_resname: str = resname.lower()
        texture_types: set[ResourceType] = {ResourceType.TPC, ResourceType.TGA}
        return next(
            (resource for resource in self.resources.values() if resource.isActive() and resource.restype() in texture_types and lower_resname == resource.identifier().lower_resname),
            None,
        )

    def textures(self) -> list[ModuleResource[MDL]]:
        """Generates a list of texture resources from this module.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[MDL]]: List of texture resources

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary
            - Check if resource type is TPC or TGA texture format
            - Include the resource in return list if type matches.
        """
        texture_types: set[ResourceType] = {ResourceType.TPC, ResourceType.TGA}
        return [resource for resource in self.resources.values() if resource.isActive() is not None and resource.restype() in texture_types]

    def sound(
        self,
        resname: str,
    ) -> ModuleResource[UTS] | None:
        """Returns the UTS resource with the given name if it exists.

        Args:
        ----
            resname: The name of the UTS resource

        Returns:
        -------
            resource: The UTS resource or None if not found

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary values
            - Check if resname matches resource name and type is UTS
            - Return matching resource or None if not found.
        """
        lower_resname: str = resname.lower()
        return next(
            (resource for resource in self.resources.values() if resource.restype() is ResourceType.UTS and lower_resname == resource.identifier().lower_resname),
            None,
        )

    def sounds(self) -> list[ModuleResource[UTS]]:
        """Returns a list of UTS resources.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTS]]: A list of UTS resources

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary
            - Check if each resource's type is UTS
            - Add matching resources to a list
            - Return the list of UTS resources.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTS]

    def loadscreen(self) -> FileResource | None:
        """Returns a FileResource object representing the loadscreen texture for this module.

        The loadscreen is determined by:
        1. Getting the LoadScreenID from the module's ARE file
        2. Looking up the bmpresref in loadscreens.2da using the LoadScreenID
        3. Finding the texture resource (TGA or TPC) with that ResRef

        References:
        ----------
            wiki/2DA-loadscreens.md - loadscreens.2da structure and bmpresref column

        Returns:
        -------
            FileResource | None: The loadscreen texture FileResource, or None if not found.

        Processing Logic:
        ----------------
            1. Get the ARE resource from the module
            2. Read the ARE to get LoadScreenID
            3. Load loadscreens.2da from the installation
            4. Get the bmpresref from loadscreens.2da using LoadScreenID as row index
            5. Search for the texture (TGA or TPC) using installation.locations()
            6. Return the FileResource from the first location found, or None if not found.
        """
        from pykotor.resource.formats.twoda.twoda_auto import read_2da

        # Get the ARE resource
        are_resource = self.are()
        if are_resource is None:
            RobustLogger().warning(f"Module '{self._root}' has no ARE resource, cannot determine loadscreen")
            return None

        # Read the ARE to get LoadScreenID
        are_data = are_resource.resource()
        if are_data is None:
            RobustLogger().warning(f"Failed to read ARE resource for module '{self._root}'")
            return None

        loadscreen_id = are_data.loadscreen_id
        if loadscreen_id == 0:
            RobustLogger().debug(f"Module '{self._root}' has LoadScreenID=0, no loadscreen specified")
            return None

        # Load loadscreens.2da from installation
        loadscreens_result = self._installation.resource(
            "loadscreens",
            ResourceType.TwoDA,
            [SearchLocation.OVERRIDE, SearchLocation.CHITIN],
        )
        if loadscreens_result is None:
            RobustLogger().warning("loadscreens.2da not found in installation")
            return None

        loadscreens_2da = read_2da(loadscreens_result.data)

        # Get the bmpresref from loadscreens.2da using LoadScreenID as row index
        try:
            loadscreen_row = loadscreens_2da.get_row(loadscreen_id)
            bmpresref = loadscreen_row.get_string("bmpresref")
            if not bmpresref or bmpresref == "****":
                RobustLogger().debug(f"Module '{self._root}' loadscreen row {loadscreen_id} has no bmpresref")
                return None
        except (IndexError, KeyError) as e:
            RobustLogger().warning(f"Failed to get bmpresref from loadscreens.2da row {loadscreen_id}: {e}")
            return None

        # Search for the texture (TGA or TPC) using installation.locations()
        texture_queries = [
            ResourceIdentifier(bmpresref, ResourceType.TPC),
            ResourceIdentifier(bmpresref, ResourceType.TGA),
        ]
        texture_locations = self._installation.locations(
            texture_queries,
            [SearchLocation.OVERRIDE, SearchLocation.CUSTOM_MODULES, SearchLocation.CHITIN, SearchLocation.TEXTURES_TPA],
        )

        # Return the FileResource from the first location found
        for query in texture_queries:
            if query in texture_locations and texture_locations[query]:
                location: LocationResult = texture_locations[query][0]
                try:
                    return location.as_file_resource()
                except RuntimeError:
                    # If FileResource wasn't set, create one from the location
                    return FileResource(
                        resname=bmpresref,
                        restype=query.restype,
                        size=location.size,
                        offset=location.offset,
                        filepath=location.filepath,
                    )

        RobustLogger().debug(f"Loadscreen texture '{bmpresref}' not found for module '{self._root}'")
        return None


class ModuleResource(Generic[T]):
    """Represents a single resource within a module with multiple possible locations.
    
    ModuleResource manages a resource that may exist in multiple locations (override,
    module archives, chitin). It tracks all locations and allows activation of a
    specific location, with lazy loading of the actual resource object.
    
    References:
    ----------
        Original BioWare Odyssey Engine (resource search order: Override > Module > Chitin)
    
    Attributes:
    ----------
        _resname: Resource name (ResRef) without extension.
            The name of the resource (e.g., "module", "danm13").
        
        _restype: Resource type identifier.
            The type of resource (e.g., ResourceType.IFO, ResourceType.ARE).
        
        _installation: Installation instance for resource lookups.
            Used to resolve resources from chitin and other locations.
        
        _active: Currently active file path for this resource.
            The file path currently being used to load this resource.
            None if no location has been activated yet.
        
        _resource_obj: Cached loaded resource object.
            The parsed resource object (e.g., IFO, ARE, UTC).
            None until resource() is called for the first time.
        
        _locations: List of all file paths where this resource exists.
            All known locations for this resource, ordered by priority.
            Search order: Override > Custom Modules > Chitin
        
        _identifier: ResourceIdentifier for this resource.
            Reference: PyKotor-specific abstraction
            Combines resname and restype for unique identification.
    """
    def __init__(
        self,
        resname: str,
        restype: ResourceType,
        installation: Installation,
        module_root: str | None = None,
    ):
        self._resname: str = resname
        self._installation: Installation = installation
        self._restype: ResourceType = restype
        self._active: Path | None = None
        self._resource_obj: Any = None
        self._locations: list[Path] = []
        self._identifier = ResourceIdentifier(resname, restype)
        self._module_root: str | None = module_root

    def __repr__(self):
        return f"{self.__class__.__name__}(resname={self._resname} restype={self._restype!r} installation={self._installation!r})"

    def __eq__(self, other):
        if self is other:
            return True
        if isinstance(other, ResourceIdentifier):
            return self._identifier == other
        if isinstance(other, ModuleResource):
            return self._identifier == other._identifier
        return NotImplemented

    def __hash__(self):
        return hash(self._identifier)

    def resname(self) -> str:
        """Returns the resource name.

        Returns:
        -------
            The resource name.
        """
        return self._resname

    def restype(self) -> ResourceType:
        """Returns the type of resource stored.

        Returns:
        -------
            The resource type.
        """
        return self._restype

    def filename(self) -> str:
        return str(self._identifier)

    def identifier(self) -> ResourceIdentifier:
        return self._identifier

    def localized_name(self) -> str | None:
        # sourcery skip: assign-if-exp, reintroduce-else
        """Returns a localized name for the resource.

        Args:
        ----
            self: The object instance

        Returns:
        -------
            str | None: Localized name or None if not found

        Processing Logic:
        ----------------
            - Get the resource from self.resource()
            - Check if resource is None and return None
            - Check type of resource and return localized name by calling installation string method
            - Return None if type is not matched.
        """
        res: T | None = self.resource()
        if res is None:
            return None
        if isinstance(res, UTC):
            return f"{self._installation.string(res.first_name)} {self._installation.string(res.last_name)}"
        if isinstance(res, (UTD, UTE, UTM, UTP, UTS, UTT, UTW)):
            return self._installation.string(res.name)
        print(f"Could not find a localized name for a ModuleResource typed {type(res).__name__}")
        return None

    def data(self) -> bytes | None:
        """Opens the file at the active location and returns the data.

        Raises:
        ------
            ValueError: If no file is active.

        Returns:
        -------
            The bytes data of the active file.
        """
        file_name = f"{self._resname}.{self._restype.extension}"
        active_path = self.active()
        if active_path is None:
            return None

        if is_capsule_file(active_path):
            data: bytes | None = Capsule(active_path).resource(self._resname, self._restype)
            if data is None:
                RobustLogger().error(f"Resource '{file_name}' not found in '{active_path}'")
            return data

        if is_bif_file(active_path):
            resource: ResourceResult | None = self._installation.resource(
                self._resname,
                self._restype,
                [SearchLocation.CHITIN],
            )
            if resource is None:
                msg = f"Resource '{file_name}' not found in BIF '{self._active}' somehow?"
                RobustLogger().error(msg)
                return None
            return resource.data

        return active_path.read_bytes()

    def resource(self) -> T | None:
        """Returns the cached resource object. If no object has been cached, then it will load the object.

        Returns:
        -------
            The resource object.

        Returns:
            The abstracted resource, or None if not found.
        """
        if self._resource_obj is None:
            conversions: dict[ResourceType, Callable[[SOURCE_TYPES], Any]] = {
                ResourceType.ARE: read_are,
                ResourceType.DLG: read_dlg,
                ResourceType.GIT: read_git,
                ResourceType.IFO: read_ifo,
                ResourceType.LYT: read_lyt,
                ResourceType.NCS: lambda data: data,
                ResourceType.PTH: read_pth,
                ResourceType.TPC: read_tpc,
                ResourceType.TGA: read_tpc,
                ResourceType.UTD: read_utd,
                ResourceType.UTE: read_ute,
                ResourceType.UTI: read_uti,
                ResourceType.UTM: read_utm,
                ResourceType.UTP: read_utp,
                ResourceType.UTS: read_uts,
                ResourceType.UTT: read_utt,
                ResourceType.UTW: read_utw,
                ResourceType.UTC: read_utc,
                ResourceType.VIS: read_vis,
                ResourceType.WOK: read_bwm,
            }
            active_path = self.active()
            if active_path is None:
                return None

            if is_capsule_file(active_path):
                data: bytes | None = Capsule(active_path).resource(self._resname, self._restype)
                if data is None:
                    msg = f"Resource '{self._identifier}' not found in '{active_path}'"
                    RobustLogger().error(msg)
                    return None
                try:
                    self._resource_obj = conversions.get(self._restype, lambda _: None)(data)
                except Exception as e:  # noqa: BLE001
                    # Some shipped installations contain malformed VIS. Treat it as missing so
                    # module workflows that do not require VIS (e.g. walkmesh extraction/build)
                    # can still function.
                    if self._restype == ResourceType.VIS:
                        RobustLogger().warning(
                            "Failed to parse VIS '%s.%s' from '%s': %s",
                            self._resname,
                            self._restype.extension,
                            active_path,
                            e,
                        )
                        self._resource_obj = None
                    else:
                        raise

            elif is_bif_file(active_path):
                resource: ResourceResult | None = self._installation.resource(
                    self._resname,
                    self._restype,
                    [SearchLocation.CHITIN],
                )
                if resource is None:
                    msg = f"Resource '{self._identifier}' not found in '{active_path}'"
                    RobustLogger().error(msg)
                    return None
                try:
                    self._resource_obj = conversions.get(self._restype, lambda _: None)(resource.data)
                except Exception as e:  # noqa: BLE001
                    if self._restype == ResourceType.VIS:
                        RobustLogger().warning(
                            "Failed to parse VIS '%s.%s' from '%s': %s",
                            self._resname,
                            self._restype.extension,
                            active_path,
                            e,
                        )
                        self._resource_obj = None
                    else:
                        raise

            else:
                data = active_path.read_bytes()
                try:
                    self._resource_obj = conversions.get(self._restype, lambda _: None)(data)
                except Exception as e:  # noqa: BLE001
                    if self._restype == ResourceType.VIS:
                        RobustLogger().warning(
                            "Failed to parse VIS '%s.%s' from '%s': %s",
                            self._resname,
                            self._restype.extension,
                            active_path,
                            e,
                        )
                        self._resource_obj = None
                    else:
                        raise

        return self._resource_obj

    def to_bytes(self) -> bytes | None:
        if self._resource_obj is None:
            return None
        conversions: dict[ResourceType, Callable[[Any, TARGET_TYPES], Any]] = {
            ResourceType.ARE: write_are,
#            ResourceType.CNV: write_cnv,
            ResourceType.DLG: write_dlg,
            ResourceType.DWK: write_bwm,
#            ResourceType.FAC: write_fac,
            ResourceType.GIT: write_git,
            ResourceType.IFO: write_ifo,
            ResourceType.LYT: write_lyt,
#            ResourceType.MDL: write_mdl,
#            ResourceType.MDX: write_mdl,
            ResourceType.NCS: write_ncs,
            ResourceType.PTH: write_pth,
#            ResourceType.PWK: write_bwm,
            ResourceType.TPC: write_tpc,
            ResourceType.TGA: write_tpc,
            ResourceType.UTC: write_utc,
            ResourceType.UTD: write_utd,
            ResourceType.UTE: write_ute,
            ResourceType.UTI: write_uti,
            ResourceType.UTM: write_utm,
            ResourceType.UTP: write_utp,
            ResourceType.UTS: write_uts,
            ResourceType.UTT: write_utt,
            ResourceType.UTW: write_utw,
            ResourceType.VIS: write_vis,
            ResourceType.WOK: write_bwm,
        }
        result: bytearray = bytearray()
        conversions.get(self._restype, lambda _a, _b: b"")(self._resource_obj, result)
        return bytes(result)

    def add_locations(self, filepaths: Iterable[Path]):
        """Adds a list of filepaths to the list of locations stored for the resource.

        If a filepath already exists, it is ignored.

        Args:
        ----
            filepaths: A list of filepaths pointing to a location for the resource.
        """
        self._locations.extend(filepath for filepath in filepaths if filepath not in self._locations)

    def locations(self) -> list[Path]:
        return self._locations

    def activate(
        self,
        filepath: os.PathLike | str | None = None,
    ) -> Path | None:
        """Sets the active file to the specified path. Calling this method will reset the loaded resource.

        If the filepath is not in the stored locations, calling this method will add it.

        Args:
        ----
            filepath: The new active file.
        """
        self._resource_obj = None
        if filepath is None:
            self._active = next(iter(self._locations), None)
        else:
            r_filepath = Path(filepath)
            if r_filepath not in self._locations:
                self._locations.append(r_filepath)
            self._active = r_filepath
        if self._active is None:
            module_info = f" in module '{self._module_root}'" if self._module_root else ""
            installation_path = str(self._installation.path())
            locations_info = f"Searched locations: {[str(loc) for loc in self._locations]}." if self._locations else "No locations were added to this resource."
            RobustLogger().warning(
                f"Cannot activate module resource '{self.identifier()}'{module_info}: No locations found. "
                f"Installation: {installation_path}. {locations_info}"
            )
        #else:
        #    other_locations_available = len(self._locations) - 1
        #    other_locations_available_display = f" ({other_locations_available} other locations available)" if other_locations_available else ""
        #    print(f"Activating module resource '{self.identifier()}' at filepath '{self._active}'{other_locations_available_display}")
        return self._active

    def unload(self):
        """Clears the cached resource object from memory."""
        self._resource_obj = None

    def reload(self):
        """Reloads the resource object from the active location."""
        self._resource_obj = None
        self.resource()

    def active(self) -> Path | None:
        """Returns the filepath of the currently active file for the resource.

        Returns:
        -------
            Filepath to the active resource.
        """
        if self._active is None:
            next_path = next(iter(self._locations), None)
            if next_path is None:
                RobustLogger().warning("No resource found for '%s'", self._identifier)
                return None
            self.activate()
            # raise RuntimeError(f"{self!r}.activate(filepath) must be called before use.")
        return self._active

    def isActive(self) -> bool:
        return bool(self._active)

    def save(self):
        """Saves the resource to the active file.

        Args:
        ----
            self: The resource object

        Returns:
        -------
            None: This function does not return anything

        Processing Logic:
        ----------------
            - Checks if an active file is selected
            - Checks file type and writes resource data accordingly
            - Writes resource data to ERF, RIM or binary file using appropriate conversion and writer.
        """
        conversions: dict[ResourceType, Callable[[Any], bytes]] = {
            ResourceType.ARE: bytes_are,
            ResourceType.DLG: bytes_dlg,
            ResourceType.GIT: bytes_git,
            ResourceType.IFO: bytes_ifo,
            ResourceType.LYT: bytes_lyt,
            ResourceType.NCS: lambda data: data,
            ResourceType.PTH: bytes_pth,
            ResourceType.TPC: bytes_tpc,
            ResourceType.TGA: bytes_tpc,
            ResourceType.UTD: bytes_utd,
            ResourceType.UTE: bytes_ute,
            ResourceType.UTI: bytes_uti,
            ResourceType.UTM: bytes_utm,
            ResourceType.UTP: bytes_utp,
            ResourceType.UTS: bytes_uts,
            ResourceType.UTT: bytes_utt,
            ResourceType.UTW: bytes_utw,
            ResourceType.UTC: bytes_utc,
            ResourceType.VIS: bytes_vis,
            ResourceType.WOK: bytes_bwm,
        }

        active_path = self.active()
        if not active_path:
            active_path = self._create_anew_in_override()
        if is_bif_file(active_path):
            msg = "Cannot save file to BIF."
            raise ValueError(msg)

        if is_any_erf_type_file(active_path):
            erf: ERF = read_erf(active_path)
            erf.set_data(
                self._resname,
                self._restype,
                conversions[self._restype](self.resource()),
            )
            write_erf(erf, active_path)

        elif is_rim_file(active_path):
            rim: RIM = read_rim(active_path)
            rim.set_data(
                self._resname,
                self._restype,
                conversions[self._restype](self.resource()),
            )
            write_rim(rim, active_path)

        else:
            data = conversions.get(self._restype, lambda _: b"")(self.resource())
            if not data:
                raise ValueError(f"No conversion available for resource type {self._restype}")
            active_path.write_bytes(data)

    def _create_anew_in_override(self) -> Path:
        res_data: bytes | None = self.to_bytes()
        if res_data is None:
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                self._installation.override_path().joinpath(self.filename()),
            )

        RobustLogger().warning(f"Saving ModuleResource '{self.identifier()}' to the Override folder as it does not have any other paths available...")
        result = self._installation.override_path().joinpath(self.filename())
        result.write_bytes(res_data)
        self.activate(result)
        return result
