from __future__ import annotations

import math

from dataclasses import dataclass
from copy import deepcopy
from typing import TYPE_CHECKING, Callable

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QPoint, QPointF, QRectF, QTimer, Qt
from qtpy.QtGui import QColor, QImage, QKeyEvent, QMouseEvent, QPainter, QPainterPath, QPen, QTransform, QWheelEvent
from qtpy.QtWidgets import (
    QApplication,
    QWidget,
)


if qtpy.QT5:
    from qtpy.QtGui import QCloseEvent, QPaintEvent
    from qtpy.QtWidgets import QUndoStack  # type: ignore[reportPrivateImportUsage]
elif qtpy.QT6:
    from qtpy.QtGui import QPaintEvent, QUndoStack  # type: ignore[assignment]  # pyright: ignore[reportPrivateImportUsage]

    try:
        from qtpy.QtGui import QCloseEvent
    except ImportError:
        # Fallback for Qt6 where QCloseEvent may be in QtCore
        from qtpy.QtCore import QCloseEvent  # type: ignore[assignment, attr-defined, no-redef]
else:
    raise ValueError(f"Invalid QT_API: '{qtpy.API_NAME}'")

from pykotor.common.indoorkit import KitComponent, KitComponentHook
from pykotor.common.indoormap import IndoorMap, IndoorMapRoom
from pykotor.resource.formats.bwm import BWM  # type: ignore[reportPrivateImportUsage]
from toolset.gui.windows.indoor_builder.builder import SnapResult
from toolset.gui.windows.indoor_builder.constants import (
    BACKGROUND_COLOR,
    COMPONENT_PREVIEW_SCALE,
    CONNECTION_LINE_COLOR,
    CONNECTION_LINE_WIDTH_SCALE,
    CURSOR_HOOK_ALPHA,
    CURSOR_PREVIEW_ALPHA,
    DEFAULT_CAMERA_POSITION_X,
    DEFAULT_CAMERA_POSITION_Y,
    DEFAULT_CAMERA_ROTATION,
    DEFAULT_CAMERA_ZOOM,
    DEFAULT_GRID_SIZE,
    DEFAULT_ROTATION_SNAP,
    GRID_COLOR,
    GRID_PEN_WIDTH,
    HOOK_COLOR_CONNECTED,
    HOOK_COLOR_SELECTED,
    HOOK_COLOR_UNCONNECTED,
    HOOK_CONNECTION_THRESHOLD,
    HOOK_DISPLAY_RADIUS,
    HOOK_HOVER_RADIUS,
    HOOK_PEN_COLOR_CONNECTED,
    HOOK_PEN_COLOR_SELECTED,
    HOOK_PEN_COLOR_UNCONNECTED,
    HOOK_SELECTED_RADIUS,
    HOOK_SNAP_BASE_THRESHOLD,
    HOOK_SNAP_DISCONNECT_BASE_THRESHOLD,
    HOOK_SNAP_DISCONNECT_SCALE_FACTOR,
    HOOK_SNAP_SCALE_FACTOR,
    MARQUEE_BORDER_COLOR,
    MARQUEE_FILL_COLOR,
    MARQUEE_MOVE_THRESHOLD_PIXELS,
    MAX_CAMERA_ZOOM,
    MIN_CAMERA_ZOOM,
    POSITION_CHANGE_EPSILON,
    RENDER_INTERVAL_MS,
    ROOM_HOVER_ALPHA,
    ROOM_HOVER_COLOR,
    ROOM_SELECTED_ALPHA,
    ROOM_SELECTED_COLOR,
    SNAP_INDICATOR_ALPHA,
    SNAP_INDICATOR_COLOR,
    SNAP_INDICATOR_PEN_WIDTH,
    SNAP_INDICATOR_RADIUS,
    WARP_POINT_ACTIVE_SCALE,
    WARP_POINT_ALPHA_ACTIVE,
    WARP_POINT_ALPHA_NORMAL,
    WARP_POINT_COLOR,
    WARP_POINT_CROSSHAIR_SCALE,
    WARP_POINT_PEN_WIDTH_ACTIVE,
    WARP_POINT_PEN_WIDTH_NORMAL,
    WARP_POINT_RADIUS,
    DragMode,
)
from utility.common.geometry import SurfaceMaterial, Vector2, Vector3

if TYPE_CHECKING:
    from qtpy.QtGui import QFocusEvent

    from pykotor.resource.formats.bwm import BWMFace  # pyright: ignore[reportMissingImports]


# =============================================================================
# Renderer caches (performance-critical)
# =============================================================================


@dataclass(frozen=True)
class _BWMSurfaceCache:
    """Precomputed geometry for a BWM in *local* space.

    This cache exists to avoid rebuilding transformed BWMs (deepcopy + rotate/flip/translate)
    on every mouse move / repaint. Transforming is handled by the painter + cheap math.
    """

    bwm_obj_id: int
    face_paths: list[QPainterPath]
    face_id_to_index: dict[int, int]
    # Unique vertex list for operations like marquee selection (local space).
    vertices: list[Vector3]
    # Local-space AABB for cheap early-out in picking.
    bbmin: Vector3
    bbmax: Vector3


# =============================================================================
# Renderer Widget
# =============================================================================


class IndoorMapRenderer(QWidget):
    sig_mouse_moved = QtCore.Signal(object, object, object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_mouse_scrolled = QtCore.Signal(object, object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_mouse_released = QtCore.Signal(object, object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_mouse_pressed = QtCore.Signal(object, object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_mouse_double_clicked = QtCore.Signal(object, object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_rooms_moved = QtCore.Signal(object, object, object)  # rooms, old_positions, new_positions  # pyright: ignore[reportPrivateImportUsage]
    sig_rooms_rotated = QtCore.Signal(object, object, object)  # rooms, old_rotations, new_rotations  # pyright: ignore[reportPrivateImportUsage]
    sig_warp_moved = QtCore.Signal(object, object)  # old_position, new_position  # pyright: ignore[reportPrivateImportUsage]
    sig_marquee_select = QtCore.Signal(object, object)  # rooms selected, additive  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self._map: IndoorMap = IndoorMap()
        self._undo_stack: QUndoStack | None = None
        self._under_mouse_room: IndoorMapRoom | None = None
        self._selected_rooms: list[IndoorMapRoom] = []

        # Camera
        self._cam_position: Vector2 = Vector2(DEFAULT_CAMERA_POSITION_X, DEFAULT_CAMERA_POSITION_Y)
        self._cam_rotation: float = DEFAULT_CAMERA_ROTATION
        self._cam_scale: float = DEFAULT_CAMERA_ZOOM

        # Cursor/placement state
        self.cursor_component: KitComponent | None = None
        self.cursor_point: Vector3 = Vector3.from_null()
        self.cursor_rotation: float = 0.0
        self.cursor_flip_x: bool = False
        self.cursor_flip_y: bool = False

        # Input state
        self._keys_down: set[int | Qt.Key] = set()
        self._mouse_down: set[int | Qt.MouseButton] = set()
        self._mouse_prev: Vector2 = Vector2.from_null()

        # Drag state
        self._dragging: bool = False
        self._drag_start_positions: list[Vector3] = []
        self._drag_start_rotations: list[float] = []
        self._drag_rooms: list[IndoorMapRoom] = []
        self._drag_mode: DragMode = DragMode.NONE

        # Snap state during drag (for soft snapping)
        self._snap_anchor_position: Vector3 | None = None  # Position where snap was first applied
        # Keep snaps easy to separate: small disconnect threshold, scaled later
        self._snap_disconnect_threshold: float = 1.0  # base units before scaling

        # Hook editing state
        self._selected_hook: tuple[IndoorMapRoom, int] | None = None
        self._dragging_hook: bool = False
        self._drag_hook_start: Vector3 = Vector3.from_null()

        # Marquee selection state
        self._marquee_active: bool = False
        self._marquee_start: Vector2 = Vector2.from_null()
        self._marquee_end: Vector2 = Vector2.from_null()

        # Warp point drag state
        self._dragging_warp: bool = False
        self._warp_drag_start: Vector3 = Vector3.from_null()

        # Snapping options
        self.snap_to_grid: bool = False
        self.snap_to_hooks: bool = True
        self.grid_size: float = DEFAULT_GRID_SIZE
        self.rotation_snap: float = float(DEFAULT_ROTATION_SNAP)

        # Visual options
        self.hide_magnets: bool = False
        self.show_grid: bool = False
        self.highlight_rooms_hover: bool = True

        # Snap visualization
        self._snap_indicator: SnapResult | None = None

        # Performance: dirty flag for rendering
        self._dirty: bool = True
        # NOTE: We no longer cache *transformed* room walkmeshes (they require deepcopy + transforms).
        # Instead we cache BWM face paths/indices in local space and apply transforms cheaply.
        self._bwm_surface_cache: dict[int, _BWMSurfaceCache] = {}

        # Warp point hover detection
        self._hovering_warp: bool = False
        self.warp_point_radius: float = WARP_POINT_RADIUS

        # Status callback (set by parent window)
        self._status_callback = None

        # Walkmesh visualization
        self._material_colors: dict[SurfaceMaterial, QColor] = {}
        self._colorize_materials: bool = False
        # Walkable materials - must match SurfaceMaterial.walkable() exactly (see geometry.py)
        # Using SurfaceMaterial enum values for clarity and maintainability
        self._walkable_values: set[SurfaceMaterial] = {
            SurfaceMaterial.DIRT,
            SurfaceMaterial.GRASS,
            SurfaceMaterial.STONE,
            SurfaceMaterial.WOOD,
            SurfaceMaterial.WATER,
            SurfaceMaterial.CARPET,
            SurfaceMaterial.METAL,
            SurfaceMaterial.PUDDLES,
            SurfaceMaterial.SWAMP,
            SurfaceMaterial.MUD,
            SurfaceMaterial.LEAVES,
            SurfaceMaterial.DOOR,
            SurfaceMaterial.TRIGGER,
        }

        # Render loop control - use QTimer instead of recursive singleShot
        self._render_timer: QTimer = QTimer(self)
        self._render_timer.timeout.connect(self._on_render_timer)
        self._render_timer.setInterval(RENDER_INTERVAL_MS)
        self._render_timer.start()

        # Connect to destroyed signal as safety mechanism
        # This ensures the loop stops immediately when widget is destroyed
        self.destroyed.connect(self._on_destroyed)

    def _on_destroyed(self):
        """Called when widget is destroyed - ensures loop stops."""
        if hasattr(self, "_render_timer"):
            self._render_timer.stop()

    def _on_render_timer(self):
        """Timer callback for render loop - only repaint when dirty.

        Uses QTimer instead of recursive singleShot for better performance
        and proper resource management.
        """
        # Safety check: validate widget is still valid
        try:
            if not self.isVisible() and self.parent() is None:
                self._render_timer.stop()
                return
        except RuntimeError:
            # Widget is in process of destruction
            self._render_timer.stop()
            return

        # Perform repaint only if dirty or actively dragging/placing
        try:
            if self._dirty or self._dragging or self.cursor_component is not None:
                self.repaint()
                self._dirty = False
        except (RuntimeError, AttributeError):
            # Widget may be in process of destruction
            self._render_timer.stop()

    def mark_dirty(self):
        """Mark the renderer as needing a repaint."""
        self._dirty = True

    def set_map(self, indoor_map: IndoorMap):
        self._map = indoor_map
        self._bwm_surface_cache.clear()
        self.mark_dirty()

    def set_undo_stack(self, undo_stack: QUndoStack):
        self._undo_stack = undo_stack

    def set_cursor_component(self, component: KitComponent | None):
        self.cursor_component = component
        self.mark_dirty()

    def set_status_callback(self, callback: Callable[[QPoint | Vector2 | None, set[int | Qt.MouseButton], set[int | Qt.Key]], None] | None) -> None:
        self._status_callback = callback  # type: ignore[assignment]  # pyright: ignore[reportAssignmentType]

    def select_room(self, room: IndoorMapRoom, *, clear_existing: bool):
        if clear_existing:
            self._selected_rooms.clear()
        if room in self._selected_rooms:
            self._selected_rooms.remove(room)
        self._selected_rooms.append(room)
        self.mark_dirty()

    def select_rooms(self, rooms: list[IndoorMapRoom], *, clear_existing: bool = True):
        """Select multiple rooms at once."""
        if clear_existing:
            self._selected_rooms.clear()
        for room in rooms:
            if room in self._selected_rooms:
                self._selected_rooms.remove(room)
            self._selected_rooms.append(room)
        self.mark_dirty()

    def room_under_mouse(self) -> IndoorMapRoom | None:
        return self._under_mouse_room

    def is_dragging_rooms(self) -> bool:
        return self._dragging and self._drag_mode == DragMode.ROOMS

    def selected_hook(self) -> tuple[IndoorMapRoom, int] | None:
        return self._selected_hook

    def hook_under_mouse(
        self,
        world: Vector3,
        *,
        radius: float = HOOK_HOVER_RADIUS,
    ) -> tuple[IndoorMapRoom, int] | None:
        """Return (room, hook_index) if a hook is under the given world position."""
        for room in reversed(self._map.rooms):
            for idx, hook in enumerate(room.component.hooks):
                hook_pos = room.hook_position(hook)
                if Vector2.from_vector3(hook_pos).distance(Vector2.from_vector3(world)) <= radius:
                    return room, idx
        return None

    def selected_rooms(self) -> list[IndoorMapRoom]:
        return self._selected_rooms

    def clear_selected_rooms(self):
        self._selected_rooms.clear()
        self.mark_dirty()

    def rotate_drag_selection(self, delta_y: float):
        """Rotate currently dragged rooms using mouse wheel delta."""
        if not self.is_dragging_rooms() or not self._drag_rooms:
            return
        step = math.copysign(self.rotation_snap, delta_y)
        for room in self._drag_rooms:
            room.rotation = (room.rotation + step) % 360
        # NOTE: Don't rebuild_room_connections() during drag - it's O(n²) and kills perf.
        # Connections are rebuilt in RotateRoomsCommand.redo() when drag ends.
        self.mark_dirty()

    def clear_selected_hook(self):
        self._selected_hook = None
        self.mark_dirty()

    def _validate_selected_hook(self):
        """Validate that the selected hook is still valid (room exists and hook index is valid)."""
        if self._selected_hook is None:
            return
        room, hook_index = self._selected_hook
        # Check if room still exists in map
        if room not in self._map.rooms:
            self._selected_hook = None
            self.mark_dirty()
            return
        # Check if hook index is still valid
        if hook_index < 0 or hook_index >= len(room.component.hooks):
            self._selected_hook = None
            self.mark_dirty()

    def select_hook(
        self,
        room: IndoorMapRoom,
        hook_index: int,
        *,
        clear_existing: bool,
    ):
        # Validate hook index
        if hook_index < 0 or hook_index >= len(room.component.hooks):
            return
        if clear_existing:
            self._selected_rooms.clear()
        self._selected_hook = (room, hook_index)
        self.mark_dirty()

    def set_material_colors(self, material_colors: dict[SurfaceMaterial, QColor]):
        self._material_colors = material_colors
        self.mark_dirty()

    def set_colorize_materials(self, enabled: bool):
        self._colorize_materials = enabled
        self.mark_dirty()

    def set_snap_to_grid(self, enabled: bool):
        self.snap_to_grid = enabled
        self.mark_dirty()

    def set_snap_to_hooks(self, enabled: bool):
        self.snap_to_hooks = enabled
        self.mark_dirty()

    def set_show_grid(self, enabled: bool):
        self.show_grid = enabled
        self.mark_dirty()

    def set_hide_magnets(self, enabled: bool):
        self.hide_magnets = enabled
        self.mark_dirty()

    def set_grid_size(self, size: float):
        self.grid_size = size
        self.mark_dirty()

    def set_rotation_snap(self, snap: float):
        self.rotation_snap = snap
        self.mark_dirty()

    def invalidate_rooms(self, rooms: list[IndoorMapRoom]):
        # Geometry caches are keyed by the BWM object id and are safe to keep across
        # room transforms (position/rotation/flip). Most invalidations are UI-driven.
        # Validate selected hook in case the room was deleted or modified
        self._validate_selected_hook()
        self.mark_dirty()

    def pick_face(self, world: Vector3) -> tuple[IndoorMapRoom | None, int | None]:
        """Return the room and *base-walkmesh* face index under the given world position.

        Performance:
        - Avoids `IndoorMapRoom.walkmesh()` which deepcopies + transforms the full mesh.
        - Uses cheap world->local math and tests against the base walkmesh in local space.
        """
        for room in reversed(self._map.rooms):
            base_bwm = room.base_walkmesh()
            cache = self._get_bwm_surface_cache(base_bwm)
            local = self._world_to_room_local(room, world)
            # Cheap AABB reject before O(n_faces) point-in-triangle scan.
            if local.x < cache.bbmin.x or local.x > cache.bbmax.x or local.y < cache.bbmin.y or local.y > cache.bbmax.y:
                continue
            face = base_bwm.faceAt(local.x, local.y)
            if face is None:
                continue
            face_index = cache.face_id_to_index.get(id(face))
            if face_index is None:
                # Fallback (should be rare): identity-based scan.
                for idx, candidate in enumerate(base_bwm.faces):
                    if candidate is face:
                        face_index = idx
                        break
            if face_index is not None:
                return room, face_index
        return None, None

    # =========================================================================
    # Coordinate conversions
    # =========================================================================

    def to_render_coords(self, x: float, y: float) -> Vector2:
        cos = math.cos(self._cam_rotation)
        sin = math.sin(self._cam_rotation)
        x -= self._cam_position.x
        y -= self._cam_position.y
        x2 = (x * cos - y * sin) * self._cam_scale + self.width() / 2
        y2 = (x * sin + y * cos) * self._cam_scale + self.height() / 2
        return Vector2(x2, y2)

    def to_world_coords(self, x: float, y: float) -> Vector3:
        cos = math.cos(-self._cam_rotation)
        sin = math.sin(-self._cam_rotation)
        x = (x - self.width() / 2) / self._cam_scale
        y = (y - self.height() / 2) / self._cam_scale
        x2 = x * cos - y * sin + self._cam_position.x
        y2 = x * sin + y * cos + self._cam_position.y
        return Vector3(x2, y2, 0)

    def to_world_delta(self, x: float, y: float) -> Vector2:
        cos = math.cos(-self._cam_rotation)
        sin = math.sin(-self._cam_rotation)
        x /= self._cam_scale
        y /= self._cam_scale
        x2 = x * cos - y * sin
        y2 = x * sin + y * cos
        return Vector2(x2, y2)

    # =========================================================================
    # Snapping
    # =========================================================================

    def _snap_to_grid(self, pos: Vector3) -> Vector3:
        """Snap position to grid."""
        if not self.snap_to_grid:
            return pos
        return Vector3(
            round(pos.x / self.grid_size) * self.grid_size,
            round(pos.y / self.grid_size) * self.grid_size,
            pos.z,
        )

    def _find_hook_snap(
        self,
        room: IndoorMapRoom | None,
        position: Vector3,
        component: KitComponent | None = None,
        rotation: float = 0.0,
        flip_x: bool = False,
        flip_y: bool = False,
    ) -> SnapResult:
        """Find if position can snap to a hook on existing rooms.

        This checks ALL possible hook pairs between the room being placed/dragged
        and existing rooms, calculating the snap position for each pair and
        returning the closest one within the snap threshold.
        """
        if not self.snap_to_hooks:
            return SnapResult(position=position, snapped=False)

        # Create a temporary room to test snapping
        if component is None and room is not None:
            component = room.component
            rotation = room.rotation
            flip_x = room.flip_x
            flip_y = room.flip_y

        if component is None:
            return SnapResult(position=position, snapped=False)

        # Create fake room for hook position calculations
        test_room = IndoorMapRoom(component, position, rotation, flip_x=flip_x, flip_y=flip_y)

        best_distance = float("inf")
        best_snap: SnapResult = SnapResult(position=position, snapped=False)
        # Snap threshold scales with zoom - reduced to keep snaps helpful but separable
        snap_threshold = max(HOOK_SNAP_BASE_THRESHOLD, HOOK_SNAP_SCALE_FACTOR / self._cam_scale)

        for existing_room in self._map.rooms:
            if room is not None and existing_room is room:
                continue
            if existing_room in self._selected_rooms:
                continue

            # Check ALL hook pairs for potential snap positions
            for test_hook in test_room.component.hooks:
                test_hook_local = test_room.hook_position(test_hook, world_offset=False)

                for existing_hook in existing_room.component.hooks:
                    existing_hook_world = existing_room.hook_position(existing_hook)

                    # Calculate where test_room would need to be positioned
                    # so that test_hook aligns with existing_hook
                    snapped_pos = Vector3(
                        existing_hook_world.x - test_hook_local.x,
                        existing_hook_world.y - test_hook_local.y,
                        existing_hook_world.z - test_hook_local.z,
                    )

                    distance = Vector2.from_vector3(position).distance(Vector2.from_vector3(snapped_pos))
                    if distance < snap_threshold and distance < best_distance:
                        best_distance = distance
                        best_snap = SnapResult(
                            position=snapped_pos,
                            snapped=True,
                            hook_from=test_hook,
                            hook_to=existing_hook,
                            target_room=existing_room,
                        )

        return best_snap

    def get_connected_hooks(
        self,
        room1: IndoorMapRoom,
        room2: IndoorMapRoom,
    ) -> tuple[KitComponentHook | None, KitComponentHook | None]:
        """Get connected hooks between two rooms."""
        hook1: KitComponentHook | None = None
        hook2: KitComponentHook | None = None

        for hook in room1.component.hooks:
            hook_pos = room1.hook_position(hook)
            for other_hook in room2.component.hooks:
                other_hook_pos = room2.hook_position(other_hook)
                distance_2d = Vector2.from_vector3(hook_pos).distance(Vector2.from_vector3(other_hook_pos))
                if distance_2d < HOOK_CONNECTION_THRESHOLD:
                    hook1 = hook
                    hook2 = other_hook

        return hook1, hook2

    def toggle_cursor_flip(self):
        if self.cursor_flip_x:
            self.cursor_flip_x = False
            self.cursor_flip_y = True
        elif self.cursor_flip_y:
            self.cursor_flip_x = False
            self.cursor_flip_y = False
        else:
            self.cursor_flip_x = True
            self.cursor_flip_y = False
        self.mark_dirty()

    def keys_down(self) -> set[int | Qt.Key]:
        return set(self._keys_down)

    def mouse_down(self) -> set[int | Qt.MouseButton]:
        return set(self._mouse_down)

    # =========================================================================
    # Drag operations
    # =========================================================================

    def start_drag(self, room: IndoorMapRoom):
        """Start dragging selected rooms.

        If the room is not in the selection, it will be added first.
        This ensures clicking on any room can start a drag.
        """
        # Ensure the room is in the selection (add it if not)
        if room not in self._selected_rooms:
            self._selected_rooms.append(room)

        # Now start the drag
        self._dragging = True
        self._drag_mode = DragMode.ROOMS
        self._drag_rooms = self._selected_rooms.copy()
        self._drag_start_positions = [Vector3(*r.position) for r in self._drag_rooms]
        self._drag_start_rotations = [r.rotation for r in self._drag_rooms]

        # Check if room is currently snapped and record snap anchor for soft snapping
        if self.snap_to_hooks and room:
            snap_result = self._find_hook_snap(room, room.position)
            if snap_result.snapped:
                # Check if room is actually at the snap position (within small threshold)
                distance_to_snap = Vector2.from_vector3(room.position).distance(Vector2.from_vector3(snap_result.position))
                # Use same threshold as _find_hook_snap for consistency
                snap_threshold = max(HOOK_SNAP_BASE_THRESHOLD, HOOK_SNAP_SCALE_FACTOR / self._cam_scale)
                if distance_to_snap <= snap_threshold:
                    # Room is snapped - record the snap anchor
                    self._snap_anchor_position = Vector3(*snap_result.position)
                else:
                    # Not actually snapped
                    self._snap_anchor_position = None
            else:
                self._snap_anchor_position = None
        else:
            self._snap_anchor_position = None

        self.mark_dirty()

    def start_warp_drag(self):
        """Start dragging the warp point."""
        self._dragging_warp = True
        self._drag_mode = DragMode.WARP
        self._warp_drag_start = Vector3(*self._map.warp_point)

    def start_marquee(self, screen_pos: Vector2):
        """Start marquee selection."""
        self._marquee_active = True
        self._drag_mode = DragMode.MARQUEE
        self._marquee_start = screen_pos
        self._marquee_end = screen_pos

    def end_drag(self):
        """End dragging and emit appropriate signal.

        CRITICAL: This MUST be called on mouse release to stop ALL drag operations.
        """
        # Handle room dragging
        if self._dragging:
            self._dragging = False
            if self._drag_rooms:
                new_positions = [Vector3(*r.position) for r in self._drag_rooms]
                self.sig_rooms_moved.emit(self._drag_rooms, self._drag_start_positions, new_positions)
                new_rotations = [r.rotation for r in self._drag_rooms]
                if self._drag_start_rotations:
                    self.sig_rooms_rotated.emit(self._drag_rooms, self._drag_start_rotations, new_rotations)
            self._drag_rooms = []
            self._drag_start_positions = []
            self._drag_start_rotations = []
            self._snap_indicator = None
            self._snap_anchor_position = None

        # Handle warp point dragging
        if self._dragging_warp:
            self._dragging_warp = False
            new_pos = Vector3(*self._map.warp_point)
            if self._warp_drag_start.distance(new_pos) > POSITION_CHANGE_EPSILON:
                self.sig_warp_moved.emit(self._warp_drag_start, new_pos)

        # Handle marquee selection - ALWAYS clear if active
        if self._marquee_active:
            self._marquee_active = False
            # Only select rooms if marquee actually moved (not just a click)
            marquee_moved = self._marquee_start.distance(self._marquee_end) > MARQUEE_MOVE_THRESHOLD_PIXELS
            if marquee_moved:
                # Select rooms within marquee
                rooms_in_marquee = self._get_rooms_in_marquee()
                additive = Qt.Key.Key_Shift in self._keys_down
                self.sig_marquee_select.emit(rooms_in_marquee, additive)

        # CRITICAL: Always reset drag mode to NONE
        self._drag_mode = DragMode.NONE
        self.mark_dirty()

    def _get_rooms_in_marquee(self) -> list[IndoorMapRoom]:
        """Get all rooms that intersect with the marquee rectangle.

        Uses cached local-space vertices and transforms to world space for testing.
        This avoids deepcopying geometry on every frame.
        """
        # Convert screen coords to world coords
        start_world = self.to_world_coords(self._marquee_start.x, self._marquee_start.y)
        end_world = self.to_world_coords(self._marquee_end.x, self._marquee_end.y)

        min_x = min(start_world.x, end_world.x)
        max_x = max(start_world.x, end_world.x)
        min_y = min(start_world.y, end_world.y)
        max_y = max(start_world.y, end_world.y)

        selected: list[IndoorMapRoom] = []
        for room in self._map.rooms:
            # Check if room center is within marquee
            if min_x <= room.position.x <= max_x and min_y <= room.position.y <= max_y:
                selected.append(room)
                continue

            # Check if any walkmesh vertex (transformed to world) is within marquee.
            # Use cached local-space vertices and transform via math (no geometry copy).
            base_bwm = room.base_walkmesh()
            cache = self._get_bwm_surface_cache(base_bwm)
            for local_v in cache.vertices:
                world_v = self._room_local_to_world(room, local_v)
                if min_x <= world_v.x <= max_x and min_y <= world_v.y <= max_y:
                    selected.append(room)
                    break

        return selected

    def is_over_warp_point(self, world_pos: Vector3) -> bool:
        """Check if world position is over the warp point."""
        return world_pos.distance(self._map.warp_point) < self.warp_point_radius

    # =========================================================================
    # Camera controls
    # =========================================================================

    def camera_zoom(self) -> float:
        return self._cam_scale

    def set_camera_zoom(self, zoom: float):
        self._cam_scale = max(MIN_CAMERA_ZOOM, min(zoom, MAX_CAMERA_ZOOM))
        self.mark_dirty()

    def zoom_in_camera(self, zoom_factor: float):
        """Zoom camera by a multiplicative factor for linear visual zoom.

        Args:
            zoom_factor: Multiplier for zoom (e.g., 1.15 to zoom in 15%, 0.869 to zoom out 15%)
        """
        self.set_camera_zoom(self._cam_scale * zoom_factor)

    def camera_position(self) -> Vector2:
        return Vector2(*self._cam_position)

    def set_camera_position(self, x: float, y: float):
        self._cam_position.x = x
        self._cam_position.y = y
        self.mark_dirty()

    def pan_camera(self, x: float, y: float):
        self._cam_position.x += x
        self._cam_position.y += y
        self.mark_dirty()

    def camera_rotation(self) -> float:
        return self._cam_rotation

    def set_camera_rotation(self, radians: float):
        self._cam_rotation = radians
        self.mark_dirty()

    def rotate_camera(self, radians: float):
        self._cam_rotation += radians
        self.mark_dirty()

    # =========================================================================
    # Drawing
    # =========================================================================

    def _draw_image(
        self,
        painter: QPainter,
        image: QImage,
        coords: Vector2,
        rotation: float,
        flip_x: bool,
        flip_y: bool,
    ):
        original = painter.transform()
        true_width, true_height = image.width(), image.height()
        width, height = image.width() * COMPONENT_PREVIEW_SCALE, image.height() * COMPONENT_PREVIEW_SCALE

        transform = self._apply_transformation()
        transform.translate(coords.x, coords.y)
        transform.rotate(rotation)
        transform.scale(-1.0 if flip_x else 1.0, -1.0 if flip_y else 1.0)
        transform.translate(-width / 2, -height / 2)

        painter.setTransform(transform)
        source = QRectF(0, 0, true_width, true_height)
        rect = QRectF(0, 0, width, height)
        painter.drawImage(rect, image, source)
        painter.setTransform(original)

    def _face_color(
        self,
        material: SurfaceMaterial,
        *,
        alpha: int | None = None,
    ) -> QColor:
        """Resolve the display color for a face."""
        if self._colorize_materials and material in self._material_colors:
            color = QColor(self._material_colors[material])
        else:
            if isinstance(material, SurfaceMaterial):
                is_walkable = material.is_walkable()
            else:
                material_value = int(material)
                try:
                    material_enum = SurfaceMaterial(material_value)
                    is_walkable = material_enum in self._walkable_values
                except ValueError:
                    # Invalid material value - treat as non-walkable
                    is_walkable = False
            color = QColor(180, 180, 180) if is_walkable else QColor(120, 120, 120)
        if alpha is not None:
            color.setAlpha(alpha)
        return color

    def _draw_hooks_for_component(
        self,
        painter: QPainter,
        component: KitComponent,
        position: Vector3,
        rotation: float,
        flip_x: bool,
        flip_y: bool,
        connections: list[IndoorMapRoom | None] | None = None,
        *,
        alpha: int = 255,
        selected: tuple[IndoorMapRoom, int] | None = None,
        room_for_selection: IndoorMapRoom | None = None,
    ):
        """Draw hook markers for a component at a transformed position."""
        # Use a temporary room to reuse hook_position logic
        temp_room = IndoorMapRoom(component, Vector3(*position), rotation, flip_x=flip_x, flip_y=flip_y)

        for hook_index, hook in enumerate(component.hooks):
            hook_pos = temp_room.hook_position(hook)
            is_connected = bool(connections and hook_index < len(connections) and connections[hook_index] is not None)
            is_selected = selected is not None and room_for_selection is not None and selected == (room_for_selection, hook_index)

            if is_selected:
                brush_color = QColor(HOOK_COLOR_SELECTED[0], HOOK_COLOR_SELECTED[1], HOOK_COLOR_SELECTED[2], alpha)
                pen_color = QColor(HOOK_PEN_COLOR_SELECTED[0], HOOK_PEN_COLOR_SELECTED[1], HOOK_PEN_COLOR_SELECTED[2], alpha)
                radius = HOOK_SELECTED_RADIUS
            elif is_connected:
                brush_color = QColor(HOOK_COLOR_CONNECTED[0], HOOK_COLOR_CONNECTED[1], HOOK_COLOR_CONNECTED[2], alpha)
                pen_color = QColor(HOOK_PEN_COLOR_CONNECTED[0], HOOK_PEN_COLOR_CONNECTED[1], HOOK_PEN_COLOR_CONNECTED[2], alpha)
                radius = HOOK_DISPLAY_RADIUS
            else:
                brush_color = QColor(HOOK_COLOR_UNCONNECTED[0], HOOK_COLOR_UNCONNECTED[1], HOOK_COLOR_UNCONNECTED[2], alpha)
                pen_color = QColor(HOOK_PEN_COLOR_UNCONNECTED[0], HOOK_PEN_COLOR_UNCONNECTED[1], HOOK_PEN_COLOR_UNCONNECTED[2], alpha)
                radius = HOOK_DISPLAY_RADIUS

            painter.setBrush(brush_color)
            painter.setPen(QPen(pen_color, GRID_PEN_WIDTH))
            painter.drawEllipse(QPointF(hook_pos.x, hook_pos.y), radius, radius)

    def _draw_room_walkmesh(
        self,
        painter: QPainter,
        room: IndoorMapRoom,
    ):
        """Draw a room using its walkmesh geometry (no QImage).

        Uses QPainter transforms to draw local-space geometry in world space.
        This avoids deepcopying the walkmesh on every frame.
        """
        base_bwm = room.base_walkmesh()
        cache = self._get_bwm_surface_cache(base_bwm)

        # Apply room transform via painter (flip -> rotate -> translate)
        painter.save()
        painter.translate(room.position.x, room.position.y)
        painter.rotate(room.rotation)
        painter.scale(-1.0 if room.flip_x else 1.0, -1.0 if room.flip_y else 1.0)

        # Draw each face using cached local-space paths
        for idx, face in enumerate(base_bwm.faces):
            painter.setBrush(self._face_color(face.material))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(cache.face_paths[idx])

        painter.restore()

        # Draw hooks (snap points) for this room (already handles transforms internally)
        self._draw_hooks_for_component(
            painter,
            room.component,
            room.position,
            room.rotation,
            room.flip_x,
            room.flip_y,
            connections=room.hooks,
            selected=self._selected_hook,
            room_for_selection=room,
        )

    def _draw_cursor_walkmesh(self, painter: QPainter):
        """Draw the cursor preview using walkmesh geometry.

        Uses QPainter transforms to draw local-space geometry in world space.
        This avoids deepcopying the walkmesh on every mouse move.
        """
        if not self.cursor_component:
            return

        base_bwm = self.cursor_component.bwm
        cache = self._get_bwm_surface_cache(base_bwm)

        # Apply cursor transform via painter (flip -> rotate -> translate)
        painter.save()
        painter.translate(self.cursor_point.x, self.cursor_point.y)
        painter.rotate(self.cursor_rotation)
        painter.scale(-1.0 if self.cursor_flip_x else 1.0, -1.0 if self.cursor_flip_y else 1.0)

        # Draw each face using cached local-space paths with semi-transparent color
        for idx, face in enumerate(base_bwm.faces):
            painter.setBrush(self._face_color(face.material, alpha=CURSOR_PREVIEW_ALPHA))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(cache.face_paths[idx])

        painter.restore()

        # Draw hooks for the cursor preview (semi-transparent)
        self._draw_hooks_for_component(
            painter,
            self.cursor_component,
            self.cursor_point,
            self.cursor_rotation,
            self.cursor_flip_x,
            self.cursor_flip_y,
            connections=None,
            alpha=CURSOR_HOOK_ALPHA,
            selected=self._selected_hook,
            room_for_selection=None,
        )

    def _draw_room_highlight(
        self,
        painter: QPainter,
        room: IndoorMapRoom,
        alpha: int,
        color: QColor | None = None,
    ):
        """Draw a highlight overlay on a room.

        Uses QPainter transforms to draw local-space geometry in world space.
        """
        base_bwm = room.base_walkmesh()
        cache = self._get_bwm_surface_cache(base_bwm)

        if color is None:
            color = QColor(255, 255, 255, alpha)
        else:
            color.setAlpha(alpha)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)

        # Apply room transform via painter
        painter.save()
        painter.translate(room.position.x, room.position.y)
        painter.rotate(room.rotation)
        painter.scale(-1.0 if room.flip_x else 1.0, -1.0 if room.flip_y else 1.0)

        for path in cache.face_paths:
            painter.drawPath(path)

        painter.restore()

    def _get_bwm_surface_cache(self, bwm: BWM) -> _BWMSurfaceCache:
        """Get (or build) cached local-space geometry for a BWM."""
        key: int = id(bwm)
        cached: _BWMSurfaceCache | None = self._bwm_surface_cache.get(key)
        if cached is not None:
            return cached

        # Build face paths (local space) and identity->index map.
        face_paths: list[QPainterPath] = []
        face_id_to_index: dict[int, int] = {}
        for idx, face in enumerate(bwm.faces):
            path = QPainterPath()
            path.moveTo(face.v1.x, face.v1.y)
            path.lineTo(face.v2.x, face.v2.y)
            path.lineTo(face.v3.x, face.v3.y)
            path.closeSubpath()
            face_paths.append(path)
            face_id_to_index[id(face)] = idx

        # Vertex list + AABB for early rejection.
        verts = bwm.vertices()
        if verts:
            bbmin = Vector3(min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts))
            bbmax = Vector3(max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts))
        else:
            bbmin = Vector3.from_null()
            bbmax = Vector3.from_null()

        cached = _BWMSurfaceCache(
            bwm_obj_id=key,
            face_paths=face_paths,
            face_id_to_index=face_id_to_index,
            vertices=verts,
            bbmin=bbmin,
            bbmax=bbmax,
        )
        self._bwm_surface_cache[key] = cached
        return cached

    def _world_to_room_local(self, room: IndoorMapRoom, world_pos: Vector3) -> Vector3:
        """Convert world position into room-local space (inverse of flip->rotate->translate)."""
        pos = Vector3(*world_pos)
        # inverse translate
        pos.x -= room.position.x
        pos.y -= room.position.y
        pos.z -= room.position.z
        # inverse rotation
        cos_r = math.cos(math.radians(-room.rotation))
        sin_r = math.sin(math.radians(-room.rotation))
        x = pos.x * cos_r - pos.y * sin_r
        y = pos.x * sin_r + pos.y * cos_r
        pos.x, pos.y = x, y
        # inverse flip
        if room.flip_x:
            pos.x = -pos.x
        if room.flip_y:
            pos.y = -pos.y
        return pos

    def _room_local_to_world(self, room: IndoorMapRoom, local_pos: Vector3) -> Vector3:
        """Convert room-local to world (flip->rotate->translate)."""
        pos = Vector3(*local_pos)
        if room.flip_x:
            pos.x = -pos.x
        if room.flip_y:
            pos.y = -pos.y
        cos_r = math.cos(math.radians(room.rotation))
        sin_r = math.sin(math.radians(room.rotation))
        x = pos.x * cos_r - pos.y * sin_r
        y = pos.x * sin_r + pos.y * cos_r
        pos.x, pos.y = x, y
        return pos + room.position

    # ------------------------------------------------------------------
    # Hook editing helpers
    # ------------------------------------------------------------------
    def _ensure_room_component_unique(self, room: IndoorMapRoom):
        """Clone the component so hooks can be edited per-room."""
        # If any other room shares this component instance, clone
        shared: bool = any(r is not room and r.component is room.component for r in self._map.rooms)
        if not shared:
            return
        component_copy: KitComponent = deepcopy(room.component)
        room.component = component_copy
        # Rebuild connections list to match hooks length
        room.hooks = [None] * len(component_copy.hooks)  # type: ignore[assignment]
        # NOTE: No cache invalidation needed - new BWM object gets a fresh cache entry

    def _world_to_local_hook(
        self,
        room: IndoorMapRoom,
        world_pos: Vector3,
    ) -> Vector3:
        """Convert world coordinates to local hook coordinates for the room."""
        pos: Vector3 = Vector3(*world_pos)
        # translate to room local
        pos.x -= room.position.x
        pos.y -= room.position.y
        # inverse rotation
        cos_r: float = math.cos(math.radians(-room.rotation))
        sin_r: float = math.sin(math.radians(-room.rotation))
        x: float = pos.x * cos_r - pos.y * sin_r
        y: float = pos.x * sin_r + pos.y * cos_r
        pos.x, pos.y = x, y
        # inverse flip
        if room.flip_x:
            pos.x = -pos.x
        if room.flip_y:
            pos.y = -pos.y
        return pos

    def add_hook_at(
        self,
        world_pos: Vector3,
    ):
        """Add a hook to the room under the mouse at world_pos."""
        room = self._under_mouse_room
        if room is None:
            return
        self._ensure_room_component_unique(room)
        local_pos = self._world_to_local_hook(room, world_pos)

        # Choose a door reference: prefer existing hook door, else first kit door
        door = room.component.hooks[0].door if room.component.hooks else (room.component.kit.doors[0] if room.component.kit.doors else None)
        if door is None:
            return  # cannot add without a door reference

        hook = KitComponentHook(position=local_pos, rotation=0.0, edge=len(room.component.hooks), door=door)
        room.component.hooks.append(hook)
        room.hooks.append(None)
        self._selected_hook = (room, len(room.component.hooks) - 1)
        self._map.rebuild_room_connections()
        self.mark_dirty()

    def delete_hook(
        self,
        room: IndoorMapRoom,
        hook_index: int,
    ):
        """Delete a hook from a room."""
        if hook_index < 0 or hook_index >= len(room.component.hooks):
            return
        self._ensure_room_component_unique(room)
        # Clear selected hook if it's the one being deleted or if it becomes invalid
        if self._selected_hook is not None:
            sel_room, sel_index = self._selected_hook
            if sel_room is room and (sel_index == hook_index or sel_index >= len(room.component.hooks) - 1):
                self._selected_hook = None
        room.component.hooks.pop(hook_index)
        if hook_index < len(room.hooks):
            room.hooks.pop(hook_index)
        # Validate selected hook index is still valid after deletion
        if self._selected_hook is not None:
            sel_room, sel_index = self._selected_hook
            if sel_room is room and sel_index >= len(room.component.hooks):
                self._selected_hook = None
        self._map.rebuild_room_connections()
        self.mark_dirty()

    def duplicate_hook(
        self,
        room: IndoorMapRoom,
        hook_index: int,
    ):
        """Duplicate a hook in place."""
        if hook_index < 0 or hook_index >= len(room.component.hooks):
            return
        self._ensure_room_component_unique(room)
        src: KitComponentHook = room.component.hooks[hook_index]
        new_hook = KitComponentHook(
            position=Vector3(*src.position),
            rotation=src.rotation,
            edge=len(room.component.hooks),
            door=src.door,
        )
        room.component.hooks.append(new_hook)
        room.hooks.append(None)
        self._selected_hook = (room, len(room.component.hooks) - 1)
        self._map.rebuild_room_connections()
        self.mark_dirty()

    def _draw_grid(self, painter: QPainter):
        """Draw grid overlay."""
        if not self.show_grid:
            return

        painter.setPen(QPen(QColor(GRID_COLOR[0], GRID_COLOR[1], GRID_COLOR[2]), GRID_PEN_WIDTH))

        # Calculate visible area
        top_left = self.to_world_coords(0, 0)
        bottom_right = self.to_world_coords(self.width(), self.height())

        min_x = min(top_left.x, bottom_right.x)
        max_x = max(top_left.x, bottom_right.x)
        min_y = min(top_left.y, bottom_right.y)
        max_y = max(top_left.y, bottom_right.y)

        # Snap to grid
        min_x = math.floor(min_x / self.grid_size) * self.grid_size
        max_x = math.ceil(max_x / self.grid_size) * self.grid_size
        min_y = math.floor(min_y / self.grid_size) * self.grid_size
        max_y = math.ceil(max_y / self.grid_size) * self.grid_size

        # Draw vertical lines
        x = min_x
        while x <= max_x:
            painter.drawLine(QPointF(x, min_y), QPointF(x, max_y))
            x += self.grid_size

        # Draw horizontal lines
        y = min_y
        while y <= max_y:
            painter.drawLine(QPointF(min_x, y), QPointF(max_x, y))
            y += self.grid_size

    def _draw_snap_indicator(self, painter: QPainter):
        """Draw snap indicator when snapping is active."""
        if self._snap_indicator is None or not self._snap_indicator.snapped:
            return

        # Prefer the exact hook-to position for visual cue; fall back to snap position.
        if self._snap_indicator.hook_to is not None and self._snap_indicator.target_room is not None:
            pos_vec = self._snap_indicator.target_room.hook_position(self._snap_indicator.hook_to)
        else:
            pos_vec = self._snap_indicator.position

        painter.setPen(QPen(QColor(SNAP_INDICATOR_COLOR[0], SNAP_INDICATOR_COLOR[1], SNAP_INDICATOR_COLOR[2]), SNAP_INDICATOR_PEN_WIDTH))
        painter.setBrush(QColor(SNAP_INDICATOR_COLOR[0], SNAP_INDICATOR_COLOR[1], SNAP_INDICATOR_COLOR[2], SNAP_INDICATOR_ALPHA))
        painter.drawEllipse(QPointF(pos_vec.x, pos_vec.y), SNAP_INDICATOR_RADIUS, SNAP_INDICATOR_RADIUS)

    def _draw_spawn_point(self, painter: QPainter, coords: Vector3):
        # Highlight when hovering or dragging
        is_active = self._hovering_warp or self._dragging_warp
        radius = self.warp_point_radius * (WARP_POINT_ACTIVE_SCALE if is_active else 1.0)
        alpha = WARP_POINT_ALPHA_ACTIVE if is_active else WARP_POINT_ALPHA_NORMAL

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(WARP_POINT_COLOR[0], WARP_POINT_COLOR[1], WARP_POINT_COLOR[2], alpha))
        painter.drawEllipse(QPointF(coords.x, coords.y), radius, radius)

        # Draw crosshair
        line_len = radius * WARP_POINT_CROSSHAIR_SCALE
        pen_width = WARP_POINT_PEN_WIDTH_ACTIVE if is_active else WARP_POINT_PEN_WIDTH_NORMAL
        painter.setPen(QPen(QColor(WARP_POINT_COLOR[0], WARP_POINT_COLOR[1], WARP_POINT_COLOR[2]), pen_width))
        painter.drawLine(QPointF(coords.x, coords.y - line_len), QPointF(coords.x, coords.y + line_len))
        painter.drawLine(QPointF(coords.x - line_len, coords.y), QPointF(coords.x + line_len, coords.y))

    def _draw_marquee(self, painter: QPainter):
        """Draw the marquee selection rectangle."""
        if not self._marquee_active:
            return

        # Reset transform to draw in screen coords
        painter.resetTransform()

        # Calculate rectangle
        x1, y1 = self._marquee_start.x, self._marquee_start.y
        x2, y2 = self._marquee_end.x, self._marquee_end.y

        rect = QRectF(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))

        # Draw semi-transparent fill
        painter.setBrush(QColor(MARQUEE_FILL_COLOR[0], MARQUEE_FILL_COLOR[1], MARQUEE_FILL_COLOR[2], MARQUEE_FILL_COLOR[3]))
        painter.setPen(QPen(QColor(MARQUEE_BORDER_COLOR[0], MARQUEE_BORDER_COLOR[1], MARQUEE_BORDER_COLOR[2], MARQUEE_BORDER_COLOR[3]), 1, Qt.PenStyle.DashLine))
        painter.drawRect(rect)

    def _build_face(self, face: BWMFace) -> QPainterPath:
        v1 = Vector2(face.v1.x, face.v1.y)
        v2 = Vector2(face.v2.x, face.v2.y)
        v3 = Vector2(face.v3.x, face.v3.y)

        path = QPainterPath()
        path.moveTo(v1.x, v1.y)
        path.lineTo(v2.x, v2.y)
        path.lineTo(v3.x, v3.y)
        path.lineTo(v1.x, v1.y)
        path.closeSubpath()
        return path

    def _apply_transformation(self) -> QTransform:
        result = QTransform()
        result.translate(self.width() / 2, self.height() / 2)
        result.rotate(math.degrees(self._cam_rotation))
        result.scale(self._cam_scale, self._cam_scale)
        result.translate(-self._cam_position.x, -self._cam_position.y)
        return result

    def paintEvent(self, e: QPaintEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        transform = self._apply_transformation()
        painter = QPainter(self)
        painter.setBrush(QColor(BACKGROUND_COLOR[0], BACKGROUND_COLOR[1], BACKGROUND_COLOR[2], BACKGROUND_COLOR[3]))
        painter.drawRect(0, 0, self.width(), self.height())
        painter.setTransform(transform)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # Draw grid
        self._draw_grid(painter)

        # Draw rooms using walkmesh geometry (NOT QImage - QImage is only for sidebar preview)
        for room in self._map.rooms:
            self._draw_room_walkmesh(painter, room)

            # Draw hooks (magnets)
            if not self.hide_magnets:
                for hook_index, hook in enumerate(room.component.hooks):
                    hook_pos = room.hook_position(hook)
                    # Color: unconnected = red, connected = green
                    if room.hooks[hook_index] is None:
                        painter.setBrush(QColor(HOOK_COLOR_UNCONNECTED[0], HOOK_COLOR_UNCONNECTED[1], HOOK_COLOR_UNCONNECTED[2], HOOK_COLOR_UNCONNECTED[3]))
                        painter.setPen(
                            QPen(
                                QColor(HOOK_PEN_COLOR_UNCONNECTED[0], HOOK_PEN_COLOR_UNCONNECTED[1], HOOK_PEN_COLOR_UNCONNECTED[2], HOOK_PEN_COLOR_UNCONNECTED[3]),
                                GRID_PEN_WIDTH,
                            )
                        )
                    else:
                        painter.setBrush(QColor(HOOK_COLOR_CONNECTED[0], HOOK_COLOR_CONNECTED[1], HOOK_COLOR_CONNECTED[2], HOOK_COLOR_CONNECTED[3]))
                        painter.setPen(
                            QPen(QColor(HOOK_PEN_COLOR_CONNECTED[0], HOOK_PEN_COLOR_CONNECTED[1], HOOK_PEN_COLOR_CONNECTED[2], HOOK_PEN_COLOR_CONNECTED[3]), GRID_PEN_WIDTH)
                        )
                    painter.drawEllipse(QPointF(hook_pos.x, hook_pos.y), HOOK_DISPLAY_RADIUS, HOOK_DISPLAY_RADIUS)

        # Draw connections (green lines for connected hooks)
        for room in self._map.rooms:
            for hook_index, hook in enumerate(room.component.hooks):
                if room.hooks[hook_index] is None:
                    continue
                hook_pos = room.hook_position(hook)
                xd = math.cos(math.radians(hook.rotation + room.rotation)) * hook.door.width / 2
                yd = math.sin(math.radians(hook.rotation + room.rotation)) * hook.door.width / 2
                painter.setPen(
                    QPen(
                        QColor(CONNECTION_LINE_COLOR[0], CONNECTION_LINE_COLOR[1], CONNECTION_LINE_COLOR[2], CONNECTION_LINE_COLOR[3]),
                        CONNECTION_LINE_WIDTH_SCALE / self._cam_scale,
                    )
                )
                painter.drawLine(
                    QPointF(hook_pos.x - xd, hook_pos.y - yd),
                    QPointF(hook_pos.x + xd, hook_pos.y + yd),
                )

        # Draw cursor preview using walkmesh (NOT QImage)
        self._draw_cursor_walkmesh(painter)

        # Draw snap indicator
        self._draw_snap_indicator(painter)

        # Draw hover highlight
        if self._under_mouse_room and self._under_mouse_room not in self._selected_rooms:
            self._draw_room_highlight(
                painter, self._under_mouse_room, ROOM_HOVER_ALPHA, QColor(ROOM_HOVER_COLOR[0], ROOM_HOVER_COLOR[1], ROOM_HOVER_COLOR[2], ROOM_HOVER_COLOR[3])
            )

        # Draw selection highlights
        for room in self._selected_rooms:
            self._draw_room_highlight(
                painter, room, ROOM_SELECTED_ALPHA, QColor(ROOM_SELECTED_COLOR[0], ROOM_SELECTED_COLOR[1], ROOM_SELECTED_COLOR[2], ROOM_SELECTED_COLOR[3])
            )

        # Draw spawn point (warp point)
        self._draw_spawn_point(painter, self._map.warp_point)

        # Draw marquee selection (in screen space, so after transform reset)
        self._draw_marquee(painter)

    # =========================================================================
    # Events
    # =========================================================================

    def wheelEvent(self, e: QWheelEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        self.sig_mouse_scrolled.emit(
            Vector2(e.angleDelta().x(), e.angleDelta().y()),
            e.buttons(),
            self._keys_down,
        )
        self.mark_dirty()

    def mouseMoveEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        coords: Vector2 = (
            Vector2(e.x(), e.y())  # pyright: ignore[reportAttributeAccessIssue]
            if qtpy.QT5
            else Vector2(e.position().toPoint().x(), e.position().toPoint().y())  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
        )
        coords_delta = Vector2(coords.x - self._mouse_prev.x, coords.y - self._mouse_prev.y)
        self._mouse_prev = coords
        self.sig_mouse_moved.emit(coords, coords_delta, self._mouse_down, self._keys_down)

        world = self.to_world_coords(coords.x, coords.y)
        self.cursor_point = world

        # Keep status bar updated with live mouse state
        if self._status_callback is not None:
            self._status_callback(coords, self._mouse_down, self._keys_down)

        # Update warp point hover state
        self._hovering_warp = self.is_over_warp_point(world)

        # Handle marquee selection - ONLY if left button is still held
        if self._marquee_active:
            if Qt.MouseButton.LeftButton not in self._mouse_down:
                # Left button released but marquee still active - force end it
                self.end_drag()
                return
            self._marquee_end = coords
            self.mark_dirty()
            return

        # Handle warp point dragging - ONLY if left button still held
        if self._dragging_warp:
            if Qt.MouseButton.LeftButton not in self._mouse_down:
                self.end_drag()
                return
            world_delta = self.to_world_delta(coords_delta.x, coords_delta.y)
            self._map.warp_point.x += world_delta.x
            self._map.warp_point.y += world_delta.y
            # Apply grid snap to warp point if enabled
            if self.snap_to_grid:
                self._map.warp_point = self._snap_to_grid(self._map.warp_point)
            self.mark_dirty()
            return

        # Handle hook dragging (selected hook) - ONLY if left button still held
        if self._dragging_hook and self._selected_hook is not None:
            if Qt.MouseButton.LeftButton not in self._mouse_down:
                self._dragging_hook = False
                self._map.rebuild_room_connections()
                self.mark_dirty()
                return
            room, hook_index = self._selected_hook
            if hook_index < len(room.component.hooks):
                world_delta = self.to_world_delta(coords_delta.x, coords_delta.y)
                hook = room.component.hooks[hook_index]
                # Move in world space then convert to local
                new_world = room.hook_position(hook) + Vector3(world_delta.x, world_delta.y, 0)
                local = self._world_to_local_hook(room, new_world)
                hook.position = local
                self.mark_dirty()
            return

        # Handle room dragging - ONLY if left button still held
        if self._dragging and self._drag_rooms:
            if Qt.MouseButton.LeftButton not in self._mouse_down:
                self.end_drag()
                return
            world_delta = self.to_world_delta(coords_delta.x, coords_delta.y)

            # Move all selected rooms by delta first
            for room in self._drag_rooms:
                room.position.x += world_delta.x
                room.position.y += world_delta.y

            # Get the primary room for snapping calculations
            active_room = self._drag_rooms[-1] if self._drag_rooms else None
            snapped = False

            # Soft hook snapping: only apply if within threshold, allow disconnection when dragged away
            if active_room and self.snap_to_hooks:
                # Check if we have a snap anchor from previous snap
                if self._snap_anchor_position is not None:
                    # Calculate distance from current position to snap anchor
                    distance_from_anchor = Vector2.from_vector3(active_room.position).distance(Vector2.from_vector3(self._snap_anchor_position))

                    # Dynamic disconnect threshold tied to zoom (smaller to make separation easy)
                    dynamic_disconnect = max(
                        HOOK_SNAP_DISCONNECT_BASE_THRESHOLD,
                        HOOK_SNAP_DISCONNECT_SCALE_FACTOR * max(HOOK_SNAP_BASE_THRESHOLD, HOOK_SNAP_SCALE_FACTOR / self._cam_scale),
                    )
                    # If moved beyond disconnect threshold, clear snap and allow free movement
                    if distance_from_anchor > dynamic_disconnect:
                        self._snap_anchor_position = None
                        self._snap_indicator = None
                    else:
                        # Still within threshold - check if we can still snap
                        snap_result = self._find_hook_snap(active_room, active_room.position)
                        if snap_result.snapped:
                            # Check distance from current position to snap point
                            distance_to_snap = Vector2.from_vector3(active_room.position).distance(Vector2.from_vector3(snap_result.position))
                            snap_threshold = max(HOOK_SNAP_BASE_THRESHOLD, HOOK_SNAP_SCALE_FACTOR / self._cam_scale)

                            # Only apply snap if within threshold
                            if distance_to_snap <= snap_threshold:
                                # Calculate offset and apply to all rooms
                                offset_x = snap_result.position.x - active_room.position.x
                                offset_y = snap_result.position.y - active_room.position.y
                                for room in self._drag_rooms:
                                    room.position.x += offset_x
                                    room.position.y += offset_y
                                self._snap_indicator = snap_result
                                # Update snap anchor to new snap position
                                self._snap_anchor_position = Vector3(*snap_result.position)
                                snapped = True
                            else:
                                # Too far from snap point - disconnect
                                self._snap_anchor_position = None
                                self._snap_indicator = None
                        else:
                            # No snap available - disconnect
                            self._snap_anchor_position = None
                            self._snap_indicator = None
                else:
                    # No existing snap anchor - try to find a new snap
                    snap_result = self._find_hook_snap(active_room, active_room.position)
                    if snap_result.snapped:
                        # Check distance from current position to snap point
                        distance_to_snap = Vector2.from_vector3(active_room.position).distance(Vector2.from_vector3(snap_result.position))
                        snap_threshold = max(1.0, 2.0 / self._cam_scale)

                        # Only apply snap if within threshold
                        if distance_to_snap <= snap_threshold:
                            # Calculate offset and apply to all rooms
                            offset_x = snap_result.position.x - active_room.position.x
                            offset_y = snap_result.position.y - active_room.position.y
                            for room in self._drag_rooms:
                                room.position.x += offset_x
                                room.position.y += offset_y
                            self._snap_indicator = snap_result
                            # Record snap anchor position
                            self._snap_anchor_position = Vector3(*snap_result.position)
                            snapped = True
                        else:
                            self._snap_indicator = None
                    else:
                        self._snap_indicator = None

            # Apply grid snapping if enabled (and not already snapped to hook)
            if self.snap_to_grid and not snapped and active_room:
                # Snap the active room to grid, then move others by same offset
                old_pos = Vector3(*active_room.position)
                snapped_pos = self._snap_to_grid(active_room.position)
                offset_x = snapped_pos.x - old_pos.x
                offset_y = snapped_pos.y - old_pos.y

                for room in self._drag_rooms:
                    room.position.x += offset_x
                    room.position.y += offset_y

            # NOTE: Don't rebuild_room_connections() during drag - it's O(n²) and kills perf.
            # Connections are rebuilt in the MoveRoomsCommand.redo() when drag ends.
            self.mark_dirty()
            return

        # Handle cursor component snapping
        if self.cursor_component:
            snapped = False

            # Try hook snap first (it's more important for connections)
            if self.snap_to_hooks:
                snap_result = self._find_hook_snap(
                    None,
                    self.cursor_point,
                    self.cursor_component,
                    self.cursor_rotation,
                    self.cursor_flip_x,
                    self.cursor_flip_y,
                )
                if snap_result.snapped:
                    self.cursor_point = snap_result.position
                    self._snap_indicator = snap_result
                    snapped = True
                else:
                    self._snap_indicator = None

            # Apply grid snap if not snapped to hook
            if self.snap_to_grid and not snapped:
                self.cursor_point = self._snap_to_grid(self.cursor_point)

            self.mark_dirty()

        # Find room under mouse
        self._under_mouse_room, _ = self.pick_face(world)
        self.mark_dirty()

    def mousePressEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        event_mouse_button = e.button()
        if event_mouse_button is None:
            return
        self._mouse_down.add(event_mouse_button)
        coords: Vector2 = (
            Vector2(e.x(), e.y())  # pyright: ignore[reportAttributeAccessIssue]
            if qtpy.QT5
            else Vector2(e.position().toPoint().x(), e.position().toPoint().y())  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
        )
        self.sig_mouse_pressed.emit(coords, self._mouse_down, self._keys_down)
        if self._status_callback is not None:
            self._status_callback(coords, self._mouse_down, self._keys_down)

    def mouseReleaseEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        event_mouse_button = e.button()
        if event_mouse_button is None:
            return
        self._mouse_down.discard(event_mouse_button)
        coords: Vector2 = (
            Vector2(e.x(), e.y())  # pyright: ignore[reportAttributeAccessIssue]
            if qtpy.QT5
            else Vector2(e.position().toPoint().x(), e.position().toPoint().y())  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
        )
        self.sig_mouse_released.emit(coords, self._mouse_down, self._keys_down)
        if self._status_callback is not None:
            self._status_callback(coords, self._mouse_down, self._keys_down)

    def mouseDoubleClickEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        event_mouse_button = e.button()
        if event_mouse_button is None:
            return
        mouse_down: set[int | Qt.MouseButton] = set(self._mouse_down)
        mouse_down.add(event_mouse_button)
        coords: Vector2 = (
            Vector2(e.x(), e.y())  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
            if qtpy.QT5
            else Vector2(e.position().toPoint().x(), e.position().toPoint().y())  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
        )
        self.sig_mouse_double_clicked.emit(coords, mouse_down, self._keys_down)

    def keyPressEvent(self, e: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        # ESC key handling at renderer level for immediate cancellation
        if e.key() == Qt.Key.Key_Escape:
            # Cancel all active operations immediately
            if self._marquee_active:
                self._marquee_active = False
                self._drag_mode = DragMode.NONE
            if self._dragging:
                self.end_drag()
            if self._dragging_hook:
                self._dragging_hook = False
            if self._dragging_warp:
                self._dragging_warp = False
            # Clear selections
            self.clear_selected_rooms()
            self.clear_selected_hook()
            # Cancel placement mode
            if self.cursor_component is not None:
                self.set_cursor_component(None)
            self.mark_dirty()
            return

        self._keys_down.add(e.key())
        self.mark_dirty()

    def keyReleaseEvent(self, e: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        self._keys_down.discard(e.key())
        self.mark_dirty()

    def focusInEvent(self, e: QFocusEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle focus in - ensure we can receive keyboard input."""
        super().focusInEvent(e)
        self.mark_dirty()

    def focusOutEvent(self, e: QFocusEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle focus out - cancel operations that require focus (standard Windows behavior)."""
        super().focusOutEvent(e)
        # Cancel drag operations when focus is lost (prevents stuck states)
        if self._dragging or self._dragging_hook or self._dragging_warp or self._marquee_active:
            self.end_drag()
            self._dragging_hook = False
            self._dragging_warp = False
            self._marquee_active = False
            self._drag_mode = DragMode.NONE
        # Clear key states to prevent stuck modifier keys
        self._keys_down.clear()
        self.mark_dirty()

    def closeEvent(self, e: QCloseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle widget close event - stop render loop and clean up resources."""
        # Stop the render timer immediately
        if hasattr(self, "_render_timer"):
            self._render_timer.stop()

        # Disconnect all signals to prevent callbacks after destruction
        try:
            self.sig_mouse_moved.disconnect()
            self.sig_mouse_scrolled.disconnect()
            self.sig_mouse_released.disconnect()
            self.sig_mouse_pressed.disconnect()
            self.sig_mouse_double_clicked.disconnect()
            self.sig_rooms_moved.disconnect()
            self.sig_warp_moved.disconnect()
            self.sig_marquee_select.disconnect()
        except Exception:
            # Signals may already be disconnected
            pass

        # Clear references to prevent circular dependencies
        self._map = IndoorMap()
        self._undo_stack = None
        self._selected_rooms.clear()
        self._bwm_surface_cache.clear()
        self.cursor_component = None

        # Process any pending events before destruction
        QApplication.processEvents()

        # Call parent closeEvent
        # Wrap in try-except to handle case where widget is already being destroyed
        try:
            if hasattr(self, "isVisible"):
                super().closeEvent(e)
            else:
                e.accept()
        except RuntimeError:
            e.accept()
        except Exception:
            try:
                e.accept()
            except Exception:
                pass
