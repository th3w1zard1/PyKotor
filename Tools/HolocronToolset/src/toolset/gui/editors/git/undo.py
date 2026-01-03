from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Sequence

from qtpy.QtWidgets import QUndoCommand  # pyright: ignore[reportPrivateImportUsage]

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from utility.common.geometry import Vector3, Vector4

if TYPE_CHECKING:
    from pykotor.resource.generics.git import GIT, GITCamera, GITCreature, GITDoor, GITInstance, GITPlaceable, GITStore, GITWaypoint
    from toolset.gui.editors.git.git import GITEditor
    from toolset.gui.windows.module_designer import ModuleDesigner


class MoveCommand(QUndoCommand):
    def __init__(
        self,
        instance: GITInstance,
        old_position: Vector3,
        new_position: Vector3,
    ):
        RobustLogger().debug(f"Init movecommand with instance {instance.identifier()}")
        super().__init__()
        self.instance: GITInstance = instance
        self.old_position: Vector3 = old_position
        self.new_position: Vector3 = new_position

    def undo(self):
        RobustLogger().debug(f"Undo position: {self.instance.identifier()} (NEW {self.new_position} --> {self.old_position})")
        self.instance.position = self.old_position

    def redo(self):
        RobustLogger().debug(f"Undo position: {self.instance.identifier()} ({self.old_position} --> NEW {self.new_position})")
        self.instance.position = self.new_position


class RotateCommand(QUndoCommand):
    def __init__(
        self, instance: GITCamera | GITCreature | GITDoor | GITPlaceable | GITStore | GITWaypoint, old_orientation: Vector4 | float, new_orientation: Vector4 | float
    ):
        RobustLogger().debug(f"Init rotatecommand with instance: {instance.identifier()}")
        super().__init__()
        self.instance: GITCamera | GITCreature | GITDoor | GITPlaceable | GITStore | GITWaypoint = instance
        self.old_orientation: Vector4 | float = old_orientation
        self.new_orientation: Vector4 | float = new_orientation

    def undo(self):
        RobustLogger().debug(f"Undo rotation: {self.instance.identifier()} (NEW {self.new_orientation} --> {self.old_orientation})")
        if isinstance(self.instance, GITCamera):
            assert isinstance(self.old_orientation, Vector4)
            self.instance.orientation = self.old_orientation
        else:
            assert isinstance(self.old_orientation, float)
            self.instance.bearing = self.old_orientation

    def redo(self):
        RobustLogger().debug(f"Redo rotation: {self.instance.identifier()} ({self.old_orientation} --> NEW {self.new_orientation})")
        if isinstance(self.instance, GITCamera):
            assert isinstance(self.new_orientation, Vector4)
            self.instance.orientation = self.new_orientation
        else:
            assert isinstance(self.new_orientation, float)
            self.instance.bearing = self.new_orientation


class DuplicateCommand(QUndoCommand):
    def __init__(
        self,
        git: GIT,
        instances: Sequence[GITInstance],
        editor: GITEditor | ModuleDesigner,
    ):
        super().__init__()
        self.git: GIT = git
        self.instances: list[GITInstance] = list(instances)
        self.editor: GITEditor | ModuleDesigner = editor

    def undo(self):
        from toolset.gui.editors.git.mode import _InstanceMode

        self.editor.enter_instance_mode()
        for instance in self.instances:
            if instance not in self.git.instances():
                print(f"{instance!r} not found in instances: no duplicate to undo.")
                continue
            RobustLogger().debug(f"Undo duplicate: {instance.identifier()}")
            if isinstance(self.editor, GITEditor):
                self.editor._mode.renderer2d.instance_selection.select([instance])  # noqa: SLF001
            else:
                self.editor.set_selection([instance])
            self.editor.delete_selected(no_undo_stack=True)
        self.rebuild_instance_list()

    def rebuild_instance_list(self):
        from toolset.gui.editors.git.mode import _InstanceMode

        if isinstance(self.editor, GITEditor):
            self.editor.enter_instance_mode()
            assert isinstance(self.editor._mode, _InstanceMode)  # noqa: SLF001
            self.editor._mode.build_list()  # noqa: SLF001
        else:
            self.editor.enter_instance_mode()
            self.editor.rebuild_instance_list()

    def redo(self):
        from toolset.gui.editors.git.mode import _InstanceMode

        for instance in self.instances:
            if instance in self.git.instances():
                print(f"{instance!r} already found in instances: no duplicate to redo.")
                continue
            RobustLogger().debug(f"Redo duplicate: {instance.identifier()}")
            self.git.add(instance)
            if isinstance(self.editor, GITEditor):
                self.editor._mode.renderer2d.instance_selection.select([instance])  # noqa: SLF001
            else:
                self.editor.set_selection([instance])
        self.rebuild_instance_list()


class DeleteCommand(QUndoCommand):
    def __init__(
        self,
        git: GIT,
        instances: list[GITInstance],
        editor: GITEditor | ModuleDesigner,
    ):
        super().__init__()
        self.git: GIT = git
        self.instances: list[GITInstance] = instances
        self.editor: GITEditor | ModuleDesigner = editor

    def undo(self):
        RobustLogger().debug(f"Undo delete: {[repr(instance) for instance in self.instances]}")
        for instance in self.instances:
            if instance in self.git.instances():
                print(f"{instance!r} already found in instances: no deletecommand to undo.")
                continue
            self.git.add(instance)
        self.rebuild_instance_list()

    def rebuild_instance_list(self):
        from toolset.gui.editors.git.mode import _InstanceMode

        if isinstance(self.editor, GITEditor):
            self.editor.enter_instance_mode()
            assert isinstance(self.editor._mode, _InstanceMode)  # noqa: SLF001
            self.editor._mode.build_list()  # noqa: SLF001
        else:
            self.editor.enter_instance_mode()
            self.editor.rebuild_instance_list()

    def redo(self):
        RobustLogger().debug(f"Redo delete: {[repr(instance) for instance in self.instances]}")
        self.editor.enter_instance_mode()
        for instance in self.instances:
            if instance not in self.git.instances():
                print(f"{instance!r} not found in instances: no deletecommand to redo.")
                continue
            RobustLogger().debug(f"Redo delete: {instance!r}")
            if isinstance(self.editor, GITEditor):
                self.editor._mode.renderer2d.instance_selection.select([instance])  # noqa: SLF001
            else:
                self.editor.set_selection([instance])
            self.editor.delete_selected(no_undo_stack=True)
        self.rebuild_instance_list()


class InsertCommand(QUndoCommand):
    def __init__(
        self,
        git: GIT,
        instance: GITInstance,
        editor: GITEditor | ModuleDesigner,
    ):
        super().__init__()
        self.git: GIT = git
        self.instance: GITInstance = instance
        self._first_run: bool = True
        self.editor: GITEditor | ModuleDesigner = editor

    def undo(self):
        RobustLogger().debug(f"Undo insert: {self.instance.identifier()}")
        self.git.remove(self.instance)
        self.rebuild_instance_list()

    def rebuild_instance_list(self):
        from toolset.gui.editors.git.mode import _GeometryMode, _InstanceMode

        if isinstance(self.editor, GITEditor):
            old_mode = self.editor._mode  # noqa: SLF001
            self.editor.enter_instance_mode()
            assert isinstance(self.editor._mode, _InstanceMode)  # noqa: SLF001
            self.editor._mode.build_list()  # noqa: SLF001
            if isinstance(old_mode, _GeometryMode):
                self.editor.enter_geometry_mode()
            elif isinstance(old_mode, type(self.editor._mode)):  # _SpawnMode  # noqa: SLF001
                self.editor.enter_spawn_mode()
        else:
            self.editor.rebuild_instance_list()

    def redo(self):
        if self._first_run is True:
            print("Skipping first redo of InsertCommand.")
            self._first_run = False
            return
        RobustLogger().debug(f"Redo insert: {self.instance.identifier()}")
        self.git.add(self.instance)
        self.rebuild_instance_list()

