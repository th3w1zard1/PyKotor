## DDS [file](GFF-File-Format) Format (KotOR)

DirectDraw Surface (DDS) [textures](TPC-File-Format) appear in two flavours across KotOR-era content:

- **Standard DirectX DDS** ([header](GFF-File-Format#file-header) magic `0x44445320`, 124-byte [header](GFF-File-Format#file-header)) used by downstream tools/ports.
- **BioWare DDS variant** (no magic; width/height/bpp/dataSize leading integers) used in Neverwinter Nights/KotOR game assets.

This page documents how PyKotor interprets both [formats](GFF-File-Format) and how it aligns with reference implementations in `vendor/xoreos` and `vendor/xoreos-tools`.

### Standard DDS (DX7+ container)

- Magic: `DDS` followed by a 124-[byte](GFF-File-Format#gff-data-types) [header](GFF-File-Format#file-header).
- Important [header](GFF-File-Format#file-header) [fields](GFF-File-Format#file-structure-overview):
  - `dwFlags` [bit](GFF-File-Format#gff-data-types) `0x00020000` signals mipmap [count](GFF-File-Format#file-structure-overview); otherwise one mipmap is assumed.
  - `dwHeight`, `dwWidth` validated up to 0x8000.
  - `DDPIXELFORMAT` describes layout:
    - FourCC `DXT1` → TPC `DXT1`
    - FourCC `DXT3` → TPC `DXT3`
    - FourCC `DXT5` → TPC `DXT5`
    - Uncompressed 32-[bit](GFF-File-Format#gff-data-types) BGRA masks (`00FF0000/0000FF00/000000FF/FF000000`) → TPC `BGRA`
    - Uncompressed 24-[bit](GFF-File-Format#gff-data-types) BGR masks (`00FF0000/0000FF00/000000FF`) → TPC `BGR`
    - 16-[bit](GFF-File-Format#gff-data-types) ARGB 1-5-5-5 (`7C00/03E0/001F/8000`) → converted to RGBA
    - 16-[bit](GFF-File-Format#gff-data-types) ARGB 4-4-4-4 (`0F00/00F0/000F/F000`) → converted to RGBA
    - 16-[bit](GFF-File-Format#gff-data-types) RGB 5-6-5 (`F800/07E0/001F/0`) → converted to RGB
  - Cubemap detection via `dwCaps2 & 0x00000200`; faces counted from `dwCaps2 & 0x0000FC00`.
- Each mip [size](GFF-File-Format#file-structure-overview) is computed with the [format](GFF-File-Format)-aware block sizing from `TPCTextureFormat.get_size`.
- [data](GFF-File-Format#file-structure-overview) layouts that [ARE](GFF-File-Format#are-area) not directly usable (4444, 1555, 565) [ARE](GFF-File-Format#are-area) expanded into RGBA/RGB before storing in the `TPC` object.

Implementation reference:

- `Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_dds.py` (standard DDS path and [format](GFF-File-Format) mapping)
- `vendor/xoreos/src/graphics/images/dds.cpp` and `vendor/xoreos-tools/src/images/dds.cpp` (baseline behaviour and [mask](GFF-File-Format#gff-data-types) checks)

### BioWare DDS variant

- No magic; [header](GFF-File-Format#file-header) is four [little-endian](https://en.wikipedia.org/wiki/Endianness) [uint32](GFF-File-Format#gff-data-types) [values](GFF-File-Format#gff-data-types):
  - `width`, `height` (must be powers of two, < 0x8000)
  - `bytesPerPixel` (`3` → DXT1, `4` → DXT5)
  - `dataSize` (must match `(width*height)/2` for DXT1 or `width*height` for DXT5)
- Followed by an unused [float](GFF-File-Format#gff-data-types), then the compressed payload and inferred mip levels until [data](GFF-File-Format#file-structure-overview) is exhausted.
- Mipmap [count](GFF-File-Format#file-structure-overview) is inferred by walking expected block sizes until [data](GFF-File-Format#file-structure-overview) would underflow.
- Always treated as compressed; no palette or other layouts.

Implementation reference:

- `Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_dds.py` (BioWare [header](GFF-File-Format#file-header) path)
- `vendor/xoreos/src/graphics/images/dds.cpp` lines around the BioWare branch for comparison.

### Writer behaviour (PyKotor)

- `TPCDDSWriter` emits only standard DDS [headers](GFF-File-Format#file-header):
  - Supports `DXT1`, `DXT3`, `DXT5`, and uncompressed `BGR/BGRA`.
  - Non-DDS-friendly [formats](GFF-File-Format) [ARE](GFF-File-Format#are-area) converted (`RGB`→`BGR`, `RGBA`→`BGRA`).
  - Mipmap counts validated per layer; cubemaps set caps (`DDSCAPS2_CUBEMAP|ALLFACES`).
- Payloads [ARE](GFF-File-Format#are-area) written in the already-compressed/uncompressed form stored in the `TPC` instance; no re-[compression](BIF-File-Format#bzf-compression) occurs.

### Detection and routing

- `detect_tpc()` now returns `ResourceType.DDS` when:
  - [file](GFF-File-Format) extension is `.dds`, or
  - Magic `DDS` is present, or
  - BioWare [header](GFF-File-Format#file-header) heuristics match width/height/bpp/dataSize.
- `read_tpc()` dispatches to `TPCDDSReader` when `ResourceType.DDS` is detected.
- `write_tpc(..., ResourceType.DDS)` routes to `TPCDDSWriter`.

### Testing coverage

- `Libraries/PyKotor/tests/resource/formats/test_dds.py`
  - Standard DDS DXT1 load/write roundtrip
  - BioWare DDS multi-mip parsing
  - Uncompressed BGRA [header](GFF-File-Format#file-header) parsing
  - Writer roundtrip for DXT1 payloads

### Practical differences vs. TGA/TPC

- **TGA**: uncompressed/RLE raster [data](GFF-File-Format#file-structure-overview); no block [compression](BIF-File-Format#bzf-compression); single [face](MDL-MDX-File-Format#face-structure) only; origin/alpha [flags](GFF-File-Format#gff-data-types) live in the [header](GFF-File-Format#file-header). DDS can be block-compressed (DXT1/3/5) and include cubemap [faces](MDL-MDX-File-Format#face-structure)/mip hierarchies in one container.
- **TPC**: KotOR-specific container with [TXI](TXI-File-Format) embedded and different [header](GFF-File-Format#file-header) layout; PyKotor maps DDS surfaces into `TPC` objects for unified downstream handling (conversion, [TXI](TXI-File-Format) logic, cubemap normalization).

### Notes and limits

- Palette-based DDS (`DDPF_INDEXED`) is rejected.
- Dimensions beyond 0x8000 [ARE](GFF-File-Format#are-area) rejected, matching xoreos limits.
- BioWare DDS requires power-of-two sizes; standard DDS does not enforce power-of-two beyond the existing dimension guard.
