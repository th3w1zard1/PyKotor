"""Comprehensive roundtrip tests for indoor map builder using ComparableMixin.compare().

These tests verify that:
1. Module -> .indoor -> module -> .indoor roundtrips preserve all data
2. .indoor -> module -> .indoor roundtrips preserve all data
3. All comparisons use ComparableMixin.compare() with udiff format output
4. No tests are skipped
"""

from __future__ import annotations

import difflib
import sys
from io import StringIO
from pathlib import Path
from typing import Any

import pytest

absolute_file_path = Path(__file__).absolute()
KOTORCLI_PATH = absolute_file_path.parents[1].joinpath("src")
PYKOTOR_PATH = absolute_file_path.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = absolute_file_path.parents[3].joinpath("Libraries", "Utility", "src")


def _add_sys_path(p: Path) -> None:
    s = str(p)
    if s not in sys.path:
        sys.path.append(s)


_add_sys_path(KOTORCLI_PATH)
_add_sys_path(PYKOTOR_PATH)
_add_sys_path(UTILITY_PATH)

from argparse import Namespace

from kotorcli.commands.indoor_builder import cmd_indoor_build, cmd_indoor_extract
from pykotor.common.indoormap import IndoorMap
from pykotor.common.modulekit import ModuleKitManager
from pykotor.extract.installation import Installation
from pykotor.tools.path import CaseAwarePath


class _MemLogger:
    """Minimal logger shim for calling CLI command functions directly in tests."""

    def setLevel(self, _level: int) -> None:  # noqa: N802
        return

    def debug(self, *_args: object, **_kwargs: object) -> None:
        return

    def info(self, *_args: object, **_kwargs: object) -> None:
        return

    def warning(self, *_args: object, **_kwargs: object) -> None:
        return

    def error(self, *_args: object, **_kwargs: object) -> None:
        return

    def exception(self, *_args: object, **_kwargs: object) -> None:
        return


def _run_indoor_extract(
    *,
    installation: Installation,
    mk_mgr: ModuleKitManager,
    game_arg: str,
    module_root: str,
    module_file: Path | None,
    output: Path,
) -> int:
    args = Namespace(
        module=module_root,
        module_file=str(module_file) if module_file is not None else None,
        output=str(output),
        installation=str(installation.path()),
        game=game_arg,
        kits=None,
        implicit_kit=True,
        log_level="error",
    )
    args._installation_obj = installation  # type: ignore[attr-defined]
    args._module_kit_manager = mk_mgr  # type: ignore[attr-defined]
    return int(cmd_indoor_extract(args, _MemLogger()))  # type: ignore[arg-type]


def _run_indoor_build(
    *,
    installation: Installation,
    mk_mgr: ModuleKitManager,
    game_arg: str,
    input_indoor: Path,
    output_mod: Path,
    module_filename: str,
) -> int:
    args = Namespace(
        input=str(input_indoor),
        output=str(output_mod),
        installation=str(installation.path()),
        game=game_arg,
        kits=None,
        implicit_kit=True,
        module_filename=module_filename,
        loading_screen=None,
        log_level="error",
    )
    args._installation_obj = installation  # type: ignore[attr-defined]
    args._module_kit_manager = mk_mgr  # type: ignore[attr-defined]
    return int(cmd_indoor_build(args, _MemLogger()))  # type: ignore[arg-type]


def _safe_out_module_id(*, module_root: str, game_key: str, room_count: int) -> str:
    """Pick a module id that will not exceed the 16-char ResRef limit."""
    max_index = max(room_count - 1, 0)
    digits = len(str(max_index))
    max_for_rooms = 16 - (len("_room") + digits)
    max_for_minimap = 16 - len("lbl_map")
    max_module_id_len = min(max_for_rooms, max_for_minimap)

    if max_module_id_len <= 0:
        msg = f"Cannot construct a valid module_id for room_count={room_count} (digits={digits})"
        raise AssertionError(msg)

    base = f"{module_root}{game_key}rt".lower()
    base = "".join(c for c in base if c.isalnum() or c == "_")
    return base[:max_module_id_len]


def _compare_indoor_maps_with_udiff(
    original: IndoorMap,
    roundtripped: IndoorMap,
    original_label: str = "original",
    roundtripped_label: str = "roundtripped",
) -> bool:
    """Compare two IndoorMap objects using ComparableMixin.compare() and output udiff format.

    Returns True if identical, False if different.
    """
    diff_lines: list[str] = []
    log_buffer = StringIO()

    def log_func(msg: str) -> None:
        diff_lines.append(msg)
        log_buffer.write(msg + "\n")

    is_identical = original.compare(roundtripped, log_func=log_func)

    if not is_identical:
        # Generate udiff format output
        original_json = original.write().decode("utf-8")
        roundtripped_json = roundtripped.write().decode("utf-8")

        original_lines = original_json.splitlines(keepends=True)
        roundtripped_lines = roundtripped_json.splitlines(keepends=True)

        udiff = list(
            difflib.unified_diff(
                original_lines,
                roundtripped_lines,
                fromfile=original_label,
                tofile=roundtripped_label,
                lineterm="",
            )
        )

        # Print the udiff
        print("\n" + "=" * 80)
        print("Unified diff (udiff format):")
        print("=" * 80)
        for line in udiff:
            print(line)
        print("=" * 80)

        # Also print the structured comparison output
        print("\nStructured comparison differences:")
        print("-" * 80)
        print(log_buffer.getvalue())
        print("-" * 80)

    return is_identical


@pytest.fixture(autouse=True)
def _require_module_case(module_case: tuple[str, str]) -> None:  # noqa: ARG001
    """Ensure all tests in this module are collected per-installation and per-module."""
    return


@pytest.fixture(scope="module")
def roundtrip_data(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
    module_case: tuple[str, str],
    k1_installation: Installation,
) -> dict[str, Any]:
    """Perform full roundtrip: module -> .indoor -> module -> .indoor."""
    game_key, source_module_root = module_case
    installation, game_arg = _installation_for(request, game_key=game_key, k1_installation=k1_installation)
    mk_mgr = ModuleKitManager(installation)

    tmp_path = tmp_path_factory.mktemp(f"rt_comparable_{game_key}_{source_module_root}")

    indoor0 = tmp_path / f"{source_module_root}.{game_key}.0.indoor"
    indoor1 = tmp_path / f"{source_module_root}.{game_key}.1.indoor"
    mod1 = tmp_path / f"{source_module_root}.{game_key}.1.mod"

    # Extract from original module
    rc = _run_indoor_extract(
        installation=installation,
        mk_mgr=mk_mgr,
        game_arg=game_arg,
        module_root=source_module_root,
        module_file=None,
        output=indoor0,
    )
    assert rc == 0, f"indoor-extract failed for {game_key}:{source_module_root} with exit code: {rc}"

    # Load original indoor map
    original_indoor_map = IndoorMap()
    missing = original_indoor_map.load(indoor0.read_bytes(), [], module_kit_manager=mk_mgr)
    assert missing == [], f"Missing rooms/components: {missing}"

    # Normalize module_id for stable comparison
    room_count = len(original_indoor_map.rooms)
    output_module_root = _safe_out_module_id(
        module_root=source_module_root, game_key=game_key, room_count=room_count
    )
    original_indoor_map.module_id = output_module_root

    # Write normalized indoor file
    indoor0.write_bytes(original_indoor_map.write())

    # Build module from indoor
    rc = _run_indoor_build(
        installation=installation,
        mk_mgr=mk_mgr,
        game_arg=game_arg,
        input_indoor=indoor0,
        output_mod=mod1,
        module_filename=output_module_root,
    )
    assert rc == 0, f"indoor-build failed for {game_key}:{source_module_root} with exit code: {rc}"

    # Extract from built module
    rc = _run_indoor_extract(
        installation=installation,
        mk_mgr=mk_mgr,
        game_arg=game_arg,
        module_root=source_module_root,
        module_file=mod1,
        output=indoor1,
    )
    assert rc == 0, f"indoor-extract (from module-file) failed for {game_key}:{source_module_root} with exit code: {rc}"

    # Load roundtripped indoor map
    roundtripped_indoor_map = IndoorMap()
    missing = roundtripped_indoor_map.load(indoor1.read_bytes(), [], module_kit_manager=mk_mgr)
    assert missing == [], f"Missing rooms/components after roundtrip: {missing}"

    return {
        "original_indoor_map": original_indoor_map,
        "roundtripped_indoor_map": roundtripped_indoor_map,
        "indoor0_path": indoor0,
        "indoor1_path": indoor1,
        "mod1_path": mod1,
        "game_key": game_key,
        "source_module_root": source_module_root,
        "output_module_root": output_module_root,
        "installation": installation,
        "mk_mgr": mk_mgr,
    }


def _installation_for(
    request: pytest.FixtureRequest,
    *,
    game_key: str,
    k1_installation: Installation,
) -> tuple[Installation, str]:
    """Resolve installation without forcing K2 fixture when K2 isn't configured."""
    if game_key == "k1":
        return k1_installation, "k1"
    if game_key == "k2":
        return request.getfixturevalue("k2_installation"), "k2"
    msg = f"Unexpected game key: {game_key!r}"
    raise AssertionError(msg)


# Test: Module -> .indoor -> module -> .indoor roundtrip
def test_module_to_indoor_to_module_to_indoor_roundtrip(roundtrip_data: dict[str, Any]) -> None:
    """Test complete roundtrip: module -> .indoor -> module -> .indoor using ComparableMixin.compare()."""
    original = roundtrip_data["original_indoor_map"]
    roundtripped = roundtrip_data["roundtripped_indoor_map"]

    is_identical = _compare_indoor_maps_with_udiff(
        original,
        roundtripped,
        original_label="original (module -> .indoor)",
        roundtripped_label="roundtripped (module -> .indoor -> module -> .indoor)",
    )

    assert is_identical, "IndoorMap objects should be identical after full roundtrip"


# Test: .indoor -> module -> .indoor roundtrip
def test_indoor_to_module_to_indoor_roundtrip(roundtrip_data: dict[str, Any]) -> None:
    """Test roundtrip: .indoor -> module -> .indoor using ComparableMixin.compare()."""
    game_key = roundtrip_data["game_key"]
    source_module_root = roundtrip_data["source_module_root"]
    output_module_root = roundtrip_data["output_module_root"]
    installation = roundtrip_data["installation"]
    mk_mgr = roundtrip_data["mk_mgr"]
    game_arg = "k1" if game_key == "k1" else "k2"

    tmp_path = roundtrip_data["indoor0_path"].parent

    # Start with the first extracted indoor file
    indoor_start = roundtrip_data["indoor0_path"]
    mod_intermediate = tmp_path / f"{source_module_root}.{game_key}.intermediate.mod"
    indoor_end = tmp_path / f"{source_module_root}.{game_key}.end.indoor"

    # Load starting indoor map
    start_indoor_map = IndoorMap()
    missing = start_indoor_map.load(indoor_start.read_bytes(), [], module_kit_manager=mk_mgr)
    assert missing == [], f"Missing rooms/components in start: {missing}"

    # Build module from indoor
    rc = _run_indoor_build(
        installation=installation,
        mk_mgr=mk_mgr,
        game_arg=game_arg,
        input_indoor=indoor_start,
        output_mod=mod_intermediate,
        module_filename=output_module_root,
    )
    assert rc == 0, f"indoor-build failed with exit code: {rc}"

    # Extract from built module
    rc = _run_indoor_extract(
        installation=installation,
        mk_mgr=mk_mgr,
        game_arg=game_arg,
        module_root=source_module_root,
        module_file=mod_intermediate,
        output=indoor_end,
    )
    assert rc == 0, f"indoor-extract failed with exit code: {rc}"

    # Load end indoor map
    end_indoor_map = IndoorMap()
    missing = end_indoor_map.load(indoor_end.read_bytes(), [], module_kit_manager=mk_mgr)
    assert missing == [], f"Missing rooms/components in end: {missing}"

    # Compare using ComparableMixin.compare()
    is_identical = _compare_indoor_maps_with_udiff(
        start_indoor_map,
        end_indoor_map,
        original_label="start (.indoor)",
        roundtripped_label="end (.indoor -> module -> .indoor)",
    )

    assert is_identical, "IndoorMap objects should be identical after .indoor -> module -> .indoor roundtrip"
