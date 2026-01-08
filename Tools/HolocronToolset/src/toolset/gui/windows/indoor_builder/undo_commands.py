from __future__ import annotations


from copy import deepcopy
from typing import Callable

import qtpy


if qtpy.QT5:
    from qtpy.QtWidgets import QUndoCommand  # type: ignore[reportPrivateImportUsage]
elif qtpy.QT6:
    from qtpy.QtGui import QUndoCommand  # type: ignore[assignment]  # pyright: ignore[reportPrivateImportUsage]
else:
    raise ValueError(f"Invalid QT_API: '{qtpy.API_NAME}'")

from pykotor.common.indoorkit import KitComponent, KitComponentHook
from pykotor.common.indoormap import EmbeddedKit, IndoorMap, IndoorMapRoom
from pykotor.resource.formats.bwm import BWM  # type: ignore[reportPrivateImportUsage]
from utility.common.geometry import SurfaceMaterial, Vector3


# =============================================================================
# Undo/Redo Commands
# =============================================================================


class AddRoomCommand(QUndoCommand):
    """Command to add a room to the map."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        room: IndoorMapRoom,
        invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = None,
    ):
        super().__init__("Add Room")
        self.indoor_map: IndoorMap = indoor_map
        self.room: IndoorMapRoom = room
        self._invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = invalidate_cb

    def undo(self):
        if self.room in self.indoor_map.rooms:
            self.indoor_map.rooms.remove(self.room)
            self.indoor_map.rebuild_room_connections()
            if self._invalidate_cb:
                self._invalidate_cb([self.room])

    def redo(self):
        if self.room not in self.indoor_map.rooms:
            self.indoor_map.rooms.append(self.room)
            self.indoor_map.rebuild_room_connections()
            if self._invalidate_cb:
                self._invalidate_cb([self.room])


class DeleteRoomsCommand(QUndoCommand):
    """Command to delete rooms from the map."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = None,
    ):
        super().__init__(f"Delete {len(rooms)} Room(s)")
        self.indoor_map: IndoorMap = indoor_map
        self.rooms: list[IndoorMapRoom] = rooms.copy()
        self._invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = invalidate_cb
        # Store indices for proper re-insertion order
        self.indices: list[int] = [indoor_map.rooms.index(r) for r in rooms if r in indoor_map.rooms]

    def undo(self):
        # Re-add rooms in original order
        for idx, room in zip(sorted(self.indices), self.rooms):
            if room not in self.indoor_map.rooms:
                self.indoor_map.rooms.insert(idx, room)
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)

    def redo(self):
        for room in self.rooms:
            if room in self.indoor_map.rooms:
                self.indoor_map.rooms.remove(room)
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)
        # NOTE: Selected hook validation should be handled by the renderer


class MoveRoomsCommand(QUndoCommand):
    """Command to move rooms."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        old_positions: list[Vector3],
        new_positions: list[Vector3],
        invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = None,
    ):
        super().__init__(f"Move {len(rooms)} Room(s)")
        self.indoor_map: IndoorMap = indoor_map
        self.rooms: list[IndoorMapRoom] = rooms.copy()
        self.old_positions: list[Vector3] = [Vector3(*p) for p in old_positions]
        self.new_positions: list[Vector3] = [Vector3(*p) for p in new_positions]
        self._invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = invalidate_cb

    def undo(self):
        for room, pos in zip(self.rooms, self.old_positions):
            room.position = Vector3(*pos)
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)

    def redo(self):
        for room, pos in zip(self.rooms, self.new_positions):
            room.position = Vector3(*pos)
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)


class RotateRoomsCommand(QUndoCommand):
    """Command to rotate rooms."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        old_rotations: list[float],
        new_rotations: list[float],
        invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = None,
    ):
        super().__init__(f"Rotate {len(rooms)} Room(s)")
        self.indoor_map: IndoorMap = indoor_map
        self.rooms: list[IndoorMapRoom] = rooms.copy()
        self.old_rotations: list[float] = old_rotations.copy()
        self.new_rotations: list[float] = new_rotations.copy()
        self._invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = invalidate_cb

    def undo(self):
        for room, rot in zip(self.rooms, self.old_rotations):
            room.rotation = rot
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)

    def redo(self):
        for room, rot in zip(self.rooms, self.new_rotations):
            room.rotation = rot
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)


class FlipRoomsCommand(QUndoCommand):
    """Command to flip rooms."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        flip_x: bool,
        flip_y: bool,
        invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = None,
    ):
        super().__init__(f"Flip {len(rooms)} Room(s)")
        self.indoor_map: IndoorMap = indoor_map
        self.rooms: list[IndoorMapRoom] = rooms.copy()
        self.flip_x: bool = flip_x
        self.flip_y: bool = flip_y
        self._invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = invalidate_cb
        # Store original states
        self.old_flip_x: list[bool] = [r.flip_x for r in rooms]
        self.old_flip_y: list[bool] = [r.flip_y for r in rooms]

    def undo(self):
        for room, fx, fy in zip(self.rooms, self.old_flip_x, self.old_flip_y):
            room.flip_x = fx
            room.flip_y = fy
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)

    def redo(self):
        for room in self.rooms:
            if self.flip_x:
                room.flip_x = not room.flip_x
            if self.flip_y:
                room.flip_y = not room.flip_y
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)


class DuplicateRoomsCommand(QUndoCommand):
    """Command to duplicate rooms."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        offset: Vector3,
        invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = None,
    ):
        super().__init__(f"Duplicate {len(rooms)} Room(s)")
        self.indoor_map: IndoorMap = indoor_map
        self.original_rooms: list[IndoorMapRoom] = rooms.copy()
        self.offset: Vector3 = offset
        self._invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = invalidate_cb
        # Create duplicates
        self.duplicates: list[IndoorMapRoom] = []
        for room in rooms:
            # Deep copy component so hooks can be edited independently
            component_copy = deepcopy(room.component)
            new_room = IndoorMapRoom(
                component_copy,
                Vector3(room.position.x + offset.x, room.position.y + offset.y, room.position.z + offset.z),
                room.rotation,
                flip_x=room.flip_x,
                flip_y=room.flip_y,
            )
            new_room.walkmesh_override = deepcopy(room.walkmesh_override) if room.walkmesh_override is not None else None
            # Initialize hooks connections list to match hooks length
            new_room.hooks = [None] * len(component_copy.hooks)
            self.duplicates.append(new_room)

    def undo(self):
        for room in self.duplicates:
            if room in self.indoor_map.rooms:
                self.indoor_map.rooms.remove(room)
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.duplicates)

    def redo(self):
        for room in self.duplicates:
            if room not in self.indoor_map.rooms:
                self.indoor_map.rooms.append(room)
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.duplicates)


class MoveWarpCommand(QUndoCommand):
    """Command to move the warp point."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        old_position: Vector3,
        new_position: Vector3,
    ):
        super().__init__("Move Warp Point")
        self.indoor_map: IndoorMap = indoor_map
        self.old_position: Vector3 = Vector3(*old_position)
        self.new_position: Vector3 = Vector3(*new_position)

    def undo(self):
        self.indoor_map.warp_point = Vector3(*self.old_position)

    def redo(self):
        self.indoor_map.warp_point = Vector3(*self.new_position)


class PaintWalkmeshCommand(QUndoCommand):
    """Command to apply material changes to walkmesh faces."""

    def __init__(
        self,
        rooms: list[IndoorMapRoom],
        face_indices: list[int],
        old_materials: list[SurfaceMaterial],
        new_materials: list[SurfaceMaterial],
        invalidate_cb: Callable[[list[IndoorMapRoom]], None],
    ):
        super().__init__(f"Paint {len(face_indices)} Face(s)")
        self.rooms: list[IndoorMapRoom] = rooms
        self.face_indices: list[int] = face_indices
        self.old_materials: list[SurfaceMaterial] = old_materials
        self.new_materials: list[SurfaceMaterial] = new_materials
        self._invalidate_cb: Callable[[list[IndoorMapRoom]], None] = invalidate_cb

    def _apply(self, materials: list[SurfaceMaterial]):
        for room, face_index, material in zip(self.rooms, self.face_indices, materials):
            # Ensure we have a writable walkmesh override
            if room.walkmesh_override is None:
                room.walkmesh_override = deepcopy(room.component.bwm)
            base_bwm = room.walkmesh_override
            if 0 <= face_index < len(base_bwm.faces):
                base_bwm.faces[face_index].material = material
        self._invalidate_cb(self.rooms)

    def undo(self):
        self._apply(self.old_materials)

    def redo(self):
        self._apply(self.new_materials)


class ResetWalkmeshCommand(QUndoCommand):
    """Command to reset walkmesh overrides for rooms."""

    def __init__(
        self,
        rooms: list[IndoorMapRoom],
        invalidate_cb: Callable[[list[IndoorMapRoom]], None],
    ):
        super().__init__(f"Reset Walkmesh ({len(rooms)} Room(s))")
        self.rooms: list[IndoorMapRoom] = rooms
        self._invalidate_cb: Callable[[list[IndoorMapRoom]], None] = invalidate_cb
        self._previous_overrides: list[BWM | None] = [None if room.walkmesh_override is None else deepcopy(room.walkmesh_override) for room in rooms]

    def undo(self):
        for room, previous in zip(self.rooms, self._previous_overrides):
            room.walkmesh_override = None if previous is None else deepcopy(previous)
        self._invalidate_cb(self.rooms)

    def redo(self):
        for room in self.rooms:
            # Clear walkmesh override by setting it to None
            room.walkmesh_override = None
        self._invalidate_cb(self.rooms)


class MergeRoomsCommand(QUndoCommand):
    """Command to merge multiple rooms into a single room.

    This creates a new room with:
    - A merged walkmesh (BWM) combining all source room geometries
    - Combined hooks from all source rooms (translated to merged coordinate space)
    - The first source room's MDL/MDX as visual (not ideal but functional)
    - Position at the centroid of all source rooms

    The merged room is treated as a single entity for selection, manipulation, and export.
    Internal hooks between merged rooms are removed; only external hooks are preserved.
    """

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        embedded_kit: EmbeddedKit,
        invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = None,
    ):
        super().__init__(f"Merge {len(rooms)} Room(s)")
        self.indoor_map: IndoorMap = indoor_map
        self.original_rooms: list[IndoorMapRoom] = rooms.copy()
        self.embedded_kit: EmbeddedKit = embedded_kit
        self._invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = invalidate_cb
        # Snapshot ordering for fully idempotent undo/redo.
        self._before_rooms: list[IndoorMapRoom] = indoor_map.rooms.copy()
        self._merge_indices: list[int] = [self._before_rooms.index(r) for r in rooms if r in self._before_rooms]
        if len(self._merge_indices) < 2:
            raise ValueError("Cannot merge: fewer than 2 selected rooms are present in the map.")
        self._insert_index: int = min(self._merge_indices)

        # Create the merged room
        self.merged_room: IndoorMapRoom = self._create_merged_room(rooms)
        after_rooms: list[IndoorMapRoom] = [r for r in self._before_rooms if r not in self.original_rooms]
        after_rooms.insert(self._insert_index, self.merged_room)
        self._after_rooms: list[IndoorMapRoom] = after_rooms

    def _create_merged_room(self, rooms: list[IndoorMapRoom]) -> IndoorMapRoom:
        """Create a single merged room from multiple source rooms."""
        if not rooms:
            raise ValueError("Cannot merge zero rooms")

        # 1. Calculate centroid position (this will be the merged room's position)
        centroid = Vector3(
            sum(r.position.x for r in rooms) / len(rooms),
            sum(r.position.y for r in rooms) / len(rooms),
            sum(r.position.z for r in rooms) / len(rooms),
        )

        # 2. Merge walkmeshes (BWMs) from all rooms
        merged_bwm: BWM = self._merge_bwms(rooms, centroid)

        # 3. Create a new merged KitComponent
        merged_component: KitComponent = self._create_merged_component(rooms, merged_bwm, centroid)

        # 4. Create the merged room at centroid position with no rotation/flip
        merged_room = IndoorMapRoom(
            merged_component,
            centroid,
            rotation=0.0,
            flip_x=False,
            flip_y=False,
        )
        # Initialize hooks list to match component hooks
        merged_room.hooks = [None] * len(merged_component.hooks)

        return merged_room

    def _merge_bwms(self, rooms: list[IndoorMapRoom], centroid: Vector3) -> BWM:
        """Merge walkmeshes from all rooms into a single BWM.

        Each room's walkmesh is transformed to world coordinates, then translated
        to be relative to the centroid position. This ensures the merged BWM is
        centered at the origin (relative to the new room position).

        Internal transitions between merged rooms are cleared since those room
        boundaries no longer exist.
        """
        from pykotor.resource.formats.bwm import BWMFace  # noqa: PLC0415

        merged_bwm = BWM()

        for room in rooms:
            # Get the room's walkmesh transformed to world coordinates
            # This applies position, rotation, and flip transforms
            world_bwm: BWM = room.walkmesh()

            # Copy each face, translating from world coords to centroid-local coords
            for face in world_bwm.faces:
                # Create a new face with vertices relative to centroid
                new_v1 = Vector3(face.v1.x - centroid.x, face.v1.y - centroid.y, face.v1.z - centroid.z)
                new_v2 = Vector3(face.v2.x - centroid.x, face.v2.y - centroid.y, face.v2.z - centroid.z)
                new_v3 = Vector3(face.v3.x - centroid.x, face.v3.y - centroid.y, face.v3.z - centroid.z)

                new_face = BWMFace(new_v1, new_v2, new_v3)
                new_face.material = face.material

                # Clear internal transitions - they reference old room structure
                # External transitions would need remapping but that's complex;
                # for now we clear all transitions
                new_face.trans1 = None
                new_face.trans2 = None
                new_face.trans3 = None

                merged_bwm.faces.append(new_face)

        # Copy hook positions from first room's BWM (these are metadata positions)
        if rooms and rooms[0].component.bwm:
            first_bwm = rooms[0].component.bwm
            merged_bwm.position = Vector3(0.0, 0.0, 0.0)
            merged_bwm.relative_hook1 = deepcopy(first_bwm.relative_hook1)
            merged_bwm.relative_hook2 = deepcopy(first_bwm.relative_hook2)
            merged_bwm.absolute_hook1 = deepcopy(first_bwm.absolute_hook1)
            merged_bwm.absolute_hook2 = deepcopy(first_bwm.absolute_hook2)

        return merged_bwm

    def _create_merged_component(
        self,
        rooms: list[IndoorMapRoom],
        merged_bwm: BWM,
        centroid: Vector3,
    ) -> KitComponent:
        """Create a new KitComponent for the merged room.

        Uses the first room's MDL/MDX for visuals (in-game rendering) and the
        merged BWM for collision/walkmesh. Hooks from all source rooms are
        combined, with positions translated to the new local coordinate space.
        Hooks that were internal (connecting merged rooms to each other) are
        excluded since those boundaries no longer exist.
        """
        # Use the first room's component as the base for MDL/MDX payloads
        first_room = rooms[0]
        first_component = first_room.component

        # Deterministic id/name derived from original room indices in map ordering.
        idxs = sorted(self._merge_indices)
        base_id = f"merge_{self.indoor_map.module_id}_{idxs[0]}_{idxs[-1]}_{len(idxs)}"
        existing_ids = {c.id for c in self.embedded_kit.components}
        unique_id = base_id
        suffix = 1
        while unique_id in existing_ids:
            suffix += 1
            unique_id = f"{base_id}_{suffix}"

        merged_component = KitComponent(
            kit=self.embedded_kit,
            name=f"Merged ({len(rooms)} rooms)",
            component_id=unique_id,
            bwm=merged_bwm,
            mdl=bytes(first_component.mdl),  # bytes() ensures no accidental shared buffer
            mdx=bytes(first_component.mdx),
        )

        # Collect external hooks from all rooms
        # A hook is "external" if it doesn't connect to another room in the merge set
        rooms_set = set(rooms)
        for room in rooms:
            for hook_idx, hook in enumerate(room.component.hooks):
                # Check if this hook connects to a room being merged (internal)
                connected_room = room.hooks[hook_idx] if hook_idx < len(room.hooks) else None
                is_internal = connected_room in rooms_set

                if not is_internal:
                    # Transform hook position from room-local to world, then to centroid-local
                    world_hook_pos: Vector3 = room.hook_position(hook, world_offset=True)
                    local_hook_pos = Vector3(
                        world_hook_pos.x - centroid.x,
                        world_hook_pos.y - centroid.y,
                        world_hook_pos.z - centroid.z,
                    )

                    # Adjust hook rotation by room rotation
                    adjusted_rotation = (hook.rotation + room.rotation) % 360

                    # Create new hook in merged component's local space
                    new_hook = KitComponentHook(
                        position=local_hook_pos,
                        rotation=adjusted_rotation,
                        edge=hook.edge,  # Edge index doesn't translate directly but we preserve it
                        door=hook.door,
                    )
                    merged_component.hooks.append(new_hook)

        return merged_component

    def undo(self):
        self.indoor_map.rooms = self._before_rooms.copy()

        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb([self.merged_room] + self.original_rooms)

    def redo(self):
        self.indoor_map.rooms = self._after_rooms.copy()

        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb([self.merged_room] + self.original_rooms)
