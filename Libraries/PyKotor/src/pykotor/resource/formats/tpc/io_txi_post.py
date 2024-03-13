from __future__ import annotations

import math
import re

from typing import TYPE_CHECKING

from typing_extensions import Literal

if TYPE_CHECKING:
    from pykotor.resource.formats.tpc.io_tga import TPCTGAReader
    from pykotor.resource.formats.tpc.io_tpc import TPCBinaryReader


def process_tpc_cubemaps_data(tpc_reader: TPCBinaryReader | TPCTGAReader, txi_lines: str) -> None | tuple[int, Literal[6]]:
    # Before setting the TPC data, check for cubemap or animated texture
    if not re.search(r"^\s*cube\s+1", txi_lines, re.IGNORECASE):
        return None

    print("make cubemap texture")
    face_size = tpc_reader._tpc._get_size(tpc_reader._tpc._width, tpc_reader._tpc._height, tpc_reader._tpc.format()) or tpc_reader._tpc.format().min_size()
    return face_size, 6


def process_tpc_animations_data(tpc_reader: TPCBinaryReader | TPCTGAReader, txi_lines: str) -> None | tuple[int, int]:
    # Check for animated texture based on the TXI data
    if not re.search(r"^\s*proceduretype\s+cycle", txi_lines, re.IGNORECASE):
        return None

    print("make animated texture")
    # Extract the number of frames in the x and y directions
    numx_match = re.search(r"^\s*numx\s+(\d+)", txi_lines, re.IGNORECASE)
    numy_match = re.search(r"^\s*numy\s+(\d+)", txi_lines, re.IGNORECASE)
    numx = int(numx_match.group(1)) if numx_match else 1
    numy = int(numy_match.group(1)) if numy_match else 1

    # Determine the default width and height of each frame
    defwidth_match = re.search(r"^\s*defaultwidth\s+(\d+)", txi_lines, re.IGNORECASE)
    defheight_match = re.search(r"^\s*defaultheight\s+(\d+)", txi_lines, re.IGNORECASE)
    defwidth = int(defwidth_match.group(1)) if defwidth_match else tpc_reader._tpc._width // numx
    defheight = int(defheight_match.group(1)) if defheight_match else tpc_reader._tpc._height // numy

    # Ensure the default dimensions do not exceed the texture dimensions
    defwidth = min(defwidth, tpc_reader._tpc._width // numx)
    defheight = min(defheight, tpc_reader._tpc._height // numy)

    # Compute the size for each frame, then for all frames, at each mipmap level
    total_data_size = 0
    w, h = defwidth, defheight
    frame_count = numx * numy
    frame_size = tpc_reader._tpc._texture_format.min_size()
    while w >= 1 or h >= 1:
        frame_size = tpc_reader._tpc._get_size(w, h, tpc_reader._tpc._texture_format) or frame_size
        total_data_size += frame_size * frame_count
        w >>= 1
        h >>= 1
    return frame_size, frame_count
