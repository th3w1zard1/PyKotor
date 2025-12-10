#!/usr/bin/env python3
"""Debug script for entry3 comment issue - check if ref is used."""

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

serialized = reply1.to_dict()


# Find entry3 in serialized data and check if it's a ref or full data
def find_entry3(d, path=""):
    if isinstance(d, dict):
        if d.get("type") == "DLGEntry" and "key" in d:
            key = d.get("key")
            comment = d.get("data", {}).get("comment", {}).get("value", "")
            if comment == "E250" or (isinstance(key, int) and str(key) == "131150836496835401093078811402700356004"):
                print(f"Found entry3 at: {path}")
                print(f"  Has 'ref': {'ref' in d}")
                print(f"  Has 'data': {'data' in d}")
                if "data" in d:
                    print(f"  Comment in data: {d['data'].get('comment', {}).get('value', 'NOT FOUND')}")
                return True
        for k, v in d.items():
            if find_entry3(v, f"{path}.{k}"):
                return True
    elif isinstance(d, list):
        for i, item in enumerate(d):
            if find_entry3(item, f"{path}[{i}]"):
                return True
    return False


print("Searching for entry3 in serialized data:")
find_entry3(serialized)
