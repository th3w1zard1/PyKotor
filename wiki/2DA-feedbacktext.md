# feedbacktext.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines feedback text [strings](GFF-File-Format#gff-data-types) displayed to the player for various game events and actions. The engine uses this [file](GFF-File-Format) to provide contextual feedback messages.

**Row [index](2DA-File-Format#row-labels)**: Feedback Text ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Feedback text label |
| Additional columns | Various | Feedback text [strings](GFF-File-Format#gff-data-types) and properties |

**References**:

- [`vendor/NorthernLights/nwscript.nss:3858`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L3858) - Comment referencing FeedBackText.2da
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:4464-4465`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L4464-L4465) - DisplayFeedBackText function

---
