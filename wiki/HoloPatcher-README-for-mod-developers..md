_This page explains how to create a mod with HoloPatcher. If you [ARE](GFF-File-Format#are-area) an end user you may be looking for [How to Use HoloPatcher](https://github.com/OldRepublicDevs/PyKotor/wiki/Installing-Mods-with-HoloPatcher)_

## Creating a HoloPatcher mod

HoloPatcher is a rewrite of TSLPatcher written in Python, utilizing the PyKotor library. Everything is backwards compatible with TSLPatcher. For this reason I suggest you first read [TSLPatcher's readme, really.](https://github.com/OldRepublicDevs/PyKotor/wiki/TSLPatcher's-Official-Readme)

**Implementation:** [`Libraries/PyKotor/src/pykotor/tslpatcher/`](https://github.com/OldRepublicDevs/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/tslpatcher/)

**Vendor Mod Installers:**

- [`vendor/TSLPatcher/`](https://github.com/th3w1zard1/TSLPatcher) - Original Perl TSLPatcher by stoffe (reference implementation)
- [`vendor/Kotor-Patch-Manager/`](https://github.com/th3w1zard1/Kotor-Patch-Manager) - Alternative mod manager with different patching approach
- [`vendor/KotORModSync/`](https://github.com/th3w1zard1/KotORModSync) - Mod synchronization and installation tool

**Related PyKotor Tools:**

- [`Tools/HolocronToolset/`](https://github.com/OldRepublicDevs/PyKotor/tree/master/Tools/HolocronToolset) - Integrated HoloPatcher [GUI](GFF-File-Format#gui-graphical-user-interface)
- [`Libraries/PyKotor/src/pykotor/tslpatcher/mods/`](https://github.com/OldRepublicDevs/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/tslpatcher/mods) - Individual patching modules

**See Also:**

- [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme) - Original documentation
- [TSLPatcher InstallList Syntax](TSLPatcher-InstallList-Syntax) - file installation
- [TSLPatcher 2DAList Syntax](TSLPatcher-2DAList-Syntax) - [2DA](2DA-File-Format) patching
- [TSLPatcher GFFList Syntax](TSLPatcher-GFFList-Syntax) - [GFF](GFF-File-Format) patching
- [Mod Creation Best Practices](Mod-Creation-Best-Practices) - General modding guidelines

## HoloPatcher changes & New Features

### [TLK](TLK-File-Format) replacements

- This is not recommended under most scenarios. You usually want to append a new entry and update your DLGs to point to it using [StrRef](TLK-File-Format#string-references-strref) in the ini. However for projects like the k1cp and mods that fix grammatical/spelling mistakes, this may be useful.

The basic syntax is:

```ini
[TLKList]
ReplaceFile0=tlk_modifications_file.tlk

[tlk_modifications_file.tlk]
StrRef0=2
```

This will replace StrRef0 in [dialog.tlk](TLK-File-Format) with StrRef2 from `tlk_modifications_file.tlk`.

[See our tests](https://github.com/OldRepublicDevs/PyKotor/blob/92f5fb81a7b9642085c67b7b48ddd50f2df4378d/tests/test_tslpatcher/test_reader.py#L463) for more examples.
Don't use the 'ignore' syntax or the 'range' syntax, these won't be documented or supported until further notice.

### HACKList (Editing [NCS](NCS-File-Format) directly)

This is a TSLPatcher feature that was [not documented in the TSLPatcher readme.](https://github.com/OldRepublicDevs/PyKotor/wiki/TSLPatcher's-Official-Readme). We can only guess why this is. The only known uses we know about [ARE](GFF-File-Format#are-area) [Stoffe's HLFP mod](https://deadlystream.com/files/file/832-high-level-force-powers/) and some starwarsknights/lucasforums archives on waybackmachine pointing to files that [ARE](GFF-File-Format#are-area) unavailable.

Due to this feature being highly undocumented and only one known usage, our implementation might not match exactly. If you happen to find an old TSLPatcher mod that produces different HACKList results than HoloPatcher, [please report them here](https://github.com/OldRepublicDevs/PyKotor/issues/24)

In continuation, HoloPatcher's [HACKList] will use the following syntax:

```ini
[HACKList]
File0=script_to_modify.NCS

[script_to_modify.ncs]
20=StrRef5
40=2DAMEMORY10
60=65535
```

This will:

- Modify offset dec 20 (hex 0x14) of `script_to_modify.ncs` and overwrite that offset with the value of StrRef5.
- Modify offset dec 40 (hex 0x28) of `script_to_modify.ncs` and overwrite that offset with the value of 2DAMEMORY10.
- Modify offset dec 60 (hex 0x3C) of `script_to_modify.ncs` and overwrite that offset with the value of dec 65535 (hex 0xFFFF) i.e. the maximum possible value.
In summary, HACKList writes unsigned WORDs (sized at two bytes) to offsets in the [NCS](NCS-File-Format) specified by the ini.

### For more information on HoloPatcher's implementation, please see the following links

#### [pykotor.tslpatcher.reader](https://github.com/OldRepublicDevs/PyKotor/blob/92f5fb81a7b9642085c67b7b48ddd50f2df4378d/Libraries/PyKotor/src/pykotor/tslpatcher/reader.py#L697)

#### [pykotor.tslpatcher.mods.ncs](https://github.com/OldRepublicDevs/PyKotor/blob/92f5fb81a7b9642085c67b7b48ddd50f2df4378d/Libraries/PyKotor/src/pykotor/tslpatcher/mods/ncs.py)
