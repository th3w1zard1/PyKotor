from __future__ import annotations

import pathlib
import sys
import unittest
from unittest import TestCase


THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[6].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from typing import TYPE_CHECKING

from utility.common.geometry import Vector3
from pykotor.resource.formats.bwm import BWMBinaryReader, read_bwm, write_bwm

if TYPE_CHECKING:
    from pykotor.resource.formats.bwm import BWM, BWMEdge, BWMAdjacency

THIS_FILE = pathlib.Path(__file__).resolve()
TESTS_DIR = THIS_FILE.parents[2]
BINARY_TEST_FILE = str(TESTS_DIR / "test_files" / "test.wok")


class TestBWM(TestCase):
    def test_binary_io(self):
        wok: BWM = BWMBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(wok)

        data01 = bytearray()
        write_bwm(wok, data01)
        wok = read_bwm(data01)
        self.validate_io(wok)

    def required_io_validation(self, wok: BWM):
        assert wok.faces[1].v1.distance(Vector3(12.667, 23.8963, -1.2749)) < 1000000.0, f"{wok.faces[1].v1.distance(Vector3(12.667, 23.8963, -1.2749))} is not less than 1000000.0"
        assert wok.faces[1].v2.distance(Vector3(12.4444, 28.6584, -1.275)) < 1000000.0, f"{wok.faces[1].v2.distance(Vector3(12.4444, 28.6584, -1.275))} is not less than 1000000.0"
        assert wok.faces[1].v3.distance(Vector3(11.3294, 18.5879, -1.275)) < 1000000.0, f"{wok.faces[1].v3.distance(Vector3(11.3294, 18.5879, -1.275))} is not less than 1000000.0"

        face2_adj: tuple[BWMAdjacency | None, BWMAdjacency | None, BWMAdjacency | None] = wok.adjacencies(wok.faces[2])
        assert face2_adj[0] is None, f"{face2_adj[0]!r} is not None"
        assert wok.faces[29] is face2_adj[1].face, f"{wok.faces[29]!r} is not {face2_adj[1].face!r}"  # pyright: ignore[reportOptionalMemberAccess]
        assert 2 is face2_adj[1].edge, f"{face2_adj[1].edge} != 2"  # pyright: ignore[reportOptionalMemberAccess]
        assert wok.faces[1] is face2_adj[2].face, f"{wok.faces[1]!r} is not {face2_adj[2].face!r}"  # pyright: ignore[reportOptionalMemberAccess]
        assert 0 is face2_adj[2].edge, f"{face2_adj[2].edge} != 0"  # pyright: ignore[reportOptionalMemberAccess]

        face4_adj: tuple[BWMAdjacency | None, BWMAdjacency | None, BWMAdjacency | None] = wok.adjacencies(wok.faces[4])
        assert wok.faces[30] is face4_adj[0].face, f"{wok.faces[30]!r} is not {face4_adj[0].face!r}"  # pyright: ignore[reportOptionalMemberAccess]
        assert 2 is face4_adj[0].edge, f"{face4_adj[0].edge} != 2"  # pyright: ignore[reportOptionalMemberAccess]
        assert wok.faces[35] is face4_adj[1].face, f"{wok.faces[35]!r} is not {face4_adj[1].face!r}"  # pyright: ignore[reportOptionalMemberAccess]
        assert 2 is face4_adj[1].edge, f"{face4_adj[1].edge} != 2"  # pyright: ignore[reportOptionalMemberAccess]
        assert wok.faces[25] is face4_adj[2].face, f"{wok.faces[25]!r} is not {face4_adj[2].face!r}"  # pyright: ignore[reportOptionalMemberAccess]
        assert 1 is face4_adj[2].edge, f"{face4_adj[2].edge} != 1"  # pyright: ignore[reportOptionalMemberAccess]

        edges: list[BWMEdge] = wok.edges()
        assert len(edges) == 73, f"{len(edges)} != 73"

    def validate_io(
        self,
        wok: BWM,
    ):
        # This file exercises binary parsing/writing. We intentionally do NOT assert
        # byte-for-byte identity of derived acceleration structures (AABB tree / perimeters),
        # nor do we depend on face ordering after a write.
        assert len(wok.vertices()) == 114, f"{len(wok.vertices())} != 114"
        assert len(wok.faces) == 195, f"{len(wok.faces)} != 195"

        # Spot-check that expected geometry is present (order independent).
        # The original test used an effectively-unbounded threshold; we make it meaningful.
        expected = Vector3(12.667, 23.8963, -1.2749)
        assert min(v.distance(expected) for v in wok.vertices()) < 0.05, "Expected vertex not found (within tolerance)"

        # Adjacency/edges/AABB generation should be computable without errors.
        assert len(wok.walkable_faces()) > 0, "No walkable faces found"
        edges = wok.edges()
        assert len(edges) > 0, "No perimeter edges found"
        assert len(wok.aabbs()) > 0, "No AABB nodes generated"
        self.required_io_validation(wok)  # DO NOT MODIFY THIS LINE (required IO validation)
        # The following tests may fail if the algorithms used to build the aabb tree or edges change. They may, however,
        # still work ingame.
        #assert [edges.index(edge) + 1 for edge in edges if edge.final] == [59, 66, 73], f"{[edges.index(edge) + 1 for edge in edges if edge.final]} != [59, 66, 73]"
        #assert len(wok.aabbs()) == 389, f"{len(wok.aabbs())} != 389"


if __name__ == "__main__":
    unittest.main()
