# tilecolor.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines tile [colors](GFF-File-Format#color) for [walkmesh](BWM-File-Format) rendering. The engine uses this [file](GFF-File-Format) to determine [color](GFF-File-Format#color) [values](GFF-File-Format#data-types) for different [walkmesh](BWM-File-Format) tiles.

**Row [index](2DA-File-Format#row-labels)**: Tile [color](GFF-File-Format#color) ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Tile [color](GFF-File-Format#color) label |
| Additional columns | Various | [color](GFF-File-Format#color) [values](GFF-File-Format#data-types) and properties |

**References**:

- [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:618-626`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L618-L626) - Tile [color](GFF-File-Format#color) loading from [2DA](2DA-File-Format)

---
