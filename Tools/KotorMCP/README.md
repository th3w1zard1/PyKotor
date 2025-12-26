<div align="center">

# KotorMCP

[![Version](https://img.shields.io/github/v/release/th3w1zard1/PyKotor?label=KotorMCP)](https://github.com/OldRepublicDevs/PyKotor/releases)
[![License](https://img.shields.io/github/license/th3w1zard1/PyKotor)](https://github.com/OldRepublicDevs/PyKotor/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-blueviolet)](https://modelcontextprotocol.io)

**Model Context Protocol server for Knights of the Old Republic game resources**

</div>

A Model Context Protocol (MCP) server that exposes context-rich tools for AI agents to interact with Knights of the Old Republic (KOTOR) and Knights of the Old Republic II: The Sith Lords (TSL) game installations. This server provides intelligent resource discovery, installation management, and game data inspection capabilities tailored for automated analysis and debugging workflows.

## Features

- **Installation Detection & Management**
  - Automatic detection of KOTOR 1 and KOTOR 2 installations
  - Environment variable support (`K1_PATH`, `K2_PATH`, `TSL_PATH`, etc.)
  - Default path discovery (Windows registry, common install locations)
  - Installation caching for performance

- **Resource Discovery & Inspection**
  - List resources from all locations (override, modules, chitin, streams)
  - Filter by resource type, name patterns, and module scope
  - Deep resource summarization (GFF structures, 2DA tables, TLK strings)
  - Resource metadata extraction (size, location, type)

- **Journal & Plot Analysis**
  - Comprehensive journal entry overview (`global.jrl`)
  - Plot category organization
  - Quest entry enumeration
  - Cross-references with game scripts and dialogs

- **AI-Optimized Workflows**
  - Context-rich responses designed for LLM consumption
  - Structured JSON output for programmatic access
  - Efficient resource scanning with configurable limits
  - Installation-aware resource resolution

## Installation Guide

### Prerequisites

- Python 3.11 or higher
- A valid KOTOR 1 or KOTOR 2 installation
- MCP-compatible client (Claude Desktop, Cursor, etc.)

### Quick Start

#### Using pip

```bash
# Install from PyPI (when available)
pip install kotormcp

# Or install from source
git clone https://github.com/OldRepublicDevs/PyKotor.git
cd PyKotor/Tools/KotorMCP
pip install -e .
```

#### Using uv (Recommended)

```bash
# Install with uv
uv pip install kotormcp

# Or from source
uv pip install -e Tools/KotorMCP
```

### Configuration

#### Claude Desktop

Add the following to your Claude Desktop configuration file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "kotormcp": {
      "command": "uvx",
      "args": [
        "--from",
        "kotormcp @ git+https://github.com/th3w1zard1/KotorMCP.git",
        "kotormcp"
      ],
      "env": {
        "K1_PATH": "C:\\Program Files\\steamapps\\common\\swkotor",
        "K2_PATH": "C:\\Program Files\\steamapps\\common\\Knights of the Old Republic II"
      }
    }
  }
}
```

#### Cursor / VS Code (Claude Dev Extension)

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "kotormcp": {
      "command": "uvx",
      "args": [
        "--from",
        "kotormcp @ git+https://github.com/th3w1zard1/KotorMCP.git",
        "kotormcp"
      ],
      "env": {
        "K1_PATH": "C:\\Program Files\\steamapps\\common\\swkotor",
        "K2_PATH": "C:\\Program Files\\steamapps\\common\\Knights of the Old Republic II"
      }
    }
  }
}
```

#### Environment Variables

The server automatically detects installations using these environment variables (in order of precedence):

**KOTOR 1:**

- `K1_PATH`
- `KOTOR_PATH`
- `KOTOR1_PATH`

**KOTOR 2:**

- `K2_PATH`
- `TSL_PATH`
- `KOTOR2_PATH`
- `K1_PATH` (fallback)

If environment variables are not set, the server will attempt to find installations using default paths (Windows registry, common install locations).

## Usage Guide

The server provides five main tools for interacting with KOTOR installations:

### 1. `detectInstallations`

Detect available KOTOR installations and their paths.

**Parameters:** None

**Response:**

```json
{
  "K1": [
    {
      "path": "C:\\Program Files\\LucasArts\\SWKotOR",
      "exists": true,
      "label": "default"
    }
  ],
  "K2": [
    {
      "path": "C:\\Program Files\\LucasArts\\SWKotOR2",
      "exists": true,
      "label": "env"
    }
  ]
}
```

**Example:**

```typescript
use_mcp_tool({
  server_name: "kotormcp",
  tool_name: "detectInstallations",
  arguments: {}
})
```

### 2. `loadInstallation`

Load and cache a KOTOR installation for subsequent operations.

**Parameters:**

- `game` (string, required): Game identifier (`"k1"`, `"k2"`, `"tsl"`, `"kotori"`, `"kotor2"`)
- `path` (string, optional): Explicit installation path (overrides environment variables)

**Response:**

```json
{
  "game": "K1",
  "path": "C:\\Program Files\\LucasArts\\SWKotOR"
}
```

**Example:**

```typescript
use_mcp_tool({
  server_name: "kotormcp",
  tool_name: "loadInstallation",
  arguments: {
    game: "k1",
    path: "C:\\Program Files\\LucasArts\\SWKotOR"
  }
})
```

### 3. `listResources`

List resources from the active installation with filtering options.

**Parameters:**

- `game` (string, required): Game identifier
- `location` (string, optional): Resource location filter (`"all"`, `"override"`, `"modules"`, `"chitin"`, `"streams"`) - default: `"all"`
- `moduleFilter` (string, optional): Filter by module name (e.g., `"001ebo"`)
- `resourceTypes` (string, optional): Comma-separated resource type extensions (e.g., `"gff,dlg,jrl"`)
- `resrefQuery` (string, optional): Filter resources by name pattern (case-insensitive)
- `limit` (number, optional): Maximum number of results (default: 50)

**Response:**

```json
{
  "count": 25,
  "items": [
    {
      "resref": "global",
      "restype": "JRL",
      "source": "override",
      "size": 12345,
      "module": null
    }
  ],
  "truncated": false
}
```

**Example:**

```typescript
use_mcp_tool({
  server_name: "kotormcp",
  tool_name: "listResources",
  arguments: {
    game: "k1",
    location: "override",
    resourceTypes: "jrl,gff",
    resrefQuery: "global",
    limit: 10
  }
})
```

### 4. `describeResource`

Get detailed information about a specific resource, including structured data for GFF files, 2DA tables, and TLK files.

**Parameters:**

- `game` (string, required): Game identifier
- `resref` (string, required): Resource name (without extension)
- `restype` (string, required): Resource type extension (e.g., `"jrl"`, `"gff"`, `"2da"`, `"tlk"`)
- `order` (array, optional): Search location priority order (default: `["override", "custom_folders", "modules", "chitin"]`)

**Response:**

```json
{
  "resref": "global",
  "restype": "JRL",
  "source": "override",
  "size": 12345,
  "summary": {
    "type": "JRL",
    "categories": 5,
    "entries": 42,
    "structure": "..."
  }
}
```

**Example:**

```typescript
use_mcp_tool({
  server_name: "kotormcp",
  tool_name: "describeResource",
  arguments: {
    game: "k1",
    resref: "global",
    restype: "jrl"
  }
})
```

### 5. `journalOverview`

Get a comprehensive overview of journal entries and plot categories from `global.jrl`.

**Parameters:**

- `game` (string, required): Game identifier

**Response:**

```json
{
  "count": 5,
  "categories": [
    {
      "id": 0,
      "name": "Main Quest",
      "entries": [
        {
          "id": 0,
          "title": "Escape from Taris",
          "text": "You must escape from the planet Taris..."
        }
      ]
    }
  ]
}
```

**Example:**

```typescript
use_mcp_tool({
  server_name: "kotormcp",
  tool_name: "journalOverview",
  arguments: {
    game: "k1"
  }
})
```

## Common Workflows

### Finding All Resources That Modify Plot Points

```typescript
// 1. Load installation
await loadInstallation({ game: "k1" });

// 2. List all journal-related resources
const resources = await listResources({
  game: "k1",
  resourceTypes: "jrl,gff,dlg",
  resrefQuery: "global",
  limit: 100
});

// 3. Get journal overview
const journal = await journalOverview({ game: "k1" });

// 4. Search for scripts that reference plot points
const scripts = await listResources({
  game: "k1",
  resourceTypes: "ncs",
  resrefQuery: "plot",
  limit: 50
});
```

### Investigating Module Structure

```typescript
// 1. List all resources in a specific module
const moduleResources = await listResources({
  game: "k1",
  location: "modules",
  moduleFilter: "001ebo",
  limit: 200
});

// 2. Get detailed information about key resources
const area = await describeResource({
  game: "k1",
  resref: "001ebo",
  restype: "are"
});

const git = await describeResource({
  game: "k1",
  resref: "001ebo",
  restype: "git"
});
```

### Debugging Missing Resources

```typescript
// 1. Check all locations for a resource
const resource = await describeResource({
  game: "k1",
  resref: "missing_resource",
  restype: "gff",
  order: ["override", "modules", "chitin", "streams"]
});

// 2. List similar resources
const similar = await listResources({
  game: "k1",
  resrefQuery: "missing",
  limit: 20
});
```

## Architecture

KotorMCP is built on the [Model Context Protocol](https://modelcontextprotocol.io) specification and uses the official Python MCP SDK. The server:

- **Caches installations** for performance across multiple tool calls
- **Resolves resources** using the same logic as `KotorCLI` and PyKotor's `Installation` class
- **Provides structured summaries** optimized for LLM consumption
- **Follows established patterns** from engine reimplementations (reone, xoreos, kotor.js)

### Implementation Notes

- Resource scanning logic mirrors `scripts/investigate_module_structure.py`
- Journal summarization follows the structure documented in `vendor/xoreos/src/engines/nwn2/journal.cpp`
- Resource resolution uses PyKotor's `Installation` class with configurable search order
- GFF structure summarization provides hierarchical field overviews

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/OldRepublicDevs/PyKotor.git
cd PyKotor

# Install dependencies
uv pip install -e Tools/KotorMCP

# Run the server
python -m kotormcp.server
```

### Project Structure

```
Tools/KotorMCP/
├── src/
│   └── kotormcp/
│       ├── __init__.py
│       └── server.py          # Main MCP server implementation
├── pyproject.toml             # Project metadata and dependencies
├── requirements.txt            # Pip-compatible requirements
└── README.md                  # This file
```

### Dependencies

- `mcp>=0.1.1` - Model Context Protocol Python SDK
- `pykotor>=1.8.0` - PyKotor core library for KOTOR file format support

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For bug reports or feature requests, please open an issue on [GitHub](https://github.com/OldRepublicDevs/PyKotor/issues).

## License

This project is part of the PyKotor ecosystem and is licensed under the LGPL-3.0-or-later License. See the main repository [LICENSE](https://github.com/OldRepublicDevs/PyKotor/blob/main/LICENSE) file for details.

## Related Projects

- **[PyKotor](https://github.com/OldRepublicDevs/PyKotor)** - Core library for KOTOR file formats
- **[KotorCLI](https://github.com/OldRepublicDevs/PyKotor/tree/main/Tools/KotorCLI)** - Command-line interface for KOTOR resources
- **[Holocron Toolset](https://github.com/OldRepublicDevs/PyKotor/tree/main/Tools/HolocronToolset)** - GUI editor for KOTOR files

## Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.io) specification
- Uses the [PyKotor](https://github.com/OldRepublicDevs/PyKotor) library for game file format support
- Inspired by engine reimplementations: [reone](https://github.com/reone-project/reone), [xoreos](https://github.com/xoreos/xoreos), [kotor.js](https://github.com/jakubg1/kotor.js)

---

<div align="center">

**Made with ❤️ for the KOTOR modding community**

[Report Bug](https://github.com/OldRepublicDevs/PyKotor/issues) · [Request Feature](https://github.com/OldRepublicDevs/PyKotor/issues) · [Documentation](https://github.com/OldRepublicDevs/PyKotor/wiki)

</div>
