from __future__ import annotations

import itertools

from typing import TYPE_CHECKING

from pykotor.resource.formats.ltr.ltr_data import LTR
from pykotor.resource.type import ResourceReader, ResourceWriter

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class LTRBinaryReader(ResourceReader):
    """Reads LTR (Letter) files.
    
    LTR files contain Markov chain probability data for generating random names
    during character creation. They use a 3rd-order Markov chain model with
    single-letter, double-letter (bigram), and triple-letter (trigram) probability tables.
    
    References:
    ----------
        Based on swkotor.exe LTR structure:
        - LTR files loaded as resources through CExoResMan
        - "LTR V1.0" format identifier - LTR file version string
        - ".ltr" extension string - LTR file extension
        - "ltr" resource type string @ 0x0074dd04 - LTR resource type identifier
        - LTR format: "LTR " type, "V1.0" version, letter count (28), probability arrays
        - Single-letter probabilities: start[28], middle[28], end[28] arrays
        - Double-letter probabilities: 28 blocks of start[28], middle[28], end[28] arrays
        - Triple-letter probabilities: 28x28 blocks of start[28], middle[28], end[28] arrays
        - Used for random name generation during character creation
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LTRObject.ts:51-121
        https://github.com/th3w1zard1/KotOR_IO/tree/master/KotOR_IO/File


    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        
        # LTR instance to be populated during loading
        self._ltr: LTR | None = None

    def load(
        self,
        auto_close: bool = True,
    ) -> LTR:
        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LTRObject.ts:51-57
        
        # Initialize LTR instance
        self._ltr = LTR()

        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LTRObject.ts:55-56
        
        # Read header: file type ("LTR ") and version ("V1.0")
        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "LTR ":
            msg = "The file type that was loaded is invalid."
            raise TypeError(msg)

        if file_version != "V1.0":
            msg = "The LTR version that was loaded is not supported."
            raise TypeError(msg)

        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LTRObject.ts:57
        
        # Read letter count (must be 28 for KotOR, 26 or 28 for NWN)
        letter_count = self._reader.read_uint8()
        if letter_count != 28:
            msg = "LTR files that do not handle exactly 28 characters are not supported."
            raise TypeError(msg)

        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LTRObject.ts:62-75
        
        # Read single-letter probability block (start, middle, end arrays)
        self._ltr._singles._start = [self._reader.read_single() for _ in range(28)]
        self._ltr._singles._middle = [self._reader.read_single() for _ in range(28)]
        self._ltr._singles._end = [self._reader.read_single() for _ in range(28)]

        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LTRObject.ts:78-95
        
        # Read double-letter probability blocks (28 blocks, one per previous character)
        for i in range(28):
            self._ltr._doubles[i]._start = [self._reader.read_single() for _ in range(28)]
            self._ltr._doubles[i]._middle = [self._reader.read_single() for _ in range(28)]
            self._ltr._doubles[i]._end = [self._reader.read_single() for _ in range(28)]

        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LTRObject.ts:98-117
        
        # Read triple-letter probability blocks (28x28 blocks, indexed by previous two characters)
        for i in range(28):
            for j in range(28):
                self._ltr._triples[i][j]._start = [self._reader.read_single() for _ in range(28)]
                self._ltr._triples[i][j]._middle = [self._reader.read_single() for _ in range(28)]
                self._ltr._triples[i][j]._end = [self._reader.read_single() for _ in range(28)]

        if auto_close:
            self._reader.close()

        return self._ltr


class LTRBinaryWriter(ResourceWriter):
    def __init__(
        self,
        ltr: LTR,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._ltr: LTR = ltr

    def write(
        self,
        auto_close: bool = True,
    ):
        self._writer.write_string("LTR V1.0")
        self._writer.write_uint8(28)

        for chance in self._ltr._singles._start:
            self._writer.write_single(chance)
        for chance in self._ltr._singles._middle:
            self._writer.write_single(chance)
        for chance in self._ltr._singles._end:
            self._writer.write_single(chance)

        for i in range(28):
            for chance in self._ltr._doubles[i]._start:
                self._writer.write_single(chance)
            for chance in self._ltr._doubles[i]._middle:
                self._writer.write_single(chance)
            for chance in self._ltr._doubles[i]._end:
                self._writer.write_single(chance)

        for i, j in itertools.product(range(28), range(28)):
            for chance in self._ltr._triples[i][j]._start:
                self._writer.write_single(chance)
            for chance in self._ltr._triples[i][j]._middle:
                self._writer.write_single(chance)
            for chance in self._ltr._triples[i][j]._end:
                self._writer.write_single(chance)

        if auto_close:
            self._writer.close()
