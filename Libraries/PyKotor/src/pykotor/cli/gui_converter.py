"""GUI converter logic shared between CLI and optional Tk GUI.

The implementation mirrors the behaviors documented in ``wiki/GFF-GUI.md`` and
the reference implementation in `` GUIs are authored
for a 640x480 base resolution and scaled to other resolutions by transforming
every control that owns an ``EXTENT`` struct (including nested controls and
embedded scrollbar/protoitem structs).
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

from loggerplus import RobustLogger
from pykotor.resource.formats.gff import GFF, GFFContent, read_gff, write_gff
from pykotor.resource.formats.gff.gff_data import GFFList, GFFStruct
from pykotor.tools.path import CaseAwarePath

ASPECT_RATIO_TO_RESOLUTION: dict[str, list[tuple[int, int]]] = {
    "16:9": [
        (3840, 2160),
        (2560, 1440),
        (1920, 1080),
        (1600, 900),
        (1366, 768),
        (1280, 720),
        (1024, 576),
        (960, 540),
        (854, 480),
        (640, 360),
    ],
    "16:10": [
        (2560, 1600),
        (1920, 1200),
        (1680, 1050),
        (1440, 900),
        (1280, 800),
        (1152, 720),
        (1024, 640),
        (768, 480),
        (640, 400),
        (512, 320),
    ],
    "4:3": [
        (1600, 1200),
        (1400, 1050),
        (1280, 960),
        (1152, 864),
        (1024, 768),
        (800, 600),
        (640, 480),
        (512, 384),
        (400, 300),
        (320, 240),
    ],
    "5:4": [
        (1280, 1024),
        (2560, 2048),
        (512, 409),
        (1024, 819),
        (640, 512),
        (320, 256),
        (256, 205),
        (128, 102),
    ],
    "21:9": [
        (5120, 2160),
        (3440, 1440),
        (2560, 1080),
        (1920, 810),
        (1680, 720),
        (1440, 612),
        (1280, 548),
        (1080, 460),
        (960, 408),
        (640, 272),
    ],
    "3:2": [
        (2160, 1440),
        (1920, 1280),
        (1440, 960),
        (1368, 912),
        (1280, 854),
        (1152, 768),
        (1080, 720),
        (1024, 682),
        (960, 640),
        (720, 480),
    ],
    "1:1": [
        (1024, 1024),
        (960, 960),
        (720, 720),
        (640, 640),
        (512, 512),
        (480, 480),
        (320, 320),
        (240, 240),
        (160, 160),
        (128, 128),
    ],
}

BASE_GUI_WIDTH = 640
BASE_GUI_HEIGHT = 480


@dataclass(frozen=True)
class ResolutionTarget:
    """Normalized resolution target."""

    width: int
    height: int

    @property
    def label(self) -> str:
        return f"{self.width}x{self.height}"

    def scale_factors(self, source_width: int, source_height: int) -> tuple[float, float]:
        if source_width <= 0 or source_height <= 0:
            msg = "Source GUI width and height must be positive for scaling."
            raise ValueError(msg)
        return self.width / source_width, self.height / source_height


def _scale_extent(extent: GFFStruct, height_scale: float, width_scale: float) -> None:
    """Scale an EXTENT struct in place."""
    extent.set_int32("TOP", int(extent.get_int32("TOP") * height_scale))
    extent.set_int32("HEIGHT", int(extent.get_int32("HEIGHT") * height_scale))
    extent.set_int32("LEFT", int(extent.get_int32("LEFT") * width_scale))
    extent.set_int32("WIDTH", int(extent.get_int32("WIDTH") * width_scale))


def _iter_structs_with_extent(control_struct: GFFStruct) -> Iterable[GFFStruct]:
    """Yield every struct that owns an EXTENT, mirroring editor tree traversal."""
    if control_struct.exists("EXTENT"):
        yield control_struct

    for field_name in ("SCROLLBAR", "PROTOITEM"):
        if control_struct.exists(field_name):
            nested = control_struct.get_struct(field_name)
            if nested is not None:
                yield from _iter_structs_with_extent(nested)

    controls_list: GFFList | None = control_struct.get_list("CONTROLS")
    if controls_list:
        for child_struct in controls_list:
            yield from _iter_structs_with_extent(child_struct)


def _scale_gui(gui_data: GFF, target: ResolutionTarget) -> GFF:
    """Return a scaled copy of the GUI for the requested resolution."""
    new_gff = GFF(GFFContent.GUI)
    new_gff.root = deepcopy(gui_data.root)

    root_extent_struct = new_gff.root.get_struct("EXTENT")
    if root_extent_struct is None:
        msg = "GUI root missing EXTENT struct; cannot scale."
        raise ValueError(msg)
    source_width = root_extent_struct.get_int32("WIDTH") or BASE_GUI_WIDTH
    source_height = root_extent_struct.get_int32("HEIGHT") or BASE_GUI_HEIGHT

    width_scale_factor, height_scale_factor = target.scale_factors(source_width, source_height)
    root_extent_struct.set_int32("WIDTH", target.width)
    root_extent_struct.set_int32("HEIGHT", target.height)

    controls_list: GFFList | None = new_gff.root.get_list("CONTROLS")
    if controls_list:
        for control_struct in controls_list:
            for struct in _iter_structs_with_extent(control_struct):
                extent = struct.get_struct("EXTENT")
                if extent is not None:
                    _scale_extent(extent, height_scale_factor, width_scale_factor)

    return new_gff


def _unique_targets(targets: Iterable[ResolutionTarget]) -> list[ResolutionTarget]:
    seen: set[tuple[int, int]] = set()
    ordered: list[ResolutionTarget] = []
    for target in targets:
        key = (target.width, target.height)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(target)
    return sorted(ordered, key=lambda item: (item.width, item.height))


def _parse_resolution_spec(resolution: str) -> list[ResolutionTarget]:
    """Parse a resolution spec string into unique targets."""
    spec = resolution.strip().lower()
    if not spec:
        msg = "Resolution is required."
        raise ValueError(msg)

    parts = [spec_part.strip() for spec_part in spec.split(",") if spec_part.strip()]
    if not parts:
        msg = "No valid resolutions provided."
        raise ValueError(msg)

    parsed: list[ResolutionTarget] = []
    for item in parts:
        if item == "all":
            for values in ASPECT_RATIO_TO_RESOLUTION.values():
                parsed.extend(ResolutionTarget(width, height) for width, height in values)
            continue

        if item in ASPECT_RATIO_TO_RESOLUTION:
            parsed.extend(ResolutionTarget(width, height) for width, height in ASPECT_RATIO_TO_RESOLUTION[item])
            continue

        try:
            width_text, height_text = item.lower().split("x")
            width = int(width_text)
            height = int(height_text)
        except Exception as exc:
            msg = f"Invalid resolution format '{item}'. Use WIDTHxHEIGHT, ALL, or a known aspect ratio key."
            raise ValueError(msg) from exc

        if width <= 0 or height <= 0:
            msg = f"Resolution must be positive: {item}"
            raise ValueError(msg)
        parsed.append(ResolutionTarget(width, height))

    return _unique_targets(parsed)


def _gather_gui_inputs(inputs: Sequence[Path], warn: Callable[[str], None]) -> list[tuple[CaseAwarePath, Path]]:
    """Expand user inputs to concrete GUI files with their relative output roots."""
    gathered: list[tuple[CaseAwarePath, Path]] = []
    for raw in inputs:
        case_path = CaseAwarePath(raw)
        if case_path.is_file():
            if case_path.suffix.lower() != ".gui":
                warn(f"Skipping non-GUI file: {case_path}")
                continue
            gathered.append((case_path, Path()))
            continue

        if case_path.is_dir():
            files = list(case_path.rglob("*.gui"))
            if not files:
                warn(f"No .gui files found under {case_path}")
                continue
            for gui_file in files:
                relative_dir = gui_file.parent.relative_to(case_path)
                gathered.append((CaseAwarePath(gui_file), relative_dir))
            continue

        warn(f"Invalid input path (skipped): {case_path}")
    return gathered


def convert_gui_inputs(
    inputs: Sequence[Path],
    output: Path,
    resolution: str,
    logger: RobustLogger | None = None,
) -> int:
    """Convert GUI files for the requested resolutions.

    Returns 0 on success, 1 on error.
    """
    log = logger.info if logger else print
    warn = logger.warning if logger else print
    err = logger.error if logger else print

    try:
        resolution_targets = _parse_resolution_spec(resolution)
    except Exception as exc:
        err(f"{exc.__class__.__name__}: {exc}")
        return 1

    case_output = CaseAwarePath(output)
    case_output.mkdir(parents=True, exist_ok=True)

    gathered = _gather_gui_inputs(inputs, warn)
    if not gathered:
        warn("No GUI files discovered from provided inputs.")
        return 1

    total_processed = 0
    for gui_file, relative_dir in gathered:
        log(f"Processing GUI file: '{gui_file}'")
        try:
            gui_data = read_gff(gui_file)
        except Exception as exc:
            err(f"Failed to read '{gui_file}': {exc}")
            continue

        for target in resolution_targets:
            try:
                adjusted = _scale_gui(gui_data, target)
            except Exception as exc:
                err(f"Failed to scale '{gui_file}' to {target.label}: {exc}")
                continue

            dest = case_output / target.label / relative_dir / gui_file.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                write_gff(adjusted, dest)
                log(f"Wrote GUI for {target.label} -> {dest}")
            except Exception as exc:
                err(f"Failed to write '{dest}': {exc}")
                continue
        total_processed += 1

    if total_processed == 0:
        warn("No GUI files processed.")
    else:
        log(f"Processed {total_processed} GUI files.")
    return 0


def launch_gui_converter() -> None:  # noqa: PLR0915
    """Open a minimal Tk GUI for interactive conversions."""
    import tkinter as tk  # noqa: PLC0415  # imported lazily to avoid headless dependency
    from tkinter import filedialog, messagebox, scrolledtext  # noqa: PLC0415

    root = tk.Tk()
    root.title("KotorCLI GUI Converter")
    root.geometry("640x400")

    logger = RobustLogger()

    def append_log(message: str) -> None:
        text.configure(state=tk.NORMAL)
        text.insert(tk.END, message + "\n")
        text.see(tk.END)
        text.configure(state=tk.DISABLED)

    def browse_input() -> None:
        path = filedialog.askdirectory(title="Select GUI folder")
        if path:
            input_var.set(path)

    def browse_output() -> None:
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            output_var.set(path)

    def run_conversion() -> None:
        input_path = input_var.get().strip()
        output_path = output_var.get().strip()
        resolution_spec = resolution_var.get().strip() or "ALL"
        if not input_path or not output_path:
            messagebox.showerror("Missing paths", "Input and output paths are required.")
            return
        try:
            exit_code = convert_gui_inputs([Path(input_path)], Path(output_path), resolution_spec, logger)
        except Exception as exc:
            messagebox.showerror("Conversion failed", f"{exc.__class__.__name__}: {exc}")
            return
        if exit_code == 0:
            messagebox.showinfo("Done", "GUI conversion completed.")
        else:
            messagebox.showwarning("Finished with warnings", "Conversion completed with warnings or no files.")

    # Layout
    frm = tk.Frame(root, padx=8, pady=8)
    frm.pack(fill=tk.BOTH, expand=True)

    tk.Label(frm, text="Input folder/file:").grid(row=0, column=0, sticky="w")
    input_var = tk.StringVar()
    tk.Entry(frm, textvariable=input_var).grid(row=0, column=1, sticky="ew", padx=4)
    tk.Button(frm, text="Browse", command=browse_input).grid(row=0, column=2)

    tk.Label(frm, text="Output folder:").grid(row=1, column=0, sticky="w")
    output_var = tk.StringVar()
    tk.Entry(frm, textvariable=output_var).grid(row=1, column=1, sticky="ew", padx=4)
    tk.Button(frm, text="Browse", command=browse_output).grid(row=1, column=2)

    tk.Label(frm, text="Resolution (WIDTHxHEIGHT or ALL):").grid(row=2, column=0, sticky="w")
    resolution_var = tk.StringVar(value="ALL")
    tk.Entry(frm, textvariable=resolution_var).grid(row=2, column=1, sticky="ew", padx=4)

    frm.grid_columnconfigure(1, weight=1)

    tk.Button(frm, text="Convert", command=run_conversion).grid(row=3, column=2, pady=6, sticky="e")

    text = scrolledtext.ScrolledText(frm, height=12, state=tk.DISABLED)
    text.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
    frm.grid_rowconfigure(4, weight=1)

    root.mainloop()
