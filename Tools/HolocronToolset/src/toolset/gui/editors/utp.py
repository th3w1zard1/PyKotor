from __future__ import annotations

import os

from contextlib import suppress
from copy import deepcopy
from typing import TYPE_CHECKING

from qtpy.QtWidgets import QMessageBox, QSizePolicy

from loggerplus import RobustLogger
from pykotor.common.misc import ResRef
from pykotor.common.module import Module
from pykotor.common.stream import BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.dlg import DLG, dismantle_dlg
from pykotor.resource.generics.utp import UTP, dismantle_utp, read_utp
from pykotor.resource.type import ResourceType
from pykotor.tools import placeable
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.dialogs.inventory import InventoryEditor
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import open_resource_editor

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from pykotor.extract.file import ResourceResult
    from pykotor.extract.installation import SearchLocation
    from pykotor.resource.formats.twoda.twoda_data import TwoDA


class UTPEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        """Initialize Placeable Editor.

        Args:
        ----
            parent: {QWidget}: Parent widget
            installation: {HTInstallation}: HTInstallation object

        Processing Logic:
        ----------------
            1. Initialize supported resource types and call super constructor
            2. Initialize global settings object
            3. Get placeables 2DA cache from installation
            4. Initialize UTP object
            5. Set up UI from designer file
            6. Set up menus, signals and installation
            7. Update 3D preview and call new() to initialize editor.
        """
        supported: list[ResourceType] = [ResourceType.UTP, ResourceType.BTP]
        super().__init__(parent, "Placeable Editor", "placeable", supported, supported, installation)

        self.globalSettings: GlobalSettings = GlobalSettings()
        self._placeables2DA: TwoDA | None = installation.ht_get_cache_2da("placeables")
        self._utp = UTP()

        from toolset.uic.qtpy.editors.utp import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Setup event filter to prevent scroll wheel interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        
        self._setup_menus()
        self._add_help_action()
        self._setup_signals()
        if installation is not None:  # will only be none in the unittests
            self._setup_installation(installation)

        # Initialize model info widget state (collapsed by default)
        self.ui.modelInfoLabel.setVisible(False)
        self.ui.modelInfoSummaryLabel.setVisible(True)

        self.update3dPreview()
        self.new()
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

    def _setup_signals(self):
        """Connect UI buttons to their respective methods.

        Processing Logic:
        ----------------
            - Connect tagGenerateButton clicked signal to generate_tag method
            - Connect resrefGenerateButton clicked signal to generate_resref method
            - Connect conversationModifyButton clicked signal to edit_conversation method
            - Connect inventoryButton clicked signal to open_inventory method

            - Connect appearanceSelect currentIndexChanged signal to update3dPreview method
            - Connect actionShowPreview triggered signal to toggle_preview method
        """
        self.ui.tagGenerateButton.clicked.connect(self.generate_tag)
        self.ui.resrefGenerateButton.clicked.connect(self.generate_resref)
        self.ui.conversationModifyButton.clicked.connect(self.edit_conversation)
        self.ui.inventoryButton.clicked.connect(self.open_inventory)

        self.ui.appearanceSelect.currentIndexChanged.connect(self.update3dPreview)
        self.ui.actionShowPreview.triggered.connect(self.toggle_preview)
        self.ui.modelInfoGroupBox.toggled.connect(self._on_model_info_toggled)
        # Connect to renderer's signal to update texture info when textures finish loading
        self.ui.previewRenderer.resourcesLoaded.connect(self._on_textures_loaded)

    def _setup_installation(
        self,
        installation: HTInstallation,
    ):
        """Sets up the installation for editing.

        Args:
        ----
            installation: {HTInstallation}: The installation to set up for editing.

        Processing Logic:
        ----------------
            - Sets the internal installation reference and updates UI elements
            - Loads required 2da files if not already loaded
            - Populates appearance and faction dropdowns from loaded 2da data
            - Hides/shows TSL specific UI elements based on installation type
        """
        self._installation = installation
        self.ui.nameEdit.set_installation(installation)
        self.ui.previewRenderer.installation = installation

        # Load required 2da files if they have not been loaded already
        required: list[str] = [HTInstallation.TwoDA_PLACEABLES, HTInstallation.TwoDA_FACTIONS]
        installation.ht_batch_cache_2da(required)

        appearances: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_PLACEABLES)
        factions: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_FACTIONS)

        self.ui.appearanceSelect.set_context(appearances, installation, HTInstallation.TwoDA_PLACEABLES)
        self.ui.factionSelect.set_context(factions, installation, HTInstallation.TwoDA_FACTIONS)

        if appearances is not None:
            self.ui.appearanceSelect.set_items(appearances.get_column("label"))
        if factions is not None:
            self.ui.factionSelect.set_items(factions.get_column("label"))

        self.ui.notBlastableCheckbox.setVisible(installation.tsl)
        self.ui.difficultyModSpin.setVisible(installation.tsl)
        self.ui.difficultySpin.setVisible(installation.tsl)
        self.ui.difficultyLabel.setVisible(installation.tsl)
        self.ui.difficultyModLabel.setVisible(installation.tsl)

        installation.setup_file_context_menu(self.ui.onClosedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onDamagedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onDeathEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onEndConversationEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onOpenFailedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onHeartbeatSelect, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onInventoryEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onMeleeAttackEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onSpellEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onOpenEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onLockEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onUnlockEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onUsedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onUserDefinedSelect, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.conversationEdit, [ResourceType.DLG])

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        utp = read_utp(data)
        self._loadUTP(utp)

        self.update_item_count()

    def _loadUTP(self, utp: UTP):
        """Loads UTP data into UI elements.

        Args:
        ----
            utp (UTP): UTP object to load data from.

        Loads UTP data:
            - Sets UI element values like name, tag, etc from UTP properties
            - Sets checkboxes, dropdowns, spinboxes from UTP boolean and integer properties
            - Sets script text fields from UTP script properties
            - Sets comment text from UTP comment property.
        """
        self._utp: UTP = utp

        # Basic
        self.ui.nameEdit.set_locstring(utp.name)
        self.ui.tagEdit.setText(utp.tag)
        self.ui.resrefEdit.setText(str(utp.resref))
        self.ui.appearanceSelect.setCurrentIndex(utp.appearance_id)
        self.ui.conversationEdit.set_combo_box_text(str(utp.conversation))

        # Advanced
        self.ui.hasInventoryCheckbox.setChecked(utp.has_inventory)
        self.ui.partyInteractCheckbox.setChecked(utp.party_interact)
        self.ui.useableCheckbox.setChecked(utp.useable)
        self.ui.min1HpCheckbox.setChecked(utp.min1_hp)
        self.ui.plotCheckbox.setChecked(utp.plot)
        self.ui.staticCheckbox.setChecked(utp.static)
        self.ui.notBlastableCheckbox.setChecked(utp.not_blastable)
        self.ui.factionSelect.setCurrentIndex(utp.faction_id)
        self.ui.animationState.setValue(utp.animation_state)
        self.ui.currenHpSpin.setValue(utp.current_hp)
        self.ui.maxHpSpin.setValue(utp.maximum_hp)
        self.ui.hardnessSpin.setValue(utp.hardness)
        self.ui.fortitudeSpin.setValue(utp.fortitude)
        self.ui.reflexSpin.setValue(utp.reflex)
        self.ui.willSpin.setValue(utp.will)

        # Lock
        self.ui.needKeyCheckbox.setChecked(utp.key_required)
        self.ui.removeKeyCheckbox.setChecked(utp.auto_remove_key)
        self.ui.keyEdit.setText(utp.key_name)
        self.ui.lockedCheckbox.setChecked(utp.locked)
        self.ui.openLockSpin.setValue(utp.unlock_dc)
        self.ui.difficultySpin.setValue(utp.unlock_diff)
        self.ui.difficultyModSpin.setValue(utp.unlock_diff_mod)

        assert self._installation is not None
        self.relevant_script_resnames = sorted(iter({res.resname().lower() for res in self._installation.get_relevant_resources(ResourceType.NCS, self._filepath)}))

        self.ui.onClosedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onDamagedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onDeathEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onEndConversationEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onOpenFailedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onHeartbeatSelect.populate_combo_box(self.relevant_script_resnames)
        self.ui.onInventoryEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onMeleeAttackEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onSpellEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onOpenEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onLockEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onUnlockEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onUsedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onUserDefinedSelect.populate_combo_box(self.relevant_script_resnames)
        self.ui.conversationEdit.populate_combo_box(sorted(res.resname() for res in self._installation.get_relevant_resources(ResourceType.DLG)))

        # Scripts
        self.ui.onClosedEdit.set_combo_box_text(str(utp.on_closed))
        self.ui.onDamagedEdit.set_combo_box_text(str(utp.on_damaged))
        self.ui.onDeathEdit.set_combo_box_text(str(utp.on_death))
        self.ui.onEndConversationEdit.set_combo_box_text(str(utp.on_end_dialog))
        self.ui.onOpenFailedEdit.set_combo_box_text(str(utp.on_open_failed))
        self.ui.onHeartbeatSelect.set_combo_box_text(str(utp.on_heartbeat))
        self.ui.onInventoryEdit.set_combo_box_text(str(utp.on_inventory))
        self.ui.onMeleeAttackEdit.set_combo_box_text(str(utp.on_melee_attack))
        self.ui.onSpellEdit.set_combo_box_text(str(utp.on_force_power))
        self.ui.onOpenEdit.set_combo_box_text(str(utp.on_open))
        self.ui.onLockEdit.set_combo_box_text(str(utp.on_lock))
        self.ui.onUnlockEdit.set_combo_box_text(str(utp.on_unlock))
        self.ui.onUsedEdit.set_combo_box_text(str(utp.on_used))
        self.ui.onUserDefinedSelect.set_combo_box_text(str(utp.on_user_defined))

        # Comments
        self.ui.commentsEdit.setPlainText(utp.comment)

        self.update_item_count()

    def build(self) -> tuple[bytes, bytes]:
        """Builds a UTP from UI fields.

        Args:
        ----
            self: The class instance
            utp: The UTP object

        Returns:
        -------
            data: The built UTP data
            mdx b"": Empty byte string

        Builds a UTP by:
            - Setting UTP properties like name, tag, scripts from UI elements
            - Writing the constructed UTP to a byte array
            - Returning the byte array and an empty byte string.
        """
        utp: UTP = deepcopy(self._utp)

        # Basic
        utp.name = self.ui.nameEdit.locstring()
        utp.tag = self.ui.tagEdit.text()
        utp.resref = ResRef(self.ui.resrefEdit.text())
        utp.appearance_id = self.ui.appearanceSelect.currentIndex()
        utp.conversation = ResRef(self.ui.conversationEdit.currentText())
        utp.has_inventory = self.ui.hasInventoryCheckbox.isChecked()

        # Advanced
        utp.min1_hp = self.ui.min1HpCheckbox.isChecked()
        utp.party_interact = self.ui.partyInteractCheckbox.isChecked()
        utp.useable = self.ui.useableCheckbox.isChecked()
        utp.plot = self.ui.plotCheckbox.isChecked()
        utp.static = self.ui.staticCheckbox.isChecked()
        utp.not_blastable = self.ui.notBlastableCheckbox.isChecked()
        utp.faction_id = self.ui.factionSelect.currentIndex()
        utp.animation_state = self.ui.animationState.value()
        utp.current_hp = self.ui.currenHpSpin.value()
        utp.maximum_hp = self.ui.maxHpSpin.value()
        utp.hardness = self.ui.hardnessSpin.value()
        utp.fortitude = self.ui.fortitudeSpin.value()
        utp.reflex = self.ui.reflexSpin.value()
        utp.will = self.ui.willSpin.value()

        # Lock
        utp.locked = self.ui.lockedCheckbox.isChecked()
        utp.unlock_dc = self.ui.openLockSpin.value()
        utp.unlock_diff = self.ui.difficultySpin.value()
        utp.unlock_diff_mod = self.ui.difficultyModSpin.value()
        utp.key_required = self.ui.needKeyCheckbox.isChecked()
        utp.auto_remove_key = self.ui.removeKeyCheckbox.isChecked()
        utp.key_name = self.ui.keyEdit.text()

        # Scripts
        utp.on_closed = ResRef(self.ui.onClosedEdit.currentText())
        utp.on_damaged = ResRef(self.ui.onDamagedEdit.currentText())
        utp.on_death = ResRef(self.ui.onDeathEdit.currentText())
        utp.on_end_dialog = ResRef(self.ui.onEndConversationEdit.currentText())
        utp.on_open_failed = ResRef(self.ui.onOpenFailedEdit.currentText())
        utp.on_heartbeat = ResRef(self.ui.onHeartbeatSelect.currentText())
        utp.on_inventory = ResRef(self.ui.onInventoryEdit.currentText())
        utp.on_melee_attack = ResRef(self.ui.onMeleeAttackEdit.currentText())
        utp.on_force_power = ResRef(self.ui.onSpellEdit.currentText())
        utp.on_open = ResRef(self.ui.onOpenEdit.currentText())
        utp.on_lock = ResRef(self.ui.onLockEdit.currentText())
        utp.on_unlock = ResRef(self.ui.onUnlockEdit.currentText())
        utp.on_used = ResRef(self.ui.onUsedEdit.currentText())
        utp.on_user_defined = ResRef(self.ui.onUserDefinedSelect.currentText())

        # Comments
        utp.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_utp(utp)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTP(UTP())

    def update_item_count(self):
        from toolset.gui.common.localization import trf

        self.ui.inventoryCountLabel.setText(trf("Total Items: {count}", count=len(self._utp.inventory)))

    def change_name(self):
        if self._installation is None:
            self.blink_window()
            return
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring())
        if dialog.exec():
            self._load_locstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)

    def generate_tag(self):
        if not self.ui.resrefEdit.text():
            self.generate_resref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generate_resref(self):
        if self._resname is not None and self._resname != "":
            self.ui.resrefEdit.setText(self._resname)
        else:
            self.ui.resrefEdit.setText("m00xx_plc_000")

    def edit_conversation(self):
        """Edits a conversation. This function is duplicated in most UT-prefixed gffs."""
        resname = self.ui.conversationEdit.currentText()
        data, filepath = None, None

        if not resname or not resname.strip():
            QMessageBox(QMessageBox.Icon.Critical, "Failed to open DLG Editor", "Conversation field cannot be blank.").exec()
            return

        assert self._installation is not None
        search: ResourceResult | None = self._installation.resource(resname, ResourceType.DLG)
        if search is None:
            msgbox: int = QMessageBox(
                QMessageBox.Icon.Information,
                "DLG file not found",
                "Do you wish to create a file in the override?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            ).exec()
            if QMessageBox.StandardButton.Yes == msgbox:
                data = bytearray()

                write_gff(dismantle_dlg(DLG()), data)
                filepath = self._installation.override_path() / f"{resname}.dlg"
                writer = BinaryWriter.to_file(filepath)
                writer.write_bytes(data)
                writer.close()
        else:
            resname, restype, filepath, data = search

        if data is not None:
            open_resource_editor(filepath, resname, ResourceType.DLG, data, self._installation, self)

    def open_inventory(self):
        """Opens inventory editor for the module.

        Processing Logic:
        ----------------
            - Gets list of capsule paths for the module
            - Creates capsule objects from the paths
            - Initializes InventoryEditor with the capsules and other data
            - Runs editor and updates inventory if changes were made.
        """
        if self._installation is None:
            self.blink_window()
            return
        capsules: list[Capsule] = []
        with suppress(Exception):
            root: str = Module.filepath_to_root(self._filepath)
            moduleNames: list[str] = [path for path in self._installation.module_names() if root in path and path != self._filepath]
            newCapsules: list[Capsule] = [Capsule(self._installation.module_path() / mod_filename) for mod_filename in moduleNames]
            capsules.extend(newCapsules)

        inventoryEditor = InventoryEditor(
            self,
            self._installation,
            capsules,
            [],
            self._utp.inventory,
            {},
            droid=False,
            hide_equipment=True,
        )
        if inventoryEditor.exec():
            self._utp.inventory = inventoryEditor.inventory
            self.update_item_count()

    def toggle_preview(self):
        self.globalSettings.showPreviewUTP = not self.globalSettings.showPreviewUTP
        self.update3dPreview()

    def update3dPreview(self):
        """Updates the model preview.

        Processing Logic:
        ----------------
            - Build the data and model name from the provided data
            - Get the MDL and MDX resources from the installation based on the model name
            - If both resources exist, set them on the preview renderer
            - If not, clear out any existing model from the preview.
            - Hides BOTH the preview renderer AND the model info groupbox when preview is hidden.
        """
        show_preview = self.globalSettings.showPreviewUTP
        self.ui.previewRenderer.setVisible(show_preview)
        self.ui.modelInfoGroupBox.setVisible(show_preview)
        self.ui.actionShowPreview.setChecked(show_preview)

        if show_preview:
            self._update_model()
        else:
            self.setMinimumSize(374, 457)

    def _update_model(self):
        """Updates the model preview.

        Processing Logic:
        ----------------
            - Build the data and model name from the provided data
            - Get the MDL and MDX resources from the installation based on the model name
            - If both resources exist, set them on the preview renderer
            - If not, clear out any existing model from the preview
            - Update the model info label with resource location details
        """
        if self._installation is None:
            self.blink_window()
            return

        self.setMinimumSize(674, 457)
        data, _ = self.build()
        utp = read_utp(data)

        # Build model information text - focus on low-level technical details
        info_lines: list[str] = []

        # Validate placeables.2da before calling placeable.get_model() to prevent crashes
        if self._placeables2DA is None:
            self.ui.previewRenderer.clear_model()
            info_lines.append("❌ placeables.2da not loaded")
            self.ui.modelInfoLabel.setText("\n".join(info_lines))
            return

        modelname: str = placeable.get_model(utp, self._installation, placeables=self._placeables2DA)

        if not modelname or not modelname.strip():
            RobustLogger().warning("Placeable '%s.%s' has no model to render!", self._resname, self._restype)
            self.ui.previewRenderer.clear_model()
            info_lines.append("❌ Model lookup failed")
            if self._placeables2DA is not None:
                try:
                    row = self._placeables2DA.get_row(utp.appearance_id)
                    if row.has_string("modelname"):
                        modelname_col = row.get_string("modelname")
                        if not modelname_col or modelname_col.strip() == "****":
                            modelname_col = "[empty]"
                    else:
                        modelname_col = "[column missing]"
                    info_lines.append(f"placeables.2da row {utp.appearance_id}: 'modelname' = '{modelname_col}'")
                except (IndexError, KeyError):
                    info_lines.append(f"⚠️ placeables.2da row {utp.appearance_id} not found")
            self.ui.modelInfoLabel.setText("\n".join(info_lines))
            return

        # Show the lookup process
        info_lines.append(f"Model resolved: '{modelname}'")
        if self._placeables2DA is not None:
            try:
                row = self._placeables2DA.get_row(utp.appearance_id)
                info_lines.append(f"Lookup: placeables.2da[row {utp.appearance_id}]['modelname']")
            except (IndexError, KeyError):
                pass

        mdl: ResourceResult | None = self._installation.resource(modelname, ResourceType.MDL)
        mdx: ResourceResult | None = self._installation.resource(modelname, ResourceType.MDX)

        if mdl is not None and mdx is not None:
            self.ui.previewRenderer.set_model(mdl.data, mdx.data)

            # Show full file paths and source locations
            try:
                mdl_rel_path = mdl.filepath.relative_to(self._installation.path())
                info_lines.append(f"MDL: {mdl_rel_path}")
            except ValueError:
                info_lines.append(f"MDL: {mdl.filepath}")

            mdl_source = self._get_source_location_type(mdl.filepath)
            if mdl_source:
                info_lines.append(f"  └─ Source: {mdl_source}")

            try:
                mdx_rel_path = mdx.filepath.relative_to(self._installation.path())
                info_lines.append(f"MDX: {mdx_rel_path}")
            except ValueError:
                info_lines.append(f"MDX: {mdx.filepath}")

            mdx_source = self._get_source_location_type(mdx.filepath)
            if mdx_source:
                info_lines.append(f"  └─ Source: {mdx_source}")

            # Show placeholder for textures - actual info will be populated when textures finish loading
            info_lines.append("")
            info_lines.append("Textures: Loading...")
        else:
            self.ui.previewRenderer.clear_model()
            info_lines.append("❌ Resources not found in installation:")
            if mdl is None:
                info_lines.append(f"  Missing: {modelname}.mdl")
                # Show search locations that were checked
                info_lines.append("  (Searched: Override → Modules → Chitin BIFs)")
            if mdx is None:
                info_lines.append(f"  Missing: {modelname}.mdx")
                info_lines.append("  (Searched: Override → Modules → Chitin BIFs)")

        full_text = "\n".join(info_lines)
        self.ui.modelInfoLabel.setText(full_text)

        # Update summary (first line or key info)
        summary = info_lines[0] if info_lines else "No model information"
        if len(info_lines) > 1 and mdl is not None and mdx is not None:
            # Show model name and source in summary
            try:
                mdl_rel = mdl.filepath.relative_to(self._installation.path()) if self._installation else str(mdl.filepath)
                summary = f"{modelname} → {mdl_rel}"
            except (ValueError, AttributeError):
                summary = f"{modelname} → {mdl.filepath}"
        self.ui.modelInfoSummaryLabel.setText(summary)

    def _on_model_info_toggled(self, checked: bool):
        """Handle model info groupbox toggle."""
        self.ui.modelInfoLabel.setVisible(checked)
        if not checked:
            # When collapsed, ensure summary is visible
            self.ui.modelInfoSummaryLabel.setVisible(True)

    def _format_search_order(self, search_order: list[SearchLocation]) -> str:
        """Format search order list into human-readable string."""
        from pykotor.extract.installation import SearchLocation

        location_names = {
            SearchLocation.OVERRIDE: "Override",
            SearchLocation.CUSTOM_MODULES: "Custom Modules",
            SearchLocation.MODULES: "Modules",
            SearchLocation.CHITIN: "Chitin BIFs",
            SearchLocation.TEXTURES_TPA: "Texture Pack A",
            SearchLocation.TEXTURES_TPB: "Texture Pack B",
            SearchLocation.TEXTURES_TPC: "Texture Pack C",
            SearchLocation.TEXTURES_GUI: "GUI Textures",
        }
        return " → ".join(location_names.get(loc, str(loc)) for loc in search_order)

    def _on_textures_loaded(self):
        """Called when renderer signals that textures have finished loading.

        Reads the EXACT lookup info from scene.texture_lookup_info - this is the
        SAME info that the renderer used when loading textures. No additional lookups.
        """
        scene = self.ui.previewRenderer._scene
        if scene is None:
            return

        # Get the EXACT lookup info stored by the renderer when it loaded textures
        texture_lookup_info = getattr(scene, "texture_lookup_info", {})

        if not texture_lookup_info:
            RobustLogger().debug("_on_textures_loaded: No texture_lookup_info available yet")
            return

        RobustLogger().debug(f"_on_textures_loaded: Found {len(texture_lookup_info)} textures with lookup info")

        # Get current model info text and update the texture section
        current_text = self.ui.modelInfoLabel.text()

        # Find and replace the "Textures: Loading..." line
        lines = current_text.split("\n")
        new_lines: list[str] = []
        skip_old_texture_section = False

        for line in lines:
            if "Textures:" in line:
                skip_old_texture_section = True
                # Add new texture section
                new_lines.append("")
                new_lines.append(f"Textures ({len(texture_lookup_info)} loaded by renderer):")

                for tex_name, lookup_info in sorted(texture_lookup_info.items()):
                    if lookup_info.get("found"):
                        filepath = lookup_info.get("filepath")
                        if filepath:
                            try:
                                if self._installation:
                                    rel_path = os.path.relpath(filepath, self._installation.path())
                                else:
                                    rel_path = str(filepath)
                                new_lines.append(f"  {tex_name}: {rel_path}")
                            except (ValueError, AttributeError):
                                new_lines.append(f"  {tex_name}: {filepath}")

                            source = self._get_source_location_type(filepath)
                            if source:
                                new_lines.append(f"    └─ Source: {source}")
                        else:
                            new_lines.append(f"  {tex_name}: ✓ Loaded")
                    else:
                        search_order = lookup_info.get("search_order", [])
                        search_str = self._format_search_order(search_order) if search_order else "Unknown"
                        new_lines.append(f"  {tex_name}: ❌ Not found")
                        new_lines.append(f"    └─ Searched: {search_str}")
            elif skip_old_texture_section and line.startswith("  "):
                # Skip old texture lines (indented)
                continue
            elif skip_old_texture_section and not line.startswith("  ") and line.strip():
                # End of old texture section
                skip_old_texture_section = False
                new_lines.append(line)
            elif not skip_old_texture_section:
                new_lines.append(line)

        self.ui.modelInfoLabel.setText("\n".join(new_lines))

    def _get_source_location_type(self, filepath: os.PathLike | str) -> str | None:
        """Determines the source location type for a given filepath.

        Args:
        ----
            filepath: The filepath to analyze

        Returns:
        -------
            A string describing the source location type, or None if unknown
        """
        if self._installation is None:
            return None

        try:
            path = self._installation.path()
            rel_path = os.path.relpath(filepath, path)
            if rel_path:
                path_str = str(rel_path).lower().replace("\\", "/")
                if "override" in path_str:
                    return "Override folder"
                if path_str.startswith("modules/"):
                    if path_str.endswith(".mod"):
                        return "Module (.mod)"
                    if path_str.endswith(".rim"):
                        return "Module (.rim)"
                    return "Module"
                if "chitin.key" in path_str or "data" in path_str:
                    return "Chitin BIFs"
                if "textures" in path_str:
                    return "Texture pack"
        except (ValueError, AttributeError):
            pass
        return None
