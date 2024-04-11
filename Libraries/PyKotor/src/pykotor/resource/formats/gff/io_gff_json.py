from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.gff.gff_data import GFF
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class GFFJSONReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._gff: GFF | None = None

    @autoclose
    def load(
        self,
        auto_close: bool = True,
    ) -> GFF:
        self._gff = GFF.from_json(self._reader.read_all().decode())
        return self._gff


class GFFJSONWriter(ResourceWriter):
    def __init__(
        self,
        gff: GFF,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self.gff: GFF = gff

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ):
        self._writer.write_string(self.gff.as_json())
