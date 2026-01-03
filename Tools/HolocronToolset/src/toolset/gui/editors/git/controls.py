from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy.QtCore import Qt
from qtpy.QtGui import QUndoStack  # pyright: ignore[reportPrivateImportUsage]

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from pykotor.resource.generics.git import GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint
from toolset.data.misc import ControlItem
from toolset.gui.widgets.settings.editor_settings.git import GITSettings
from toolset.gui.widgets.settings.widgets.module_designer import ModuleDesignerSettings
from utility.common.geometry import Vector2, Vector3, Vector4

if qtpy.QT5:
    from qtpy.QtWidgets import QUndoStack
elif qtpy.QT6:
    from qtpy.QtGui import QUndoStack

if TYPE_CHECKING:
    from pykotor.resource.generics.git import GITInstance
    from toolset.gui.editors.git.git import GITEditor
    from toolset.gui.editors.git.mode import _InstanceMode
    from toolset.gui.editors.git.undo import DeleteCommand, MoveCommand, RotateCommand


def calculate_zoom_strength(
    delta_y: float,
    sens_setting: int,
) -> float:
    assert sens_setting is not None, "sens_setting cannot be None in calculate_zoom_strength({delta_y!r})"
    m = 0.00202
    b = 1
    factor_in = m * sens_setting + b
    return 1 / abs(factor_in) if delta_y < 0 else abs(factor_in)


class GITControlScheme:
    def __init__(self, editor: GITEditor):
        self.editor: GITEditor = editor
        self.settings: GITSettings = GITSettings()

        self.undo_stack: QUndoStack = QUndoStack(self.editor)
        self.initial_positions: dict[GITInstance, Vector3] = {}
        self.initial_rotations: dict[GITCamera | GITCreature | GITDoor | GITPlaceable | GITStore | GITWaypoint, Vector4 | float] = {}
        self.is_drag_moving: bool = False
        self.is_drag_rotating: bool = False

    def on_mouse_scrolled(
        self,
        delta: Vector2,
        buttons: set[Qt.MouseButton],
        keys: set[Qt.Key],
    ):
        if self.zoom_camera.satisfied(buttons, keys):
            if not delta.y:
                return  # sometimes it'll be zero when holding middlemouse-down.
            sens_setting = ModuleDesignerSettings().zoomCameraSensitivity2d
            zoom_factor = calculate_zoom_strength(delta.y, sens_setting)
            # RobustLogger.debug(f"on_mouse_scrolled zoom_camera (delta.y={delta.y}, zoom_factor={zoom_factor}, sensSetting={sensSetting}))")
            self.editor.zoom_camera(zoom_factor)

    def on_mouse_moved(
        self,
        screen: Vector2,
        screen_delta: Vector2,
        world: Vector2,
        world_delta: Vector2,
        buttons: set[Qt.MouseButton],
        keys: set[Qt.Key],
    ):
        # sourcery skip: extract-duplicate-method, remove-redundant-if, split-or-ifs
        from toolset.gui.editors.git.mode import _InstanceMode

        should_pan_camera = self.pan_camera.satisfied(buttons, keys)
        should_rotate_camera = self.rotate_camera.satisfied(buttons, keys)

        # Adjust world_delta if cursor is locked
        adjusted_world_delta = world_delta
        if should_pan_camera or should_rotate_camera:
            self.editor.ui.renderArea.do_cursor_lock(screen)
            adjusted_world_delta = Vector2(-world_delta.x, -world_delta.y)

        if should_pan_camera:
            moveSens = ModuleDesignerSettings().moveCameraSensitivity2d / 100
            # RobustLogger.debug(f"on_mouse_scrolled move_camera (delta.y={screenDelta.y}, sensSetting={moveSens}))")
            self.editor.move_camera(-world_delta.x * moveSens, -world_delta.y * moveSens)
        if should_rotate_camera:
            self._handle_camera_rotation(screen_delta)

        if self.move_selected.satisfied(buttons, keys):
            if not self.is_drag_moving and isinstance(self.editor._mode, _InstanceMode):  # noqa: SLF001
                # RobustLogger().debug("move_selected instance GITControlScheme")
                selection: list[GITInstance] = self.editor._mode.renderer2d.instance_selection.all()  # noqa: SLF001
                self.initial_positions = {instance: Vector3(*instance.position) for instance in selection}
                self.is_drag_moving = True
            self.editor.move_selected(adjusted_world_delta.x, adjusted_world_delta.y)
        if self.rotate_selected_to_point.satisfied(buttons, keys):
            if (
                not self.is_drag_rotating and not self.editor.ui.lockInstancesCheck.isChecked() and isinstance(self.editor._mode, _InstanceMode)  # noqa: SLF001
            ):
                self.is_drag_rotating = True
                RobustLogger().debug("rotateSelected instance in GITControlScheme")
                selection = self.editor._mode.renderer2d.instance_selection.all()  # noqa: SLF001
                for instance in selection:
                    if not isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                        continue  # doesn't support rotations.
                    self.initial_rotations[instance] = instance.orientation if isinstance(instance, GITCamera) else instance.bearing
            self.editor.rotate_selected_to_point(world.x, world.y)

    def _handle_camera_rotation(self, screen_delta: Vector2):
        delta_magnitude = abs(screen_delta.x)
        direction = -1 if screen_delta.x < 0 else 1 if screen_delta.x > 0 else 0
        rotate_sens = ModuleDesignerSettings().rotateCameraSensitivity2d / 1000
        rotate_amount = delta_magnitude * rotate_sens * direction
        # RobustLogger.debug(f"on_mouse_scrolled rotate_camera (delta_value={delta_magnitude}, rotateAmount={rotateAmount}, sensSetting={rotateSens}))")
        self.editor.rotate_camera(rotate_amount)

    def handle_undo_redo_from_long_action_finished(self):
        from toolset.gui.editors.git.undo import MoveCommand, RotateCommand

        # Check if we were dragging
        if self.is_drag_moving:
            for instance, old_position in self.initial_positions.items():
                new_position = instance.position
                if new_position != old_position:
                    RobustLogger().debug("GITControlScheme: Create the MoveCommand for undo/redo functionality")
                    move_command = MoveCommand(instance, old_position, new_position)
                    self.undo_stack.push(move_command)
                else:
                    RobustLogger().debug("GITControlScheme: Both old and new positions are the same %s", instance.resref)

            # Reset for the next drag operation
            self.initial_positions.clear()
            # RobustLogger().debug("No longer drag moving GITControlScheme")
            self.is_drag_moving = False

        if self.is_drag_rotating:
            for instance, old_rotation in self.initial_rotations.items():
                new_rotation = instance.orientation if isinstance(instance, GITCamera) else instance.bearing
                if new_rotation != old_rotation:
                    RobustLogger().debug(f"Create the RotateCommand for undo/redo functionality: {instance!r}")
                    self.undo_stack.push(RotateCommand(instance, old_rotation, new_rotation))
                else:
                    RobustLogger().debug("Both old and new rotations are the same for %s", instance.resref)

            # Reset for the next drag operation
            self.initial_rotations.clear()
            # RobustLogger().debug("No longer drag rotating GITControlScheme")
            self.is_drag_rotating = False

    def on_mouse_pressed(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        if self.duplicate_selected.satisfied(buttons, keys):
            position = self.editor.ui.renderArea.to_world_coords(screen.x, screen.y)
            self.editor.duplicate_selected(position)
        if self.select_underneath.satisfied(buttons, keys):
            self.editor.select_underneath()

    def on_mouse_released(
        self,
        screen: Vector2,
        buttons: set[Qt.MouseButton],
        keys: set[Qt.Key],
    ):
        self.handle_undo_redo_from_long_action_finished()

    def on_keyboard_pressed(
        self,
        buttons: set[Qt.MouseButton],
        keys: set[Qt.Key],
    ):
        from toolset.gui.editors.git.mode import _InstanceMode
        from toolset.gui.editors.git.undo import DeleteCommand

        if self.delete_selected.satisfied(buttons, keys):
            if isinstance(self.editor._mode, _InstanceMode):  # noqa: SLF001
                selection: list[GITInstance] = self.editor._mode.renderer2d.instance_selection.all()  # noqa: SLF001
                if selection:
                    self.undo_stack.push(DeleteCommand(self.editor._git, selection.copy(), self.editor))  # noqa: SLF001
            self.editor.delete_selected(no_undo_stack=True)

        if self.toggle_instance_lock.satisfied(buttons, keys):
            self.editor.ui.lockInstancesCheck.setChecked(not self.editor.ui.lockInstancesCheck.isChecked())

    def on_keyboard_released(
        self,
        buttons: set[Qt.MouseButton],
        keys: set[Qt.Key],
    ):
        self.handle_undo_redo_from_long_action_finished()

    # Use @property decorators to allow Users to change their settings without restarting the editor.
    @property
    def pan_camera(self) -> ControlItem:
        return ControlItem(self.settings.moveCameraBind)

    @property
    def rotate_camera(self) -> ControlItem:
        return ControlItem(self.settings.rotateCameraBind)

    @property
    def zoom_camera(self) -> ControlItem:
        return ControlItem(self.settings.zoomCameraBind)

    @property
    def rotate_selected_to_point(self) -> ControlItem:
        return ControlItem(self.settings.rotateSelectedToPointBind)

    @property
    def move_selected(self) -> ControlItem:
        return ControlItem(self.settings.moveSelectedBind)

    @property
    def select_underneath(self) -> ControlItem:
        return ControlItem(self.settings.selectUnderneathBind)

    @property
    def delete_selected(self) -> ControlItem:
        return ControlItem(self.settings.deleteSelectedBind)

    @property
    def duplicate_selected(self) -> ControlItem:
        return ControlItem(self.settings.duplicateSelectedBind)

    @property
    def toggle_instance_lock(self) -> ControlItem:
        return ControlItem(self.settings.toggleLockInstancesBind)

