# loadscreenhints.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines loading screen hints displayed during area transitions. The engine uses this [file](GFF-File-Format) to show helpful tips and hints to players while loading.

**Row [index](2DA-File-Format#row-labels)**: Loading Screen Hint ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Hint label |
| `strref` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#gff-data-types) reference for hint text |

**References**:

- [`vendor/xoreos/src/engines/kotor/gui/loadscreen/loadscreen.cpp:45`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotor/gui/loadscreen/loadscreen.cpp#L45) - Loading screen hints TODO comment (KotOR-specific)

---
