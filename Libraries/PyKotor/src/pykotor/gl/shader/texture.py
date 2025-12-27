from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pykotor.gl.compat import (
    MissingPyOpenGLError,
    has_pyopengl,
    missing_constant,
    missing_gl_func,
)

HAS_PYOPENGL = has_pyopengl()

if HAS_PYOPENGL:
    from OpenGL.GL import GL_NO_ERROR, glGenTextures, glGetError, glTexImage2D  # pyright: ignore[reportMissingImports]
    from OpenGL.GL.framebufferobjects import glGenerateMipmap  # pyright: ignore[reportMissingImports]
    from OpenGL.GLU import gluErrorString  # pyright: ignore[reportMissingImports]
    from OpenGL.raw.GL.EXT.texture_compression_s3tc import (  # pyright: ignore[reportMissingImports]
        GL_COMPRESSED_RGBA_S3TC_DXT3_EXT,
        GL_COMPRESSED_RGBA_S3TC_DXT5_EXT,
        GL_COMPRESSED_RGB_S3TC_DXT1_EXT,
    )
    from OpenGL.raw.GL.VERSION.GL_1_0 import (  # pyright: ignore[reportMissingImports]
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
    from OpenGL.raw.GL.VERSION.GL_1_1 import glBindTexture  # pyright: ignore[reportMissingImports]
    from OpenGL.raw.GL.VERSION.GL_1_3 import glCompressedTexImage2D  # pyright: ignore[reportMissingImports]
else:
    glGenTextures = missing_gl_func("glGenTextures")
    glGetError = missing_gl_func("glGetError")
    glTexImage2D = missing_gl_func("glTexImage2D")
    glGenerateMipmap = missing_gl_func("glGenerateMipmap")
    gluErrorString = missing_gl_func("gluErrorString")
    glBindTexture = missing_gl_func("glBindTexture")
    glCompressedTexImage2D = missing_gl_func("glCompressedTexImage2D")
    glTexParameteri = missing_gl_func("glTexParameteri")
    GL_NO_ERROR = missing_constant("GL_NO_ERROR")
    GL_COMPRESSED_RGBA_S3TC_DXT3_EXT = missing_constant("GL_COMPRESSED_RGBA_S3TC_DXT3_EXT")
    GL_COMPRESSED_RGBA_S3TC_DXT5_EXT = missing_constant("GL_COMPRESSED_RGBA_S3TC_DXT5_EXT")
    GL_COMPRESSED_RGB_S3TC_DXT1_EXT = missing_constant("GL_COMPRESSED_RGB_S3TC_DXT1_EXT")
    GL_LINEAR = missing_constant("GL_LINEAR")
    GL_NEAREST_MIPMAP_LINEAR = missing_constant("GL_NEAREST_MIPMAP_LINEAR")
    GL_REPEAT = missing_constant("GL_REPEAT")
    GL_RGB = missing_constant("GL_RGB")
    GL_RGBA = missing_constant("GL_RGBA")
    GL_TEXTURE_2D = missing_constant("GL_TEXTURE_2D")
    GL_TEXTURE_MAG_FILTER = missing_constant("GL_TEXTURE_MAG_FILTER")
    GL_TEXTURE_MIN_FILTER = missing_constant("GL_TEXTURE_MIN_FILTER")
    GL_TEXTURE_WRAP_S = missing_constant("GL_TEXTURE_WRAP_S")
    GL_TEXTURE_WRAP_T = missing_constant("GL_TEXTURE_WRAP_T")
    GL_UNSIGNED_BYTE = missing_constant("GL_UNSIGNED_BYTE")

from pykotor.resource.formats.tpc import TPCTextureFormat
from pykotor.resource.formats.tpc.convert.dxt.decompress_dxt import (
    dxt1_to_rgb,
    dxt3_to_rgba,
    dxt5_to_rgba,
)

if TYPE_CHECKING:
    from pykotor.resource.formats.tpc import TPC, TPCMipmap


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

    @classmethod
    def from_tpc(
        cls,
        tpc: TPC,
    ) -> Texture:
        mm: TPCMipmap = tpc.get(0, 0)
        image_size: int = len(mm.data)

        rgba_cache: bytes
        if mm.tpc_format == TPCTextureFormat.DXT1:
            rgba_cache = _rgb_to_rgba_bytes(dxt1_to_rgb(mm.data, mm.width, mm.height), mm.width, mm.height)
        elif mm.tpc_format == TPCTextureFormat.DXT3:
            rgba_cache = bytes(dxt3_to_rgba(mm.data, mm.width, mm.height))
        elif mm.tpc_format == TPCTextureFormat.DXT5:
            rgba_cache = bytes(dxt5_to_rgba(mm.data, mm.width, mm.height))
        elif mm.tpc_format == TPCTextureFormat.RGB:
            rgba_cache = _rgb_to_rgba_bytes(mm.data, mm.width, mm.height)
        elif mm.tpc_format == TPCTextureFormat.RGBA:
            rgba_cache = bytes(mm.data)
        else:
            raise ValueError(f"Unsupported texture format: {mm.tpc_format!r}")

        # If PyOpenGL is not available, keep an in-memory texture placeholder.
        if not HAS_PYOPENGL:
            return Texture(0, mm.width, mm.height, rgba_cache)

        gl_id: int = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, gl_id)

        if mm.tpc_format == TPCTextureFormat.DXT1:
            glCompressedTexImage2D(GL_TEXTURE_2D, 0, GL_COMPRESSED_RGB_S3TC_DXT1_EXT, mm.width, mm.height, 0, image_size, mm.data)
        elif mm.tpc_format == TPCTextureFormat.DXT3:
            glCompressedTexImage2D(GL_TEXTURE_2D, 0, GL_COMPRESSED_RGBA_S3TC_DXT3_EXT, mm.width, mm.height, 0, image_size, mm.data)
        elif mm.tpc_format == TPCTextureFormat.DXT5:
            glCompressedTexImage2D(GL_TEXTURE_2D, 0, GL_COMPRESSED_RGBA_S3TC_DXT5_EXT, mm.width, mm.height, 0, image_size, mm.data)
        elif mm.tpc_format == TPCTextureFormat.RGB:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, mm.width, mm.height, 0, GL_RGB, GL_UNSIGNED_BYTE, mm.data)
        elif mm.tpc_format == TPCTextureFormat.RGBA:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, mm.width, mm.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, mm.data)
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
        if not HAS_PYOPENGL:
            return Texture(0, width, height, bytes(rgba_data))

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
        # Create pixel data using numpy for better performance and alignment
        pixels: np.ndarray = np.full((64, 64, 3), [r, g, b], dtype=np.uint8)

        if not HAS_PYOPENGL:
            rgba = _rgb_to_rgba_bytes(pixels.tobytes(), 64, 64)
            return Texture(0, 64, 64, rgba)

        gl_id: int = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, gl_id)

        # Immediate error checking before and after glTexImage2D
        errno: int | None = glGetError()
        if errno is not None and errno != GL_NO_ERROR:
            print(f"Error before glTexImage2D: {gluErrorString(errno)}")

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 64, 64, 0, GL_RGB, GL_UNSIGNED_BYTE, pixels)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # Cache RGBA for downstream consumers (and for consistency with other loaders).
        rgba = _rgb_to_rgba_bytes(pixels.tobytes(), 64, 64)
        return Texture(gl_id, 64, 64, rgba)

    def use(self):
        if not HAS_PYOPENGL:
            raise MissingPyOpenGLError("PyOpenGL is required to bind GL textures.")
        glBindTexture(GL_TEXTURE_2D, self._id)


def _rgb_to_rgba_bytes(
    data: bytes | bytearray,
    width: int,
    height: int,
) -> bytes:
    pixel_count = width * height
    arr = np.frombuffer(data, dtype=np.uint8).reshape(pixel_count, 3)
    alpha = np.full((pixel_count, 1), 255, dtype=np.uint8)
    return np.hstack([arr, alpha]).astype(np.uint8).tobytes()


