#!/usr/bin/env python
"""Debug script to trace the indoor builder walkmesh bug.

This script traces through the build process to find where transitions
end up on NON_WALK faces instead of WALKABLE faces.
"""

import sys
from pathlib import Path
from copy import deepcopy

# Add PyKotor to path
pykotor_path = Path(__file__).resolve().parent.parent / "Libraries" / "PyKotor" / "src"
sys.path.insert(0, str(pykotor_path))
toolset_path = Path(__file__).resolve().parent.parent / "Tools" / "HolocronToolset" / "src"
sys.path.insert(0, str(toolset_path))

from pykotor.resource.formats.bwm import read_bwm, bytes_bwm


def analyze_kit_wok(kit_path: Path) -> None:
    """Analyze a kit WOK file to show which faces have transitions."""
    print(f"\n{'='*70}")
    print(f"Analyzing Kit WOK: {kit_path.name}")
    print(f"{'='*70}")
    
    data = kit_path.read_bytes()
    bwm = read_bwm(data)
    
    walkable = [f for f in bwm.faces if f.material.walkable()]
    unwalkable = [f for f in bwm.faces if not f.material.walkable()]
    
    print(f"Total faces: {len(bwm.faces)}")
    print(f"Walkable: {len(walkable)}, Unwalkable: {len(unwalkable)}")
    
    # Find faces with transitions
    transition_faces = []
    for i, face in enumerate(bwm.faces):
        trans = []
        if face.trans1 is not None:
            trans.append(f"trans1={face.trans1}")
        if face.trans2 is not None:
            trans.append(f"trans2={face.trans2}")
        if face.trans3 is not None:
            trans.append(f"trans3={face.trans3}")
        if trans:
            is_walkable = face.material.walkable()
            walkable_idx = None
            if is_walkable:
                for w_idx, w_face in enumerate(walkable):
                    if w_face is face:
                        walkable_idx = w_idx
                        break
            transition_faces.append({
                "overall_idx": i,
                "walkable_idx": walkable_idx,
                "material": face.material.name,
                "is_walkable": is_walkable,
                "transitions": trans,
                "v1": (round(face.v1.x, 3), round(face.v1.y, 3), round(face.v1.z, 3)),
            })
    
    print(f"\nFaces with transitions: {len(transition_faces)}")
    for tf in transition_faces:
        walkable_str = f"walkable_idx={tf['walkable_idx']}" if tf['is_walkable'] else "NOT WALKABLE"
        print(f"  Face {tf['overall_idx']}: {tf['material']} ({walkable_str})")
        print(f"    Transitions: {', '.join(tf['transitions'])}")
        print(f"    Vertex 1: {tf['v1']}")
    
    return bwm


def simulate_build_process(bwm, flip_x=False, flip_y=False, rotation=0.0, 
                          position=(0, 0, 0), dummy_to_actual=None) -> None:
    """Simulate the indoor builder's build process and trace transitions."""
    
    print(f"\n{'='*70}")
    print(f"Simulating Build Process")
    print(f"  flip_x={flip_x}, flip_y={flip_y}, rotation={rotation}")
    print(f"  position={position}")
    print(f"  dummy_to_actual={dummy_to_actual}")
    print(f"{'='*70}")
    
    # Step 1: Deep copy (like process_bwm does)
    bwm_copy = deepcopy(bwm)
    print("\n[Step 1] After deepcopy:")
    _show_transition_faces(bwm_copy, "  ")
    
    # Step 2: Flip (like process_bwm does)
    bwm_copy.flip(flip_x, flip_y)
    print("\n[Step 2] After flip:")
    _show_transition_faces(bwm_copy, "  ")
    
    # Step 3: Rotate (like process_bwm does)
    bwm_copy.rotate(rotation)
    print("\n[Step 3] After rotate:")
    _show_transition_faces(bwm_copy, "  ")
    
    # Step 4: Translate (like process_bwm does)
    bwm_copy.translate(*position)
    print("\n[Step 4] After translate:")
    _show_transition_faces(bwm_copy, "  ")
    
    # Step 5: Remap transitions (like remap_transitions does)
    if dummy_to_actual:
        for dummy_idx, actual_idx in dummy_to_actual.items():
            _remap_transitions(bwm_copy, dummy_idx, actual_idx)
    print("\n[Step 5] After remap_transitions:")
    _show_transition_faces(bwm_copy, "  ")
    
    # Step 6: Serialize with bytes_bwm (this is where edges are computed)
    print("\n[Step 6] Serializing with bytes_bwm...")
    serialized = bytes_bwm(bwm_copy)
    
    # Step 7: Read back and check
    bwm_final = read_bwm(serialized)
    print("\n[Step 7] After roundtrip (bytes_bwm -> read_bwm):")
    _show_transition_faces(bwm_final, "  ")
    
    # Check edges
    edges = bwm_final.edges()
    edges_with_trans = [e for e in edges if e.transition is not None and e.transition >= 0]
    print(f"\n  Edges with transitions: {len(edges_with_trans)}")
    for edge in edges_with_trans:
        face_idx = None
        for i, f in enumerate(bwm_final.faces):
            if f is edge.face:
                face_idx = i
                break
        is_walkable = edge.face.material.walkable()
        print(f"    Edge: face_idx={face_idx}, edge_idx={edge.index}, transition={edge.transition}")
        print(f"           material={edge.face.material.name}, walkable={is_walkable}")
    
    return bwm_final


def _show_transition_faces(bwm, indent=""):
    """Show faces that have transitions."""
    walkable = [f for f in bwm.faces if f.material.walkable()]
    
    transition_faces = []
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
            transition_faces.append({
                "idx": i,
                "material": face.material.name,
                "is_walkable": is_walkable,
                "transitions": ", ".join(trans),
            })
    
    if not transition_faces:
        print(f"{indent}No faces with transitions")
    else:
        print(f"{indent}Faces with transitions: {len(transition_faces)}")
        for tf in transition_faces:
            status = "WALKABLE" if tf['is_walkable'] else "**NON_WALK**"
            print(f"{indent}  Face {tf['idx']}: {tf['material']} ({status}) - {tf['transitions']}")


def _remap_transitions(bwm, dummy_index, actual_index):
    """Remap transitions like IndoorMap.remap_transitions does."""
    for face in bwm.faces:
        if face.trans1 == dummy_index:
            face.trans1 = actual_index
        if face.trans2 == dummy_index:
            face.trans2 = actual_index
        if face.trans3 == dummy_index:
            face.trans3 = actual_index


def main():
    kit_path = Path(__file__).resolve().parent.parent / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "blackvulkar"
    
    # Analyze the hallway_1.wok (used in both step01 and step02)
    hallway_wok_path = kit_path / "hallway_1.wok"
    if not hallway_wok_path.exists():
        print(f"ERROR: Kit WOK not found: {hallway_wok_path}")
        return
    
    bwm = analyze_kit_wok(hallway_wok_path)
    
    # Simulate STEP01 build (working - from v2.0.4)
    # From step01.indoor: position=[-1.7924528301886795, 0.6132075471698124, 0], rotation=0.0
    print("\n" + "="*70)
    print("SIMULATING STEP01 BUILD (Working v2.0.4)")
    print("="*70)
    simulate_build_process(
        bwm,
        flip_x=False,
        flip_y=False,
        rotation=0.0,
        position=(-1.79, 0.61, 0),
        dummy_to_actual={20: 1, 21: 1}  # Both hooks connect to room 1
    )
    
    # Simulate STEP02 build (buggy - from v4.0.0b3)
    # From step02.indoor: position=[-0.09433962264150944, 6.320754716981132, 0], rotation=0.0
    print("\n" + "="*70)
    print("SIMULATING STEP02 BUILD (Buggy v4.0.0b3)")
    print("="*70)
    simulate_build_process(
        bwm,
        flip_x=False,
        flip_y=False,
        rotation=0.0,
        position=(-0.09, 6.32, 0),
        dummy_to_actual={20: 1, 21: 1}  # Both hooks connect to room 1
    )
    
    # The key question: why does step02 have transitions on NON_WALK faces?
    # Let's check if there's a face ordering issue
    print("\n" + "="*70)
    print("FACE ORDERING ANALYSIS")
    print("="*70)
    
    walkable = [f for f in bwm.faces if f.material.walkable()]
    unwalkable = [f for f in bwm.faces if not f.material.walkable()]
    
    print(f"Original ordering: {len(walkable)} walkable, {len(unwalkable)} unwalkable")
    
    # Check which faces have transitions
    for i, face in enumerate(bwm.faces):
        trans = []
        if face.trans1 is not None:
            trans.append(f"t1={face.trans1}")
        if face.trans2 is not None:
            trans.append(f"t2={face.trans2}")
        if face.trans3 is not None:
            trans.append(f"t3={face.trans3}")
        if trans:
            in_walkable = face in walkable
            walkable_idx = walkable.index(face) if in_walkable else None
            print(f"  Face {i}: {face.material.name} (in walkable list: {in_walkable}, walkable_idx={walkable_idx})")
            print(f"    Transitions: {', '.join(trans)}")
    
    # Now check after BWM writer reordering
    print("\n" + "="*70)
    print("BWM WRITER REORDERING ANALYSIS")
    print("="*70)
    
    # The BWM writer reorders faces: walkable first, then unwalkable
    reordered = walkable + unwalkable
    print(f"Reordered: walkable (indices 0-{len(walkable)-1}), unwalkable (indices {len(walkable)}-{len(reordered)-1})")
    
    for new_idx, face in enumerate(reordered):
        old_idx = bwm.faces.index(face)
        trans = []
        if face.trans1 is not None:
            trans.append(f"t1={face.trans1}")
        if face.trans2 is not None:
            trans.append(f"t2={face.trans2}")
        if face.trans3 is not None:
            trans.append(f"t3={face.trans3}")
        if trans:
            is_in_walkable_range = new_idx < len(walkable)
            status = "GOOD" if is_in_walkable_range else "**BUG**: transition on unwalkable range face"
            print(f"  Reordered idx {new_idx} (was {old_idx}): {face.material.name}")
            print(f"    Transitions: {', '.join(trans)} - {status}")


if __name__ == "__main__":
    main()

