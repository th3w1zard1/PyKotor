## DDS file Format (KotOR)

DirectDraw Surface (DDS) [textures](TPC-File-Format) appear in two flavours across KotOR-era content:

- **Standard DirectX DDS** (header magic `0x44445320`, 124-byte header) used by downstream tools/ports.
- **BioWare DDS variant** (no magic; width/height/bpp/dataSize leading integers) used in **KotOR and Neverwinter Nights** game assets (shared Aurora engine format).

This page documents how PyKotor interprets both formats and how it aligns with reference implementations in `vendor/xoreos` and `vendor/xoreos-tools`.

### Standard DDS (DX7+ container)

- Magic: `DDS` followed by a 124-[byte](GFF-File-Format#gff-data-types) header.
- Important header fields:
  - `dwFlags` bit `0x00020000` signals mipmap count; otherwise one mipmap is assumed.
  - `dwHeight`, `dwWidth` validated up to 0x8000.
  - `DDPIXELFORMAT` describes layout:
    - FourCC `DXT1` → TPC `DXT1`
    - FourCC `DXT3` → TPC `DXT3`
    - FourCC `DXT5` → TPC `DXT5`
    - Uncompressed 32-bit BGRA masks (`00FF0000/0000FF00/000000FF/FF000000`) → TPC `BGRA`
    - Uncompressed 24-bit BGR masks (`00FF0000/0000FF00/000000FF`) → TPC `BGR`
    - 16-bit ARGB 1-5-5-5 (`7C00/03E0/001F/8000`) → converted to RGBA
    - 16-bit ARGB 4-4-4-4 (`0F00/00F0/000F/F000`) → converted to RGBA
    - 16-bit RGB 5-6-5 (`F800/07E0/001F/0`) → converted to RGB
  - Cubemap detection via `dwCaps2 & 0x00000200`; faces counted from `dwCaps2 & 0x0000FC00`.
- Each mip size is computed with the format-aware block sizing from `TPCTextureFormat.get_size`.
- data layouts that are not directly usable (4444, 1555, 565) are expanded into RGBA/RGB before storing in the `TPC` object.

Implementation reference:

- `Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_dds.py` (standard DDS path and format mapping)
- `vendor/xoreos/src/graphics/images/dds.cpp` and `vendor/xoreos-tools/src/images/dds.cpp` (baseline behaviour and [mask](GFF-File-Format#gff-data-types) checks)

### BioWare DDS variant

- No magic; header is four [little-endian](https://en.wikipedia.org/wiki/Endianness) [uint32](GFF-File-Format#gff-data-types) values:
  - `width`, `height` (must be powers of two, < 0x8000)
  - `bytesPerPixel` (`3` → DXT1, `4` → DXT5)
  - `dataSize` (must match `(width*height)/2` for DXT1 or `width*height` for DXT5)
- Followed by an unused [float](GFF-File-Format#gff-data-types), then the compressed payload and inferred mip levels until data is exhausted.
- Mipmap count is inferred by walking expected block sizes until data would underflow.
- Always treated as compressed; no palette or other layouts.

Implementation reference:

- `Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_dds.py` (BioWare header path)
- `vendor/xoreos/src/graphics/images/dds.cpp` lines around the BioWare branch for comparison.

### Writer behaviour (PyKotor)

- `TPCDDSWriter` emits only standard DDS headers:
  - Supports `DXT1`, `DXT3`, `DXT5`, and uncompressed `BGR/BGRA`.
  - Non-DDS-friendly formats are converted (`RGB`→`BGR`, `RGBA`→`BGRA`).
  - Mipmap counts validated per layer; cubemaps set caps (`DDSCAPS2_CUBEMAP|ALLFACES`).
- Payloads are written in the already-compressed/uncompressed form stored in the `TPC` instance; no re-compression occurs.

### Detection and routing

- `detect_tpc()` now returns `ResourceType.DDS` when:
  - file extension is `.dds`, or
  - Magic `DDS` is present, or
  - BioWare header heuristics match width/height/bpp/dataSize.
- `read_tpc()` dispatches to `TPCDDSReader` when `ResourceType.DDS` is detected.
- `write_tpc(..., ResourceType.DDS)` routes to `TPCDDSWriter`.

### Testing coverage

- `Libraries/PyKotor/tests/resource/formats/test_dds.py`
  - Standard DDS DXT1 load/write roundtrip
  - BioWare DDS multi-mip parsing
  - Uncompressed BGRA header parsing
  - Writer roundtrip for DXT1 payloads

### Practical differences vs. TGA/TPC

- **TGA**: uncompressed/RLE raster data; no block compression; single [face](MDL-MDX-File-Format#face-structure) only; origin/alpha [flags](GFF-File-Format#gff-data-types) live in the header. DDS can be block-compressed (DXT1/3/5) and include cubemap [faces](MDL-MDX-File-Format#face-structure)/mip hierarchies in one container.
- **TPC**: KotOR-specific container with [TXI](TXI-File-Format) embedded and different header layout; PyKotor maps DDS surfaces into `TPC` objects for unified downstream handling (conversion, [TXI](TXI-File-Format) logic, cubemap normalization).

### Notes and limits

- Palette-based DDS (`DDPF_INDEXED`) is rejected.
- Dimensions beyond 0x8000 are rejected, matching xoreos limits.
- BioWare DDS requires power-of-two sizes; standard DDS does not enforce power-of-two beyond the existing dimension guard.
