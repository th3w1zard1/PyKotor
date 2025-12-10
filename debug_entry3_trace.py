#!/usr/bin/env python3
"""Trace entry3 deserialization to see when comment is set."""

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

# Monkey patch to trace comment setting
original_setattr = setattr
comment_set_calls = []


def traced_setattr(obj, name, value):
    if name == "comment" and isinstance(obj, DLGEntry):
        comment_set_calls.append((obj._hash_cache, value, f"Setting comment to '{value}'"))
    return original_setattr(obj, name, value)


# Test case
reply1 = DLGReply(text=LocalizedString.from_english("R222"))
reply2 = DLGReply(text=LocalizedString.from_english("R223"))
reply3 = DLGReply(text=LocalizedString.from_english("R249"))
entry1 = DLGEntry(comment="E248")
entry2 = DLGEntry(comment="E221")
entry3 = DLGEntry(comment="E250")

entry3_key = entry3.__hash__()
print(f"Original entry3 key: {entry3_key}")
print(f"Original entry3 comment: '{entry3.comment}'")

reply1.links.append(DLGLink(node=entry1))
reply2.links.append(DLGLink(node=entry2))
entry1.links.append(DLGLink(node=reply2))
entry2.links.append(DLGLink(node=reply3))
reply3.links.append(DLGLink(node=entry3))

serialized = reply1.to_dict()


# Find entry3's key in serialized data
def find_entry3_key(d):
    if isinstance(d, dict):
        if d.get("type") == "DLGEntry" and "data" in d:
            comment = d.get("data", {}).get("comment", {}).get("value", "")
            if comment == "E250":
                return d.get("key")
        for v in d.values():
            if isinstance(v, (dict, list)):
                result = find_entry3_key(v) if isinstance(v, dict) else None
                if result is not None:
                    return result
                if isinstance(v, list):
                    for item in v:
                        result = find_entry3_key(item) if isinstance(item, dict) else None
                        if result is not None:
                            return result
    return None


entry3_serialized_key = find_entry3_key(serialized)
print(f"entry3 key in serialized data: {entry3_serialized_key}")

# Temporarily patch setattr
import builtins

builtins.setattr = traced_setattr

deserialized = DLGReply.from_dict(serialized)

# Restore setattr
builtins.setattr = original_setattr

entry3_deserialized = deserialized.links[0].node.links[0].node.links[0].node.links[0].node
print("\nAfter deserialization:")
print(f"  entry3_deserialized._hash_cache: {entry3_deserialized._hash_cache}")
print(f"  entry3_deserialized.comment: '{entry3_deserialized.comment}'")
print("\nComment set calls:")
for key, value, msg in comment_set_calls:
    print(f"  {msg} on object with key {key}")
