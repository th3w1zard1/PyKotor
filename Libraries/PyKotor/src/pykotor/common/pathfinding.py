"""Pathfinding system for KotOR games.

This module provides an abstract A* pathfinding implementation that can be used
by any engine implementation. The pathfinder uses PTH (path) data from modules
to find navigation paths between points.

References:
----------
    vendor/reone/src/libs/game/pathfinder.cpp (A* pathfinding implementation)
    vendor/reone/include/reone/game/pathfinder.h (Pathfinder interface)
    vendor/reone/include/reone/resource/path.h (Path data structure)
    vendor/KotOR.js/src/pathfinding/Pathfinder.ts (TypeScript pathfinding)
    Note: Pathfinding uses A* algorithm with PTH waypoint data
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from utility.common.geometry import Vector3  # noqa: PLC2701

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pykotor.resource.generics.pth import PTH


@dataclass
class PathfindingVertex:
    """A vertex in the pathfinding graph."""

    index: int
    position: Vector3
    adjacent_indices: list[int]


@dataclass
class PathfindingContextVertex:
    """A vertex in the A* search context."""

    index: int
    parent_index: int = -1
    distance: float = 0.0
    heuristic: float = 0.0
    total_cost: float = 0.0


class Pathfinder:
    """A* pathfinding implementation for KotOR modules.

    This class implements the A* pathfinding algorithm using PTH (path) data
    from modules. It finds optimal paths between two points in 3D space.

    The pathfinder loads waypoint data from PTH files and constructs a graph
    of connected waypoints. When finding a path, it uses A* to search for the
    optimal route through this graph.

    References:
    ----------
        vendor/reone/src/libs/game/pathfinder.cpp (lines 26-154)
        vendor/reone/include/reone/game/pathfinder.h (lines 29-56)
    """

    def __init__(self) -> None:
        """Initialize a new pathfinder."""
        self._vertices: list[Vector3] = []
        self._adjacent_vertices: dict[int, list[int]] = {}

    def load_from_pth(self, pth: PTH, point_z: dict[int, float] | None = None) -> None:
        """Load pathfinding data from a PTH file.

        Args:
        ----
            pth: The PTH resource containing waypoint data
            point_z: Optional mapping of point indices to Z coordinates
                If not provided, Z coordinates default to 0.0
        """
        self._vertices = []
        self._adjacent_vertices = {}

        point_z = point_z or {}

        # Convert PTH points to 3D vertices
        for i, point in enumerate(pth):
            z = point_z.get(i, 0.0)
            vertex = Vector3(point.x, point.y, z)
            self._vertices.append(vertex)

        # Build adjacency list from PTH connections
        # PTH stores connections as edges, iterate through all points and their outgoing connections
        for i in range(len(pth)):
            outgoing_edges = pth.outgoing(i)
            if i not in self._adjacent_vertices:
                self._adjacent_vertices[i] = []

            for edge in outgoing_edges:
                target_idx = edge.target
                if target_idx not in self._adjacent_vertices:
                    self._adjacent_vertices[target_idx] = []

                # Add bidirectional connections
                if target_idx not in self._adjacent_vertices[i]:
                    self._adjacent_vertices[i].append(target_idx)
                if i not in self._adjacent_vertices[target_idx]:
                    self._adjacent_vertices[target_idx].append(i)

    def load(
        self,
        points: Sequence[tuple[float, float] | Vector3],
        connections: Sequence[tuple[int, int]] | None = None,
        point_z: dict[int, float] | None = None,
    ) -> None:
        """Load pathfinding data from raw point and connection data.

        Args:
        ----
            points: Sequence of (x, y) tuples or Vector3 objects
            connections: Optional sequence of (source_idx, target_idx) tuples
                If not provided, no connections are created
            point_z: Optional mapping of point indices to Z coordinates
                If not provided, Z coordinates default to 0.0
        """
        self._vertices = []
        self._adjacent_vertices = {}

        point_z = point_z or {}

        # Convert points to 3D vertices
        for i, point in enumerate(points):
            if isinstance(point, Vector3):
                vertex = point
            else:
                z = point_z.get(i, 0.0)
                vertex = Vector3(point[0], point[1], z)
            self._vertices.append(vertex)

        # Build adjacency list from connections
        if connections:
            for source_idx, target_idx in connections:
                if source_idx not in self._adjacent_vertices:
                    self._adjacent_vertices[source_idx] = []
                if target_idx not in self._adjacent_vertices:
                    self._adjacent_vertices[target_idx] = []

                # Add bidirectional connections
                if target_idx not in self._adjacent_vertices[source_idx]:
                    self._adjacent_vertices[source_idx].append(target_idx)
                if source_idx not in self._adjacent_vertices[target_idx]:
                    self._adjacent_vertices[target_idx].append(source_idx)

    def find_path(self, from_pos: Vector3, to_pos: Vector3) -> list[Vector3]:
        """Find a path from one position to another using A* algorithm.

        Args:
        ----
            from_pos: Starting position
            to_pos: Target position

        Returns:
        -------
            List of Vector3 positions representing the path from start to end
            If no path is found, returns a path containing only start and end points
        """
        # When there are no vertices, return a path of start and end points
        if not self._vertices:
            return [from_pos, to_pos]

        # Find vertices nearest to start and end points
        from_idx = self._get_nearest_vertex(from_pos)
        to_idx = self._get_nearest_vertex(to_pos)

        # When start and end point have a common nearest vertex, return a path of start and end point
        if from_idx == to_idx:
            return [from_pos, to_pos]

        # A* search context
        context_vertices: dict[int, PathfindingContextVertex] = {}
        open_set: set[int] = {from_idx}
        closed_set: set[int] = set()

        # Add starting vertex to context
        from_vert = PathfindingContextVertex(index=from_idx)
        context_vertices[from_idx] = from_vert

        while open_set:
            # Extract vertex with least total cost from open set
            current_idx = self._get_vertex_with_least_cost(open_set, context_vertices)
            open_set.remove(current_idx)
            closed_set.add(current_idx)

            current = context_vertices[current_idx]

            # Reconstruct path if current vertex is nearest to end point
            if current.index == to_idx:
                path: list[Vector3] = []
                idx = current.index
                while idx != -1:
                    vert = context_vertices[idx]
                    path.append(self._vertices[vert.index])
                    idx = vert.parent_index
                path.reverse()
                return path

            # Skip current vertex if it has no adjacent vertices
            adj_indices = self._adjacent_vertices.get(current.index, [])
            if not adj_indices:
                continue

            for adj_idx in adj_indices:
                # Skip adjacent vertex if it is present in closed set
                if adj_idx in closed_set:
                    continue

                # Calculate costs for adjacent vertex
                distance = current.distance + self._distance_squared(
                    self._vertices[current.index],
                    self._vertices[adj_idx],
                )
                heuristic = self._distance_squared(
                    self._vertices[adj_idx],
                    self._vertices[to_idx],
                )
                total_cost = distance + heuristic

                # Check if adjacent vertex is already in open set
                if adj_idx in open_set:
                    existing_vert = context_vertices[adj_idx]
                    # Do nothing if computed distance is greater
                    if distance > existing_vert.distance:
                        continue
                    # Update existing vertex if new path is better
                    existing_vert.parent_index = current.index
                    existing_vert.distance = distance
                    existing_vert.heuristic = heuristic
                    existing_vert.total_cost = total_cost
                else:
                    # Add new vertex to open set
                    child = PathfindingContextVertex(
                        index=adj_idx,
                        parent_index=current.index,
                        distance=distance,
                        heuristic=heuristic,
                        total_cost=total_cost,
                    )
                    context_vertices[adj_idx] = child
                    open_set.add(adj_idx)

        # Return a path of start and end points by default (no path found)
        return [from_pos, to_pos]

    def _get_nearest_vertex(self, point: Vector3) -> int:
        """Find the index of the vertex nearest to the given point.

        Args:
        ----
            point: The point to find nearest vertex for

        Returns:
        -------
            Index of the nearest vertex
        """
        nearest_idx = -1
        min_dist_sq = float("inf")

        for i, vertex in enumerate(self._vertices):
            dist_sq = self._distance_squared(point, vertex)
            if nearest_idx == -1 or dist_sq < min_dist_sq:
                nearest_idx = i
                min_dist_sq = dist_sq

        return nearest_idx

    def _get_vertex_with_least_cost(
        self,
        open_set: set[int],
        context_vertices: dict[int, PathfindingContextVertex],
    ) -> int:
        """Get the vertex index with the least total cost from the open set.

        Args:
        ----
            open_set: Set of vertex indices in the open set
            context_vertices: Dictionary mapping vertex indices to context vertices

        Returns:
        -------
            Index of the vertex with the least total cost
        """
        best_idx = -1
        best_cost = float("inf")

        for idx in open_set:
            vert = context_vertices[idx]
            if best_idx == -1 or vert.total_cost < best_cost:
                best_idx = idx
                best_cost = vert.total_cost

        return best_idx

    @staticmethod
    def _distance_squared(a: Vector3, b: Vector3) -> float:
        """Calculate squared distance between two points.

        Args:
        ----
            a: First point
            b: Second point

        Returns:
        -------
            Squared distance between the two points
        """
        dx = a.x - b.x
        dy = a.y - b.y
        dz = a.z - b.z
        return dx * dx + dy * dy + dz * dz

