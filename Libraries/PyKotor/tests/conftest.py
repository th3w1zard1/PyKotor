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
