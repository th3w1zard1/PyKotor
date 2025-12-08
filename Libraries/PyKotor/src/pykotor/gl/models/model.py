from __future__ import annotations

from typing import TYPE_CHECKING

import glm

from glm import mat4, vec3

if TYPE_CHECKING:
    from pykotor.gl.models.node import Node
    from pykotor.gl.scene import Scene
    from pykotor.gl.shader import Shader

class Model:
    def __init__(self, scene: Scene, root: Node):
        self._scene: Scene = scene
        self.root: Node = root

    def draw(
        self,
        shader: Shader,
        transform: mat4,
        *,
        override_texture: str | None = None,
    ):
        self.root.draw(shader, transform, override_texture)

    def find(self, name: str) -> Node | None:
        nodes: list[Node] = [self.root]
        while nodes:
            node: Node = nodes.pop()
            if node.name.lower() == name.lower():
                return node
            nodes.extend(node.children)
        return None

    def all(self) -> list[Node]:
        all_nodes: list[Node] = []
        search: list[Node] = [self.root]
        while search:
            node: Node = search.pop()
            search.extend(node.children)
            all_nodes.append(node)
        return all_nodes

    def box(self) -> tuple[vec3, vec3]:
        return self.bounds(mat4())

    def bounds(
        self,
        transform: mat4,
    ) -> tuple[vec3, vec3]:
        min_point = vec3(100000, 100000, 100000)
        max_point = vec3(-100000, -100000, -100000)
        self._bounds_rec(self.root, transform, min_point, max_point)

        min_point.x -= 0.1
        min_point.y -= 0.1
        min_point.z -= 0.1
        max_point.x += 0.1
        max_point.y += 0.1
        max_point.z += 0.1

        return min_point, max_point

    def _bounds_rec(
        self,
        node: Node,
        transform: mat4,
        min_point: vec3,
        max_point: vec3,
    ):
        local_transform = transform * glm.translate(node._position)  # noqa: SLF001
        local_transform = local_transform * glm.mat4_cast(node._rotation)  # noqa: SLF001

        if node.mesh and node.render:
            mesh_min, mesh_max = node.mesh.bounds(local_transform)
            min_point.x = min(min_point.x, mesh_min.x)
            min_point.y = min(min_point.y, mesh_min.y)
            min_point.z = min(min_point.z, mesh_min.z)
            max_point.x = max(max_point.x, mesh_max.x)
            max_point.y = max(max_point.y, mesh_max.y)
            max_point.z = max(max_point.z, mesh_max.z)

        for child in node.children:
            self._bounds_rec(child, local_transform, min_point, max_point)
