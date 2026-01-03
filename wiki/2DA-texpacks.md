# texpacks.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines [texture](TPC-File-Format) pack configurations for graphics settings (KotOR 2 only). The engine uses this file to determine available [texture](TPC-File-Format) pack options in the graphics menu.

**Row index**: [texture](TPC-File-Format) Pack ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | [texture](TPC-File-Format) pack label |
| `strrefname` | [StrRef](TLK-File-Format#string-references-strref) | string reference for [texture](TPC-File-Format) pack name |
| Additional columns | Various | [texture](TPC-File-Format) pack properties and settings |

**References**:

- [`vendor/KotOR.js/src/game/tsl/menu/MenuGraphicsAdvanced.ts:51-122`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/game/tsl/menu/MenuGraphicsAdvanced.ts#L51-L122) - [texture](TPC-File-Format) pack loading from [2DA](2DA-File-Format) for graphics menu (KotOR 2 only)
- [`vendor/KotOR.js/src/game/kotor/menu/MenuGraphicsAdvanced.ts:63-121`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/game/kotor/menu/MenuGraphicsAdvanced.ts#L63-L121) - [texture](TPC-File-Format) pack usage in KotOR 1 graphics menu

---
