"""Tests for indoor map builder CLI commands."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

absolute_file_path = Path(__file__).absolute()
KOTORCLI_PATH = absolute_file_path.parents[1].joinpath("src")
PYKOTOR_PATH = absolute_file_path.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = absolute_file_path.parents[3].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: Path) -> None:
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


add_sys_path(KOTORCLI_PATH)
add_sys_path(PYKOTOR_PATH)
add_sys_path(UTILITY_PATH)

from pykotor.common.misc import Game
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
from pykotor.resource.type import ResourceType

from kotorcli.commands.indoor_builder import (  # pyright: ignore[reportMissingImports]
    cmd_indoor_build,
    cmd_indoor_extract,
)
from kotorcli.indoor_builder import parse_game_argument  # pyright: ignore[reportMissingImports]


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
        args.output = "/tmp/test.indoor"
        args.installation = "/tmp/install"
        args.kits = "/tmp/kits"
        args.game = None
        args.log_level = None

        logger = MagicMock()

        result = cmd_indoor_extract(args, logger)
        assert result == 1
        logger.error.assert_called()

    def test_extract_embedded_indoormap_txt_from_mod(self):
        """Extract should succeed when `indoormap.txt` is embedded in the .mod."""
        with tempfile.TemporaryDirectory() as tmpdir:
            install_dir = Path(tmpdir) / "install"
            install_dir.mkdir()
            (install_dir / "swkotor.exe").touch()  # helps resemble K1 install, though we pass --game

            modules_dir = install_dir / "modules"
            modules_dir.mkdir()

            kits_dir = Path(tmpdir) / "kits"
            kits_dir.mkdir()

            output_file = Path(tmpdir) / "output.indoor"

            # Create a minimal .mod with embedded indoormap.txt
            mod_path = modules_dir / "test01.mod"
            erf = ERF(ERFType.MOD)
            payload = b'{"module_id":"test01","name":{"stringref":-1},"lighting":[0.5,0.5,0.5],"skybox":"","warp":"test01","rooms":[]}'
            erf.set_data("indoormap", ResourceType.TXT, payload)
            write_erf(erf, mod_path)

            args: Any = MagicMock()
            args.module = "test01"
            args.output = str(output_file)
            args.installation = str(install_dir)
            args.kits = str(kits_dir)
            args.game = "k1"
            args.log_level = None

            logger = MagicMock()

            result = cmd_indoor_extract(args, logger)
            assert result == 0
            assert output_file.exists()
            assert output_file.read_bytes() == payload
