# Search/Replace Strings to Revert Overly Broad Hyperlinks

Use these search/replace patterns in your batch replacement tool to remove inappropriate hyperlinks for common words.

## Most Common (Priority Order)

1. **type** → type
   - Search: `[type](GFF-File-Format#data-types)`
   - Replace: `type`
   - Search: `[type](GFF-File-Format#gff-data-types)`
   - Replace: `type`

2. **value** → value
   - Search: `[value](GFF-File-Format#data-types)`
   - Replace: `value`
   - Search: `[value](GFF-File-Format#gff-data-types)`
   - Replace: `value`

3. **values** → values
   - Search: `[values](GFF-File-Format#data-types)`
   - Replace: `values`
   - Search: `[values](GFF-File-Format#gff-data-types)`
   - Replace: `values`

4. **field** → field
   - Search: `[field](GFF-File-Format#file-structure)`
   - Replace: `field`

5. **fields** → fields
   - Search: `[fields](GFF-File-Format#file-structure)`
   - Replace: `fields`

6. **format** → format
   - Search: `[format](GFF-File-Format)`
   - Replace: `format`

7. **formats** → formats
   - Search: `[formats](GFF-File-Format)`
   - Replace: `formats`

8. **file** → file
   - Search: `[file](GFF-File-Format)`
   - Replace: `file`

9. **files** → files
   - Search: `[files](GFF-File-Format)`
   - Replace: `files`

10. **data** → data
    - Search: `[data](GFF-File-Format#file-structure)`
    - Replace: `data`

11. **structure** → structure
    - Search: `[structure](GFF-File-Format#file-structure)`
    - Replace: `structure`

12. **structures** → structures
    - Search: `[structures](GFF-File-Format#file-structure)`
    - Replace: `structures`

13. **string** → string
    - Search: `[string](GFF-File-Format#cexostring)`
    - Replace: `string`
    - Search: `[string](GFF-File-Format#gff-data-types)`
    - Replace: `string`

14. **strings** → strings
    - Search: `[strings](GFF-File-Format#cexostring)`
    - Replace: `strings`
    - Search: `[strings](GFF-File-Format#gff-data-types)`
    - Replace: `strings`

15. **array** → array
    - Search: `[array](2DA-File-Format)`
    - Replace: `array`

16. **arrays** → arrays
    - Search: `[arrays](2DA-File-Format)`
    - Replace: `arrays`

17. **index** → index
    - Search: `[index](2DA-File-Format#row-labels)`
    - Replace: `index`

18. **indexes** → indexes
    - Search: `[indexes](2DA-File-Format#row-labels)`
    - Replace: `indexes`

19. **indices** → indices
    - Search: `[indices](2DA-File-Format#row-labels)`
    - Replace: `indices`

20. **vector** → vector
    - Search: `[vector](GFF-File-Format#vector)`
    - Replace: `vector`
    - Search: `[vector](GFF-File-Format#gff-data-types)`
    - Replace: `vector`

21. **vectors** → vectors
    - Search: `[vectors](GFF-File-Format#vector)`
    - Replace: `vectors`
    - Search: `[vectors](GFF-File-Format#gff-data-types)`
    - Replace: `vectors`

22. **color** → color
    - Search: `[color](GFF-File-Format#color)`
    - Replace: `color`
    - Search: `[color](GFF-File-Format#gff-data-types)`
    - Replace: `color`

23. **colors** → colors
    - Search: `[colors](GFF-File-Format#color)`
    - Replace: `colors`
    - Search: `[colors](GFF-File-Format#gff-data-types)`
    - Replace: `colors`

## Additional Common Words

24. **count** → count
    - Search: `[count](GFF-File-Format#file-structure)`
    - Replace: `count`

25. **size** → size
    - Search: `[size](GFF-File-Format#file-structure)`
    - Replace: `size`

26. **offset** → offset
    - Search: `[offset](GFF-File-Format#file-structure)`
    - Replace: `offset`

27. **offsets** → offsets
    - Search: `[offsets](GFF-File-Format#file-structure)`
    - Replace: `offsets`

28. **pointer** → pointer
    - Search: `[pointer](GFF-File-Format#file-structure)`
    - Replace: `pointer`

29. **pointers** → pointers
    - Search: `[pointers](GFF-File-Format#file-structure)`
    - Replace: `pointers`

30. **header** → header
    - Search: `[header](GFF-File-Format#file-header)`
    - Replace: `header`

31. **headers** → headers
    - Search: `[headers](GFF-File-Format#file-header)`
    - Replace: `headers`

32. **flag** → flag
    - Search: `[flag](GFF-File-Format#data-types)`
    - Replace: `flag`

33. **flags** → flags
    - Search: `[flags](GFF-File-Format#data-types)`
    - Replace: `flags`

34. **bit** → bit
    - Search: `[bit](GFF-File-Format#data-types)`
    - Replace: `bit`

35. **bits** → bits
    - Search: `[bits](GFF-File-Format#data-types)`
    - Replace: `bits`

36. **mask** → mask
    - Search: `[mask](GFF-File-Format#data-types)`
    - Replace: `mask`

37. **masks** → masks
    - Search: `[masks](GFF-File-Format#data-types)`
    - Replace: `masks`

38. **bitmask** → bitmask
    - Search: `[bitmask](GFF-File-Format#data-types)`
    - Replace: `bitmask`

39. **bitmasks** → bitmasks
    - Search: `[bitmasks](GFF-File-Format#data-types)`
    - Replace: `bitmasks`

40. **matrix** → matrix
    - Search: `[matrix](BWM-File-Format#vertex-data-processing)`
    - Replace: `matrix`

41. **matrices** → matrices
    - Search: `[matrices](BWM-File-Format#vertex-data-processing)`
    - Replace: `matrices`

42. **coordinate** → coordinate
    - Search: `[coordinate](GFF-File-Format#are-area)`
    - Replace: `coordinate`

43. **coordinates** → coordinates
    - Search: `[coordinates](GFF-File-Format#are-area)`
    - Replace: `coordinates`

44. **position** → position
    - Search: `[position](MDL-MDX-File-Format#node-header)`
    - Replace: `position`

45. **positions** → positions
    - Search: `[positions](MDL-MDX-File-Format#node-header)`
    - Replace: `positions`

46. **orientation** → orientation
    - Search: `[orientation](MDL-MDX-File-Format#node-header)`
    - Replace: `orientation`

47. **orientations** → orientations
    - Search: `[orientations](MDL-MDX-File-Format#node-header)`
    - Replace: `orientations`

48. **rotation** → rotation
    - Search: `[rotation](MDL-MDX-File-Format#node-header)`
    - Replace: `rotation`

49. **rotations** → rotations
    - Search: `[rotations](MDL-MDX-File-Format#node-header)`
    - Replace: `rotations`

50. **transformation** → transformation
    - Search: `[transformation](BWM-File-Format#vertex-data-processing)`
    - Replace: `transformation`

51. **transformations** → transformations
    - Search: `[transformations](BWM-File-Format#vertex-data-processing)`
    - Replace: `transformations`

52. **scale** → scale
    - Search: `[scale](MDL-MDX-File-Format#node-header)`
    - Replace: `scale`

53. **types** → types
    - Search: `[types](GFF-File-Format#data-types)`
    - Replace: `types`

## Notes

- Apply these in order (most common first)
- Some terms may appear with different anchor links (e.g., `#data-types` vs `#gff-data-types`), so check both variants
- After reverting, the script has been fixed to prevent these from happening again
- Total affected: ~4144 matches across 212 files

