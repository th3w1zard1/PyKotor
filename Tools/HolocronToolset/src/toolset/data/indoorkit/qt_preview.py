from __future__ import annotations

"""Qt-only preview helpers for indoor kits.

`pykotor.common.*` holds the headless data model. Toolset needs QImage previews for UI,
so we attach them dynamically on KitComponents via this module.
"""

from typing import TYPE_CHECKING

from qtpy.QtGui import QColor, QImage, QPainter, QPainterPath

from utility.common.geometry import SurfaceMaterial, Vector3

if TYPE_CHECKING:
    from pykotor.common.indoorkit import KitComponent
    from pykotor.resource.formats.bwm import BWM


def ensure_component_image(component: KitComponent) -> QImage:
    """Ensure a `KitComponent` has a Qt `image` attribute and return it."""
    img = component.image
    if img is not None:
        if isinstance(img, QImage):
            return img
        raise TypeError(f"KitComponent.image must be a QImage, got {type(img)!r}")

    image = _create_preview_image_from_bwm(component.bwm)
    component.image = image
    return image


def _get_default_material_color(material: SurfaceMaterial) -> QColor:
    # Default material colors (matching typical walkmesh painter settings)
    material_colors: dict[SurfaceMaterial, QColor] = {
        SurfaceMaterial.UNDEFINED: QColor(128, 128, 128),  # Gray
        SurfaceMaterial.OBSCURING: QColor(64, 64, 64),  # Dark gray
        SurfaceMaterial.DIRT: QColor(139, 90, 43),  # Brown
        SurfaceMaterial.GRASS: QColor(34, 139, 34),  # Green
        SurfaceMaterial.STONE: QColor(192, 192, 192),  # Light gray
        SurfaceMaterial.WOOD: QColor(101, 67, 33),  # Brown
        SurfaceMaterial.WATER: QColor(0, 100, 200),  # Blue
        SurfaceMaterial.NON_WALK: QColor(64, 64, 64),  # Dark gray
        SurfaceMaterial.TRANSPARENT: QColor(128, 128, 128, 128),  # Semi-transparent gray
        SurfaceMaterial.CARPET: QColor(139, 69, 19),  # Saddle brown
        SurfaceMaterial.METAL: QColor(192, 192, 192),  # Silver
        SurfaceMaterial.PUDDLES: QColor(0, 150, 255),  # Light blue
        SurfaceMaterial.SWAMP: QColor(85, 107, 47),  # Dark olive green
        SurfaceMaterial.MUD: QColor(101, 67, 33),  # Brown
        SurfaceMaterial.LEAVES: QColor(34, 139, 34),  # Green
        SurfaceMaterial.LAVA: QColor(255, 69, 0),  # Red-orange
        SurfaceMaterial.BOTTOMLESS_PIT: QColor(25, 25, 25),  # Very dark gray
        SurfaceMaterial.DEEP_WATER: QColor(0, 0, 139),  # Dark blue
        SurfaceMaterial.DOOR: QColor(184, 134, 11),  # Dark goldenrod
        SurfaceMaterial.NON_WALK_GRASS: QColor(85, 107, 47),  # Dark olive green
        SurfaceMaterial.TRIGGER: QColor(255, 215, 0),  # Gold
    }
    return material_colors.get(material, QColor(128, 128, 128))


def _create_preview_image_from_bwm(bwm: BWM) -> QImage:
    """Create a preview image from a walkmesh showing fully rendered materials.

    Matches the historical Toolset/kit rendering conventions:
    - 10 px / unit
    - minimum 256x256
    - RGB888
    - Y-flip during draw + `mirrored()` final pass
    """
    vertices: list[Vector3] = list(bwm.vertices())
    if not vertices:
        image = QImage(256, 256, QImage.Format.Format_RGB888)
        image.fill(QColor(0, 0, 0))
        return image.mirrored()

    min_x = min(v.x for v in vertices)
    min_y = min(v.y for v in vertices)
    max_x = max(v.x for v in vertices)
    max_y = max(v.y for v in vertices)

    padding = 5.0
    min_x -= padding
    min_y -= padding
    max_x += padding
    max_y += padding

    PIXELS_PER_UNIT = 10
    width = max(int((max_x - min_x) * PIXELS_PER_UNIT), 256)
    height = max(int((max_y - min_y) * PIXELS_PER_UNIT), 256)

    image = QImage(width, height, QImage.Format.Format_RGB888)
    image.fill(QColor(0, 0, 0))

    def world_to_image(v: Vector3) -> tuple[float, float]:
        x = (v.x - min_x) * PIXELS_PER_UNIT
        y = height - (v.y - min_y) * PIXELS_PER_UNIT  # Flip Y
        return x, y

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    for face in bwm.faces:
        color = _get_default_material_color(face.material)
        painter.setBrush(color)
        painter.setPen(color)

        path = QPainterPath()
        x1, y1 = world_to_image(face.v1)
        x2, y2 = world_to_image(face.v2)
        x3, y3 = world_to_image(face.v3)

        path.moveTo(x1, y1)
        path.lineTo(x2, y2)
        path.lineTo(x3, y3)
        path.closeSubpath()
        painter.drawPath(path)

    painter.end()
    return image.mirrored()


