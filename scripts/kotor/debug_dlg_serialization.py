"""Debug script to understand DLG serialization issue."""
from pykotor.resource.generics.dlg import DLGEntry, DLGReply, DLGLink
from pykotor.common.language import LocalizedString, Language, Gender

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
reply1.links.extend([DLGLink(node=entry2), DLGLink(node=reply2)])
reply2.links.append(DLGLink(node=entry3))
entry3.links.append(DLGLink(node=reply4))
reply4.links.append(DLGLink(node=reply5))
entry2.links.append(DLGLink(node=reply3))

# Serialize
serialized = entry1.to_dict()

# Print the structure
import json
print("Serialized structure:")
print(json.dumps(serialized, indent=2, default=str))

# Deserialize
deserialized = DLGEntry.from_dict(serialized)

# Check reply4's link
print("\nOriginal reply4 links:")
for i, link in enumerate(reply4.links):
    print(f"  link[{i}].node.text = {link.node.text.get(Language.ENGLISH, Gender.MALE)}")

print("\nDeserialized reply4 links:")
deserialized_reply4 = deserialized.links[0].node.links[1].node.links[0].node.links[0].node
for i, link in enumerate(deserialized_reply4.links):
    print(f"  link[{i}].node.text = {link.node.text.get(Language.ENGLISH, Gender.MALE)}")
    print(f"  link[{i}].node is reply4: {link.node is deserialized_reply4}")

