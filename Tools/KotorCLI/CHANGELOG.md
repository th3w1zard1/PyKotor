# Changelog

All notable changes to KotorCLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-21

### Added
- Initial release of KotorCLI
- cli-compatible command syntax
- Support for all major commands:
  - `config` - Configuration management
  - `init` - Project initialization
  - `list` - List targets
  - `unpack` - Unpack modules/ERFs/haks to source
  - `convert` - Convert JSON to GFF
  - `compile` - Compile NWScript
  - `pack` - Pack sources into module/ERF/hak
  - `install` - Pack and install to KOTOR directory
  - `launch` - Install and launch game (with aliases: serve, play, test)
- TOML-based configuration file (KotorCLI.cfg)
- Variable expansion support
- Target inheritance
- Source filtering and rules
- Git integration
- Colored terminal output
- Comprehensive documentation

### Features
- Compatible with cli's command syntax
- Built on PyKotor's high-performance libraries
- Cross-platform support (Windows, Linux, macOS)
- Flexible source tree organization
- JSON-based source format for version control
- Script compilation using nwnnsscomp
- Multiple target support
- Group-based target building

[1.0.0]: https://github.com/th3w1zard1/PyKotor/releases/tag/KotorCLI-v1.0.0



