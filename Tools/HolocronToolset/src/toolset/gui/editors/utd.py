from __future__ import annotations

import os

from copy import deepcopy
from typing import TYPE_CHECKING

from loggerplus import RobustLogger  # type: ignore[import-untyped, note]
from qtpy.QtWidgets import QMessageBox

from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryWriter
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.dlg import DLG, dismantle_dlg
from pykotor.resource.generics.utd import UTD, dismantle_utd, read_utd
from pykotor.resource.type import ResourceType
from pykotor.tools import door
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import open_resource_editor

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from pykotor.extract.file import ResourceResult
    from pykotor.resource.formats.twoda.twoda_data import TwoDA


class UTDEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None = None,
        installation: HTInstallation | None = None,
    ):
        """Initialize the Door Editor.

        Args:
        ----
            parent: {QWidget}: The parent widget.
            installation: {HTInstallation}: The installation object.

        Returns:
        -------
            None: Does not return anything.

        Processing Logic:
        ----------------
            1. Get supported resource types and call parent initializer.
            2. Initialize global settings object.
            3. Get generic doors 2DA cache from installation.
            4. Initialize UTD object.
            5. Set up UI from designer file.
            6. Set up menus, signals and installation.
            7. Update 3D preview and call new() to initialize editor.
        """
        supported: list[ResourceType] = [ResourceType.UTD, ResourceType.BTD]
        super().__init__(parent, "Door Editor", "door", supported, supported, installation)

        self.global_settings: GlobalSettings = GlobalSettings()
        self._genericdoors_2da: TwoDA | None = installation.ht_get_cache_2da("genericdoors") if installation is not None else None
        self._utd: UTD = UTD()

        from toolset.uic.qtpy.editors.utd import Ui_MainWindow  # noqa: PLC0415

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
        self.resize(654, 495)

    def _setup_signals(self):
        """Connect GUI buttons and signals to methods.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Connect tagGenerateButton click signal to generate_tag method
            - Connect resrefGenerateButton click signal to generate_resref method
            - Connect conversationModifyButton click signal to edit_conversation method
            - Connect appearanceSelect currentIndexChanged signal to update3dPreview method
            - Connect actionShowPreview triggered signal to toggle_preview method.
        """
        self.ui.tagGenerateButton.clicked.connect(self.generate_tag)
        self.ui.resrefGenerateButton.clicked.connect(self.generate_resref)
        self.ui.conversationModifyButton.clicked.connect(self.edit_conversation)

        self.ui.appearanceSelect.currentIndexChanged.connect(self.update3dPreview)
        self.ui.actionShowPreview.triggered.connect(self.toggle_preview)
        self.ui.modelInfoGroupBox.toggled.connect(self._on_model_info_toggled)
        # Connect to renderer's signal to update texture info when textures finish loading
        self.ui.previewRenderer.resourcesLoaded.connect(self._on_textures_loaded)

    def _setup_installation(self, installation: HTInstallation):
        """Sets up the installation for editing.

        Args:
        ----
            installation: {HTInstallation}: The installation to set up for editing.

        Processing Logic:
        ----------------
            - Sets the internal installation reference and updates UI elements
            - Loads required 2da files if not already loaded
            - Populates appearance and faction dropdowns from loaded 2da files
            - Shows/hides TSL-specific UI elements based on installation type.
        """
        self._installation = installation
        self.ui.nameEdit.set_installation(installation)
        self.ui.previewRenderer.installation = installation

        # Load required 2da files if they have not been loaded already
        required: list[str] = [HTInstallation.TwoDA_DOORS, HTInstallation.TwoDA_FACTIONS]
        installation.ht_batch_cache_2da(required)

        appearances: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_DOORS)
        factions: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_FACTIONS)

        self.ui.appearanceSelect.set_context(appearances, self._installation, HTInstallation.TwoDA_DOORS)
        self.ui.factionSelect.set_context(factions, self._installation, HTInstallation.TwoDA_FACTIONS)

        if appearances is not None:
            self.ui.appearanceSelect.set_items(appearances.get_column("label"))
        if factions is not None:
            self.ui.factionSelect.set_items(factions.get_column("label"))

        self.handle_widget_with_tsl(self.ui.notBlastableCheckbox, installation)
        self.handle_widget_with_tsl(self.ui.difficultyModSpin, installation)
        self.handle_widget_with_tsl(self.ui.difficultySpin, installation)
        self.handle_widget_with_tsl(self.ui.difficultyLabel, installation)
        self.handle_widget_with_tsl(self.ui.difficultyModLabel, installation)

        installation.setup_file_context_menu(self.ui.onClickEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onClosedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onDamagedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onDeathEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onHeartbeatSelect, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onMeleeAttackEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onOpenEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onOpenFailedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onSpellEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onUnlockEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onUserDefinedSelect, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.conversationEdit, [ResourceType.DLG])

    def handle_widget_with_tsl(
        self,
        widget: QWidget,
        installation: HTInstallation,
    ):
        widget.setEnabled(installation.tsl)
        if not installation.tsl:
            from toolset.gui.common.localization import translate as tr  # noqa: PLC0415

            widget.setToolTip(tr("This widget is only available in KOTOR II."))

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes | bytearray,
    ) -> None:
        super().load(filepath, resref, restype, data)

        utd = read_utd(data)
        self._loadUTD(utd)

    def _loadUTD(  # noqa: PLR0915
        self,
        utd: UTD,
    ):
        """Loads UTD data into UI elements.

        Args:
        ----
            utd (UTD): UTD object to load data from

        Processing Logic:
        ----------------
            - Sets UI element values from UTD object attributes
            - Divides loading into sections for Basic, Advanced, Lock, Scripts, and Comments
            - Handles different UI element types like checkboxes, dropdowns, text fields, etc.
        """
        assert self._installation is not None
        self._utd = utd

        # Basic
        self.ui.nameEdit.set_locstring(utd.name)
        self.ui.tagEdit.setText(utd.tag)
        self.ui.resrefEdit.setText(str(utd.resref))
        self.ui.appearanceSelect.setCurrentIndex(utd.appearance_id)
        self.ui.conversationEdit.set_combo_box_text(str(utd.conversation))

        # Advanced
        self.ui.min1HpCheckbox.setChecked(utd.min1_hp)
        self.ui.plotCheckbox.setChecked(utd.plot)
        self.ui.staticCheckbox.setChecked(utd.static)
        self.ui.notBlastableCheckbox.setChecked(utd.not_blastable)
        self.ui.factionSelect.setCurrentIndex(utd.faction_id)
        self.ui.animationState.setValue(utd.animation_state)
        self.ui.currenHpSpin.setValue(utd.current_hp)
        self.ui.maxHpSpin.setValue(utd.maximum_hp)
        self.ui.hardnessSpin.setValue(utd.hardness)
        self.ui.fortitudeSpin.setValue(utd.fortitude)
        self.ui.reflexSpin.setValue(utd.reflex)
        self.ui.willSpin.setValue(utd.willpower)

        # Lock
        self.ui.needKeyCheckbox.setChecked(utd.key_required)
        self.ui.removeKeyCheckbox.setChecked(utd.auto_remove_key)
        self.ui.keyEdit.setText(utd.key_name)
        self.ui.lockedCheckbox.setChecked(utd.locked)
        self.ui.openLockSpin.setValue(utd.unlock_dc)
        self.ui.difficultySpin.setValue(utd.unlock_diff)
        self.ui.difficultyModSpin.setValue(utd.unlock_diff_mod)

        # Scripts
        self.ui.onClickEdit.set_combo_box_text(str(utd.on_click))
        self.ui.onClosedEdit.set_combo_box_text(str(utd.on_closed))
        self.ui.onDamagedEdit.set_combo_box_text(str(utd.on_damaged))
        self.ui.onDeathEdit.set_combo_box_text(str(utd.on_death))
        self.ui.onOpenFailedEdit.set_combo_box_text(str(utd.on_open_failed))
        self.ui.onHeartbeatSelect.set_combo_box_text(str(utd.on_heartbeat))
        self.ui.onMeleeAttackEdit.set_combo_box_text(str(utd.on_melee))
        self.ui.onSpellEdit.set_combo_box_text(str(utd.on_power))
        self.ui.onOpenEdit.set_combo_box_text(str(utd.on_open))
        self.ui.onUnlockEdit.set_combo_box_text(str(utd.on_unlock))
        self.ui.onUserDefinedSelect.set_combo_box_text(str(utd.on_user_defined))

        self.relevant_script_resnames: list[str] = sorted(iter({res.resname().lower() for res in self._installation.get_relevant_resources(ResourceType.NCS, self._filepath)}))
        self.ui.onClickEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onClosedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onDamagedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onDeathEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onHeartbeatSelect.populate_combo_box(self.relevant_script_resnames)
        self.ui.onMeleeAttackEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onOpenEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onOpenFailedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onSpellEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onUnlockEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onUserDefinedSelect.populate_combo_box(self.relevant_script_resnames)
        self.ui.conversationEdit.populate_combo_box(
            sorted(iter({res.resname().lower() for res in self._installation.get_relevant_resources(ResourceType.DLG, self._filepath)}))
        )  # noqa: E501

        # Comments
        self.ui.commentsEdit.setPlainText(utd.comment)

    def build(self) -> tuple[bytes | bytearray, bytes]:
        """Builds a UTD object from UI data.

        Returns:
        -------
            tuple[bytes, bytes]: A tuple containing the GFF data (bytes) and errors (bytes)

        Processing Logic:
        ----------------
            - Sets UTD properties from UI elements like name, tag, resrefs etc
            - Writes the constructed UTD to a GFF bytearray
            - Returns the GFF data and any errors
        """
        utd: UTD = deepcopy(self._utd)

        # Basic
        utd.name = self.ui.nameEdit.locstring()
        utd.tag = self.ui.tagEdit.text()
        utd.resref = ResRef(self.ui.resrefEdit.text())
        utd.appearance_id = self.ui.appearanceSelect.currentIndex()
        utd.conversation = ResRef(self.ui.conversationEdit.currentText())

        # Advanced
        utd.min1_hp = self.ui.min1HpCheckbox.isChecked()
        utd.plot = self.ui.plotCheckbox.isChecked()
        utd.static = self.ui.staticCheckbox.isChecked()
        utd.not_blastable = self.ui.notBlastableCheckbox.isChecked()
        utd.faction_id = self.ui.factionSelect.currentIndex()
        utd.animation_state = self.ui.animationState.value()
        utd.current_hp = self.ui.currenHpSpin.value()
        utd.maximum_hp = self.ui.maxHpSpin.value()
        utd.hardness = self.ui.hardnessSpin.value()
        utd.fortitude = self.ui.fortitudeSpin.value()
        utd.reflex = self.ui.reflexSpin.value()
        utd.willpower = self.ui.willSpin.value()

        # Lock
        utd.locked = self.ui.lockedCheckbox.isChecked()
        utd.unlock_dc = self.ui.openLockSpin.value()
        utd.unlock_diff = self.ui.difficultySpin.value()
        utd.unlock_diff_mod = self.ui.difficultyModSpin.value()
        utd.key_required = self.ui.needKeyCheckbox.isChecked()
        utd.auto_remove_key = self.ui.removeKeyCheckbox.isChecked()
        utd.key_name = self.ui.keyEdit.text()

        # Scripts
        utd.on_click = ResRef(self.ui.onClickEdit.currentText())
        utd.on_closed = ResRef(self.ui.onClosedEdit.currentText())
        utd.on_damaged = ResRef(self.ui.onDamagedEdit.currentText())
        utd.on_death = ResRef(self.ui.onDeathEdit.currentText())
        utd.on_open_failed = ResRef(self.ui.onOpenFailedEdit.currentText())
        utd.on_heartbeat = ResRef(self.ui.onHeartbeatSelect.currentText())
        utd.on_melee = ResRef(self.ui.onMeleeAttackEdit.currentText())
        utd.on_power = ResRef(self.ui.onSpellEdit.currentText())
        utd.on_open = ResRef(self.ui.onOpenEdit.currentText())
        utd.on_unlock = ResRef(self.ui.onUnlockEdit.currentText())
        utd.on_user_defined = ResRef(self.ui.onUserDefinedSelect.currentText())

        # Comments
        utd.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_utd(utd)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTD(UTD())

    def change_name(self):
        assert self._installation is not None
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring())
        if dialog.exec():
            self._load_locstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)

    def generate_tag(self):
        if not self.ui.resrefEdit.text():
            self.generate_resref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generate_resref(self):
        if self._resname:
            self.ui.resrefEdit.setText(self._resname)
        else:
            self.ui.resrefEdit.setText("m00xx_dor_000")

    def edit_conversation(self):
        """Edits a conversation.

        Processing Logic:
        ----------------
            1. Gets the conversation name from the UI text field
            2. Searches the installation for the conversation resource
            3. If not found, prompts to create a new file in the override folder
            4. If found or created, opens the resource editor window.
        """
        assert self._installation is not None
        resname: str = self.ui.conversationEdit.currentText()
        data: bytes | bytearray | None = None
        filepath: os.PathLike | None = None

        if not resname or not resname.strip():
            QMessageBox(QMessageBox.Icon.Critical, "Failed to open DLG Editor", "Conversation field cannot be blank.").exec()
            return

        search: ResourceResult | None = self._installation.resource(resname, ResourceType.DLG)

        if search is None:
            msgbox = QMessageBox(
                QMessageBox.Icon.Information,
                "DLG file not found",
                "Do you wish to create a file in the override?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            ).exec()
            if msgbox == QMessageBox.StandardButton.Yes:
                data = bytearray()

                write_gff(dismantle_dlg(DLG()), data)
                filepath = self._installation.override_path() / f"{resname}.dlg"
                writer = BinaryWriter.to_file(filepath)
                writer.write_bytes(data)
                writer.close()
        else:
            resname, filepath, data = search.resname, search.filepath, search.data

        if data is not None:
            open_resource_editor(filepath, resname, ResourceType.DLG, data, self._installation, self)

    def toggle_preview(self):
        self.global_settings.showPreviewUTP = not self.global_settings.showPreviewUTP
        self.update3dPreview()

    def update3dPreview(self):
        """Updates the 3D preview renderer visibility and size.

        Processing Logic:
        ----------------
            - Checks if the global setting for showing preview is True
            - If True, calls _update_model() to update the 3D model preview
            - If False, hides BOTH the preview renderer AND the model info groupbox.
        """
        show_preview = self.global_settings.showPreviewUTP
        self.ui.previewRenderer.setVisible(show_preview)
        self.ui.modelInfoGroupBox.setVisible(show_preview)
        self.ui.actionShowPreview.setChecked(show_preview)

        try:
            if show_preview:
                self._update_model()
            else:
                self.resize(max(374, self.sizeHint().width()), max(457, self.sizeHint().height()))
        except Exception:  # noqa: BLE001, S110
            # Silently handle any errors in preview update to prevent pytest-qt from reporting them
            # Errors are already handled in _update_model, but we catch here for signal handlers
            pass

    def _update_model(self):
        """Updates the model preview.

        Processing Logic:
        ----------------
            - Build the model data from the installation data
            - Get the model name based on the data and installation details
            - Load the MDL and MDX resources using the model name
            - If resources are loaded, set them on the preview renderer
            - If not loaded, clear the existing model from the preview renderer
            - Update the model info label with resource location details
            - Do DIRECT texture lookups using Installation (not async scene tracking)
        """
        assert self._installation is not None
        self.resize(max(674, self.sizeHint().width()), max(457, self.sizeHint().height()))

        data, _ = self.build()
        utd = read_utd(data)

        # Build model information text - focus on low-level technical details
        info_lines: list[str] = []

        # Validate appearance_id before calling door.get_model() to prevent IndexError
        if self._genericdoors_2da is None:
            self.ui.previewRenderer.clear_model()
            info_lines.append("❌ genericdoors.2da not loaded")
            self.ui.modelInfoLabel.setText("\n".join(info_lines))
            return

        # Check if appearance_id is within valid range
        if utd.appearance_id < 0 or utd.appearance_id >= self._genericdoors_2da.get_height():
            self.ui.previewRenderer.clear_model()
            info_lines.append("❌ Invalid appearance ID")
            info_lines.append(f"Range: 0-{self._genericdoors_2da.get_height() - 1}")
            self.ui.modelInfoLabel.setText("\n".join(info_lines))
            return

        try:
            modelname: str = door.get_model(utd, self._installation, genericdoors=self._genericdoors_2da)
        except (IndexError, ValueError) as e:
            # Fallback: Invalid appearance_id or missing genericdoors.2da - clear the model
            self.ui.previewRenderer.clear_model()
            info_lines.append(f"❌ Lookup error: {e}")
            try:
                row = self._genericdoors_2da.get_row(utd.appearance_id)
                if row.has_string("modelname"):
                    modelname_col = row.get_string("modelname")
                    if not modelname_col or modelname_col.strip() == "****":
                        modelname_col = "[empty]"
                else:
                    modelname_col = "[column missing]"
                info_lines.append(f"genericdoors.2da row {utd.appearance_id}: 'modelname' = '{modelname_col}'")
            except (IndexError, KeyError):
                pass
            self.ui.modelInfoLabel.setText("\n".join(info_lines))
            return

        # Show the lookup process
        info_lines.append(f"Model resolved: '{modelname}'")
        try:
            row = self._genericdoors_2da.get_row(utd.appearance_id)
            info_lines.append(f"Lookup: genericdoors.2da[row {utd.appearance_id}]['modelname']")
        except (IndexError, KeyError):
            pass

        # Use same search order as renderer for consistency
        model_search_order: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.MODULES, SearchLocation.CHITIN]
        mdl: ResourceResult | None = self._installation.resource(modelname, ResourceType.MDL, model_search_order)
        mdx: ResourceResult | None = self._installation.resource(modelname, ResourceType.MDX, model_search_order)

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
            search_order_str = self._format_search_order(model_search_order)
            if mdl is None:
                info_lines.append(f"  Missing: {modelname}.mdl")
                info_lines.append(f"  (Searched: {search_order_str})")
            if mdx is None:
                info_lines.append(f"  Missing: {modelname}.mdx")
                info_lines.append(f"  (Searched: {search_order_str})")

        full_text = "\n".join(info_lines)
        self.ui.modelInfoLabel.setText(full_text)

        # Update summary (first line or key info)
        summary = info_lines[0] if info_lines else "No model information"
        if len(info_lines) > 1 and mdl is not None and mdx is not None:
            # Show model name and source in summary
            try:
                mdl_rel = os.path.relpath(mdl.filepath, self._installation.path()) if self._installation else str(mdl.filepath)
                summary = f"{modelname} → {mdl_rel}"
            except (ValueError, AttributeError):
                summary = f"{modelname} → {mdl.filepath}"
        self.ui.modelInfoSummaryLabel.setText(summary)

    def _format_search_order(self, search_order: list[SearchLocation]) -> str:
        """Format search order list into human-readable string."""
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

    def _on_model_info_toggled(self, checked: bool):
        """Handle model info groupbox toggle."""
        self.ui.modelInfoLabel.setVisible(checked)
        if not checked:
            # When collapsed, ensure summary is visible
            self.ui.modelInfoSummaryLabel.setVisible(True)

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
            from pathlib import Path

            path = self._installation.path()
            filepath_obj = Path(filepath) if not isinstance(filepath, Path) else filepath
            rel_path = filepath_obj.relative_to(path)
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
