"""PyKotor test suite integration shim.

This repository vendors PyKotor for format reference + cross-verification tests.
Some PyKotor tests rely on optional heavyweight inputs (e.g. the
`vendor/Vanilla_KOTOR_Script_Source` submodule) which is not always present.

In upstream PyKotor, these tests use `unittest.TestCase.skipTest()` when the
optional inputs are missing. In this workspace's pytest environment, that skip
path can be misreported as a failure, so we proactively mark those tests as
skipped during collection when their prerequisites are absent.
"""

from __future__ import annotations

import sys
import os

from pathlib import Path

import pytest

# Ensure the vendored PyKotor + Utility sources in this repo are used instead of any
# globally-installed copies that may exist on the machine running the tests.
_PYKOTOR_SRC = Path(__file__).resolve().parents[1] / "src"
_UTILITY_SRC = Path(__file__).resolve().parents[2] / "Utility" / "src"
for _p in (_PYKOTOR_SRC, _UTILITY_SRC):
    _ps = str(_p)
    if _p.exists() and _ps not in sys.path:
        sys.path.insert(0, _ps)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:  # noqa: ARG001
    vanilla_root = Path(__file__).resolve().parents[4] / "vendor" / "Vanilla_KOTOR_Script_Source"
    has_vanilla_sources = vanilla_root.exists()

    if has_vanilla_sources:
        return

    skip_roundtrip = pytest.mark.skip(reason="Vanilla_KOTOR_Script_Source submodule not available")
    for item in items:
        # Skip the one test that depends on the vanilla script source submodule.
        if "test_ncs.py::TestNCSRoundtrip::test_nss_roundtrip" in item.nodeid:
            item.add_marker(skip_roundtrip)


def _discover_game_install_roots() -> list[tuple[str, Path]]:
    """Discover game install roots from env vars.

    - K1: K1_PATH
    - K2: TSL_PATH (preferred) or K2_PATH

    Returned list is stable and de-duplicated.
    """
    roots: list[tuple[str, Path]] = []
    seen: set[str] = set()

    def _add(label: str, value: str | None):
        if not value:
            return
        p = Path(value).expanduser()
        key = str(p.resolve()) if p.exists() else str(p)
        if key in seen:
            return
        seen.add(key)
        roots.append((label, p))

    _add("k1", os.environ.get("K1_PATH"))
    _add("k2", os.environ.get("TSL_PATH") or os.environ.get("K2_PATH"))
    return roots


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize tests that request `game_install_root`.

    This keeps installation-backed tests pytest-native and ensures that if both
    K1 and K2 are configured, tests run once per install.
    """
    if "game_install_root" not in metafunc.fixturenames:
        return

    # `test_mdl_ascii.py::test_models_bif_roundtrip_eq_hash_pytest` provides its own
    # combined parametrization of (game_install_root, mdl_entry) to avoid the
    # cartesian product that would otherwise be created by this hook.
    #
    # If we parametrize `game_install_root` here and `mdl_entry` in the test module,
    # pytest will generate mismatched pairs and skip them at runtime, defeating the
    # whole point of the combined parametrization.
    if "test_mdl_ascii.py::test_models_bif_roundtrip_eq_hash_pytest" in metafunc.definition.nodeid:
        return

    roots = _discover_game_install_roots()
    if not roots:
        metafunc.parametrize(
            "game_install_root",
            [
                pytest.param(
                    ("missing", Path(".")),
                    marks=pytest.mark.skip(
                        reason="Requires K1_PATH and/or TSL_PATH/K2_PATH to be set to a game installation root.",
                    ),
                    id="missing-install",
                ),
            ],
            indirect=True,
        )
        return

    params = [pytest.param(r, id=r[0]) for r in roots]
    metafunc.parametrize("game_install_root", params, indirect=True)


@pytest.fixture
def game_install_root(request: pytest.FixtureRequest) -> tuple[str, Path]:
    """(label, root_path) for a game installation, parameterized via pytest_generate_tests."""
    label, root = request.param
    key_path = root / "chitin.key"
    if not key_path.exists():
        pytest.skip(f"{label}: missing chitin.key at {key_path}")
    return label, root
