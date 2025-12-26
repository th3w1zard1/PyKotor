"""Qt-only helpers for indoor maps (Toolset).

Repo rule:
- All *core* indoor/map/kit/modulekit logic lives in `Libraries/PyKotor/src/pykotor/...`
- Toolset keeps only Qt rendering / UI helpers.

This module exists as a compatibility shim for Toolset code that historically imported
`toolset.data.indoormap.*`.
"""
from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, NamedTuple

from qtpy import QtCore  # pyright: ignore[reportMissingImports]
from qtpy.QtGui import QColor, QImage, QPainter, QPixmap, QTransform  # pyright: ignore[reportMissingImports]

from pykotor.common.indoormap import (  # re-exported for Toolset imports
    DoorInsertion,
    IndoorMap,
    IndoorMapRoom,
    MissingRoomInfo,
)
from toolset.data.indoorkit.qt_preview import ensure_component_image
from utility.common.geometry import Vector2, Vector3

if TYPE_CHECKING:
    from pykotor.resource.formats.bwm import BWM


class MinimapData(NamedTuple):
    """Qt minimap render output."""

    image: QImage
    imagePointMin: Vector2
    imagePointMax: Vector2
    worldPointMin: Vector2
    worldPointMax: Vector2


def generate_mipmap(indoor_map: IndoorMap) -> MinimapData:
    """Render a minimap QImage from an `IndoorMap` for the Toolset UI.

    The resulting image is 512x256 (like the game UI), with bounds computed from
    the transformed walkmeshes.
    """
    # Compute bounds from transformed walkmeshes (same shape as old toolset impl).
    walkmeshes: list[BWM] = []
    for room in indoor_map.rooms:
        bwm = deepcopy(room.base_walkmesh())
        bwm.flip(room.flip_x, room.flip_y)
        bwm.rotate(room.rotation)
        bwm.translate(room.position.x, room.position.y, room.position.z)
        walkmeshes.append(bwm)

    bbmin = Vector3(1000000, 1000000, 1000000)
    bbmax = Vector3(-1000000, -1000000, -1000000)
    for bwm in walkmeshes:
        for v in bwm.vertices():
            bbmin.x = min(bbmin.x, v.x)
            bbmin.y = min(bbmin.y, v.y)
            bbmax.x = max(bbmax.x, v.x)
            bbmax.y = max(bbmax.y, v.y)

    # padding in world units
    bbmin.x -= 5
    bbmin.y -= 5
    bbmax.x += 5
    bbmax.y += 5

    px_per_unit = 10.0
    width_px = max(int((bbmax.x - bbmin.x) * px_per_unit), 1)
    height_px = max(int((bbmax.y - bbmin.y) * px_per_unit), 1)

    pixmap = QPixmap(width_px, height_px)
    pixmap.fill(QColor(0))

    painter = QPainter(pixmap)
    for room in indoor_map.rooms:
        image = ensure_component_image(room.component)

        painter.save()
        painter.translate(
            room.position.x * px_per_unit - bbmin.x * px_per_unit,
            room.position.y * px_per_unit - bbmin.y * px_per_unit,
        )
        painter.rotate(room.rotation)
        painter.scale(-1 if room.flip_x else 1, -1 if room.flip_y else 1)
        painter.translate(-image.width() / 2, -image.height() / 2)
        painter.drawImage(0, 0, image)
        painter.restore()
    painter.end()

    # Scale to minimap aspect (512x256) with same behavior as legacy toolset.
    scaled = pixmap.scaled(435, 256, QtCore.Qt.KeepAspectRatio)  # type: ignore[attr-defined]
    canvas = QPixmap(512, 256)
    canvas.fill(QColor(0))

    painter2 = QPainter(canvas)
    painter2.drawPixmap(0, int(128 - scaled.height() / 2), scaled)
    painter2.end()

    out_image = canvas.transformed(QTransform().scale(1, -1)).toImage()
    out_image.convertTo(QImage.Format.Format_RGB888)

    image_point_min = Vector2(0 / 435, (128 - scaled.height() / 2) / 256)
    image_point_max = Vector2((image_point_min.x + scaled.width()) / 435, (image_point_min.y + scaled.height()) / 256)
    world_point_min = Vector2(bbmax.x, bbmin.y)
    world_point_max = Vector2(bbmin.x, bbmax.y)

    return MinimapData(out_image, image_point_min, image_point_max, world_point_min, world_point_max)


__all__ = [
    "DoorInsertion",
    "IndoorMap",
    "IndoorMapRoom",
    "MissingRoomInfo",
    "MinimapData",
    "generate_mipmap",
]
