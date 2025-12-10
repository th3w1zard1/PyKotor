# camerastyle.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines camera styles for areas, including distance, pitch, view angle, and height settings. The engine uses this [file](GFF-File-Format) to configure camera behavior in different areas.

**Row [index](2DA-File-Format#row-labels)**: Camera Style ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Camera style label |
| `name` | [string](GFF-File-Format#cexostring) | Camera style name |
| `distance` | Float | Camera distance from target |
| `pitch` | Float | Camera pitch angle |
| `viewangle` | Float | Camera view angle |
| `height` | Float | Camera height [offset](GFF-File-Format#file-structure) |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:497`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L497) - TwoDARegistry.CAMERAS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:550`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L550) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) mapping: "CameraStyle" -> camerastyle.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:37`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L37) - [ARE](GFF-File-Format#are-area) camera_style [field](GFF-File-Format#file-structure) documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:123`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L123) - Camera style [index](2DA-File-Format#row-labels) comment
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:442`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L442) - CameraStyle [field](GFF-File-Format#file-structure) parsing from [ARE](GFF-File-Format#are-area) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:579`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L579) - CameraStyle [field](GFF-File-Format#file-structure) writing to [ARE](GFF-File-Format#are-area) [GFF](GFF-File-Format)

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:96`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L96) - HTInstallation.TwoDA_CAMERAS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/are.py:102`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/are.py#L102) - camerastyle.2da loading in [ARE](GFF-File-Format#are-area) editor

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/camerastyles.cpp:29-42`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/camerastyles.cpp#L29-L42) - Camera style loading from [2DA](2DA-File-Format)
- [`vendor/reone/src/libs/game/object/area.cpp:140-148`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/area.cpp#L140-L148) - Camera style usage in areas

---
