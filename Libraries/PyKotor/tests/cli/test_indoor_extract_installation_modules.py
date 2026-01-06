from __future__ import annotations

import json
from pathlib import Path

from pykotor.cli.dispatch import cli_main
from pykotor.common.module import Module
from pykotor.extract.installation import Installation


def _run_cli(argv: list[str]) -> int:
    return cli_main(argv)


def _parse_indoor(raw: bytes) -> dict:
    return json.loads(raw.decode("utf-8"))


def _expected_room_count_from_layout(installation: Installation, module_root: str) -> int | None:
    """Determine expected extracted room count from the module's LYT (fast mode, no texture crawling)."""
    module = Module(module_root, installation, use_dot_mod=True, load_textures=False)
    lyt_res = module.layout()
    if lyt_res is None:
        return None
    lyt = lyt_res.resource()
    if lyt is None:
        return None
    return len(lyt.rooms)


def _installation_for(
    game_key: str,
    k1_installation: Installation,
    k2_installation: Installation,
) -> Installation:
    """Get the installation for the given game key."""
    if game_key == "k1":
        return k1_installation
    if game_key == "k2":
        return k2_installation
    msg = f"Unexpected game key: {game_key!r}"
    raise AssertionError(msg)


def test_indoor_extract_each_module_matches_modulekit_loadability(
    module_case: tuple[str, str],
    tmp_path: Path,
    k1_installation: Installation,
    k2_installation: Installation,
) -> None:
    """One test per module root in the real installations.

    This is intentionally strict and non-skipping:
    - If the module has a usable layout (LYT with rooms), CLI must succeed.
    - If the module lacks a usable layout, CLI must fail cleanly (non-zero exit).
    """
    game_key, module_root = module_case
    installation = _installation_for(game_key, k1_installation, k2_installation)
    game_arg = "k1" if game_key == "k1" else "k2"

    expected_room_count = _expected_room_count_from_layout(installation, module_root)

    out = tmp_path / f"{game_key}_{module_root}.indoor"
    rc = _run_cli(
        [
            "indoor-extract",
            "--implicit-kit",
            "--module",
            module_root,
            "--output",
            str(out),
            "--installation",
            str(installation.path()),
            "--game",
            game_arg,
            "--log-level",
            "error",
        ]
    )

    if expected_room_count is not None and expected_room_count > 0:
        assert rc == 0, f"CLI failed for module with LYT rooms ({expected_room_count}): {module_root} (rc={rc})"
        assert out.is_file(), f"Output file does not exist: {out}"
        raw = out.read_bytes()
        d = _parse_indoor(raw)
        assert "rooms" in d, f"Indoor file missing rooms: {d}"
        assert isinstance(d["rooms"], list), f"Rooms is not a list: {d['rooms']}"
        assert len(d["rooms"]) == expected_room_count, f"Rooms length mismatch: {len(d['rooms'])} != {expected_room_count}"
        for room in d["rooms"]:
            assert "kit" in room, f"Room missing kit: {room}"
            assert str(room["kit"]).lower() == module_root.lower(), f"Room kit mismatch: {room['kit']} != {module_root}"
            assert "component" in room, f"Room missing component: {room}"
            assert "module_root" in room, f"Room missing module_root: {room}"
            assert (
                str(room["module_root"]).lower() == module_root.lower()
            ), f"Room module_root mismatch: {room['module_root']} != {module_root}"
            assert "position" in room, f"Room missing position: {room}"
            assert isinstance(room["position"], list), f"Room position is not a list: {room['position']}"
            assert len(room["position"]) == 3, f"Room position has wrong length: {len(room['position'])} != 3"
            assert "rotation" in room, f"Room missing rotation: {room}"
            assert "flip_x" in room, f"Room missing flip_x: {room}"
            assert isinstance(room["flip_x"], bool), f"Room flip_x is not a bool: {room['flip_x']}"
            assert "flip_y" in room, f"Room missing flip_y: {room}"
            assert isinstance(room["flip_y"], bool), f"Room flip_y is not a bool: {room['flip_y']}"
    else:
        assert rc != 0, f"CLI unexpectedly succeeded for module without usable LYT rooms: {module_root}"
        assert not out.exists(), f"Output file should not exist: {out}"
