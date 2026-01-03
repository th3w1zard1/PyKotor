from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QMenu, QMessageBox, QShortcut, QTreeView

from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.fac import FAC, FACFaction, FACReputation, dismantle_fac, read_fac
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QItemSelection, QPoint
    from qtpy.QtWidgets import QWidget


class FACEditor(Editor):
    """Faction Editor for editing FAC (Faction) files.

    The Faction Editor allows editing faction definitions and reputation relationships.
    Factions are displayed in a tree view, and reputations can be edited to define
    how factions perceive each other.
    """

    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        """Initialize the Faction Editor.

        Args:
        ----
            parent: The parent widget.
            installation: The installation object.
        """
        supported: list[ResourceType] = [ResourceType.FAC]
        super().__init__(parent, "Faction Editor", "faction", supported, supported, installation)

        self._fac: FAC = FAC()
        self._faction_model: QStandardItemModel = QStandardItemModel(self)
        self._reputation_model: QStandardItemModel = QStandardItemModel(self)

        # Try to load UI from designer file (may not exist, but code should work if it does)
        try:
            from toolset.uic.qtpy.editors.fac import Ui_MainWindow  # noqa: PLC0415

            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)
            self.ui.factionTree.setModel(self._faction_model)
            self.ui.factionTree.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
            self.ui.reputationTree.setModel(self._reputation_model)
            self.ui.reputationTree.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
            
            # Setup event filter to prevent scroll wheel interaction with controls
            from toolset.gui.common.filters import NoScrollEventFilter
            self._no_scroll_filter = NoScrollEventFilter(self)
            self._no_scroll_filter.setup_filter(parent_widget=self)
        except ImportError:
            # UI file doesn't exist yet - create minimal UI programmatically
            # This allows the editor to function even without a .ui file
            from qtpy.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget

            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)

            # Factions section
            faction_label = QLabel("Factions:")
            layout.addWidget(faction_label)
            self.ui_faction_tree = QTreeView()
            self.ui_faction_tree.setModel(self._faction_model)
            self.ui_faction_tree.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
            layout.addWidget(self.ui_faction_tree)

            # Reputations section
            reputation_label = QLabel("Reputations:")
            layout.addWidget(reputation_label)
            self.ui_reputation_tree = QTreeView()
            self.ui_reputation_tree.setModel(self._reputation_model)
            self.ui_reputation_tree.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
            layout.addWidget(self.ui_reputation_tree)

            # Simple controls (minimal UI)
            controls_layout = QHBoxLayout()
            self.ui_faction_name_edit = QLineEdit()
            self.ui_global_effect_check = QPushButton("Toggle Global Effect")
            self.ui_parent_id_spin = QSpinBox()
            self.ui_parent_id_spin.setMaximum(1000)
            controls_layout.addWidget(QLabel("Name:"))
            controls_layout.addWidget(self.ui_faction_name_edit)
            controls_layout.addWidget(self.ui_global_effect_check)
            controls_layout.addWidget(QLabel("Parent ID:"))
            controls_layout.addWidget(self.ui_parent_id_spin)
            layout.addLayout(controls_layout)

            # Setup event filter to prevent scroll wheel interaction with controls
            from toolset.gui.common.filters import NoScrollEventFilter
            self._no_scroll_filter = NoScrollEventFilter(self)
            self._no_scroll_filter.setup_filter(parent_widget=self)

            # Create a minimal ui object for compatibility
            class MinimalUI:
                def __init__(self):
                    self.factionTree = self.ui_faction_tree
                    self.reputationTree = self.ui_reputation_tree
                    self.factionNameEdit = self.ui_faction_name_edit
                    self.globalEffectCheck = self.ui_global_effect_check
                    self.parentIdSpin = self.ui_parent_id_spin

            self.ui = MinimalUI()

        self._setup_menus()
        self._add_help_action()
        self._setup_signals()
        self.new()

    def _setup_signals(self):
        """Connect GUI signals to methods."""
        self.ui.factionTree.selectionChanged = self.on_faction_selection_changed  # type: ignore[assignment]
        self.ui.factionTree.customContextMenuRequested.connect(self.on_faction_context_menu)
        self.ui.reputationTree.selectionChanged = self.on_reputation_selection_changed  # type: ignore[assignment]
        self.ui.reputationTree.customContextMenuRequested.connect(self.on_reputation_context_menu)

        if hasattr(self.ui, "factionNameEdit"):
            self.ui.factionNameEdit.editingFinished.connect(self.on_faction_value_updated)
        if hasattr(self.ui, "globalEffectCheck"):
            if hasattr(self.ui.globalEffectCheck, "clicked"):
                self.ui.globalEffectCheck.clicked.connect(self.on_faction_value_updated)
        if hasattr(self.ui, "parentIdSpin"):
            self.ui.parentIdSpin.valueChanged.connect(self.on_faction_value_updated)

        QShortcut("Del", self).activated.connect(self.on_delete_shortcut)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        """Load faction data from a file.

        Args:
        ----
            filepath: Path or name of the file to load from
            resref: Resource reference
            restype: Resource type
            data: Byte data of the file
        """
        super().load(filepath, resref, restype, data)

        self._fac = read_fac(data)

        # Populate faction tree
        self._faction_model.clear()
        for i, faction in enumerate(self._fac.factions):
            faction_item = QStandardItem()
            faction_item.setData(faction)
            self.refresh_faction_item(faction_item)
            self._faction_model.appendRow(faction_item)

        # Populate reputation tree
        self._reputation_model.clear()
        for rep in self._fac.reputations:
            rep_item = QStandardItem()
            rep_item.setData(rep)
            self.refresh_reputation_item(rep_item)
            self._reputation_model.appendRow(rep_item)

    def build(self) -> tuple[bytes, bytes]:
        """Build the FAC data for saving."""
        data = bytearray()
        write_gff(dismantle_fac(self._fac), data)
        return data, b""

    def new(self):
        """Create a new empty FAC file."""
        super().new()
        self._fac = FAC()
        self._faction_model.clear()
        self._reputation_model.clear()

    def refresh_faction_item(self, faction_item: QStandardItem):
        """Update the faction item's display text."""
        faction: FACFaction = faction_item.data()
        text = f"[{self._faction_model.indexFromItem(faction_item).row()}] {faction.name}"
        if faction.global_effect:
            text += " (Global)"
        faction_item.setText(text)

    def refresh_reputation_item(self, rep_item: QStandardItem):
        """Update the reputation item's display text."""
        rep: FACReputation = rep_item.data()
        faction1_name = self._fac.factions[rep.faction_id1].name if rep.faction_id1 < len(self._fac.factions) else f"Faction{rep.faction_id1}"
        faction2_name = self._fac.factions[rep.faction_id2].name if rep.faction_id2 < len(self._fac.factions) else f"Faction{rep.faction_id2}"

        # Determine relationship text
        if rep.reputation <= 10:
            rel_text = "Hostile"
        elif rep.reputation <= 89:
            rel_text = "Neutral"
        else:
            rel_text = "Friendly"

        text = f"{faction2_name} -> {faction1_name}: {rep.reputation} ({rel_text})"
        rep_item.setText(text)

    def on_faction_selection_changed(self, selection: QItemSelection, deselected: QItemSelection):
        """Handle faction tree selection change."""
        QTreeView.selectionChanged(self.ui.factionTree, selection, deselected)  # type: ignore[call-overload]

        if hasattr(self.ui, "factionNameEdit") and selection.indexes():
            index = selection.indexes()[0]
            item = self._faction_model.itemFromIndex(index)
            if item is not None:
                faction: FACFaction = item.data()
                self.ui.factionNameEdit.blockSignals(True)
                self.ui.factionNameEdit.setText(faction.name)
                self.ui.factionNameEdit.blockSignals(False)
                if hasattr(self.ui, "globalEffectCheck"):
                    if hasattr(self.ui.globalEffectCheck, "setChecked"):
                        self.ui.globalEffectCheck.setChecked(faction.global_effect)
                if hasattr(self.ui, "parentIdSpin"):
                    self.ui.parentIdSpin.blockSignals(True)
                    self.ui.parentIdSpin.setValue(faction.parent_id if faction.parent_id != 0xFFFFFFFF else 0)
                    self.ui.parentIdSpin.blockSignals(False)

    def on_reputation_selection_changed(self, selection: QItemSelection, deselected: QItemSelection):
        """Handle reputation tree selection change."""
        QTreeView.selectionChanged(self.ui.reputationTree, selection, deselected)  # type: ignore[call-overload]

        # Update reputation editing controls if they exist
        if selection.indexes() and hasattr(self.ui, "reputationValueSpin"):
            index = selection.indexes()[0]
            item = self._reputation_model.itemFromIndex(index)
            if item is not None:
                rep: FACReputation = item.data()
                self.ui.reputationValueSpin.blockSignals(True)
                self.ui.reputationValueSpin.setValue(rep.reputation)
                self.ui.reputationValueSpin.blockSignals(False)

    def on_faction_value_updated(self):
        """Update the selected faction when values change."""
        if not self.ui.factionTree.selectedIndexes():
            return

        index = self.ui.factionTree.selectedIndexes()[0]
        item = self._faction_model.itemFromIndex(index)
        if item is None:
            return

        faction: FACFaction = item.data()
        if hasattr(self.ui, "factionNameEdit"):
            faction.name = self.ui.factionNameEdit.text()
        if hasattr(self.ui, "globalEffectCheck"):
            if hasattr(self.ui.globalEffectCheck, "isChecked"):
                faction.global_effect = self.ui.globalEffectCheck.isChecked()
        if hasattr(self.ui, "parentIdSpin"):
            parent_id = self.ui.parentIdSpin.value()
            faction.parent_id = 0xFFFFFFFF if parent_id == 0 else parent_id

        self.refresh_faction_item(item)

    def on_reputation_value_updated(self):
        """Update the selected reputation when values change."""
        if not self.ui.reputationTree.selectedIndexes():
            return

        index = self.ui.reputationTree.selectedIndexes()[0]
        item = self._reputation_model.itemFromIndex(index)
        if item is None:
            return

        rep: FACReputation = item.data()
        if hasattr(self.ui, "reputationValueSpin"):
            rep.reputation = self.ui.reputationValueSpin.value()

        self.refresh_reputation_item(item)

    def on_faction_context_menu(self, point: QPoint):
        """Handle context menu for faction tree."""
        index = self.ui.factionTree.indexAt(point)
        item = self._faction_model.itemFromIndex(index)

        menu = QMenu(self)

        if item:
            menu.addAction("Remove Faction").triggered.connect(lambda: self.remove_faction(item))
        menu.addAction("Add Faction").triggered.connect(lambda: self.add_faction(FACFaction()))

        viewport = self.ui.factionTree.viewport()
        if viewport is not None:
            menu.popup(viewport.mapToGlobal(point))

    def on_reputation_context_menu(self, point: QPoint):
        """Handle context menu for reputation tree."""
        index = self.ui.reputationTree.indexAt(point)
        item = self._reputation_model.itemFromIndex(index)

        menu = QMenu(self)

        if item:
            menu.addAction("Remove Reputation").triggered.connect(lambda: self.remove_reputation(item))
        menu.addAction("Add Reputation").triggered.connect(lambda: self.add_reputation(FACReputation()))

        viewport = self.ui.reputationTree.viewport()
        if viewport is not None:
            menu.popup(viewport.mapToGlobal(point))

    def on_delete_shortcut(self):
        """Handle delete key shortcut."""
        if self.ui.factionTree.hasFocus() and self.ui.factionTree.selectedIndexes():
            item = self._faction_model.itemFromIndex(self.ui.factionTree.selectedIndexes()[0])
            if item is not None:
                self.remove_faction(item)
        elif self.ui.reputationTree.hasFocus() and self.ui.reputationTree.selectedIndexes():
            item = self._reputation_model.itemFromIndex(self.ui.reputationTree.selectedIndexes()[0])
            if item is not None:
                self.remove_reputation(item)

    def add_faction(self, faction: FACFaction):
        """Add a faction to the FAC."""
        self._fac.factions.append(faction)
        faction_item = QStandardItem()
        faction_item.setData(faction)
        self.refresh_faction_item(faction_item)
        self._faction_model.appendRow(faction_item)

    def remove_faction(self, faction_item: QStandardItem):
        """Remove a faction from the FAC."""
        faction: FACFaction = faction_item.data()
        self._faction_model.removeRow(faction_item.row())
        self._fac.factions.remove(faction)

        # Remove all reputations involving this faction
        to_remove = [
            rep_item
            for rep_item in [self._reputation_model.item(i) for i in range(self._reputation_model.rowCount())]
            if rep_item is not None and (rep_item.data().faction_id1 == self._fac.factions.index(faction) or rep_item.data().faction_id2 == self._fac.factions.index(faction))
        ]
        for rep_item in to_remove:
            if rep_item is not None:
                self.remove_reputation(rep_item)

    def add_reputation(self, reputation: FACReputation):
        """Add a reputation to the FAC."""
        self._fac.reputations.append(reputation)
        rep_item = QStandardItem()
        rep_item.setData(reputation)
        self.refresh_reputation_item(rep_item)
        self._reputation_model.appendRow(rep_item)

    def remove_reputation(self, rep_item: QStandardItem):
        """Remove a reputation from the FAC."""
        reputation: FACReputation = rep_item.data()
        self._reputation_model.removeRow(rep_item.row())
        self._fac.reputations.remove(reputation)

