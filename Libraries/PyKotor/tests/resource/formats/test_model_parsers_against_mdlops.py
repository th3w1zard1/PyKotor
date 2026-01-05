"""Test MDL/MDX models from actual game installations for both K1 and TSL."""

from __future__ import annotations

import difflib
import random
import subprocess
import tempfile
from pathlib import Path

import pytest
from pykotor.common.misc import Game
from pykotor.extract.file import FileResource
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.type import ResourceType
from pykotor.tools.path import find_kotor_paths_from_default


def find_test_models(
    game: Game,
    max_models: int = 50,
) -> list[tuple[FileResource, FileResource]]:
    """Find MDL/MDX pairs from game installation. Improved for performance and memory."""
    paths = find_kotor_paths_from_default()
    game_paths = paths.get(game, [])
    if not game_paths:
        return []

    mdl_dict: dict[str, FileResource] = {}
    mdx_dict: dict[str, FileResource] = {}

    for game_path in game_paths:
        installation = Installation(game_path)
        # Use generator and type filtering for speed, avoid repeated mapping/creation
        for res in installation:
            restype = res.restype()
            if restype == ResourceType.MDL:
                mdl_dict[res.resname()] = res
            elif restype == ResourceType.MDX:
                mdx_dict[res.resname()] = res

    mdl_mdx_pairs: list[tuple[FileResource, FileResource]] = []
    # Only return pairs where both MDL and MDX exist
    for resname, mdl_res in mdl_dict.items():
        mdx_res = mdx_dict.get(resname)
        if mdx_res:
            mdl_mdx_pairs.append((mdl_res, mdx_res))

    return mdl_mdx_pairs


@pytest.fixture(scope="session")
def mdlops_exe() -> Path:
    """Find and return the path to mdlops.exe."""
    # Try multiple possible locations
    test_file = Path(__file__).resolve()
    # Try different parent levels to find repo root (vendor/MDLOps should be at repo root)
    possible_roots = [test_file.parents[i] for i in range(4, 8)]
    possible_paths = []
    for repo_root in possible_roots:
        possible_paths.append(repo_root / "vendor" / "MDLOps" / "mdlops.exe")
        possible_paths.append(repo_root / "MDLOps" / "mdlops.exe")
    # Also try relative to current working directory
    possible_paths.append(Path("vendor/MDLOps/mdlops.exe").resolve())

    for path in possible_paths:
        if path.exists():
            return path

    pytest.skip(f"MDLOps not found. Checked: {[str(p) for p in possible_paths[:10]]}")


@pytest.fixture(scope="session")
def k1_models() -> list[tuple[FileResource, FileResource]]:
    """Find K1 models for testing."""
    models = find_test_models(Game.K1, max_models=50)
    if not models:
        pytest.skip("No K1 installation found or no models available")
    return models


@pytest.fixture(scope="session")
def k2_models() -> list[tuple[FileResource, FileResource]]:
    """Find K2/TSL models for testing."""
    models = find_test_models(Game.K2, max_models=50)
    if not models:
        pytest.skip("No TSL installation found or no models available")
    return models


def _test_single_model(
    mdl_res: FileResource,
    mdx_res: FileResource,
    mdlops_exe: Path,
) -> tuple[bool, str]:
    """Test a single model with MDLOps and compare with PyKotor output.

    Returns:
        Tuple of (success: bool, message: str)
    """
    with tempfile.TemporaryDirectory(prefix="mdl_test_") as td:
        td_path = Path(td)
        # Construct filenames from resname and extension
        mdl_filename = f"{mdl_res.resname()}.{mdl_res.restype().extension}"
        mdx_filename = f"{mdx_res.resname()}.{mdx_res.restype().extension}"
        test_mdl = td_path / mdl_filename
        test_mdx = td_path / mdx_filename

        # Write byte data from FileResource to temporary files
        # This works for both archive-based and file-based resources
        test_mdl.write_bytes(mdl_res.data())
        test_mdx.write_bytes(mdx_res.data())

        # Step 1: Decompile with MDLOps
        print("    [1/4] MDLOps: Decompiling original binary...")
        try:
            result = subprocess.run(
                [str(mdlops_exe), str(test_mdl)],
                cwd=str(td_path),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                return False, f"MDLOps failed to decompile original: {error_msg[:500]}"

            mdlops_ascii_path = td_path / f"{test_mdl.stem}-ascii.mdl"
            if not mdlops_ascii_path.exists():
                return False, "MDLOps succeeded but no ASCII output file created"

            print(f"         -> Created: {mdlops_ascii_path.name}")

        except subprocess.TimeoutExpired:
            return False, "MDLOps timeout while decompiling original"
        except Exception as e:
            return False, f"MDLOps error while decompiling original: {e}"

        # Step 2: Read MDL with PyKotor and write back to binary
        print("    [2/6] PyKotor: Reading and writing binary...")
        try:
            # Read the original binary MDL/MDX
            mdl_obj = read_mdl(
                test_mdl, source_ext=test_mdx, file_format=ResourceType.MDL
            )
            if mdl_obj is None:
                return False, "PyKotor failed to read MDL"

            # Write PyKotor binary output
            pykotor_mdl = td_path / f"{test_mdl.stem}-pykotor.mdl"
            pykotor_mdx = td_path / f"{test_mdl.stem}-pykotor.mdx"
            write_mdl(mdl_obj, pykotor_mdl, ResourceType.MDL, target_ext=pykotor_mdx)

            if not pykotor_mdl.exists():
                return False, "PyKotor failed to write MDL"

            print(f"         -> Created: {pykotor_mdl.name}, {pykotor_mdx.name}")

        except Exception as e:
            return False, f"PyKotor error: {e}"

        # Step 3: Recompile MDLOps ASCII back to binary for oracle
        print("    [3/6] MDLOps: Recompiling ASCII to binary...")
        try:
            result = subprocess.run(
                [str(mdlops_exe), str(mdlops_ascii_path)],
                cwd=str(td_path),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                return False, f"MDLOps failed to recompile ASCII: {error_msg[:500]}"

            # MDLOps writes -bin suffix for binary outputs
            ascii_stem = mdlops_ascii_path.stem  # e.g. foo-ascii
            mdlops_bin_mdl = td_path / f"{ascii_stem}-bin.mdl"
            mdlops_bin_mdx = td_path / f"{ascii_stem}-bin.mdx"
            if not mdlops_bin_mdl.exists() or not mdlops_bin_mdx.exists():
                return False, "MDLOps ASCII recompile missing binary outputs"

        except subprocess.TimeoutExpired:
            return False, "MDLOps timeout while recompiling ASCII"
        except Exception as e:
            return False, f"MDLOps error while recompiling ASCII: {e}"

        # Step 4: Binary parity check: PyKotor vs MDLOps binaries
        print("    [4/6] Comparing binary outputs...")
        try:
            pykotor_mdl_bytes = pykotor_mdl.read_bytes()
            pykotor_mdx_bytes = pykotor_mdx.read_bytes()
            mdlops_mdl_bytes = mdlops_bin_mdl.read_bytes()
            mdlops_mdx_bytes = mdlops_bin_mdx.read_bytes()

            def _compare_bytes(lhs: bytes, rhs: bytes, label: str) -> tuple[bool, str]:
                if lhs == rhs:
                    return True, "OK"
                if len(lhs) != len(rhs):
                    return False, f"{label} size mismatch: {len(lhs)} vs {len(rhs)}"
                # Find first differing offset
                for i, (a, b) in enumerate(zip(lhs, rhs)):
                    if a != b:
                        context_start = max(0, i - 8)
                        context_end = min(len(lhs), i + 8)
                        lhs_slice = lhs[context_start:context_end]
                        rhs_slice = rhs[context_start:context_end]
                        return (
                            False,
                            f"{label} byte diff @ {i}: {a:#04x}!={b:#04x} "
                            f"lhs[{context_start}:{context_end}]={lhs_slice.hex()} "
                            f"rhs[{context_start}:{context_end}]={rhs_slice.hex()}",
                        )
                return False, f"{label} differs but no diff located"

            ok_mdl, msg_mdl = _compare_bytes(pykotor_mdl_bytes, mdlops_mdl_bytes, "MDL")
            ok_mdx, msg_mdx = _compare_bytes(pykotor_mdx_bytes, mdlops_mdx_bytes, "MDX")
            if not ok_mdl or not ok_mdx:
                combined = "; ".join(filter(None, [msg_mdl if not ok_mdl else "", msg_mdx if not ok_mdx else ""]))
                return False, f"Binary mismatch: {combined}"
        except Exception as e:
            return False, f"Binary comparison error: {e}"

        # Step 5: Decompile PyKotor output with MDLOps
        print("    [5/6] MDLOps: Decompiling PyKotor binary...")
        try:
            result = subprocess.run(
                [str(mdlops_exe), str(pykotor_mdl)],
                cwd=str(td_path),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                # Show more context for MDLOps errors
                full_error = error_msg
                if len(error_msg) > 1000:
                    full_error = (
                        error_msg[:1000]
                        + f"\n... ({len(error_msg) - 1000} more characters)"
                    )
                return (
                    False,
                    f"MDLOps failed to decompile PyKotor output:\n{full_error}",
                )

            pykotor_ascii_path = td_path / f"{pykotor_mdl.stem}-ascii.mdl"
            if not pykotor_ascii_path.exists():
                return False, "MDLOps succeeded but no ASCII output for PyKotor binary"

            print(f"         -> Created: {pykotor_ascii_path.name}")

        except subprocess.TimeoutExpired:
            return False, "MDLOps timeout while decompiling PyKotor output"
        except Exception as e:
            return False, f"MDLOps error while decompiling PyKotor output: {e}"

        # Step 6: Compare MDLOps ASCII outputs using unified diff
        print("    [6/6] Comparing ASCII outputs...")
        try:
            mdlops_ascii = mdlops_ascii_path.read_text(
                encoding="utf-8", errors="replace"
            )
            pykotor_ascii = pykotor_ascii_path.read_text(
                encoding="utf-8", errors="replace"
            )

            # Normalize filedependancy lines - MDLOps uses filename, so PyKotor output
            # will have "-pykotor" suffix in filename, which MDLOps reads and uses
            # Replace "-pykotor" suffix in filedependancy lines for comparison
            import re
            pykotor_ascii_normalized = re.sub(
                r"^filedependancy (.+)-pykotor (NULL\.mlk)$",
                r"filedependancy \1 \2",
                pykotor_ascii,
                flags=re.MULTILINE
            )

            if mdlops_ascii == pykotor_ascii_normalized:
                print("         -> PASS: Outputs match exactly")
                return True, "OK"

            # Generate unified diff
            diff_lines = list(
                difflib.unified_diff(
                    mdlops_ascii.splitlines(keepends=True),
                    pykotor_ascii_normalized.splitlines(keepends=True),
                    fromfile="MDLOps (original)",
                    tofile="MDLOps (PyKotor binary)",
                    lineterm="",
                )
            )

            if diff_lines:
                # Show full diff in pytest output
                diff_text = "".join(diff_lines)
                # Limit to first 300 lines for readability
                if len(diff_lines) > 300:
                    diff_text = (
                        "".join(diff_lines[:300])
                        + f"\n... ({len(diff_lines) - 300} more lines)"
                    )
                return False, f"Mismatch detected:\n{diff_text}"

            return False, "Files differ but no diff generated"

        except Exception as e:
            return False, f"Comparison error: {e}"


def test_k1_models_random_sample(
    mdlops_exe: Path,
    k1_models: list[tuple[FileResource, FileResource]],
) -> None:
    """Test a random sample of K1 models."""
    # Randomly sample up to 10 models for testing
    test_count = min(10, len(k1_models))
    random_models = random.sample(k1_models, test_count)

    print(f"\n{'=' * 70}")
    print("K1 (Knights of the Old Republic) Models")
    print(f"{'=' * 70}")
    print(f"Found {len(k1_models)} K1 models")
    print(f"Testing {test_count} random models...\n")

    passed = 0
    failed = 0

    for mdl_res, mdx_res in random_models:
        model_name = f"{mdl_res.resname()}.{mdl_res.restype().extension}"
        print(f"  Testing: {model_name}")
        success, msg = _test_single_model(mdl_res, mdx_res, mdlops_exe)
        if success:
            passed += 1
            print("  Result: PASS\n")
        else:
            failed += 1
            print(f"  Result: FAIL - {msg}\n")
            # Fail the test on first failure for now
            pytest.fail(f"Model {model_name} failed: {msg}")

    print(f"{'=' * 70}")
    print(f"Summary: {passed} passed, {failed} failed out of {test_count} tested")
    print(f"{'=' * 70}\n")


def test_k2_models_random_sample(
    mdlops_exe: Path,
    k2_models: list[tuple[FileResource, FileResource]],
) -> None:
    """Test a random sample of TSL/K2 models."""
    # Randomly sample up to 10 models for testing
    test_count = min(10, len(k2_models))
    random_models = random.sample(k2_models, test_count)

    print(f"\n{'=' * 70}")
    print("TSL (Knights of the Old Republic II) Models")
    print(f"{'=' * 70}")
    print(f"Found {len(k2_models)} TSL models")
    print(f"Testing {test_count} random models...\n")

    passed = 0
    failed = 0

    for mdl_res, mdx_res in random_models:
        model_name = f"{mdl_res.resname()}.{mdl_res.restype().extension}"
        print(f"  Testing: {model_name}")
        success, msg = _test_single_model(mdl_res, mdx_res, mdlops_exe)
        if success:
            passed += 1
            print("  Result: PASS\n")
        else:
            failed += 1
            print(f"  Result: FAIL - {msg}\n")
            # Fail the test on first failure for now
            pytest.fail(f"Model {model_name} failed: {msg}")

    print(f"{'=' * 70}")
    print(f"Summary: {passed} passed, {failed} failed out of {test_count} tested")
    print(f"{'=' * 70}\n")


def main():
    print("Running tests...")
    pytest.main(["-v", __file__])
    print("Tests completed.")


if __name__ == "__main__":
    main()
