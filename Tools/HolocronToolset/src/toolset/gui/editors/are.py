from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtGui import QColor, QImage, QPixmap, QShortcut
from qtpy.QtWidgets import QColorDialog

from pykotor.common.misc import Color, ResRef
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.gff import read_gff, write_gff
from pykotor.resource.formats.lyt import read_lyt
from pykotor.resource.generics.are import ARE, ARENorthAxis, AREWindPower, dismantle_are, read_are
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.widgets.module_designer import ModuleDesignerSettings
from utility.common.geometry import SurfaceMaterial, Vector2

from loggerplus import RobustLogger

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QLabel, QWidget

    from pykotor.extract.file import ResourceResult
    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.formats.twoda import TwoDA
    from pykotor.resource.generics.are import ARERoom
    from toolset.gui.widgets.long_spinbox import LongSpinBox


class AREEditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        supported: list[ResourceType] = [ResourceType.ARE]
        super().__init__(parent, "ARE Editor", "none", supported, supported, installation)
        self.setMinimumSize(400, 600)  # Lock the window size

        self._are: ARE = ARE()
        self._loaded_are: ARE | None = None  # Store reference to loaded ARE to preserve original values
        self._minimap: TPC | None = None
        self._rooms: list[ARERoom] = []  # TODO(th3w1zard1): define somewhere in ui.

        from toolset.uic.qtpy.editors.are import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Setup event filter to prevent scroll wheel interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        
        self._setup_menus()
        self._add_help_action()  # Auto-detects "GFF-ARE.md" for ARE
        self._setup_signals()
        if installation is not None:  # will only be none in the unittests
            self._setup_installation(installation)

        self.ui.dirtColor1Edit.allow_alpha = True
        self.ui.dirtColor2Edit.allow_alpha = True
        self.ui.dirtColor3Edit.allow_alpha = True

        self.ui.minimapRenderer.default_material_color = QColor(0, 0, 255, 127)
        self.ui.minimapRenderer.material_colors[SurfaceMaterial.NON_WALK] = QColor(255, 0, 0, 80)
        self.ui.minimapRenderer.material_colors[SurfaceMaterial.NON_WALK_GRASS] = QColor(255, 0, 0, 80)
        self.ui.minimapRenderer.material_colors[SurfaceMaterial.UNDEFINED] = QColor(255, 0, 0, 80)
        self.ui.minimapRenderer.material_colors[SurfaceMaterial.OBSCURING] = QColor(255, 0, 0, 80)
        self.ui.minimapRenderer.hide_walkmesh_edges = True
        self.ui.minimapRenderer.highlight_boundaries = False
        self.ui.minimapRenderer.highlight_on_hover = False

        # Set higher precision for map coordinate spinboxes (normalized 0-1 values need more decimals)
        self.ui.mapImageX1Spin.setDecimals(6)
        self.ui.mapImageY1Spin.setDecimals(6)
        self.ui.mapImageX2Spin.setDecimals(6)
        self.ui.mapImageY2Spin.setDecimals(6)

        self.new()

    def _setup_signals(self):
        self.ui.tagGenerateButton.clicked.connect(self.generate_tag)

        self.ui.mapAxisSelect.currentIndexChanged.connect(self.redoMinimap)
        self.ui.mapWorldX1Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapWorldX2Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapWorldY1Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapWorldY2Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapImageX1Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapImageX2Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapImageY1Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapImageY2Spin.valueChanged.connect(self.redoMinimap)

        # Minimap renderer input: match other WalkmeshRenderer users (PTH/BWM).
        self.ui.minimapRenderer.sig_mouse_moved.connect(self.on_minimap_mouse_moved)
        self.ui.minimapRenderer.sig_mouse_scrolled.connect(self.on_minimap_mouse_scrolled)

        # Common zoom shortcuts: use "=" (base key) for zoom in, "-" for zoom out.
        # "+" requires Shift, but "=" works without modifiers (standard keyboard behavior).
        QShortcut("=", self).activated.connect(lambda: self.ui.minimapRenderer.camera.nudge_zoom(1.25))
        QShortcut("-", self).activated.connect(lambda: self.ui.minimapRenderer.camera.nudge_zoom(0.8))
        QShortcut("Ctrl+0", self).activated.connect(self.fit_minimap_view)

        assert self._installation is not None, "Installation is not set"
        self.relevant_script_resnames: list[str] = sorted(
            iter(
                {
                    res.resname().lower()
                    for res in self._installation.get_relevant_resources(
                        ResourceType.NCS, self._filepath
                    )
                }
            )
        )

        self.ui.onEnterSelect.populate_combo_box(self.relevant_script_resnames)
        self.ui.onExitSelect.populate_combo_box(self.relevant_script_resnames)
        self.ui.onHeartbeatSelect.populate_combo_box(self.relevant_script_resnames)
        self.ui.onUserDefinedSelect.populate_combo_box(self.relevant_script_resnames)

    def _setup_installation(self, installation: HTInstallation):
        self._installation = installation

        self.ui.nameEdit.set_installation(installation)

        cameras: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_CAMERAS)

        self.ui.cameraStyleSelect.clear()
        self.ui.cameraStyleSelect.set_context(cameras, self._installation, HTInstallation.TwoDA_CAMERAS)
        assert cameras is not None, "Cameras are not set"
        for label in cameras.get_column("name"):
            self.ui.cameraStyleSelect.addItem(label.title())

        self.ui.dirtGroup.setVisible(installation.tsl)
        self.ui.grassEmissiveEdit.setVisible(installation.tsl)
        self.ui.grassEmissiveLabel.setVisible(installation.tsl)
        self.ui.snowCheck.setVisible(installation.tsl)
        self.ui.snowCheck.setEnabled(installation.tsl)
        self.ui.rainCheck.setVisible(installation.tsl)
        self.ui.rainCheck.setEnabled(installation.tsl)
        self.ui.lightningCheck.setVisible(installation.tsl)
        self.ui.lightningCheck.setEnabled(installation.tsl)

        installation.setup_file_context_menu(self.ui.onEnterSelect, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onExitSelect, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onHeartbeatSelect, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onUserDefinedSelect, [ResourceType.NSS, ResourceType.NCS])

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes | bytearray,
    ):
        super().load(filepath, resref, restype, data)

        if not data:
            raise ValueError("The ARE file data is empty or invalid.")

        are: ARE = read_are(data)
        self._loaded_are = are  # Store reference to preserve original values
        self._loadARE(are)
        self.adjustSize()

    def _loadARE(self, are: ARE):
        if not self._installation:
            print("Load an installation first.")
            return
        self._rooms = are.rooms
        # Only attempt related-resource lookups when we have a real area resref.
        # Editor uses `untitled_<hex>` placeholders for new/unsaved tabs.
        # Engine reference: `vendor/swkotor.c:L468225-L468237` (`area_name` -> "lbl_map%s").
        if self._resname and not self._resname.startswith("untitled_"):
            # Layout (.lyt) lookup for room walkmeshes.
            # Mirrors engine: areas resolve by `area_name` and then load auxiliary assets.
            # Engine reference: `vendor/swkotor.c:L476816-L476845` and `vendor/swkotor.c:L194243-L194331`.
            order_lyt: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
            res_result_lyt: ResourceResult | None = self._installation.resource(self._resname, ResourceType.LYT, order_lyt)
            if res_result_lyt:
                lyt: LYT = read_lyt(res_result_lyt.data)
                queries: list[ResourceIdentifier] = [ResourceIdentifier(room.model, ResourceType.WOK) for room in lyt.rooms]

                wok_results: dict[ResourceIdentifier, ResourceResult | None] = self._installation.resources(queries, order_lyt)
                walkmeshes: list[BWM] = [read_bwm(result.data) for result in wok_results.values() if result]
                self.ui.minimapRenderer.set_walkmeshes(walkmeshes)

            # Minimap texture lookup: "lbl_map<area>" (TGA/TPC via `Installation.texture`).
            # Engine reference: `vendor/swkotor.c:L468230-L468238` and `vendor/swkotor.c:L476829-L476842`.
            order_tex: list[SearchLocation] = [
                SearchLocation.OVERRIDE,
                SearchLocation.TEXTURES_TPA,
                SearchLocation.TEXTURES_GUI,
                SearchLocation.CHITIN,
                SearchLocation.MODULES,
            ]
            minimap_resname = f"lbl_map{self._resname}"
            self._minimap = self._installation.texture(minimap_resname, order_tex)
            if self._minimap is None:
                RobustLogger().warning(f"Could not find texture '{minimap_resname}' required for minimap")
            else:
                self.ui.minimapRenderer.set_minimap(are, self._minimap)

            # Fit view after bounds/minimap are set; show with margin so content is not edge-to-edge.
            self.fit_minimap_view()

        max_value: int = 100

        # Basic
        self.ui.nameEdit.set_locstring(are.name)
        self.ui.tagEdit.setText(are.tag)
        self.ui.cameraStyleSelect.setCurrentIndex(are.camera_style)
        self.ui.envmapEdit.setText(str(are.default_envmap))
        self.ui.disableTransitCheck.setChecked(are.disable_transit)
        self.ui.unescapableCheck.setChecked(are.unescapable)
        self.ui.alphaTestSpin.setValue(are.alpha_test)
        self.ui.stealthCheck.setChecked(are.stealth_xp)
        self.ui.stealthMaxSpin.setValue(are.stealth_xp_max)
        self.ui.stealthLossSpin.setValue(are.stealth_xp_loss)

        # Map
        self.ui.mapAxisSelect.setCurrentIndex(are.north_axis)
        self.ui.mapZoomSpin.setValue(are.map_zoom)
        self.ui.mapResXSpin.setValue(are.map_res_x)
        self.ui.mapImageX1Spin.setValue(are.map_point_1.x)
        self.ui.mapImageX2Spin.setValue(are.map_point_2.x)
        self.ui.mapImageY1Spin.setValue(are.map_point_1.y)
        self.ui.mapImageY2Spin.setValue(are.map_point_2.y)
        self.ui.mapWorldX1Spin.setValue(are.world_point_1.x)
        self.ui.mapWorldX2Spin.setValue(are.world_point_2.x)
        self.ui.mapWorldY1Spin.setValue(are.world_point_1.y)
        self.ui.mapWorldY2Spin.setValue(are.world_point_2.y)

        # Weather
        self.ui.fogEnabledCheck.setChecked(are.fog_enabled)
        self.ui.fogColorEdit.set_color(are.fog_color)
        self.ui.fogNearSpin.setValue(are.fog_near)
        self.ui.fogFarSpin.setValue(are.fog_far)
        self.ui.ambientColorEdit.set_color(are.sun_ambient)
        self.ui.diffuseColorEdit.set_color(are.sun_diffuse)
        self.ui.dynamicColorEdit.set_color(are.dynamic_light)
        self.ui.windPowerSelect.setCurrentIndex(are.wind_power)
        self.ui.rainCheck.setChecked(are.chance_rain == max_value)
        self.ui.snowCheck.setChecked(are.chance_snow == max_value)
        self.ui.lightningCheck.setChecked(are.chance_lightning == max_value)
        self.ui.shadowsCheck.setChecked(are.shadows)
        self.ui.shadowsSpin.setValue(are.shadow_opacity)

        # Terrain
        self.ui.grassTextureEdit.setText(str(are.grass_texture))
        self.ui.grassDiffuseEdit.set_color(are.grass_diffuse)
        self.ui.grassAmbientEdit.set_color(are.grass_ambient)
        self.ui.grassEmissiveEdit.set_color(are.grass_emissive)
        self.ui.grassDensitySpin.setValue(are.grass_density)
        self.ui.grassSizeSpin.setValue(are.grass_size)
        self.ui.grassProbLLSpin.setValue(are.grass_prob_ll)
        self.ui.grassProbLRSpin.setValue(are.grass_prob_lr)
        self.ui.grassProbULSpin.setValue(are.grass_prob_ul)
        self.ui.grassProbURSpin.setValue(are.grass_prob_ur)
        self.ui.dirtColor1Edit.set_color(are.dirty_argb_1)
        self.ui.dirtColor2Edit.set_color(are.dirty_argb_2)
        self.ui.dirtColor3Edit.set_color(are.dirty_argb_3)
        self.ui.dirtFormula1Spin.setValue(are.dirty_formula_1)
        self.ui.dirtFormula2Spin.setValue(are.dirty_formula_2)
        self.ui.dirtFormula3Spin.setValue(are.dirty_formula_3)
        self.ui.dirtFunction1Spin.setValue(are.dirty_func_1)
        self.ui.dirtFunction2Spin.setValue(are.dirty_func_2)
        self.ui.dirtFunction3Spin.setValue(are.dirty_func_3)
        self.ui.dirtSize1Spin.setValue(are.dirty_size_1)
        self.ui.dirtSize2Spin.setValue(are.dirty_size_2)
        self.ui.dirtSize3Spin.setValue(are.dirty_size_3)

        # Scripts
        self.ui.onEnterSelect.set_combo_box_text(str(are.on_enter))
        self.ui.onExitSelect.set_combo_box_text(str(are.on_exit))
        self.ui.onHeartbeatSelect.set_combo_box_text(str(are.on_heartbeat))
        self.ui.onUserDefinedSelect.set_combo_box_text(str(are.on_user_defined))

        # Comments
        self.ui.commentsEdit.setPlainText(are.comment)

    def build(self) -> tuple[bytes, bytes]:
        self._are = self._buildARE()
        
        # Copy original values from loaded ARE to new ARE for roundtrip preservation
        if getattr(self, '_loaded_are', None) is not None:
            if getattr(self._loaded_are, '_has_original', False):
                self._are._has_original = True
                self._are._original_values = getattr(self._loaded_are, '_original_values', {}).copy()

        if self._installation:
            game = self._installation.game()
        else:
            from pykotor.common.misc import Game
            game = Game.K1
        new_gff = dismantle_are(self._are, game)
        
        # Preserve extra fields from original GFF if available (for roundtrip tests)
        if self._revert:
            try:
                from pykotor.resource.formats.gff.gff_data import GFFStruct
                old_gff = read_gff(self._revert)
                GFFStruct._add_missing(new_gff.root, old_gff.root)
            except Exception:  # noqa: BLE001
                # If preserving fails, continue without preservation
                pass
        
        data = bytearray()
        write_gff(new_gff, data)
        return bytes(data), b""

    def _buildARE(self) -> ARE:
        are = ARE()

        # Basic
        are.name = self.ui.nameEdit.locstring()
        are.tag = self.ui.tagEdit.text()
        are.camera_style = self.ui.cameraStyleSelect.currentIndex()
        are.default_envmap = ResRef(self.ui.envmapEdit.text())
        are.unescapable = self.ui.unescapableCheck.isChecked()
        are.disable_transit = self.ui.disableTransitCheck.isChecked()
        are.alpha_test = float(self.ui.alphaTestSpin.value())
        are.stealth_xp = self.ui.stealthCheck.isChecked()
        are.stealth_xp_max = self.ui.stealthMaxSpin.value()
        are.stealth_xp_loss = self.ui.stealthLossSpin.value()

        # Map
        are.north_axis = ARENorthAxis(self.ui.mapAxisSelect.currentIndex())
        are.map_zoom = self.ui.mapZoomSpin.value()
        are.map_res_x = self.ui.mapResXSpin.value()
        are.map_point_1 = Vector2(self.ui.mapImageX1Spin.value(), self.ui.mapImageY1Spin.value())
        are.map_point_2 = Vector2(self.ui.mapImageX2Spin.value(), self.ui.mapImageY2Spin.value())
        are.world_point_1 = Vector2(self.ui.mapWorldX1Spin.value(), self.ui.mapWorldY1Spin.value())
        are.world_point_2 = Vector2(self.ui.mapWorldX2Spin.value(), self.ui.mapWorldY2Spin.value())

        # Weather
        are.fog_enabled = self.ui.fogEnabledCheck.isChecked()
        are.fog_color = self.ui.fogColorEdit.color()
        are.fog_near = self.ui.fogNearSpin.value()
        are.fog_far = self.ui.fogFarSpin.value()
        are.sun_ambient = self.ui.ambientColorEdit.color()
        are.sun_diffuse = self.ui.diffuseColorEdit.color()
        are.dynamic_light = self.ui.dynamicColorEdit.color()
        are.wind_power = AREWindPower(self.ui.windPowerSelect.currentIndex())
        # Read checkbox state - if checkbox is checked, use 100; otherwise use 0
        # For K1 installations, weather checkboxes are TSL-only and should always be 0
        if self._installation and self._installation.tsl:
            are.chance_rain = 100 if self.ui.rainCheck.isChecked() else 0
            are.chance_snow = 100 if self.ui.snowCheck.isChecked() else 0
            are.chance_lightning = 100 if self.ui.lightningCheck.isChecked() else 0
        else:
            # K1 installations don't support weather checkboxes
            are.chance_rain = 0
            are.chance_snow = 0
            are.chance_lightning = 0
        are.shadows = self.ui.shadowsCheck.isChecked()
        are.shadow_opacity = self.ui.shadowsSpin.value()

        # Terrain
        are.grass_texture = ResRef(self.ui.grassTextureEdit.text())
        are.grass_diffuse = self.ui.grassDiffuseEdit.color()
        are.grass_ambient = self.ui.grassAmbientEdit.color()
        are.grass_emissive = self.ui.grassEmissiveEdit.color()
        are.grass_size = self.ui.grassSizeSpin.value()
        are.grass_density = self.ui.grassDensitySpin.value()
        are.grass_prob_ll = self.ui.grassProbLLSpin.value()
        are.grass_prob_lr = self.ui.grassProbLRSpin.value()
        are.grass_prob_ul = self.ui.grassProbULSpin.value()
        are.grass_prob_ur = self.ui.grassProbURSpin.value()
        are.dirty_argb_1 = self.ui.dirtColor1Edit.color()
        are.dirty_argb_2 = self.ui.dirtColor2Edit.color()
        are.dirty_argb_3 = self.ui.dirtColor3Edit.color()
        are.dirty_formula_1 = self.ui.dirtFormula1Spin.value()
        are.dirty_formula_2 = self.ui.dirtFormula2Spin.value()
        are.dirty_formula_3 = self.ui.dirtFormula3Spin.value()
        are.dirty_func_1 = self.ui.dirtFunction1Spin.value()
        are.dirty_func_2 = self.ui.dirtFunction2Spin.value()
        are.dirty_func_3 = self.ui.dirtFunction3Spin.value()
        are.dirty_size_1 = self.ui.dirtSize1Spin.value()
        are.dirty_size_2 = self.ui.dirtSize2Spin.value()
        are.dirty_size_3 = self.ui.dirtSize3Spin.value()

        # Scripts
        are.on_enter = ResRef(self.ui.onEnterSelect.currentText())
        are.on_exit = ResRef(self.ui.onExitSelect.currentText())
        are.on_heartbeat = ResRef(self.ui.onHeartbeatSelect.currentText())
        are.on_user_defined = ResRef(self.ui.onUserDefinedSelect.currentText())

        # Comments
        are.comment = self.ui.commentsEdit.toPlainText()

        # Remaining.
        are.rooms = self._rooms

        return are

    def new(self):
        super().new()
        self._loaded_are = None  # Clear loaded ARE reference for new files
        self._loadARE(ARE())

    def redoMinimap(self):
        if self._minimap:
            are: ARE = self._buildARE()
            self.ui.minimapRenderer.set_minimap(are, self._minimap)

    def fit_minimap_view(self):
        # Default view: fit bounds with margin so walkmesh/minimap occupies ~half the view area.
        # This is intentionally less tight than a full fit for usability.
        self.ui.minimapRenderer.center_camera(fill=0.70710678)  # sqrt(0.5)

    def on_minimap_mouse_moved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]):
        # Pan/rotate controls mirror `BWMEditor` (Ctrl+drag) and respect module designer sensitivities.
        world_delta: Vector2 = self.ui.minimapRenderer.to_world_delta(delta.x, delta.y)
        if Qt.MouseButton.LeftButton in buttons and Qt.Key.Key_Control in keys:  # type: ignore[attr-defined]
            self.ui.minimapRenderer.do_cursor_lock(screen)
            move_sens = ModuleDesignerSettings().moveCameraSensitivity2d / 100
            self.ui.minimapRenderer.camera.nudge_position(-world_delta.x * move_sens, -world_delta.y * move_sens)
        elif Qt.MouseButton.MiddleButton in buttons and Qt.Key.Key_Control in keys:  # type: ignore[attr-defined]
            self.ui.minimapRenderer.do_cursor_lock(screen)
            rotate_sens = ModuleDesignerSettings().rotateCameraSensitivity2d / 1000
            self.ui.minimapRenderer.camera.nudge_rotation((delta.x / 50) * rotate_sens)

    def on_minimap_mouse_scrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if not delta.y:
            return
        if Qt.Key.Key_Control not in keys:  # type: ignore[attr-defined]
            return
        sens_setting = ModuleDesignerSettings().zoomCameraSensitivity2d
        zoom_factor = calculate_zoom_strength(delta.y, sens_setting)
        self.ui.minimapRenderer.camera.nudge_zoom(zoom_factor)

    def change_color(self, color_spin: LongSpinBox):
        qcolor: QColor = QColorDialog.getColor(QColor(color_spin.value()))
        color = Color.from_bgr_integer(qcolor.rgb())
        color_spin.setValue(color.bgr_integer())

    def redo_color_image(self, value: int, color_label: QLabel):
        color = Color.from_bgr_integer(value)
        r, g, b = int(color.r * 255), int(color.g * 255), int(color.b * 255)
        data = bytes([r, g, b] * 16 * 16)
        pixmap = QPixmap.fromImage(QImage(data, 16, 16, QImage.Format.Format_RGB888))
        color_label.setPixmap(pixmap)

    def change_name(self):
        assert self._installation is not None, "Installation is not set"
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring())
        if dialog.exec():
            self._load_locstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)

    def generate_tag(self):
        self.ui.tagEdit.setText("newarea" if self._resname is None or self._resname == "" else self._resname)


def calculate_zoom_strength(delta_y: float, sens_setting: int) -> float:
    # Mirrors `BWMEditor.calculate_zoom_strength` / `PTHEditor.calculate_zoom_strength`.
    m = 0.00202
    b = 1
    factor_in = (m * sens_setting + b)
    return 1 / abs(factor_in) if delta_y < 0 else abs(factor_in)
