"""Debug script to analyze BWM roundtrip differences."""

from __future__ import annotations

import io
import sys

from pathlib import Path

# Add paths
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "Libraries" / "PyKotor" / "src"))
sys.path.insert(0, str(repo_root / "Libraries" / "Utility" / "src"))

from pykotor.resource.formats.bwm import read_bwm  # noqa: E402
from pykotor.resource.formats.bwm.io_bwm import BWMBinaryWriter  # noqa: E402

# Find test file
test_file = repo_root / "tests" / "test_toolset" / "test_files" / "zio006j.wok"
if not test_file.exists():
    print(f"Test file not found: {test_file}")
    sys.exit(1)

data = test_file.read_bytes()
old = read_bwm(data)

# Roundtrip using writer directly
buf = io.BytesIO()
writer = BWMBinaryWriter(old, buf)
writer.write(auto_close=False)
buf.seek(0)
new_data = buf.read()
new = read_bwm(new_data)

print(f"Old faces: {len(old.faces)}")
print(f"New faces: {len(new.faces)}")

# Check face equality
old_set = set(old.faces)
new_set = set(new.faces)
only_in_old = old_set - new_set
only_in_new = new_set - old_set

print(f"Only in old: {len(only_in_old)}")
print(f"Only in new: {len(only_in_new)}")

# Analyze differences
if only_in_old:
    print("\n=== Faces only in OLD ===")
    for i, face in enumerate(list(only_in_old)[:3]):
        print(f"\nFace {i}:")
        print(f"  v1={face.v1}")
        print(f"  v2={face.v2}")
        print(f"  v3={face.v3}")
        print(f"  material={face.material}")
        print(f"  trans1={face.trans1}, trans2={face.trans2}, trans3={face.trans3}")

        # Try to find matching face in new by vertices
        for new_face in new.faces:
            if new_face.v1 == face.v1 and new_face.v2 == face.v2 and new_face.v3 == face.v3 and new_face.material == face.material:
                print("\n  MATCH in new by vertices+material:")
                print(f"  new trans1={new_face.trans1}, trans2={new_face.trans2}, trans3={new_face.trans3}")
                if new_face.trans1 != face.trans1 or new_face.trans2 != face.trans2 or new_face.trans3 != face.trans3:
                    print("  *** TRANSITION MISMATCH! ***")
                break
        else:
            print("  No match found in new by vertices+material")

# Count how many faces have transitions
old_with_trans = sum(1 for f in old.faces if f.trans1 is not None or f.trans2 is not None or f.trans3 is not None)
new_with_trans = sum(1 for f in new.faces if f.trans1 is not None or f.trans2 is not None or f.trans3 is not None)
print(f"\nFaces with transitions - old: {old_with_trans}, new: {new_with_trans}")

# Check if the issue is just transitions
print("\n=== Checking if only transitions differ ===")
mismatch_count = 0
for old_face in old.faces:
    found_match = False
    for new_face in new.faces:
        if new_face.v1 == old_face.v1 and new_face.v2 == old_face.v2 and new_face.v3 == old_face.v3 and new_face.material == old_face.material:
            found_match = True
            if new_face.trans1 != old_face.trans1 or new_face.trans2 != old_face.trans2 or new_face.trans3 != old_face.trans3:
                mismatch_count += 1
                if mismatch_count <= 5:
                    print("\nTransition mismatch:")
                    print(f"  old: t1={old_face.trans1}, t2={old_face.trans2}, t3={old_face.trans3}")
                    print(f"  new: t1={new_face.trans1}, t2={new_face.trans2}, t3={new_face.trans3}")
            break
    if not found_match:
        print(f"Face not found in new: v1={old_face.v1}, material={old_face.material}")

print(f"\nTotal transition mismatches: {mismatch_count}")

# Debug equality and hash
print("\n=== Debugging equality/hash ===")
if old.faces and new.faces:
    old_face = old.faces[0]
    new_face = None
    for nf in new.faces:
        if nf.v1 == old_face.v1 and nf.v2 == old_face.v2 and nf.v3 == old_face.v3 and nf.material == old_face.material:
            new_face = nf
            break

    if new_face:
        print(f"old_face == new_face: {old_face == new_face}")
        print(f"hash(old_face) == hash(new_face): {hash(old_face) == hash(new_face)}")
        print(f"hash(old_face): {hash(old_face)}")
        print(f"hash(new_face): {hash(new_face)}")

        # Check vertex equality
        print(f"\nold_face.v1 == new_face.v1: {old_face.v1 == new_face.v1}")
        print(f"old_face.v2 == new_face.v2: {old_face.v2 == new_face.v2}")
        print(f"old_face.v3 == new_face.v3: {old_face.v3 == new_face.v3}")

        # Check vertex identity
        print(f"\nold_face.v1 is new_face.v1: {old_face.v1 is new_face.v1}")

        # Verify set comparison works now
        if old_face in new_set:
            print("\nold_face is in new_set: True")
        else:
            print("\nold_face is in new_set: False")
