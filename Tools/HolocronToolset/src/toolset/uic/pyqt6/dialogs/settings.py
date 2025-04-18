# Form implementation generated from reading ui file '..\ui\dialogs\settings.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(757, 451)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtWidgets.QSplitter(parent=Dialog)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.splitter.setObjectName("splitter")
        self.settingsTree = QtWidgets.QTreeWidget(parent=self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.settingsTree.sizePolicy().hasHeightForWidth())
        self.settingsTree.setSizePolicy(sizePolicy)
        self.settingsTree.setHeaderHidden(True)
        self.settingsTree.setObjectName("settingsTree")
        item_0 = QtWidgets.QTreeWidgetItem(self.settingsTree)
        item_0 = QtWidgets.QTreeWidgetItem(self.settingsTree)
        item_0 = QtWidgets.QTreeWidgetItem(self.settingsTree)
        item_0 = QtWidgets.QTreeWidgetItem(self.settingsTree)
        item_0 = QtWidgets.QTreeWidgetItem(self.settingsTree)
        self.settingsStack = QtWidgets.QStackedWidget(parent=self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.settingsStack.sizePolicy().hasHeightForWidth())
        self.settingsStack.setSizePolicy(sizePolicy)
        self.settingsStack.setObjectName("settingsStack")
        self.installationsPage = QtWidgets.QWidget()
        self.installationsPage.setObjectName("installationsPage")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.installationsPage)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.installationsWidget = InstallationsWidget(parent=self.installationsPage)
        self.installationsWidget.setObjectName("installationsWidget")
        self.gridLayout_2.addWidget(self.installationsWidget, 0, 0, 1, 1)
        self.settingsStack.addWidget(self.installationsPage)
        self.applicationSettingsPage = QtWidgets.QWidget()
        self.applicationSettingsPage.setObjectName("applicationSettingsPage")
        self.gridLayout_26 = QtWidgets.QGridLayout(self.applicationSettingsPage)
        self.gridLayout_26.setObjectName("gridLayout_26")
        self.applicationSettingsWidget = ApplicationSettingsWidget(parent=self.applicationSettingsPage)
        self.applicationSettingsWidget.setObjectName("applicationSettingsWidget")
        self.gridLayout_26.addWidget(self.applicationSettingsWidget, 0, 0, 1, 1)
        self.settingsStack.addWidget(self.applicationSettingsPage)
        self.moduleDesignerPage = QtWidgets.QWidget()
        self.moduleDesignerPage.setObjectName("moduleDesignerPage")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.moduleDesignerPage)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.moduleDesignerWidget = ModuleDesignerWidget(parent=self.moduleDesignerPage)
        self.moduleDesignerWidget.setObjectName("moduleDesignerWidget")
        self.gridLayout_3.addWidget(self.moduleDesignerWidget, 0, 0, 1, 1)
        self.settingsStack.addWidget(self.moduleDesignerPage)
        self.miscPage = QtWidgets.QWidget()
        self.miscPage.setObjectName("miscPage")
        self.gridLayout = QtWidgets.QGridLayout(self.miscPage)
        self.gridLayout.setObjectName("gridLayout")
        self.miscWidget = MiscWidget(parent=self.miscPage)
        self.miscWidget.setObjectName("miscWidget")
        self.gridLayout.addWidget(self.miscWidget, 0, 1, 1, 1)
        self.settingsStack.addWidget(self.miscPage)
        self.gitEditorPage = QtWidgets.QWidget()
        self.gitEditorPage.setObjectName("gitEditorPage")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.gitEditorPage)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.gitEditorWidget = GITWidget(parent=self.gitEditorPage)
        self.gitEditorWidget.setObjectName("gitEditorWidget")
        self.gridLayout_4.addWidget(self.gitEditorWidget, 0, 0, 1, 1)
        self.settingsStack.addWidget(self.gitEditorPage)
        self.verticalLayout.addWidget(self.splitter)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.settingsStack.setCurrentIndex(1)
        self.buttonBox.accepted.connect(Dialog.accept) # type: ignore
        self.buttonBox.rejected.connect(Dialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Settings"))
        self.settingsTree.headerItem().setText(0, _translate("Dialog", "1"))
        __sortingEnabled = self.settingsTree.isSortingEnabled()
        self.settingsTree.setSortingEnabled(False)
        self.settingsTree.topLevelItem(0).setText(0, _translate("Dialog", "Installations"))
        self.settingsTree.topLevelItem(1).setText(0, _translate("Dialog", "GIT Editor"))
        self.settingsTree.topLevelItem(2).setText(0, _translate("Dialog", "Module Designer"))
        self.settingsTree.topLevelItem(3).setText(0, _translate("Dialog", "Misc"))
        self.settingsTree.topLevelItem(4).setText(0, _translate("Dialog", "Application"))
        self.settingsTree.setSortingEnabled(__sortingEnabled)
from toolset.gui.widgets.settings.application import ApplicationSettingsWidget
from toolset.gui.widgets.settings.git import GITWidget
from toolset.gui.widgets.settings.installations import InstallationsWidget
from toolset.gui.widgets.settings.misc import MiscWidget
from toolset.gui.widgets.settings.module_designer import ModuleDesignerWidget

from toolset.rcc import resources_rc_pyqt6
