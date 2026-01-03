from __future__ import annotations

import math
import os

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QDialog, QListWidgetItem, QMenu

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from pykotor.extract.installation import SearchLocation
from pykotor.resource.generics.git import (
    GIT,
    GITCamera,
    GITCreature,
    GITDoor,
    GITEncounter,
    GITPlaceable,
    GITSound,
    GITStore,
    GITTrigger,
    GITWaypoint,
)
from toolset.gui.dialogs.instance.camera import CameraDialog
from toolset.gui.dialogs.instance.creature import CreatureDialog
from toolset.gui.dialogs.instance.door import DoorDialog
from toolset.gui.dialogs.instance.encounter import EncounterDialog
from toolset.gui.dialogs.instance.placeable import PlaceableDialog
from toolset.gui.dialogs.instance.sound import SoundDialog
from toolset.gui.dialogs.instance.store import StoreDialog
from toolset.gui.dialogs.instance.trigger import TriggerDialog
from toolset.gui.dialogs.instance.waypoint import WaypointDialog
from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow, ResourceItems
from toolset.gui.widgets.renderer.walkmesh import GeomPoint
from toolset.utils.window import add_window, open_resource_editor
from utility.common.geometry import Vector2, Vector3

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtWidgets import QListWidget, QWidget

    from pykotor.extract.file import LocationResult, ResourceIdentifier
    from pykotor.resource.generics.git import GITInstance
    from toolset.data.installation import HTInstallation
    from toolset.gui.editors.git.git import GITEditor
    from toolset.gui.windows.module_designer import ModuleDesigner


def open_instance_dialog(
    parent: QWidget,
    instance: GITInstance,
    installation: HTInstallation,
) -> int:
    dialog = QDialog()

    if isinstance(instance, GITCamera):
        dialog = CameraDialog(parent, instance)
    elif isinstance(instance, GITCreature):
        dialog = CreatureDialog(parent, instance)
    elif isinstance(instance, GITDoor):
        dialog = DoorDialog(parent, instance, installation)
    elif isinstance(instance, GITEncounter):
        dialog = EncounterDialog(parent, instance)
    elif isinstance(instance, GITPlaceable):
        dialog = PlaceableDialog(parent, instance)
    elif isinstance(instance, GITTrigger):
        dialog = TriggerDialog(parent, instance, installation)
    elif isinstance(instance, GITSound):
        dialog = SoundDialog(parent, instance)
    elif isinstance(instance, GITStore):
        dialog = StoreDialog(parent, instance)
    elif isinstance(instance, GITWaypoint):
        dialog = WaypointDialog(parent, instance, installation)

    return dialog.exec()


class _Mode(ABC):
    def __init__(
        self,
        editor: GITEditor | ModuleDesigner,
        installation: HTInstallation | None,
        git: GIT,
    ):
        self._editor: GITEditor | ModuleDesigner = editor
        self._installation: HTInstallation | None = installation
        self._git: GIT = git

        self._ui = editor.ui
        self.renderer2d = editor.ui.renderArea if isinstance(editor, GITEditor) else editor.ui.flatRenderer

    def list_widget(self) -> QListWidget:
        return self._ui.listWidget if isinstance(self._editor, GITEditor) else self._ui.instanceList  # pyright: ignore[reportAttributeAccessIssue]

    @abstractmethod
    def on_item_selection_changed(self, item: QListWidgetItem): ...

    @abstractmethod
    def on_filter_edited(self, text: str): ...

    @abstractmethod
    def on_render_context_menu(self, world: Vector2, screen: QPoint): ...

    @abstractmethod
    def open_list_context_menu(self, item: QListWidgetItem, screen: QPoint): ...

    @abstractmethod
    def update_visibility(self): ...

    @abstractmethod
    def select_underneath(self): ...

    @abstractmethod
    def delete_selected(self, *, no_undo_stack: bool = False): ...

    @abstractmethod
    def duplicate_selected(self, position: Vector3): ...

    @abstractmethod
    def move_selected(self, x: float, y: float): ...

    @abstractmethod
    def rotate_selected(self, angle: float): ...

    @abstractmethod
    def rotate_selected_to_point(self, x: float, y: float): ...

    def move_camera(self, x: float, y: float):
        self.renderer2d.camera.nudge_position(x, y)

    def zoom_camera(self, amount: float):
        self.renderer2d.camera.nudge_zoom(amount)

    def rotate_camera(self, angle: float):
        self.renderer2d.camera.nudge_rotation(angle)

    @abstractmethod
    def update_status_bar(self, world: Vector2): ...


class _InstanceMode(_Mode):
    def __init__(
        self,
        editor: GITEditor | ModuleDesigner,
        installation: HTInstallation | None,
        git: GIT,
    ):
        super().__init__(editor, installation, git)
        RobustLogger().debug("init InstanceMode")
        self.renderer2d.hide_geom_points = True
        self.renderer2d.geometry_selection.clear()
        self.update_visibility()

    def set_selection(self, instances: list[GITInstance]):
        # set the renderer widget selection
        """Sets the selection of instances in the renderer and list widgets.

        Args:
        ----
            instances: list[GITInstance]: List of instances to select

        Processing Logic:
        ----------------
            - Select instances in the renderer widget
            - Block list widget signals to prevent selection changed signal
            - Loop through list widget items and select matching instances
            - Unblock list widget signals.
        """
        self.renderer2d.instance_selection.select(instances)

        # set the list widget selection
        self.list_widget().blockSignals(True)
        for i in range(self.list_widget().count()):
            item = self.list_widget().item(i)
            if item is None:
                continue
            instance = item.data(Qt.ItemDataRole.UserRole)
            if instance in instances:
                self.list_widget().setCurrentItem(item)
        self.list_widget().blockSignals(False)

    def edit_selected_instance(self):
        """Edits the selected instance.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Gets the selected instance from the render area
            - Checks if an instance is selected
            - Gets the last selected instance from the list
            - Opens an instance dialog to edit the selected instance properties
            - Rebuilds the instance list after editing.
        """
        selection: list[GITInstance] = self.renderer2d.instance_selection.all()
        assert self._installation is not None, "Installation is required to edit selected instance"

        if selection:
            instance: GITInstance = selection[-1]
            open_instance_dialog(self._editor, instance, self._installation)
            self.build_list()

    def edit_selected_instance_resource(self):
        selection: list[GITInstance] = self.renderer2d.instance_selection.all()

        if not selection:
            return
        instance: GITInstance = selection[-1]
        resident: ResourceIdentifier | None = instance.identifier()
        assert resident is not None, "resident cannot be None in edit_selected_instance_resource({instance!r})"
        resname, restype = resident.resname, resident.restype

        order: list[SearchLocation] = [SearchLocation.CHITIN, SearchLocation.MODULES, SearchLocation.OVERRIDE]
        assert self._installation is not None, "Installation is required to edit selected instance resource"
        search: list[LocationResult] = self._installation.location(resname, restype, order)

        if isinstance(self._editor, GITEditor):
            assert self._editor._filepath is not None, "filepath cannot be None in edit_selected_instance_resource({instance!r})"  # noqa: SLF001
            module_root: str = self._installation.get_module_root(self._editor._filepath.name).lower()  # noqa: SLF001
            edited_file_from_dot_mod = self._editor._filepath.suffix.lower() == ".mod"  # noqa: SLF001
        else:
            assert self._editor._module is not None, "module cannot be None in edit_selected_instance_resource({instance!r})"  # noqa: SLF001
            module_root = self._editor._module.root().lower()  # noqa: SLF001
            edited_file_from_dot_mod = self._editor._module.dot_mod  # noqa: SLF001

        for i, loc in reversed(list(enumerate(search))):
            if loc.filepath.parent.name.lower() == "modules":
                assert self._installation is not None, "Installation is required to edit selected instance resource"
                loc_module_root = self._installation.get_module_root(loc.filepath.name.lower())
                loc_is_dot_mod = loc.filepath.suffix.lower() == ".mod"
                if loc_module_root != module_root:
                    RobustLogger().debug(f"Removing location '{loc.filepath}' (not in our module '{module_root}')")
                    search.pop(i)
                elif loc_is_dot_mod != edited_file_from_dot_mod:
                    RobustLogger().debug(f"Removing location '{loc.filepath}' due to rim/mod check")
                    search.pop(i)
        if len(search) > 1:
            selection_window = FileSelectionWindow(search, self._installation)
            selection_window.show()
            selection_window.activateWindow()
            add_window(selection_window)
        elif search:
            open_resource_editor(search[0].as_file_resource(), self._installation)

    def edit_selected_instance_geometry(self):
        if self.renderer2d.instance_selection.last():
            self.renderer2d.instance_selection.last()
            self._editor.enter_geometry_mode()

    def edit_selected_instance_spawns(self):
        if self.renderer2d.instance_selection.last():
            self.renderer2d.instance_selection.last()
            # TODO: Implement spawn mode (UTE)
            # self._editor.enter_spawn_mode()

    def add_instance(self, instance: GITInstance):
        from toolset.gui.editors.git.undo import InsertCommand

        assert self._installation is not None, "Installation is required to add instance"
        if open_instance_dialog(self._editor, instance, self._installation):
            self._git.add(instance)
            undo_stack = self._editor._controls.undo_stack if isinstance(self._editor, GITEditor) else self._editor.undo_stack  # noqa: SLF001
            undo_stack.push(InsertCommand(self._git, instance, self._editor))
            self.build_list()

    def add_instance_actions_to_menu(self, instance: GITInstance, menu: QMenu):
        """Adds instance actions to a context menu.

        Args:
        ----
            instance: {The selected GIT instance object}
            menu: {The QMenu to add actions to}.
        """
        menu.addAction("Remove").triggered.connect(self.delete_selected)  # pyright: ignore[reportOptionalMemberAccess]
        if isinstance(self._editor, GITEditor):
            menu.addAction("Edit Instance").triggered.connect(self.edit_selected_instance)  # pyright: ignore[reportOptionalMemberAccess]

        action_edit_resource = menu.addAction("Edit Resource")
        action_edit_resource.triggered.connect(self.edit_selected_instance_resource)  # pyright: ignore[reportOptionalMemberAccess]
        action_edit_resource.setEnabled(not isinstance(instance, GITCamera))  # pyright: ignore[reportOptionalMemberAccess]
        menu.addAction(action_edit_resource)

        if isinstance(instance, (GITEncounter, GITTrigger)):
            menu.addAction("Edit Geometry").triggered.connect(self.edit_selected_instance_geometry)  # pyright: ignore[reportOptionalMemberAccess]

        if isinstance(instance, GITEncounter):
            menu.addAction("Edit Spawn Points").triggered.connect(self.edit_selected_instance_spawns)  # pyright: ignore[reportOptionalMemberAccess]
        menu.addSeparator()
        self.add_resource_sub_menu(menu, instance)

    def add_resource_sub_menu(self, menu: QMenu, instance: GITInstance) -> QMenu:
        if isinstance(instance, GITCamera):
            return menu
        locations = self._installation.location(*instance.identifier().unpack())  # pyright: ignore[reportOptionalMemberAccess]
        if not locations:
            return menu

        # Create the main context menu
        file_menu = menu.addMenu("File Actions")
        assert file_menu is not None

        if isinstance(self._editor, GITEditor):
            valid_filepaths = [self._editor._filepath]  # noqa: SLF001
        else:
            assert self._editor._module is not None  # noqa: SLF001
            valid_filepaths = [res.filepath() for res in self._editor._module.get_capsules() if res is not None]  # noqa: SLF001

        assert self._installation is not None, "Installation is required to add resource submenu"
        override_path = self._installation.override_path()
        # Iterate over each location to create submenus
        for result in locations:
            # Create a submenu for each location
            if result.filepath not in valid_filepaths:
                continue
            if os.path.commonpath([result.filepath, override_path]) == str(override_path):
                display_path = result.filepath.relative_to(override_path.parent)
            else:
                display_path = result.filepath.joinpath(str(instance.identifier())).relative_to(self._installation.path())
            loc_menu: QMenu | None = file_menu.addMenu(str(display_path))  # pyright: ignore[reportOptionalMemberAccess]
            assert loc_menu is not None, "loc_menu cannot be None in add_resource_submenu({instance!r})"
            ResourceItems(resources=[result]).build_menu(loc_menu)

        def more_info():
            selection_window = FileSelectionWindow(locations, self._installation)
            selection_window.show()
            selection_window.activateWindow()
            add_window(selection_window)

        file_menu.addAction("Details...").triggered.connect(more_info)  # pyright: ignore[reportOptionalMemberAccess]
        return menu

    def set_list_item_label(self, item: QListWidgetItem, instance: GITInstance):
        assert self._installation is not None, "Installation is required to set list item label"
        item.setData(Qt.ItemDataRole.UserRole, instance)
        item.setToolTip(self.get_instance_tooltip(instance))

        name: str | None = None

        assert isinstance(self._editor, GITEditor)
        if isinstance(instance, GITCamera):
            item.setText(str(instance.camera_id))
            return
        if isinstance(instance, GITCreature):
            if self._editor.settings.creatureLabel == "tag":
                name = self._editor.get_instance_external_tag(instance)
            elif self._editor.settings.creatureLabel == "name":
                name = self._editor.get_instance_external_name(instance)
        elif isinstance(instance, GITPlaceable):
            if self._editor.settings.placeableLabel == "tag":
                name = self._editor.get_instance_external_tag(instance)
            elif self._editor.settings.placeableLabel == "name":
                name = self._editor.get_instance_external_name(instance)
        elif isinstance(instance, GITDoor):
            if self._editor.settings.doorLabel == "tag":
                name = instance.tag
            elif self._editor.settings.doorLabel == "name":
                name = self._editor.get_instance_external_name(instance)
        elif isinstance(instance, GITStore):
            if self._editor.settings.storeLabel == "tag":
                name = self._editor.get_instance_external_tag(instance)
            elif self._editor.settings.storeLabel == "name":
                name = self._editor.get_instance_external_name(instance)
        elif isinstance(instance, GITSound):
            if self._editor.settings.soundLabel == "tag":
                name = self._editor.get_instance_external_tag(instance)
            elif self._editor.settings.soundLabel == "name":
                name = self._editor.get_instance_external_name(instance)
        elif isinstance(instance, GITWaypoint):
            if self._editor.settings.waypointLabel == "tag":
                name = instance.tag
            elif self._editor.settings.waypointLabel == "name":
                name = self._installation.string(instance.name, "")
        elif isinstance(instance, GITEncounter):
            if self._editor.settings.encounterLabel == "tag":
                name = self._editor.get_instance_external_tag(instance)
            elif self._editor.settings.encounterLabel == "name":
                name = self._editor.get_instance_external_name(instance)
        elif isinstance(instance, GITTrigger):
            if self._editor.settings.triggerLabel == "tag":
                name = instance.tag
            elif self._editor.settings.triggerLabel == "name":
                name = self._editor.get_instance_external_name(instance)

        ident = instance.identifier()
        text: str = name or ""
        if not name:
            text = ident and ident.resname or ""
            font = item.font()
            font.setItalic(True)
            item.setFont(font)

        item.setText(text)

    def get_instance_tooltip(self, instance: GITInstance) -> str:
        if isinstance(instance, GITCamera):
            return f"Struct Index: {self._git.index(instance)}\nCamera ID: {instance.camera_id}"
        return f"Struct Index: {self._git.index(instance)}\nResRef: {instance.identifier().resname}"  # pyright: ignore[reportOptionalMemberAccess]

    # region Interface Methods
    def on_filter_edited(self, text: str):
        self.renderer2d.instance_filter = text
        self.build_list()

    def on_item_selection_changed(self, item: QListWidgetItem):
        self.set_selection([] if item is None else [item.data(Qt.ItemDataRole.UserRole)])

    def update_status_bar(self, world: Vector2):
        if self.renderer2d.instances_under_mouse() and self.renderer2d.instances_under_mouse()[-1] is not None:
            instance: GITInstance = self.renderer2d.instances_under_mouse()[-1]
            resname = "" if isinstance(instance, GITCamera) else instance.identifier().resname  # pyright: ignore[reportOptionalMemberAccess]
            self._editor.statusBar().showMessage(f"({world.x:.1f}, {world.y:.1f}) {resname}")  # pyright: ignore[reportOptionalMemberAccess]
        else:
            self._editor.statusBar().showMessage(f"({world.x:.1f}, {world.y:.1f})")  # pyright: ignore[reportOptionalMemberAccess]

    def open_list_context_menu(self, item: QListWidgetItem, point: QPoint):  # pyright: ignore[reportIncompatibleMethodOverride]
        if item is None:
            return

        instance = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self.list_widget())

        self.add_instance_actions_to_menu(instance, menu)

        menu.popup(point)

    def on_render_context_menu(self, world: Vector2, point: QPoint):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Renders context menu on right click.

        Args:
        ----
            self: {The class instance}
            world: {The world coordinates clicked}
            point: {The screen coordinates clicked}.

        Renders context menu:
            - Adds instance creation actions if no selection
            - Adds instance actions to selected instance if single selection
            - Adds deselect action for instances under mouse
        """
        menu = QMenu(self.list_widget())
        self._get_render_context_menu(world, menu)
        menu.popup(point)

    def _get_render_context_menu(self, world: Vector2, menu: QMenu):
        under_mouse: list[GITInstance] = self.renderer2d.instances_under_mouse()
        if not self.renderer2d.instance_selection.isEmpty():
            last = self.renderer2d.instance_selection.last()
            assert last is not None
            self.add_instance_actions_to_menu(last, menu)
        else:
            self.add_insert_actions_to_menu(menu, world)
        if under_mouse:
            menu.addSeparator()
            for instance in under_mouse:
                icon = QIcon(self.renderer2d.instance_pixmap(instance))
                reference = "" if instance.identifier() is None else instance.identifier().resname  # pyright: ignore[reportOptionalMemberAccess]
                index = self._editor.git().index(instance)

                instance_action = menu.addAction(icon, f"[{index}] {reference}")
                instance_action.triggered.connect(lambda _=None, inst=instance: self.set_selection([inst]))  # pyright: ignore[reportOptionalMemberAccess]
                instance_action.setEnabled(instance not in self.renderer2d.instance_selection.all())  # pyright: ignore[reportOptionalMemberAccess]
                menu.addAction(instance_action)

    def add_insert_actions_to_menu(self, menu: QMenu, world: Vector2):
        menu.addAction("Insert Creature").triggered.connect(lambda: self.add_instance(GITCreature(world.x, world.y)))  # pyright: ignore[reportOptionalMemberAccess]
        menu.addAction("Insert Door").triggered.connect(lambda: self.add_instance(GITDoor(world.x, world.y)))  # pyright: ignore[reportOptionalMemberAccess]
        menu.addAction("Insert Placeable").triggered.connect(lambda: self.add_instance(GITPlaceable(world.x, world.y)))  # pyright: ignore[reportOptionalMemberAccess]
        menu.addAction("Insert Store").triggered.connect(lambda: self.add_instance(GITStore(world.x, world.y)))  # pyright: ignore[reportOptionalMemberAccess]
        menu.addAction("Insert Sound").triggered.connect(lambda: self.add_instance(GITSound(world.x, world.y)))  # pyright: ignore[reportOptionalMemberAccess]
        menu.addAction("Insert Waypoint").triggered.connect(lambda: self.add_instance(GITWaypoint(world.x, world.y)))  # pyright: ignore[reportOptionalMemberAccess]
        menu.addAction("Insert Camera").triggered.connect(lambda: self.add_instance(GITCamera(world.x, world.y)))  # pyright: ignore[reportOptionalMemberAccess]
        menu.addAction("Insert Encounter").triggered.connect(lambda: self.add_instance(GITEncounter(world.x, world.y)))  # pyright: ignore[reportOptionalMemberAccess]

        simple_trigger = GITTrigger(world.x, world.y)
        simple_trigger.geometry.extend(
            [
                Vector3(0.0, 0.0, 0.0),
                Vector3(3.0, 0.0, 0.0),
                Vector3(3.0, 3.0, 0.0),
                Vector3(0.0, 3.0, 0.0),
            ],
        )
        menu.addAction("Insert Trigger").triggered.connect(lambda: self.add_instance(simple_trigger))  # pyright: ignore[reportOptionalMemberAccess]

    def build_list(self):
        self.list_widget().clear()

        def instance_sort(inst: GITInstance) -> str:
            resident: ResourceIdentifier | None = inst.identifier()
            assert resident is not None, "resident cannot be None in instance_sort({inst!r})"
            text_to_sort: str = str(inst.camera_id) if isinstance(inst, GITCamera) else resident.resname
            return text_to_sort.rjust(9, "0") if isinstance(inst, GITCamera) else resident.restype.extension + text_to_sort

        instances: list[GITInstance] = sorted(self._git.instances(), key=instance_sort)
        for instance in instances:
            resident: ResourceIdentifier | None = instance.identifier()
            assert resident is not None, "resident cannot be None in build_list({instance!r})"
            filter_source: str = str(instance.camera_id) if isinstance(instance, GITCamera) else resident.resname
            is_visible: bool | None = self.renderer2d.is_instance_visible(instance)
            is_filtered: bool = self._ui.filterEdit.text().lower() in filter_source.lower()  # pyright: ignore[reportAttributeAccessIssue]

            if is_visible and is_filtered:
                icon = QIcon(self.renderer2d.instance_pixmap(instance))
                item = QListWidgetItem(icon, "")
                self.set_list_item_label(item, instance)
                self.list_widget().addItem(item)

    def update_visibility(self):
        self.renderer2d.hide_creatures = not self._ui.viewCreatureCheck.isChecked()
        self.renderer2d.hide_placeables = not self._ui.viewPlaceableCheck.isChecked()
        self.renderer2d.hide_doors = not self._ui.viewDoorCheck.isChecked()
        self.renderer2d.hide_triggers = not self._ui.viewTriggerCheck.isChecked()
        self.renderer2d.hide_encounters = not self._ui.viewEncounterCheck.isChecked()
        self.renderer2d.hide_waypoints = not self._ui.viewWaypointCheck.isChecked()
        self.renderer2d.hide_sounds = not self._ui.viewSoundCheck.isChecked()
        self.renderer2d.hide_stores = not self._ui.viewStoreCheck.isChecked()
        self.renderer2d.hide_cameras = not self._ui.viewCameraCheck.isChecked()
        self.build_list()

    def select_underneath(self):
        under_mouse: list[GITInstance] = self.renderer2d.instances_under_mouse()
        selection: list[GITInstance] = self.renderer2d.instance_selection.all()

        # Do not change the selection if the selected instance if its still underneath the mouse
        if selection and selection[0] in under_mouse:
            RobustLogger().info(f"Not changing selection: selected instance '{selection[0].classification()}' is still underneath the mouse.")
            return

        if under_mouse:
            self.set_selection([under_mouse[-1]])
        else:
            self.set_selection([])

    def delete_selected(
        self,
        *,
        no_undo_stack: bool = False,
    ):
        from toolset.gui.editors.git.undo import DeleteCommand

        selection = self.renderer2d.instance_selection.all()
        if no_undo_stack:
            for instance in selection:
                self._git.remove(instance)
                self.renderer2d.instance_selection.remove(instance)
        else:
            (self._editor._controls.undo_stack if isinstance(self._editor, GITEditor) else self._editor.undo_stack).push(
                DeleteCommand(self._git, selection.copy(), self._editor)
            )  # noqa: SLF001
        self.build_list()

    def duplicate_selected(
        self,
        position: Vector3,
        *,
        no_undo_stack: bool = False,
    ):
        from toolset.gui.editors.git.undo import DuplicateCommand

        selection = self.renderer2d.instance_selection.all()
        if selection:
            instance: GITInstance = deepcopy(selection[-1])
            if isinstance(instance, GITCamera):
                instance.camera_id = self._editor.git().next_camera_id()
            instance.position = position
            if no_undo_stack:
                self._git.add(instance)
                self.build_list()
                self.set_selection([instance])
            else:
                undo_stack = (
                    self._editor._controls.undo_stack  # noqa: SLF001
                    if isinstance(self._editor, GITEditor)
                    else self._editor.undo_stack
                )
                undo_stack.push(DuplicateCommand(self._git, [instance], self._editor))

    def move_selected(
        self,
        x: float,
        y: float,
        *,
        no_undo_stack: bool = False,
    ):
        if self._ui.lockInstancesCheck.isChecked():
            RobustLogger().info("Ignoring move_selected for instancemode, lockInstancesCheck is checked.")
            return

        for instance in self.renderer2d.instance_selection.all():
            instance.move(x, y, 0)

    def rotate_selected(self, angle: float):
        for instance in self.renderer2d.instance_selection.all():
            if isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                instance.rotate(angle, 0, 0)

    def rotate_selected_to_point(self, x: float, y: float):
        rotation_threshold = 0.05  # Threshold for rotation changes, adjust as needed
        for instance in self.renderer2d.instance_selection.all():
            current_angle = -math.atan2(x - instance.position.x, y - instance.position.y)
            current_angle = (current_angle + math.pi) % (2 * math.pi) - math.pi  # Normalize to -π to π
            yaw = ((instance.yaw() or 0.01) + math.pi) % (2 * math.pi) - math.pi  # Normalize to -π to π
            rotation_difference = ((yaw - current_angle) + math.pi) % (2 * math.pi) - math.pi
            if abs(rotation_difference) < rotation_threshold:
                continue
            if isinstance(instance, GITCamera):
                instance.rotate(yaw - current_angle, 0, 0)
            elif isinstance(instance, (GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                instance.rotate(-yaw + current_angle, 0, 0)

    # endregion


class _GeometryMode(_Mode):
    def __init__(
        self,
        editor: GITEditor | ModuleDesigner,
        installation: HTInstallation | None,
        git: GIT,
        *,
        hide_others: bool = True,
    ):
        super().__init__(editor, installation, git)

        if hide_others:
            self.renderer2d.hide_creatures = True
            self.renderer2d.hide_doors = True
            self.renderer2d.hide_placeables = True
            self.renderer2d.hide_sounds = True
            self.renderer2d.hide_stores = True
            self.renderer2d.hide_cameras = True
            self.renderer2d.hide_triggers = True
            self.renderer2d.hide_encounters = True
            self.renderer2d.hide_waypoints = True
        else:
            self.renderer2d.hide_encounters = False
            self.renderer2d.hide_triggers = False
        self.renderer2d.hide_geom_points = False

    def insert_point_at_mouse(self):
        screen: QPoint = self.renderer2d.mapFromGlobal(self._editor.cursor().pos())
        world: Vector3 = self.renderer2d.to_world_coords(screen.x(), screen.y())

        instance: GITInstance = self.renderer2d.instance_selection.get(0)
        assert isinstance(instance, (GITEncounter, GITTrigger))
        point: Vector3 = world - instance.position
        new_geom_point = GeomPoint(instance, point)
        instance.geometry.append(point)
        self.renderer2d.geom_points_under_mouse().append(new_geom_point)
        self.renderer2d.geometry_selection._selection.append(new_geom_point)  # noqa: SLF001
        RobustLogger().debug(f"Inserting new geompoint, instance {instance.identifier()}. Total points: {len(list(instance.geometry))}")

    # region Interface Methods
    def on_item_selection_changed(self, item: QListWidgetItem): ...

    def on_filter_edited(self, text: str): ...

    def update_status_bar(self, world: Vector2):
        instance: GITInstance | None = self.renderer2d.instance_selection.last()
        if instance:
            self._editor.statusBar().showMessage(f"({world.x:.1f}, {world.y:.1f}) Editing Geometry of {instance.identifier().resname}")  # pyright: ignore[reportOptionalMemberAccess]

    def on_render_context_menu(self, world: Vector2, screen: QPoint):
        menu = QMenu(self._editor)
        self._get_render_context_menu(world, menu)
        menu.popup(screen)

    def _get_render_context_menu(
        self,
        world: Vector2,
        menu: QMenu,
    ):
        if not self.renderer2d.geometry_selection.isEmpty():
            menu.addAction("Remove").triggered.connect(self.delete_selected)  # pyright: ignore[reportOptionalMemberAccess]

        if self.renderer2d.geometry_selection.count() == 0:
            menu.addAction("Insert").triggered.connect(self.insert_point_at_mouse)  # pyright: ignore[reportOptionalMemberAccess]

        menu.addSeparator()
        menu.addAction("Finish Editing").triggered.connect(self._editor.enter_instance_mode)  # pyright: ignore[reportOptionalMemberAccess]

    def open_list_context_menu(self, item: QListWidgetItem, screen: QPoint):
        ...

    def update_visibility(self):
        ...

    def select_underneath(self):
        under_mouse: list[GeomPoint] = self.renderer2d.geom_points_under_mouse()
        selection: list[GeomPoint] = self.renderer2d.geometry_selection.all()

        # Do not change the selection if the selected instance if its still underneath the mouse
        if selection and selection[0] in under_mouse:
            RobustLogger().info(f"Not changing selection: selected instance '{selection[0].instance.classification()}' is still underneath the mouse.")
            return
        self.renderer2d.geometry_selection.select(under_mouse or [])

    def delete_selected(self, *, no_undo_stack: bool = False):
        vertex: GeomPoint | None = self.renderer2d.geometry_selection.last()
        if vertex is None:
            RobustLogger().error("Could not delete last GeomPoint, there's none selected.")
            return
        instance: GITInstance = vertex.instance
        RobustLogger().debug(f"Removing last geometry point for instance {instance.identifier()}")
        self.renderer2d.geometry_selection.remove(GeomPoint(instance, vertex.point))

    def duplicate_selected(self, position: Vector3): ...

    def move_selected(self, x: float, y: float):
        for vertex in self.renderer2d.geometry_selection.all():
            vertex.point.x += x
            vertex.point.y += y

    def rotate_selected(self, angle: float): ...

    def rotate_selected_to_point(self, x: float, y: float): ...

    # endregion


class _SpawnMode(_Mode):
    def on_item_selection_changed(self, item: QListWidgetItem): ...

    def on_filter_edited(self, text: str): ...

    def on_render_context_menu(self, world: Vector2, screen: QPoint): ...

    def open_list_context_menu(self, item: QListWidgetItem, screen: QPoint): ...

    def update_visibility(self): ...

    def select_underneath(self): ...

    def delete_selected(self, *, no_undo_stack: bool = False): ...

    def duplicate_selected(self, position: Vector3): ...

    def move_selected(self, x: float, y: float): ...

    def rotate_selected(self, angle: float): ...

    def rotate_selected_to_point(self, x: float, y: float): ...

    def update_status_bar(self, world: Vector2): ...

