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
from typing import TYPE_CHECKING, Any

from loggerplus import RobustLogger

from toolset.blender.ipc_client import BlenderCommands, BlenderIPCClient, ConnectionState, get_ipc_client
from toolset.blender.serializers import (
    deserialize_git_instance,
    deserialize_lyt,
    serialize_git,
    serialize_git_instance,
    serialize_lyt,
    serialize_lyt_room,
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

    def __post_init__(self):
        if self.instance_to_object is None:
            self.instance_to_object = {}
        if self.object_to_instance is None:
            self.object_to_instance = {}


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
        self._selection_callbacks: list[callable] = []
        self._transform_callbacks: list[callable] = []
        self._instance_callbacks: list[callable] = []

        # Register for Blender events
        self._client.on_event("selection_changed", self._on_selection_changed)
        self._client.on_event("transform_changed", self._on_transform_changed)
        self._client.on_event("instance_added", self._on_instance_added)
        self._client.on_event("instance_removed", self._on_instance_removed)

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

    def on_state_change(self, callback: callable):
        """Register callback for connection state changes."""
        self._client.on_state_change(callback)

    def on_selection_changed(self, callback: callable):
        """Register callback for selection changes in Blender."""
        self._selection_callbacks.append(callback)

    def on_transform_changed(self, callback: callable):
        """Register callback for transform changes in Blender."""
        self._transform_callbacks.append(callback)

    def on_instance_changed(self, callback: callable):
        """Register callback for instance add/remove in Blender."""
        self._instance_callbacks.append(callback)

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
            self._logger.info(f"Loaded module '{module_root}' in Blender")
        else:
            self._logger.error(f"Failed to load module '{module_root}' in Blender")

        return success

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
        object_name = self._commands.add_instance(instance_data)

        if object_name and self._session:
            instance_id = id(instance)
            self._session.instance_to_object[instance_id] = object_name
            self._session.object_to_instance[object_name] = instance_id

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
        object_name = self._session.instance_to_object.get(instance_id)

        if not object_name:
            return False

        success = self._commands.remove_instance(object_name)

        if success:
            self._session.instance_to_object.pop(instance_id, None)
            self._session.object_to_instance.pop(object_name, None)

        return success

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
    # Event Handlers
    # =========================================================================

    def _on_selection_changed(self, event):
        """Handle selection changed event from Blender."""
        if self._session is None:
            return

        selected_names = event.params.get("selected", [])
        instance_ids = []

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

        for callback in self._instance_callbacks:
            try:
                callback("added", instance_data)
            except Exception as e:
                self._logger.error(f"Error in instance callback: {e}")

    def _on_instance_removed(self, event):
        """Handle instance removed event from Blender."""
        object_name = event.params.get("name")
        if not object_name:
            return

        instance_id = None
        if self._session:
            instance_id = self._session.object_to_instance.pop(object_name, None)
            if instance_id:
                self._session.instance_to_object.pop(instance_id, None)

        for callback in self._instance_callbacks:
            try:
                callback("removed", {"name": object_name, "id": instance_id})
            except Exception as e:
                self._logger.error(f"Error in instance callback: {e}")


# Global controller instance
_controller: BlenderEditorController | None = None


def get_blender_controller() -> BlenderEditorController:
    """Get or create the global Blender editor controller."""
    global _controller
    if _controller is None:
        _controller = BlenderEditorController()
    return _controller

