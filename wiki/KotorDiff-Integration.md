# KotorDiff Integration in KotorCLI

The standalone KotorDiff tool now ships inside KotorCLI and follows the same headless-first pattern as other Holocron utilities.

## Behavior

- Supplying any diff paths keeps execution headless; omitting paths or passing `--gui` launches the Tkinter UI (`Tools/KotorCLI/src/kotorcli/diff_tool/__main__.py` L20-L120).
- CLI arguments [ARE](GFF-File-Format#are-area) shared between the dedicated scripts (`kotordiff`, `kotor-diff`, `diff-installation`) and the `kotorcli diff-installation` subcommand (`Tools/KotorCLI/src/kotorcli/diff_tool/cli.py` L26-L147).
- Headless execution builds a `KotorDiffConfig` and routes to the n-way differ (`Tools/KotorCLI/src/kotorcli/diff_tool/cli.py` L168-L238).

## CLI Usage

```bash
# Installation vs installation with filtering
python -m kotorcli diff-installation --path1 "C:\Games\KOTOR" --path2 "C:\Games\KOTOR_Modded" --filter tat_m17ac --output-mode diff_only

# Generate incremental TSLPatcher output while diffing
python -m kotorcli diff-installation --path1 "C:\Games\KOTOR" --path2 "C:\Games\KOTOR_Modded" --tslpatchdata .\tslpatchdata --ini changes.ini --incremental

# GUI fallback (no args or explicit flag)
kotordiff
# or
python -m kotorcli diff-installation --gui
```

[KEY](KEY-File-Format) [flags](GFF-File-Format#gff-data-types):

- `--path1/--path2/--path3/--path` for multi-path comparisons
- `--filter` to constrain resources/modules
- `--output-mode` (`full`, `diff_only`, `quiet`) + `--output-log`
- `--tslpatchdata` / `--ini` with optional `--incremental` writer
- `--compare-hashes/--no-compare-hashes`, `--log-level`, `--no-color`, `--use-profiler`, `--gui`

## Implementation Notes

- Diff orchestration, filtering, and incremental TSLPatcher generation live in `Tools/KotorCLI/src/kotorcli/diff_tool/app.py` L40-L530. Incremental writer creation and [StrRef](TLK-File-Format#string-references-strref) analysis [ARE](GFF-File-Format#are-area) handled in `handle_diff` and `generate_tslpatcher_data` (L295-L529).
- CLI argument wiring and headless execution [ARE](GFF-File-Format#are-area) defined in `Tools/KotorCLI/src/kotorcli/diff_tool/cli.py` L26-L238.
- [GUI](GFF-File-Format#gui-graphical-user-interface) fallback is implemented in `Tools/KotorCLI/src/kotorcli/diff_tool/gui.py` (headless when arguments [ARE](GFF-File-Format#are-area) present, UI when omitted).
