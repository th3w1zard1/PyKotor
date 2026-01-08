from __future__ import annotations

from abc import ABC, abstractmethod
from copy import copy
from enum import Enum
from typing import TYPE_CHECKING, TypeVar, cast

from pykotor.common.misc import ResRef  # type: ignore[import-untyped]
from pykotor.extract.file import ResourceIdentifier  # type: ignore[import-untyped]
from pykotor.resource.formats._base import ComparableMixin  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import ClassVar

    from typing_extensions import Self  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.formats.bif import BIF  # type: ignore[import-untyped]
    from pykotor.resource.formats.erf import ERF  # type: ignore[import-untyped]
    from pykotor.resource.formats.rim import RIM  # type: ignore[import-untyped]
    from pykotor.resource.type import ResourceType  # type: ignore[import-untyped]

B = TypeVar("B")


class HashAlgo(Enum):
    NONE = 0
    CRC32 = 1
    FNV32 = 2
    FNV64 = 3
    JENKINS = 4


class ArchiveResource:
    """Represents a resource stored within a BioWare archive (ERF, RIM, BIF).

    Contains resource reference, type, and data. Used as the base resource type
    for archive-based resource storage.

    References:
    ----------
        BioWare archive format specification
    """

    def __init__(
        self,
        resref: ResRef,
        restype: ResourceType,
        data: bytes,
        size: int | None = None,
    ):
        self.resref: ResRef = resref
        self.restype: ResourceType = restype
        if isinstance(data, bytearray):
            data = bytes(data)
        self.data: bytes = data
        self.size: int = len(data) if size is None else size

    def __eq__(
        self,
        other,  # noqa: ANN001
    ) -> bool:
        if self is other or hash(self) == hash(other):
            return True
        if not isinstance(other, ArchiveResource):
            return NotImplemented
        return self.resref == other.resref and self.restype == other.restype and self.data == other.data

    def __hash__(self):
        return hash((self.resref, self.restype, self.data))

    def identifier(self) -> ResourceIdentifier:
        return ResourceIdentifier(str(self.resref), self.restype)

    def __repr__(self) -> str:
        """Return a concise string representation suitable for diff output."""
        return f"Resource(resref={self.resref!r}, restype={self.restype.name}, size={self.size})"

    def __str__(self) -> str:
        """Return a human-readable string representation of the resource."""
        try:
            return self._str_for_resource_type()
        except Exception:
            # Fallback to basic representation if conversion fails
            return f"Resource '{self.resref}' ({self.restype.name}, {self.size} bytes)"

    def _str_for_resource_type(self) -> str:
        """Convert resource data to human-readable format based on type."""
        from pykotor.resource.type import ResourceType

        # Handle text-based resources
        if self.restype in (ResourceType.NSS, ResourceType.NCS):
            try:
                text = self.data.decode("utf-8", errors="replace")
                if self.restype == ResourceType.NSS:
                    return f"NSS Script '{self.resref}':\n{text}"
                else:
                    return f"NCS Script '{self.resref}' (compiled, {self.size} bytes)"
            except UnicodeDecodeError:
                return f"Script '{self.resref}' ({self.restype.name}, {self.size} bytes, binary)"

        # Handle GFF-based resources
        elif self.restype.is_gff():
            try:
                from pykotor.resource.formats.gff import read_gff

                gff = read_gff(self.data)
                gff_str = str(gff)
                if gff_str.startswith("<"):  # If str() returns repr-like output, try repr
                    gff_str = repr(gff)
                if len(gff_str) > 1000:  # Limit output for large GFFs
                    gff_str = gff_str[:997] + "..."
                return f"GFF {self.restype.name} '{self.resref}':\n{gff_str}"
            except Exception as e:
                return f"GFF {self.restype.name} '{self.resref}' ({self.size} bytes, parse error: {e})"

        # Handle TLK resources
        elif self.restype == ResourceType.TLK:
            try:
                from pykotor.resource.formats.tlk import read_tlk

                tlk = read_tlk(self.data)
                entry_count = len(tlk)
                return f"TLK '{self.resref}' ({entry_count} entries, {self.size} bytes)"
            except Exception:
                return f"TLK '{self.resref}' ({self.size} bytes, parse error)"

        # Handle TPC resources
        elif self.restype == ResourceType.TPC:
            try:
                from pykotor.resource.formats.tpc import read_tpc

                tpc = read_tpc(self.data)
                if tpc.layers and tpc.layers[0].mipmaps:
                    width = tpc.layers[0].mipmaps[0].width
                    height = tpc.layers[0].mipmaps[0].height
                    return f"TPC Texture '{self.resref}' ({width}x{height}, {self.size} bytes)"
                else:
                    return f"TPC Texture '{self.resref}' ({self.size} bytes)"
            except Exception:
                return f"TPC Texture '{self.resref}' ({self.size} bytes, parse error)"

        # Handle 2DA resources
        elif self.restype == ResourceType.TwoDA:
            try:
                from pykotor.resource.formats.twoda import read_2da

                twoda = read_2da(self.data)
                return f"2DA '{self.resref}' ({len(twoda)} rows, {len(twoda._headers)} columns)"
            except Exception:
                return f"2DA '{self.resref}' ({self.size} bytes, parse error)"

        # Handle image resources
        elif self.restype in (ResourceType.TGA, ResourceType.TXI):
            if self.restype == ResourceType.TGA:
                return f"TGA Image '{self.resref}' ({self.size} bytes)"
            else:
                try:
                    text = self.data.decode("utf-8", errors="replace")
                    return f"TXI Info '{self.resref}':\n{text}"
                except UnicodeDecodeError:
                    return f"TXI Info '{self.resref}' ({self.size} bytes, binary)"

        # Handle sound resources
        elif self.restype in (ResourceType.WAV, ResourceType.BMU, ResourceType.WMA, ResourceType.WMV):
            return f"Audio '{self.resref}' ({self.restype.name}, {self.size} bytes)"

        # Handle model resources
        elif self.restype in (ResourceType.MDL, ResourceType.MDX):
            return f"Model '{self.resref}' ({self.restype.name}, {self.size} bytes)"

        # Handle dialog resources
        elif self.restype == ResourceType.DLG:
            try:
                from pykotor.resource.formats.gff import read_gff

                gff = read_gff(self.data)
                gff_str = str(gff)
                if len(gff_str) > 1000:  # Limit output for large GFFs
                    gff_str = gff_str[:997] + "..."
                return f"Dialog '{self.resref}':\n{gff_str}"
            except Exception as e:
                return f"Dialog '{self.resref}' ({self.size} bytes, parse error: {e})"

        # Default fallback
        else:
            return f"Resource '{self.resref}' ({self.restype.name}, {self.size} bytes)"


class BiowareArchive(ComparableMixin, ABC):
    """Abstract base class for BioWare archive formats (ERF, RIM, BIF).

    Provides common interface for archive operations including resource storage,
    retrieval, and comparison. Subclasses implement format-specific reading/writing.

    References:
    ----------
        BioWare archive format specification
    """

    BINARY_TYPE: ClassVar[ResourceType]
    ARCHIVE_TYPE: type[ArchiveResource] = ArchiveResource
    COMPARABLE_SET_FIELDS: ClassVar[tuple[str, ...]] = ("_resources",)

    def __init__(self) -> None:
        self._resources: list[ArchiveResource] = []
        self._resource_dict: dict[ResourceIdentifier, ArchiveResource] = {}

    @abstractmethod
    def get_resource_offset(self, resource: ArchiveResource) -> int: ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(resources=[{self._resources!r}])"

    def __iter__(self) -> Iterator[ArchiveResource]:  # noqa: B027
        yield from self._resources.copy()

    def __len__(self) -> int:
        return len(self._resources)

    def __getitem__(
        self,
        item: int | str | ResourceIdentifier,
    ) -> ArchiveResource:
        if isinstance(item, int):
            return copy(self._resources[item])
        if isinstance(item, str):
            item = ResourceIdentifier.from_path(item)
        if not isinstance(item, ResourceIdentifier):
            raise TypeError(f"Expected ResourceIdentifier, got {type(item)}")
        return copy(self._resource_dict[item])

    def __contains__(
        self,
        item: str | ResourceIdentifier,
    ) -> bool:
        return item in self._resource_dict

    def __setitem__(
        self,
        key: str | ResourceIdentifier,
        value: ArchiveResource,
    ):
        if isinstance(key, str):
            key = ResourceIdentifier(key, value.restype)
        self._resource_dict[key] = value
        if value not in self._resources:
            self._resources.append(value)

    def __delitem__(
        self,
        key: str | ResourceIdentifier,
    ):
        if isinstance(key, str):
            key = ResourceIdentifier.from_path(key)
        self._resources.remove(cast(dict[ResourceIdentifier, ArchiveResource], self._resource_dict).pop(key))

    def __add__(
        self,
        other: BiowareArchive,
    ) -> Self:  # noqa: ANN001
        if not isinstance(other, BiowareArchive):
            return NotImplemented

        combined_archive: Self = self.__class__()
        resource: ArchiveResource
        for resource in self:
            combined_archive.set_data(str(resource.resref), resource.restype, resource.data)
        for resource in other:
            combined_archive.set_data(str(resource.resref), resource.restype, resource.data)

        return combined_archive

    def __eq__(
        self,
        other: object,  # noqa: ANN001
    ) -> bool:
        if self is other:
            return True
        if not isinstance(other, BiowareArchive):
            return NotImplemented
        return (
            set(self._resources) == set(other._resources) and super().__eq__(other)  # ComparableMixin.__eq__
        )

    def set_resource(
        self,
        resname: str,
        restype: ResourceType,
        data: bytes,
    ):
        self.set_data(resname, restype, data)

    def set_data(
        self,
        resname: str,
        restype: ResourceType,
        data: bytes,
    ) -> None:
        resource: ArchiveResource | None = next(
            (resource for resource in cast(list[ArchiveResource], self._resources) if resource.resref == resname and resource.restype == restype),
            None,
        )
        if resource is None:
            resource = self.ARCHIVE_TYPE(ResRef(resname), restype, data)
            self._resources.append(resource)
            self._resource_dict[resource.identifier()] = resource
        else:
            resource.data = data

    def get(
        self,
        resname: str,
        restype: ResourceType,
    ) -> bytes | None:
        resource_dict: dict[ResourceIdentifier, ArchiveResource] = cast(dict[ResourceIdentifier, ArchiveResource], self._resource_dict)
        resource: ArchiveResource | None = resource_dict.get(ResourceIdentifier(resname, restype), None)
        return None if resource is None else resource.data

    def get_data(
        self,
        resname: str,
        restype: ResourceType,
    ) -> bytes | None:
        return self.get(resname, restype)

    def has(
        self,
        resname: str,
        restype: ResourceType,
    ) -> bool:
        return ResourceIdentifier(resname, restype) in self._resource_dict

    def remove(
        self,
        resname: str,
        restype: ResourceType,
    ):
        key = ResourceIdentifier(resname, restype)
        popped_resource: ArchiveResource | None = self._resource_dict.pop(key, None)
        assert popped_resource is not None, f"Resource '{key.resref}' not found in archive"
        self._resources.remove(popped_resource)

    def find_resource_by_hash(
        self,
        h: int,
    ) -> int | None:
        return next(
            (i for i, resource in enumerate(self._resources) if hash(resource) == h),
            None,
        )

    def to_bif(self) -> BIF:
        from pykotor.resource.formats.bif.bif_data import BIF  # Prevent circular imports

        bif = BIF()
        for resource in cast(list[ArchiveResource], self._resources):
            bif.set_data(ResRef(resource.resref), resource.restype, resource.data)
        return bif

    def to_erf(self) -> ERF:
        from pykotor.resource.formats.erf.erf_data import ERF  # Prevent circular imports

        erf = ERF()
        for resource in cast(list[ArchiveResource], self._resources):
            erf.set_data(ResRef(resource.resref), resource.restype, resource.data)
        return erf

    def to_rim(self) -> RIM:
        from pykotor.resource.formats.rim.rim_data import RIM  # Prevent circular imports

        rim = RIM()
        for resource in cast(list[ArchiveResource], self._resources):
            rim.set_data(ResRef(resource.resref), resource.restype, resource.data)
        return rim
