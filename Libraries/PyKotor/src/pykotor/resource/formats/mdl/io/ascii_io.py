from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.type import ResourceReader, ResourceWriter

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES
    pass


class MDLASCIIReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int | None = None,
        *,
        use_high_level_reader: bool = True,
    ):
        super().__init__(source, offset, size, use_high_level_reader=use_high_level_reader)


class MDLASCIIWriter(ResourceWriter):
    def __init__(
        self,
        target: TARGET_TYPES,
        *,
        use_high_level_writer: bool = True,
    ):
        super().__init__(target, use_high_level_writer=use_high_level_writer)
