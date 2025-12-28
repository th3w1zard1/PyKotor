"""Shared texture preview/thumbnail helpers.

This module centralizes the logic for producing a displayable preview from a KOTOR
resource. The goal is to ensure *all* UI locations (Texture tab, background loader,
fallback thread/process pools, editors) use the same decode/conversion rules.

In particular:
- DXT-compressed TPC mipmaps are converted to RGB/RGBA before creating any QImage.
- BGRA/BGR/Greyscale mipmaps are converted to Qt-friendly formats.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from pykotor.extract.file import FileResource
from pykotor.resource.formats.tpc import read_tpc
from pykotor.resource.formats.tpc.tpc_data import TPCMipmap, TPCTextureFormat
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from qtpy.QtGui import QImage


def load_preview_mipmap_from_bytes(restype: ResourceType, data: bytes, target_size: int) -> TPCMipmap:
    """Load a displayable preview mipmap from raw bytes + declared restype."""
    if restype is ResourceType.TPC:
        return load_tpc_preview_mipmap(data, target_size)

    if restype is ResourceType.TGA:
        try:
            return load_tpc_preview_mipmap(data, target_size)
        except Exception:
            return load_image_preview_mipmap(data, target_size=target_size)

    return load_image_preview_mipmap(data, target_size=target_size)


def normalize_mipmap_for_qt(mipmap: TPCMipmap) -> TPCMipmap:
    """Return a copy of *mipmap* converted to a Qt-displayable pixel format.

    `TPCMipmap.to_qimage()` does not support DXT formats and will raise.
    This mirrors the conversion logic used by `TPCEditor`.
    """
    mm = mipmap.copy()
    fmt = mm.tpc_format
    if fmt == TPCTextureFormat.DXT1:
        mm.convert(TPCTextureFormat.RGB)
    elif fmt in (TPCTextureFormat.DXT3, TPCTextureFormat.DXT5):
        mm.convert(TPCTextureFormat.RGBA)
    elif fmt == TPCTextureFormat.BGRA:
        mm.convert(TPCTextureFormat.RGBA)
    elif fmt == TPCTextureFormat.BGR:
        mm.convert(TPCTextureFormat.RGB)
    elif fmt == TPCTextureFormat.Greyscale:
        # The rest of the UI expects an RGB/RGBA preview.
        mm.convert(TPCTextureFormat.RGBA)
    return mm


def choose_best_mipmap(mipmaps: list[TPCMipmap], target_size: int) -> TPCMipmap:
    """Choose a mipmap close to `target_size` (preferring <= target when possible)."""
    if not mipmaps:
        raise ValueError("TPC has no mipmaps")

    # Prefer the largest mipmap that is still <= target_size in both dimensions.
    under = [m for m in mipmaps if m.width <= target_size and m.height <= target_size]
    if under:
        # "Largest under" gives the most detail while respecting the target.
        return max(under, key=lambda m: (m.width, m.height))

    # Otherwise fall back to the smallest mipmap (most likely the last entry).
    return min(mipmaps, key=lambda m: (m.width, m.height))


def load_tpc_preview_mipmap(tpc_bytes: bytes, target_size: int) -> TPCMipmap:
    """Load a displayable preview mipmap from raw TPC bytes."""
    tpc = read_tpc(tpc_bytes)
    # IMPORTANT (performance): do NOT call tpc.decode()/tpc.convert() here.
    # Those convert *every* mipmap in the texture, which is far too slow for thumbnails.
    # We only normalize the single chosen mipmap.
    best = choose_best_mipmap(tpc.layers[0].mipmaps, target_size)
    return normalize_mipmap_for_qt(best)


def load_image_preview_mipmap(
    data: bytes,
    *,
    target_size: int,
) -> TPCMipmap:
    """Load a displayable preview mipmap from generic image bytes (PIL first, Qt fallback)."""
    # Prefer PIL (works headlessly and is fast enough for thumbnails).
    try:
        from PIL import Image

        with Image.open(BytesIO(data)) as img:
            rgba = img.convert("RGBA")
        rgba = rgba.resize((target_size, target_size), Image.Resampling.BICUBIC)
        return TPCMipmap(
            width=rgba.width,
            height=rgba.height,
            tpc_format=TPCTextureFormat.RGBA,
            data=bytearray(rgba.tobytes()),
        )
    except Exception:  # noqa: BLE001
        return qimage_to_preview_mipmap(_qimage_from_bytes(data), target_size=target_size)


def load_resource_preview_mipmap(resource: FileResource, target_size: int) -> TPCMipmap:
    """Load a displayable preview mipmap for a `FileResource`."""
    if resource.restype() is ResourceType.TPC:
        return load_tpc_preview_mipmap(resource.data(), target_size)

    # Try parsing as TPC container if possible (some inputs route through read_tpc).
    if resource.restype() is ResourceType.TGA:
        try:
            return load_tpc_preview_mipmap(resource.data(), target_size)
        except Exception:
            return load_image_preview_mipmap(resource.data(), target_size=target_size)

    return load_image_preview_mipmap(resource.data(), target_size=target_size)


def qimage_to_preview_mipmap(qimg: "QImage", *, target_size: int) -> TPCMipmap:
    """Convert a QImage to a `TPCMipmap` suitable for thumbnails."""
    from qtpy.QtCore import Qt
    from qtpy.QtGui import QImage

    if qimg.format() == QImage.Format.Format_RGB888:
        tex_fmt = TPCTextureFormat.RGB
    else:
        tex_fmt = TPCTextureFormat.RGBA
        if qimg.format() != QImage.Format.Format_RGBA8888:
            qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888, Qt.ImageConversionFlag.AutoColor)

    # Scale if needed.
    if (target_size < qimg.width() and target_size < qimg.height()) or (target_size > qimg.width() and target_size > qimg.height()):
        qimg = qimg.scaled(target_size, target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    const_bits = qimg.constBits()
    if const_bits is None:
        raise ValueError("QImage.constBits() returned None")

    bpp = 3 if tex_fmt == TPCTextureFormat.RGB else 4
    data_len = qimg.width() * qimg.height() * bpp
    return TPCMipmap(width=qimg.width(), height=qimg.height(), tpc_format=tex_fmt, data=bytearray(const_bits.asarray(data_len)))


def _qimage_from_bytes(data: bytes) -> "QImage":
    """Load a QImage from bytes."""
    from qtpy.QtGui import QImage

    qimg = QImage()
    if not qimg.loadFromData(data):
        raise ValueError("Failed to load image data into QImage")
    return qimg


