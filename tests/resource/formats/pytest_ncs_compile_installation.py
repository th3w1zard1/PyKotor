from __future__ import annotations

import cProfile
import os
import pathlib
import sys
from io import StringIO
from typing import TYPE_CHECKING

import pytest

from pykotor.extract.file import ResourceIdentifier

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.common.misc import Game  # noqa: E402
from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS  # noqa: E402
from pykotor.common.scriptlib import KOTOR_LIBRARY, TSL_LIBRARY  # noqa: E402
from pykotor.resource.formats.ncs.compiler.classes import CompileError, EntryPointError  # noqa: E402
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer  # noqa: E402
from pykotor.resource.formats.ncs.compiler.parser import NssParser  # noqa: E402
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler, InbuiltNCSCompiler  # noqa: E402
from pykotor.resource.formats.ncs.ncs_auto import compile_nss, write_ncs  # noqa: E402
from pykotor.resource.formats.ncs.ncs_data import NCS, NCSCompiler  # noqa: E402
from utility.error_handling import format_exception_with_variables, universal_simplify_exception  # noqa: E402
from utility.system.path import Path  # noqa: E402

if TYPE_CHECKING:
    from ply import yacc
    from pykotor.extract.file import FileResource

TSLPATCHER_NWNNSSCOMP_PATH: str = "../<game>/nwnnsscomp/TSLPatcher/nwnnsscomp.exe"
LOG_FILENAME = "test_ncs_compilers_install"

def log_file(
    *args,
    filepath: os.PathLike | str | None = None,
    file: StringIO | None = None,
    **kwargs,
):
    # Create an in-memory text stream
    buffer: StringIO = file or StringIO()
    # Print to the in-memory stream
    print(*args, file=buffer, **kwargs)

    # Retrieve the printed content
    msg: str = buffer.getvalue()

    # Print the captured output to console
    print(*args, **kwargs)  # noqa: T201

    filepath = (
        Path.cwd().joinpath(f"{LOG_FILENAME}.txt")
        if filepath is None
        else Path.pathify(filepath)
    )
    with filepath.open(mode="a", encoding="utf-8", errors="strict") as f:
        f.write(msg)

def bizarre_compiler(
    script: str,
    game: Game,
    library: dict[str, bytes] | None = None,
    library_lookup: list[str | Path] | list[str] | list[Path] | str | Path | None = None,
) -> NCS:
    if not library:
        library = KOTOR_LIBRARY if game == Game.K1 else TSL_LIBRARY
    _nssLexer = NssLexer()
    nssParser = NssParser(
        library=library,
        constants=KOTOR_CONSTANTS,
        functions=KOTOR_FUNCTIONS,
        library_lookup=library_lookup
    )

    parser: yacc.LRParser = nssParser.parser
    t = parser.parse(script, tracking=True)

    ncs = NCS()
    t.compile(ncs)
    return ncs

# Don't trust pytest's logger, use fallbacks to ensure information isn't lost.
def _handle_compile_exc(
    e: Exception,
    file_res: FileResource,
    nss_path: Path,
    compiler_identifier: str,
    game: Game,
):
    exc_type_name, exc_basic_info_str = universal_simplify_exception(e)
    exc_debug_info_str = format_exception_with_variables(e)

    prefix_msg = "Could not compile " if e.__class__ is CompileError else f"Unexpected exception of type '{exc_type_name}' occurred when compiling"
    msg = f"{prefix_msg} '{nss_path.name}' (from {file_res.filepath()}) with '{compiler_identifier}' compiler!"
    exc_separator_str = "-" * len(msg)

    msg_info_level = os.linesep.join((msg, exc_basic_info_str, exc_separator_str))
    msg_debug_level = os.linesep.join((msg, exc_debug_info_str, exc_separator_str))

    log_file(msg_info_level, filepath=f"fallback_level_info_{game}_{compiler_identifier}.txt")
    log_file(msg_debug_level, filepath=f"fallback_level_debug_{game}_{compiler_identifier}.txt")
    log_file(f'"{nss_path.name}",', filepath=f"{compiler_identifier}_incompatible_{game}.txt")  # for quick copy/paste into the known_issues hashset
    pytest.fail(msg_info_level, pytrace=False)

    
CUR_FAILED_EXT: dict[Game, set[ResourceIdentifier]] = {
    Game.K1: set(),
    Game.K2: set(),
}
def compile_with_abstract_compatible(
    compiler: NCSCompiler,
    file_res: FileResource,
    nss_path: Path,
    ncs_path: Path,
    game: Game,
    compiler_identifier: str,
):
    global CUR_FAILED_EXT
    try:
        if isinstance(compiler, ExternalNCSCompiler):
            try:
                stdout, stderr = compiler.compile_script(nss_path, ncs_path, game)
            except EntryPointError as e:
                pytest.xfail(f"{compiler_identifier}: No entry point found in '{nss_path.name}': {e}")
            else:
                if stderr:
                    raise CompileError(f"stdout: {stdout}\nstderr: {stderr}")
        else:
            try:
                compiler.compile_script(nss_path, ncs_path, game, debug=False)
            except EntryPointError as e:
                pytest.xfail(f"{compiler_identifier}: No entry point found in '{nss_path.name}': {e}")

        if not ncs_path.is_file():
            # raise it so _handle_compile_exc can be used to reduce duplicated logging code.
            new_exc = FileNotFoundError(f"Could not find NCS compiled script on disk, '{compiler_identifier}' compiler failed.")
            new_exc.filename = ncs_path
            raise new_exc

    except Exception as e:  # noqa: BLE001
        if isinstance(compiler, ExternalNCSCompiler):
            CUR_FAILED_EXT[game].add(ResourceIdentifier.from_path(nss_path))
        elif ResourceIdentifier.from_path(nss_path) in CUR_FAILED_EXT[game]:
            pytest.xfail(f"{nss_path.name} could not compile with {compiler_identifier} but also failed with nwnnsscomp: {e}")
        _handle_compile_exc(e, file_res, nss_path, compiler_identifier, game)


def compare_external_results(
    compiler_result: dict[str | None, bytes | None],
):
    """Compare results between compilers. No real point since having any of them match is rare."""
    # Ensure all non-None results are the same
    non_none_results: dict[str, bytes] = {
        cp: result
        for cp, result in compiler_result.items()
        if result is not None and cp is not None
    }

    if not non_none_results:
        pytest.skip("No compilers were available or produced output for comparison.")

    # Initialize containers for tracking matches and mismatches
    matches: list[str] = []
    mismatches: list[str] = []

    # Compare the results
    compiler_paths = list(non_none_results.keys())
    for i in range(len(compiler_paths)):
        for j in range(i + 1, len(compiler_paths)):
            path_i = compiler_paths[i]
            path_j = compiler_paths[j]
            result_i = non_none_results[path_i]
            result_j = non_none_results[path_j]

            if result_i == result_j:
                matches.append(f"Match: Compiler outputs for '{path_i}' and '{path_j}' are identical.")
            else:
                mismatches.append(f"Mismatch: Compiler outputs for '{path_i}' and '{path_j}' differ.")

    # Report results
    if mismatches:
        error_report = "\n".join(mismatches + matches)  # Include matches for context
        pytest.fail(error_report, pytrace=False)

    if matches:
        print("\n".join(matches))

def compare_bytes(data1: bytes, data2: bytes) -> list[str]:
    min_len = min(len(data1), len(data2))
    differences: list[str] = []
    i = 0
    while i < min_len:
        if data1[i] != data2[i]:
            start_offset = i
            # Find the end of the difference sequence
            while i < min_len and data1[i] != data2[i]:
                i += 1
            end_offset = i - 1
            diff_length = end_offset - start_offset + 1
            data1_diff = data1[start_offset:i]
            data2_diff = data2[start_offset:i]
            data1_diff_repr = "b'" + ''.join(f"\\x{byte:02x}" for byte in data1[start_offset:i]) + "'"
            data2_diff_repr = "b'" + ''.join(f"\\x{byte:02x}" for byte in data2[start_offset:i]) + "'"
            try:
                data1_str = data1_diff.decode(encoding='windows-1252', errors="replace")
                data2_str = data2_diff.decode(encoding='windows-1252', errors="replace")
                str_repr = f"\nDecoded: '{data1_str}' vs '{data2_str}'"
            except UnicodeDecodeError:
                str_repr = ""
            differences.append(f"Offset 0x{start_offset:02X} to 0x{end_offset:02X}: {diff_length} bytes differ.\nData: {data1_diff_repr} vs {data2_diff_repr}{str_repr}")
        else:
            i += 1
    if len(data1) != len(data2):
        differences.append(f"Data lengths differ: data1 is {len(data1)} bytes, data2 is {len(data2)} bytes")
    return differences

def test_tslpatcher_nwnnsscomp(
    script_data: tuple[Game, tuple[FileResource, Path, Path]],
):
    compilers: dict[str, ExternalNCSCompiler] = {
        TSLPATCHER_NWNNSSCOMP_PATH: ExternalNCSCompiler(TSLPATCHER_NWNNSSCOMP_PATH),
    }

    game, script_info = script_data
    file_res, nss_path, ncs_path = script_info
    for compiler_path, compiler in compilers.items():
        compiler_path = compiler_path.replace("<game>", ("K1" if game.is_k1() else "TSL"))
        compiler.change_nwnnsscomp_path(compiler_path)
        if nss_path.name == "nwscript.nss":
            continue
        if nss_path.is_symlink():
            continue

        unique_ncs_path = ncs_path.with_stem(f"{ncs_path.stem}_{Path(compiler_path).stem}_(tslpatcher)")
        compile_with_abstract_compatible(compiler, file_res, nss_path, unique_ncs_path, game, "tslpatcher")
        with unique_ncs_path.open("rb") as f:
            compiled_ncs_data = f.read()
        original_ncs_path = Path(f"../{('K1' if game.is_k1() else 'TSL')}/Comparisons/{file_res.filepath().parent.parent.name}/{ncs_path.parent.name}/{file_res.identifier()}").with_suffix(".ncs")
        if not original_ncs_path.safe_isfile():
            pytest.skip(f"'{original_ncs_path}' was not found on disk, comparisons cannot be made.")
        with original_ncs_path.open("rb") as f:
            original_ncs_data = f.read()
        differences: list[str] = compare_bytes(compiled_ncs_data, original_ncs_data)
        if differences:
            pytest.fail(f"Bytecodes of compiled '{file_res.filepath()}' does not match with vanilla ncs:\n" + "\n".join(differences))



def save_profiler_output(
    profiler: cProfile.Profile,
    filepath: os.PathLike | str,
):
    profiler.disable()
    profiler_output_file: Path = Path.pathify(filepath)
    profiler_output_file_str = str(profiler_output_file)
    profiler.dump_stats(profiler_output_file_str)
    # Generate reports from the profile stats
    #stats = pstats.Stats(profiler_output_file_str).sort_stats('cumulative')
    #stats.print_stats()

    # Generate some line-execution graphs for flame graphs
    #profiler.create_stats()
    #stats_text = pstats.Stats(profiler).sort_stats('cumulative')
    #stats_text.print_stats()
    #stats_text.dump_stats(f"{LOG_FILENAME}.pstats")
    #stats_text.print_callers()
    #stats_text.print_callees()
    # Cumulative list of the calls
    #stats_text.print_stats(100)
    # Cumulative list of calls per function
    #stats_text.print_callers(100, 'cumulative')
    #stats_text.print_callees(100, 'cumulative')

    # Generate some flat line graphs
    #profiler.print_stats(sort='time')  # (Switch to sort='cumulative' then scroll up to see where time was spent!)
    #profiler.print_stats(sort='name')  # (toString of OBJ is called the most often, followed by compiler drivers)
    #profiler.print_stats(sort='cinit') # (A constructor for NCS is where most (<2%) of time is spent)

if __name__ == "__main__":
    profiler: cProfile.Profile = True  # type: ignore[reportAssignmentType, assignment]
    if profiler:
        profiler = cProfile.Profile()
        profiler.enable()


    result: int | pytest.ExitCode = pytest.main(
        [
            __file__,
            "-v",
            "-ra",
            "-o",
            "log_cli=true",
            "--capture=no",
            "--junitxml=pytest_report.xml",
            "--html=pytest_report.html",
            "--self-contained-html",
            "--tb=no",
            "-n",
            "auto"
        ],
    )

    if profiler:
        save_profiler_output(profiler, "profiler_output.pstat")

    sys.exit(result)
    # Cleanup temporary directories after use
    #for temp_dir in temp_dirs.values():
    #    temp_dir.cleanup()  # noqa: ERA001
