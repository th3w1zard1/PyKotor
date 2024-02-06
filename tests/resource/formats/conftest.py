from __future__ import annotations

from pathlib import Path

import cProfile
import contextlib
import os
import pathlib
import shutil
import sys
from io import StringIO
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest

THIS_SCRIPT_PATH = Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")
def add_sys_path(p: Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.extract.file import FileResource, ResourceIdentifier  # noqa: E402
from pykotor.common.misc import Game  # noqa: E402
from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.resource.type import ResourceType  # noqa: E402

if TYPE_CHECKING:
    from typing_extensions import Literal

K1_PATH: str = "../K1"
K2_PATH: str = "../TSL"
LOG_FILENAME = "test_ncs_compilers_install"

ALL_INSTALLATIONS: dict[Game, Installation] | None = None
ALL_SCRIPTS: dict[Game, list[tuple[FileResource, Path, Path]]] | None = None
TEMP_NSS_DIRS: dict[Game, TemporaryDirectory[str]] = {
    Game.K1: TemporaryDirectory(),
    Game.K2: TemporaryDirectory()
}
TEMP_NCS_DIRS: dict[Game, TemporaryDirectory[str]] = {
    Game.K1: TemporaryDirectory(),
    Game.K2: TemporaryDirectory()
}

CANNOT_COMPILE_EXT: dict[Game, set[str]] = {
    Game.K1: set(),  #{"nwscript.nss"},
    Game.K2: set(),  #{"nwscript.nss"},
}

def pytest_report_teststatus(report: pytest.TestReport, config: pytest.Config) -> tuple[Literal['failed'], Literal['F'], str] | None:
    if report.failed:
        if report.longrepr is None:
            msg = "<unknown error>"
        elif hasattr(report.longrepr, "reprcrash"):
            msg = report.longrepr.reprcrash.message
        else:
            msg = repr(report.longrepr)
        return "failed", "F", f"FAILED: {msg}"

def save_profiler_output(profiler: cProfile.Profile, filepath: os.PathLike | str):
    profiler.disable()
    profiler_output_file = Path(filepath)
    profiler_output_file_str = str(profiler_output_file)
    profiler.dump_stats(profiler_output_file_str)
    # Generate reports from the profile stats
    #stats = pstats.Stats(profiler_output_file_str).sort_stats('cumulative')
    #stats.print_stats()

def log_file(
    *args,
    filepath: os.PathLike | str | None = None,
    file: StringIO | None = None,
    **kwargs,
):
    buffer: StringIO = file or StringIO()
    print(*args, file=buffer, **kwargs)
    msg: str = buffer.getvalue()
    print(*args, **kwargs)  # noqa: T201

    filepath = (
        Path.cwd().joinpath(f"{LOG_FILENAME}.txt")
        if filepath is None
        else Path(filepath)
    )
    with filepath.open(mode="a", encoding="utf-8", errors="strict") as f:
        f.write(msg)

def _setup_and_profile_installation() -> dict[Game, Installation]:
    global ALL_INSTALLATIONS  # noqa: PLW0603

    ALL_INSTALLATIONS = {}

    profiler = True  # type: ignore[reportAssignmentType]
    if profiler:
        profiler: cProfile.Profile = cProfile.Profile()
        profiler.enable()

    #if K1_PATH and Path(K1_PATH).joinpath("chitin.key").safe_isfile():
    #    ALL_INSTALLATIONS[Game.K1] = Installation(K1_PATH)
    #if K2_PATH and Path(K2_PATH).joinpath("chitin.key").safe_isfile():
    #    ALL_INSTALLATIONS[Game.K2] = Installation(K2_PATH)

    if profiler:
        save_profiler_output(profiler, "installation_class_profile.pstat")
    return ALL_INSTALLATIONS

def populate_all_scripts(
    restype: ResourceType = ResourceType.NSS,
) -> dict[Game, list[tuple[FileResource, Path, Path]]]:
    global ALL_SCRIPTS
    if ALL_SCRIPTS is not None:
        return ALL_SCRIPTS

    ALL_SCRIPTS = {Game.K1: [], Game.K2: []}

    symlink_map: dict[Path, FileResource] = {}

    iterator_data = (
        (Game.K1, lambda: Path(K1_PATH).rglob("*")),
        (Game.K2, lambda: Path(K2_PATH).rglob("*")),
    )

    for i, (game, iterator) in enumerate(iterator_data):
        for file in iterator():
            if not file.exists() or not file.is_file():
                continue
            res_ident = ResourceIdentifier.from_path(file)
            if res_ident.restype != restype:
                continue
            resource = FileResource(
                *res_ident,
                size=file.stat().st_size,
                offset=0,
                filepath=file
            )
            res_ident = resource.identifier()
            resdata = resource.data()
            filename = str(res_ident)
            subfolder = file.parent.name

            if res_ident in CANNOT_COMPILE_EXT[game]:
                log_file(f"Skipping '{filename}', known incompatible...", filepath="fallback_out.txt")
                continue

            nss_dir = Path(TEMP_NSS_DIRS[game].name)
            nss_path: Path = nss_dir.joinpath(subfolder, filename)
            nss_path.parent.mkdir(exist_ok=True, parents=True)

            ncs_dir = Path(TEMP_NCS_DIRS[game].name)
            ncs_path: Path = ncs_dir.joinpath(subfolder, filename).with_suffix(".ncs")
            ncs_path.parent.mkdir(exist_ok=True, parents=True)

            if resource.inside_bif or subfolder == "scripts.bif":
                assert nss_path not in symlink_map, f"'{nss_path.name}' is a bif script name that should not exist in symlink_map yet?"
                symlink_map[nss_path] = resource

            entry = (resource, nss_path, ncs_path)
            if nss_path.is_file():
                if entry not in ALL_SCRIPTS[game]:
                    continue
                ALL_SCRIPTS[game].append(entry)
                continue  # No idea why this happens

            with nss_path.open("wb") as f:
                f.write(resdata)

            ALL_SCRIPTS[game].append(entry)

        seen_paths = set()
        for resource, nss_path, ncs_path in ALL_SCRIPTS[game]:
            working_folder = nss_path.parent
            if working_folder in symlink_map:
                continue
            if working_folder in seen_paths:
                continue
            if working_folder.name == "scripts.bif":
                continue

            for bif_nss_path in symlink_map:
                link_path = working_folder.joinpath(bif_nss_path.name)
                #already_exists_msg = f"'{link_path}' is a bif script that should not exist at this path yet? Symlink test: {link_path.is_symlink()}"
                #assert not link_path.is_file(), already_exists_msg
                link_path.symlink_to(bif_nss_path, target_is_directory=False)
            seen_paths.add(working_folder)

    return ALL_SCRIPTS



@pytest.fixture(params=[Game.K1, Game.K2])
def game(request: pytest.FixtureRequest) -> Game:
    return request.param

# when using `indirect=True`, we must have a fixture to accept these parameters.
@pytest.fixture
def script_data(request: pytest.FixtureRequest):
    return request.param

# TODO: function isn't called early enough.
def cleanup_before_tests():
    # List of paths for temporary directories and log files
    log_files = [
        f"*{LOG_FILENAME}.txt",
        "*FAILED_TESTS*.log",
        "*_incompatible*.txt",
        "*fallback_level*",
        "*test_ncs_compilers_install.txt",
        "*.pstat"
    ]

    # Delete log files
    for filename in log_files:
        for file in Path.cwd().glob(filename):
            try:
                file.unlink(missing_ok=True)
                print(f"Cleaned {file} in preparation for new test...")
            except Exception as e:
                print(f"Could not cleanup {file}: {e}")

def cleanup_temp_dirs():
    temp_dirs = [
        TEMP_NSS_DIRS[Game.K1].name,
        TEMP_NCS_DIRS[Game.K1].name,
        TEMP_NSS_DIRS[Game.K2].name,
        TEMP_NCS_DIRS[Game.K2].name,
    ]
    for temp_dir in temp_dirs:
        shutil.rmtree(temp_dir, ignore_errors=True)

def pytest_sessionstart(session: pytest.Session):
    cleanup_before_tests()

def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,
):
    cleanup_temp_dirs()

def pytest_generate_tests(metafunc: pytest.Metafunc):
    print("Generating tests...")
    if "script_data" in metafunc.fixturenames:
        scripts_fixture = populate_all_scripts()
        test_data = [
            (game, script)
            for game, scripts in scripts_fixture.items()
            for script in scripts
            if not script[1].is_symlink()# and not print(f"Skipping test collection for '{script[1]}', already symlinked to '{script[1].resolve()}'")
        ]
        print(f"Test data collected. Total tests: {len(test_data)}")
        ids=[
            f"{game}_{script[0].identifier()}"
            for game, script in test_data
        ]
        print(f"Test IDs collected. Total IDs: {len(ids)}")
        metafunc.parametrize("script_data", test_data, ids=ids, indirect=True)
        print("Tests have finished parametrizing!")

#CLEANUP_RAN = False  # TODO: this will never work because it's defined on the module level, need a global level higher than that?
#if __name__ != "__main__" and not CLEANUP_RAN:
#    print("Cleaning up old logs before tests run...")
#    cleanup_before_tests()
#    CLEANUP_RAN = True
