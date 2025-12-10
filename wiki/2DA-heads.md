# heads.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines head [models](MDL-MDX-File-Format) and [textures](TPC-File-Format) for player characters and NPCs. The engine uses this [file](GFF-File-Format) when loading character heads, determining which 3D [model](MDL-MDX-File-Format) and [textures](TPC-File-Format) to apply.

**Row [index](2DA-File-Format#row-labels)**: Head ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `head` | ResRef (optional) | Head [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `headtexe` | ResRef (optional) | Head [texture](TPC-File-Format) E [ResRef](GFF-File-Format#gff-data-types) |
| `headtexg` | ResRef (optional) | Head [texture](TPC-File-Format) G [ResRef](GFF-File-Format#gff-data-types) |
| `headtexve` | ResRef (optional) | Head [texture](TPC-File-Format) VE [ResRef](GFF-File-Format#gff-data-types) |
| `headtexvg` | ResRef (optional) | Head [texture](TPC-File-Format) VG [ResRef](GFF-File-Format#gff-data-types) |
| `headtexvve` | ResRef (optional) | Head [texture](TPC-File-Format) VVE [ResRef](GFF-File-Format#gff-data-types) |
| `headtexvvve` | ResRef (optional) | Head [texture](TPC-File-Format) VVVE [ResRef](GFF-File-Format#gff-data-types) |
| `alttexture` | ResRef (optional) | Alternative [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types) |

**Column Details**:

The complete column [structure](GFF-File-Format#file-structure-overview) is defined in reone's heads parser:

- `head`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types)
- `alttexture`: Optional [ResRef](GFF-File-Format#gff-data-types) - alternative [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types)
- `headtexe`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [texture](TPC-File-Format) for evil alignment
- `headtexg`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [texture](TPC-File-Format) for good alignment
- `headtexve`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [texture](TPC-File-Format) for very evil alignment
- `headtexvg`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [texture](TPC-File-Format) for very good alignment
- `headtexvve`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [texture](TPC-File-Format) for very very evil alignment
- `headtexvvve`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [texture](TPC-File-Format) for very very very evil alignment

**References**:

- [`vendor/reone/src/libs/resource/parser/2da/heads.cpp:29-39`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/heads.cpp#L29-L39) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/creature.cpp:1223-1228`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1223-L1228) - Head loading from [2DA](2DA-File-Format)

---
