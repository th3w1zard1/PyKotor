# facialanim.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines facial [animation](MDL-MDX-File-Format#animation-header) expressions for dialog conversations (KotOR 2 only). The engine uses this file to determine which facial expression [animation](MDL-MDX-File-Format#animation-header) to play during dialog lines.

**Row index**: Expression ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Expression label |
| Additional columns | Various | Facial [animation](MDL-MDX-File-Format#animation-header) properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:492`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L492) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:91`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L91) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py:1267-1325`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py#L1267-L1325) - Expression loading in dialog editor (KotOR 2 only)

---
