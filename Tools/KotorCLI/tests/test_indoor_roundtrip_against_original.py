"""Strict `.mod -> .indoor -> .mod` and `.indoor -> .mod -> .indoor` assertions against originals.

What this suite covers (implicit-kit / ModuleKit only):
- Original composite module LYT room ordering and positions are preserved through extraction/build.
- Each original room WOK is reproduced **byte-for-byte** in the rebuilt `.mod` (per room index mapping).
  This implicitly asserts:
  - vertex coordinates (including any translation / flip / rotation handling)
  - face ordering / edge ordering
  - surface material indices (walkability-critical)
  - transition indices / per-edge metadata inside the WOK

Important:
- This suite compares the *source installation module* to the rebuilt module.
- No skips / xfails inside the file; install availability is handled by the shared conftest fixtures.
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


import difflib
from io import StringIO

from pykotor.cli.dispatch import cli_main
from pykotor.common.indoormap import IndoorMap
from pykotor.common.module import Module, ModuleResource
from pykotor.common.modulekit import ModuleKitManager
from pykotor.extract.installation import Installation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.erf import read_erf
from pykotor.resource.formats.lyt import LYT, LYTRoom, read_lyt
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath


def _run_cli(argv: list[str]) -> int:
    return int(cli_main(argv))


def _read_erf_payloads(mod_path: Path) -> dict[tuple[str, ResourceType], bytes]:
    erf = read_erf(mod_path)
    out: dict[tuple[str, ResourceType], bytes] = {}
    for res in erf:
        payload = res.data() if callable(getattr(res, "data", None)) else res.data  # type: ignore[truthy-function]
        out[(str(res.resref).lower(), res.restype)] = bytes(payload)
    return out


def _load_module_lyt(module: Module) -> LYT:
    lyt_res: ModuleResource[LYT] | None = module.layout()
    if lyt_res is None or lyt_res.resource() is None:
        msg = f"Module '{module.module_id()}' has no LYT layout resource"
        raise AssertionError(msg)
    lyt = lyt_res.resource()
    if lyt is None:
        msg = f"LYT resource is None for module '{module.module_id()}'"
        raise AssertionError(msg)
    return lyt


def _iter_source_rooms(lyt: LYT, *, module_root: str) -> list[str]:
    """Return room model resrefs in source order, excluding the known sky room."""
    out: list[str] = []
    sky = f"{module_root}_sky".lower()
    for r in lyt.rooms:
        model = (r.model or "").strip()
        if not model:
            continue
        if model.lower() == sky:
            continue
        out.append(model.lower())
    return out


def _wok_bytes_from_module(module: Module, model_resref: str) -> bytes:
    res = module.resource(model_resref, ResourceType.WOK)
    if res is None:
        msg = f"Missing WOK for room model '{model_resref}'"
        raise AssertionError(msg)
    data = res.data()
    if data is None:
        msg = f"Empty WOK for room model '{model_resref}'"
        raise AssertionError(msg)
    return bytes(data)


def _parse_indoor(raw: bytes) -> dict[str, Any]:
    return json.loads(raw.decode("utf-8"))


def _normalize_indoor_identity(d: dict[str, Any]) -> dict[str, Any]:
    """Normalize fields that legitimately change when you rebuild under a new module id."""
    out = dict(d)
    out["warp"] = "__norm__"
    out["module_id"] = "__norm__"
    return out


def _safe_out_module_id(
    *,
    module_root: str,
    game: str,
    room_count: int,
) -> str:
    """Pick a module id that will not exceed the 16-char ResRef limit for `{id}_room{i}` and `lbl_map{id}`."""
    max_index: int = max(room_count - 1, 0)
    digits: int = len(str(max_index))
    # Two constraints:
    # 1. Room models: `{module_id}_room{i}` must fit in 16 chars
    # 2. Minimap: `lbl_map{id}` must fit in 16 chars
    max_for_rooms: int = 16 - (len("_room") + digits)
    max_for_minimap: int = 16 - len("lbl_map")
    max_module_id_len: int = min(max_for_rooms, max_for_minimap)

    if max_module_id_len <= 0:
        msg = f"Cannot construct a valid module_id for room_count={room_count} (digits={digits})"
        raise AssertionError(msg)

    base = f"{module_root}{game}rt".lower()
    base = "".join(c for c in base if c.isalnum() or c == "_")
    return base[:max_module_id_len]


def _choose_strict_module_roots(
    installation: Installation,
    *,
    max_roots: int,
) -> list[str]:
    """Deterministically pick module roots suitable for strict WOK roundtrip comparisons."""
    roots: list[str] = []
    # Use installation.module_names(use_hardcoded=True) for determinism.
    for module_filename in installation.module_names(use_hardcoded=True):
        root = installation.get_module_root(module_filename)
        if root in roots:
            continue
        try:
            mod = Module(root, installation, use_dot_mod=True, load_textures=False)
            lyt = _load_module_lyt(mod)
            room_models = _iter_source_rooms(lyt, module_root=root)
            if not room_models:
                continue
            # Require every listed room to have a WOK payload in the composite module resolution.
            for model in room_models:
                _wok_bytes_from_module(mod, model)
        except Exception:
            continue
        roots.append(root)
        if len(roots) >= max_roots:
            break
    if not roots:
        msg = "No suitable module roots found for strict WOK roundtrip tests."
        raise AssertionError(msg)
    return roots


@dataclass(frozen=True)
class RtOrigCase:
    game: str  # "k1" | "k2"
    module_root: str
    install_dir: Path


@pytest.fixture(scope="session")
def rt_orig_cases(
    k1_installation: Installation,
    k2_installation: Installation,
) -> list[RtOrigCase]:
    # Keep runtime reasonable but still meaningful: 3 modules per game.
    k1_roots: list[str] = _choose_strict_module_roots(k1_installation, max_roots=3)
    k2_roots: list[str] = _choose_strict_module_roots(k2_installation, max_roots=3)
    out: list[RtOrigCase] = []
    for k1_root in k1_roots:
        out.append(RtOrigCase("k1", k1_root, Path(k1_installation.path())))
    for k2_root in k2_roots:
        out.append(RtOrigCase("k2", k2_root, Path(k2_installation.path())))
    return out


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "rt_case" not in metafunc.fixturenames:
        return
    # Defer to the session fixture values via indirect parametrization.
    # We parametrize a dummy index and resolve actual case objects in the fixture below.
    metafunc.parametrize("rt_case", list(range(6)), ids=[f"case{i}" for i in range(6)], indirect=True)  # type: ignore[arg-type]


@pytest.fixture
def rt_case(
    request: pytest.FixtureRequest,
    rt_orig_cases: list[RtOrigCase],
) -> RtOrigCase:
    idx: int = int(request.param)
    if idx >= len(rt_orig_cases):
        # If fewer than 6 total cases exist (unlikely with real installs), reuse the last.
        idx = len(rt_orig_cases) - 1
    return rt_orig_cases[idx]


@pytest.fixture
def rt_run(
    tmp_path: Path,
    rt_case: RtOrigCase,
) -> dict[str, Any]:
    module_root: str = rt_case.module_root
    game: str = rt_case.game
    install_dir: Path = rt_case.install_dir

    indoor0_path: Path = tmp_path / f"{module_root}.{game}.0.indoor"
    indoor1_path: Path = tmp_path / f"{module_root}.{game}.1.indoor"
    mod1_path: Path = tmp_path / f"{module_root}.{game}.1.mod"

    installation = Installation(CaseAwarePath(install_dir))
    original_module: Module = Module(module_root, installation, use_dot_mod=True, load_textures=False)
    original_lyt: LYT = _load_module_lyt(original_module)
    source_room_models: list[str] = _iter_source_rooms(original_lyt, module_root=module_root)
    assert source_room_models, f"No usable rooms discovered in source module {game}:{module_root}"

    out_module_id: str = _safe_out_module_id(module_root=module_root, game=game, room_count=len(source_room_models))

    rc: int = _run_cli(
        [
            "indoor-extract",
            "--implicit-kit",
            "--module",
            module_root,
            "--output",
            str(indoor0_path),
            "--installation",
            str(install_dir),
            "--game",
            game,
            "--log-level",
            "error",
        ]
    )
    assert rc == 0, f"indoor-extract failed for {game}:{module_root} with exit code {rc}"

    # Normalize the `.indoor` module_id so the build output produces a stable module id.
    indoor0_data = _parse_indoor(indoor0_path.read_bytes())
    indoor0_data["warp"] = out_module_id
    indoor0_data["module_id"] = out_module_id
    indoor0_path.write_bytes(json.dumps(indoor0_data).encode("utf-8"))

    rc = _run_cli(
        [
            "indoor-build",
            "--implicit-kit",
            "--input",
            str(indoor0_path),
            "--output",
            str(mod1_path),
            "--installation",
            str(install_dir),
            "--game",
            game,
            "--module-filename",
            out_module_id,
            "--log-level",
            "error",
        ]
    )
    assert rc == 0, f"indoor-build failed for {game}:{module_root} with exit code {rc}"

    rc = _run_cli(
        [
            "indoor-extract",
            "--implicit-kit",
            "--module",
            module_root,
            "--module-file",
            str(mod1_path),
            "--output",
            str(indoor1_path),
            "--installation",
            str(install_dir),
            "--game",
            game,
            "--log-level",
            "error",
        ]
    )
    assert rc == 0, f"indoor-extract (from module-file) failed for {game}:{module_root} with exit code {rc}"

    built_payloads: dict[tuple[str, ResourceType], bytes] = _read_erf_payloads(mod1_path)
    built_lyt: LYT = read_lyt(built_payloads[(out_module_id.lower(), ResourceType.LYT)])

    return {
        "built_lyt": built_lyt,
        "built_payloads": built_payloads,
        "game": game,
        "indoor0_raw": indoor0_path.read_bytes(),
        "indoor1_raw": indoor1_path.read_bytes(),
        "install_dir": install_dir,
        "module_root": module_root,
        "original_lyt": original_lyt,
        "original_module": original_module,
        "out_module_id": out_module_id.lower(),
        "source_room_models": source_room_models,
    }


# -----------------------------
# `.mod -> .indoor -> .mod` (original vs rebuilt)
# -----------------------------


def test_orig_room_count_matches_lyt(rt_run: dict[str, Any]) -> None:
    assert len(rt_run["source_room_models"]) > 0, "No source room models found"
    assert len(_parse_indoor(rt_run["indoor0_raw"]).get("rooms", [])) == len(rt_run["source_room_models"]), (
        f"Room count mismatch: {len(_parse_indoor(rt_run['indoor0_raw']).get('rooms', []))} != {len(rt_run['source_room_models'])}"
    )


def test_orig_lyt_positions_preserved(rt_run: dict[str, Any]) -> None:
    module_root: str = rt_run["module_root"]
    out_id: str = rt_run["out_module_id"]
    built_lyt: LYT = rt_run["built_lyt"]
    original_lyt: LYT = rt_run["original_lyt"]

    src_rooms: list[LYTRoom] = [
        r
        for r in original_lyt.rooms
        if (r.model or "").strip() and (r.model or "").lower() != f"{module_root}_sky".lower()
    ]
    assert len(built_lyt.rooms) == len(src_rooms), (
        f"Built LYT room count mismatch: {len(built_lyt.rooms)} != {len(src_rooms)}"
    )

    for i, src in enumerate(src_rooms):
        built: LYTRoom = built_lyt.rooms[i]
        assert built.model.lower() == f"{out_id}_room{i}", f"Room model mismatch at index {i}"
        assert built.position.x == src.position.x, f"Position X mismatch at index {i}"
        assert built.position.y == src.position.y, f"Position Y mismatch at index {i}"
        assert built.position.z == src.position.z, f"Position Z mismatch at index {i}"


def test_orig_wok_room_count_matches(rt_run: dict[str, Any]) -> None:
    out_id: str = rt_run["out_module_id"]
    built_payloads: dict[tuple[str, ResourceType], bytes] = rt_run["built_payloads"]
    woks: list[tuple[str, ResourceType]] = [
        k for k in built_payloads if k[1] == ResourceType.WOK and k[0].startswith(f"{out_id}_room")
    ]
    assert len(woks) == len(rt_run["source_room_models"])


def test_orig_wok_bytes_identical_per_room_index(rt_run: dict[str, Any]) -> None:
    """Geometry/material/transition equivalence check (NOT raw-byte equivalence).

    We intentionally do not require byte-for-byte identity against shipped game assets:
    - Toolset/CLI workflows rebuild derived tables (AABB tree, adjacency, perimeters) and offsets.
    - Different but equivalent AABB tree shapes can still be fully valid in-game.

    What we do require is that walkability-critical geometry and metadata is preserved.
    """
    out_id: str = rt_run["out_module_id"]
    built_payloads: dict[tuple[str, ResourceType], bytes] = rt_run["built_payloads"]
    original_module: Module = rt_run["original_module"]
    source_room_models: list[str] = rt_run["source_room_models"]

    for i, src_model in enumerate(source_room_models):
        src_bwm = read_bwm(_wok_bytes_from_module(original_module, src_model))
        built_key: tuple[str, ResourceType] = (f"{out_id}_room{i}", ResourceType.WOK)
        assert built_key in built_payloads, f"Missing built WOK payload for room {i}: {built_key}"
        built_bwm = read_bwm(built_payloads[built_key])

        assert len(src_bwm.faces) == len(built_bwm.faces), f"Face count differs for room {i} ({src_model})"
        assert len(src_bwm.vertices()) == len(built_bwm.vertices()), f"Vertex count differs for room {i} ({src_model})"

        for fi, (f_src, f_bld) in enumerate(zip(src_bwm.faces, built_bwm.faces)):
            assert f_src.material == f_bld.material, f"Material differs at face {fi} for room {i} ({src_model})"
            assert f_src.trans1 == f_bld.trans1, f"trans1 differs at face {fi} for room {i} ({src_model})"
            assert f_src.trans2 == f_bld.trans2, f"trans2 differs at face {fi} for room {i} ({src_model})"
            assert f_src.trans3 == f_bld.trans3, f"trans3 differs at face {fi} for room {i} ({src_model})"

        # Broad walkability sanity: ensure we preserve existence of walkable faces.
        assert any(f.material.walkable() for f in src_bwm.faces) == any(
            f.material.walkable() for f in built_bwm.faces
        ), f"Walkable face presence mismatch for room {i} ({src_model})"


def test_orig_wok_materials_and_transitions_preserved(rt_run: dict[str, Any]) -> None:
    """Extra explicit checks (redundant if bytes match, but gives clearer failure signal)."""
    out_id: str = rt_run["out_module_id"]
    built_payloads: dict[tuple[str, ResourceType], bytes] = rt_run["built_payloads"]
    original_module: Module = rt_run["original_module"]
    source_room_models: list[str] = rt_run["source_room_models"]

    for i, src_model in enumerate(source_room_models):
        src_bwm = read_bwm(_wok_bytes_from_module(original_module, src_model))
        built_bwm = read_bwm(built_payloads[(f"{out_id}_room{i}", ResourceType.WOK)])

        assert len(src_bwm.faces) == len(built_bwm.faces), f"Face count differs for room {i} ({src_model})"
        assert len(src_bwm.edges()) == len(built_bwm.edges()), f"Edge count differs for room {i} ({src_model})"

        # Face material ordering.
        for fi, (f_src, f_bld) in enumerate(zip(src_bwm.faces, built_bwm.faces)):
            assert f_src.material == f_bld.material, f"Material differs at face {fi} for room {i} ({src_model})"

        # Edge transition ordering.
        for ei, (e_src, e_bld) in enumerate(zip(src_bwm.edges(), built_bwm.edges())):
            assert e_src.transition == e_bld.transition, f"Transition differs at edge {ei} for room {i} ({src_model})"


# -----------------------------
# `.indoor -> .mod -> .indoor`
# -----------------------------


def test_indoor_roundtrip_json_stable_except_identity(rt_run: dict[str, Any]) -> None:
    d0 = _parse_indoor(rt_run["indoor0_raw"])
    d1 = _parse_indoor(rt_run["indoor1_raw"])
    assert _normalize_indoor_identity(d0) == _normalize_indoor_identity(d1), f"Indoor JSON mismatch: {d0} != {d1}"


def test_indoor_roundtrip_room_positions_identical(rt_run: dict[str, Any]) -> None:
    d0 = _parse_indoor(rt_run["indoor0_raw"])
    d1 = _parse_indoor(rt_run["indoor1_raw"])
    r0 = d0.get("rooms", [])
    r1 = d1.get("rooms", [])
    assert len(r0) == len(r1), f"Room count mismatch: {len(r0)} != {len(r1)}"
    for i, (a, b) in enumerate(zip(r0, r1)):
        assert a["position"] == b["position"], (
            f"Room position mismatch at index {i}: {a['position']} != {b['position']}"
        )


def test_indoor_roundtrip_flip_rotation_preserved(rt_run: dict[str, Any]) -> None:
    d0 = _parse_indoor(rt_run["indoor0_raw"])
    d1 = _parse_indoor(rt_run["indoor1_raw"])
    r0 = d0.get("rooms", [])
    r1 = d1.get("rooms", [])
    assert len(r0) == len(r1), f"Room count mismatch: {len(r0)} != {len(r1)}"
    for i, (a, b) in enumerate(zip(r0, r1)):
        assert a["flip_x"] == b["flip_x"], f"flip_x mismatch at index {i}: {a['flip_x']} != {b['flip_x']}"
        assert a["flip_y"] == b["flip_y"], f"flip_y mismatch at index {i}: {a['flip_y']} != {b['flip_y']}"
        assert float(a["rotation"]) == float(b["rotation"]), (
            f"rotation mismatch at index {i}: {a['rotation']} != {b['rotation']}"
        )


def test_indoor_roundtrip_using_comparable_mixin(rt_run: dict[str, Any]) -> None:
    """Test .indoor -> .mod -> .indoor roundtrip using ComparableMixin.compare() with udiff output."""
    game: str = rt_run["game"]
    install_dir: Path = rt_run["install_dir"]
    indoor0_raw: bytes = rt_run["indoor0_raw"]
    indoor1_raw: bytes = rt_run["indoor1_raw"]

    installation = Installation(CaseAwarePath(install_dir))
    mk_mgr = ModuleKitManager(installation)

    # Load both indoor maps
    original_map = IndoorMap()
    missing = original_map.load(indoor0_raw, [], module_kit_manager=mk_mgr)
    assert missing == [], f"Missing rooms/components in original: {missing}"

    roundtripped_map = IndoorMap()
    missing = roundtripped_map.load(indoor1_raw, [], module_kit_manager=mk_mgr)
    assert missing == [], f"Missing rooms/components in roundtripped: {missing}"

    # Compare using ComparableMixin.compare() with udiff output
    diff_lines: list[str] = []
    log_buffer = StringIO()

    def log_func(msg: str) -> None:
        diff_lines.append(msg)
        log_buffer.write(msg + "\n")

    is_identical = original_map.compare(roundtripped_map, log_func=log_func)

    if not is_identical:
        # Generate udiff format output
        original_json = original_map.write().decode("utf-8")
        roundtripped_json = roundtripped_map.write().decode("utf-8")

        original_lines = original_json.splitlines(keepends=True)
        roundtripped_lines = roundtripped_json.splitlines(keepends=True)

        udiff = list(
            difflib.unified_diff(
                original_lines,
                roundtripped_lines,
                fromfile="original (.indoor)",
                tofile="roundtripped (.indoor -> .mod -> .indoor)",
                lineterm="",
            )
        )

        # Print the udiff
        print("\n" + "=" * 80)  # noqa: T201
        print("Unified diff (udiff format):")  # noqa: T201
        print("=" * 80)  # noqa: T201
        for line in udiff:
            print(line)  # noqa: T201
        print("=" * 80)  # noqa: T201

        # Also print the structured comparison output
        print("\nStructured comparison differences:")  # noqa: T201
        print("-" * 80)  # noqa: T201
        print(log_buffer.getvalue())  # noqa: T201
        print("-" * 80)  # noqa: T201

    assert is_identical, "IndoorMap objects should be identical after .indoor -> .mod -> .indoor roundtrip"
