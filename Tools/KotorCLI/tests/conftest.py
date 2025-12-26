from __future__ import annotations

import os
from pathlib import Path

import pytest
from pykotor.extract.installation import Installation
from pykotor.tools.path import CaseAwarePath


def _load_dotenv_if_present() -> None:
    """Load repo-root `.env` into `os.environ` if it exists.

    We intentionally avoid external deps (python-dotenv) in the test runner.
    """
    # This conftest lives at Tools/KotorCLI/tests/ → repo root is 3 parents up.
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.exists() or not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


_load_dotenv_if_present()

import cProfile
import pstats
import re
from typing import Iterator


def _profile_threshold_ms() -> int:
    raw = os.environ.get("PYKOTOR_PROFILE_SLOW_MS", "0").strip()
    try:
        return int(raw)
    except ValueError:
        return 0


def _safe_name(nodeid: str) -> str:
    s = nodeid.replace("::", "__")
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", s)
    return s[:180]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: pytest.Item) -> Iterator[None]:
    """If enabled, dump cProfile for slow tests.

    Set `PYKOTOR_PROFILE_SLOW_MS=5000` to profile any test taking >= 5s (call phase).
    Outputs go to `<repo_root>/profiling/`.
    """
    threshold = _profile_threshold_ms()
    if threshold <= 0:
        yield
        return

    profiler = cProfile.Profile()
    profiler.enable()
    yield
    profiler.disable()

    rep = getattr(item, "rep_call", None)
    dur_ms = int(rep.duration * 1000) if rep is not None else None
    if dur_ms is not None and dur_ms < threshold:
        return

    out_dir = Path(__file__).resolve().parents[3] / "profiling"
    out_dir.mkdir(parents=True, exist_ok=True)

    base = _safe_name(item.nodeid)
    pstat_path = out_dir / f"{base}.pstat"
    txt_path = out_dir / f"{base}.txt"

    profiler.dump_stats(str(pstat_path))
    with txt_path.open("w", encoding="utf-8") as f:
        stats = pstats.Stats(profiler, stream=f)
        stats.strip_dirs()
        stats.sort_stats("cumulative")
        f.write(f"nodeid: {item.nodeid}\n")
        f.write(f"threshold_ms: {threshold}\n\n")
        stats.print_stats(60)
        f.write("\n\n---- callers (top 30) ----\n")
        stats.print_callers(30)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):  # type: ignore[no-untyped-def]  # noqa: ARG001
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        item.rep_call = rep  # type: ignore[attr-defined]
    return rep


def _require_installation_path(env_var: str) -> Path:
    value = os.environ.get(env_var)
    if not value:
        pytest.skip(f"{env_var} not set (ensure `.env` is loaded or set the env var).")
    p = Path(value)
    if not p.is_dir():
        pytest.skip(f"{env_var} path does not exist or is not a directory: {p}")
    # We require chitin.key for a real install.
    if not p.joinpath("chitin.key").exists() or not p.joinpath("chitin.key").is_file():
        pytest.skip(f"{env_var} does not look like a real install (missing chitin.key): {p}")
    return p


@pytest.fixture(scope="session")
def k1_installation() -> Installation:
    k1_path = _require_installation_path("K1_PATH")
    return Installation(CaseAwarePath(k1_path))


@pytest.fixture(scope="session")
def k2_installation() -> Installation:
    # Accept either K2_PATH or TSL_PATH (repo convention).
    k2_env = os.environ.get("K2_PATH") or os.environ.get("TSL_PATH")
    assert k2_env, "K2_PATH or TSL_PATH is required for these tests (set it to your KOTOR2 installation directory)."
    k2_path = Path(k2_env)
    assert k2_path.is_dir(), f"K2_PATH/TSL_PATH path does not exist or is not a directory: {k2_path}"
    assert k2_path.joinpath(
        "chitin.key"
    ).is_file(), f"K2_PATH/TSL_PATH does not look like a real install (missing chitin.key): {k2_path}"
    return Installation(CaseAwarePath(k2_path))


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate one test per module root in the real installations (no skips)."""

    if "module_case" not in metafunc.fixturenames:
        return

    cases: list[tuple[str, str]] = []
    ids: list[str] = []

    k1_path = _require_installation_path("K1_PATH")
    # If skipped above, pytest will never reach here.
    k1_install = Installation(CaseAwarePath(k1_path))
    for module_filename in k1_install.module_names(use_hardcoded=True):
        root = k1_install.get_module_root(module_filename)
        key = ("k1", root)
        if key in cases:
            continue
        cases.append(key)
        ids.append(f"k1:{root}")

    # K2 is optional: if not present, we just won't generate K2 cases.
    k2_env = os.environ.get("K2_PATH") or os.environ.get("TSL_PATH")
    if not k2_env:
        metafunc.parametrize("module_case", cases, ids=ids)  # type: ignore[arg-type]
        return
    k2_path = Path(k2_env)
    if not k2_path.joinpath("chitin.key").is_file():
        metafunc.parametrize("module_case", cases, ids=ids)  # type: ignore[arg-type]
        return
    k2_install = Installation(CaseAwarePath(k2_path))
    for module_filename in k2_install.module_names(use_hardcoded=True):
        root = k2_install.get_module_root(module_filename)
        key = ("k2", root)
        if key in cases:
            continue
        cases.append(key)
        ids.append(f"k2:{root}")

    metafunc.parametrize("module_case", cases, ids=ids)  # type: ignore[arg-type]
