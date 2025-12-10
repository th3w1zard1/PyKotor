# alienvo.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines alien voice-over configurations (KotOR 2 only). The engine uses this [file](GFF-File-Format) to determine alien voice-over sound effects for various emotional states and situations.

**Row [index](2DA-File-Format#row-labels)**: Alien Voice-Over ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Alien voice-over label |
| `angry_long`, `angry_medium`, `angry_short` | [ResRef](GFF-File-Format#gff-data-types) | Angry voice-over sound ResRefs |
| `comment_generic_long`, `comment_generic_medium`, `comment_generic_short` | [ResRef](GFF-File-Format#gff-data-types) | Generic comment voice-over sound ResRefs |
| `greeting_medium`, `greeting_short` | [ResRef](GFF-File-Format#gff-data-types) | Greeting voice-over sound ResRefs |
| `happy_thankful_long`, `happy_thankful_medium`, `happy_thankful_short` | [ResRef](GFF-File-Format#gff-data-types) | Happy/thankful voice-over sound ResRefs |
| `laughter_normal`, `laughter_mocking_medium`, `laughter_mocking_short`, `laughter_long`, `laughter_short` | [ResRef](GFF-File-Format#gff-data-types) | Laughter voice-over sound ResRefs |
| `pleading_medium`, `pleading_short` | [ResRef](GFF-File-Format#gff-data-types) | Pleading voice-over sound ResRefs |
| `question_long`, `question_medium`, `question_short` | [ResRef](GFF-File-Format#gff-data-types) | Question voice-over sound ResRefs |
| `sad_long`, `sad_medium`, `sad_short` | [ResRef](GFF-File-Format#gff-data-types) | Sad voice-over sound ResRefs |
| `scared_long`, `scared_medium`, `scared_short` | [ResRef](GFF-File-Format#gff-data-types) | Scared voice-over sound ResRefs |
| `seductive_long`, `seductive_medium`, `seductive_short` | [ResRef](GFF-File-Format#gff-data-types) | Seductive voice-over sound ResRefs |
| `silence` | [ResRef](GFF-File-Format#gff-data-types) | Silence voice-over sound [ResRef](GFF-File-Format#gff-data-types) |
| `wounded_medium`, `wounded_small` | [ResRef](GFF-File-Format#gff-data-types) | Wounded voice-over sound ResRefs |
| `screaming_medium`, `screaming_small` | [ResRef](GFF-File-Format#gff-data-types) | Screaming voice-over sound ResRefs |
| Additional columns | Various | Alien voice-over properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:363-375`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L363-L375) - Sound [ResRef](GFF-File-Format#gff-data-types) column definitions for alienvo.2da (KotOR 2 only)

---
