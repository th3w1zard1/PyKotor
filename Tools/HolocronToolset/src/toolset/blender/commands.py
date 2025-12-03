"""High-level command interfaces for Blender integration.

This module provides high-level commands for:
- Module loading and management
- Instance manipulation
- Layout editing
- Synchronization
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from loggerplus import RobustLogger

from toolset.blender.ipc_client import BlenderCommands, BlenderIPCClient, get_ipc_client
from toolset.blender.serializers import (
    serialize_git_instance,
    serialize_module_data,
)

if TYPE_CHECKING:
    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.generics.git import GIT, GITInstance


class BlenderEditorMode(Enum):
    """Mode for Blender editor integration."""

    MODULE_DESIGNER = "module_designer"
    GIT_EDITOR = "git_editor"
    INDOOR_BUILDER = "indoor_builder"


@dataclass
class BlenderSession:
    """Represents an active Blender editing session."""

    mode: BlenderEditorMode
    module_root: str
    installation_path: str
    is_active: bool = False

    # Object name mappings (PyKotor instance <-> Blender object name)
    instance_to_object: dict[int, str] = None  # type: ignore[assignment]
    object_to_instance: dict[str, int] = None  # type: ignore[assignment]
    runtime_to_object: dict[int, str] = None  # type: ignore[assignment]
    runtime_to_instance: dict[int, "GITInstance"] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.instance_to_object is None:
            self.instance_to_object = {}
        if self.object_to_instance is None:
            self.object_to_instance = {}
        if self.runtime_to_object is None:
            self.runtime_to_object = {}
        if self.runtime_to_instance is None:
            self.runtime_to_instance = {}


class BlenderEditorController:
    """Controller for managing Blender editor integration.

    This class coordinates between the toolset UI and Blender,
    handling module loading, instance synchronization, and events.
    """

    def __init__(self):
        self._client: BlenderIPCClient = get_ipc_client()
        self._commands: BlenderCommands = BlenderCommands(self._client)
        self._session: BlenderSession | None = None
        self._logger = RobustLogger()

        # Event callbacks
        self._selection_callbacks: list[Callable[[list[int]], None]] = []
        self._transform_callbacks: list[Callable[[int, dict | None, dict | None], None]] = []
        self._instance_callbacks: list[Callable[[str, dict[str, Any]], None]] = []
        self._instance_update_callbacks: list[Callable[[int, dict[str, Any]], None]] = []
        self._context_menu_callbacks: list[Callable[[list[int]], None]] = []

        # Register for Blender events
        self._client.on_event("selection_changed", self._on_selection_changed)
        self._client.on_event("transform_changed", self._on_transform_changed)
        self._client.on_event("instance_added", self._on_instance_added)
        self._client.on_event("instance_removed", self._on_instance_removed)
        self._client.on_event("instance_updated", self._on_instance_updated)
        self._client.on_event("context_menu_requested", self._on_context_menu_requested)

    @property
    def is_connected(self) -> bool:
        """Check if connected to Blender."""
        return self._client.is_connected

    @property
    def session(self) -> BlenderSession | None:
        """Get the current session."""
        return self._session

    def connect(self, timeout: float = 5.0) -> bool:
        """Connect to Blender IPC server.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connected successfully
        """
        return self._client.connect(timeout)

    def disconnect(self):
        """Disconnect from Blender."""
        self._client.disconnect()
        self._session = None

    def on_state_change(self, callback: Callable[[ConnectionState], None]):
        """Register callback for connection state changes."""
        self._client.on_state_change(callback)

    def on_selection_changed(self, callback: Callable[[list[int]], None]):
        """Register callback for selection changes in Blender."""
        self._selection_callbacks.append(callback)

    def on_transform_changed(self, callback: Callable[[int, dict | None, dict | None], None]):
        """Register callback for transform changes in Blender."""
        self._transform_callbacks.append(callback)

    def on_instance_changed(self, callback: Callable[[str, dict[str, Any]], None]):
        """Register callback for instance add/remove in Blender."""
        self._instance_callbacks.append(callback)

    def on_context_menu_requested(self, callback: Callable[[list[int]], None]):
        """Register callback for context menu requests originating in Blender."""
        self._context_menu_callbacks.append(callback)

    def on_instance_updated(self, callback: Callable[[int, dict[str, Any]], None]):
        """Register callback for arbitrary property updates originating in Blender."""
        self._instance_update_callbacks.append(callback)

    def on_material_changed(self, callback: Callable[[dict[str, Any]], None]):
        """Register callback for material/texture changes."""
        self._client.on_event("material_changed", lambda e: callback(e.params))

    # =========================================================================
    # Module Loading
    # =========================================================================

    def load_module(
        self,
        mode: BlenderEditorMode,
        lyt: LYT,
        git: GIT,
        walkmeshes: list[BWM],
        module_root: str,
        installation_path: str | Path,
    ) -> bool:
        """Load a module into Blender.

        Args:
            mode: Editor mode
            lyt: Layout resource
            git: GIT resource
            walkmeshes: List of walkmesh resources
            module_root: Module root name
            installation_path: Path to KotOR installation

        Returns:
            True if loaded successfully
        """
        if not self.is_connected:
            self._logger.error("Cannot load module: not connected to Blender")
            return False

        # Serialize module data
        module_data = serialize_module_data(
            lyt, git, walkmeshes, module_root, str(installation_path)
        )

        # Send to Blender
        success = self._commands.load_module(
            lyt_data=module_data["lyt"],
            git_data=module_data["git"],
            installation_path=str(installation_path),
            module_root=module_root,
        )

        if success:
            self._session = BlenderSession(
                mode=mode,
                module_root=module_root,
                installation_path=str(installation_path),
                is_active=True,
            )
            self._register_runtime_instances(git)
            self._logger.info(f"Loaded module '{module_root}' in Blender")
        else:
            self._logger.error(f"Failed to load module '{module_root}' in Blender")

        return success

    def _register_runtime_instances(self, git: GIT):
        """Cache runtime identifiers for every instance within the active GIT."""
        if self._session is None:
            return
        for instance in git.instances():
            self._register_runtime_instance(instance)

    def _register_runtime_instance(self, instance: GITInstance):
        if self._session is None:
            return
        runtime_id = id(instance)
        self._session.runtime_to_instance[runtime_id] = instance

    def unload_module(self) -> bool:
        """Unload the current module from Blender.

        Returns:
            True if unloaded successfully
        """
        if not self.is_connected:
            return True

        success = self._commands.unload_module()
        if success:
            self._session = None
            self._logger.info("Unloaded module from Blender")

        return success

    # =========================================================================
    # Instance Management
    # =========================================================================

    def add_instance(self, instance: GITInstance) -> str | None:
        """Add a GIT instance to Blender.

        Args:
            instance: GITInstance to add

        Returns:
            Blender object name if successful
        """
        if not self.is_connected or self._session is None:
            return None

        instance_data = serialize_git_instance(instance)
        runtime_id = instance_data.get("runtime_id")
        self._register_runtime_instance(instance)
        object_name = self._commands.add_instance(instance_data)

        if object_name and self._session:
            instance_id = id(instance)
            self._session.instance_to_object[instance_id] = object_name
            self._session.object_to_instance[object_name] = instance_id
            if runtime_id is not None:
                self.bind_runtime_instance(int(runtime_id), instance, object_name)

        return object_name

    def remove_instance(self, instance: GITInstance) -> bool:
        """Remove a GIT instance from Blender.

        Args:
            instance: GITInstance to remove

        Returns:
            True if removed successfully
        """
        if not self.is_connected or self._session is None:
            return False

        instance_id = id(instance)
        runtime_id = instance_id
        object_name = self._session.instance_to_object.get(instance_id)

        if not object_name:
            return False

        success = self._commands.remove_instance(object_name)

        if success:
            self._session.instance_to_object.pop(instance_id, None)
            self._session.object_to_instance.pop(object_name, None)
            self._session.runtime_to_object.pop(runtime_id, None)
            self._session.runtime_to_instance.pop(runtime_id, None)

        return success

    def bind_runtime_instance(
        self,
        runtime_id: int,
        instance: GITInstance,
        object_name: str | None = None,
    ) -> None:
        """Associate a runtime id with a Python instance (and optionally a Blender object)."""
        if self._session is None:
            return
        self._session.runtime_to_instance[runtime_id] = instance
        if object_name:
            self._session.runtime_to_object[runtime_id] = object_name
            instance_id = id(instance)
            self._session.instance_to_object[instance_id] = object_name
            self._session.object_to_instance[object_name] = instance_id

    def unbind_runtime_instance(self, runtime_id: int) -> None:
        """Remove a runtime association."""
        if self._session is None:
            return
        self._session.runtime_to_object.pop(runtime_id, None)
        self._session.runtime_to_instance.pop(runtime_id, None)

    def update_instance_position(
        self,
        instance: GITInstance,
        x: float,
        y: float,
        z: float,
    ) -> bool:
        """Update instance position in Blender.

        Args:
            instance: GITInstance to update
            x, y, z: New position coordinates

        Returns:
            True if updated successfully
        """
        if not self.is_connected or self._session is None:
            return False

        object_name = self._session.instance_to_object.get(id(instance))
        if not object_name:
            return False

        return self._commands.update_instance(
            object_name,
            {"position": {"x": x, "y": y, "z": z}},
        )

    def update_instance_rotation(
        self,
        instance: GITInstance,
        bearing: float | None = None,
        orientation: tuple[float, float, float, float] | None = None,
    ) -> bool:
        """Update instance rotation in Blender.

        Args:
            instance: GITInstance to update
            bearing: Bearing angle for non-camera instances
            orientation: Quaternion for cameras

        Returns:
            True if updated successfully
        """
        if not self.is_connected or self._session is None:
            return False

        object_name = self._session.instance_to_object.get(id(instance))
        if not object_name:
            return False

        properties: dict[str, Any] = {}
        if bearing is not None:
            properties["bearing"] = bearing
        if orientation is not None:
            properties["orientation"] = {
                "x": orientation[0],
                "y": orientation[1],
                "z": orientation[2],
                "w": orientation[3],
            }

        return self._commands.update_instance(object_name, properties)

    def select_instances(self, instances: list[GITInstance]) -> bool:
        """Select instances in Blender.

        Args:
            instances: List of GITInstances to select

        Returns:
            True if selection changed successfully
        """
        if not self.is_connected or self._session is None:
            return False

        object_names = []
        for instance in instances:
            name = self._session.instance_to_object.get(id(instance))
            if name:
                object_names.append(name)

        return self._commands.select_instances(object_names)

    def get_selected_instance_ids(self) -> list[int]:
        """Get IDs of currently selected instances in Blender.

        Returns:
            List of instance IDs (from id(instance))
        """
        if not self.is_connected or self._session is None:
            return []

        object_names = self._commands.get_selection()
        instance_ids = []

        for name in object_names:
            instance_id = self._session.object_to_instance.get(name)
            if instance_id is not None:
                instance_ids.append(instance_id)

        return instance_ids

    # =========================================================================
    # Layout Editing
    # =========================================================================

    def add_room(self, model: str, x: float, y: float, z: float) -> str | None:
        """Add a room to the layout in Blender.

        Args:
            model: Room model name
            x, y, z: Room position

        Returns:
            Blender object name if successful
        """
        if not self.is_connected:
            return None

        room_data = {
            "model": model,
            "position": {"x": x, "y": y, "z": z},
        }

        return self._commands.add_room(room_data)

    def update_room_position(
        self,
        object_name: str,
        x: float,
        y: float,
        z: float,
    ) -> bool:
        """Update room position in Blender.

        Args:
            object_name: Blender object name
            x, y, z: New position

        Returns:
            True if updated successfully
        """
        if not self.is_connected:
            return False

        return self._commands.update_room(
            object_name,
            {"position": {"x": x, "y": y, "z": z}},
        )

    # =========================================================================
    # Synchronization
    # =========================================================================

    def save_changes(self) -> tuple[dict | None, dict | None]:
        """Export modified data from Blender.

        Returns:
            Tuple of (lyt_data, git_data) or (None, None) on failure
        """
        if not self.is_connected:
            return None, None

        result = self._commands.save_changes()
        if result:
            return result.get("lyt"), result.get("git")

        return None, None

    # =========================================================================
    # Undo/Redo
    # =========================================================================

    def undo(self) -> bool:
        """Trigger undo in Blender.

        Returns:
            True if undo was successful
        """
        if not self.is_connected:
            return False
        return self._commands.undo()

    def redo(self) -> bool:
        """Trigger redo in Blender.

        Returns:
            True if redo was successful
        """
        if not self.is_connected:
            return False
        return self._commands.redo()

    # =========================================================================
    # Visibility and Render Settings
    # =========================================================================

    def set_visibility(self, instance_type: str, visible: bool) -> bool:
        """Set visibility of an instance type in Blender.

        Args:
            instance_type: Type name (creature, placeable, door, etc.)
            visible: Whether instances should be visible

        Returns:
            True if updated successfully
        """
        if not self.is_connected:
            return False
        return self._commands.set_visibility(instance_type, visible)

    def set_render_settings(
        self,
        backface_culling: bool | None = None,
        use_lightmap: bool | None = None,
        show_cursor: bool | None = None,
    ) -> bool:
        """Update render settings in Blender.

        Args:
            backface_culling: Enable/disable backface culling
            use_lightmap: Enable/disable lightmap usage
            show_cursor: Show/hide cursor

        Returns:
            True if updated successfully
        """
        if not self.is_connected:
            return False
        return self._commands.set_render_settings(
            backface_culling=backface_culling,
            use_lightmap=use_lightmap,
            show_cursor=show_cursor,
        )

    def set_camera_view(
        self,
        x: float,
        y: float,
        z: float,
        yaw: float | None = None,
        pitch: float | None = None,
        distance: float | None = None,
    ) -> bool:
        """Set viewport camera position and orientation in Blender.

        Args:
            x, y, z: Camera position
            yaw: Camera yaw angle (radians)
            pitch: Camera pitch angle (radians)
            distance: Camera distance (for orbit mode)

        Returns:
            True if updated successfully
        """
        if not self.is_connected:
            return False
        return self._commands.set_camera_view(x, y, z, yaw, pitch, distance)

    # =========================================================================
    # Layout Editing
    # =========================================================================

    def add_door_hook(
        self,
        room: str,
        door: str,
        x: float,
        y: float,
        z: float,
        orientation: tuple[float, float, float, float] | None = None,
    ) -> str | None:
        """Add a door hook to the layout in Blender.

        Args:
            room: Room model name
            door: Door name
            x, y, z: Door hook position
            orientation: Quaternion orientation (x, y, z, w)

        Returns:
            Blender object name if successful
        """
        if not self.is_connected:
            return None

        door_hook_data: dict[str, Any] = {
            "room": room,
            "door": door,
            "position": {"x": x, "y": y, "z": z},
        }
        if orientation is not None:
            door_hook_data["orientation"] = {
                "x": orientation[0],
                "y": orientation[1],
                "z": orientation[2],
                "w": orientation[3],
            }

        return self._commands.add_door_hook(door_hook_data)

    def add_track(self, model: str, x: float, y: float, z: float) -> str | None:
        """Add a track to the layout in Blender.

        Args:
            model: Track model name
            x, y, z: Track position

        Returns:
            Blender object name if successful
        """
        if not self.is_connected:
            return None

        track_data = {
            "model": model,
            "position": {"x": x, "y": y, "z": z},
        }

        return self._commands.add_track(track_data)

    def add_obstacle(self, model: str, x: float, y: float, z: float) -> str | None:
        """Add an obstacle to the layout in Blender.

        Args:
            model: Obstacle model name
            x, y, z: Obstacle position

        Returns:
            Blender object name if successful
        """
        if not self.is_connected:
            return None

        obstacle_data = {
            "model": model,
            "position": {"x": x, "y": y, "z": z},
        }

        return self._commands.add_obstacle(obstacle_data)

    def update_door_hook(
        self,
        object_name: str,
        room: str | None = None,
        door: str | None = None,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None,
    ) -> bool:
        """Update door hook properties in Blender.

        Args:
            object_name: Blender object name
            room: Room model name
            door: Door name
            x, y, z: New position

        Returns:
            True if updated successfully
        """
        if not self.is_connected:
            return False

        properties: dict[str, Any] = {}
        if room is not None:
            properties["room"] = room
        if door is not None:
            properties["door"] = door
        if x is not None or y is not None or z is not None:
            pos: dict[str, float] = {}
            if x is not None:
                pos["x"] = x
            if y is not None:
                pos["y"] = y
            if z is not None:
                pos["z"] = z
            properties["position"] = pos

        if not properties:
            return True

        return self._commands.update_door_hook(object_name, properties)

    def update_track(
        self,
        object_name: str,
        model: str | None = None,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None,
    ) -> bool:
        """Update track properties in Blender.

        Args:
            object_name: Blender object name
            model: Track model name
            x, y, z: New position

        Returns:
            True if updated successfully
        """
        if not self.is_connected:
            return False

        properties: dict[str, Any] = {}
        if model is not None:
            properties["model"] = model
        if x is not None or y is not None or z is not None:
            pos: dict[str, float] = {}
            if x is not None:
                pos["x"] = x
            if y is not None:
                pos["y"] = y
            if z is not None:
                pos["z"] = z
            properties["position"] = pos

        if not properties:
            return True

        return self._commands.update_track(object_name, properties)

    def update_obstacle(
        self,
        object_name: str,
        model: str | None = None,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None,
    ) -> bool:
        """Update obstacle properties in Blender.

        Args:
            object_name: Blender object name
            model: Obstacle model name
            x, y, z: New position

        Returns:
            True if updated successfully
        """
        if not self.is_connected:
            return False

        properties: dict[str, Any] = {}
        if model is not None:
            properties["model"] = model
        if x is not None or y is not None or z is not None:
            pos: dict[str, float] = {}
            if x is not None:
                pos["x"] = x
            if y is not None:
                pos["y"] = y
            if z is not None:
                pos["z"] = z
            properties["position"] = pos

        if not properties:
            return True

        return self._commands.update_obstacle(object_name, properties)

    def remove_lyt_element(self, object_name: str, element_type: str) -> bool:
        """Remove a LYT element from Blender.

        Args:
            object_name: Blender object name
            element_type: Type of element (room, door_hook, track, obstacle)

        Returns:
            True if removed successfully
        """
        if not self.is_connected:
            return False
        return self._commands.remove_lyt_element(object_name, element_type)

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_selection_changed(self, event):
        """Handle selection changed event from Blender."""
        if self._session is None:
            return

        runtime_ids = event.params.get("selected_runtime_ids") or []
        selected_names = event.params.get("selected", [])
        instance_ids = []

        for runtime_id in runtime_ids:
            try:
                runtime_key = int(runtime_id)
            except (TypeError, ValueError):
                continue
            instance = self._session.runtime_to_instance.get(runtime_key)
            if instance is not None:
                instance_ids.append(id(instance))

        if not instance_ids:
            for name in selected_names:
                instance_id = self._session.object_to_instance.get(name)
                if instance_id is not None:
                    instance_ids.append(instance_id)

        for callback in self._selection_callbacks:
            try:
                callback(instance_ids)
            except Exception as e:
                self._logger.error(f"Error in selection callback: {e}")

    def _on_transform_changed(self, event):
        """Handle transform changed event from Blender."""
        if self._session is None:
            return

        object_name = event.params.get("name")
        position = event.params.get("position")
        rotation = event.params.get("rotation")
        runtime_id = event.params.get("runtime_id")

        instance_id = None
        if runtime_id is not None:
            try:
                runtime_key = int(runtime_id)
            except (TypeError, ValueError):
                runtime_key = None
            if runtime_key is not None:
                instance = self._session.runtime_to_instance.get(runtime_key)
                if instance is not None:
                    instance_id = id(instance)

        if instance_id is None and object_name:
            instance_id = self._session.object_to_instance.get(object_name)
        if instance_id is None:
            return

        for callback in self._transform_callbacks:
            try:
                callback(instance_id, position, rotation)
            except Exception as e:
                self._logger.error(f"Error in transform callback: {e}")

    def _on_instance_added(self, event):
        """Handle instance added event from Blender."""
        instance_data = event.params.get("instance")
        if not instance_data:
            return
        runtime_id = event.params.get("runtime_id")
        object_name = event.params.get("name")
        if (
            runtime_id is not None
            and object_name
            and self._session is not None
        ):
            try:
                runtime_key = int(runtime_id)
            except (TypeError, ValueError):
                runtime_key = None
            if runtime_key is not None:
                self._session.runtime_to_object[runtime_key] = object_name
                instance = self._session.runtime_to_instance.get(runtime_key)
                if instance is not None:
                    instance_id = id(instance)
                    self._session.instance_to_object[instance_id] = object_name
                    self._session.object_to_instance[object_name] = instance_id

        for callback in self._instance_callbacks:
            try:
                callback("added", event.params)
            except Exception as e:
                self._logger.error(f"Error in instance callback: {e}")

    def _on_instance_removed(self, event):
        """Handle instance removed event from Blender."""
        object_name = event.params.get("name")
        if not object_name:
            return

        instance_id = None
        runtime_id = event.params.get("runtime_id")
        if self._session:
            instance_id = self._session.object_to_instance.pop(object_name, None)
            if instance_id:
                self._session.instance_to_object.pop(instance_id, None)
        if runtime_id and self._session:
            try:
                runtime_key = int(runtime_id)
            except (TypeError, ValueError):
                runtime_key = None
            if runtime_key is not None:
                self.unbind_runtime_instance(runtime_key)

        for callback in self._instance_callbacks:
            try:
                callback("removed", {"name": object_name, "id": instance_id, "runtime_id": runtime_id})
            except Exception as e:
                self._logger.error(f"Error in instance callback: {e}")

    def _on_instance_updated(self, event):
        """Handle property updates sent from Blender."""
        if self._session is None:
            return
        properties = event.params.get("properties", {})
        if not properties:
            return
        runtime_id = event.params.get("runtime_id")
        name = event.params.get("name")
        instance_id = None
        if runtime_id is not None:
            try:
                runtime_key = int(runtime_id)
            except (TypeError, ValueError):
                runtime_key = None
            if runtime_key is not None:
                instance = self._session.runtime_to_instance.get(runtime_key)
                if instance is not None:
                    instance_id = id(instance)
        if instance_id is None and name:
            instance_id = self._session.object_to_instance.get(name)
        if instance_id is None:
            return

        for callback in self._instance_update_callbacks:
            try:
                callback(instance_id, properties)
            except Exception as e:
                self._logger.error(f"Error in instance update callback: {e}")

    def _on_context_menu_requested(self, event):
        """Handle context-menu requests from Blender."""
        if self._session is None:
            return

        runtime_ids = event.params.get("runtime_ids") or []
        selected_names = event.params.get("selected", [])
        instance_ids: list[int] = []
        for runtime_id in runtime_ids:
            try:
                runtime_key = int(runtime_id)
            except (TypeError, ValueError):
                continue
            instance = self._session.runtime_to_instance.get(runtime_key)
            if instance is not None:
                instance_ids.append(id(instance))

        if not instance_ids:
            for name in selected_names:
                instance_id = self._session.object_to_instance.get(name)
                if instance_id is not None:
                    instance_ids.append(instance_id)

        for callback in self._context_menu_callbacks:
            try:
                callback(instance_ids)
            except Exception as e:
                self._logger.error(f"Error in context menu callback: {e}")


# Global controller instance
_controller: BlenderEditorController | None = None


def get_blender_controller() -> BlenderEditorController:
    """Get or create the global Blender editor controller."""
    global _controller
    if _controller is None:
        _controller = BlenderEditorController()
    return _controller

