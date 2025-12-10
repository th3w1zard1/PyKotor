"""Debug DLG serialization issue turned into executable tests."""  # noqa: INP001

from __future__ import annotations

import sys

sys.path.insert(0, "Libraries/PyKotor/src")
sys.path.insert(0, "Libraries/Utility/src")

from pykotor.common.language import Gender, Language, LocalizedString  # pyright: ignore[reportMissingImports]
from pykotor.resource.generics.dlg import DLGEntry, DLGLink, DLGReply  # pyright: ignore[reportMissingImports]


def _build_nested_chain() -> DLGEntry:
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
    return entry1


def test_serialization_roundtrip_preserves_deep_chain():
    """Ensure nested entry/reply chains survive to_dict/from_dict roundtrips."""
    root = _build_nested_chain()
    serialized = root.to_dict()
    deserialized = DLGEntry.from_dict(serialized)

    # Walk the reconstructed chain to validate ordering and identity
    reply1 = deserialized.links[0].node
    reply2 = deserialized.links[0].node.links[1].node
    entry3 = reply2.links[0].node
    reply4 = entry3.links[0].node
    reply5 = reply4.links[0].node

    assert reply1.text.get(Language.ENGLISH, Gender.MALE) == "R222"
    assert reply2.text.get(Language.ENGLISH, Gender.MALE) == "R223"
    assert entry3.comment == "E250"
    assert reply4.text.get(Language.ENGLISH, Gender.MALE) == "R225"
    assert reply5.text.get(Language.ENGLISH, Gender.MALE) == "R224"


def test_shared_node_identity_survives_link_roundtrip():
    """Ensure shared nodes are restored as the same object when deserialized."""
    shared_reply = DLGReply(text=LocalizedString.from_english("Shared Reply"))
    link_a = DLGLink(node=shared_reply, list_index=0)
    link_b = DLGLink(node=shared_reply, list_index=1)

    node_map: dict[str | int, object] = {}
    link_a_dict = link_a.to_dict(node_map)
    link_b_dict = link_b.to_dict(node_map)

    restore_map: dict[str | int, object] = {}
    restored_a = DLGLink.from_dict(link_a_dict, restore_map)
    restored_b = DLGLink.from_dict(link_b_dict, restore_map)

    assert restored_a.node is restored_b.node
    assert restored_a.node.text.get(Language.ENGLISH, Gender.MALE) == "Shared Reply"
    assert {restored_a.list_index, restored_b.list_index} == {0, 1}