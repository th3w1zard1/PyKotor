# Global Variables

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** TSL-Only Functions

<a id="decrementglobalnumber"></a>

## `DecrementGlobalNumber(sIdentifier, nAmount)` - Routine 800

- `800. DecrementGlobalNumber`
- DJS-OEI 2/3/2004
- Decreases the [value](GFF-File-Format#data-types) of the given global number by the given amount.
- This function only works with Number [type](GFF-File-Format#data-types) globals, not booleans. It
- will fail with a warning if the final amount is less than the minimum
- of -128.

- `sIdentifier`: [string](GFF-File-Format#cexostring)
- `nAmount`: int

<a id="incrementglobalnumber"></a>

## `IncrementGlobalNumber(sIdentifier, nAmount)` - Routine 799

- `799. IncrementGlobalNumber`
- DJS-OEI 2/3/2004
- Increases the [value](GFF-File-Format#data-types) of the given global number by the given amount.
- This function only works with Number [type](GFF-File-Format#data-types) globals, not booleans. It
- will fail with a warning if the final amount is greater than the max
- of 127.

- `sIdentifier`: [string](GFF-File-Format#cexostring)
- `nAmount`: int
