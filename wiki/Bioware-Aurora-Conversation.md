# Conversation
*Official Bioware Aurora Documentation*

---

## Page 1

BioWare Corp.
http://www.bioware.com
BioWare Aurora Engine
Conversation File Format
1. Introduction
A Conversation is a branching set of predefined text strings ("lines") that a player and one or more
NPCs can say to each other, along with the conditions that govern which lines are said and which are
not, which are available to say and which are not, and the actions that accompany each line as it is said.
Conversations are stored as .dlg files, and may be present in global game resources in BIF files, in the
override directory, in a module, or in a savegame. Conversation files use BioWare's Generic File
Format (GFF), and it is assumed that the reader of this document is familiar with GFF. The GFF
FileType string in the header of repute.fac is "DLG ".
This document uses color conventions from the toolset's Conversation Editor when referring to certain
data structures. In the Conversation Editor, NPC text shows up in red by default, and Player text shows
up in blue by default. This document uses the same color schemes for the names of data structures that
refer to NPC or Player text.
2. Conversation Structs
2.1. Top Level Struct
Table 2.1: Conversation Top Level Struct
Label
Type
Description
DelayEntry
### DWORD

Number of seconds to wait before showing each entry.
DelayReply
### DWORD

Number of seconds to wait before showing each reply.
EndConverAbort
CResRef
ResRef of script to run when the conversation is
aborted, such as by combat, hitting the ESC key, or
saving a game in the middle of conversation.
EndConversation
CResRef
ResRef of script to run when the conversation ends
normally.
EntryList
List
List of NPC Dialog Structs. StructID = list index.
NumWords
### DWORD

Number of words counted in this conversation.
Dynamically updated as the user edits the conversation
in the toolset's Conversation Editor. Informational only.
Does not serve a purpose in game.
PreventZoomIn
### BYTE

1 if initiating the conversation will cause the game
camera to zoom in on the speakers, if the "Enable
Dialog Zoom" checkbox is checked under the game's
"Control Options". If a conversation is spoken as a one-
liner popup over an NPC's head, then no zoomin occurs
regardless of Game Options or the PreventZoomin flag.

0 if initiating the conversation will not cause the game
camera to move.
ReplyList
List
List of Player Dialog Structs. StructID = list index.
StartingList
List
List of NPC Sync Structs at the root level of the
conversation. These are the entries that are candidates
for being the first thing that the NPC says when the
conversation starts.
These entries are sorted in the same order as they


## Page 2

BioWare Corp.
http://www.bioware.com
appear in the Conversation Editor in the toolset, with
the first entries in the list being the highest in the
treeview.
StructID = list index.
2.2. Dialog Structs
A Dialog Struct defines a line of dialog in a conversation tree, plus any additional data relevant to that
line. It may be a line spoken by a player or by an NPC.
Dialog Structs appear in the ReplyList and the EntryList found in the Top-Level Struct of a conversation
file.
2.2.1. Dialog Struct
The Table below lists the Fields that are present in a Dialog Struct.
Table 2.2.1: Fields in Dialog Struct (StructID = list index)
Label
Type
Description
Animation
### DWORD

0 = default, talk normal
28 = taunt
29 = greeting
30 = listen
33 = worship
34 = overlay salute
35 = bow
37 = steal
38 = talk normal
39 = talk pleading
40 = talk forceful
41 = talk laugh
44 = victory fighter
45 = victory mage
46 = victory thief
48 = look far
70 = overlay drink
71 = overlay read
88 = play no animation
AnimLoop
### BYTE

Obsolete. No longer used.
Did not play well with animation system because
"looping" is a property that is part of an animation, not
an external property that can be applied to an
animation.
Comment
CExoString
Conversation writer's comment. In the Conversation
Editor, this comment only appears when editing the
original version of the line of dialog. When editing a
link (shows up in grey by default), the link comment
shows up instead (see Section 2.3).
Delay
### DWORD

0xFFFFFFFF
Quest
CExoString
Tag of Journal Category to update when showing this
line of conversation.
QuestEntry
### DWORD

ID of the Journal Entry to show when showing this line
of conversation.
This Field is present only if Quest Field is non-empty.


## Page 3

BioWare Corp.
http://www.bioware.com
Script
CResRef
ResRef of script to run when showing this line.
Sound
CResRef
ResRef of WAV file to play
Text
CExoLocString
Localized text to display to the user for this line of
dialog.
2.2.2. Player Reply Dialog Struct
A Dialog Struct contained in the Player ReplyList contains all the Fields listed in Table 2.2.1, plus
those Fields listed in Table 2.2.2.
Table 2.2.2: Additional Fields in Reply Struct (StructID = list index)
Label
Type
Description
EntriesList
List
List of Sync Structs describing the list of possible NPC
replies to this line of player dialog..
Struct ID = list index.
2.2.3. NPC Entry Dialog Struct
A Dialog Struct contained in the NPC EntryList contains all the Fields found in a Dialog Struct as
detailed in Table 2.2.1, plus those Fields listed in Table 2.2.3.
Table 2.2.3: Additional Fields in Entry Struct (StructID = list index)
Label
Type
Description
RepliesList
List
List of Sync Structs describing the list of possible
Player replies to this line of NPC dialog.
Struct ID = list index.
Speaker
CExoString
Tag of the speaker.
Blank if the speaker is the conversation owner.
2.3. Sync Structs
A Sync Struct describes a pointer or reference to a Dialog Struct.
A Sync Struct may refer directly to a Dialog Struct, or it may be a "link" to the original line of dialog. In
the toolset's Conversation Editor, direct references show up in normal text color (blue for player text,
red for NPC text), while links show up in grey text.
In a conversation tree, each line of dialog (ie., node in the tree) has several properties associated with it,
as described in Section 2.2. However, there are some properties that are not part of the dialog lines
themselves, but are instead stored on the Sync Structs that point to those dialog lines.
For all dialog lines, the "Action Taken" script is part of the Sync Struct, not the Dialog Struct.
For linked lines of dialog (ie., the ones that appear by default in grey text in the Conversation Editor),
the Comment is also part of the Sync Struct, and not the Dialog Struct.
2.3.1. NPC StartingList Sync Struct
Sync Structs found in the StartingList point to a NPC Dialogs in the Top-Level Struct's EntryList. The
StartingList is the list of all lines of dialog that appear at the root level of the conversation tree.
The Table below lists the Fields that are present in a StartingList Sync Struct.


## Page 4

BioWare Corp.
http://www.bioware.com
Table 2.3.1: Fields in StartingList Sync Struct (StructID = list index)
Label
Type
Description
Active
CResRef
ResRef of conditional script to run to determine if this
line of conversation appears to the player. If the script
returns FALSE, then skip to the next Link Struct in the
StartingList.
Index
### DWORD

Index into Top-Level Struct EntryList.
2.3.2. Player RepliesList Link Struct
Sync Structs in the RepliesList of an NPC Entry Dialog Struct point to Player Dialogs in the Top-Level
Struct's ReplyList.
The Table below lists the Fields that are present in a RepliesList Sync Struct.
Table 2.3.2: Fields in RepliesList Sync Struct (StructID = list index)
Label
Type
Description
Active
CResRef
ResRef of conditional script to run to determine if this
line of conversation appears to the player.
Index
### DWORD

Index into Top-Level Struct ReplyList.
IsChild
### BYTE

1 if this is a link, and there is a LinkComment.
0 if this is a direct reference to the dialog, and there is
no LinkComment.
LinkComment
CExoString
This Field is present only if this Sync Struct is for a
linked line of conversation (appears grey by default in
the toolset Conversation Editor).
If this is a link, then the Conversation Editor will show
and edit the LinkComment instead of the Dialog
Struct's own Comment.
2.3.3. NPC EntriesList Sync Struct
Sync Structs in the EntriesList of a Player Reply Dialog Struct point to NPC Dialogs in the Top-Level
Struct's EntryList.
The Table below lists the Fields that are present in an EntriesList Sync Struct.
Table 2.3.3: Fields in EntriesList Sync Struct (StructID = list index)
Label
Type
Description
Active
CResRef
ResRef of conditional script to run to determine if the
NPC speaks this line. If the script returns FALSE, then
check the next Link Struct in the current EntriesList.
Index
### DWORD

Index into Top-Level Struct EntryList.
IsChild
### BYTE

1 if this is a link, and there is a LinkComment.
0 if this is a direct reference to the dialog, and there is
no LinkComment.
LinkComment
CExoString
This Field is present only if this Sync Struct is for a
linked line of conversation (appears grey by default in
the toolset Conversation Editor).
If this is a link, then the Conversation Editor will show
and edit the LinkComment instead of the Dialog
Struct's own Comment.



