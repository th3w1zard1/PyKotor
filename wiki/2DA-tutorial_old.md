# tutorial_old.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines old tutorial message configurations (legacy). The engine uses this [file](GFF-File-Format) to determine tutorial messages (replaced by `tutorial.2da` in newer versions).

**Row [index](2DA-File-Format#row-labels)**: Tutorial Message ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Tutorial message label |
| `message0` through `message2` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#gff-data-types) references for tutorial messages |
| Additional columns | Various | Tutorial message properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:147`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L147) - [StrRef](TLK-File-Format#string-references-strref) column definitions for tutorial_old.2da

---
