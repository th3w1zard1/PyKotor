from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from OpenGL.GL import GL_NO_ERROR, glGenTextures, glGetError, glTexImage2D
from OpenGL.GL.framebufferobjects import glGenerateMipmap
from OpenGL.GLU import gluErrorString
from OpenGL.raw.GL.EXT.texture_compression_s3tc import (
    GL_COMPRESSED_RGBA_S3TC_DXT3_EXT,
    GL_COMPRESSED_RGBA_S3TC_DXT5_EXT,
    GL_COMPRESSED_RGB_S3TC_DXT1_EXT,
)
from OpenGL.raw.GL.VERSION.GL_1_0 import (
    GL_LINEAR,
    GL_NEAREST_MIPMAP_LINEAR,
    GL_REPEAT,
    GL_RGB,
    GL_RGBA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNSIGNED_BYTE,
    glTexParameteri,
)
from OpenGL.raw.GL.VERSION.GL_1_1 import glBindTexture
from OpenGL.raw.GL.VERSION.GL_1_3 import glCompressedTexImage2D

from pykotor.resource.formats.tpc import TPCTextureFormat
from pykotor.resource.formats.tpc.convert.dxt.decompress_dxt import (
    dxt1_to_rgb,
    dxt3_to_rgba,
    dxt5_to_rgba,
)

if TYPE_CHECKING:
    from moderngl import Context as ModernContext, Texture as ModernTexture
    from pykotor.resource.formats.tpc import TPC, TPCMipmap
else:  # pragma: no cover - optional dependency
    ModernContext = Any  # type: ignore[assignment]
    ModernTexture = Any  # type: ignore[assignment]


class Texture:
    def __init__(
        self,
        tex_id: int,
        width: int | None = None,
        height: int | None = None,
        rgba_data: bytes | None = None,
    ):
        self._id: int = tex_id
        self._width: int | None = width
        self._height: int | None = height
        self._rgba_cache: bytes | None = rgba_data
        self._modern_texture: ModernTexture | None = None  # type: ignore[name-defined]

    @classmethod
    def from_tpc(
        cls,
        tpc: TPC,
    ) -> Texture:
        mm: TPCMipmap = tpc.get(0, 0)
        image_size: int = len(mm.data)

        gl_id: int = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, gl_id)

        rgba_cache: bytes | None = None

        if mm.tpc_format == TPCTextureFormat.DXT1:
            glCompressedTexImage2D(GL_TEXTURE_2D, 0, GL_COMPRESSED_RGB_S3TC_DXT1_EXT, mm.width, mm.height, 0, image_size, mm.data)
            rgba_cache = _rgb_to_rgba_bytes(dxt1_to_rgb(mm.data, mm.width, mm.height), mm.width, mm.height)
        elif mm.tpc_format == TPCTextureFormat.DXT3:
            glCompressedTexImage2D(GL_TEXTURE_2D, 0, GL_COMPRESSED_RGBA_S3TC_DXT3_EXT, mm.width, mm.height, 0, image_size, mm.data)
            rgba_cache = bytes(dxt3_to_rgba(mm.data, mm.width, mm.height))
        elif mm.tpc_format == TPCTextureFormat.DXT5:
            glCompressedTexImage2D(GL_TEXTURE_2D, 0, GL_COMPRESSED_RGBA_S3TC_DXT5_EXT, mm.width, mm.height, 0, image_size, mm.data)
            rgba_cache = bytes(dxt5_to_rgba(mm.data, mm.width, mm.height))
        elif mm.tpc_format == TPCTextureFormat.RGB:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, mm.width, mm.height, 0, GL_RGB, GL_UNSIGNED_BYTE, mm.data)
            rgba_cache = _rgb_to_rgba_bytes(mm.data, mm.width, mm.height)
        elif mm.tpc_format == TPCTextureFormat.RGBA:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, mm.width, mm.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, mm.data)
            rgba_cache = bytes(mm.data)
        else:
            raise ValueError(f"Unsupported texture format: {mm.tpc_format!r}")

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)

        return Texture(gl_id, mm.width, mm.height, rgba_cache)

    @classmethod
    def from_rgba(
        cls,
        width: int,
        height: int,
        rgba_data: bytes,
    ) -> Texture:
        """Create texture from RGBA pixel data.
        
        Args:
        ----
            width: Texture width in pixels
            height: Texture height in pixels
            rgba_data: Raw RGBA pixel data (bytes)
        
        Returns:
        -------
            Texture: OpenGL texture object
        """
        gl_id: int = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, gl_id)
        
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, rgba_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)
        
        return Texture(gl_id, width, height, bytes(rgba_data))

    @classmethod
    def from_color(
        cls,
        r: int = 0,
        g: int = 0,
        b: int = 0,
    ) -> Texture:
        gl_id: int = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, gl_id)

        # Create pixel data using numpy for better performance and alignment
        pixels: np.ndarray = np.full((64, 64, 3), [r, g, b], dtype=np.uint8)

        # Immediate error checking before and after glTexImage2D
        errno: int | None = glGetError()
        if errno is not None and errno != GL_NO_ERROR:
            print(f"Error before glTexImage2D: {gluErrorString(errno)}")

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 64, 64, 0, GL_RGB, GL_UNSIGNED_BYTE, pixels)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        rgba = bytes(pixels.tobytes())
        return Texture(gl_id, 64, 64, rgba)

    def use(self):
        glBindTexture(GL_TEXTURE_2D, self._id)

    def ensure_modern(
        self,
        ctx: ModernContext,
    ):
        if self._modern_texture is not None:
            return self._modern_texture
        if self._rgba_cache is None or self._width is None or self._height is None:
            raise RuntimeError("RGBA texture data not available for moderngl upload")
        texture = ctx.texture((self._width, self._height), 4, data=self._rgba_cache)
        texture.repeat_x = True
        texture.repeat_y = True
        texture.build_mipmaps()
        self._modern_texture = texture
        return texture


def _rgb_to_rgba_bytes(
    data: bytes | bytearray,
    width: int,
    height: int,
) -> bytes:
    pixel_count = width * height
    arr = np.frombuffer(data, dtype=np.uint8).reshape(pixel_count, 3)
    alpha = np.full((pixel_count, 1), 255, dtype=np.uint8)
    return np.hstack([arr, alpha]).astype(np.uint8).tobytes()


