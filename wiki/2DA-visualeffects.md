# [visualeffects.2da](2DA-visualeffects)

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines visual effects (particle effects, impact effects, environmental effects) with their durations, [models](MDL-MDX-File-Format), and properties. The engine uses this [file](GFF-File-Format) when playing visual effects for spells, combat, and environmental events.

**Row [index](2DA-File-Format#row-labels)**: Visual effect ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Visual effect label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#cexostring) reference for effect name |
| `model` | ResRef (optional) | Effect [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#resref) |
| `impactmodel` | ResRef (optional) | Impact [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#resref) |
| `impactorient` | Integer | Impact [orientation](MDL-MDX-File-Format#node-header) |
| `impacttype` | Integer | Impact [type](GFF-File-Format#data-types) identifier |
| `duration` | Float | Effect duration in seconds |
| `durationvariance` | Float | Duration variance |
| `loop` | Boolean | Whether effect loops |
| `render` | Boolean | Whether effect is rendered |
| `renderhint` | Integer | Render hint [flags](GFF-File-Format#data-types) |
| `sound` | ResRef (optional) | Sound effect [ResRef](GFF-File-Format#resref) |
| `sounddelay` | Float | Sound delay in seconds |
| `soundvariance` | Float | Sound variance |
| `soundloop` | Boolean | Whether sound loops |
| `soundvolume` | Float | Sound volume (0.0-1.0) |
| `light` | Boolean | Whether effect emits light |
| `lightcolor` | [string](GFF-File-Format#cexostring) | Light [color](GFF-File-Format#color) RGB [values](GFF-File-Format#data-types) |
| `lightintensity` | Float | Light intensity |
| `lightradius` | Float | Light radius |
| `lightpulse` | Boolean | Whether light pulses |
| `lightpulselength` | Float | Light pulse length |
| `lightfade` | Boolean | Whether light fades |
| `lightfadelength` | Float | Light fade length |
| `lightfadestart` | Float | Light fade start time |
| `lightfadeend` | Float | Light fade end time |
| `lightshadow` | Boolean | Whether light casts shadows |
| `lightshadowradius` | Float | Light shadow radius |
| `lightshadowintensity` | Float | Light shadow intensity |
| `lightshadowcolor` | [string](GFF-File-Format#cexostring) | Light shadow [color](GFF-File-Format#color) RGB [values](GFF-File-Format#data-types) |
| `lightshadowfade` | Boolean | Whether light shadow fades |
| `lightshadowfadelength` | Float | Light shadow fade length |
| `lightshadowfadestart` | Float | Light shadow fade start time |
| `lightshadowfadeend` | Float | Light shadow fade end time |
| `lightshadowpulse` | Boolean | Whether light shadow pulses |
| `lightshadowpulselength` | Float | Light shadow pulse length |
| `lightshadowpulseintensity` | Float | Light shadow pulse intensity |
| `lightshadowpulsecolor` | [string](GFF-File-Format#cexostring) | Light shadow pulse [color](GFF-File-Format#color) RGB [values](GFF-File-Format#data-types) |
| `lightshadowpulsefade` | Boolean | Whether light shadow pulse fades |
| `lightshadowpulsefadelength` | Float | Light shadow pulse fade length |
| `lightshadowpulsefadestart` | Float | Light shadow pulse fade start time |
| `lightshadowpulsefadeend` | Float | Light shadow pulse fade end time |
| `lightshadowpulsefadeintensity` | Float | Light shadow pulse fade intensity |
| `lightshadowpulsefadecolor` | [string](GFF-File-Format#cexostring) | Light shadow pulse fade [color](GFF-File-Format#color) RGB [values](GFF-File-Format#data-types) |
| `lightshadowpulsefadepulse` | Boolean | Whether light shadow pulse fade pulses |
| `lightshadowpulsefadepulselength` | Float | Light shadow pulse fade pulse length |
| `lightshadowpulsefadepulseintensity` | Float | Light shadow pulse fade pulse intensity |
| `lightshadowpulsefadepulsecolor` | [string](GFF-File-Format#cexostring) | Light shadow pulse fade pulse [color](GFF-File-Format#color) RGB [values](GFF-File-Format#data-types) |
| `lightshadowpulsefadepulsefade` | Boolean | Whether light shadow pulse fade pulse fades |
| `lightshadowpulsefadepulsefadelength` | Float | Light shadow pulse fade pulse fade length |
| `lightshadowpulsefadepulsefadestart` | Float | Light shadow pulse fade pulse fade start time |
| `lightshadowpulsefadepulsefadeend` | Float | Light shadow pulse fade pulse fade end time |
| `lightshadowpulsefadepulsefadeintensity` | Float | Light shadow pulse fade pulse fade intensity |
| `lightshadowpulsefadepulsefadecolor` | [string](GFF-File-Format#cexostring) | Light shadow pulse fade pulse fade [color](GFF-File-Format#color) RGB [values](GFF-File-Format#data-types) |

**Note**: The `visualeffects.2da` [file](GFF-File-Format) may contain many optional columns for advanced lighting and shadow effects.

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:593`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L593) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) mapping: "VisualType" -> [visualeffects.2da](2DA-visualeffects)

---
