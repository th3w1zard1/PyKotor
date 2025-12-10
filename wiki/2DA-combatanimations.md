# combatanimations.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines combat-specific [animation](MDL-MDX-File-Format#animation-header) properties and mappings. The engine uses this file to determine which [animations](MDL-MDX-File-Format#animation-header) to play during combat actions.

**Row index**: Combat [animation](MDL-MDX-File-Format#animation-header) ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Combat [animation](MDL-MDX-File-Format#animation-header) label |
| Additional columns | Various | Combat [animation](MDL-MDX-File-Format#animation-header) properties |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:1482`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L1482) - Combat [animation](MDL-MDX-File-Format#animation-header) lookup from [2DA](2DA-File-Format)

---
