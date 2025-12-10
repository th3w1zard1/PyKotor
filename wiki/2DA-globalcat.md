# globalcat.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines global variables and their [types](GFF-File-Format#gff-data-types) for the game engine. The engine uses this [file](GFF-File-Format) to initialize global variables at game start, determining which variables [ARE](GFF-File-Format#are-area) integers, floats, or [strings](GFF-File-Format#gff-data-types).

**Row [index](2DA-File-Format#row-labels)**: Global Variable Index (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Global variable label |
| `name` | [string](GFF-File-Format#gff-data-types) | Global variable name |
| `type` | [string](GFF-File-Format#gff-data-types) | Variable type ("Number", "Boolean", "[string](GFF-File-Format#gff-data-types)", etc.) |

**References**:

- [`vendor/NorthernLights/Assets/Scripts/Systems/StateSystem.cs:282-294`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/Systems/StateSystem.cs#L282-L294) - Global variable initialization from [2DA](2DA-File-Format)

---
