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
from pykotor.resource.formats.tpc.convert.dxt.decompress_dxt import dxt1_to_rgb, dxt3_to_rgba, dxt5_to_rgba
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
        caps2: int = 0,
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
        header += struct.pack("<I", caps2)  # caps2
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

    def test_standard_dds_dxt5_alpha_and_multiple_mips(self):
        width = height = 4
        rgba = bytearray([0, 0, 0, 0, 0, 0, 0, 255] * 8)  # alternating transparent/opaque
        # DXT5 block from existing converter for consistency
        dxt5_block = bytearray(
            [
                0xFF,
                0x00,  # alpha endpoints (alpha0=255, alpha1=0)
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,  # alpha indices
                0x00,
                0x1F,
                0x00,
                0x1F,
                0x00,
                0x1F,
                0x00,
                0x1F,  # color endpoints = pure red
            ]
        )
        mip1 = bytes([0xAA] * 16)  # second mip (2x2) placeholder

        header = self._write_standard_dds_header(
            width,
            height,
            mip_count=2,
            fourcc=b"DXT5",
            bitcount=0,
            masks=(0, 0, 0, 0),
            ddpf_flags=self.DDPF_FOURCC,
        )
        dds_bytes = bytes(header + dxt5_block + mip1)
        tpc = read_tpc(dds_bytes)
        self.assertEqual(TPCTextureFormat.DXT5, tpc.format())
        self.assertEqual(2, len(tpc.layers[0].mipmaps))
        rgba_decoded = dxt5_to_rgba(tpc.layers[0].mipmaps[0].data, width, height)
        self.assertEqual(len(rgba_decoded), width * height * 4)
        self.assertGreater(sum(rgba_decoded[3::4]), 0)  # alpha present

    def test_standard_dds_uncompressed_bgr_24bit(self):
        width = height = 2
        # Pixel order: blue, green, red, white (BGR)
        pixels = bytes(
            [
                0xFF,
                0x00,
                0x00,  # blue
                0x00,
                0xFF,
                0x00,  # green
                0x00,
                0x00,
                0xFF,  # red
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
            bitcount=24,
            masks=(0x00FF0000, 0x0000FF00, 0x000000FF, 0),
            ddpf_flags=self.DDPF_RGB,
        )
        tpc = read_tpc(bytes(header + pixels))
        self.assertEqual(TPCTextureFormat.BGR, tpc.format())
        self.assertEqual(bytes(tpc.layers[0].mipmaps[0].data[:3]), b"\xff\x00\x00")

    def test_uncompressed_16bit_paths_4444_1555_565(self):
        width = height = 2

        # ARGB4444: alpha=15, red=15, g/b=0 => 0xFF00 in LE
        raw_4444 = bytes([0x00, 0xFF] * (width * height))
        header_4444 = self._write_standard_dds_header(
            width,
            height,
            mip_count=1,
            fourcc=None,
            bitcount=16,
            masks=(0x00000F00, 0x000000F0, 0x0000000F, 0x0000F000),
            ddpf_flags=self.DDPF_RGB | self.DDPF_ALPHAPIXELS,
        )
        tpc_4444 = read_tpc(bytes(header_4444 + raw_4444))
        rgba = tpc_4444.layers[0].mipmaps[0].data
        self.assertEqual(tpc_4444.format(), TPCTextureFormat.RGBA)
        self.assertEqual(rgba[:4], b"\xff\x00\x00\xff")

        # A1R5G5B5: alpha set, red max => 0xFC00 LE
        raw_1555 = bytes([0x00, 0xFC] * (width * height))
        header_1555 = self._write_standard_dds_header(
            width,
            height,
            mip_count=1,
            fourcc=None,
            bitcount=16,
            masks=(0x00007C00, 0x000003E0, 0x0000001F, 0x00008000),
            ddpf_flags=self.DDPF_RGB | self.DDPF_ALPHAPIXELS,
        )
        tpc_1555 = read_tpc(bytes(header_1555 + raw_1555))
        rgba_1555 = tpc_1555.layers[0].mipmaps[0].data
        self.assertEqual(rgba_1555[:4], b"\xff\x00\x00\xff")

        # R5G6B5: all max => 0xFFFF LE
        raw_565 = bytes([0xFF, 0xFF] * (width * height))
        header_565 = self._write_standard_dds_header(
            width,
            height,
            mip_count=1,
            fourcc=None,
            bitcount=16,
            masks=(0x0000F800, 0x000007E0, 0x0000001F, 0),
            ddpf_flags=self.DDPF_RGB,
        )
        tpc_565 = read_tpc(bytes(header_565 + raw_565))
        rgb_565 = tpc_565.layers[0].mipmaps[0].data
        self.assertEqual(rgb_565[:3], b"\xff\xff\xff")

    def test_cubemap_faces_detection(self):
        width = height = 4
        face_count = 6
        dxt1_face = bytes([0x11] * 8)  # 4x4 DXT1 block
        caps2 = 0x00000200 | 0x0000FC00  # cubemap | all faces
        header = self._write_standard_dds_header(
            width,
            height,
            mip_count=1,
            fourcc=b"DXT1",
            bitcount=0,
            masks=(0, 0, 0, 0),
            ddpf_flags=self.DDPF_FOURCC,
            caps2=caps2,
        )
        payload = dxt1_face * face_count
        tpc = read_tpc(bytes(header + payload))
        self.assertTrue(tpc.is_cube_map)
        self.assertEqual(len(tpc.layers), face_count)
        for layer in tpc.layers:
            self.assertEqual(layer.mipmaps[0].width, width)
            self.assertEqual(layer.mipmaps[0].height, height)

    def test_detect_tpc_by_extension(self):
        self.assertEqual(ResourceType.DDS, detect_tpc("texture.dds"))

    def test_bioware_invalid_data_size_raises(self):
        width = height = 4
        # bpp=3 would expect (width*height)/2 = 8 bytes; provide mismatch to trigger failure
        header = struct.pack("<IIIII", width, height, 3, 1234, 0)
        with self.assertRaises(ValueError):
            read_tpc(header + b"\x00" * 4)

    def test_writer_converts_rgba_to_bgra_for_dds(self):
        tpc = TPC()
        rgba_pixel = bytearray([1, 2, 3, 4])
        mip = TPCMipmap(1, 1, TPCTextureFormat.RGBA, rgba_pixel)
        layer = TPCLayer([mip])
        tpc.layers = [layer]
        tpc._format = TPCTextureFormat.RGBA  # noqa: SLF001

        dds_bytes = bytes_tpc(tpc, ResourceType.DDS)
        parsed = read_tpc(dds_bytes)
        self.assertEqual(TPCTextureFormat.BGRA, parsed.format())
        self.assertEqual(parsed.layers[0].mipmaps[0].data, bytearray([3, 2, 1, 4]))


if __name__ == "__main__":
    unittest.main()

