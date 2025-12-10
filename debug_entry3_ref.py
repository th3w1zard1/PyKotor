#!/usr/bin/env python3
"""Check if entry3 is referenced via ref in serialized data."""

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
entry1 = DLGEntry(comment="E248")
entry2 = DLGEntry(comment="E221")
entry3 = DLGEntry(comment="E250")

reply1.links.append(DLGLink(node=entry1))
reply2.links.append(DLGLink(node=entry2))
entry1.links.append(DLGLink(node=reply2))
entry2.links.append(DLGLink(node=reply3))
reply3.links.append(DLGLink(node=entry3))

entry3_key = entry3.__hash__()
serialized = reply1.to_dict()


# Find all references to entry3_key
def find_refs(d, key, path="", refs=[]):
    if isinstance(d, dict):
        if d.get("ref") == key:
            refs.append((path, "ref"))
        if d.get("key") == key:
            refs.append((path, "full"))
        for k, v in d.items():
            find_refs(v, key, f"{path}.{k}", refs)
    elif isinstance(d, list):
        for i, item in enumerate(d):
            find_refs(item, key, f"{path}[{i}]", refs)
    return refs


refs = find_refs(serialized, entry3_key)
print(f"Found {len(refs)} references to entry3 (key: {entry3_key}):")
for path, ref_type in refs:
    print(f"  {ref_type} at {path}")
