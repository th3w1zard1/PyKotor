#!/usr/bin/env python3
"""Analyze the indoor map builder walkmesh bug.

This script:
1. Reads kit WOK files to understand their original transition structure
2. Compares step01 (working) vs step02 (buggy) generated modules
3. Identifies where transitions get lost or applied to wrong faces

Usage:
    python scripts/analyze_walkmesh_bug.py

Requires PyKotor venv to be activated.
"""

from __future__ import annotations

import sys

from pathlib import Path

# Setup paths
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # Goes up from vendor/PyKotor/scripts
PYKOTOR_LIBS = SCRIPT_DIR.parent / "Libraries" / "PyKotor" / "src"
UTILITY_LIBS = SCRIPT_DIR.parent / "Libraries" / "Utility" / "src"

if str(PYKOTOR_LIBS) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_LIBS))
if str(UTILITY_LIBS) not in sys.path:
    sys.path.insert(0, str(UTILITY_LIBS))

from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.erf import read_erf
from pykotor.resource.type import ResourceType


def analyze_wok_file(path: Path, name: str) -> dict:
    """Analyze a WOK file and return detailed info."""
    print(f"\n{'=' * 70}")
    print(f"Analyzing: {name}")
    print(f"Path: {path}")
    print(f"{'=' * 70}")

    data = path.read_bytes()
    bwm = read_bwm(data)

    result = {
        "name": name,
        "path": str(path),
        "total_faces": len(bwm.faces),
        "walkable_faces": [],
        "unwalkable_faces": [],
        "faces_with_transitions": [],
        "edges_with_transitions": 0,
    }

    # Categorize faces
    for i, face in enumerate(bwm.faces):
        is_walkable = face.material.walkable()
        has_trans = face.trans1 is not None or face.trans2 is not None or face.trans3 is not None

        face_info = {
            "index": i,
            "material": face.material.name,
            "walkable": is_walkable,
            "trans1": face.trans1,
            "trans2": face.trans2,
            "trans3": face.trans3,
            "v1": (round(face.v1.x, 3), round(face.v1.y, 3), round(face.v1.z, 3)),
            "v2": (round(face.v2.x, 3), round(face.v2.y, 3), round(face.v2.z, 3)),
            "v3": (round(face.v3.x, 3), round(face.v3.y, 3), round(face.v3.z, 3)),
        }

        if is_walkable:
            result["walkable_faces"].append(face_info)
        else:
            result["unwalkable_faces"].append(face_info)

        if has_trans:
            result["faces_with_transitions"].append(face_info)

    # Count edges with transitions
    try:
        edges = bwm.edges()
        for edge in edges:
            if edge.transition is not None and edge.transition != -1:
                result["edges_with_transitions"] += 1
    except Exception as e:
        print(f"  Warning: Could not compute edges: {e}")

    # Print summary
    print(f"  Total faces: {result['total_faces']}")
    print(f"  Walkable faces: {len(result['walkable_faces'])}")
    print(f"  Unwalkable faces: {len(result['unwalkable_faces'])}")
    print(f"  Faces with transitions: {len(result['faces_with_transitions'])}")
    print(f"  Edges with transitions: {result['edges_with_transitions']}")

    # Print transition details
    if result["faces_with_transitions"]:
        print("\n  Faces with transitions:")
        for face_info in result["faces_with_transitions"]:
            trans_str = []
            if face_info["trans1"] is not None:
                trans_str.append(f"trans1={face_info['trans1']}")
            if face_info["trans2"] is not None:
                trans_str.append(f"trans2={face_info['trans2']}")
            if face_info["trans3"] is not None:
                trans_str.append(f"trans3={face_info['trans3']}")
            print(f"    Face {face_info['index']}: material={face_info['material']}, walkable={face_info['walkable']}, {', '.join(trans_str)}")
            print(f"      v1={face_info['v1']}")
            print(f"      v2={face_info['v2']}")
            print(f"      v3={face_info['v3']}")

    return result


def analyze_mod_woks(mod_path: Path, name: str) -> list:
    """Analyze all WOK files in a .mod file."""
    print(f"\n{'#' * 70}")
    print(f"Analyzing MOD: {name}")
    print(f"Path: {mod_path}")
    print(f"{'#' * 70}")

    results = []
    erf = read_erf(mod_path.read_bytes())

    for res in erf:
        if res.restype == ResourceType.WOK:
            # Create temp file-like analysis
            data = res.data
            bwm = read_bwm(data)

            result = {
                "resref": str(res.resref),
                "total_faces": len(bwm.faces),
                "walkable_count": 0,
                "unwalkable_count": 0,
                "faces_with_transitions": [],
                "edges_with_transitions": 0,
            }

            # Analyze faces
            for i, face in enumerate(bwm.faces):
                is_walkable = face.material.walkable()
                has_trans = face.trans1 is not None or face.trans2 is not None or face.trans3 is not None

                if is_walkable:
                    result["walkable_count"] += 1
                else:
                    result["unwalkable_count"] += 1

                if has_trans:
                    result["faces_with_transitions"].append(
                        {
                            "index": i,
                            "material": face.material.name,
                            "walkable": is_walkable,
                            "trans1": face.trans1,
                            "trans2": face.trans2,
                            "trans3": face.trans3,
                            "v1": (round(face.v1.x, 3), round(face.v1.y, 3), round(face.v1.z, 3)),
                        }
                    )

            # Count edges with transitions
            try:
                edges = bwm.edges()
                for edge in edges:
                    if edge.transition is not None and edge.transition != -1:
                        result["edges_with_transitions"] += 1
            except Exception as e:
                pass  # Edges computation might fail

            results.append(result)

            # Print summary for this WOK
            print(f"\n  WOK: {result['resref']}")
            print(f"    Total faces: {result['total_faces']}")
            print(f"    Walkable: {result['walkable_count']}, Unwalkable: {result['unwalkable_count']}")
            print(f"    Faces with transitions: {len(result['faces_with_transitions'])}")
            print(f"    Edges with transitions: {result['edges_with_transitions']}")

            # Print transition details
            for face_info in result["faces_with_transitions"]:
                trans_str = []
                if face_info["trans1"] is not None:
                    trans_str.append(f"t1={face_info['trans1']}")
                if face_info["trans2"] is not None:
                    trans_str.append(f"t2={face_info['trans2']}")
                if face_info["trans3"] is not None:
                    trans_str.append(f"t3={face_info['trans3']}")

                walkable_str = "WALKABLE" if face_info["walkable"] else "NON_WALK"
                print(f"      Face {face_info['index']}: {face_info['material']} ({walkable_str}) - {', '.join(trans_str)}")

    return results


def main():
    print("=" * 70)
    print("INDOOR MAP BUILDER WALKMESH BUG ANALYSIS")
    print("=" * 70)

    # Define paths
    kits_dir = SCRIPT_DIR.parent / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits"
    repro_dir = REPO_ROOT / "reproduce_walkbug_indoorbuilder"

    # 1. Analyze original kit WOK files
    print("\n" + "=" * 70)
    print("PART 1: ORIGINAL KIT WOK FILES")
    print("=" * 70)

    kit_woks = []
    blackvulkar_dir = kits_dir / "blackvulkar"

    if blackvulkar_dir.exists():
        for wok_file in blackvulkar_dir.glob("*.wok"):
            kit_woks.append(analyze_wok_file(wok_file, f"Kit: {wok_file.name}"))
    else:
        print(f"Kit directory not found: {blackvulkar_dir}")

    # 2. Analyze step01 (working v2.0.4)
    print("\n" + "=" * 70)
    print("PART 2: STEP01 - WORKING (v2.0.4)")
    print("=" * 70)

    step01_dir = repro_dir / "step01"
    if step01_dir.exists():
        for mod_file in step01_dir.glob("*.mod"):
            step01_results = analyze_mod_woks(mod_file, "step01")
    else:
        print(f"Step01 directory not found: {step01_dir}")
        step01_results = []

    # 3. Analyze step02 (buggy v4 beta)
    print("\n" + "=" * 70)
    print("PART 3: STEP02 - BUGGY (v4.0.0 beta)")
    print("=" * 70)

    step02_dir = repro_dir / "step02 from beta"
    if step02_dir.exists():
        for mod_file in step02_dir.glob("*.mod"):
            step02_results = analyze_mod_woks(mod_file, "step02")
    else:
        print(f"Step02 directory not found: {step02_dir}")
        step02_results = []

    # 4. Summary comparison
    print("\n" + "#" * 70)
    print("SUMMARY COMPARISON")
    print("#" * 70)

    print("\n| Version | WOK | Faces w/ Trans | Trans on Walkable? | Edges w/ Trans |")
    print("|---------|-----|----------------|-------------------|----------------|")

    for result in step01_results:
        trans_walkable = all(f["walkable"] for f in result["faces_with_transitions"]) if result["faces_with_transitions"] else "N/A"
        print(f"| Step01  | {result['resref'][:15]} | {len(result['faces_with_transitions'])} | {trans_walkable} | {result['edges_with_transitions']} |")

    for result in step02_results:
        trans_walkable = all(f["walkable"] for f in result["faces_with_transitions"]) if result["faces_with_transitions"] else "N/A"
        print(f"| Step02  | {result['resref'][:15]} | {len(result['faces_with_transitions'])} | {trans_walkable} | {result['edges_with_transitions']} |")

    # 5. Root cause analysis
    print("\n" + "#" * 70)
    print("ROOT CAUSE ANALYSIS")
    print("#" * 70)

    if step01_results and step02_results:
        step01_room0 = next((r for r in step01_results if "room0" in r["resref"].lower()), None)
        step02_room0 = next((r for r in step02_results if "room0" in r["resref"].lower()), None)

        if step01_room0 and step02_room0:
            print("\nRoom0 Comparison:")
            print(f"  Step01: {len(step01_room0['faces_with_transitions'])} faces with transitions, {step01_room0['edges_with_transitions']} edges with transitions")
            print(f"  Step02: {len(step02_room0['faces_with_transitions'])} faces with transitions, {step02_room0['edges_with_transitions']} edges with transitions")

            # Check if transitions are on walkable faces
            step01_trans_walkable = [f for f in step01_room0["faces_with_transitions"] if f["walkable"]]
            step01_trans_nonwalk = [f for f in step01_room0["faces_with_transitions"] if not f["walkable"]]
            step02_trans_walkable = [f for f in step02_room0["faces_with_transitions"] if f["walkable"]]
            step02_trans_nonwalk = [f for f in step02_room0["faces_with_transitions"] if not f["walkable"]]

            print("\n  Step01 transitions:")
            print(f"    On WALKABLE faces: {len(step01_trans_walkable)}")
            print(f"    On NON_WALK faces: {len(step01_trans_nonwalk)}")

            print("\n  Step02 transitions:")
            print(f"    On WALKABLE faces: {len(step02_trans_walkable)}")
            print(f"    On NON_WALK faces: {len(step02_trans_nonwalk)}")

            if step02_trans_nonwalk and not step02_trans_walkable:
                print("\n  ** BUG CONFIRMED: Step02 has transitions ONLY on NON_WALK faces! **")
                print("     This is why edges have no transitions - edges are computed from walkable faces only.")

    print("\n" + "=" * 70)
    print("Analysis complete.")


if __name__ == "__main__":
    main()
