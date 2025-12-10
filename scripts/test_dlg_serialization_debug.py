"""Debug DLG serialization issue."""  # noqa: INP001

from __future__ import annotations

import sys

sys.path.insert(0, "Libraries/PyKotor/src")
sys.path.insert(0, "Libraries/Utility/src")

from pykotor.common.language import Gender, Language, LocalizedString  # pyright: ignore[reportMissingImports]
from pykotor.resource.generics.dlg import DLGEntry, DLGLink, DLGReply  # pyright: ignore[reportMissingImports]

# Create the same structure as the test
entry1 = DLGEntry(comment="E248")
entry2 = DLGEntry(comment="E221")
entry3 = DLGEntry(comment="E250")

reply1 = DLGReply(text=LocalizedString.from_english("R222"))
reply2 = DLGReply(text=LocalizedString.from_english("R223"))
reply3 = DLGReply(text=LocalizedString.from_english("R249"))
reply4 = DLGReply(text=LocalizedString.from_english("R225"))
reply5 = DLGReply(text=LocalizedString.from_english("R224"))

entry1.links.append(DLGLink(node=reply1))
reply1.links.extend([DLGLink(node=entry2), DLGLink(node=reply2)])  # type: ignore[arg-type]
reply2.links.append(DLGLink(node=entry3))
entry3.links.append(DLGLink(node=reply4))
reply4.links.append(DLGLink(node=reply5))  # type: ignore[arg-type]
entry2.links.append(DLGLink(node=reply3))

# Check original structure
print("Original structure:")
print(f"  reply4.links[0].node.text = {reply4.links[0].node.text.get(Language.ENGLISH, Gender.MALE)}")
print(f"  reply4 is reply5: {reply4 is reply5}")
print(f"  reply4.links[0].node is reply5: {reply4.links[0].node is reply5}")

# Serialize
serialized = entry1.to_dict()

# Deserialize
deserialized = DLGEntry.from_dict(serialized)

# Navigate to reply4
deserialized_reply4 = deserialized.links[0].node.links[1].node.links[0].node.links[0].node
print("\nDeserialized structure:")
print(f"  deserialized_reply4.text = {deserialized_reply4.text.get(Language.ENGLISH, Gender.MALE)}")
print(f"  deserialized_reply4.links count: {len(deserialized_reply4.links)}")
if len(deserialized_reply4.links) > 0:
    print(f"  deserialized_reply4.links[0].node.text = {deserialized_reply4.links[0].node.text.get(Language.ENGLISH, Gender.MALE)}")
    print(f"  deserialized_reply4.links[0].node is deserialized_reply4: {deserialized_reply4.links[0].node is deserialized_reply4}")

# Extra debugging: verify node_map preserves shared node identity
shared_reply = DLGReply(text=LocalizedString.from_english("Shared Reply"))
link_a = DLGLink(node=shared_reply, list_index=0)
link_b = DLGLink(node=shared_reply, list_index=1)

node_map: dict[str | int, object] = {}
link_a_dict = link_a.to_dict(node_map)
link_b_dict = link_b.to_dict(node_map)

restore_map: dict[str | int, object] = {}
restored_a = DLGLink.from_dict(link_a_dict, restore_map)
restored_b = DLGLink.from_dict(link_b_dict, restore_map)

print("\nShared node identity check:")
print(f"  restored_a.node is restored_b.node -> {restored_a.node is restored_b.node}")
print(f"  restored_a.node text: {restored_a.node.text.get(Language.ENGLISH, Gender.MALE)}")
print(f"  link indices: {restored_a.list_index}, {restored_b.list_index}")