"""High-granularity ModuleKit (implicit-kit) roundtrip tests for KotorCLI indoor commands.

These tests are designed to catch the nasty class of bugs where a module can be built, but
walkability is broken in-game (typically via WOK/BWM material/transition issues).

Constraints:
- Do NOT rely on external on-disk kits. Use `--implicit-kit` only.
- Use KotorCLI commands (via `kotorcli.__main__.cli_main`) so behavior matches the CLI.
"""

from __future__ import annotations

import json
import shutil
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
from pykotor.extract.installation import Installation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.erf import ERF, ERFType, read_erf, write_erf
from pykotor.resource.formats.lyt import LYT, LYTRoom, bytes_lyt, read_lyt
from pykotor.resource.type import ResourceType
from pykotor.tools.indoormap import IndoorMap
from pykotor.tools.modulekit import ModuleKitManager
from pykotor.tools.path import CaseAwarePath


@dataclass(frozen=True)
class FixtureModule:
    module_root: str
    mod_path: Path


FIXTURE: FixtureModule = FixtureModule(
    module_root="step01",
    mod_path=absolute_file_path.parents[3]
    / "Libraries"
    / "PyKotor"
    / "tests"
    / "test_files"
    / "indoormap_bug_inspect_workspace"
    / "v2.0.4-toolset"
    / "step01"
    / "step01.mod",
)


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


@dataclass
class RoundtripResult:
    module_root: str
    install_dir: Path
    indoor0_raw: bytes
    indoor1_raw: bytes
    mod1_bytes: bytes
    mod2_bytes: bytes
    mod1_payloads: dict[tuple[str, ResourceType], bytes]
    mod2_payloads: dict[tuple[str, ResourceType], bytes]


@pytest.fixture(scope="session")
def rt(tmp_path_factory: pytest.TempPathFactory) -> RoundtripResult:
    assert FIXTURE.mod_path.is_file(), f"Missing fixture module: {FIXTURE.mod_path}"
    tmp_path = tmp_path_factory.mktemp("rt_modulekit")

    install_dir = _make_min_installation(tmp_path)
    tiny_mod = install_dir / "modules" / f"{FIXTURE.module_root}.mod"
    _write_tiny_1room_module_from_fixture(src_mod=FIXTURE.mod_path, dst_mod=tiny_mod, module_root=FIXTURE.module_root)

    indoor0 = tmp_path / f"{FIXTURE.module_root}.0.indoor"
    indoor1 = tmp_path / f"{FIXTURE.module_root}.1.indoor"
    mod1 = tmp_path / f"{FIXTURE.module_root}.1.mod"
    mod2 = tmp_path / f"{FIXTURE.module_root}.2.mod"

    rc = _run_cli(
        [
            "indoor-extract",
            "--implicit-kit",
            "--module",
            FIXTURE.module_root,
            "--output",
            str(indoor0),
            "--installation",
            str(install_dir),
            "--game",
            "k1",
            "--log-level",
            "error",
        ]
    )
    assert rc == 0

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
            "k1",
            "--log-level",
            "error",
        ]
    )
    assert rc == 0

    shutil.copyfile(mod1, tiny_mod)
    rc = _run_cli(
        [
            "indoor-extract",
            "--implicit-kit",
            "--module",
            FIXTURE.module_root,
            "--output",
            str(indoor1),
            "--installation",
            str(install_dir),
            "--game",
            "k1",
            "--log-level",
            "error",
        ]
    )
    assert rc == 0

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
            "k1",
            "--log-level",
            "error",
        ]
    )
    assert rc == 0

    indoor0_raw = indoor0.read_bytes()
    indoor1_raw = indoor1.read_bytes()
    mod1_bytes = mod1.read_bytes()
    mod2_bytes = mod2.read_bytes()
    mod1_payloads = _read_erf_payloads(mod1)
    mod2_payloads = _read_erf_payloads(mod2)

    return RoundtripResult(
        module_root=FIXTURE.module_root,
        install_dir=install_dir,
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
    assert rt.mod1_bytes == rt.mod2_bytes


def test_mim_resource_keys_identical(rt: RoundtripResult):
    assert set(rt.mod1_payloads.keys()) == set(rt.mod2_payloads.keys())


def test_mim_resource_payloads_identical(rt: RoundtripResult):
    for key, b1 in rt.mod1_payloads.items():
        assert b1 == rt.mod2_payloads[key]


def test_mim_has_core_resources(rt: RoundtripResult):
    keys = set(rt.mod1_payloads.keys())
    root = rt.module_root
    assert (root, ResourceType.LYT) in keys
    assert (root, ResourceType.VIS) in keys
    assert (root, ResourceType.ARE) in keys
    assert (root, ResourceType.GIT) in keys
    assert ("module", ResourceType.IFO) in keys


def test_mim_embeds_indoormap(rt: RoundtripResult):
    assert ("indoormap", ResourceType.TXT) in rt.mod1_payloads


def test_mim_embedded_indoormap_matches_extracted(rt: RoundtripResult):
    assert rt.mod1_payloads[("indoormap", ResourceType.TXT)] == rt.indoor1_raw


def test_mim_has_wok(rt: RoundtripResult):
    assert any(restype == ResourceType.WOK for (_r, restype) in rt.mod1_payloads)


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

    assert mats(rt.mod1_payloads) == mats(rt.mod2_payloads)


def test_mim_has_room_model_triplet(rt: RoundtripResult):
    prefix = f"{rt.module_root}_room"
    mdls = [k for k in rt.mod1_payloads if k[1] == ResourceType.MDL and k[0].startswith(prefix)]
    mdxs = [k for k in rt.mod1_payloads if k[1] == ResourceType.MDX and k[0].startswith(prefix)]
    woks = [k for k in rt.mod1_payloads if k[1] == ResourceType.WOK and k[0].startswith(prefix)]
    assert len(mdls) == len(mdxs) == len(woks)
    assert len(mdls) > 0


def test_mim_minimap_exists(rt: RoundtripResult):
    assert (f"lbl_map{rt.module_root}", ResourceType.TGA) in rt.mod1_payloads


def test_mim_git_nonempty(rt: RoundtripResult):
    assert len(rt.mod1_payloads[(rt.module_root, ResourceType.GIT)]) > 0


def test_mim_wok_bytes_identical(rt: RoundtripResult):
    for key, b1 in rt.mod1_payloads.items():
        if key[1] != ResourceType.WOK:
            continue
        assert b1 == rt.mod2_payloads[key]


def test_mim_embedded_indoormap_present_after_roundtrip(rt: RoundtripResult):
    assert ("indoormap", ResourceType.TXT) in rt.mod2_payloads


# -----------------------------
# 15 tests: indoor -> mod -> indoor
# -----------------------------


def test_imi_indoor_bytes_identical(rt: RoundtripResult):
    assert rt.indoor0_raw == rt.indoor1_raw


def test_imi_indoor_json_parses(rt: RoundtripResult):
    _parse_indoor(rt.indoor1_raw)


def test_imi_rooms_present(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    assert "rooms" in d
    assert isinstance(d["rooms"], list)
    assert len(d["rooms"]) > 0


def test_imi_room_fields(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    for room in d["rooms"]:
        assert "position" in room
        assert isinstance(room["position"], list)
        assert len(room["position"]) == 3
        assert "rotation" in room
        assert "flip_x" in room
        assert "flip_y" in room
        assert "kit" in room
        assert "component" in room


def test_imi_module_root_written(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    for room in d["rooms"]:
        assert "module_root" in room
        assert str(room["module_root"]).lower() == rt.module_root


def test_imi_warp_matches(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    assert d.get("warp") == rt.module_root


def test_imi_lighting_triplet(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    lighting = d.get("lighting")
    assert isinstance(lighting, list)
    assert len(lighting) == 3


def test_imi_components_unique(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    comps = [r["component"] for r in d["rooms"]]
    assert len(comps) == len(set(comps))


def test_imi_kit_is_module_root(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    assert all(str(r["kit"]).lower() == rt.module_root for r in d["rooms"])


def test_imi_loadable_with_modulekit(rt: RoundtripResult):
    installation = Installation(CaseAwarePath(rt.install_dir))
    mk = ModuleKitManager(installation)
    indoor = IndoorMap()
    missing = indoor.load(rt.indoor1_raw, [], module_kit_manager=mk)
    assert missing == []
    assert len(indoor.rooms) > 0


def test_imi_positions_finite(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    for room in d["rooms"]:
        x, y, z = room["position"]
        assert abs(float(x)) < 1e9
        assert abs(float(y)) < 1e9
        assert abs(float(z)) < 1e9


def test_imi_rotation_numeric(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    for room in d["rooms"]:
        assert isinstance(room["rotation"], (int, float))


def test_imi_flip_flags_bool(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    for room in d["rooms"]:
        assert isinstance(room["flip_x"], bool)
        assert isinstance(room["flip_y"], bool)


def test_imi_name_shape(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    assert "name" in d
    assert isinstance(d["name"], dict)
    assert "stringref" in d["name"]


def test_imi_target_game_type_optional(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    if "target_game_type" in d:
        assert d["target_game_type"] in (True, False, None)


# -----------------------------
# 20 additional focused checks
# -----------------------------


def test_unit_mod_has_are(rt: RoundtripResult):
    assert (rt.module_root, ResourceType.ARE) in rt.mod1_payloads


def test_unit_mod_has_git(rt: RoundtripResult):
    assert (rt.module_root, ResourceType.GIT) in rt.mod1_payloads


def test_unit_mod_has_vis(rt: RoundtripResult):
    assert (rt.module_root, ResourceType.VIS) in rt.mod1_payloads


def test_unit_mod_has_ifo(rt: RoundtripResult):
    assert ("module", ResourceType.IFO) in rt.mod1_payloads


def test_unit_room_models_have_mdl(rt: RoundtripResult):
    assert any(restype == ResourceType.MDL for (_r, restype) in rt.mod1_payloads)


def test_unit_room_models_have_mdx(rt: RoundtripResult):
    assert any(restype == ResourceType.MDX for (_r, restype) in rt.mod1_payloads)


def test_unit_embedded_indoor_is_utf8(rt: RoundtripResult):
    rt.indoor1_raw.decode("utf-8")


def test_unit_mod_payloads_nonempty(rt: RoundtripResult):
    assert len(rt.mod1_payloads) > 0


def test_unit_indoormap_present_in_payloads(rt: RoundtripResult):
    assert ("indoormap", ResourceType.TXT) in rt.mod1_payloads


def test_unit_wok_count_matches_room_count(rt: RoundtripResult):
    room_count = len(_parse_indoor(rt.indoor1_raw)["rooms"])
    wok_count = sum(
        1 for (_r, t) in rt.mod1_payloads if t == ResourceType.WOK and _r.startswith(f"{rt.module_root}_room")
    )
    assert wok_count == room_count


def test_unit_wok_faces_walkable_present(rt: RoundtripResult):
    any_walkable = False
    for (_resref, restype), data in rt.mod1_payloads.items():
        if restype != ResourceType.WOK:
            continue
        if any(f.material.is_walkable() for f in read_bwm(data).faces):
            any_walkable = True
            break
    assert any_walkable


def test_unit_modulekit_loads_from_install(rt: RoundtripResult):
    installation = Installation(CaseAwarePath(rt.install_dir))
    mk = ModuleKitManager(installation)
    kit = mk.get_module_kit(rt.module_root)
    assert kit.ensure_loaded()


def test_unit_modulekit_components_nonempty(rt: RoundtripResult):
    installation = Installation(CaseAwarePath(rt.install_dir))
    mk = ModuleKitManager(installation)
    kit = mk.get_module_kit(rt.module_root)
    assert kit.ensure_loaded()
    assert len(kit.components) > 0


def test_unit_modulekit_components_have_default_position(rt: RoundtripResult):
    installation = Installation(CaseAwarePath(rt.install_dir))
    mk = ModuleKitManager(installation)
    kit = mk.get_module_kit(rt.module_root)
    assert kit.ensure_loaded()
    for c in kit.components:
        pos = getattr(c, "default_position", None)
        assert pos is not None


def test_unit_modulekit_bwm_centered(rt: RoundtripResult):
    installation = Installation(CaseAwarePath(rt.install_dir))
    mk = ModuleKitManager(installation)
    kit = mk.get_module_kit(rt.module_root)
    assert kit.ensure_loaded()
    for comp in kit.components:
        verts = list(comp.bwm.vertices())
        assert verts
        cx = (min(v.x for v in verts) + max(v.x for v in verts)) / 2.0
        cy = (min(v.y for v in verts) + max(v.y for v in verts)) / 2.0
        assert abs(cx) < 1e-3
        assert abs(cy) < 1e-3


def test_unit_modulekit_hook_edges_int(rt: RoundtripResult):
    installation = Installation(CaseAwarePath(rt.install_dir))
    mk = ModuleKitManager(installation)
    kit = mk.get_module_kit(rt.module_root)
    assert kit.ensure_loaded()
    for comp in kit.components:
        for h in comp.hooks:
            assert isinstance(h.edge, int)


def test_unit_indoor_contains_module_root_field(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    assert all("module_root" in r for r in d["rooms"])


def test_unit_indoor_room_count_positive(rt: RoundtripResult):
    d = _parse_indoor(rt.indoor1_raw)
    assert len(d["rooms"]) > 0


def test_unit_mod_roundtrip_payloads_match(rt: RoundtripResult):
    assert rt.mod1_payloads == rt.mod2_payloads
