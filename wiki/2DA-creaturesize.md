# creaturesize.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines creature [size](GFF-File-Format#file-structure) categories and their properties. The engine uses this [file](GFF-File-Format) to determine [size](GFF-File-Format#file-structure)-based combat modifiers, reach, and other [size](GFF-File-Format#file-structure)-related calculations.

**Row [index](2DA-File-Format#row-labels)**: [size](GFF-File-Format#file-structure) Category ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | [size](GFF-File-Format#file-structure) category label |
| Additional columns | Various | [size](GFF-File-Format#file-structure) category properties and modifiers |

**References**:

- [`vendor/Kotor.NET/Kotor.NET/Tables/Appearance.cs:42-44`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Tables/Appearance.cs#L42-L44) - Comment referencing creaturesize.2da for SizeCategoryID

---
