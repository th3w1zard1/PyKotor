"""DDS (DirectDraw Surface) reader/writer for PyKotor TPC workflows.

This supports both the standard DirectDraw DDS container and BioWare's
NWN/KotOR-era DDS variant. The implementation mirrors the behaviour of:
-  (standard + BioWare reader)
-  (reader + detection)
Differences are documented inline where PyKotor maps DDS surfaces onto TPC
structures.
"""

from __future__ import annotations

import enum
import struct
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pykotor.resource.formats.tpc.tpc_data import TPC, TPCLayer, TPCMipmap, TPCTextureFormat
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class _DDSDataLayout(enum.Enum):
    DIRECT = "direct"
    ARGB4444 = "argb4444"
    A1R5G5B5 = "a1r5g5b5"
    R5G6B5 = "r5g6b5"


@dataclass
class _DDSPixelFormat:
    size: int
    flags: int
    fourcc: int
    bit_count: int
    r_mask: int
    g_mask: int
    b_mask: int
    a_mask: int


class TPCDDSReader(ResourceReader):
    """Parse DDS (standard + BioWare) images into a TPC instance."""

    MAGIC = 0x44445320  # "DDS "
    HEADER_SIZE = 124
    HEADER_FLAGS_MIPS = 0x00020000
    PIXELFLAG_ALPHA = 0x00000001
    PIXELFLAG_FOURCC = 0x00000004
    PIXELFLAG_INDEXED = 0x00000020
    PIXELFLAG_RGB = 0x00000040

    CAP_CUBEMAP = 0x00000200
    CAP_CUBEMAP_ALLFACES = 0x0000FC00

    FOURCC_DXT1 = 0x44585431  # "DXT1"
    FOURCC_DXT3 = 0x44585433  # "DXT3"
    FOURCC_DXT5 = 0x44585435  # "DXT5"

    MAX_DIMENSION = 0x8000

    def __init__(self, source: SOURCE_TYPES, offset: int = 0, size: int | None = None):
        super().__init__(source, offset, size or 0)
        self._tpc = TPC()

    @staticmethod
    def _scale_bits(value: int, bits: int) -> int:
        """Scale an N-bit channel to 0-255."""
        if bits <= 0:
            return 0
        max_in = (1 << bits) - 1
        return (value * 255) // max_in

    @staticmethod
    def _convert_4444(raw: bytes) -> bytearray:
        rgba = bytearray()
        for i in range(0, len(raw), 2):
            pixel = int.from_bytes(raw[i : i + 2], "little")
            r = TPCDDSReader._scale_bits((pixel >> 8) & 0x0F, 4)
            g = TPCDDSReader._scale_bits((pixel >> 4) & 0x0F, 4)
            b = TPCDDSReader._scale_bits(pixel & 0x0F, 4)
            a = TPCDDSReader._scale_bits((pixel >> 12) & 0x0F, 4)
            rgba.extend((r, g, b, a))
        return rgba

    @staticmethod
    def _convert_1555(raw: bytes) -> bytearray:
        rgba = bytearray()
        for i in range(0, len(raw), 2):
            pixel = int.from_bytes(raw[i : i + 2], "little")
            a = 0xFF if (pixel & 0x8000) else 0x00
            r = TPCDDSReader._scale_bits((pixel >> 10) & 0x1F, 5)
            g = TPCDDSReader._scale_bits((pixel >> 5) & 0x1F, 5)
            b = TPCDDSReader._scale_bits(pixel & 0x1F, 5)
            rgba.extend((r, g, b, a))
        return rgba

    @staticmethod
    def _convert_565(raw: bytes) -> bytearray:
        rgb = bytearray()
        for i in range(0, len(raw), 2):
            pixel = int.from_bytes(raw[i : i + 2], "little")
            r = TPCDDSReader._scale_bits((pixel >> 11) & 0x1F, 5)
            g = TPCDDSReader._scale_bits((pixel >> 5) & 0x3F, 6)
            b = TPCDDSReader._scale_bits(pixel & 0x1F, 5)
            rgb.extend((r, g, b))
        return rgb

    def _detect_format(self, fmt: _DDSPixelFormat) -> tuple[TPCTextureFormat, _DDSDataLayout]:
        """Map DDS pixel format to TPCTextureFormat and data layout.

        Mirrors 
        """
        data_layout = _DDSDataLayout.DIRECT

        if (fmt.flags & self.PIXELFLAG_FOURCC) and fmt.fourcc == self.FOURCC_DXT1:
            tpc_format = TPCTextureFormat.DXT1
        elif (fmt.flags & self.PIXELFLAG_FOURCC) and fmt.fourcc == self.FOURCC_DXT3:
            tpc_format = TPCTextureFormat.DXT3
        elif (fmt.flags & self.PIXELFLAG_FOURCC) and fmt.fourcc == self.FOURCC_DXT5:
            tpc_format = TPCTextureFormat.DXT5
        elif (
            fmt.flags & self.PIXELFLAG_RGB
            and fmt.flags & self.PIXELFLAG_ALPHA
            and fmt.bit_count == 32
            and fmt.r_mask == 0x00FF0000
            and fmt.g_mask == 0x0000FF00
            and fmt.b_mask == 0x000000FF
            and fmt.a_mask == 0xFF000000
        ):
            tpc_format = TPCTextureFormat.BGRA
        elif (
            fmt.flags & self.PIXELFLAG_RGB
            and not (fmt.flags & self.PIXELFLAG_ALPHA)
            and fmt.bit_count == 24
            and fmt.r_mask == 0x00FF0000
            and fmt.g_mask == 0x0000FF00
            and fmt.b_mask == 0x000000FF
        ):
            tpc_format = TPCTextureFormat.BGR
        elif (
            fmt.flags & self.PIXELFLAG_RGB
            and fmt.flags & self.PIXELFLAG_ALPHA
            and fmt.bit_count == 16
            and fmt.r_mask == 0x00007C00
            and fmt.g_mask == 0x000003E0
            and fmt.b_mask == 0x0000001F
            and fmt.a_mask == 0x00008000
        ):
            tpc_format = TPCTextureFormat.RGBA
            data_layout = _DDSDataLayout.A1R5G5B5
        elif (
            fmt.flags & self.PIXELFLAG_RGB
            and not (fmt.flags & self.PIXELFLAG_ALPHA)
            and fmt.bit_count == 16
            and fmt.r_mask == 0x0000F800
            and fmt.g_mask == 0x000007E0
            and fmt.b_mask == 0x0000001F
        ):
            tpc_format = TPCTextureFormat.RGB
            data_layout = _DDSDataLayout.R5G6B5
        elif (
            fmt.flags & self.PIXELFLAG_RGB
            and fmt.flags & self.PIXELFLAG_ALPHA
            and fmt.bit_count == 16
            and fmt.r_mask == 0x00000F00
            and fmt.g_mask == 0x000000F0
            and fmt.b_mask == 0x0000000F
            and fmt.a_mask == 0x0000F000
        ):
            tpc_format = TPCTextureFormat.RGBA
            data_layout = _DDSDataLayout.ARGB4444
        elif fmt.flags & self.PIXELFLAG_INDEXED:
            raise ValueError("Palette-based DDS images are not supported.")
        else:
            raise ValueError(
                f"Unknown DDS pixel format: flags={fmt.flags:#x} fourcc={fmt.fourcc:#x} "
                f"bit_count={fmt.bit_count} masks={fmt.r_mask:#x}/{fmt.g_mask:#x}/{fmt.b_mask:#x}/{fmt.a_mask:#x}"
            )

        return tpc_format, data_layout

    @autoclose
    def load(self, *, auto_close: bool = True) -> TPC:
        """Load DDS data into a TPC instance."""
        self._tpc = TPC()
        start_pos = self._reader.position()
        magic = self._reader.read_uint32(big=True)
        if magic == self.MAGIC:
            self._read_standard_header()
        else:
            self._reader.seek(start_pos)
            self._read_bioware_header()
        return self._tpc

    def _read_standard_header(self) -> None:
        header_size = self._reader.read_uint32()
        if header_size != self.HEADER_SIZE:
            raise ValueError(f"Invalid DDS header size: {header_size}")

        flags = self._reader.read_uint32()
        height = self._reader.read_uint32()
        width = self._reader.read_uint32()
        if width >= self.MAX_DIMENSION or height >= self.MAX_DIMENSION:
            raise ValueError(f"Unsupported image dimensions ({width}x{height})")

        self._reader.skip(8)  # pitch + depth
        mip_count = self._reader.read_uint32()
        if (flags & self.HEADER_FLAGS_MIPS) == 0:
            mip_count = 1

        self._reader.skip(44)
        fmt = _DDSPixelFormat(
            size=self._reader.read_uint32(),
            flags=self._reader.read_uint32(),
            fourcc=self._reader.read_uint32(big=True),
            bit_count=self._reader.read_uint32(),
            r_mask=self._reader.read_uint32(),
            g_mask=self._reader.read_uint32(),
            b_mask=self._reader.read_uint32(),
            a_mask=self._reader.read_uint32(),
        )
        tpc_format, data_layout = self._detect_format(fmt)

        _caps1 = self._reader.read_uint32()
        caps2 = self._reader.read_uint32()
        self._reader.skip(8)  # caps3 + caps4
        self._reader.skip(4)  # reserved2

        face_count = 1
        if caps2 & self.CAP_CUBEMAP:
            face_bits = caps2 & self.CAP_CUBEMAP_ALLFACES
            face_count = bin(face_bits).count("1") or 6
            self._tpc.is_cube_map = True

        self._tpc.is_animated = False
        self._tpc._format = tpc_format  # noqa: SLF001
        self._read_surfaces(width, height, mip_count, face_count, tpc_format, data_layout)

    def _read_bioware_header(self) -> None:
        width = self._reader.read_uint32()
        height = self._reader.read_uint32()
        if width >= self.MAX_DIMENSION or height >= self.MAX_DIMENSION:
            raise ValueError(f"Unsupported image dimensions ({width}x{height})")
        if width == 0 or height == 0 or (width & (width - 1)) or (height & (height - 1)):
            raise ValueError("BioWare DDS requires power-of-two dimensions.")

        bpp = self._reader.read_uint32()
        if bpp == 3:
            tpc_format = TPCTextureFormat.DXT1
        elif bpp == 4:
            tpc_format = TPCTextureFormat.DXT5
        else:
            raise ValueError(f"Unsupported BioWare DDS bytes-per-pixel value: {bpp}")

        data_size = self._reader.read_uint32()
        expected = (width * height) // 2 if bpp == 3 else width * height
        if data_size != expected:
            raise ValueError(f"BioWare DDS data size mismatch: {data_size} != {expected}")

        self._reader.skip(4)  # Unknown float
        full_data_size = self._reader.size() - self._reader.position()

        mip_count = 0
        tmp_width, tmp_height = width, height
        while tmp_width >= 1 and tmp_height >= 1:
            size_needed = tpc_format.get_size(tmp_width, tmp_height)
            if full_data_size < size_needed:
                break
            full_data_size -= size_needed
            mip_count += 1
            tmp_width >>= 1
            tmp_height >>= 1

        mip_count = max(1, mip_count)
        self._tpc.is_cube_map = False
        self._tpc.is_animated = False
        self._tpc._format = tpc_format  # noqa: SLF001
        self._read_surfaces(width, height, mip_count, 1, tpc_format, _DDSDataLayout.DIRECT)

    def _file_mipmap_size(self, width: int, height: int, tpc_format: TPCTextureFormat, layout: _DDSDataLayout) -> int:
        if layout in {_DDSDataLayout.A1R5G5B5, _DDSDataLayout.ARGB4444, _DDSDataLayout.R5G6B5}:
            return width * height * 2
        return tpc_format.get_size(width, height)

    def _convert_data(
        self,
        raw: bytes,
        width: int,
        height: int,
        layout: _DDSDataLayout,
    ) -> bytearray:
        if layout == _DDSDataLayout.DIRECT:
            return bytearray(raw)
        if layout == _DDSDataLayout.ARGB4444:
            return self._convert_4444(raw)
        if layout == _DDSDataLayout.A1R5G5B5:
            return self._convert_1555(raw)
        if layout == _DDSDataLayout.R5G6B5:
            return self._convert_565(raw)
        raise ValueError(f"Unsupported DDS data layout: {layout}")

    def _read_surfaces(
        self,
        width: int,
        height: int,
        mip_count: int,
        face_count: int,
        tpc_format: TPCTextureFormat,
        layout: _DDSDataLayout,
    ) -> None:
        face_count = max(1, face_count)
        for _ in range(face_count):
            layer = TPCLayer()
            self._tpc.layers.append(layer)
            mm_width, mm_height = width, height
            for _ in range(mip_count):
                mm_width = max(1, mm_width)
                mm_height = max(1, mm_height)
                file_size = self._file_mipmap_size(mm_width, mm_height, tpc_format, layout)
                raw = self._reader.read_bytes(file_size)
                if len(raw) != file_size:
                    raise ValueError("DDS truncated while reading mip data.")
                data = self._convert_data(raw, mm_width, mm_height, layout)
                layer.mipmaps.append(
                    TPCMipmap(
                        width=mm_width,
                        height=mm_height,
                        tpc_format=tpc_format if layout == _DDSDataLayout.DIRECT else (TPCTextureFormat.RGB if layout == _DDSDataLayout.R5G6B5 else TPCTextureFormat.RGBA),
                        data=data,
                    )
                )
                mm_width >>= 1
                mm_height >>= 1


class TPCDDSWriter(ResourceWriter):
    """Serialize TPC textures as standard DDS images."""

    MAGIC = b"DDS "
    HEADER_SIZE = 124

    DDSD_CAPS = 0x1
    DDSD_HEIGHT = 0x2
    DDSD_WIDTH = 0x4
    DDSD_PITCH = 0x8
    DDSD_PIXELFORMAT = 0x1000
    DDSD_MIPMAPCOUNT = 0x20000
    DDSD_LINEARSIZE = 0x80000

    DDSCAPS_TEXTURE = 0x1000
    DDSCAPS_MIPMAP = 0x400000
    DDSCAPS_COMPLEX = 0x8

    DDSCAPS2_CUBEMAP = 0x00000200
    DDSCAPS2_ALLFACES = 0x0000FC00

    DDPF_ALPHAPIXELS = 0x1
    DDPF_FOURCC = 0x4
    DDPF_RGB = 0x40

    def __init__(self, tpc: TPC, target: TARGET_TYPES):
        super().__init__(target)
        self._tpc = tpc

    def _pixel_format_fields(self, fmt: TPCTextureFormat) -> tuple[int, int, int, int, int, int, int]:
        """Return (ddpf_flags, fourcc, bitcount, rmask, gmask, bmask, amask)."""
        # Aligns with  mappings.
        if fmt == TPCTextureFormat.DXT1:
            return self.DDPF_FOURCC, 0x44585431, 0, 0, 0, 0, 0
        if fmt == TPCTextureFormat.DXT3:
            return self.DDPF_FOURCC, 0x44585433, 0, 0, 0, 0, 0
        if fmt == TPCTextureFormat.DXT5:
            return self.DDPF_FOURCC, 0x44585435, 0, 0, 0, 0, 0
        if fmt == TPCTextureFormat.BGRA:
            return (self.DDPF_RGB | self.DDPF_ALPHAPIXELS, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
        if fmt == TPCTextureFormat.BGR:
            return (self.DDPF_RGB, 0, 24, 0x00FF0000, 0x0000FF00, 0x000000FF, 0)
        raise ValueError(f"DDS writer does not support format {fmt!r}")

    def _ensure_supported_format(self) -> TPCTextureFormat:
        fmt = self._tpc.format()
        if fmt in (TPCTextureFormat.DXT1, TPCTextureFormat.DXT3, TPCTextureFormat.DXT5, TPCTextureFormat.BGR, TPCTextureFormat.BGRA):
            return fmt
        if fmt == TPCTextureFormat.RGB:
            return TPCTextureFormat.BGR
        if fmt == TPCTextureFormat.RGBA:
            return TPCTextureFormat.BGRA
        raise ValueError(f"Unsupported TPC format for DDS export: {fmt!r}")

    def _convert_mipmap_payload(self, mipmap: TPCMipmap, target_format: TPCTextureFormat) -> bytes:
        if mipmap.tpc_format == target_format:
            return bytes(mipmap.data)
        copy = mipmap.copy()
        copy.convert(target_format)
        return bytes(copy.data)

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002
        if not self._tpc.layers or not self._tpc.layers[0].mipmaps:
            raise ValueError("TPC contains no mipmaps to write as DDS.")

        target_format = self._ensure_supported_format()
        layer0 = self._tpc.layers[0]
        base = layer0.mipmaps[0]
        width, height = base.width, base.height
        mip_count = len(layer0.mipmaps)
        face_count = len(self._tpc.layers) if self._tpc.is_cube_map else 1

        flags = self.DDSD_CAPS | self.DDSD_HEIGHT | self.DDSD_WIDTH | self.DDSD_PIXELFORMAT
        if target_format.is_dxt():
            flags |= self.DDSD_LINEARSIZE
            pitch_or_linear = target_format.get_size(width, height)
        else:
            flags |= self.DDSD_PITCH
            pitch_or_linear = width * target_format.bytes_per_pixel()

        if mip_count > 1:
            flags |= self.DDSD_MIPMAPCOUNT

        pf_flags, fourcc, bitcount, rmask, gmask, bmask, amask = self._pixel_format_fields(target_format)

        caps1 = self.DDSCAPS_TEXTURE
        caps2 = 0
        if mip_count > 1:
            caps1 |= self.DDSCAPS_MIPMAP | self.DDSCAPS_COMPLEX
        if self._tpc.is_cube_map:
            caps1 |= self.DDSCAPS_COMPLEX
            caps2 |= self.DDSCAPS2_CUBEMAP | self.DDSCAPS2_ALLFACES

        header = bytearray()
        header += self.MAGIC
        header += struct.pack("<I", self.HEADER_SIZE)
        header += struct.pack("<I", flags)
        header += struct.pack("<I", height)
        header += struct.pack("<I", width)
        header += struct.pack("<I", pitch_or_linear)
        header += struct.pack("<I", 0)  # depth
        header += struct.pack("<I", mip_count)
        header += bytes(44)
        header += struct.pack("<I", 32)
        header += struct.pack("<I", pf_flags)
        header += struct.pack(">I", fourcc)
        header += struct.pack("<I", bitcount)
        header += struct.pack("<I", rmask)
        header += struct.pack("<I", gmask)
        header += struct.pack("<I", bmask)
        header += struct.pack("<I", amask)
        header += struct.pack("<I", caps1)
        header += struct.pack("<I", caps2)
        header += bytes(12)  # caps3, caps4, reserved

        self._writer.write_bytes(bytes(header))

        for face in range(face_count):
            layer = self._tpc.layers[face] if self._tpc.is_cube_map else self._tpc.layers[0]
            if len(layer.mipmaps) < mip_count:
                raise ValueError(f"Layer {face} does not contain {mip_count} mipmaps required for DDS export.")
            mm_width, mm_height = width, height
            for mip_index in range(mip_count):
                mipmap = layer.mipmaps[mip_index]
                expected_w, expected_h = max(1, mm_width), max(1, mm_height)
                if mipmap.width != expected_w or mipmap.height != expected_h:
                    raise ValueError(
                        f"Mipmap {mip_index} dimensions mismatch: expected {expected_w}x{expected_h}, "
                        f"found {mipmap.width}x{mipmap.height}"
                    )
                payload = self._convert_mipmap_payload(mipmap, target_format)
                self._writer.write_bytes(payload)
                mm_width >>= 1
                mm_height >>= 1

