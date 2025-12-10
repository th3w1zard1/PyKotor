# appearancesndset.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines sound appearance [types](GFF-File-Format#gff-data-types) for creature appearances. The engine uses this [file](GFF-File-Format) to determine which sound appearance [type](GFF-File-Format#gff-data-types) to use based on the creature's appearance.

**Row [index](2DA-File-Format#row-labels)**: Sound Appearance [type](GFF-File-Format#gff-data-types) ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Sound appearance [type](GFF-File-Format#gff-data-types) label |
| Additional columns | Various | Sound appearance [type](GFF-File-Format#gff-data-types) properties |

**References**:

- [`vendor/Kotor.NET/Kotor.NET/Tables/Appearance.cs:58-60`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Tables/Appearance.cs#L58-L60) - Comment referencing appearancesndset.2da for SoundAppTypeID

---
