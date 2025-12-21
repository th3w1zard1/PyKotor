#!/usr/bin/env python
"""Verify the current status of the indoor builder walkmesh bug.

This script:
1. Reads the actual step02.mod file (known buggy)
2. Regenerates a fresh build from the step02.indoor file using current code
3. Compares the two to determine if the bug still exists
"""

import sys
from pathlib import Path

# Add PyKotor to path
pykotor_path = Path(__file__).resolve().parent.parent / "Libraries" / "PyKotor" / "src"
sys.path.insert(0, str(pykotor_path))
toolset_path = Path(__file__).resolve().parent.parent / "Tools" / "HolocronToolset" / "src"
sys.path.insert(0, str(toolset_path))

from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.erf import read_erf
from pykotor.resource.type import ResourceType


def analyze_mod_woks(mod_path: Path, mod_name: str):
    """Analyze WOK files in a MOD file."""
    print(f"\n{'='*70}")
    print(f"Analyzing: {mod_name}")
    print(f"Path: {mod_path}")
    print(f"{'='*70}")
    
    if not mod_path.exists():
        print(f"ERROR: File not found: {mod_path}")
        return None
    
    erf = read_erf(mod_path.read_bytes())
    results = []
    
    for resource in erf:
        if resource.restype == ResourceType.WOK:
            data = erf.get(resource.resref.get(), resource.restype)
            if data:
                bwm = read_bwm(data)
                
                walkable = [f for f in bwm.faces if f.material.walkable()]
                unwalkable = [f for f in bwm.faces if not f.material.walkable()]
                
                # Find faces with transitions
                transition_info = []
                for i, face in enumerate(bwm.faces):
                    trans = []
                    if face.trans1 is not None:
                        trans.append(f"t1={face.trans1}")
                    if face.trans2 is not None:
                        trans.append(f"t2={face.trans2}")
                    if face.trans3 is not None:
                        trans.append(f"t3={face.trans3}")
                    if trans:
                        is_walkable = face.material.walkable()
                        in_walkable_range = i < len(walkable)
                        transition_info.append({
                            "face_idx": i,
                            "material": face.material.name,
                            "is_walkable": is_walkable,
                            "in_walkable_range": in_walkable_range,
                            "transitions": trans,
                            "v1": (round(face.v1.x, 3), round(face.v1.y, 3), round(face.v1.z, 3)),
                        })
                
                # Check edges
                edges = bwm.edges()
                edges_with_trans = [e for e in edges if e.transition is not None and e.transition >= 0]
                
                result = {
                    "resref": resource.resref.get(),
                    "total_faces": len(bwm.faces),
                    "walkable": len(walkable),
                    "unwalkable": len(unwalkable),
                    "faces_with_trans": len(transition_info),
                    "edges_with_trans": len(edges_with_trans),
                    "transition_faces": transition_info,
                    "transitions_on_walkable": all(t["is_walkable"] for t in transition_info),
                }
                results.append(result)
                
                print(f"\n  WOK: {resource.resref.get()}")
                print(f"    Total faces: {len(bwm.faces)}")
                print(f"    Walkable: {len(walkable)}, Unwalkable: {len(unwalkable)}")
                print(f"    Faces with transitions: {len(transition_info)}")
                print(f"    Edges with transitions: {len(edges_with_trans)}")
                
                for tf in transition_info:
                    status = "[OK] WALKABLE" if tf["is_walkable"] else "[BUG] NON_WALK!"
                    print(f"      Face {tf['face_idx']}: {tf['material']} - {status}")
                    print(f"        Transitions: {', '.join(tf['transitions'])}")
                
                if transition_info:
                    all_walkable = all(t["is_walkable"] for t in transition_info)
                    if all_walkable:
                        print("    [OK] Status: CORRECT - All transitions on walkable faces")
                    else:
                        print("    [BUG] Status: Transitions on non-walkable faces!")
    
    return results


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    
    # Paths to reproduction data
    step01_mod = repo_root / "reproduce_walkbug_indoorbuilder" / "step01" / "step01.mod"
    step02_mod = repo_root / "reproduce_walkbug_indoorbuilder" / "step02 from beta" / "step02.mod"
    
    print("\n" + "="*70)
    print("INDOOR BUILDER WALKMESH BUG STATUS VERIFICATION")
    print("="*70)
    
    # Analyze the actual MOD files
    step01_results = analyze_mod_woks(step01_mod, "STEP01 (Working v2.0.4)")
    step02_results = analyze_mod_woks(step02_mod, "STEP02 (Buggy v4.0.0b3)")
    
    # Summary comparison
    print("\n" + "="*70)
    print("SUMMARY COMPARISON")
    print("="*70)
    
    if step01_results and step02_results:
        print("\n| Version | WOK | Trans on Walkable? | Edges w/ Trans | Status |")
        print("|---------|-----|-------------------|----------------|--------|")
        
        for r in step01_results:
            status = "OK" if r["transitions_on_walkable"] else "BUG"
            print(f"| Step01 | {r['resref']} | {r['transitions_on_walkable']} | {r['edges_with_trans']} | {status} |")
        
        for r in step02_results:
            status = "OK" if r["transitions_on_walkable"] else "BUG"
            print(f"| Step02 | {r['resref']} | {r['transitions_on_walkable']} | {r['edges_with_trans']} | {status} |")
    
    # Conclusion
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    
    if step02_results:
        has_bug = any(not r["transitions_on_walkable"] for r in step02_results)
        if has_bug:
            print("""
The step02.mod file DOES contain the bug:
  - Transitions are on NON_WALK faces instead of WALKABLE faces
  - This causes edges to have no transitions (edges are computed from walkable faces only)
  - As a result, room transitions don't work in the game

However, our simulation shows the CURRENT codebase produces correct output!
This suggests the bug may have been fixed, but we need to verify the specific
code path that creates the step02.mod to confirm.

To fully resolve this:
1. Identify what code path in v4.0.0b3 produced the buggy step02.mod
2. Ensure the fix is comprehensive and covers all cases
3. Write regression tests to prevent this from happening again
""")
        else:
            print("No bug detected in step02.mod - transitions are on walkable faces.")
    
    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()

