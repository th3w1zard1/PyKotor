"""Field mappings and search configuration for reference finding.

This module defines which GFF fields should be searched for different types of references,
based on the KotOR findrefs utility functionality.
"""

from __future__ import annotations

from pykotor.resource.formats.gff.gff_data import GFFFieldType


# Field mappings for script references (ResRef fields that contain script names)
SCRIPT_FIELDS: dict[str, set[str]] = {
    "IFO": {
        "Mod_OnAcquireItem",
        "Mod_OnActivateItem",
        "Mod_OnClientLeave",
        "Mod_OnHeartbeat",
        "Mod_OnLoad",
        "Mod_OnStart",
        "Mod_OnPlrDeath",
        "Mod_OnPlrLvlUp",
        "Mod_OnPlrRest",
        "Mod_OnSpawnBtnDn",
        "Mod_OnUnAqreItem",
        "Mod_OnUsrDefined",
    },
    "ARE": {
        "OnEnter",
        "OnExit",
        "OnHeartbeat",
        "OnUserDefined",
    },
    "UTC": {
        "ScriptHeartbeat",
        "ScriptAttacked",
        "ScriptDamaged",
        "ScriptDeath",
        "ScriptDialogue",
        "ScriptDisturbed",
        "ScriptEndDialogu",
        "ScriptEndRound",
        "ScriptOnNotice",
        "ScriptRested",
        "ScriptSpawn",
        "ScriptSpellAt",
        "ScriptUserDefine",
    },
    "UTD": {
        "OnClick",
        "OnClosed",
        "OnDamaged",
        "OnDeath",
        "OnFailToOpen",
        "OnHeartbeat",
        "OnLock",
        "OnMeleeAttacked",
        "OnOpen",
        "OnSpellCastAt",
        "OnTrapTriggered",
        "OnUnlock",
        "OnUserDefined",
    },
    "UTM": {
        "OnOpenStore",
    },
    "UTP": {
        "OnClosed",
        "OnDamaged",
        "OnDeath",
        "OnDisarm",
        "OnEndDialogue",
        "OnHeartbeat",
        "OnInvDisturbed",
        "OnLock",
        "OnMeleeAttacked",
        "OnOpen",
        "OnSpellCastAt",
        "OnTrapTriggered",
        "OnUnlock",
        "OnUsed",
        "OnUserDefined",
    },
    "UTT": {
        "ScriptHeartbeat",
        "ScriptOnEnter",
        "ScriptOnExit",
        "ScriptUserDefine",
    },
    "DLG": {
        # DLG has nested structures, handled specially
        "StartingList",  # StartingList[].Active, StartingList[].Active2 (TSL), StartingList[].ParamStrA (TSL), StartingList[].ParamStrB (TSL)
        "EntryList",  # EntryList[].Script, EntryList[].Script2 (TSL), EntryList[].RepliesList[].Active, EntryList[].RepliesList[].Active2 (TSL), EntryList[].RepliesList[].ParamStrA (TSL), EntryList[].RepliesList[].ParamStrB (TSL)
        "ReplyList",  # ReplyList[].Script, ReplyList[].Script2 (TSL), ReplyList[].EntriesList[].Active, ReplyList[].EntriesList[].Active2 (TSL), ReplyList[].EntriesList[].ParamStrA (TSL), ReplyList[].EntriesList[].ParamStrB (TSL)
    },
}

# Field mappings for tag references (String fields)
TAG_FIELDS: dict[str, set[str]] = {
    "UTC": {"Tag"},
    "UTD": {"Tag"},
    "UTM": {"Tag"},
    "UTP": {"Tag"},
    "UTT": {"Tag"},
    "UTI": {"Tag"},
    # Also search ItemList and Equip_ItemList in UTC/UTP/UTM
}

# Field mappings for TemplateResRef references (ResRef fields)
TEMPLATE_RESREF_FIELDS: dict[str, set[str]] = {
    "UTC": {"TemplateResRef"},
    "UTD": {"TemplateResRef"},
    "UTM": {"TemplateResRef"},
    "UTP": {"TemplateResRef"},
    "UTT": {"TemplateResRef"},
    "UTI": {"TemplateResRef"},
}

# Field mappings for conversation references (ResRef fields)
CONVERSATION_FIELDS: dict[str, set[str]] = {
    "UTC": {"Conversation"},
    "UTD": {"Conversation"},
    "UTP": {"Conversation"},
    "IFO": {"Mod_OnStart"},  # Some modules reference conversations in Mod_OnStart
}

# Field mappings for ItemList searches (for tag/resref searches in inventory)
ITEMLIST_FIELDS: dict[str, set[str]] = {
    "UTC": {"ItemList", "Equip_ItemList"},
    "UTP": {"ItemList"},
    "UTM": {"ItemList"},
}

# Nested field paths for DLG script searches
DLG_SCRIPT_PATHS: list[tuple[str, str]] = [
    # (list_field, script_field)
    ("StartingList", "Active"),
    ("StartingList", "Active2"),  # TSL only
    ("StartingList", "ParamStrA"),  # TSL only
    ("StartingList", "ParamStrB"),  # TSL only
    ("EntryList", "Script"),
    ("EntryList", "Script2"),  # TSL only
    ("EntryList", "ActionParamStrA"),  # TSL only
    ("EntryList", "ActionParamStrB"),  # TSL only
    ("EntryList", "RepliesList"),  # Nested: RepliesList[].Active, etc.
    ("ReplyList", "Script"),
    ("ReplyList", "Script2"),  # TSL only
    ("ReplyList", "ActionParamStrA"),  # TSL only
    ("ReplyList", "ActionParamStrB"),  # TSL only
    ("ReplyList", "EntriesList"),  # Nested: EntriesList[].Active, etc.
]

# Nested field paths for DLG reply/entry condition searches
DLG_CONDITION_PATHS: list[tuple[str, str]] = [
    ("EntryList", "RepliesList"),  # RepliesList[].Active, RepliesList[].Active2 (TSL), RepliesList[].ParamStrA (TSL), RepliesList[].ParamStrB (TSL)
    ("ReplyList", "EntriesList"),  # EntriesList[].Active, EntriesList[].Active2 (TSL), EntriesList[].ParamStrA (TSL), EntriesList[].ParamStrB (TSL)
]

# Field types to search for each reference type
SCRIPT_FIELD_TYPES: set[GFFFieldType] = {GFFFieldType.ResRef}
TAG_FIELD_TYPES: set[GFFFieldType] = {GFFFieldType.String}
TEMPLATE_RESREF_FIELD_TYPES: set[GFFFieldType] = {GFFFieldType.ResRef}
CONVERSATION_FIELD_TYPES: set[GFFFieldType] = {GFFFieldType.ResRef}
ITEMLIST_FIELD_TYPES: set[GFFFieldType] = {GFFFieldType.String, GFFFieldType.ResRef}  # Can contain both tags and resrefs


def get_script_fields_for_type(file_type: str) -> set[str]:
    """Get script field names for a specific GFF file type.

    Args:
    ----
        file_type: File type abbreviation (e.g., "UTC", "UTD", "ARE")

    Returns:
    -------
        Set of field names to search for scripts
    """
    return SCRIPT_FIELDS.get(file_type, set())


def get_tag_fields_for_type(file_type: str) -> set[str]:
    """Get tag field names for a specific GFF file type.

    Args:
    ----
        file_type: File type abbreviation

    Returns:
    -------
        Set of field names to search for tags
    """
    fields = TAG_FIELDS.get(file_type, set()).copy()
    # Also include ItemList fields for UTC/UTP/UTM
    if file_type in {"UTC", "UTP", "UTM"}:
        fields.update(ITEMLIST_FIELDS.get(file_type, set()))
    return fields


def get_template_resref_fields_for_type(file_type: str) -> set[str]:
    """Get TemplateResRef field names for a specific GFF file type.

    Args:
    ----
        file_type: File type abbreviation

    Returns:
    -------
        Set of field names to search for TemplateResRef
    """
    return TEMPLATE_RESREF_FIELDS.get(file_type, set())


def get_conversation_fields_for_type(file_type: str) -> set[str]:
    """Get conversation field names for a specific GFF file type.

    Args:
    ----
        file_type: File type abbreviation

    Returns:
    -------
        Set of field names to search for conversations
    """
    return CONVERSATION_FIELDS.get(file_type, set())


def get_itemlist_fields_for_type(file_type: str) -> set[str]:
    """Get ItemList field names for a specific GFF file type.

    Args:
    ----
        file_type: File type abbreviation

    Returns:
    -------
        Set of field names containing item lists
    """
    return ITEMLIST_FIELDS.get(file_type, set())


def get_all_searchable_file_types() -> set[str]:
    """Get all file types that can be searched for references.

    Returns:
    -------
        Set of file type abbreviations
    """
    all_types: set[str] = set()
    all_types.update(SCRIPT_FIELDS.keys())
    all_types.update(TAG_FIELDS.keys())
    all_types.update(TEMPLATE_RESREF_FIELDS.keys())
    all_types.update(CONVERSATION_FIELDS.keys())
    all_types.update(ITEMLIST_FIELDS.keys())
    return all_types

