# visualeffects.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines visual effects (particle effects, impact effects, environmental effects) with their durations, [models](MDL-MDX-File-Format), and properties. The engine uses this file when playing visual effects for spells, combat, and environmental events.

**Row index**: Visual effect ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Visual effect label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for effect name |
| `model` | ResRef (optional) | Effect [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `impactmodel` | ResRef (optional) | Impact [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `impactorient` | Integer | Impact orientation |
| `impacttype` | Integer | Impact type identifier |
| `duration` | Float | Effect duration in seconds |
| `durationvariance` | Float | Duration variance |
| `loop` | Boolean | Whether effect loops |
| `render` | Boolean | Whether effect is rendered |
| `renderhint` | Integer | Render hint [flags](GFF-File-Format#gff-data-types) |
| `sound` | ResRef (optional) | Sound effect [ResRef](GFF-File-Format#gff-data-types) |
| `sounddelay` | Float | Sound delay in seconds |
| `soundvariance` | Float | Sound variance |
| `soundloop` | Boolean | Whether sound loops |
| `soundvolume` | Float | Sound volume (0.0-1.0) |
| `light` | Boolean | Whether effect emits light |
| `lightcolor` | string | Light color RGB values |
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
| `lightshadowcolor` | string | Light shadow color RGB values |
| `lightshadowfade` | Boolean | Whether light shadow fades |
| `lightshadowfadelength` | Float | Light shadow fade length |
| `lightshadowfadestart` | Float | Light shadow fade start time |
| `lightshadowfadeend` | Float | Light shadow fade end time |
| `lightshadowpulse` | Boolean | Whether light shadow pulses |
| `lightshadowpulselength` | Float | Light shadow pulse length |
| `lightshadowpulseintensity` | Float | Light shadow pulse intensity |
| `lightshadowpulsecolor` | string | Light shadow pulse color RGB values |
| `lightshadowpulsefade` | Boolean | Whether light shadow pulse fades |
| `lightshadowpulsefadelength` | Float | Light shadow pulse fade length |
| `lightshadowpulsefadestart` | Float | Light shadow pulse fade start time |
| `lightshadowpulsefadeend` | Float | Light shadow pulse fade end time |
| `lightshadowpulsefadeintensity` | Float | Light shadow pulse fade intensity |
| `lightshadowpulsefadecolor` | string | Light shadow pulse fade color RGB values |
| `lightshadowpulsefadepulse` | Boolean | Whether light shadow pulse fade pulses |
| `lightshadowpulsefadepulselength` | Float | Light shadow pulse fade pulse length |
| `lightshadowpulsefadepulseintensity` | Float | Light shadow pulse fade pulse intensity |
| `lightshadowpulsefadepulsecolor` | string | Light shadow pulse fade pulse color RGB values |
| `lightshadowpulsefadepulsefade` | Boolean | Whether light shadow pulse fade pulse fades |
| `lightshadowpulsefadepulsefadelength` | Float | Light shadow pulse fade pulse fade length |
| `lightshadowpulsefadepulsefadestart` | Float | Light shadow pulse fade pulse fade start time |
| `lightshadowpulsefadepulsefadeend` | Float | Light shadow pulse fade pulse fade end time |
| `lightshadowpulsefadepulsefadeintensity` | Float | Light shadow pulse fade pulse fade intensity |
| `lightshadowpulsefadepulsefadecolor` | string | Light shadow pulse fade pulse fade color RGB values |

**Note**: The `visualeffects.2da` file may contain many optional columns for advanced lighting and shadow effects.

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:593`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L593) - [GFF](GFF-File-Format) field mapping: "VisualType" -> visualeffects.2da

---
