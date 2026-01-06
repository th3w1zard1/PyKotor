"""Compare failing vs passing models to identify differences."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "vendor/PyKotor/Libraries/PyKotor/src")
from pykotor.resource.formats.mdl.mdl_auto import read_mdl, write_mdl
from pykotor.resource.type import ResourceType

mdlops_exe = Path("vendor/MDLOps/mdlops.exe")


def analyze_model(mdl_path: Path, mdx_path: Path, name: str):
    """Analyze a model and report key characteristics."""
    print(f"\n{'=' * 60}")
    print(f"{name}: {mdl_path.name}")
    print(f"{'=' * 60}")

    # Check if MDLOps can decompile the original
    with tempfile.TemporaryDirectory(prefix="mdl_analyze_") as td:
        td_path = Path(td)
        test_mdl = td_path / mdl_path.name
        test_mdx = td_path / mdx_path.name
        shutil.copy(mdl_path, test_mdl)
        shutil.copy(mdx_path, test_mdx)

        result = subprocess.run(
            [str(mdlops_exe), str(test_mdl)],
            cwd=str(td_path),
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("[OK] MDLOps can decompile original")
        else:
            print(f"[FAIL] MDLOps FAILED to decompile original: {result.stdout[:300]}")
            return

    # Read with PyKotor
    try:
        mdl_obj = read_mdl(mdl_path, source_ext=mdx_path)
        print("[OK] PyKotor can read original binary")
        print(f"  - Name: {mdl_obj.name}")
        print(f"  - Supermodel: {mdl_obj.supermodel}")
        print(f"  - Node count: {len(mdl_obj.all_nodes())}")
        print(f"  - Animation count: {len(mdl_obj.anims)}")

        # Count nodes with textures
        nodes_with_textures = 0
        nodes_with_uv1 = 0
        nodes_with_uv2 = 0
        for node in mdl_obj.all_nodes():
            if node.mesh:
                if node.mesh.texture_1 and node.mesh.texture_1.upper() != "NULL":
                    nodes_with_textures += 1
                if node.mesh.vertex_uv1:
                    nodes_with_uv1 += 1
                if node.mesh.vertex_uv2:
                    nodes_with_uv2 += 1

        print(f"  - Nodes with textures: {nodes_with_textures}")
        print(f"  - Nodes with UV1: {nodes_with_uv1}")
        print(f"  - Nodes with UV2: {nodes_with_uv2}")

        # Check MDX data structure
        with open(mdx_path, "rb") as f:
            mdx_size = len(f.read())
        print(f"  - MDX file size: {mdx_size} bytes")

    except Exception as e:
        print(f"[FAIL] PyKotor failed to read: {e}")
        return

    # Try ASCII roundtrip
    try:
        ascii_path = td_path / f"{test_mdl.stem}-ascii.mdl"
        if ascii_path.exists():
            mdl_obj_ascii = read_mdl(
                ascii_path.read_bytes(), file_format=ResourceType.MDL_ASCII
            )
            print("[OK] PyKotor can read MDLOps ASCII")

            # Write binary
            out_dir = td_path / "out"
            out_dir.mkdir()
            out_mdl = out_dir / mdl_path.name
            out_mdx = out_dir / mdx_path.name
            write_mdl(mdl_obj_ascii, out_mdl, ResourceType.MDL, target_ext=out_mdx)
            print("[OK] PyKotor can write binary")

            # Try MDLOps on PyKotor output
            result2 = subprocess.run(
                [str(mdlops_exe), str(out_mdl)],
                cwd=str(out_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result2.returncode == 0:
                print("[OK] MDLOps can decompile PyKotor binary")
            else:
                print("[FAIL] MDLOps FAILED to decompile PyKotor binary:")
                print(f"  {result2.stdout[:500]}")
        else:
            print("[FAIL] No ASCII output from MDLOps")
    except Exception as e:
        print(f"[FAIL] Roundtrip failed: {e}")


# Test both models
passing_model_mdl = Path(
    "vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/c_dewback.mdl"
)
passing_model_mdx = Path(
    "vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/c_dewback.mdx"
)

failing_model_mdl = Path(
    "vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/dor_lhr02.mdl"
)
failing_model_mdx = Path(
    "vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/dor_lhr02.mdx"
)

analyze_model(passing_model_mdl, passing_model_mdx, "PASSING MODEL")
analyze_model(failing_model_mdl, failing_model_mdx, "FAILING MODEL")
