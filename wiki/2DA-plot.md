# plot.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines journal/quest entries with their experience point rewards and labels. The engine uses this file to manage quest tracking, [journal entries](GFF-File-Format#jrl-journal), and experience point calculations for quest completion.

**Row index**: Plot ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Plot/quest label (used as quest identifier) |
| `xp` | Integer | Experience points awarded for quest completion |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:123-125`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L123-L125) - [UTC](GFF-File-Format#utc-creature) plot field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:375`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L375) - [UTC](GFF-File-Format#utc-creature) plot field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:579-580`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L579-L580) - Plot field parsing from [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:839`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L839) - Plot field writing to [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py:71-73`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py#L71-L73) - [UTI](GFF-File-Format#uti-item) plot field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py:129`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py#L129) - [UTI](GFF-File-Format#uti-item) plot field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py:256-258`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py#L256-L258) - Plot field parsing from [UTI](GFF-File-Format#uti-item) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py:339`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py#L339) - Plot field writing to [UTI](GFF-File-Format#uti-item) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/dlg/io/gff.py:89-92`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/dlg/io/gff.py#L89-L92) - Dialog [node](MDL-MDX-File-Format#node-structures) PlotIndex and PlotXPPercentage field parsing

**Vendor Implementations:**

- [`vendor/KotOR.js/src/managers/JournalManager.ts:58-64`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/JournalManager.ts#L58-L64) - Plot/quest experience lookup from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/managers/JournalManager.ts:101-104`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/JournalManager.ts#L101-L104) - Plot existence check from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:7845-7848`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L7845-L7848) - Plot table access for quest experience

---
