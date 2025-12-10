# difficultyopt.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines difficulty options and their properties. The engine uses this [file](GFF-File-Format) to determine difficulty settings, modifiers, and descriptions.

**Row [index](2DA-File-Format#row-labels)**: Difficulty Option ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Difficulty option label |
| `desc` | [string](GFF-File-Format#cexostring) | Difficulty description (e.g., "Default") |
| Additional columns | Various | Difficulty modifiers and properties |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:66-74`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L66-L74) - Difficulty options initialization from [2DA](2DA-File-Format)

---
