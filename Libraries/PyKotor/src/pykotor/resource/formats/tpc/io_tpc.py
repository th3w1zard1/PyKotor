from __future__ import annotations

import math
import re

from typing import TYPE_CHECKING

from pykotor.resource.formats.tpc.io_txi_post import process_tpc_animations_data, process_tpc_cubemaps_data
from pykotor.resource.formats.tpc.tpc_data import TPC, TPCTextureFormat
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class TPCBinaryReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
        txi_lines: str | None = None,
    ):
        super().__init__(source, offset, size)
        self._tpc: TPC | None = None
        self._txi_lines: str | None = None

    @autoclose
    def load(
        self,
        auto_close: bool = True,
    ) -> TPC:
        """Loads a texture from the reader and returns a TPC object.

        Args:
        ----
            auto_close: Whether to close the reader after loading (default True)

        Returns:
        -------
            TPC: The loaded TPC texture object

        Processing Logic:
        ----------------
            - Reads header values like size, dimensions, format
            - Skips unnecessary data
            - Loops to read each mipmap level
            - Sets TPC data and returns the object
        """
        self._tpc = TPC()

        size: int = self._reader.read_uint32()
        min_size = -1
        compressed: bool = size != 0

        self._reader.skip(4)

        width, height = self._reader.read_uint16(), self._reader.read_uint16()
        color_depth = self._reader.read_uint8()
        mipmap_count = self._reader.read_uint8()
        self._reader.skip(114)

        tpc_format = TPCTextureFormat.Invalid
        if compressed:
            if color_depth == 2:
                tpc_format = TPCTextureFormat.DXT1
            elif color_depth == 4:
                tpc_format = TPCTextureFormat.DXT5
        elif color_depth == 1:
            tpc_format = TPCTextureFormat.Greyscale
        elif color_depth == 2:
            tpc_format = TPCTextureFormat.RGB
        elif color_depth == 4:
            tpc_format = TPCTextureFormat.RGBA

        mipmaps: list[bytes] = []
        mm_width, mm_height = width, height
        for _ in range(mipmap_count):
            mm_size = _get_size(mm_width, mm_height, tpc_format) or min_size
            mm_data = self._reader.read_bytes(mm_size)
            mipmaps.append(mm_data)

            mm_width >>= 1
            mm_height >>= 1
            mm_width = max(mm_width, 1)
            mm_height = max(mm_height, 1)

        file_size = self._reader.size()
        txi = self._reader.read_string(file_size - self._reader.position(), encoding="ascii")

        self._tpc.txi = self._txi_lines or txi

        # Since animated textures don't use mipmaps in the same way, we store only the base level
        cubemap_result = process_tpc_cubemaps_data(self, self._tpc.txi)
        flipbook_result = process_tpc_animations_data(self, self._tpc.txi)
        if cubemap_result is None and flipbook_result is None:
            return self._tpc

        if cubemap_result:
            face_size, post_count = cubemap_result
            #tpc_reader._tpc._cubemap_size = face_size * 6  # There are 6 faces in a cubemap. Assign this to a method at some point.
            # We'll store each face as a separate mipmap in the existing _mipmaps list
            self._tpc._mipmaps = [self._reader.read_bytes(face_size) for _ in range(6)]
            # Recalculate the mipmap count for the cubemap based on one face's dimensions
            #tpc_reader._tpc._mipmap_count = int(math.log(tpc_reader._tpc._width, 2)) + 1

        if flipbook_result:
            post_size, post_count = flipbook_result
            self._tpc._mipmaps = [self._reader.read_bytes(post_size) for _ in range(post_count)]
            self._tpc._is_flipbook = True

        self._tpc.set_data(width, height, mipmaps, tpc_format)

        return self._tpc


class TPCBinaryWriter(ResourceWriter):
    def __init__(
        self,
        tpc: TPC,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._tpc: TPC = tpc

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ):
        """Writes the TPC texture data to the file stream.

        Args:
        ----
            auto_close: Whether to close the file stream after writing (default: True)

        Writes TPC texture data to file stream:
            - Gets texture data from TPC object
            - Writes header information like size, dimensions, encoding
            - Writes raw texture data
            - Writes TXI data
            - Optionally closes file stream..
        """
        data = bytearray()
        size: int = 0

        for i in range(self._tpc.mipmap_count()):
            width, height, texture_format, mm_data = self._tpc.get(i)
            assert mm_data is not None
            data += mm_data
            detsize = _get_size(width, height, texture_format)
            assert detsize is not None
            size += detsize

        if self._tpc.format() == TPCTextureFormat.RGBA:
            encoding = 4
            size = 0
        elif self._tpc.format() == TPCTextureFormat.RGB:
            encoding = 2
            size = 0
        elif self._tpc.format() == TPCTextureFormat.Greyscale:
            encoding = 1
            size = 0
        elif self._tpc.format() == TPCTextureFormat.DXT1:
            encoding = 2
        elif self._tpc.format() == TPCTextureFormat.DXT5:
            encoding = 4
        else:
            msg = "Invalid TPC texture format."
            raise ValueError(msg)

        width, height = self._tpc.dimensions()

        self._writer.write_uint32(size)
        self._writer.write_single(0.0)
        self._writer.write_uint16(width)
        self._writer.write_uint16(height)
        self._writer.write_uint8(encoding)
        self._writer.write_uint8(self._tpc.mipmap_count())
        self._writer.write_bytes(b"\x00" * 114)
        self._writer.write_bytes(data)
        self._writer.write_bytes(self._tpc.txi.encode("ascii"))
