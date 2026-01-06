#!/usr/bin/env python
"""
All-in-one MDL/MDX debugging CLI.

Goal: replace the grab-bag of scripts in `scripts/kotor/model/` with a single, configurable tool
that can reproduce (close enough) the same investigations, while adding higher-signal outputs:
- first-mismatch context
- unified diffs of hexdumps
- diff ranges + section attribution (what bytes correspond to what logical section)
- parsed/semantic diffs (nodes/meshes/MDX rows)

This script is intentionally verbose *when asked* (via flags), but defaults to concise summaries.
"""

from __future__ import annotations

import argparse
import dataclasses
import difflib
import json
import os
import subprocess
import sys
import tempfile

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Literal, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
PYKOTOR_SRC = REPO_ROOT / "Libraries" / "PyKotor" / "src"
if str(PYKOTOR_SRC) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_SRC))

from pykotor.common.misc import Game  # noqa: E402
from pykotor.common.stream import BinaryReader  # noqa: E402
from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.resource.formats.mdl import read_mdl, write_mdl  # noqa: E402
from pykotor.resource.formats.mdl.io_mdl import (  # noqa: E402
    MDLBinaryReader,
    _MDXDataFlags,
    _ModelHeader,
    _NodeHeader,
    _TrimeshHeader,
)
from pykotor.resource.formats.mdl.mdl_types import MDLNodeFlags  # noqa: E402
from pykotor.resource.type import ResourceType  # noqa: E402
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default  # noqa: E402

OutputFormat = Literal["text", "json", "compact"]
SourceKind = Literal["original", "pykotor", "mdlops"]


@dataclass(frozen=True)
class ModelBytes:
    mdl: bytes
    mdx: bytes
    label: str


@dataclass(frozen=True)
class DiffRange:
    start: int
    end: int  # inclusive

    @property
    def length(self) -> int:
        return self.end - self.start + 1


@dataclass(frozen=True)
class Segment:
    start: int
    end: int  # exclusive
    label: str
    details: dict[str, str]

    def overlaps(self, dr: DiffRange) -> bool:
        # Segment is [start, end), DiffRange is [start, end]
        return not (dr.end < self.start or (dr.start >= self.end))


def _err(msg: str) -> str:
    return f"ERROR: {msg}"


def _human_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KiB"
    return f"{n / (1024 * 1024):.1f} MiB"


def _resolve_game(game: str) -> Game:
    g = game.strip().lower()
    if g in ("k1", "1", "swkotor"):
        return Game.K1
    if g in ("k2", "2", "tsl"):
        return Game.K2
    raise ValueError(f"Unknown game '{game}', expected k1 or k2")


def _default_install_path(game: Game) -> Path | None:
    # Prefer env vars (repo rule)
    if game == Game.K1:
        env = os.environ.get("K1_PATH")
        if env:
            p = Path(env)
            return p if p.exists() else None
    else:
        env = os.environ.get("K2_PATH") or os.environ.get("TSL_PATH")
        if env:
            p = Path(env)
            return p if p.exists() else None

    # Fall back to helper
    try:
        paths: dict[Game, list[CaseAwarePath]] = find_kotor_paths_from_default()
    except Exception:
        return None
    game_paths = paths.get(game, [])
    return Path(str(game_paths[0])) if game_paths else None


def _load_from_installation(*, game: Game, install_path: Path, resref: str) -> ModelBytes:
    inst = Installation(install_path)
    mdl_res = inst.resource(resref, ResourceType.MDL)
    if mdl_res is None:
        raise FileNotFoundError(f"MDL resource '{resref}' not found in installation at {install_path}")
    mdx_res = inst.resource(resref, ResourceType.MDX)
    mdx_bytes = mdx_res.data if mdx_res is not None else b""
    return ModelBytes(mdl=mdl_res.data, mdx=mdx_bytes, label=f"{resref} (installation)")


def _load_from_files(*, mdl_path: Path, mdx_path: Path | None) -> ModelBytes:
    mdl = mdl_path.read_bytes()
    mdx = mdx_path.read_bytes() if mdx_path and mdx_path.exists() else b""
    label = mdl_path.name
    return ModelBytes(mdl=mdl, mdx=mdx, label=label)


def _pykotor_roundtrip(original: ModelBytes) -> ModelBytes:
    mdl_obj = read_mdl(original.mdl, source_ext=(original.mdx or None), file_format=ResourceType.MDL)
    mdl_out = BytesIO()
    mdx_out = BytesIO()
    write_mdl(mdl_obj, mdl_out, ResourceType.MDL, target_ext=mdx_out)
    return ModelBytes(mdl=mdl_out.getvalue(), mdx=mdx_out.getvalue(), label="pykotor-roundtrip")


def _find_mdlops_exe(explicit: Path | None) -> Path:
    if explicit is not None:
        if explicit.exists():
            return explicit
        raise FileNotFoundError(f"MDLOps exe not found at {explicit}")
    candidate = REPO_ROOT / "vendor" / "MDLOps" / "mdlops.exe"
    if candidate.exists():
        return candidate
    raise FileNotFoundError("MDLOps exe not found (expected vendor/MDLOps/mdlops.exe). Use --mdlops-exe.")


def _run_mdlops_roundtrip(
    *,
    original: ModelBytes,
    mdlops_exe: Path,
    game: Game,
    timeout_s: int,
    keep_dir: Path | None,
    resref: str,
) -> tuple[ModelBytes, Path]:
    # Write to tempdir so MDLOps can produce ascii + bin
    if keep_dir is not None:
        keep_dir.mkdir(parents=True, exist_ok=True)
        td_cm = None
        td_path = keep_dir
    else:
        td_cm = tempfile.TemporaryDirectory(prefix="mdl_aio_mdlops_")
        td_path = Path(td_cm.name)

    try:
        orig_mdl_path = td_path / f"{resref}.mdl"
        orig_mdx_path = td_path / f"{resref}.mdx"
        orig_mdl_path.write_bytes(original.mdl)
        if original.mdx:
            orig_mdx_path.write_bytes(original.mdx)

        # Decompile (reads only MDL path; expects MDX sibling if needed)
        dec = subprocess.run(
            [str(mdlops_exe), str(orig_mdl_path)],
            cwd=str(td_path),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        ascii_path = td_path / f"{resref}-ascii.mdl"
        if dec.returncode != 0 or not ascii_path.exists():
            raise RuntimeError(f"MDLOps decompile failed (rc={dec.returncode}): {dec.stderr.strip() or dec.stdout.strip()}")

        # Compile
        args = [str(mdlops_exe), str(ascii_path), "-k1" if game == Game.K1 else "-k2"]
        comp = subprocess.run(
            args,
            cwd=str(td_path),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        suffix = "k1" if game == Game.K1 else "k2"
        out_mdl = td_path / f"{resref}-ascii-{suffix}-bin.mdl"
        out_mdx = td_path / f"{resref}-ascii-{suffix}-bin.mdx"
        if comp.returncode != 0 or not out_mdl.exists():
            files = sorted(p.name for p in td_path.iterdir())
            raise RuntimeError(
                f"MDLOps compile failed or did not produce expected outputs. (rc={comp.returncode}) files={files} stderr={comp.stderr.strip() or comp.stdout.strip()}"
            )

        return ModelBytes(mdl=out_mdl.read_bytes(), mdx=(out_mdx.read_bytes() if out_mdx.exists() else b""), label="mdlops-roundtrip"), td_path
    finally:
        if td_cm is not None:
            td_cm.cleanup()


def diff_ranges(a: bytes, b: bytes) -> tuple[list[DiffRange], int | None]:
    min_len = min(len(a), len(b))
    ranges: list[DiffRange] = []
    start: int | None = None
    first: int | None = None
    for i in range(min_len):
        if a[i] != b[i]:
            if first is None:
                first = i
            if start is None:
                start = i
        else:
            if start is not None:
                ranges.append(DiffRange(start=start, end=i - 1))
                start = None
    if start is not None:
        ranges.append(DiffRange(start=start, end=min_len - 1))
    # handle trailing bytes if sizes differ
    if len(a) != len(b):
        tail_start = min_len
        tail_end = max(len(a), len(b)) - 1
        ranges.append(DiffRange(start=tail_start, end=tail_end))
        if first is None:
            first = tail_start
    return ranges, first


def hexdump_lines(data: bytes, *, width: int = 16, base: int = 0) -> list[str]:
    lines: list[str] = []
    for off in range(0, len(data), width):
        chunk = data[off : off + width]
        hex_str = " ".join(f"{b:02X}" for b in chunk)
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{base + off:08X}  {hex_str:<{width * 3 - 1}}  |{ascii_str}|")
    return lines


def unified_hexdiff(
    a: bytes,
    b: bytes,
    *,
    a_label: str,
    b_label: str,
    context_lines: int,
    max_lines: int,
    width: int = 16,
) -> list[str]:
    # create compact hexdump lists; difflib works on lines
    a_lines = hexdump_lines(a, width=width)
    b_lines = hexdump_lines(b, width=width)

    # If huge, restrict to a window around first mismatch
    ranges, first = diff_ranges(a, b)
    if first is not None and (len(a_lines) + len(b_lines)) > max_lines * 4:
        first_line = first // width
        lo = max(0, first_line - context_lines)
        hi = min(max(len(a_lines), len(b_lines)), first_line + context_lines + 1)
        a_lines = a_lines[lo:hi]
        b_lines = b_lines[lo:hi]
        a_label = f"{a_label} (window @{lo * width:08X})"
        b_label = f"{b_label} (window @{lo * width:08X})"

    diff = list(
        difflib.unified_diff(
            a_lines,
            b_lines,
            fromfile=a_label,
            tofile=b_label,
            lineterm="",
            n=context_lines,
        )
    )
    if len(diff) > max_lines:
        return diff[:max_lines] + [f"... truncated unified diff (max_lines={max_lines}) ..."]
    return diff


def first_mismatch_context(a: bytes, b: bytes, *, around: int = 64) -> dict[str, object]:
    _, first = diff_ranges(a, b)
    if first is None:
        return {"first_mismatch": None}
    lo = max(0, first - around)
    hi = min(max(len(a), len(b)), first + around)
    return {
        "first_mismatch": first,
        "a_len": len(a),
        "b_len": len(b),
        "window_start": lo,
        "window_end": hi,
        "a_hex": a[lo : min(hi, len(a))].hex(),
        "b_hex": b[lo : min(hi, len(b))].hex(),
    }


def _compute_expected_row_size(bitmap: int, is_skin: bool = False) -> int:
    """Compute the expected MDX row size based on the bitmap.

    MDLOps writes MDX rows with this layout (each field present if bitmap flag is set):
    - VERTEX (0x01): 3 floats (12 bytes) at offset 0
    - NORMAL (0x20): 3 floats (12 bytes)
    - TEX0 (0x02): 2 floats (8 bytes)
    - TEX1 (0x04): 2 floats (8 bytes)
    - TEX2 (0x08): 2 floats (8 bytes)
    - TEX3 (0x10): 2 floats (8 bytes)
    - TANGENT_SPACE (0x80): 12 bytes (3 floats for tangent + 3 floats for binormal) or 24 bytes

    For skins, also:
    - 4 bone weights (16 bytes)
    - 4 bone indices (as floats, 16 bytes)

    Reference: vendor/MDLOps/MDLOpsM.pm (MDX writing loop)
    """
    size = 0
    if bitmap & _MDXDataFlags.VERTEX:
        size += 12  # 3 floats
    if bitmap & _MDXDataFlags.NORMAL:
        size += 12  # 3 floats
    if bitmap & _MDXDataFlags.TEX0:
        size += 8  # 2 floats
    if bitmap & _MDXDataFlags.TEX1:
        size += 8  # 2 floats
    if bitmap & 0x08:  # TEX2
        size += 8
    if bitmap & 0x10:  # TEX3
        size += 8
    if bitmap & _MDXDataFlags.TANGENT_SPACE:
        size += 24  # 6 floats (tangent.xyz + binormal.xyz)
    if is_skin:
        size += 32  # 4 bone weights + 4 bone indices
    return size


def _parse_nodes_for_mdx_rows(mdl: bytes, mdx: bytes, game: Game) -> list[dict[str, object]]:
    """
    Capture per-mesh MDX row metadata (bitmap/offsets/stride) from binary headers.

    This intentionally reads *binary header fields* rather than relying on `MDLMesh` fields,
    because the semantic object model does not expose the MDX bitmap/row offsets directly.
    """
    reader = BinaryReader.from_auto(mdl, 0)
    reader.set_offset(reader.offset() + 12)
    header = _ModelHeader().read(reader)

    root_off = int(header.geometry.root_node_offset)
    seen: set[int] = set()
    out: list[dict[str, object]] = []

    def walk(node_off: int) -> None:
        if node_off in seen:
            return
        seen.add(node_off)

        reader.seek(node_off)
        hdr = _NodeHeader().read(reader)

        is_mesh = bool(hdr.type_id & MDLNodeFlags.MESH)
        info: dict[str, object] = {
            "node_offset": node_off,
            "node_id": int(hdr.node_id),
            "type_id": int(hdr.type_id),
            "is_mesh": is_mesh,
            "offset_to_children": int(hdr.offset_to_children),
            "children_count": int(hdr.children_count),
        }

        tri: _TrimeshHeader | None = None
        if is_mesh:
            tri = _TrimeshHeader().read(reader, game)
            info.update(
                {
                    "vertex_count": int(tri.vertex_count),
                    "mdx_data_offset": int(tri.mdx_data_offset),
                    "mdx_data_size": int(tri.mdx_data_size),
                    "mdx_data_bitmap": int(tri.mdx_data_bitmap),
                    "mdx_vertex_offset": int(tri.mdx_vertex_offset),
                    "mdx_normal_offset": int(tri.mdx_normal_offset),
                    "mdx_tex0_offset": int(tri.mdx_texture1_offset),
                    "mdx_tex1_offset": int(tri.mdx_texture2_offset),
                    "mdx_tangent_offset": int(tri.mdx_tangent_offset),
                    "vertices_offset_mdl": int(tri.vertices_offset),
                    "texture1": tri.texture1,
                    "texture2": tri.texture2,
                }
            )
            out.append(info)

        # Traverse children via child offsets array
        if hdr.offset_to_children not in (0, 0xFFFFFFFF) and hdr.children_count > 0:
            reader.seek(int(hdr.offset_to_children))
            children = [reader.read_uint32() for _ in range(int(hdr.children_count))]
            for child_off in children:
                if child_off not in (0, 0xFFFFFFFF):
                    walk(int(child_off))

    walk(root_off)
    return out


def _layout_segments_from_reader(mdl: bytes, game: Game) -> list[Segment]:
    """
    Produce a *best-effort* labeled layout map of the MDL file using the binary reader's internal headers.
    This is for attributing diff ranges to logical sections, not for correctness-critical parsing.
    """
    rdr = MDLBinaryReader(mdl, source_ext=None)
    rdr.game = game
    _ = rdr.load()

    segs: list[Segment] = []
    # Always include the 12-byte wrapper header
    segs.append(Segment(0, 12, "file_header", {}))
    # Names header area is inside model header, but we treat model header as a segment.
    # We don't have direct access to _file_header here without importing internals; keep coarse.
    segs.append(Segment(12, 12 + 196, "model_header", {}))

    # Approximate: names offsets start at 12 + 196? In practice, offset_to_name_offsets is inside header;
    # for robust segment labeling we only label per-node structures with offsets we can trust.
    # We'll parse raw node offsets from the geometry header (byte-level).
    import struct

    if len(mdl) < 12 + 60:
        return segs
    root_node_offset = struct.unpack_from("<I", mdl, 12 + 40)[0] + 12
    node_count = struct.unpack_from("<I", mdl, 12 + 44)[0]
    segs.append(Segment(root_node_offset, len(mdl), "node_block (approx)", {"node_count": str(node_count)}))
    return segs


@dataclass(frozen=True)
class CapturedMeshNode:
    node_offset: int  # MDL-relative (reader offset applied, i.e. NOT including outer +12)
    node_id: int
    type_id: int
    offset_to_children: int
    children_count: int
    offset_to_controllers: int
    controller_count: int
    offset_to_controller_data: int
    controller_data_length: int
    # Trimesh
    vertex_count: int
    vertices_offset: int
    faces_count: int
    offset_to_faces: int
    indices_counts_count: int
    offset_to_indices_counts: int
    indices_offsets_count: int
    offset_to_indices_offsets: int
    counters_count: int
    offset_to_counters: int
    # MDX
    mdx_data_offset: int
    mdx_data_size: int
    mdx_data_bitmap: int
    mdx_vertex_offset: int
    mdx_normal_offset: int
    mdx_color_offset: int
    mdx_tex0_offset: int
    mdx_tex1_offset: int
    mdx_tangent_offset: int
    texture1: str
    texture2: str


def _capture_mesh_nodes(mdl: bytes, *, game: Game) -> list[CapturedMeshNode]:
    """
    Walk the node tree using raw binary offsets and capture key header fields for every mesh node.
    Offsets returned are MDL-relative (i.e. the same units used inside the MDL after the 12-byte wrapper).

    Uses proper tree traversal via child pointers for accurate node discovery.
    """
    reader = BinaryReader.from_auto(mdl, 0)
    reader.set_offset(reader.offset() + 12)

    try:
        header = _ModelHeader().read(reader)
    except Exception:
        return []

    file_size = len(mdl)
    out_by_node_id: dict[int, CapturedMeshNode] = {}
    seen_offsets: set[int] = set()

    def walk(offset: int) -> None:
        # Sanity checks
        if offset in seen_offsets:
            return
        if offset == 0 or offset >= file_size:
            return
        seen_offsets.add(offset)

        try:
            reader.seek(offset)
            hdr = _NodeHeader().read(reader)
        except Exception:
            return

        # Plausibility checks
        if hdr.node_id > 5000:
            return
        if hdr.children_count > 500:
            return

        # If it's a mesh node, capture the trimesh header
        if hdr.type_id & MDLNodeFlags.MESH:
            try:
                tri = _TrimeshHeader().read(reader, game)
                # Validate trimesh data
                if tri.vertex_count < 500000 and tri.faces_count < 500000:
                    node_id = int(hdr.node_id)
                    if node_id not in out_by_node_id:
                        out_by_node_id[node_id] = CapturedMeshNode(
                            node_offset=offset,
                            node_id=node_id,
                            type_id=int(hdr.type_id),
                            offset_to_children=int(hdr.offset_to_children),
                            children_count=int(hdr.children_count),
                            offset_to_controllers=int(hdr.offset_to_controllers),
                            controller_count=int(hdr.controller_count),
                            offset_to_controller_data=int(hdr.offset_to_controller_data),
                            controller_data_length=int(hdr.controller_data_length),
                            vertex_count=int(tri.vertex_count),
                            vertices_offset=int(tri.vertices_offset),
                            faces_count=int(tri.faces_count),
                            offset_to_faces=int(tri.offset_to_faces),
                            indices_counts_count=int(tri.indices_counts_count),
                            offset_to_indices_counts=int(tri.offset_to_indices_counts),
                            indices_offsets_count=int(tri.indices_offsets_count),
                            offset_to_indices_offsets=int(tri.offset_to_indices_offset),
                            counters_count=int(tri.counters_count),
                            offset_to_counters=int(tri.offset_to_counters),
                            mdx_data_offset=int(tri.mdx_data_offset),
                            mdx_data_size=int(tri.mdx_data_size),
                            mdx_data_bitmap=int(tri.mdx_data_bitmap),
                            mdx_vertex_offset=int(tri.mdx_vertex_offset),
                            mdx_normal_offset=int(tri.mdx_normal_offset),
                            mdx_color_offset=int(tri.mdx_color_offset),
                            mdx_tex0_offset=int(tri.mdx_texture1_offset),
                            mdx_tex1_offset=int(tri.mdx_texture2_offset),
                            mdx_tangent_offset=int(tri.mdx_tangent_offset),
                            texture1=tri.texture1,
                            texture2=tri.texture2,
                        )
            except Exception:
                pass

        # Walk children
        if hdr.children_count > 0 and 0 < hdr.offset_to_children < file_size:
            try:
                reader.seek(hdr.offset_to_children)
                for _ in range(hdr.children_count):
                    child_off = reader.read_uint32()
                    if 0 < child_off < file_size:
                        walk(child_off)
            except Exception:
                pass

    walk(header.geometry.root_node_offset)
    return [out_by_node_id[k] for k in sorted(out_by_node_id)]


def _segments_for_mdl(mdl: bytes, *, game: Game) -> list[Segment]:
    """
    Build labeled segments for the MDL file, using binary offsets from mesh node headers.
    This is designed for diff attribution (what bytes correspond to what logical section).
    """
    segs: list[Segment] = [Segment(0, 12, "file_header", {}), Segment(12, 12 + 196, "model_header", {})]
    nodes = _capture_mesh_nodes(mdl, game=game)

    def add_if_valid(start_rel: int, size: int, label: str, details: dict[str, str]) -> None:
        if start_rel in (0, 0xFFFFFFFF) or size <= 0:
            return
        start = start_rel + 12
        end = start + size
        if start < 0 or end < 0 or start > len(mdl) or end > len(mdl):
            return
        segs.append(Segment(start, end, label, details))

    for n in nodes:
        prefix = f"node[{n.node_id}]"
        details = {"node_id": str(n.node_id), "type_id": f"0x{n.type_id:04X}", "tex1": n.texture1}

        # Faces / vertices / index tables
        add_if_valid(n.offset_to_faces, n.faces_count * 32, f"{prefix}.faces", details)
        add_if_valid(n.vertices_offset, n.vertex_count * 12, f"{prefix}.vertices_mdl", details)
        add_if_valid(n.offset_to_indices_counts, n.indices_counts_count * 4, f"{prefix}.indices_counts", details)
        add_if_valid(n.offset_to_indices_offsets, n.indices_offsets_count * 4, f"{prefix}.indices_offsets", details)
        add_if_valid(n.offset_to_counters, n.counters_count * 4, f"{prefix}.inverted_counters", details)

        # Children offsets / controllers / controller data
        add_if_valid(n.offset_to_children, n.children_count * 4, f"{prefix}.children_offsets", details)
        add_if_valid(n.offset_to_controllers, n.controller_count * 16, f"{prefix}.controllers", details)
        add_if_valid(n.offset_to_controller_data, n.controller_data_length, f"{prefix}.controller_data", details)

    # Stable order helps readability
    segs.sort(key=lambda s: (s.start, s.end, s.label))
    return segs


def _attribute_ranges_to_segments(ranges: list[DiffRange], segments: list[Segment], *, max_hits: int) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    for dr in ranges:
        overlapped = [s for s in segments if s.overlaps(dr)]
        for s in overlapped:
            overlap_start = max(dr.start, s.start)
            overlap_end = min(dr.end + 1, s.end)
            if overlap_end > overlap_start:
                hits.append(
                    {
                        "diff_start": dr.start,
                        "diff_end": dr.end,
                        "diff_len": dr.length,
                        "segment": s.label,
                        "segment_start": s.start,
                        "segment_end": s.end,
                        "overlap_bytes": overlap_end - overlap_start,
                        "details": s.details,
                    }
                )
    hits.sort(key=lambda h: int(h["overlap_bytes"]), reverse=True)
    return hits[:max_hits]


def _hexdiff_windows_for_top_ranges(
    a: bytes,
    b: bytes,
    *,
    a_label: str,
    b_label: str,
    ranges: list[DiffRange],
    width: int,
    context_lines: int,
    windows: int,
    max_lines: int,
) -> list[list[str]]:
    # choose the largest ranges (most informative), plus always include the first mismatch
    if not ranges:
        return []
    ordered = sorted(ranges, key=lambda r: r.length, reverse=True)
    top = ordered[:windows]
    out: list[list[str]] = []
    for dr in top:
        # compute a line-window around range start
        start_line = dr.start // width
        lo = max(0, start_line - context_lines)
        hi = start_line + context_lines + 1
        a_lines = hexdump_lines(a, width=width)
        b_lines = hexdump_lines(b, width=width)
        a_slice = a_lines[lo:hi]
        b_slice = b_lines[lo:hi]
        out.append(
            unified_hexdiff(
                b"\n".join(x.encode("utf-8") for x in a_slice),
                b"\n".join(x.encode("utf-8") for x in b_slice),
                a_label=f"{a_label} (range @{dr.start:08X})",
                b_label=f"{b_label} (range @{dr.start:08X})",
                context_lines=context_lines,
                max_lines=max_lines,
                width=width,
            )
        )
    return out


def _format_output(obj: object, fmt: OutputFormat) -> str:
    if fmt == "json":
        return json.dumps(obj, indent=2, ensure_ascii=False, default=str)
    if fmt == "compact":
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, default=str)
    # text
    if isinstance(obj, str):
        return obj
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)


def _write_output(text: str, out_path: Path | None) -> None:
    if out_path is None:
        print(text)
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")


def cmd_bytes_diff(args: argparse.Namespace) -> int:
    a = Path(args.a).read_bytes()
    b = Path(args.b).read_bytes()
    ranges, first = diff_ranges(a, b)
    report: dict[str, object] = {
        "a": str(args.a),
        "b": str(args.b),
        "a_size": len(a),
        "b_size": len(b),
        "a_size_h": _human_size(len(a)),
        "b_size_h": _human_size(len(b)),
        "first_mismatch": first,
        "diff_ranges": [dataclasses.asdict(r) for r in ranges[: args.max_ranges]],
        "diff_ranges_total": len(ranges),
    }
    if args.with_context:
        report["first_mismatch_context"] = first_mismatch_context(a, b, around=args.context_bytes)
    if args.hexdiff:
        report["unified_hexdiff"] = unified_hexdiff(
            a,
            b,
            a_label=str(args.a),
            b_label=str(args.b),
            context_lines=args.hexdiff_context,
            max_lines=args.max_diff_lines,
            width=args.hexdiff_width,
        )
    _write_output(_format_output(report, args.format), args.out)
    return 0 if not ranges else 1


def _load_source_from_args(args: argparse.Namespace) -> ModelBytes:
    if args.mdl is not None:
        return _load_from_files(mdl_path=args.mdl, mdx_path=args.mdx)
    if args.resref is None:
        raise ValueError("Must provide either --mdl or --resref.")
    game = _resolve_game(args.game)
    install_path = args.install_path or _default_install_path(game)
    if install_path is None:
        raise FileNotFoundError("Could not determine install path. Provide --install-path or set K1_PATH/K2_PATH/TSL_PATH.")
    return _load_from_installation(game=game, install_path=install_path, resref=args.resref)


def _get_named_sources(
    *,
    args: argparse.Namespace,
    game: Game,
    want: set[SourceKind],
    mdlops_timeout_s: int,
    keep_dir: Path | None,
) -> dict[SourceKind, ModelBytes]:
    original = _load_source_from_args(args)
    resref = args.resref if args.resref is not None else (args.mdl.stem if args.mdl is not None else "model")

    out: dict[SourceKind, ModelBytes] = {"original": original}
    if "pykotor" in want:
        out["pykotor"] = _pykotor_roundtrip(original)
    if "mdlops" in want:
        mdlops_exe = _find_mdlops_exe(getattr(args, "mdlops_exe", None))
        mdlops_bytes, _art_dir = _run_mdlops_roundtrip(
            original=original,
            mdlops_exe=mdlops_exe,
            game=game,
            timeout_s=mdlops_timeout_s,
            keep_dir=keep_dir,
            resref=resref,
        )
        out["mdlops"] = mdlops_bytes
    return out


def _decode_mdx_row_block(
    *,
    mdx: bytes,
    mdx_data_offset: int,
    row_size: int,
    row_count: int,
    offsets: dict[str, int],
    max_rows: int,
) -> dict[str, object]:
    import struct

    # Try to find a base that fits; MDX offset semantics vary across tools.
    bases = [mdx_data_offset]
    if mdx_data_offset + 12 < len(mdx):
        bases.append(mdx_data_offset + 12)
    if mdx_data_offset >= 12:
        bases.append(mdx_data_offset - 12)

    base_used: int | None = None
    for base in bases:
        end = base + (row_size * row_count)
        if 0 <= base < len(mdx) and end <= len(mdx):
            base_used = base
            break
    if base_used is None:
        return {
            "ok": False,
            "reason": "row block does not fit in mdx for any tried base offset",
            "tried_bases": bases,
            "mdx_len": len(mdx),
        }

    rows: list[dict[str, object]] = []
    n = min(row_count, max_rows)
    for i in range(n):
        row_base = base_used + (i * row_size)
        row: dict[str, object] = {"row": i, "row_base": row_base}

        # floats
        def rf(off: int) -> float:
            return float(struct.unpack_from("<f", mdx, row_base + off)[0])

        if "vertex" in offsets:
            o = offsets["vertex"]
            row["vertex"] = [rf(o + 0), rf(o + 4), rf(o + 8)]
        if "normal" in offsets:
            o = offsets["normal"]
            row["normal"] = [rf(o + 0), rf(o + 4), rf(o + 8)]
        if "tex0" in offsets:
            o = offsets["tex0"]
            row["tex0"] = [rf(o + 0), rf(o + 4)]
        if "tex1" in offsets:
            o = offsets["tex1"]
            row["tex1"] = [rf(o + 0), rf(o + 4)]
        if "tangent" in offsets:
            o = offsets["tangent"]
            row["tangent"] = [rf(o + 0), rf(o + 4), rf(o + 8)]

        rows.append(row)

    return {
        "ok": True,
        "base_used": base_used,
        "row_size": row_size,
        "row_count": row_count,
        "decoded_rows": rows,
    }


def cmd_compare(args: argparse.Namespace) -> int:
    game = _resolve_game(args.game)
    original = _load_source_from_args(args)
    resref = args.resref if args.resref is not None else (args.mdl.stem if args.mdl is not None else "model")

    # Produce target B
    if args.against == "original":
        other = original
        other_label = original.label
        artifacts_dir: Path | None = None
    elif args.against == "pykotor":
        other = _pykotor_roundtrip(original)
        other_label = other.label
        artifacts_dir = None
    else:
        mdlops_exe = _find_mdlops_exe(args.mdlops_exe)
        keep = args.keep_dir
        other, artifacts_dir = _run_mdlops_roundtrip(
            original=original,
            mdlops_exe=mdlops_exe,
            game=game,
            timeout_s=args.mdlops_timeout_s,
            keep_dir=keep,
            resref=resref,
        )
        other_label = other.label

    # Compare chosen pairs: (pykotor vs mdlops) is typical, but here we compare "pykotor-roundtrip" to "mdlops-roundtrip"
    if args.compare_mode == "pykotor-vs-against":
        left = _pykotor_roundtrip(original)
        right = other
        left_label = left.label
        right_label = other_label
    else:
        left = original
        right = other
        left_label = original.label
        right_label = other_label

    mdl_ranges, mdl_first = diff_ranges(left.mdl, right.mdl)
    mdx_ranges, mdx_first = diff_ranges(left.mdx, right.mdx)

    report: dict[str, object] = {
        "game": "k1" if game == Game.K1 else "k2",
        "left": left_label,
        "right": right_label,
        "mdl": {
            "left_size": len(left.mdl),
            "right_size": len(right.mdl),
            "left_size_h": _human_size(len(left.mdl)),
            "right_size_h": _human_size(len(right.mdl)),
            "first_mismatch": mdl_first,
            "diff_ranges_total": len(mdl_ranges),
            "diff_ranges": [dataclasses.asdict(r) for r in mdl_ranges[: args.max_ranges]],
        },
        "mdx": {
            "left_size": len(left.mdx),
            "right_size": len(right.mdx),
            "left_size_h": _human_size(len(left.mdx)),
            "right_size_h": _human_size(len(right.mdx)),
            "first_mismatch": mdx_first,
            "diff_ranges_total": len(mdx_ranges),
            "diff_ranges": [dataclasses.asdict(r) for r in mdx_ranges[: args.max_ranges]],
        },
    }

    if args.with_context:
        report["mdl"]["first_mismatch_context"] = first_mismatch_context(left.mdl, right.mdl, around=args.context_bytes)
        report["mdx"]["first_mismatch_context"] = first_mismatch_context(left.mdx, right.mdx, around=args.context_bytes)

    if args.hexdiff:
        report["mdl"]["unified_hexdiff"] = unified_hexdiff(
            left.mdl,
            right.mdl,
            a_label=f"{left_label}.mdl",
            b_label=f"{right_label}.mdl",
            context_lines=args.hexdiff_context,
            max_lines=args.max_diff_lines,
            width=args.hexdiff_width,
        )
        report["mdx"]["unified_hexdiff"] = unified_hexdiff(
            left.mdx,
            right.mdx,
            a_label=f"{left_label}.mdx",
            b_label=f"{right_label}.mdx",
            context_lines=args.hexdiff_context,
            max_lines=args.max_diff_lines,
            width=args.hexdiff_width,
        )

    if args.layout:
        report["mdl"]["layout_segments_left"] = [dataclasses.asdict(s) for s in _layout_segments_from_reader(left.mdl, game)]
        report["mdl"]["layout_segments_right"] = [dataclasses.asdict(s) for s in _layout_segments_from_reader(right.mdl, game)]

    if args.mdx_rows:
        report["mdx"]["mdx_rows_summary_left"] = _parse_nodes_for_mdx_rows(left.mdl, left.mdx, game)
        report["mdx"]["mdx_rows_summary_right"] = _parse_nodes_for_mdx_rows(right.mdl, right.mdx, game)

    if args.attribute:
        left_segs = _segments_for_mdl(left.mdl, game=game)
        right_segs = _segments_for_mdl(right.mdl, game=game)
        largest = sorted(mdl_ranges, key=lambda r: r.length, reverse=True)[: args.max_ranges]
        report["mdl"]["attribution_left"] = _attribute_ranges_to_segments(largest, left_segs, max_hits=args.max_attribution)
        report["mdl"]["attribution_right"] = _attribute_ranges_to_segments(largest, right_segs, max_hits=args.max_attribution)

    if artifacts_dir is not None:
        report["mdlops_artifacts_dir"] = str(artifacts_dir)

    _write_output(_format_output(report, args.format), args.out)
    ok = (len(mdl_ranges) == 0) and (len(mdx_ranges) == 0)
    return 0 if ok else 1


def cmd_extract(args: argparse.Namespace) -> int:
    game = _resolve_game(args.game)
    want: set[SourceKind] = set(args.include)
    sources = _get_named_sources(
        args=args,
        game=game,
        want=want,
        mdlops_timeout_s=args.mdlops_timeout_s,
        keep_dir=args.keep_dir,
    )
    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    resref = args.resref if args.resref is not None else (args.mdl.stem if args.mdl is not None else "model")
    written: list[str] = []
    for kind, mb in sources.items():
        base = out_dir / f"{resref}-{kind}"
        (base.with_suffix(".mdl")).write_bytes(mb.mdl)
        written.append(str(base.with_suffix(".mdl")))
        if mb.mdx:
            (base.with_suffix(".mdx")).write_bytes(mb.mdx)
            written.append(str(base.with_suffix(".mdx")))

    _write_output(_format_output({"written": written}, args.format), args.out)
    return 0


def cmd_mdx_rows(args: argparse.Namespace) -> int:
    game = _resolve_game(args.game)
    want: set[SourceKind] = {args.source}
    if args.against is not None:
        want.add(args.against)
    sources = _get_named_sources(
        args=args,
        game=game,
        want=want,
        mdlops_timeout_s=args.mdlops_timeout_s,
        keep_dir=args.keep_dir,
    )

    src = sources[args.source]
    meshes = _capture_mesh_nodes(src.mdl, game=game)
    mesh_by_id = {m.node_id: m for m in meshes}

    if args.node_id is None:
        report = {
            "source": args.source,
            "mesh_nodes": [
                {
                    "node_id": m.node_id,
                    "type_id": f"0x{m.type_id:04X}",
                    "vertex_count": m.vertex_count,
                    "mdx_data_offset": m.mdx_data_offset,
                    "mdx_data_size": m.mdx_data_size,
                    "mdx_data_bitmap": f"0x{m.mdx_data_bitmap:08X}",
                    "texture1": m.texture1,
                }
                for m in sorted(meshes, key=lambda x: x.node_id)
            ],
        }
        _write_output(_format_output(report, args.format), args.out)
        return 0

    node_id = int(args.node_id)
    mesh = mesh_by_id.get(node_id)
    if mesh is None:
        _write_output(_format_output({"error": f"node_id {node_id} not found"}, args.format), args.out)
        return 2

    # Determine which fields are present
    offsets: dict[str, int] = {}
    if mesh.mdx_data_bitmap & _MDXDataFlags.VERTEX:
        offsets["vertex"] = mesh.mdx_vertex_offset
    if mesh.mdx_data_bitmap & _MDXDataFlags.NORMAL:
        offsets["normal"] = mesh.mdx_normal_offset
    if mesh.mdx_data_bitmap & _MDXDataFlags.TEX0:
        offsets["tex0"] = mesh.mdx_tex0_offset
    if mesh.mdx_data_bitmap & _MDXDataFlags.TEX1:
        offsets["tex1"] = mesh.mdx_tex1_offset
    if mesh.mdx_data_bitmap & _MDXDataFlags.TANGENT_SPACE:
        offsets["tangent"] = mesh.mdx_tangent_offset

    decoded = _decode_mdx_row_block(
        mdx=src.mdx,
        mdx_data_offset=mesh.mdx_data_offset,
        row_size=mesh.mdx_data_size,
        row_count=mesh.vertex_count,
        offsets=offsets,
        max_rows=args.max_rows,
    )

    report: dict[str, object] = {
        "source": args.source,
        "node_id": node_id,
        "mdx_data_offset": mesh.mdx_data_offset,
        "mdx_data_size": mesh.mdx_data_size,
        "mdx_data_bitmap": f"0x{mesh.mdx_data_bitmap:08X}",
        "fields": list(offsets.keys()),
        "decoded": decoded,
    }

    if args.against is not None:
        other = sources[args.against]
        other_meshes = _capture_mesh_nodes(other.mdl, game=game)
        other_by_id = {m.node_id: m for m in other_meshes}
        other_mesh = other_by_id.get(node_id)
        report["against"] = args.against
        if other_mesh is None:
            report["against_error"] = f"node_id {node_id} not found in against source"
        else:
            other_offsets: dict[str, int] = {}
            if other_mesh.mdx_data_bitmap & _MDXDataFlags.VERTEX:
                other_offsets["vertex"] = other_mesh.mdx_vertex_offset
            if other_mesh.mdx_data_bitmap & _MDXDataFlags.NORMAL:
                other_offsets["normal"] = other_mesh.mdx_normal_offset
            if other_mesh.mdx_data_bitmap & _MDXDataFlags.TEX0:
                other_offsets["tex0"] = other_mesh.mdx_tex0_offset
            if other_mesh.mdx_data_bitmap & _MDXDataFlags.TEX1:
                other_offsets["tex1"] = other_mesh.mdx_tex1_offset
            if other_mesh.mdx_data_bitmap & _MDXDataFlags.TANGENT_SPACE:
                other_offsets["tangent"] = other_mesh.mdx_tangent_offset

            report["against_meta"] = {
                "mdx_data_offset": other_mesh.mdx_data_offset,
                "mdx_data_size": other_mesh.mdx_data_size,
                "mdx_data_bitmap": f"0x{other_mesh.mdx_data_bitmap:08X}",
                "fields": list(other_offsets.keys()),
            }
            report["against_decoded"] = _decode_mdx_row_block(
                mdx=other.mdx,
                mdx_data_offset=other_mesh.mdx_data_offset,
                row_size=other_mesh.mdx_data_size,
                row_count=other_mesh.vertex_count,
                offsets=other_offsets,
                max_rows=args.max_rows,
            )

    _write_output(_format_output(report, args.format), args.out)
    return 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    """
    Diagnose MDL/MDX discrepancies between PyKotor and MDLOps.

    This is a high-signal summary designed to immediately tell you what's wrong.
    """

    game = _resolve_game(args.game)

    # Get original bytes
    original: ModelBytes
    if args.resref is not None:
        install_path = args.install_path or _default_install_path(game)
        if install_path is None:
            raise RuntimeError(f"No installation found for {game.name}; use --install-path")
        original = _load_from_installation(game=game, install_path=install_path, resref=args.resref)
        resref = args.resref
    elif args.mdl is not None:
        original = _load_from_files(mdl_path=args.mdl, mdx_path=args.mdx)
        resref = args.mdl.stem
    else:
        raise RuntimeError("Specify --resref or --mdl")

    # Generate PyKotor roundtrip
    pykotor = _pykotor_roundtrip(original)

    # Generate MDLOps roundtrip
    mdlops_exe = _find_mdlops_exe(args.mdlops_exe)
    try:
        mdlops, _ = _run_mdlops_roundtrip(
            original=original,
            mdlops_exe=mdlops_exe,
            game=game,
            timeout_s=args.mdlops_timeout_s,
            keep_dir=args.keep_dir,
            resref=resref,
        )
    except Exception as e:
        print(f"MDLOps roundtrip failed: {e}", file=sys.stderr)
        return 2

    # Analyze discrepancies
    report_lines: list[str] = []
    report_lines.append(f"=== MDL/MDX Diagnostic: {resref} ({game.name}) ===\n")

    # Size comparison
    report_lines.append("FILE SIZES:")
    report_lines.append(f"  Original:  MDL={len(original.mdl):>7} bytes, MDX={len(original.mdx):>7} bytes")
    report_lines.append(f"  PyKotor:   MDL={len(pykotor.mdl):>7} bytes, MDX={len(pykotor.mdx):>7} bytes")
    report_lines.append(f"  MDLOps:    MDL={len(mdlops.mdl):>7} bytes, MDX={len(mdlops.mdx):>7} bytes")

    mdl_diff = len(pykotor.mdl) - len(mdlops.mdl)
    mdx_diff = len(pykotor.mdx) - len(mdlops.mdx)
    report_lines.append(f"  Delta (PyKotor - MDLOps): MDL={mdl_diff:+d} bytes, MDX={mdx_diff:+d} bytes")
    report_lines.append("")

    # Compare PyKotor vs MDLOps
    mdl_ranges, mdl_first = diff_ranges(pykotor.mdl, mdlops.mdl)
    mdx_ranges, mdx_first = diff_ranges(pykotor.mdx, mdlops.mdx)

    if len(mdl_ranges) == 0 and len(mdx_ranges) == 0:
        report_lines.append("RESULT: PASS - PyKotor output is byte-identical to MDLOps!")
        _write_output("\n".join(report_lines), args.out)
        return 0

    report_lines.append("BYTE DIFFERENCES:")
    report_lines.append(f"  MDL: {len(mdl_ranges)} diff ranges, first mismatch at offset 0x{mdl_first:X}" if mdl_first else "  MDL: Identical (except size)")
    report_lines.append(f"  MDX: {len(mdx_ranges)} diff ranges, first mismatch at offset 0x{mdx_first:X}" if mdx_first else "  MDX: Identical (except size)")
    report_lines.append("")

    # Parse mesh nodes from both
    pk_meshes = _capture_mesh_nodes(pykotor.mdl, game=game)
    mo_meshes = _capture_mesh_nodes(mdlops.mdl, game=game)
    pk_by_id = {m.node_id: m for m in pk_meshes}
    mo_by_id = {m.node_id: m for m in mo_meshes}

    # Find mesh node discrepancies
    report_lines.append("MESH NODE COMPARISON (MDX metadata):")
    mismatches: list[dict] = []

    for node_id in sorted(set(pk_by_id.keys()) | set(mo_by_id.keys())):
        pk = pk_by_id.get(node_id)
        mo = mo_by_id.get(node_id)

        if pk is None or mo is None:
            report_lines.append(f"  Node {node_id}: MISSING in {'PyKotor' if pk is None else 'MDLOps'}")
            continue

        problems: list[str] = []

        # Check mdx_data_size (row stride)
        if pk.mdx_data_size != mo.mdx_data_size:
            problems.append(f"row_size {pk.mdx_data_size} vs {mo.mdx_data_size}")

        # Check bitmap
        if pk.mdx_data_bitmap != mo.mdx_data_bitmap:
            problems.append(f"bitmap 0x{pk.mdx_data_bitmap:08X} vs 0x{mo.mdx_data_bitmap:08X}")

        # Check vertex count
        if pk.vertex_count != mo.vertex_count:
            problems.append(f"vertex_count {pk.vertex_count} vs {mo.vertex_count}")

        # Check MDX data total size (vertex_count * row_size)
        pk_total = pk.vertex_count * pk.mdx_data_size
        mo_total = mo.vertex_count * mo.mdx_data_size
        if pk_total != mo_total:
            problems.append(f"mdx_total {pk_total} vs {mo_total}")

        if problems:
            mismatches.append(
                {
                    "node_id": node_id,
                    "tex1": pk.texture1 or "NULL",
                    "pk": pk,
                    "mo": mo,
                    "problems": problems,
                }
            )
            report_lines.append(f"  Node {node_id} ({pk.texture1 or 'NULL'}): " + ", ".join(problems))

    if not mismatches:
        report_lines.append("  All mesh nodes have matching MDX metadata")

    report_lines.append("")

    # Detailed analysis of first mismatch
    if mismatches:
        first_mm = mismatches[0]
        pk = first_mm["pk"]
        mo = first_mm["mo"]
        report_lines.append(f"DETAILED ANALYSIS of first mismatched node (node_id={first_mm['node_id']}):")
        report_lines.append("  PyKotor:")
        report_lines.append(f"    mdx_data_offset: {pk.mdx_data_offset}")
        report_lines.append(f"    mdx_data_size (row stride): {pk.mdx_data_size}")
        report_lines.append(f"    mdx_data_bitmap: 0x{pk.mdx_data_bitmap:08X}")
        report_lines.append(f"    vertex_count: {pk.vertex_count}")
        report_lines.append(f"    Implied MDX bytes: {pk.vertex_count * pk.mdx_data_size}")
        report_lines.append("  MDLOps:")
        report_lines.append(f"    mdx_data_offset: {mo.mdx_data_offset}")
        report_lines.append(f"    mdx_data_size (row stride): {mo.mdx_data_size}")
        report_lines.append(f"    mdx_data_bitmap: 0x{mo.mdx_data_bitmap:08X}")
        report_lines.append(f"    vertex_count: {mo.vertex_count}")
        report_lines.append(f"    Implied MDX bytes: {mo.vertex_count * mo.mdx_data_size}")

        # Compute expected row size from bitmap
        pk_expected = _compute_expected_row_size(pk.mdx_data_bitmap, is_skin=bool(pk.type_id & 0x40))
        mo_expected = _compute_expected_row_size(mo.mdx_data_bitmap, is_skin=bool(mo.type_id & 0x40))
        report_lines.append("  Computed expected row sizes from bitmap:")
        report_lines.append(f"    PyKotor bitmap -> expected row_size: {pk_expected}")
        report_lines.append(f"    MDLOps bitmap -> expected row_size: {mo_expected}")

        if pk.mdx_data_size != pk_expected:
            report_lines.append(f"    *** PyKotor row_size ({pk.mdx_data_size}) != expected ({pk_expected})")
        if mo.mdx_data_size != mo_expected:
            report_lines.append(f"    *** MDLOps row_size ({mo.mdx_data_size}) != expected ({mo_expected})")

        report_lines.append("")

        # Show first few MDX rows from both
        report_lines.append("  First 3 MDX rows (raw hex):")
        for label, mb, mesh in [("PyKotor", pykotor, pk), ("MDLOps", mdlops, mo)]:
            report_lines.append(f"    {label}:")
            base = mesh.mdx_data_offset
            stride = mesh.mdx_data_size
            for row_i in range(min(3, mesh.vertex_count)):
                start = base + row_i * stride
                end = start + stride
                if end <= len(mb.mdx):
                    row_hex = mb.mdx[start:end].hex()
                    report_lines.append(f"      row[{row_i}] @{start}: {row_hex[:80]}...")
                else:
                    report_lines.append(f"      row[{row_i}]: OOB (start={start}, mdx_len={len(mb.mdx)})")

    report_lines.append("")
    report_lines.append("DIAGNOSIS:")

    # Provide actionable insight
    if mdx_diff != 0 and mismatches:
        if any("row_size" in " ".join(m["problems"]) for m in mismatches):
            report_lines.append("  - MDX row stride mismatch detected. Check MDLBinaryWriter._update_mdx() calculation of mdx_data_size.")
            report_lines.append("  - The bitmap->row_size mapping may not match MDLOps expectations.")
        if any("bitmap" in " ".join(m["problems"]) for m in mismatches):
            report_lines.append("  - MDX bitmap mismatch. Check how tangent_space and other flags are computed.")
    if mdl_diff != 0:
        report_lines.append("  - MDL size differs. Check node offsets, padding, or extra/missing data sections.")

    report_lines.append("\nRESULT: FAIL - See above for details.")

    _write_output("\n".join(report_lines), args.out)
    return 1


NODE_TYPE_NAMES: dict[int, str] = {
    0x0001: "dummy",
    0x0003: "light",
    0x0005: "emitter",
    0x0011: "camera",
    0x0021: "trimesh",
    0x0041: "reference",
    0x0061: "skin",
    0x0081: "anim",
    0x00A1: "dangly",
    0x00C1: "aabb",
    0x0101: "saber",
}


def _walk_binary_nodes(
    mdl_data: bytes,
    root_offset: int,
    names_list: list[str],
) -> list[dict]:
    """Walk node tree from binary MDL and return node metadata."""
    reader = BinaryReader.from_bytes(mdl_data)
    nodes: list[dict] = []
    data_len = len(mdl_data)

    def walk(offset: int, depth: int):
        reader.seek(offset + 12)  # file header offset
        # Use _NodeHeader to parse correctly
        node_hdr = _NodeHeader()
        node_hdr.read(reader)
        
        node_type = node_hdr.type_id
        node_id = node_hdr.node_id
        children_off = node_hdr.offset_to_children
        children_count = node_hdr.children_count

        # Get name from names list (node_id is the index)
        name = names_list[node_id] if node_id < len(names_list) else "?"

        type_name = NODE_TYPE_NAMES.get(node_type, f"unknown(0x{node_type:04X})")

        nodes.append(
            {
                "id": node_id,
                "type": node_type,
                "type_name": type_name,
                "name": name,
                "depth": depth,
                "children_count": children_count,
                "children_off": children_off,
                "offset": offset,
            }
        )

        if children_count > 0 and children_off > 0:
            # children_off is an offset into the model data (already accounts for file header in MDL format)
            # We need to add 12 to seek to the correct position in raw file bytes
            seek_pos = children_off + 12
            if seek_pos < data_len - 4:
                reader.seek(seek_pos)
                child_offsets = [reader.read_uint32() for _ in range(children_count)]
                for child_off in child_offsets:
                    if 0 < child_off < data_len - 40:  # min node header size
                        walk(child_off, depth + 1)

    walk(root_offset, 0)
    return nodes


def cmd_node_types(args: argparse.Namespace) -> int:
    """Walk node tree and show binary node types."""
    game = _resolve_game(args.game)
    
    # Load original
    if args.mdl:
        original = _load_from_files(mdl_path=args.mdl, mdx_path=args.mdx)
        resref = args.mdl.stem
    elif args.resref:
        install_path = args.install_path or _default_install_path(game)
        if install_path is None:
            return _write_output(_err(f"No {game.name} installation found"), args.out) or 1
        original = _load_from_installation(game=game, install_path=install_path, resref=args.resref)
        resref = args.resref
    else:
        return _write_output(_err("Must provide --resref or --mdl"), args.out) or 1
    
    mdl_data = original.mdl
    reader = BinaryReader.from_bytes(mdl_data)
    
    # Parse model header using _ModelHeader from io_mdl
    # File header: 12 bytes (skip), model header starts at offset 12
    reader.seek(12)  # Skip file header
    model_header = _ModelHeader()
    model_header.read(reader)
    
    root_node_offset = model_header.geometry.root_node_offset
    name_offsets_offset = model_header.offset_to_name_offsets
    name_offsets_count = model_header.name_offsets_count

    # Read name offsets (these are actually just indices, names are sequential after)
    reader.seek(name_offsets_offset + 12)
    name_offsets = [reader.read_uint32() for _ in range(name_offsets_count)]
    
    # Names start right after name offsets, read as sequential null-terminated strings
    names_start = name_offsets_offset + name_offsets_count * 4 + 12
    # Names end at offset_to_animations
    names_end = model_header.offset_to_animations + 12
    names_size = names_end - names_start
    if names_size > 0:
        reader.seek(names_start)
        names_raw = reader.read_bytes(names_size)
        names_list: list[str] = []
        current_pos = 0
        for _ in range(name_offsets_count):
            null_pos = names_raw.find(b'\x00', current_pos)
            if null_pos == -1:
                null_pos = len(names_raw)
            name_bytes = names_raw[current_pos:null_pos]
            names_list.append(name_bytes.decode('ascii', errors='ignore'))
            current_pos = null_pos + 1
            if current_pos >= len(names_raw):
                break
    else:
        names_list = []

    # Walk nodes
    nodes = _walk_binary_nodes(mdl_data, root_node_offset, names_list)

    # Also read with PyKotor to compare
    pk_mdl = read_mdl(original.mdl, source_ext=(original.mdx or None), file_format=ResourceType.MDL)
    pk_nodes = list(pk_mdl.all_nodes())
    pk_node_types = {n.name: type(n).__name__ for n in pk_nodes}
    # Also capture mesh info
    pk_has_mesh = {n.name: (n.mesh is not None) for n in pk_nodes}
    pk_vertex_counts = {n.name: len(n.mesh.vertex_positions) if n.mesh else 0 for n in pk_nodes}
    pk_face_counts = {n.name: len(n.mesh.faces) if n.mesh and n.mesh.faces else 0 for n in pk_nodes}
    # Light node info
    pk_light_info: dict[str, dict] = {}
    for n in pk_nodes:
        if n.light:
            pk_light_info[n.name] = {
                "flare": n.light.flare,
                "flare_sizes": len(n.light.flare_sizes) if n.light.flare_sizes else 0,
                "flare_positions": len(n.light.flare_positions) if n.light.flare_positions else 0,
                "flare_textures": len(n.light.flare_textures) if n.light.flare_textures else 0,
                "flare_color_shifts": len(n.light.flare_color_shifts) if n.light.flare_color_shifts else 0,
            }

    # Count types
    type_counts: dict[str, int] = {}
    for n in nodes:
        t = n["type_name"]
        type_counts[t] = type_counts.get(t, 0) + 1

    # Count total controllers
    total_controllers = sum(len(n.controllers) for n in pk_nodes)
    # Count animations
    total_anims = len(pk_mdl.animations)
    anim_node_count = sum(len(list(a.all_nodes())) for a in pk_mdl.animations)
    
    lines = [
        f"=== Node Types for {resref} ({game.name}) ===",
        "",
        f"MDL size: {len(original.mdl)} bytes",
        f"Model header node_count: {model_header.geometry.node_count}",
        f"Model header anim_count: {model_header.animation_count}",
        f"Model header anim_offset: {model_header.offset_to_animations}",
        f"Root node offset: {root_node_offset}",
        f"Name offsets: offset={name_offsets_offset}, count={name_offsets_count}",
        f"Total controllers read: {total_controllers}",
        f"Total animations read: {total_anims} ({anim_node_count} anim nodes)",
        "",
        f"Total nodes found by walk: {len(nodes)}",
        f"Type distribution: {dict(sorted(type_counts.items(), key=lambda x: -x[1]))}",
        "",
        "Binary node tree:",
    ]

    for n in nodes[: args.max_nodes]:
        indent = "  " * n["depth"]
        pk_type = pk_node_types.get(n["name"], "?")
        marker = ""
        if n["type_name"] == "trimesh" and pk_type == "MDLNode":
            marker = " *** LOST MESH DATA"
        elif n["type_name"] == "skin" and pk_type == "MDLNode":
            marker = " *** LOST SKIN DATA"
        elif n["type_name"] == "dangly" and pk_type == "MDLNode":
            marker = " *** LOST DANGLY DATA"
        elif n["type_name"] == "aabb" and pk_type == "MDLNode":
            marker = " *** LOST AABB DATA"
        has_mesh = pk_has_mesh.get(n["name"], False)
        verts = pk_vertex_counts.get(n["name"], 0)
        faces = pk_face_counts.get(n["name"], 0)
        light_info = pk_light_info.get(n["name"])
        if has_mesh:
            mesh_info = f"v={verts} f={faces}"
        elif light_info:
            mesh_info = f"light flare={light_info['flare']} sz={light_info['flare_sizes']} pos={light_info['flare_positions']} tex={light_info['flare_textures']}"
        else:
            mesh_info = "no_mesh"
        # Lost data = binary has mesh type but PyKotor didn't read mesh data
        marker = ""
        binary_has_mesh = n["type_name"] in ("trimesh", "skin", "dangly", "aabb", "saber", "unknown(0x0221)")
        if binary_has_mesh and not has_mesh:
            marker = " *** LOST MESH DATA"
        lines.append(f"{indent}[{n['id']:2d}] {n['type_name']:10s} ({n['type']:04X}) name={n['name']!r:20s} -> PyKotor: {mesh_info}{marker}")

    if len(nodes) > args.max_nodes:
        lines.append(f"  ... and {len(nodes) - args.max_nodes} more nodes")

    lines.append("")
    lines.append("Summary of lost data:")
    mesh_types = ("trimesh", "skin", "dangly", "aabb", "saber", "unknown(0x0221)")
    lost = [n for n in nodes if n["type_name"] in mesh_types and not pk_has_mesh.get(n["name"], False)]
    if lost:
        lines.append(f"  {len(lost)} nodes had mesh data in binary but PyKotor didn't read mesh attribute")
        for n in lost[:10]:
            lines.append(f"    - node {n['id']} ({n['name']!r}): binary type={n['type_name']}")
    else:
        lines.append("  No mesh data loss detected.")

    _write_output("\n".join(lines), args.out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mdl_aio",
        description="All-in-one MDL/MDX debugging CLI (PyKotor vs original vs MDLOps).",
    )
    p.add_argument("--format", choices=("text", "json", "compact"), default="text")
    p.add_argument("--out", type=Path, default=None, help="Write output to file (default: stdout).")

    sub = p.add_subparsers(dest="cmd", required=True)

    # bytes-diff: generic binary compare
    bd = sub.add_parser("bytes-diff", help="Compare two files (bytes) and report diff ranges + optional hexdump udiff.")
    bd.add_argument("--a", type=Path, required=True)
    bd.add_argument("--b", type=Path, required=True)
    bd.add_argument("--max-ranges", type=int, default=25)
    bd.add_argument("--with-context", action="store_true")
    bd.add_argument("--context-bytes", type=int, default=64)
    bd.add_argument("--hexdiff", action="store_true", help="Include a unified diff of hexdump lines.")
    bd.add_argument("--hexdiff-context", type=int, default=3)
    bd.add_argument("--hexdiff-width", type=int, default=16)
    bd.add_argument("--max-diff-lines", type=int, default=400)
    bd.set_defaults(func=cmd_bytes_diff)

    # compare: orchestration around installation/files + pykotor + mdlops
    cmp = sub.add_parser("compare", help="Compare models (original/pykotor/mdlops) with actionable diffs.")
    src = cmp.add_argument_group("source")
    src.add_argument("--game", choices=("k1", "k2"), default="k1")
    src.add_argument("--install-path", type=Path, default=None)
    src.add_argument("--resref", type=str, default=None, help="Resource name (without extension) from installation.")
    src.add_argument("--mdl", type=Path, default=None, help="Path to .mdl to use as source instead of --resref.")
    src.add_argument("--mdx", type=Path, default=None, help="Optional path to .mdx for --mdl source.")

    tgt = cmp.add_argument_group("target")
    tgt.add_argument("--against", choices=("original", "pykotor", "mdlops"), default="mdlops")
    tgt.add_argument("--compare-mode", choices=("pykotor-vs-against", "original-vs-against"), default="pykotor-vs-against")
    tgt.add_argument("--mdlops-exe", type=Path, default=None)
    tgt.add_argument("--mdlops-timeout-s", type=int, default=900)
    tgt.add_argument("--keep-dir", type=Path, default=None, help="Keep MDLOps temp artifacts here (debugging).")

    out = cmp.add_argument_group("report")
    out.add_argument("--max-ranges", type=int, default=25)
    out.add_argument("--with-context", action="store_true")
    out.add_argument("--context-bytes", type=int, default=64)
    out.add_argument("--hexdiff", action="store_true")
    out.add_argument("--hexdiff-context", type=int, default=3)
    out.add_argument("--hexdiff-width", type=int, default=16)
    out.add_argument("--max-diff-lines", type=int, default=400)
    out.add_argument("--layout", action="store_true", help="Include coarse layout segment maps.")
    out.add_argument("--mdx-rows", action="store_true", help="Include a simple per-node MDX rows summary.")
    out.add_argument("--attribute", action="store_true", help="Attribute diff ranges to labeled sections (faces/verts/controllers/etc).")
    out.add_argument("--max-attribution", type=int, default=30)
    cmp.set_defaults(func=cmd_compare)

    ex = sub.add_parser("extract", help="Write original/pykotor/mdlops artifacts to an output folder.")
    ex.add_argument("--game", choices=("k1", "k2"), default="k1")
    ex.add_argument("--install-path", type=Path, default=None)
    ex.add_argument("--resref", type=str, default=None)
    ex.add_argument("--mdl", type=Path, default=None)
    ex.add_argument("--mdx", type=Path, default=None)
    ex.add_argument("--output-dir", type=Path, required=True)
    ex.add_argument("--include", choices=("original", "pykotor", "mdlops"), nargs="+", default=["original", "pykotor"])
    ex.add_argument("--mdlops-exe", type=Path, default=None)
    ex.add_argument("--mdlops-timeout-s", type=int, default=900)
    ex.add_argument("--keep-dir", type=Path, default=None)
    ex.set_defaults(func=cmd_extract)

    mr = sub.add_parser("mdx-rows", help="Inspect MDX row data for a mesh node (optionally compare two sources).")
    mr.add_argument("--game", choices=("k1", "k2"), default="k1")
    mr.add_argument("--install-path", type=Path, default=None)
    mr.add_argument("--resref", type=str, default=None)
    mr.add_argument("--mdl", type=Path, default=None)
    mr.add_argument("--mdx", type=Path, default=None)
    mr.add_argument("--source", choices=("original", "pykotor", "mdlops"), default="original")
    mr.add_argument("--against", choices=("original", "pykotor", "mdlops"), default=None)
    mr.add_argument("--node-id", type=int, default=None, help="If omitted, lists mesh nodes with MDX metadata.")
    mr.add_argument("--max-rows", type=int, default=10)
    mr.add_argument("--mdlops-exe", type=Path, default=None)
    mr.add_argument("--mdlops-timeout-s", type=int, default=900)
    mr.add_argument("--keep-dir", type=Path, default=None)
    mr.set_defaults(func=cmd_mdx_rows)

    # diagnose: concise, actionable summary
    diag = sub.add_parser("diagnose", help="Quick diagnosis of PyKotor vs MDLOps discrepancies (high-signal summary).")
    diag.add_argument("resref", type=str, nargs="?", default=None, help="Resource name (without extension) from installation.")
    diag.add_argument("--game", choices=("k1", "k2"), default="k1")
    diag.add_argument("--install-path", type=Path, default=None)
    diag.add_argument("--mdl", type=Path, default=None, help="Path to .mdl to use as source instead of resref.")
    diag.add_argument("--mdx", type=Path, default=None, help="Optional path to .mdx for --mdl source.")
    diag.add_argument("--mdlops-exe", type=Path, default=None)
    diag.add_argument("--mdlops-timeout-s", type=int, default=900)
    diag.add_argument("--keep-dir", type=Path, default=None)
    diag.set_defaults(func=cmd_diagnose)

    # node-types: walk binary node tree and show types
    nt = sub.add_parser("node-types", help="Walk binary node tree and show node types (debug reader issues).")
    nt.add_argument("resref", type=str, nargs="?", default=None, help="Resource name from installation.")
    nt.add_argument("--game", choices=("k1", "k2"), default="k1")
    nt.add_argument("--install-path", type=Path, default=None)
    nt.add_argument("--mdl", type=Path, default=None, help="Path to .mdl to use as source instead of resref.")
    nt.add_argument("--mdx", type=Path, default=None, help="Optional path to .mdx for --mdl source.")
    nt.add_argument("--max-nodes", type=int, default=60, help="Max nodes to display in tree.")
    nt.set_defaults(func=cmd_node_types)

    return p


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print(_err("Interrupted"), file=sys.stderr)
        return 130
    except Exception as e:
        print(_err(str(e)), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
