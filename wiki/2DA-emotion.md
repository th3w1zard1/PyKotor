# emotion.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines emotion [animations](MDL-MDX-File-Format#animation-header) for dialog conversations (KotOR 2 only). The engine uses this file to determine which emotion [animation](MDL-MDX-File-Format#animation-header) to play during dialog lines.

**Row index**: Emotion ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Emotion label |
| Additional columns | Various | Emotion [animation](MDL-MDX-File-Format#animation-header) properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:491`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L491) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:90`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L90) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py:1267-1319`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py#L1267-L1319) - Emotion loading in dialog editor (KotOR 2 only)

---
