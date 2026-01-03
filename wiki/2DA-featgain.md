# featgain.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines feat gain progression by class and level. The engine uses this file to determine which feats [ARE](GFF-File-Format#are-area) available to each class at each level.

**Row index**: Feat Gain Entry ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Feat gain entry label |
| Additional columns | Various | Feat gain progression by class and level |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:101-105`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L101-L105) - Feat gain initialization from [2DA](2DA-File-Format)

---
