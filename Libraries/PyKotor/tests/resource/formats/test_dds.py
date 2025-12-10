from __future__ import annotations

import struct
import unittest

from pykotor.resource.formats.tpc import (
    TPC,
    TPCLayer,
    TPCMipmap,
    TPCTextureFormat,
    read_tpc,
    bytes_tpc,
)
from pykotor.resource.formats.tpc.tpc_auto import detect_tpc
from pykotor.resource.formats.tpc.convert.dxt.compress_dxt import rgb_to_dxt1
from pykotor.resource.formats.tpc.convert.dxt.decompress_dxt import dxt1_to_rgb, dxt5_to_rgba
from pykotor.resource.type import ResourceType


class TestDDSParsing(unittest.TestCase):
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

    DDPF_ALPHAPIXELS = 0x1
    DDPF_FOURCC = 0x4
    DDPF_RGB = 0x40

    @staticmethod
    def _write_standard_dds_header(
        width: int,
        height: int,
        mip_count: int,
        *,
        fourcc: bytes | None,
        bitcount: int,
        masks: tuple[int, int, int, int],
        ddpf_flags: int,
    ) -> bytearray:
        header_flags = (
            TestDDSParsing.DDSD_CAPS
            | TestDDSParsing.DDSD_HEIGHT
            | TestDDSParsing.DDSD_WIDTH
            | TestDDSParsing.DDSD_PIXELFORMAT
        )
        if fourcc:
            header_flags |= TestDDSParsing.DDSD_LINEARSIZE
            pitch_or_linear = max(1, ((width + 3) // 4) * ((height + 3) // 4)) * (8 if fourcc == b"DXT1" else 16)
        else:
            header_flags |= TestDDSParsing.DDSD_PITCH
            pitch_or_linear = width * (bitcount // 8)

        if mip_count > 1:
            header_flags |= TestDDSParsing.DDSD_MIPMAPCOUNT

        caps1 = TestDDSParsing.DDSCAPS_TEXTURE
        if mip_count > 1:
            caps1 |= TestDDSParsing.DDSCAPS_MIPMAP | TestDDSParsing.DDSCAPS_COMPLEX

        header = bytearray()
        header += b"DDS "
        header += struct.pack("<I", 124)
        header += struct.pack("<I", header_flags)
        header += struct.pack("<I", height)
        header += struct.pack("<I", width)
        header += struct.pack("<I", pitch_or_linear)
        header += struct.pack("<I", 0)  # depth
        header += struct.pack("<I", mip_count)
        header += bytes(44)  # reserved
        header += struct.pack("<I", 32)  # pixel format size
        header += struct.pack("<I", ddpf_flags)
        header += fourcc if fourcc else b"\x00\x00\x00\x00"
        header += struct.pack("<I", bitcount)
        header += struct.pack("<I", masks[0])
        header += struct.pack("<I", masks[1])
        header += struct.pack("<I", masks[2])
        header += struct.pack("<I", masks[3])
        header += struct.pack("<I", caps1)
        header += struct.pack("<I", 0)  # caps2
        header += bytes(12)
        return header

    def test_standard_dds_dxt1_roundtrip(self):
        width = height = 4
        rgb = bytearray([255, 0, 0] * (width * height))
        dxt1 = rgb_to_dxt1(rgb, width, height)

        header = self._write_standard_dds_header(
            width,
            height,
            mip_count=1,
            fourcc=b"DXT1",
            bitcount=0,
            masks=(0, 0, 0, 0),
            ddpf_flags=self.DDPF_FOURCC,
        )
        dds_bytes = bytes(header + dxt1)

        self.assertEqual(ResourceType.DDS, detect_tpc(dds_bytes))
        tpc = read_tpc(dds_bytes)
        self.assertEqual(TPCTextureFormat.DXT1, tpc.format())
        self.assertEqual(width, tpc.layers[0].mipmaps[0].width)
        decompressed = dxt1_to_rgb(tpc.layers[0].mipmaps[0].data, width, height)
        expected = dxt1_to_rgb(dxt1, width, height)
        self.assertEqual(len(decompressed), width * height * 3)
        self.assertEqual(decompressed, expected)

        # Writer roundtrip keeps payload identical for DXT1
        roundtrip = read_tpc(bytes_tpc(tpc, ResourceType.DDS))
        self.assertEqual(tpc.layers[0].mipmaps[0].data, roundtrip.layers[0].mipmaps[0].data)

    def test_bioware_dds_multiple_mips(self):
        width = height = 4
        data_size = width * height
        # Two mip levels, each occupying 16 bytes for DXT5
        mip0 = bytes([0xAA] * 16)
        mip1 = bytes([0x55] * 16)
        header = struct.pack("<IIIII", width, height, 4, data_size, 0)
        bioware_dds = header + mip0 + mip1

        tpc = read_tpc(bioware_dds)
        self.assertEqual(TPCTextureFormat.DXT5, tpc.format())
        self.assertEqual(2, len(tpc.layers[0].mipmaps))
        dxt_payload = tpc.layers[0].mipmaps[0].data
        decompressed = dxt5_to_rgba(dxt_payload, width, height)
        self.assertEqual(len(decompressed), width * height * 4)

    def test_uncompressed_bgra_header(self):
        width = height = 2
        # Simple 2x2 BGRA payload (blue, green, red, white)
        pixels = bytes(
            [
                0xFF,
                0x00,
                0x00,
                0xFF,  # blue
                0x00,
                0xFF,
                0x00,
                0xFF,  # green
                0x00,
                0x00,
                0xFF,
                0xFF,  # red
                0xFF,
                0xFF,
                0xFF,
                0xFF,  # white
            ]
        )

        header = self._write_standard_dds_header(
            width,
            height,
            mip_count=1,
            fourcc=None,
            bitcount=32,
            masks=(0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000),
            ddpf_flags=self.DDPF_RGB | self.DDPF_ALPHAPIXELS,
        )
        dds_bytes = bytes(header + pixels)
        tpc = read_tpc(dds_bytes)
        self.assertEqual(TPCTextureFormat.BGRA, tpc.format())
        mip = tpc.layers[0].mipmaps[0]
        self.assertEqual(bytes(mip.data[:4]), b"\xff\x00\x00\xff")

    def test_dds_writer_from_tpc_instance(self):
        width = height = 4
        rgb = bytearray([10, 20, 30] * (width * height))
        dxt1 = rgb_to_dxt1(rgb, width, height)
        tpc = TPC()
        layer = TPCLayer([TPCMipmap(width, height, TPCTextureFormat.DXT1, bytearray(dxt1))])
        tpc.layers = [layer]
        tpc._format = TPCTextureFormat.DXT1  # noqa: SLF001
        written = bytes_tpc(tpc, ResourceType.DDS)
        parsed = read_tpc(written)
        self.assertEqual(TPCTextureFormat.DXT1, parsed.format())
        self.assertEqual(dxt1, parsed.layers[0].mipmaps[0].data)


if __name__ == "__main__":
    unittest.main()

