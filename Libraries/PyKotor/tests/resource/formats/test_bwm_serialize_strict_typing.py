"""Tests for BWM serialize() method with strict type checking.

Tests verify that enum.value access works correctly without hasattr/getattr.
"""

from __future__ import annotations

import pathlib
import sys

# Setup paths
THIS_FILE = pathlib.Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[5]
PYKOTOR_SRC = REPO_ROOT / "Libraries" / "PyKotor" / "src"
UTILITY_SRC = REPO_ROOT / "Libraries" / "Utility" / "src"

for path in (PYKOTOR_SRC, UTILITY_SRC):
    as_posix = path.as_posix()
    if as_posix not in sys.path:
        sys.path.insert(0, as_posix)


from pykotor.resource.formats.bwm.bwm_data import BWM, BWMFace, BWMType
from utility.common.geometry import SurfaceMaterial, Vector3


class TestBWMSerializeStrictTyping:
    """Test BWM serialize() with strict type checking (no hasattr/getattr)."""

    def test_serialize_walkmesh_type_enum_value(self):
        """Test that walkmesh_type.value is accessed directly without hasattr."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel

        result = bwm.serialize()

        # Should access .value directly - BWMType is IntEnum, always has .value
        assert result["walkmesh_type"] == BWMType.AreaModel.value
        assert isinstance(result["walkmesh_type"], int)
        assert result["walkmesh_type"] == 1

    def test_serialize_walkmesh_type_placeable_enum_value(self):
        """Test that PlaceableOrDoor enum value works correctly."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.PlaceableOrDoor

        result = bwm.serialize()

        assert result["walkmesh_type"] == BWMType.PlaceableOrDoor.value
        assert result["walkmesh_type"] == 0

    def test_serialize_face_material_enum_value(self):
        """Test that face.material.value is accessed directly without hasattr."""
        bwm = BWM()
        face = BWMFace(Vector3(0, 0, 0), Vector3(1, 0, 0), Vector3(0, 1, 0))
        face.material = SurfaceMaterial.GRASS

        bwm.faces.append(face)

        result = bwm.serialize()

        # Should access .value directly - SurfaceMaterial is IntEnum, always has .value
        assert len(result["faces"]) == 1
        face_data = result["faces"][0]
        assert face_data["material"] == SurfaceMaterial.GRASS.value
        assert isinstance(face_data["material"], int)

    def test_serialize_multiple_faces_different_materials(self):
        """Test serializing multiple faces with different materials."""
        bwm = BWM()

        for i, material in enumerate([SurfaceMaterial.GRASS, SurfaceMaterial.STONE, SurfaceMaterial.WOOD]):
            face = BWMFace(Vector3(i, 0, 0), Vector3(i + 1, 0, 0), Vector3(i, 1, 0))
            face.material = material
            bwm.faces.append(face)

        result = bwm.serialize()

        assert len(result["faces"]) == 3
        for i, face_data in enumerate(result["faces"]):
            expected_material = [SurfaceMaterial.GRASS, SurfaceMaterial.STONE, SurfaceMaterial.WOOD][i]
            assert face_data["material"] == expected_material.value
            assert isinstance(face_data["material"], int)

    def test_serialize_complete_bwm_structure(self):
        """Test serializing a complete BWM with all fields."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        bwm.position = Vector3(10, 20, 30)

        face = BWMFace(Vector3(0, 0, 0), Vector3(1, 0, 0), Vector3(0, 1, 0))
        face.material = SurfaceMaterial.METAL
        bwm.faces.append(face)

        result = bwm.serialize()

        # Verify all enum values are accessed directly
        assert result["walkmesh_type"] == BWMType.AreaModel.value
        assert len(result["faces"]) == 1
        assert result["faces"][0]["material"] == SurfaceMaterial.METAL.value
        assert "vertices" in result
