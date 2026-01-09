"""Texture loading utilities for Panda3D.

This module provides TPC texture loading functionality for the Panda3D engine.

References:
----------
        Based on swkotor.exe TPC structure:
        - CResTPC::CResTPC @ 0x00712ea0 - TPC resource constructor
        - GetTPCAttrib @ 0x00712ef0 - Gets TPC texture attributes
        - TPC texture loading and format conversion functions
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        
        Libraries/PyKotor/src/pykotor/resource/formats/tpc - TPC format


"""

from __future__ import annotations

from typing import TYPE_CHECKING

from panda3d.core import Texture  # pyright: ignore[reportMissingImports]

from pykotor.resource.formats.tpc import TPCTextureFormat  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.tpc import TPC  # pyright: ignore[reportMissingImports]


def load_tpc(tpc: TPC) -> Texture:
    """Load a KotOR TPC file into a Panda3D Texture.
    
    Args:
    ----
        tpc: TPC resource object
    
    Returns:
    -------
        Panda3D Texture object
    
    References:
    ----------
        Based on swkotor.exe TPC structure:
        - CResTPC::CResTPC @ 0x00712ea0 - TPC resource constructor
        - GetTPCAttrib @ 0x00712ef0 - Gets TPC texture attributes
        - TPC texture loading and format conversion functions
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        
        Libraries/PyKotor/src/pykotor/resource/formats/tpc - TPC format

    """
    mipmap = tpc.get(0, 0)
    tpc_format = tpc.format()

    # Create texture
    texture = Texture()

    # Convert compressed formats to uncompressed
    if tpc_format in {TPCTextureFormat.DXT1, TPCTextureFormat.DXT3, TPCTextureFormat.DXT5}:
        target_format = TPCTextureFormat.RGB if tpc_format == TPCTextureFormat.DXT1 else TPCTextureFormat.RGBA
        tpc.convert(target_format)
        mipmap = tpc.get(0, 0)
        tpc_format = target_format

    # Setup texture based on format and ensure data size matches expected size
    if tpc_format == TPCTextureFormat.RGB:
        expected_size = mipmap.width * mipmap.height * 3
        if len(mipmap.data) != expected_size:
            raise ValueError(f"Invalid RGB image data size. Expected {expected_size}, got {len(mipmap.data)}")
        texture.setup2dTexture(mipmap.width, mipmap.height, Texture.T_unsigned_byte, Texture.F_rgb)
        texture.setRamImage(mipmap.data)
    elif tpc_format == TPCTextureFormat.RGBA:
        expected_size = mipmap.width * mipmap.height * 4
        if len(mipmap.data) != expected_size:
            raise ValueError(f"Invalid RGBA image data size. Expected {expected_size}, got {len(mipmap.data)}")
        texture.setup2dTexture(mipmap.width, mipmap.height, Texture.T_unsigned_byte, Texture.F_rgba)
        texture.setRamImage(mipmap.data)
    elif tpc_format == TPCTextureFormat.BGR:
        expected_size = mipmap.width * mipmap.height * 3
        if len(mipmap.data) != expected_size:
            raise ValueError(f"Invalid BGR image data size. Expected {expected_size}, got {len(mipmap.data)}")
        texture.setup2dTexture(mipmap.width, mipmap.height, Texture.T_unsigned_byte, Texture.F_rgb)
        # Convert BGR to RGB
        converted = bytearray()
        for i in range(0, len(mipmap.data), 3):
            pixel = mipmap.data[i : i + 3]
            converted.extend(reversed(pixel))
        texture.setRamImage(bytes(converted))
    elif tpc_format == TPCTextureFormat.BGRA:
        expected_size = mipmap.width * mipmap.height * 4
        if len(mipmap.data) != expected_size:
            raise ValueError(f"Invalid BGRA image data size. Expected {expected_size}, got {len(mipmap.data)}")
        texture.setup2dTexture(mipmap.width, mipmap.height, Texture.T_unsigned_byte, Texture.F_rgba)
        # Convert BGRA to RGBA
        converted = bytearray()
        for i in range(0, len(mipmap.data), 4):
            pixel = mipmap.data[i : i + 4]
            converted.extend(reversed(pixel[:3]))  # Reverse BGR
            converted.append(pixel[3])  # Keep alpha
        texture.setRamImage(bytes(converted))
    elif tpc_format == TPCTextureFormat.Greyscale:
        expected_size = mipmap.width * mipmap.height
        if len(mipmap.data) != expected_size:
            raise ValueError(f"Invalid Greyscale image data size. Expected {expected_size}, got {len(mipmap.data)}")
        texture.setup2dTexture(mipmap.width, mipmap.height, Texture.T_unsigned_byte, Texture.F_luminance)
        texture.setRamImage(mipmap.data)
    else:
        # Default to RGBA
        texture.setup2dTexture(mipmap.width, mipmap.height, Texture.T_unsigned_byte, Texture.F_rgba)
        texture.setRamImage(mipmap.data)

    # Configure texture settings
    texture.setMagfilter(Texture.FT_linear)
    texture.setMinfilter(Texture.FT_linear_mipmap_linear)
    texture.setAnisotropicDegree(16)
    texture.setWrapU(Texture.WM_clamp)
    texture.setWrapV(Texture.WM_clamp)

    return texture

