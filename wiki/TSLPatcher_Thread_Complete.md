# TSLPatcher v1.2.10b1 (mod installer) - Complete Thread Archive

**Source:** LucasForums Archive - <https://lucasforumsarchive.com/thread/149285-tslpatcher-v1210b1-mod-installer>

**Note: LucasForums Archive Project**

The content here was reconstructed by scraping the Wayback Machine in an effort to restore some of what was lost when LF went down. The LucasForums Archive Project claims no ownership over the content or assets that were archived on archive.org.

This project is meant for research purposes only.

---

## Page 1 of 6

**[stoffe](https://lucasforumsarchive.com/user/121047 "stoffe's profile")** - 05-25-2005, 6:13 AM - **#1**

Latest version: TSLPatcher 1.2.10b1, ChangeEdit 1.0.5b1 (<http://www.starwarsknights.com/tools.php#mctl>)

(You can check which version you currently have by opening the Properties window of the EXE [file](GFF-File-Format) in Windows Explorer and check on the Version tab.)

\* \* \*

About TSLPatcher:
The TSLPatcher is a small application intended to be used as a mod installer for KotOR and K2:TSL. Despite the name it works with both games in the series. Its purpose is to move some of the burden of making different mods compatible from the end mod user to the mod developer.

ChangeEdit is a support utility, used to create TSLPatcher configuration [files](GFF-File-Format) with a somewhat user-friendly graphical user interface. (Well, more user-friendly than creating the config [files](GFF-File-Format) by hand in notepad, anyway.)

It can, in general terms:

- Add new entries to the [dialog.tlk](TLK-File-Format) [file](GFF-File-Format), so you won't have to distribute the whole 10 MB [file](GFF-File-Format) with a mod, and make it compatible with other mods adding new entries.

- Modify and add new lines and columns to [2DA files](2DA-File-Format) that might already exist in the user's override folder, allowing different mods to modify the same [2DA file](2DA-File-Format) with less risk of causing incompatibility.

- Modify [values](GFF-File-Format#data-types) in [fields](GFF-File-Format#file-structure) and add new [fields](GFF-File-Format#file-structure) to [GFF](GFF-File-Format) [format](GFF-File-Format) files (UT\*, [DLG](GFF-File-Format#dlg-dialogue), [JRL](GFF-File-Format#jrl-journal), [GIT](GFF-File-Format#git-game-instance-template), [ARE](GFF-File-Format#are-area), [IFO](GFF-File-Format#ifo-module-info) etc...) that might already exist in the user's override folder or inside [ERF](ERF-File-Format)/RIM archives. Again to reduce incompatibility when different mods need to do things to the same [file](GFF-File-Format).

- Dynamically assign StrRefs from your new [dialog.tlk](TLK-File-Format) entries to [2DA](2DA-File-Format), [GFF](GFF-File-Format), [NSS](NSS-File-Format) and [SSF](SSF-File-Format) [format](GFF-File-Format) [files](GFF-File-Format), allowing you to use your new [TLK](TLK-File-Format) entries regardless of which [StrRef](TLK-File-Format#string-references-strref) [indexes](2DA-File-Format#row-labels) they were added as, through the use of token references. (E.g. add the correct [StrRef](TLK-File-Format#string-references-strref) [values](GFF-File-Format#data-types) to the "name" and "desc" column in [spells.2da](2DA-spells) if you add a new force power.)

- Dynamically assign [values](GFF-File-Format#data-types) from [2DA](2DA-File-Format) and [GFF files](GFF-File-Format) to cells and [fields](GFF-File-Format#file-structure) in other [2DA](2DA-File-Format), [GFF](GFF-File-Format) and [NSS files](NSS-File-Format), such as the line numbers from newly added rows in a [2DA file](2DA-File-Format) or the [field](GFF-File-Format#file-structure) path label of a newly added [field](GFF-File-Format#file-structure). This can be used to link together [files](GFF-File-Format) that reference eachother dynamically, regardless of where in the [files](GFF-File-Format) your additions end up. E.g. linking new heads.2da --> [appearance.2da](2DA-appearance) --> portrait.2da lines together to add a new player appearance. Or linking a new [appearance.2da](2DA-appearance) line for an NPC to the "Appearance\_Type" [field](GFF-File-Format#file-structure) in their [UTC](GFF-File-Format#utc-creature) template, just to mention a couple of potential uses.

- Insert [StrRef](TLK-File-Format#string-references-strref) or [2DA](2DA-File-Format)/[GFF](GFF-File-Format) token [values](GFF-File-Format#data-types) into scripts and recompile those scripts automatically with the correct [values](GFF-File-Format#data-types). (E.g. adding new Force Powers with an impact script that needs to know which lines in [spells.2da](2DA-spells) the new powers [ARE](GFF-File-Format#are-area) defined at.)

- Dynamically modify SSF (Soundset) [files](GFF-File-Format) to point to new entries you have added to [dialog.tlk](TLK-File-Format).

- Automatically put other [files](GFF-File-Format) that does not need to be modified into the correct folder within your game folder (e.g. "Override", "Modules", "StreamMusic" etc...), or inside [ERF](ERF-File-Format) or RIM [format](GFF-File-Format) archive [files](GFF-File-Format) existing in any of those folders.

- Insert modified [GFF files](GFF-File-Format) into a RIM or [ERF](ERF-File-Format) [format](GFF-File-Format) file ([ERF](ERF-File-Format), MOD, SAV etc), found in the game folder or any of its sub-folders, or modify existing [files](GFF-File-Format) already found in that destination [file](GFF-File-Format). Recompiled [NCS](NCS-File-Format) script [files](GFF-File-Format) can also be inserted into RIM and [ERF](ERF-File-Format) [format](GFF-File-Format) files (but only overwrite, not modify existing scripts with the same name).

- Make unaltered backup copies of any [files](GFF-File-Format) it modifies or overwrites, making it a little easier to uninstall a mod again.

- Provide the user with different installation alternatives which may be chosen at installation time.

- Display a ReadMe, instruction text or agreement with basic font and text formatting support (using the Rich Text [format](GFF-File-Format)) to the user prior to installation.

It cannot, in no uncertain terms:

- Make standard game scripts that [ARE](GFF-File-Format#are-area) modified by serveral mods compatible. The [structure](GFF-File-Format#file-structure) of a script [file](GFF-File-Format) is too dynamic to lend itself well to automatic merging (at least for someone of my skill level in programming).

- Resolve naming/priority conflicts resulting from placing several variants of [files](GFF-File-Format) with the same name in different sub-folders inside the override folder. It will always assume that all [files](GFF-File-Format) it is supposed to modify [ARE](GFF-File-Format#are-area) located directly in the override folder and not in any subfolders to avoid ambiguous situations.

- Modify [files](GFF-File-Format) held inside [BIF files](BIF-File-Format) in the game, since [KEY](KEY-File-Format)/[BIF files](BIF-File-Format) work pretty much the same as the override folder in most cases, and editing the [KEY](KEY-File-Format)/[BIF](BIF-File-Format) [data](GFF-File-Format#file-structure) can lead to problems. This does of course not prevent you from extracting whatever [files](GFF-File-Format) you need from the [BIF](BIF-File-Format) [data](GFF-File-Format#file-structure) in advance and put them in the TSLPatcher's [data](GFF-File-Format#file-structure) folder.

A few quick "how to" examples:

- Insert new branches into [DLG](GFF-File-Format#dlg-dialogue) [files](GFF-File-Format). (<http://www.lucasforums.com/showpost.php?p=2135535&postcount=177>)
- Install a New Player Appearance mod. (<http://www.lucasforums.com/showpost.php?p=2168405&postcount=201>)

Troubleshooting:
Q: I get a RichEdit line insertion error when trying to install mods. What's wrong?

A: It seems a few people have odd versions of the RichEdit DLL [files](GFF-File-Format) installed in their system that doesn't play nice with the colored text box component TSLPatcher uses. To work around this you could try to replace the RichEd DLL [files](GFF-File-Format) with versions that should work. Extract the two DLL [files](GFF-File-Format) from this archive (<http://www.starwarsknights.com/forumdl/richedlibraries.rar>) and put them in your Windows\\Windows32 folder. Move existing [files](GFF-File-Format) with those names to a safe location first so you can restore them if this causes other problems! Do not overwrite them!

Alternatively, if you don't want to mess with your DLL [files](GFF-File-Format), you could force TSLPatcher to use a plain text box for status messages rather than the colored/formatted one. To do this, use Notepad to open the changes.ini [file](GFF-File-Format) found inside the tslpatchdata folder that came with the mod you wish to install. Under the \[Settings\] section, change the [value](GFF-File-Format#data-types) of the [KEY](KEY-File-Format) PlaintextLog from 0 to 1.

Q: I'm not seeing any Install Mod button, and the text [field](GFF-File-Format#file-structure) in the TSLPatcher window seems to extend behind the window boundraries.

A: This odd problem some people experience seems to be tied to what screen resolution and pixel density is being used in your monitor settings, but I have been unable to replicate it or figure out exactly what's going on. As a workaround you can "click" on the Install button by using it's quick keyboard command. Pressing the \[ALT\] \[S\] keys on your keyboard should start the installation process.

Q: When trying to install a mod it complains that it's not a valid installation location. What's wrong?

A: Make sure you [ARE](GFF-File-Format#are-area) selecting the folder the game is installed in, not the override folder, when the TSLPatcher asks you where to install the mod.

Q: When trying to install a mod it complains that access was denied to the [dialog.tlk](TLK-File-Format) [file](GFF-File-Format).

A: Make sure that your [dialog.tlk](TLK-File-Format) [file](GFF-File-Format) is not write protected. This [file](GFF-File-Format) is found in the same folder as the swkotor.exe binary. To check if it's write protected and undo it, right-click on the [file](GFF-File-Format), pick Properties in the context menu and uncheck the write protected checkbox.

\* \* \*

Thread update history:
EDIT(2007-09-19) Uploaded TSLPatcher v1.2.10b1 and ChangeEdit 1.0.5b1, which fixes a bug/oversight breaking the changes.ini [format](GFF-File-Format) when adding or updating ExoString [fields](GFF-File-Format#file-structure) or ExoLocString substring [fields](GFF-File-Format#file-structure) with text contining newline (LR/CR) characters. In those cases only the text before the first newline would get added earlier. This should now be fixed to handle text with multiple paragraphs properly. See this post (<http://www.lucasforums.com/showpost.php?p=2371689&postcount=247>) for more details.

EDIT(2007-08-13) Uploaded TSLPatcher v1.2.9b which will handle already existing [GFF](GFF-File-Format) [fields](GFF-File-Format#file-structure) a [bit](GFF-File-Format#data-types) better when adding new [fields](GFF-File-Format#file-structure) to a [GFF file](GFF-File-Format). It will now update the [value](GFF-File-Format#data-types) of the existing [field](GFF-File-Format#file-structure) to match what the new [field](GFF-File-Format#file-structure) would have had set, rather than just skip it entirely.

EDIT(2006-12-12) Uploaded TSLPatcher v1.2.8b10 hopefully making the Require [file](GFF-File-Format) checks work reliably all the time, this time. Thanks to Darkkender for pointing this out.

EDIT(2006-12-10) Uploaded TSLPatcher v1.2.8b9 fixing a bug with the patcher not checking for required [file](GFF-File-Format) if using multiple setups and auto-detecting the game install location. Thanks to Darkkender for pointing this out.

EDIT(2006-12-02) Uploaded TSLPatcher v1.2.8b8, which contains fixes for two bugs that sneaked their way into version 1.2.8b6. The bugs would cause installation to abort if the [dialog.tlk](TLK-File-Format) [file](GFF-File-Format) was write protected, or if copying a [2DA](2DA-File-Format) line and using a high() token to assign a new [value](GFF-File-Format#data-types) to a column of the new line. Thanks to DarthCyclopsRLZ for pointing out these bugs.

EDIT(2006-10-03) Uploaded TSLPatcher v1.2.8b6, which contains a whole bunch of bug fixes and some new features. Please see this post for details (<http://www.lucasforums.com/showpost.php?p=2186813&postcount=210>).

EDIT(2006-09-07) Sneaky mini-update to TSLPatcher v1.2.8b4, fixes a bug with backing up [files](GFF-File-Format) before replacing them from the InstallList, which was introduced when the install list sequence was changed to happen before [2DA](2DA-File-Format) edits. Also fixed mistake where word wrap was permanently left off when toggling from the Config Summary back to the info.rtf display on the main TSLPatcher window.

EDIT(2006-08-28) TSLPatcher v1.2.8b3 uploaded, this hopefully fixes the occasional crashes when recompiling scripts with include [files](GFF-File-Format), and works around the weird [GUI](GFF-File-Format#gui-graphical-user-interface) glitch in the main TSLPatcher window that resulted in the buttons and scrollbars ending up outside the window area. Huge thanks to tk102 for taking time to iron out the nwnnsscomp bug.

EDIT(2006-08-09) TSLPatcher v1.2.8b2 uploaded. This version fixes a bug with the RIM handling class which caused the game to have trouble loading RIMs modified by the Patcher, caused by an error in the RIM specifications I had at my disposal. The game should now properly load modified RIM [files](GFF-File-Format) without problems.

EDIT(2006-08-09) TSLPatcher v1.2.8b1 and ChangeEdit v1.0.4b8 uploaded. This version allows the "Install" function to place [files](GFF-File-Format) into [ERF](ERF-File-Format)/RIM archives, allows options for renaming [files](GFF-File-Format) during installation, and adds a "config summary" button to the main TSLPatcher window.

EDIT(2006-08-06) TSLPatcher v1.2.8b0 and ChangeEdit v1.0.4b7 uploaded. This version changes how the [ERF](ERF-File-Format) handling functionality works to make it more useful. See this post (<http://www.lucasforums.com/showpost.php?p=2144898&postcount=181>) for more info.

EDIT(2006-07-25) TSLPatcher v1.2.7b9 and ChangeEdit v1.0.4b6 uploaded. This version has some changed made to the Add/Modify [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) functionality, allowing to to be used to insert new conversation branched into [DLG](GFF-File-Format#dlg-dialogue) [files](GFF-File-Format). Various minor user interface changes have also been made.

EDIT(2006-07-08) TSLPatcher v1.2.7b7 and ChangeEdit v1.0.4b4 uploaded, containing some bugfixes, interface improvements (I hope) and minor changes to make it a little less sensitive to errors.

EDIT(2006-05-28) Uploaded TSLPatcher v1.2.7b5 and ChangeEdit v1.0.4b3, with a Mini-update that allows it to optionally auto-detect the game folder location rather than ask the user where it is, as requested.

EDIT(2006-05-11) Uploaded TSLPatcher v1.2.7b4 and ChangeEdit v1.0.4b2. No new features, just some fixes to bugs I discovered, and slight change to how the script compiler is called to allow it to work with the custom version of nwnnsscomp that tk102 has been kind enough to provide. This custom version is also included in the download now.

EDIT(2006-04-29) Uploaded TSLPatcher v1.2.7b1 and ChangeEdit v1.0.4b1. Too much more information can be found in this post (<http://64.20.36.211/showpost.php?p=2076883&postcount=166>).

EDIT(2006-03-25) Updated ChangeEdit to v1.0.3a with [GFF](GFF-File-Format) Compare function, [2DA](2DA-File-Format) Modifier copy button and a whole bunch of interface improvements. See this post (<http://64.20.36.211/showpost.php?p=2055110&postcount=163>).

EDIT(2006-03-19) Updated TSLPatcher to v1.2.6a (wip v2), which fixes a bug that would prevent the script compilation function to work properly on Windows 98 and Windows 2000 computers.

EDIT(2006-03-09) Uploaded new test version, TSLPatcher v1.2.6a (WIP v1) with added support for modifying [SSF](SSF-File-Format) Soundset [files](GFF-File-Format) with dynamic StrRefs for added [TLK](TLK-File-Format) entries. See this post (<http://64.20.36.211/showpost.php?p=2041981&postcount=159>) for a little more detail.

EDIT(2006-02-03) I've uploaded a new test version, TSLPatcher v.1.2.5a, which has some limited ERF (e.g. module [file](GFF-File-Format)) packing functionality added. See this post (<http://64.20.36.211/showpost.php?p=2010175&postcount=150>) for more details.

EDIT(2006-01-16): I've uploaded a test version of TSLPatcher v1.2 and ChangeEdit v1.0 which has some new features added. See this post (<http://64.20.36.211/showpost.php?p=1988487&postcount=132>) for details.

**[T7nowhere](https://lucasforumsarchive.com/user/105329 "T7nowhere's profile")** - 05-25-2005, 7:46 AM - **#2**

Great work man.

Thanks

**[General Kenobi](https://lucasforumsarchive.com/user/120665 "General Kenobi's profile")** - 05-25-2005, 11:43 AM - **#3**

Excellent work my friend :thumbsup: My lil' achin' [2DA](2DA-File-Format) brain thanks you :D

5/5 Elephant Rating

:elephant: :elephant: :elephant: :elephant: :elephant:

I have been having issues with [2DA](2DA-File-Format) editing and this will be a killer tool to use to merge existing ones.

Again thanks man :D

DM

**[Darkkender](https://lucasforumsarchive.com/user/112932 "Darkkender's profile")** - 05-25-2005, 12:32 PM - **#4**

Good to see this in final release now.

**[Jeff](https://lucasforumsarchive.com/user/119803 "Jeff's profile")** - 05-25-2005, 6:41 PM - **#5**

Great job stoffe. This is great :)

**[Jackel](https://lucasforumsarchive.com/user/88180 "Jackel's profile")** - 05-25-2005, 6:43 PM - **#6**

Nice work stoffe! I will be experimenting with this in the next few days for sure.

**[Keiko](https://lucasforumsarchive.com/user/119830 "Keiko's profile")** - 05-25-2005, 6:49 PM - **#7**

Nice Job!:)

**[Mav](https://lucasforumsarchive.com/user/109045 "Mav's profile")** - 05-25-2005, 10:10 PM - **#8**

This sounds like an exceptional tool, I'll be looking into this more in depth in the next few days.

**[ChAiNz.2da](https://lucasforumsarchive.com/user/116647 "ChAiNz.2da's profile")** - 05-26-2005, 10:54 AM - **#9**

Great stuff man!

I'm persnally glad to see the [GUI](GFF-File-Format#gui-graphical-user-interface) was in the public release :D

When I first started testing, It took me a few read throughs of the readme to get going... after that.. (to quote Atton) "Pure Pazaak" ;)

:thumbsup:

**[stoffe](https://lucasforumsarchive.com/user/121047 "stoffe's profile")** - 06-03-2005, 2:22 PM - **#10**

I have uploaded a new version of the Patcher and its support applications. If anyone is interested you can download it on this page. (<http://www.starwarsknights.com/tools.php>)

As before, comments, suggestions and bug reports [ARE](GFF-File-Format#are-area) welcomed.

This is what has changed since the first release, snipped from the Readme:

TSLPatcher v1.1.1b
------------------------

- Added a new Setting that when set will make the Patcher run in Installer mode instead. When doing this, the Patcher will not ask for each individual [file](GFF-File-Format). It will only ask the user for the folder where the game is installed, and then automatically use the [dialog.tlk](TLK-File-Format) [file](GFF-File-Format) found in that folder, and the override folder located there. If no Override folder exists within the selected folder, one will be created. The patcher will then check the Override folder for the presence of any of the files (except [dialog.tlk](TLK-File-Format) of course) it should modify. If present, it will modify those existing [files](GFF-File-Format). If the [files](GFF-File-Format) [ARE](GFF-File-Format#are-area) not present, the Patcher will look in the "tslpatchdata" folder for the [file](GFF-File-Format), which will then be copied to Override and modified there. Thus, when using the Patcher in Installer mode, all [data](GFF-File-Format#file-structure) [files](GFF-File-Format) that make up your mod should be put in the "tslpatchdata" folder (except [dialog.tlk](TLK-File-Format)). In the case of [2DA files](2DA-File-Format), don't put the modified version here, put an unaltered copy of the [2DA files](2DA-File-Format) in "tslpatchdata". They will only be used if the user doesn't already have a custom version of that [file](GFF-File-Format) in their Override folder.

- Added a bare bones [file](GFF-File-Format) "installer" feature to allow the Patcher to also install [files](GFF-File-Format) it shouldn't modify. All [files](GFF-File-Format) must be located within the "tslpatchdata" folder, and will be copied to the specified folder within the main Game folder the user has selected (override in most cases). This will only work when the patcher runs in Installer mode. Intended to allow the patcher to fully install a mod into the game, not just the [files](GFF-File-Format) that it should modify. Useful for things like [textures](TPC-File-Format), icons, unmodified scripts etc.

- Added support for the [orientation](MDL-MDX-File-Format#node-header) and [position](MDL-MDX-File-Format#node-header) [type](GFF-File-Format#data-types) of fields (that I missed earlier) when modifying [GFF](GFF-File-Format) [fields](GFF-File-Format#file-structure). If you wish to use it for whatever reason, [orientation](MDL-MDX-File-Format#node-header) is set as four decimal [values](GFF-File-Format#data-types) separated by a | character. [position](MDL-MDX-File-Format#node-header) works the same, but is three numbers instead of four. For example:

[field](GFF-File-Format#file-structure): CameraList\0\[orientation](MDL-MDX-File-Format#node-header)
[value](GFF-File-Format#data-types): 12.4|6.5121|1.25|-9.6

- Added a primitive way for the Patcher to modify things like [NCS](NCS-File-Format) scripts with correct [2DA](2DA-File-Format) [index](2DA-File-Format#row-labels) [values](GFF-File-Format#data-types) and StrRefs. It is currently VERY primitive, and WILL mess up your [files](GFF-File-Format) if you don't know what you [ARE](GFF-File-Format#are-area) doing when you configure it. As such it is not added to the ChangeEdit application, and I won't describe how it works here. If you really need to use it, ask me and I'll describe how it works.

TalkEd v0.9.9b
------------------

- Added new option in the Search dialog to search for each word individually. Checking this box and typing "vogga dance" as criteria would match the [string](GFF-File-Format#cexostring) "Do you wish to dance for vogga?" for example.

- Fixed some annoying behavior in the list when adding new entries. The list should now display all new entries that have been added since the current [file](GFF-File-Format) was loaded (or created in case it is a new [file](GFF-File-Format)) when a new entry has been added.
- Added support for associating TalkEd with [TLK files](TLK-File-Format) in the Windows Explorer. If a [TLK files](TLK-File-Format) is drag-n-dropped on the TalkEd icon, that [file](GFF-File-Format) will be opened. If TalkEd is associated with [TLK files](TLK-File-Format), doubleclicking a [TLK file](TLK-File-Format) will open it in TalkEd.

ChangeEdit v0.9.3b
-------------------------

- Fixed annoying list behavior, when adding a new entry to a list, the new line will be selected.

- Added CTRL-SHIFT+Arrowkey keyboard shortcuts to press the arrow buttons that store/retrieve [data](GFF-File-Format#file-structure) in lists.
- Two new entries in the Settings section. You may now set if the patcher should do backups of existing [files](GFF-File-Format) before modifying them, and you may set which run mode (Patcher or Installer) it should run in.
- Added new section for specifying [files](GFF-File-Format) that should be installed by the patcher when running in Installer mode.
- A whole bunch of minor bug fixes.

(Check the Force Powers mod I recently uploaded to PCGameMods if you wish to see a working example of this version of the Patcher in action.)

**[Darth333](https://lucasforumsarchive.com/user/106715 "Darth333's profile")** - 06-03-2005, 2:49 PM - **#11**

Good work as always stoffe :) It's getting better and better!

As discussed, I uploaded the [file](GFF-File-Format) at swk.com: (<http://www.starwarsknights.com/tools.php>) and added a link to this thread so it can be found easily. If there is anything you want to be changed, just let me know.

---

_Note: The complete thread archive continues with 260+ posts across all 6 pages. This [file](GFF-File-Format) has been created with the extracted content from all pages. For the full detailed archive with all posts from pages 2-6, please refer to the complete extraction which contains extensive discussions, tutorials, bug reports, feature requests, and Q&A sessions spanning from May 2005 to November 2007._
