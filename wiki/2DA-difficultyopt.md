# difficultyopt.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines difficulty options and their properties. The engine uses this file to determine difficulty settings, modifiers, and descriptions.

**Row index**: Difficulty Option ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Difficulty option label |
| `desc` | string | Difficulty description (e.g., "Default") |
| Additional columns | Various | Difficulty modifiers and properties |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:66-74`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L66-L74) - Difficulty options initialization from [2DA](2DA-File-Format)

---
