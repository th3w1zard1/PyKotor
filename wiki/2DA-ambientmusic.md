# ambientmusic.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines ambient music tracks for areas. The engine uses this file to determine which music to play in different areas based on [area properties](GFF-File-Format#are-area).

**Row index**: Music ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Music label |
| `music` | [ResRef](GFF-File-Format#gff-data-types) | Music file [ResRef](GFF-File-Format#gff-data-types) |
| `resource` | [ResRef](GFF-File-Format#gff-data-types) | Music resource [ResRef](GFF-File-Format#gff-data-types) |
| `stinger1`, `stinger2`, `stinger3` | ResRef (optional) | Stinger music ResRefs |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:206`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L206) - Music [ResRef](GFF-File-Format#gff-data-types) column definitions for ambientmusic.2da (K1: resource, stinger1, stinger2, stinger3)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:398`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L398) - Music [ResRef](GFF-File-Format#gff-data-types) column definitions for ambientmusic.2da (K2: resource, stinger1, stinger2, stinger3)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:545-548`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L545-L548) - [GFF](GFF-File-Format) field mapping: "MusicDay", "MusicNight", "MusicBattle", "MusicDelay" -> ambientmusic.2da

---
