#!/usr/bin/env python3
"""Debug script for entry3 comment issue."""

from __future__ import annotations

import sys

from pathlib import Path

# Setup paths
REPO_ROOT = Path(__file__).resolve().parent
PYKOTOR_SRC = REPO_ROOT / "Libraries" / "PyKotor" / "src"
UTILITY_SRC = REPO_ROOT / "Libraries" / "Utility" / "src"

for path in (PYKOTOR_SRC, UTILITY_SRC):
    as_posix = path.as_posix()
    if as_posix not in sys.path:
        sys.path.insert(0, as_posix)

from pykotor.common.language import LocalizedString
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGReply

# Test case from test_dlg_reply_with_multiple_levels
reply1 = DLGReply(text=LocalizedString.from_english("R222"))
reply2 = DLGReply(text=LocalizedString.from_english("R223"))
reply3 = DLGReply(text=LocalizedString.from_english("R249"))
reply4 = DLGReply(text=LocalizedString.from_english("R225"))
reply5 = DLGReply(text=LocalizedString.from_english("R224"))

entry1 = DLGEntry(comment="E248")
entry2 = DLGEntry(comment="E221")
entry3 = DLGEntry(comment="E250")

reply1.links.append(DLGLink(node=entry1))
reply2.links.append(DLGLink(node=entry2))
entry1.links.append(DLGLink(node=reply2))
entry2.links.append(DLGLink(node=reply3))
reply3.links.append(DLGLink(node=entry3))
entry3.links.append(DLGLink(node=reply4))
# Note: reply4.links.append(DLGLink(node=reply5)) is invalid - replies link to entries, not replies

print("Before serialization:")
print(f"  entry3.comment: '{entry3.comment}'")
print(f"  entry3 key: {entry3.__hash__()}")

serialized = reply1.to_dict()

# Check if entry3 is in serialized data
import json

serialized_str = json.dumps(serialized, indent=2, default=str)
if "E250" in serialized_str:
    print("\nE250 found in serialized data")
else:
    print("\nE250 NOT found in serialized data")

# Check if entry3 key is referenced
entry3_key = str(entry3.__hash__())
if entry3_key in serialized_str:
    print(f"entry3 key ({entry3_key}) found in serialized data")
else:
    print(f"entry3 key ({entry3_key}) NOT found in serialized data")

deserialized = DLGReply.from_dict(serialized)
entry3_deserialized = deserialized.links[0].node.links[0].node.links[0].node.links[0].node

print("\nAfter deserialization:")
print(f"  entry3_deserialized.comment: '{entry3_deserialized.comment}'")
print("  Expected: 'E250'")
print(f"  Match: {entry3_deserialized.comment == 'E250'}")
