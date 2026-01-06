"""Tests for indoor map builder CLI commands."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

# sys.path modifications removed - pykotor is now a proper package

from pykotor.cli.commands.indoor_builder import (
    cmd_indoor_build,
    cmd_indoor_extract,
)
from pykotor.cli.indoor_builder import parse_game_argument
from pykotor.common.misc import Game
from pykotor.resource.formats.bwm import BWM, BWMFace
from pykotor.tools.indoormap import infer_room_transform_bwm
from utility.common.geometry import SurfaceMaterial, Vector3


class TestParseGameArgument:
    """Test game argument parsing."""

    def test_parse_k1(self):
        """Test parsing K1 game argument."""
        assert parse_game_argument("k1") == Game.K1
        assert parse_game_argument("K1") == Game.K1
        assert parse_game_argument("kotor1") == Game.K1
        assert parse_game_argument("KOTOR 1") == Game.K1

    def test_parse_k2(self):
        """Test parsing K2 game argument."""
        assert parse_game_argument("k2") == Game.K2
        assert parse_game_argument("K2") == Game.K2
        assert parse_game_argument("kotor2") == Game.K2
        assert parse_game_argument("TSL") == Game.K2

    def test_parse_invalid(self):
        """Test parsing invalid game argument."""
        assert parse_game_argument("invalid") is None
        assert parse_game_argument("") is None
        assert parse_game_argument(None) is None


class TestIndoorBuild:
    """Test indoor-build command."""

    def test_build_missing_input(self):
        """Test build command with missing input file."""
        args: Any = MagicMock()
        args.input = None
        args.output = "/tmp/test.mod"
        args.installation = "/tmp/install"
        args.kits = "/tmp/kits"
        args.game = None
        args.module_filename = None
        args.loading_screen = None
        args.log_level = None

        logger = MagicMock()

        result = cmd_indoor_build(args, logger)
        assert result == 1
        logger.error.assert_called()

    def test_build_missing_installation(self):
        """Test build command with missing installation."""
        with tempfile.NamedTemporaryFile(suffix=".indoor", delete=False) as tmp:
            tmp.write(b'{"module_id": "test01", "rooms": []}')
            tmp_path = tmp.name

        try:
            args: Any = MagicMock()
            args.input = tmp_path
            args.output = "/tmp/test.mod"
            args.installation = None
            args.kits = "/tmp/kits"
            args.game = None
            args.module_filename = None
            args.loading_screen = None
            args.log_level = None

            logger = MagicMock()

            result = cmd_indoor_build(args, logger)
            assert result == 1
            logger.error.assert_called()
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class TestIndoorExtract:
    """Test indoor-extract command."""

    def test_extract_missing_module(self):
        """Test extract command with missing module."""
        args: Any = MagicMock()
        args.module = None
        # MagicMock returns a truthy MagicMock for missing attrs; define explicitly.
        args.module_file = None
        args.output = "/tmp/test.indoor"
        args.installation = None
        args.kits = None
        args.implicit_kit = True
        args.game = None
        args.log_level = None

        logger = MagicMock()

        result = cmd_indoor_extract(args, logger)
        assert result == 1
        logger.error.assert_called()


class TestInferRoomTransform:
    """Unit tests for the walkmesh transform inference used by reverse-extraction."""

    def test_infer_transform_roundtrip(self):
        base = BWM()
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(1.0, 0.0, 0.0)
        v3 = Vector3(0.0, 1.0, 0.0)
        face = BWMFace(v1, v2, v3)
        face.material = SurfaceMaterial.GRASS
        base.faces.append(face)

        instance = BWM()
        instance.faces.append(BWMFace(Vector3(0.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)))
        instance.faces[0].material = SurfaceMaterial.GRASS

        # Apply known transform to the instance mesh
        instance.flip(True, False)
        instance.rotate(90.0)
        instance.translate(10.0, -5.0, 2.0)

        inferred = infer_room_transform_bwm(base, instance, max_rms=1e-6)
        assert inferred is not None
        flip_x, flip_y, rot_deg, translation, rms = inferred
        assert rms <= 1e-6

        # Validate the inferred transform reproduces the instance geometry.
        check = BWM()
        check.faces.append(BWMFace(Vector3(0.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)))
        check.faces[0].material = SurfaceMaterial.GRASS
        check.flip(flip_x, flip_y)
        check.rotate(rot_deg)
        check.translate(translation.x, translation.y, translation.z)

        for a, b in zip(check.vertices(), instance.vertices()):
            assert abs(a.x - b.x) < 1e-6
            assert abs(a.y - b.y) < 1e-6
            assert abs(a.z - b.z) < 1e-6
