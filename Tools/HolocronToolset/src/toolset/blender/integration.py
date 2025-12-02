"""Blender integration for toolset editors.

This module provides mixin classes and utilities for integrating
Blender as an alternative editor in Module Designer, GIT Editor,
and Indoor Map Builder.
"""

from __future__ import annotations

import subprocess
import threading

from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QMessageBox, QWidget

from toolset.blender import BlenderInfo, launch_blender_with_ipc
from toolset.blender.commands import BlenderEditorController, BlenderEditorMode, get_blender_controller
from toolset.blender.detection import get_blender_settings
from toolset.blender.ipc_client import ConnectionState

from pykotor.resource.generics.git import (
    GITCamera,
    GITCreature,
    GITDoor,
    GITPlaceable,
    GITStore,
    GITWaypoint,
)

if TYPE_CHECKING:
    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.generics.git import GIT, GITInstance


class BlenderEditorMixin:
    """Mixin class for adding Blender integration to editors.

    This mixin provides:
    - Blender detection and launch
    - IPC connection management
    - Module/GIT loading in Blender
    - Selection synchronization
    - Transform synchronization

    Usage:
        class MyEditor(QMainWindow, BlenderEditorMixin):
            def __init__(self, ...):
                super().__init__(...)
                self._init_blender_integration(BlenderEditorMode.MODULE_DESIGNER)
    """

    _blender_mode: BlenderEditorMode
    _blender_controller: BlenderEditorController | None = None
    _blender_process: subprocess.Popen | None = None
    _blender_enabled: bool = False
    _blender_connection_timer: QTimer | None = None
    _blender_output_thread: threading.Thread | None = None

    def _init_blender_integration(self, mode: BlenderEditorMode):
        """Initialize Blender integration.

        Args:
            mode: Editor mode for Blender
        """
        self._blender_mode = mode
        self._blender_controller = None
        self._blender_process = None
        self._blender_enabled = False
        self._blender_output_thread = None

        # Setup connection monitoring timer
        self._blender_connection_timer = QTimer()
        self._blender_connection_timer.timeout.connect(self._check_blender_connection)

    def is_blender_mode(self) -> bool:
        """Check if Blender mode is active."""
        return self._blender_enabled

    def start_blender_mode(
        self,
        lyt: LYT | None = None,
        git: GIT | None = None,
        walkmeshes: list[BWM] | None = None,
        module_root: str = "",
        installation_path: str | Path = "",
    ) -> bool:
        """Start Blender mode and load data.

        Args:
            lyt: Layout resource (optional)
            git: GIT resource (optional)
            walkmeshes: List of walkmesh resources (optional)
            module_root: Module root name
            installation_path: Path to KotOR installation

        Returns:
            True if Blender mode started successfully
        """
        settings = get_blender_settings()
        blender_info = settings.get_blender_info()

        if not blender_info.is_valid:
            QMessageBox.warning(
                self,  # type: ignore[arg-type]
                "Blender Not Found",
                blender_info.error,
            )
            return False

        if not blender_info.has_kotorblender:
            result = QMessageBox.warning(
                self,  # type: ignore[arg-type]
                "kotorblender Not Found",
                f"{blender_info.error}\n\nDo you want to continue without kotorblender support?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if result != QMessageBox.Yes:
                return False

        # Launch Blender with IPC
        self._blender_process = launch_blender_with_ipc(
            blender_info,
            ipc_port=settings.ipc_port,
            installation_path=str(installation_path) if installation_path else None,
            capture_output=True,
        )

        if self._blender_process is None:
            QMessageBox.critical(
                self,  # type: ignore[arg-type]
                "Launch Failed",
                "Failed to launch Blender. Please check your Blender installation.",
            )
            return False

        # Wait for Blender to start and connect
        self._blender_enabled = True
        if self._blender_process.stdout is not None:
            self._start_blender_output_listener()
        self._connect_to_blender(lyt, git, walkmeshes, module_root, installation_path)

        return True

    def _connect_to_blender(
        self,
        lyt: LYT | None,
        git: GIT | None,
        walkmeshes: list[BWM] | None,
        module_root: str,
        installation_path: str | Path,
    ):
        """Connect to Blender IPC server and load data."""
        self._blender_controller = get_blender_controller()

        # Store data for loading after connection
        self._pending_lyt = lyt
        self._pending_git = git
        self._pending_walkmeshes = walkmeshes or []
        self._pending_module_root = module_root
        self._pending_installation_path = str(installation_path)

        # Register callbacks
        self._blender_controller.on_state_change(self._on_blender_state_change)
        self._blender_controller.on_selection_changed(self._on_blender_selection_changed)
        self._blender_controller.on_transform_changed(self._on_blender_transform_changed)
        self._blender_controller.on_context_menu_requested(self._on_blender_context_menu_requested)
        self._blender_controller.on_instance_changed(self._on_blender_instance_changed)
        self._blender_controller.on_instance_updated(self._on_blender_instance_updated)
        
        # Register material/texture change handler
        if hasattr(self._blender_controller, 'on_material_changed'):
            self._blender_controller.on_material_changed(self._on_blender_material_changed)

        # Start connection attempts
        self._connection_attempts = 0
        self._max_connection_attempts = 10

        if self._blender_connection_timer:
            self._blender_connection_timer.start(1000)  # Try every second

    def _check_blender_connection(self):
        """Check and attempt Blender connection."""
        if self._blender_controller is None:
            return

        if self._blender_controller.is_connected:
            # Already connected
            if self._blender_connection_timer:
                self._blender_connection_timer.stop()
            return

        self._connection_attempts += 1

        if self._connection_attempts > self._max_connection_attempts:
            if self._blender_connection_timer:
                self._blender_connection_timer.stop()
            QMessageBox.warning(
                self,  # type: ignore[arg-type]
                "Connection Failed",
                "Failed to connect to Blender IPC server.\n"
                "Please make sure Blender started correctly and kotorblender is installed.",
            )
            self.stop_blender_mode()
            self._on_blender_connection_failed()
            return

        # Attempt connection
        if self._blender_controller.connect(timeout=2.0):
            if self._blender_connection_timer:
                self._blender_connection_timer.stop()
            self._load_data_in_blender()

    def _load_data_in_blender(self):
        """Load pending data in Blender."""
        if self._blender_controller is None:
            return

        if self._pending_git is None or self._pending_lyt is None:
            RobustLogger().warning("Cannot load Blender session without both LYT and GIT data")
            return

        pending_git = self._pending_git
        pending_lyt = self._pending_lyt

        success = self._blender_controller.load_module(
            mode=self._blender_mode,
            lyt=pending_lyt,
            git=pending_git,
            walkmeshes=self._pending_walkmeshes,
            module_root=self._pending_module_root,
            installation_path=self._pending_installation_path,
        )

        if success:
            RobustLogger().info("Module loaded in Blender successfully")
            self._on_blender_module_loaded()
        else:
            QMessageBox.warning(
                self,  # type: ignore[arg-type]
                "Load Failed",
                "Failed to load module in Blender. Check the Blender console for errors.",
            )

    def stop_blender_mode(self):
        """Stop Blender mode and disconnect."""
        if self._blender_connection_timer:
            self._blender_connection_timer.stop()

        if self._blender_controller:
            self._blender_controller.unload_module()
            self._blender_controller.disconnect()
            self._blender_controller = None

        if self._blender_process:
            try:
                self._blender_process.terminate()
                self._blender_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._blender_process.kill()
            self._blender_process = None
        self._blender_output_thread = None

        self._blender_enabled = False
        self._on_blender_mode_stopped()

    def sync_selection_to_blender(self, instances: list[GITInstance]):
        """Sync selection to Blender.

        Args:
            instances: List of selected instances
        """
        if not self._blender_enabled or self._blender_controller is None:
            return

        self._blender_controller.select_instances(instances)

    def sync_instance_to_blender(self, instance: GITInstance):
        """Sync instance position/rotation to Blender.

        Args:
            instance: Instance to sync
        """
        if not self._blender_enabled or self._blender_controller is None:
            return

        self._blender_controller.update_instance_position(
            instance,
            instance.position.x,
            instance.position.y,
            instance.position.z,
        )

        # Update rotation if applicable
        if isinstance(instance, (GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
            self._blender_controller.update_instance_rotation(
                instance,
                bearing=instance.bearing,
            )
        elif isinstance(instance, GITCamera):
            ori = instance.orientation
            self._blender_controller.update_instance_rotation(
                instance,
                orientation=(ori.x, ori.y, ori.z, ori.w),
            )

    def add_instance_to_blender(self, instance: GITInstance) -> str | None:
        """Add an instance to Blender.

        Args:
            instance: Instance to add

        Returns:
            Blender object name if successful
        """
        if not self._blender_enabled or self._blender_controller is None:
            return None

        return self._blender_controller.add_instance(instance)

    def remove_instance_from_blender(self, instance: GITInstance) -> bool:
        """Remove an instance from Blender.

        Args:
            instance: Instance to remove

        Returns:
            True if removed successfully
        """
        if not self._blender_enabled or self._blender_controller is None:
            return False

        return self._blender_controller.remove_instance(instance)

    def save_blender_changes(self) -> tuple[dict | None, dict | None]:
        """Get modified data from Blender.

        Returns:
            Tuple of (lyt_data, git_data)
        """
        if not self._blender_enabled or self._blender_controller is None:
            return None, None

        return self._blender_controller.save_changes()

    def blender_undo(self) -> bool:
        """Trigger undo in Blender.

        Returns:
            True if undo was successful
        """
        if not self._blender_enabled or self._blender_controller is None:
            return False
        return self._blender_controller.undo()

    def blender_redo(self) -> bool:
        """Trigger redo in Blender.

        Returns:
            True if redo was successful
        """
        if not self._blender_enabled or self._blender_controller is None:
            return False
        return self._blender_controller.redo()

    # Override these methods in subclasses
    def _on_blender_state_change(self, state: ConnectionState):
        """Handle Blender connection state change."""
        RobustLogger().debug(f"Blender connection state: {state}")

    def _on_blender_selection_changed(self, instance_ids: list[int]):
        """Handle selection change from Blender.

        Override this to update the toolset selection.
        """
        pass

    def _on_blender_transform_changed(
        self,
        instance_id: int,
        position: dict | None,
        rotation: dict | None,
    ):
        """Handle transform change from Blender.

        Override this to update instance transforms in the toolset.
        """
        pass

    def _on_blender_module_loaded(self):
        """Called when module is loaded in Blender.

        Override this to perform post-load actions.
        """
        pass

    def _on_blender_mode_stopped(self):
        """Called when Blender mode is stopped.

        Override this to perform cleanup.
        """
        pass

    def _on_blender_context_menu_requested(self, instance_ids: list[int]):
        """Handle context menu requests from Blender selections."""
        RobustLogger().debug(f"Blender context menu requested for {len(instance_ids)} instances")

    def _on_blender_instance_changed(self, action: str, payload: dict):
        """Handle instance add/remove notifications from Blender."""
        RobustLogger().debug(f"Blender instance change action={action} payload_keys={list(payload.keys())}")

    def _on_blender_instance_updated(self, instance_id: int, properties: dict):
        """Handle granular property updates streamed from Blender."""
        RobustLogger().debug(f"Blender updated instance={instance_id} props={list(properties.keys())}")

    def _on_blender_connection_failed(self):
        """Hook invoked when IPC connection retries are exhausted."""
        pass

    def _on_blender_material_changed(self, payload: dict):
        """Handle material/texture changes from Blender.
        
        Override this to update textures/models in the toolset.
        
        Args:
            payload: Event payload containing:
                - object_name: Blender object name
                - material_slot: Material slot index
                - material: Material data (name, textures, etc.)
                - model_name: KotOR model name (if applicable)
        """
        RobustLogger().debug(f"Blender material changed: {payload.get('object_name')} slot={payload.get('material_slot')}")

    def _start_blender_output_listener(self):
        """Start background thread that relays Blender stdout/stderr."""

        process = self._blender_process
        if process is None or process.stdout is None:
            return
        stdout_pipe = process.stdout

        def _pump():
            try:
                for line in stdout_pipe:
                    if not line:
                        break
                    self._on_blender_output(line.rstrip("\n"))
            except Exception as exc:  # noqa: BLE001
                RobustLogger().debug(f"Blender output reader stopped: {exc}")

        self._blender_output_thread = threading.Thread(target=_pump, name="BlenderIPCOutput", daemon=True)
        self._blender_output_thread.start()

    def _on_blender_output(self, line: str):
        """Handle stdout lines emitted by the Blender process."""
        RobustLogger().debug(f"[Blender] {line}")


def check_blender_and_ask(
    parent: QWidget,
    context: str = "Module Designer",
) -> tuple[bool, BlenderInfo | None]:
    """Check for Blender and ask user if they want to use it.

    Args:
        parent: Parent widget for dialogs
        context: Context name for the dialog

    Returns:
        Tuple of (use_blender, blender_info)
    """
    from toolset.gui.dialogs.blender_choice import show_blender_choice_dialog

    choice, _ = show_blender_choice_dialog(parent, context)

    if choice == "cancelled":
        return False, None
    elif choice == "blender":
        settings = get_blender_settings()
        info = settings.get_blender_info()
        return True, info
    else:
        return False, None

