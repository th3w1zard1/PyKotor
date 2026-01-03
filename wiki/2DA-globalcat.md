# globalcat.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines global variables and their types for the game engine. The engine uses this file to initialize global variables at game start, determining which variables [ARE](GFF-File-Format#are-area) integers, floats, or strings.

**Row index**: Global Variable Index (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Global variable label |
| `name` | string | Global variable name |
| `type` | string | Variable type ("Number", "Boolean", "string", etc.) |

**References**:

- [`vendor/NorthernLights/Assets/Scripts/Systems/StateSystem.cs:282-294`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/Systems/StateSystem.cs#L282-L294) - Global variable initialization from [2DA](2DA-File-Format)

---
