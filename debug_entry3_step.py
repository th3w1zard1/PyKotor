#!/usr/bin/env python3
"""Step through entry3 deserialization."""

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

from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGReply
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.common.language import LocalizedString

# Test case from test_dlg_reply_with_multiple_levels
reply1 = DLGReply(text=LocalizedString.from_english("R222"))
reply2 = DLGReply(text=LocalizedString.from_english("R223"))
reply3 = DLGReply(text=LocalizedString.from_english("R249"))
entry1 = DLGEntry(comment="E248")
entry2 = DLGEntry(comment="E221")
entry3 = DLGEntry(comment="E250")

reply1.links.append(DLGLink(node=entry1))
reply2.links.append(DLGLink(node=entry2))
entry1.links.append(DLGLink(node=reply2))
entry2.links.append(DLGLink(node=reply3))
reply3.links.append(DLGLink(node=entry3))

serialized = reply1.to_dict()

# Find entry3's serialized data
def find_entry3_data(d, path=""):
    if isinstance(d, dict):
        if d.get("type") == "DLGEntry" and "data" in d:
            comment = d.get("data", {}).get("comment", {}).get("value", "")
            if comment == "E250":
                return d
        for k, v in d.items():
            result = find_entry3_data(v, f"{path}.{k}")
            if result:
                return result
    elif isinstance(d, list):
        for i, item in enumerate(d):
            result = find_entry3_data(item, f"{path}[{i}]")
            if result:
                return result
    return None

entry3_data = find_entry3_data(serialized)
if entry3_data:
    print("entry3 serialized data:")
    print(f"  key: {entry3_data.get('key')}")
    print(f"  comment in data: {entry3_data.get('data', {}).get('comment', {}).get('value', 'NOT FOUND')}")
    print(f"  node_data keys: {list(entry3_data.get('data', {}).keys())}")
    
    # Now deserialize and check
    deserialized = DLGReply.from_dict(serialized)
    entry3_deserialized = deserialized.links[0].node.links[0].node.links[0].node.links[0].node
    print("\nAfter deserialization:")
    print(f"  entry3_deserialized.comment: '{entry3_deserialized.comment}'")
    print(f"  entry3_deserialized._hash_cache: {entry3_deserialized._hash_cache}")
    print(f"  entry3_deserialized.__dict__: {entry3_deserialized.__dict__}")

