# Comprehensive CLI Commands Reference

This document catalogs all CLI commands, arguments, and parameters from the following repositories/projects to ensure comprehensive and exhaustive support in KotorCLI.

## Table of Contents

1. [reone (seedhartha/reone)](#reone-seedharthareone)
2. [neverwinter.nim (niv/neverwinter.nim)](#neverwinternim-nivneverwinternim)
3. [xoreos-tools (xoreos/xoreos-tools)](#xoreos-tools-xoreosxoreos-tools)
4. [nasher (squattingmonk/nasher)](#nasher-squattingmonknasher)
5. [mdlops (ndixUR/mdlops)](#mdlops-ndixurmdlops)
6. [ncs2nss (lachjames/ncs2nss)](#ncs2nss-lachjamesncs2nss)
7. [Other CLI Tools](#other-cli-tools)

---

## reone (seedhartha/reone)

**Repository**: <https://github.com/seedhartha/reone>  
**Primary Games**: KOTOR 1/2 (Odyssey)  
**Tools**: reone-tool, mills

### reone-tool

Extract/convert KOTOR format files.

**Commands/Operations**:

- Extract KEY/BIF archives
- Extract RIM archives
- Extract ERF archives
- Convert TPC→TGA textures
- Convert SSF→WAV sounds
- Convert LIP files
- Model operations (MDL/MDX)

**Expected CLI Syntax** (to be investigated from source):

```bash
reone-tool [command] [options] [input] [output]
```

**Key Features**:

- KEY/BIF extraction
- RIM extraction
- ERF extraction
- TPC to TGA conversion
- SSF to WAV conversion
- LIP file handling
- Model file operations

### mills

MDL/MDX compilation, lightmap baking, pathfinding.

**Expected CLI Syntax** (to be investigated from source):

```bash
mills [command] [options] [input] [output]
```

**Key Features**:

- MDL/MDX compilation (binary ↔ editable ↔ binary)
- Lightmap baking
- Pathfinding generation

---

## neverwinter.nim (niv/neverwinter.nim)

**Repository**: <https://github.com/niv/neverwinter.nim>  
**Primary Games**: Neverwinter Nights 1 & 2 (Aurora/Electron)  
**Tools**: 20+ utilities

### nwn_resman_*

Resource manager utilities.

#### nwn_resman_grep

```bash
nwn_resman_grep [options] <pattern> [files...]
```

- Search for text patterns in game resources
- Supports regex patterns
- Can search across multiple archive types

#### nwn_resman_extract

```bash
nwn_resman_extract [options] <resource> <output>
```

- Extract specific resources from archives
- Supports KEY, BIF, ERF, RIM formats
- Output directory specification

#### nwn_resman_cat

```bash
nwn_resman_cat [options] <resource>
```

- Display resource contents to stdout
- Supports text-based resources
- Useful for quick inspection

#### nwn_resman_diff

```bash
nwn_resman_diff [options] <resource1> <resource2>
```

- Compare two resources
- Shows differences
- Useful for mod development

#### nwn_resman_stats

```bash
nwn_resman_stats [options] [files...]
```

- Show statistics about resources
- Archive sizes, resource counts
- Compression ratios

#### nwn_resman_pkg

```bash
nwn_resman_pkg [options] <directory> <output>
```

- Package directory into archive
- Supports ERF, HAK formats
- Resource deduplication

### nwn_erf_*

ERF archive utilities.

#### nwn_erf (pack/unpack)

```bash
nwn_erf pack [options] <directory> <output.erf>
nwn_erf unpack [options] <erf_file> <output_dir>
```

- Pack/unpack ERF archives
- Resource filtering
- Metadata preservation

### nwn_erf_tlkify

```bash
nwn_erf_tlkify [options] <erf_file> [output]
```

- Convert ERF string references to TLK indices
- Supports batch processing
- TLK file specification

### nwn_key_*

KEY/BIF archive utilities.

#### nwn_key_pack

```bash
nwn_key_pack [options] <directory> <output.key>
```

- Create KEY archive from directory
- BIF file association
- Resource table generation

#### nwn_key_unpack

```bash
nwn_key_unpack [options] <key_file> <output_dir>
```

- Extract KEY archive
- Extract associated BIF files
- Resource extraction

#### nwn_key_shadows

```bash
nwn_key_shadows [options] <key_file>
```

- Analyze resource shadowing
- Show resource conflicts
- Priority resolution

#### nwn_key_transparent

```bash
nwn_key_transparent [options] <key_file> [output]
```

- Create transparent KEY (all resources visible)
- Useful for development
- Resource merging

### nwn_gff

GFF format utilities.

```bash
nwn_gff [options] <command> <input> [output]
```

**Commands**:

- `convert` - Convert GFF between formats (binary/XML/JSON)
- `extract` - Extract specific fields
- `merge` - Merge GFF files
- `validate` - Validate GFF structure

**Options**:

- `--format` - Output format (binary/xml/json)
- `--pretty` - Pretty-print output
- `--compress` - Enable compression
- `--fields` - Specific fields to extract

### nwn_tlk

TLK (talk table) utilities.

```bash
nwn_tlk [options] <command> <input> [output]
```

**Commands**:

- `convert` - Convert TLK to/from XML/CSV
- `merge` - Merge multiple TLK files
- `extract` - Extract specific strings
- `import` - Import from CSV/XML
- `export` - Export to CSV/XML

**Options**:

- `--format` - Output format
- `--encoding` - Character encoding
- `--range` - String ID range
- `--filter` - Filter strings by pattern

### nwn_twoda

2DA (two-dimensional array) utilities.

```bash
nwn_twoda [options] <command> <input> [output]
```

**Commands**:

- `convert` - Convert 2DA to/from CSV/JSON
- `merge` - Merge 2DA files
- `diff` - Compare 2DA files
- `validate` - Validate 2DA structure

**Options**:

- `--format` - Output format
- `--delimiter` - CSV delimiter
- `--headers` - Include headers

### nwn_script_comp

NWScript compiler/assembler.

```bash
nwn_script_comp compile [options] <input.nss> [output.ncs]
nwn_script_comp assemble [options] <input.ncs> [output.nss]
nwn_script_comp disassemble [options] <input.ncs> [output.txt]
```

**Options**:

- `--include` - Include directories
- `--optimize` - Enable optimizations
- `--debug` - Include debug info
- `--game` - Target game version
- `--warnings` - Warning level

### nwn_compressedbuf

Compressed buffer utilities.

```bash
nwn_compressedbuf compress [options] <input> <output>
nwn_compressedbuf decompress [options] <input> <output>
```

**Options**:

- `--level` - Compression level (1-9)
- `--format` - Compression format

### nwn_asm

NWScript assembler.

```bash
nwn_asm [options] <input.asm> [output.ncs]
```

**Options**:

- `--include` - Include directories
- `--output` - Output file
- `--debug` - Debug output

### nwn_net

Network utilities.

```bash
nwn_net [options] <command> [args...]
```

**Commands**:

- `server` - Start server
- `client` - Connect client
- `query` - Query server status

### nwn_nwsync_*

NWSync server utilities.

#### nwn_nwsync_write

```bash
nwn_nwsync_write [options] <module_dir> <output>
```

- Create NWSync manifest
- Module packaging
- Version information

#### nwn_nwsync_fetch

```bash
nwn_nwsync_fetch [options] <manifest> <output_dir>
```

- Fetch module from NWSync server
- Resource downloading
- Verification

#### nwn_nwsync_print

```bash
nwn_nwsync_print [options] <manifest>
```

- Print manifest information
- Resource listing
- Metadata display

#### nwn_nwsync_prune

```bash
nwn_nwsync_prune [options] <manifest> [output]
```

- Prune manifest
- Remove unused resources
- Optimization

### nwn_ssf

SSF (sound set file) utilities.

```bash
nwn_ssf [options] <command> <input> [output]
```

**Commands**:

- `convert` - Convert SSF to/from XML
- `extract` - Extract sound references

---

## xoreos-tools (xoreos/xoreos-tools)

**Repository**: <https://github.com/xoreos/xoreos-tools>  
**Primary Games**: NWN1/2, KOTOR 1/2, Jade Empire, Dragon Age, The Witcher  
**Tools**: 30+ tools

### Archive Tools

#### unerf

```bash
unerf [options] <erf_file> [output_dir]
```

- Extract ERF archives
- Options: `--list`, `--filter`, `--output`

#### unrim

```bash
unrim [options] <rim_file> [output_dir]
```

- Extract RIM archives
- Options: `--list`, `--filter`, `--output`

#### unkeybif

```bash
unkeybif [options] <key_file> [output_dir]
```

- Extract KEY/BIF archives
- Options: `--list`, `--filter`, `--output`, `--bif-dir`

#### unherf

```bash
unherf [options] <herf_file> [output_dir]
```

- Extract HERF archives (Jade Empire)
- Options: `--list`, `--filter`, `--output`

#### unnds

```bash
unnds [options] <nds_file> [output_dir]
```

- Extract NDS archives (Nintendo DS)
- Options: `--list`, `--filter`, `--output`

#### unobb

```bash
unobb [options] <obb_file> [output_dir]
```

- Extract OBB archives (Android)
- Options: `--list`, `--filter`, `--output`

#### untws

```bash
untws [options] <tws_file> [output_dir]
```

- Extract TWS archives (The Witcher)
- Options: `--list`, `--filter`, `--output`

### Archive Creation Tools

#### erf

```bash
erf [options] create <directory> <output.erf>
erf [options] list <erf_file>
erf [options] extract <erf_file> [output_dir]
```

- Create/list/extract ERF archives
- Options: `--type`, `--compress`, `--filter`

#### rim

```bash
rim [options] create <directory> <output.rim>
rim [options] list <rim_file>
rim [options] extract <rim_file> [output_dir]
```

- Create/list/extract RIM archives
- Options: `--compress`, `--filter`

#### keybif

```bash
keybif [options] create <key_dir> <bif_dir> <output.key>
keybif [options] list <key_file>
```

- Create KEY/BIF archives
- Options: `--filter`, `--compress`

#### tws

```bash
tws [options] create <directory> <output.tws>
tws [options] list <tws_file>
tws [options] extract <tws_file> [output_dir]
```

- Create/list/extract TWS archives
- Options: `--compress`, `--filter`

### Format Conversion Tools

#### gff2xml

```bash
gff2xml [options] <input.gff> [output.xml]
```

- Convert GFF to XML
- Options: `--pretty`, `--indent`, `--output`

#### xml2gff

```bash
xml2gff [options] <input.xml> [output.gff]
```

- Convert XML to GFF
- Options: `--type`, `--compress`, `--output`

#### tlk2xml

```bash
tlk2xml [options] <input.tlk> [output.xml]
```

- Convert TLK to XML
- Options: `--pretty`, `--encoding`, `--output`

#### xml2tlk

```bash
xml2tlk [options] <input.xml> [output.tlk]
```

- Convert XML to TLK
- Options: `--encoding`, `--output`

#### ssf2xml

```bash
ssf2xml [options] <input.ssf> [output.xml]
```

- Convert SSF to XML
- Options: `--pretty`, `--output`

#### xml2ssf

```bash
xml2ssf [options] <input.xml> [output.ssf]
```

- Convert XML to SSF
- Options: `--output`

#### convert2da

```bash
convert2da [options] <input.2da> <output.csv>
convert2da [options] <input.csv> <output.2da>
```

- Convert 2DA to/from CSV
- Options: `--delimiter`, `--headers`, `--encoding`

### NWScript Tools

#### ncsdis

```bash
ncsdis [options] <input.ncs> [output.txt]
```

- Disassemble NCS bytecode
- Options: `--pretty`, `--output`

#### ncsdecomp

```bash
ncsdecomp [options] <input.ncs> [output.nss]
```

- Decompile NCS to NSS
- Options: `--pretty`, `--output`, `--comments`

### Texture Tools

#### xoreostex2tga

```bash
xoreostex2tga [options] <input.tex> [output.tga]
```

- Convert xoreos texture to TGA
- Options: `--format`, `--output`

#### cbgt2tga

```bash
cbgt2tga [options] <input.cbgt> [output.tga]
```

- Convert CBGT to TGA
- Options: `--output`

#### cdpth2tga

```bash
cdpth2tga [options] <input.cdpth> [output.tga]
```

- Convert CDPTH to TGA
- Options: `--output`

#### nbfs2tga

```bash
nbfs2tga [options] <input.nbfs> [output.tga]
```

- Convert NBFS to TGA
- Options: `--output`

#### ncgr2tga

```bash
ncgr2tga [options] <input.ncgr> [output.tga]
```

- Convert NCGR to TGA
- Options: `--output`

### Other Tools

#### fixpremiumgff

```bash
fixpremiumgff [options] <input.gff> [output.gff]
```

- Fix premium module GFF files
- Options: `--output`

#### fixnwn2xml

```bash
fixnwn2xml [options] <input.xml> [output.xml]
```

- Fix NWN2 XML files
- Options: `--output`

#### fev2xml

```bash
fev2xml [options] <input.fev> [output.xml]
```

- Convert FEV to XML
- Options: `--output`

#### desmall

```bash
desmall [options] <input.small> [output]
```

- Decompress SMALL archives
- Options: `--output`

---

## nasher (squattingmonk/nasher)

**Repository**: <https://github.com/squattingmonk/nasher>  
**Primary Games**: Neverwinter Nights (Aurora)  
**Tools**: Build tool for NWN modules

### Main Commands

#### pack

```bash
nasher pack [options] [target]
```

- Pack module/hak/erf from source
- Options: `--clean`, `--skip-compile`, `--output`

#### unpack

```bash
nasher unpack [options] [target] [file]
```

- Unpack module/hak/erf to source
- Options: `--clean`, `--output-dir`

#### convert

```bash
nasher convert [options] [target]
```

- Convert source files
- Options: `--from`, `--to`, `--format`

#### compile

```bash
nasher compile [options] [target] [files...]
```

- Compile NWScript files
- Options: `--clean`, `--file`, `--output-dir`

#### install

```bash
nasher install [options] [target]
```

- Install module to game directory
- Options: `--install-dir`, `--overwrite`

#### serve

```bash
nasher serve [options] [target]
```

- Start development server
- Options: `--port`, `--host`

#### clean

```bash
nasher clean [options] [target]
```

- Clean build artifacts
- Options: `--all`, `--cache`

#### list

```bash
nasher list [options]
```

- List targets
- Options: `--verbose`

#### config

```bash
nasher config [options] <key> [value]
nasher config [options] --list
```

- Get/set configuration
- Options: `--global`, `--local`, `--list`

---

## mdlops (ndixUR/mdlops)

**Repository**: <https://github.com/ndixUR/mdlops>  
**Primary Games**: KOTOR 1/2, Jade Empire (Odyssey)  
**Tools**: Model conversion (binary ↔ ASCII)

### Main Commands

```bash
mdlops [options] <command> <input> [output]
```

**Commands**:

- `toascii` - Convert binary MDL to ASCII
- `tobinary` - Convert ASCII MDL to binary
- `validate` - Validate MDL structure
- `info` - Show MDL information

**Options**:

- `--game` - Target game (kotor1/kotor2/jade)
- `--output` - Output file/directory
- `--verbose` - Verbose output
- `--warnings` - Show warnings

---

## ncs2nss (lachjames/ncs2nss)

**Repository**: <https://github.com/lachjames/ncs2nss>  
**Primary Games**: NWN 1/2, KOTOR (Aurora/Odyssey)  
**Tools**: NCS bytecode decompiler

### Main Command

```bash
ncs2nss [options] <input.ncs> [output.nss]
```

**Options**:

- `--output` / `-o` - Output file
- `--pretty` - Pretty-print output
- `--comments` - Include comments
- `--library` - Library file path
- `--verbose` - Verbose output
- `--game` - Target game (nwn/kotor)

---

## Other CLI Tools

### nwnsc (nwneetools/nwnsc)

**Repository**: <https://github.com/nwneetools/nwnsc>  
**Primary Games**: Neverwinter Nights: Enhanced Edition  
**Tools**: NWScript compiler

```bash
nwnsc [options] <input.nss> [output.ncs]
```

**Options**:

- `--output` / `-o` - Output file
- `--include` / `-I` - Include directories
- `--optimize` - Enable optimizations
- `--debug` - Include debug info
- `--warnings` - Warning level
- `--game` - Target game version
- `--version` - Show version

### erfherder-cli (jd28/arclight-py)

**Repository**: <https://github.com/jd28/arclight-py>  
**Primary Games**: Neverwinter Nights / general Aurora  
**Tools**: ERF/HAK container tools

```bash
erfherder [options] <command> [args...]
```

**Commands**:

- `extract` - Extract ERF/HAK
- `pack` - Pack directory to ERF/HAK
- `list` - List contents
- `search` - Search with regex

**Options**:

- `--regex` - Use regex matching
- `--output` - Output directory/file
- `--filter` - Resource filter

### unbif (marc-q/unbif)

**Repository**: <https://github.com/marc-q/unbif>  
**Primary Games**: Neverwinter Nights (Aurora)  
**Tools**: BIF unpacker

```bash
unbif [options] <bif_file> [output_dir]
```

**Options**:

- `--list` - List contents only
- `--output` - Output directory
- `--filter` - Resource filter

### da2tlkconv (longod/da2tlkconv)

**Repository**: <https://github.com/longod/da2tlkconv>  
**Primary Games**: Dragon Age II (Eclipse)  
**Tools**: TLK converter

```bash
da2tlkconv [options] <command> <input> [output]
```

**Commands**:

- `to_text` - Convert TLK to text
- `to_tlk` - Convert text to TLK

**Options**:

- `--encoding` - Character encoding
- `--output` - Output file

### nwn-gff (CromFr/nwn-lib-d)

**Repository**: <https://github.com/CromFr/nwn-lib-d>  
**Primary Games**: Neverwinter Nights 1/2  
**Tools**: GFF/JSON/YAML conversion

```bash
nwn-gff [options] <command> <input> [output]
```

**Commands**:

- `convert` - Convert GFF/JSON/YAML
- `edit` - In-place editing
- `validate` - Validate structure

**Options**:

- `--format` - Output format
- `--pretty` - Pretty-print
- `--in-place` - Edit in place

---

## Command Categories for Implementation

Based on the comprehensive analysis above, KotorCLI should support:

### Core Build Commands (Already Implemented)

- `config` - Configuration management
- `init` - Project initialization
- `list` - List targets
- `unpack` - Unpack archives
- `convert` - Format conversion
- `compile` - Script compilation
- `pack` - Pack archives
- `install` - Install to game directory
- `launch` - Launch game

### Archive Management Commands (To Add)

- `extract` - Extract from various archive types (KEY/BIF, RIM, ERF, etc.)
- `create-archive` - Create archives from directories
- `list-archive` - List archive contents
- `search-archive` - Search archives with patterns

### Format Conversion Commands (To Add)

- `gff2json` / `json2gff` - GFF ↔ JSON conversion
- `gff2xml` / `xml2gff` - GFF ↔ XML conversion
- `tlk2xml` / `xml2tlk` - TLK ↔ XML conversion
- `ssf2xml` / `xml2ssf` - SSF ↔ XML conversion
- `2da2csv` / `csv2da` - 2DA ↔ CSV conversion

### Script Tools (To Add)

- `decompile` - Decompile NCS to NSS
- `disassemble` - Disassemble NCS bytecode
- `assemble` - Assemble NSS to NCS

### Resource Tools (To Add)

- `texture-convert` - Convert textures (TPC↔TGA, etc.)
- `sound-convert` - Convert sounds (SSF↔WAV, etc.)
- `model-convert` - Convert models (MDL↔ASCII)

### Utility Commands (To Add)

- `diff` - Compare resources
- `grep` - Search resources
- `stats` - Show resource statistics
- `validate` - Validate file formats
- `merge` - Merge resources

### kit-generate

Generate a Holocron-compatible kit from a module (headless or GUI).

```bash
python -m kotorcli kit-generate --installation <path> --module <module> --output <dir> [--kit-id <id>] [--log-level info|debug|warning|error|critical]
```

- Uses `pykotor.tools.kit.extract_kit` internally (see `Libraries/PyKotor/src/pykotor/tools/kit.py`)
- Requires installation path, module name (stem is normalized), and output directory
- Supplying required args keeps execution headless; running `python -m kotorcli` with no args opens the Tkinter GUI for interactive kit generation

### gui-convert

Convert KotOR GUI layouts to target resolutions. Headless when arguments are provided; launches a Tk GUI when arguments are omitted.

```bash
python -m kotorcli gui-convert --input <file_or_folder> --output <dir> --resolution <WIDTHxHEIGHT|ALL>
```

- Multiple `--input` values are allowed
- `--resolution` accepts comma-separated WIDTHxHEIGHT or `ALL` for every supported aspect ratio/resolution pair
- Internally uses `pykotor.resource.formats.gff` to resize controls (`Libraries/PyKotor/src/pykotor/resource/formats/gff`)

### Advanced Commands (To Add)

- `resman` - Resource manager interface
- `key-pack` / `key-unpack` - KEY/BIF operations
- `rim-pack` / `rim-unpack` - RIM operations
- `erf-pack` / `erf-unpack` - ERF operations

---

## Implementation Priority

### Phase 1: Archive Operations

1. Extract operations (KEY/BIF, RIM, ERF)
2. Pack operations (ERF, RIM)
3. List archive contents

### Phase 2: Format Conversions

1. GFF conversions (JSON, XML)
2. TLK conversions (XML, CSV)
3. 2DA conversions (CSV)

### Phase 3: Script Tools

1. Decompile NCS→NSS
2. Disassemble NCS
3. Script utilities

### Phase 4: Resource Tools

1. Texture conversion
2. Sound conversion
3. Model conversion

### Phase 5: Advanced Utilities

1. Resource manager
2. Diff/grep/stats
3. Validation tools

---

## Notes

- This document should be updated as CLI syntax is discovered from source code
- All commands should support `--help` for documentation
- Commands should follow consistent naming conventions
- Options should use standardized flags where possible (e.g., `--output`, `--verbose`, `--quiet`)
