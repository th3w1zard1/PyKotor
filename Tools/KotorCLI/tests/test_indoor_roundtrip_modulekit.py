"""High-granularity ModuleKit (implicit-kit) roundtrip tests for KotorCLI indoor commands.

These tests are designed to catch the nasty class of bugs where a module can be built, but
walkability is broken in-game (typically via WOK/BWM material/transition issues).

Constraints:
- Do NOT rely on external on-disk kits. Use `--implicit-kit` only.
- Use KotorCLI commands (via `kotorcli.__main__.cli_main`) so behavior matches the CLI.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
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


from kotorcli.__main__ import cli_main
from pykotor.common.indoormap import IndoorMap
from pykotor.common.modulekit import ModuleKitManager
from pykotor.extract.installation import Installation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.erf import ERF, ERFType, read_erf, write_erf
from pykotor.resource.formats.lyt import LYT, LYTRoom, bytes_lyt, read_lyt
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath


def _run_cli(argv: list[str]) -> int:
    return int(cli_main(argv))


def _make_min_installation(tmp_path: Path) -> Path:
    install_dir = tmp_path / "install"
    install_dir.mkdir(parents=True, exist_ok=True)
    (install_dir / "swkotor.exe").touch()
    (install_dir / "modules").mkdir(parents=True, exist_ok=True)
    return install_dir


def _read_erf_payloads(mod_path: Path) -> dict[tuple[str, ResourceType], bytes]:
    erf = read_erf(mod_path)
    out: dict[tuple[str, ResourceType], bytes] = {}
    for res in erf:
        payload = res.data() if callable(getattr(res, "data", None)) else res.data  # type: ignore[truthy-function]
        out[(str(res.resref).lower(), res.restype)] = bytes(payload)
    return out


def _write_tiny_1room_module_from_fixture(*, src_mod: Path, dst_mod: Path, module_root: str) -> None:
    """Carve a tiny 1-room module out of a large fixture for fast tests."""
    payloads = _read_erf_payloads(src_mod)

    lyt_candidates = [data for (_resref, restype), data in payloads.items() if restype == ResourceType.LYT]
    if not lyt_candidates:
        msg = f"Fixture module has no LYT: {src_mod}"
        raise AssertionError(msg)

    src_lyt: LYT | None = None
    for lyt_bytes in lyt_candidates:
        try:
            src_lyt = read_lyt(lyt_bytes)
            break
        except Exception:
            continue
    if src_lyt is None:
        msg = f"Failed to parse any LYT from fixture: {src_mod}"
        raise AssertionError(msg)

    chosen_model: str | None = None
    chosen_pos = None
    for room in src_lyt.rooms:
        model = (room.model or "").strip().lower()
        if not model:
            continue
        if (model, ResourceType.MDL) not in payloads:
            continue
        if (model, ResourceType.MDX) not in payloads:
            continue
        if (model, ResourceType.WOK) not in payloads:
            continue
        bwm = read_bwm(payloads[(model, ResourceType.WOK)])
        if not bwm.faces:
            continue
        chosen_model = model
        chosen_pos = room.position
        break

    if chosen_model is None or chosen_pos is None:
        msg = f"No suitable (MDL+MDX+WOK) room found in fixture LYT: {src_mod}"
        raise AssertionError(msg)

    out_lyt = LYT()
    out_lyt.rooms.append(LYTRoom(chosen_model, chosen_pos))

    erf = ERF(ERFType.MOD)
    erf.set_data(module_root.lower(), ResourceType.LYT, bytes_lyt(out_lyt))
    erf.set_data(chosen_model, ResourceType.MDL, payloads[(chosen_model, ResourceType.MDL)])
    erf.set_data(chosen_model, ResourceType.MDX, payloads[(chosen_model, ResourceType.MDX)])
    erf.set_data(chosen_model, ResourceType.WOK, payloads[(chosen_model, ResourceType.WOK)])
    write_erf(erf, dst_mod)


def _parse_indoor(raw: bytes) -> dict[str, Any]:
    return json.loads(raw.decode("utf-8"))


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


def _safe_out_module_id(*, module_root: str, game_key: str, room_count: int) -> str:
    """Pick a module id that will not exceed the 16-char ResRef limit for `{id}_room{i}`."""
    max_index = max(room_count - 1, 0)
    digits = len(str(max_index))
    max_module_id_len = 16 - (len("_room") + digits)
    if max_module_id_len <= 0:
        msg = f"Cannot construct a valid module_id for room_count={room_count} (digits={digits})"
        raise AssertionError(msg)

    base = f"{module_root}{game_key}rt".lower()
    base = "".join(c for c in base if c.isalnum() or c == "_")
    return base[:max_module_id_len]


@pytest.fixture(autouse=True)
def _require_module_case(module_case: tuple[str, str]) -> None:  # noqa: ARG001
    """Ensure all tests in this module are collected per-installation and per-module."""
    return


@dataclass
class RoundtripResult:
    module_root: str
    source_module_root: str
    install_dir: Path
    source_mod_bytes: bytes
    source_mod_payloads: dict[tuple[str, ResourceType], bytes]
    indoor0_extracted_raw: bytes
    indoor0_normalized_raw: bytes
    indoor0_raw: bytes
    indoor1_raw: bytes
    mod1_bytes: bytes
    mod2_bytes: bytes
    mod1_payloads: dict[tuple[str, ResourceType], bytes]
    mod2_payloads: dict[tuple[str, ResourceType], bytes]


@pytest.fixture(scope="module")
def rt(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
    module_case: tuple[str, str],
    k1_installation: Installation,
) -> RoundtripResult:
    """Roundtrip once per (installation, module_root), reused across granular assertions."""
    game_key, source_module_root = module_case
    installation, game_arg = _installation_for(request, game_key=game_key, k1_installation=k1_installation)

    tmp_path = tmp_path_factory.mktemp(f"rt_modulekit_{game_key}_{source_module_root}")

    indoor0 = tmp_path / f"{source_module_root}.{game_key}.0.indoor"
    indoor1 = tmp_path / f"{source_module_root}.{game_key}.1.indoor"
    mod1 = tmp_path / f"{source_module_root}.{game_key}.1.mod"
    mod2 = tmp_path / f"{source_module_root}.{game_key}.2.mod"

    # Use the real installation as the authoritative source; do not copy/mutate it.
    install_dir = Path(installation.path())
    source_mod_bytes = b""
    source_mod_payloads = {}

    rc = _run_cli(
        [
            "indoor-extract",
            "--implicit-kit",
            "--module",
            source_module_root,
            "--output",
            str(indoor0),
            "--installation",
            str(install_dir),
            "--game",
            game_arg,
            "--log-level",
            "error",
        ]
    )
    assert rc == 0, f"indoor-extract failed for {game_key}:{source_module_root} with exit code: {rc}"

    indoor0_extracted_raw = indoor0.read_bytes()

    # Normalize the `.indoor` module id to the output module root, so the build output embeds
    # an `.indoor` that is stable and so `indoor0 == indoor1`.
    d0 = _parse_indoor(indoor0.read_bytes())
    room_count = len(d0.get("rooms", [])) if isinstance(d0.get("rooms", []), list) else 0
    output_module_root = _safe_out_module_id(module_root=source_module_root, game_key=game_key, room_count=room_count)
    d0["warp"] = output_module_root
    d0["module_id"] = output_module_root
    indoor0.write_bytes(json.dumps(d0).encode("utf-8"))
    indoor0_normalized_raw = indoor0.read_bytes()

    rc = _run_cli(
        [
            "indoor-build",
            "--implicit-kit",
            "--input",
            str(indoor0),
            "--output",
            str(mod1),
            "--installation",
            str(install_dir),
            "--game",
            game_arg,
            "--module-filename",
            output_module_root,
            "--log-level",
            "error",
        ]
    )
    assert rc == 0, f"indoor-build failed for {game_key}:{source_module_root} with exit code: {rc}"

    rc = _run_cli(
        [
            "indoor-extract",
            "--implicit-kit",
            "--module-file",
            str(mod1),
            "--output",
            str(indoor1),
            "--installation",
            str(install_dir),
            "--game",
            game_arg,
            "--log-level",
            "error",
        ]
    )
    assert rc == 0, f"indoor-extract (module-file) failed for {game_key}:{source_module_root} with exit code: {rc}"

    rc = _run_cli(
        [
            "indoor-build",
            "--implicit-kit",
            "--input",
            str(indoor1),
            "--output",
            str(mod2),
            "--installation",
            str(install_dir),
            "--game",
            game_arg,
            "--module-filename",
            output_module_root,
            "--log-level",
            "error",
        ]
    )
    assert rc == 0, f"indoor-build (2nd) failed for {game_key}:{source_module_root} with exit code: {rc}"

    indoor0_raw = indoor0.read_bytes()
    indoor1_raw = indoor1.read_bytes()
    mod1_bytes = mod1.read_bytes()
    mod2_bytes = mod2.read_bytes()
    mod1_payloads = _read_erf_payloads(mod1)
    mod2_payloads = _read_erf_payloads(mod2)

    return RoundtripResult(
        module_root=output_module_root,
        source_module_root=source_module_root,
        install_dir=install_dir,
        source_mod_bytes=source_mod_bytes,
        source_mod_payloads=source_mod_payloads,
        indoor0_extracted_raw=indoor0_extracted_raw,
        indoor0_normalized_raw=indoor0_normalized_raw,
        indoor0_raw=indoor0_raw,
        indoor1_raw=indoor1_raw,
        mod1_bytes=mod1_bytes,
        mod2_bytes=mod2_bytes,
        mod1_payloads=mod1_payloads,
        mod2_payloads=mod2_payloads,
    )


# -----------------------------
# 15 tests: mod -> indoor -> mod
# -----------------------------


def test_mim_mod_bytes_identical(rt: RoundtripResult):
    assert rt.mod1_bytes == rt.mod2_bytes, f"Mod1 bytes do not match mod2 bytes: {rt.mod1_bytes} != {rt.mod2_bytes}"


def test_mim_resource_keys_identical(rt: RoundtripResult):
    assert set(rt.mod1_payloads.keys()) == set(
        rt.mod2_payloads.keys()
    ), f"Mod1 payload keys do not match mod2 payload keys: {rt.mod1_payloads.keys()} != {rt.mod2_payloads.keys()}"


def test_mim_resource_payloads_identical(rt: RoundtripResult):
    for key, b1 in rt.mod1_payloads.items():
        assert (
            b1 == rt.mod2_payloads[key]
        ), f"Mod1 payload {key} does not match mod2 payload {key}: {b1} != {rt.mod2_payloads[key]}"


def test_mim_has_core_resources(rt: RoundtripResult):
    keys = set(rt.mod1_payloads.keys())
    root = rt.module_root
    assert (root, ResourceType.LYT) in keys, f"LYT not in mod1 payloads: {keys}"
    assert (root, ResourceType.VIS) in keys, f"VIS not in mod1 payloads: {keys}"
    assert (root, ResourceType.ARE) in keys, f"ARE not in mod1 payloads: {keys}"
    assert (root, ResourceType.GIT) in keys, f"GIT not in mod1 payloads: {keys}"
    assert ("module", ResourceType.IFO) in keys, f"IFO not in mod1 payloads: {keys}"


def test_mim_embeds_indoormap(rt: RoundtripResult):
    assert (
        "indoormap",
        ResourceType.TXT,
    ) in rt.mod1_payloads, f"indoormap not in mod1 payloads: {rt.mod1_payloads.keys()}"


def test_mim_embedded_indoormap_matches_extracted(rt: RoundtripResult):
    assert (
        rt.mod1_payloads[("indoormap", ResourceType.TXT)] == rt.indoor1_raw
    ), f"indoormap payload does not match extracted indoor1: {rt.mod1_payloads[('indoormap', ResourceType.TXT)]} != {rt.indoor1_raw}"


def test_mim_has_wok(rt: RoundtripResult):
    assert any(
        restype == ResourceType.WOK for (_r, restype) in rt.mod1_payloads
    ), f"No WOK in mod1 payloads: {rt.mod1_payloads.keys()}"


def test_mim_all_woks_nonempty(rt: RoundtripResult):
    for (resref, restype), data in rt.mod1_payloads.items():
        if restype != ResourceType.WOK:
            continue
        assert read_bwm(data).faces, f"Empty walkmesh: {resref}.wok"


def test_mim_wok_materials_preserved(rt: RoundtripResult):
    def mats(payloads: dict[tuple[str, ResourceType], bytes]) -> set[int]:
        out: set[int] = set()
        for (resref, restype), data in payloads.items():
            if restype != ResourceType.WOK:
                continue
            bwm = read_bwm(data)
            for f in bwm.faces:
                out.add(int(f.material))
                for t in (f.trans1, f.trans2, f.trans3):
                    if t is None:
                        continue
                    assert -1 <= int(t) <= 2048, f"Suspicious transition index in {resref}.wok: {t}"
        return out

    assert mats(rt.mod1_payloads) == mats(
        rt.mod2_payloads
    ), f"WOK materials do not match: {mats(rt.mod1_payloads)} != {mats(rt.mod2_payloads)}"


def test_mim_has_room_model_triplet(rt: RoundtripResult):
    prefix = f"{rt.module_root}_room"
    mdls = [k for k in rt.mod1_payloads if k[1] == ResourceType.MDL and k[0].startswith(prefix)]
    mdxs = [k for k in rt.mod1_payloads if k[1] == ResourceType.MDX and k[0].startswith(prefix)]
    woks = [k for k in rt.mod1_payloads if k[1] == ResourceType.WOK and k[0].startswith(prefix)]
    assert len(mdls) == len(mdxs) == len(woks), f"MDL/MDX/WOK count mismatch: {len(mdls)} != {len(mdxs)} != {len(woks)}"
    assert len(mdls) > 0, f"No MDLs in mod1 payloads: {rt.mod1_payloads.keys()}"


def test_mim_minimap_exists(rt: RoundtripResult):
    assert (
        f"lbl_map{rt.module_root}",
        ResourceType.TGA,
    ) in rt.mod1_payloads, f"lbl_map{rt.module_root} not in mod1 payloads: {rt.mod1_payloads.keys()}"


def test_mim_git_nonempty(rt: RoundtripResult):
    assert (
        len(rt.mod1_payloads[(rt.module_root, ResourceType.GIT)]) > 0
    ), f"GIT is empty: {rt.mod1_payloads[(rt.module_root, ResourceType.GIT)]}"


def test_mim_wok_bytes_identical(rt: RoundtripResult):
    for key, b1 in rt.mod1_payloads.items():
        if key[1] != ResourceType.WOK:
            continue
        assert (
            b1 == rt.mod2_payloads[key]
        ), f"WOK {key} does not match mod2 payload {key}: {b1} != {rt.mod2_payloads[key]}"


def test_mim_embedded_indoormap_present_after_roundtrip(rt: RoundtripResult):
    assert (
        "indoormap",
        ResourceType.TXT,
    ) in rt.mod2_payloads, f"indoormap not in mod2 payloads: {rt.mod2_payloads.keys()}"


# -----------------------------
# 15 tests: indoor -> mod -> indoor
# -----------------------------


def test_imi_indoor_bytes_identical(rt: RoundtripResult):
    assert (
        rt.indoor0_raw == rt.indoor1_raw
    ), f"indoor0 raw does not match indoor1 raw: {rt.indoor0_raw} != {rt.indoor1_raw}"


def test_imi_indoor_json_parses(rt: RoundtripResult):
    try:
        _parse_indoor(rt.indoor1_raw)
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse indoor1 raw as JSON: {e}")


def test_imi_rooms_present(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    assert "rooms" in d, f"Rooms not in indoor1 raw: {d}"
    assert isinstance(d["rooms"], list), f"Rooms is not a list: {d['rooms']}"
    assert len(d["rooms"]) > 0, f"Rooms is empty: {d['rooms']}"


def test_imi_room_fields(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    for room in d["rooms"]:
        assert "position" in room, f"Position not in room: {room}"
        assert isinstance(room["position"], list), f"Position is not a list: {room['position']}"
        assert len(room["position"]) == 3, f"Position has wrong length: {len(room['position'])} != 3"
        assert "rotation" in room, f"Rotation not in room: {room}"
        assert "flip_x" in room, f"Flip_x not in room: {room}"
        assert "flip_y" in room, f"Flip_y not in room: {room}"
        assert "kit" in room, f"Kit not in room: {room}"
        assert "component" in room, f"Component not in room: {room}"


def test_imi_module_root_written(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    for room in d["rooms"]:
        assert "module_root" in room, f"Module_root not in room: {room}"
        assert (
            str(room["module_root"]).lower() == rt.source_module_root
        ), f"Module_root does not match source module root: {room['module_root']} != {rt.source_module_root}"


def test_imi_warp_matches(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    assert d.get("warp") == rt.module_root, f"Warp does not match module root: {d.get('warp')} != {rt.module_root}"


def test_imi_lighting_triplet(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    lighting = d.get("lighting")
    assert isinstance(lighting, list), f"Lighting is not a list: {lighting}"
    assert len(lighting) == 3, f"Lighting has wrong length: {len(lighting)} != 3"


def test_imi_components_unique(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    comps = [r["component"] for r in d["rooms"]]
    assert len(comps) == len(set(comps)), f"Components are not unique: {comps}"


def test_imi_kit_is_module_root(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    assert all(
        str(r["kit"]).lower() == rt.source_module_root for r in d["rooms"]
    ), f"Kit does not match source module root: {d['rooms']}"


def test_imi_loadable_with_modulekit(rt: RoundtripResult):
    installation = Installation(CaseAwarePath(rt.install_dir))
    mk = ModuleKitManager(installation)
    indoor = IndoorMap()
    missing = indoor.load(rt.indoor1_raw, [], module_kit_manager=mk)
    assert missing == [], f"Missing rooms: {missing}"
    assert len(indoor.rooms) > 0, f"Indoor has no rooms: {indoor.rooms}"


def test_imi_positions_finite(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    for room in d["rooms"]:
        x, y, z = room["position"]
        assert abs(float(x)) < 1e9, f"Position X is out of range: {x}"
        assert abs(float(y)) < 1e9, f"Position Y is out of range: {y}"
        assert abs(float(z)) < 1e9, f"Position Z is out of range: {z}"


def test_imi_rotation_numeric(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    for room in d["rooms"]:
        assert isinstance(room["rotation"], (int, float)), f"Rotation is not a number: {room['rotation']}"


def test_imi_flip_flags_bool(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    for room in d["rooms"]:
        assert isinstance(room["flip_x"], bool), f"Flip_x is not a bool: {room['flip_x']}"
        assert isinstance(room["flip_y"], bool), f"Flip_y is not a bool: {room['flip_y']}"


def test_imi_name_shape(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    assert "name" in d, f"Name not in indoor1 raw: {d}"
    assert isinstance(d["name"], dict), f"Name is not a dict: {d['name']}"
    assert "stringref" in d["name"], f"Stringref not in name: {d['name']}"


def test_imi_target_game_type_optional(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    if "target_game_type" in d:
        assert d["target_game_type"] in (
            True,
            False,
            None,
        ), f"Target game type is not a bool or None: {d['target_game_type']}"


# -----------------------------
# 20 additional focused checks
# -----------------------------


def test_unit_mod_has_are(rt: RoundtripResult):
    assert (
        rt.module_root,
        ResourceType.ARE,
    ) in rt.mod1_payloads, f"ARE not in mod1 payloads: {rt.mod1_payloads.keys()}"


def test_unit_mod_has_git(rt: RoundtripResult):
    assert (
        rt.module_root,
        ResourceType.GIT,
    ) in rt.mod1_payloads, f"GIT not in mod1 payloads: {rt.mod1_payloads.keys()}"


def test_unit_mod_has_vis(rt: RoundtripResult):
    assert (
        rt.module_root,
        ResourceType.VIS,
    ) in rt.mod1_payloads, f"VIS not in mod1 payloads: {rt.mod1_payloads.keys()}"


def test_unit_mod_has_ifo(rt: RoundtripResult):
    assert ("module", ResourceType.IFO) in rt.mod1_payloads, f"IFO not in mod1 payloads: {rt.mod1_payloads.keys()}"


def test_unit_room_models_have_mdl(rt: RoundtripResult):
    assert any(
        restype == ResourceType.MDL for (_r, restype) in rt.mod1_payloads
    ), f"No MDL in mod1 payloads: {rt.mod1_payloads.keys()}"


def test_unit_room_models_have_mdx(rt: RoundtripResult):
    assert any(
        restype == ResourceType.MDX for (_r, restype) in rt.mod1_payloads
    ), f"No MDX in mod1 payloads: {rt.mod1_payloads.keys()}"


def test_unit_embedded_indoor_is_utf8(rt: RoundtripResult):
    try:
        rt.indoor1_raw.decode("utf-8")
    except UnicodeDecodeError as e:
        pytest.fail(f"Failed to decode indoor1 raw as UTF-8: {e}")


def test_unit_mod_payloads_nonempty(rt: RoundtripResult):
    assert len(rt.mod1_payloads) > 0, f"Mod1 payloads is empty: {rt.mod1_payloads.keys()}"


def test_unit_indoormap_present_in_payloads(rt: RoundtripResult):
    assert (
        "indoormap",
        ResourceType.TXT,
    ) in rt.mod1_payloads, f"indoormap not in mod1 payloads: {rt.mod1_payloads.keys()}"


def test_unit_wok_count_matches_room_count(rt: RoundtripResult):
    room_count = len(_parse_indoor(rt.indoor1_raw)["rooms"])
    wok_count = sum(
        1 for (_r, t) in rt.mod1_payloads if (t == ResourceType.WOK and _r.startswith(f"{rt.module_root}_room"))
    )
    assert wok_count == room_count, f"Wok count does not match room count: {wok_count} != {room_count}"


def test_unit_wok_faces_walkable_present(rt: RoundtripResult):
    any_walkable = False
    for (_resref, restype), data in rt.mod1_payloads.items():
        if restype != ResourceType.WOK:
            continue
        if any(f.material.is_walkable() for f in read_bwm(data).faces):
            any_walkable = True
            break
    assert any_walkable, f"No walkable WOK in mod1 payloads: {rt.mod1_payloads.keys()}"


def test_unit_modulekit_loads_from_install(rt: RoundtripResult):
    installation = Installation(CaseAwarePath(rt.install_dir))
    mk = ModuleKitManager(installation)
    kit = mk.get_module_kit(rt.source_module_root)
    assert kit.ensure_loaded(), f"ModuleKit failed to load module: {rt.source_module_root}"


def test_unit_modulekit_components_nonempty(rt: RoundtripResult):
    installation = Installation(CaseAwarePath(rt.install_dir))
    mk = ModuleKitManager(installation)
    kit = mk.get_module_kit(rt.source_module_root)
    assert kit.ensure_loaded(), f"ModuleKit failed to load module: {rt.source_module_root}"
    assert len(kit.components) > 0, f"ModuleKit has no components: {rt.source_module_root}"


def test_unit_modulekit_components_have_default_position(rt: RoundtripResult):
    installation = Installation(CaseAwarePath(rt.install_dir))
    mk = ModuleKitManager(installation)
    kit = mk.get_module_kit(rt.source_module_root)
    assert kit.ensure_loaded(), f"ModuleKit failed to load module: {rt.source_module_root}"
    for c in kit.components:
        pos = getattr(c, "default_position", None)
        assert pos is not None, f"Component {c.id} has no default position: {c}"


def test_unit_modulekit_bwm_is_room_local_via_lyt_translation(rt: RoundtripResult):
    """Validate our critical coordinate-space rule:

    - Module WOKs are commonly authored in room-local space (matching MDL coordinates).
    - ModuleKit does NOT translate them; they're already in the correct coordinate space.
    """
    # Read composite module LYT+WOK via Module (supports .rim/_s.rim/_dlg.erf/.mod).
    from pykotor.common.module import Module

    installation = Installation(CaseAwarePath(rt.install_dir))
    module = Module(rt.source_module_root, installation, use_dot_mod=True)
    lyt_res = module.layout()
    assert lyt_res is not None, f"Module {rt.source_module_root} has no layout: {lyt_res}"
    lyt = lyt_res.resource()
    assert lyt is not None, f"LYT resource is None: {lyt}"
    assert len(lyt.rooms) > 0, f"LYT has no rooms: {lyt.rooms}"

    # Build expected bbox per component id from the module's own WOKs.
    expected_bbox_by_component_id: dict[str, tuple[float, float, float, float]] = {}
    for idx, room in enumerate(lyt.rooms):
        model = (room.model or f"room{idx}").strip().lower()
        wok_res = module.resource(model, ResourceType.WOK)
        if wok_res is None:
            continue
        wok_bytes = wok_res.data()
        if wok_bytes is None:
            continue
        bwm = read_bwm(wok_bytes)
        verts = list(bwm.vertices())
        if not verts:
            continue
        component_id = f"{model}_{idx}"
        expected_bbox_by_component_id[component_id] = (
            min(v.x for v in verts),
            max(v.x for v in verts),
            min(v.y for v in verts),
            max(v.y for v in verts),
        )

    assert expected_bbox_by_component_id, f"Module {rt.source_module_root} has no usable WOK/BWM vertices to compare"

    # Load ModuleKit component and verify coordinates match (no translation applied).
    mk = ModuleKitManager(installation)
    kit = mk.get_module_kit(rt.source_module_root)
    assert kit.ensure_loaded(), f"ModuleKit failed to load module: {rt.source_module_root}"
    assert kit.components, f"ModuleKit has no components: {rt.source_module_root}"

    # Compare each component's bbox against its corresponding module WOK bbox.
    for comp in kit.components:
        verts = list(comp.bwm.vertices())
        assert verts, f"Component {comp.id} has no vertices: {rt.source_module_root}"
        bbox = (
            min(v.x for v in verts),
            max(v.x for v in verts),
            min(v.y for v in verts),
            max(v.y for v in verts),
        )
        exp = expected_bbox_by_component_id.get(comp.id)
        if exp is None:
            # If the module lacks a WOK (or it's empty/unparseable), ModuleKit falls back to a
            # placeholder quad at origin (size=5 => bbox [-5..5] on X/Y).
            assert len(comp.bwm.faces) == 2, f"Component {comp.id} has no faces: {rt.source_module_root}"
            assert abs(bbox[0] - (-5.0)) < 1e-6, f"Component {comp.id} has incorrect X bbox: {bbox[0]} != {-5.0}"
            assert abs(bbox[1] - (5.0)) < 1e-6, f"Component {comp.id} has incorrect Y bbox: {bbox[1]} != {5.0}"
            assert abs(bbox[2] - (-5.0)) < 1e-6, f"Component {comp.id} has incorrect X bbox: {bbox[2]} != {-5.0}"
            assert abs(bbox[3] - (5.0)) < 1e-6, f"Component {comp.id} has incorrect Y bbox: {bbox[3]} != {5.0}"
        else:
            assert abs(exp[0] - bbox[0]) < 1e-6, f"Component {comp.id} has incorrect X bbox: {bbox[0]} != {exp[0]}"
            assert abs(exp[1] - bbox[1]) < 1e-6, f"Component {comp.id} has incorrect Y bbox: {bbox[1]} != {exp[1]}"
            assert abs(exp[2] - bbox[2]) < 1e-6, f"Component {comp.id} has incorrect X bbox: {bbox[2]} != {exp[2]}"
            assert abs(exp[3] - bbox[3]) < 1e-6, f"Component {comp.id} has incorrect Y bbox: {bbox[3]} != {exp[3]}"


def test_unit_modulekit_hook_edges_int(rt: RoundtripResult):
    installation = Installation(CaseAwarePath(rt.install_dir))
    mk = ModuleKitManager(installation)
    kit = mk.get_module_kit(rt.source_module_root)
    assert kit.ensure_loaded(), f"ModuleKit failed to load module: {rt.source_module_root}"
    for comp in kit.components:
        for h in comp.hooks:
            assert isinstance(h.edge, int), f"Hook edge is not an int: {h.edge}"


def test_unit_indoor_contains_module_root_field(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    assert all("module_root" in r for r in d["rooms"]), f"Rooms missing module_root field: {d['rooms']}"


def test_unit_indoor_room_count_positive(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    assert len(d["rooms"]) > 0, f"Rooms is empty: {d['rooms']}"


def test_unit_mod_roundtrip_payloads_match(rt: RoundtripResult):
    assert (
        rt.mod1_payloads == rt.mod2_payloads
    ), f"Mod1 payloads do not match mod2 payloads: {rt.mod1_payloads} != {rt.mod2_payloads}"
