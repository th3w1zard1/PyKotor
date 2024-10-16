# Form implementation generated from reading ui file '..\ui\editors\jrl.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(948, 701)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QtWidgets.QSplitter(parent=self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.splitter.setObjectName("splitter")
        self.journalTree = RobustTreeView(parent=self.splitter)
        self.journalTree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.journalTree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.journalTree.setHeaderHidden(True)
        self.journalTree.setObjectName("journalTree")
        self.questPages = QtWidgets.QStackedWidget(parent=self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.questPages.sizePolicy().hasHeightForWidth())
        self.questPages.setSizePolicy(sizePolicy)
        self.questPages.setObjectName("questPages")
        self.categoryPage = QtWidgets.QWidget()
        self.categoryPage.setObjectName("categoryPage")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.categoryPage)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(parent=self.categoryPage)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.categoryNameEdit = LocalizedStringLineEdit(parent=self.categoryPage)
        self.categoryNameEdit.setMinimumSize(QtCore.QSize(0, 23))
        self.categoryNameEdit.setObjectName("categoryNameEdit")
        self.horizontalLayout.addWidget(self.categoryNameEdit)
        self.formLayout.setLayout(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.horizontalLayout)
        self.label_2 = QtWidgets.QLabel(parent=self.categoryPage)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_2)
        self.label_5 = QtWidgets.QLabel(parent=self.categoryPage)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_5)
        self.categoryTag = QtWidgets.QLineEdit(parent=self.categoryPage)
        self.categoryTag.setObjectName("categoryTag")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.categoryTag)
        self.label_3 = QtWidgets.QLabel(parent=self.categoryPage)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_3)
        self.categoryPlanetSelect = ComboBox2DA(parent=self.categoryPage)
        self.categoryPlanetSelect.setObjectName("categoryPlanetSelect")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.categoryPlanetSelect)
        self.categoryPlotSelect = ComboBox2DA(parent=self.categoryPage)
        self.categoryPlotSelect.setObjectName("categoryPlotSelect")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.categoryPlotSelect)
        self.label_4 = QtWidgets.QLabel(parent=self.categoryPage)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_4)
        self.categoryPrioritySelect = QtWidgets.QComboBox(parent=self.categoryPage)
        self.categoryPrioritySelect.setObjectName("categoryPrioritySelect")
        self.categoryPrioritySelect.addItem("")
        self.categoryPrioritySelect.addItem("")
        self.categoryPrioritySelect.addItem("")
        self.categoryPrioritySelect.addItem("")
        self.categoryPrioritySelect.addItem("")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.categoryPrioritySelect)
        self.horizontalLayout_2.addLayout(self.formLayout)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_6 = QtWidgets.QLabel(parent=self.categoryPage)
        self.label_6.setObjectName("label_6")
        self.verticalLayout_2.addWidget(self.label_6)
        self.categoryCommentEdit = HTPlainTextEdit(parent=self.categoryPage)
        self.categoryCommentEdit.setObjectName("categoryCommentEdit")
        self.verticalLayout_2.addWidget(self.categoryCommentEdit)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 2)
        self.questPages.addWidget(self.categoryPage)
        self.entryPage = QtWidgets.QWidget()
        self.entryPage.setObjectName("entryPage")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.entryPage)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.formLayout_2 = QtWidgets.QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_8 = QtWidgets.QLabel(parent=self.entryPage)
        self.label_8.setObjectName("label_8")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_8)
        self.entryIdSpin = QtWidgets.QSpinBox(parent=self.entryPage)
        self.entryIdSpin.setMinimumSize(QtCore.QSize(80, 0))
        self.entryIdSpin.setObjectName("entryIdSpin")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.entryIdSpin)
        self.label_7 = QtWidgets.QLabel(parent=self.entryPage)
        self.label_7.setObjectName("label_7")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_7)
        self.label_9 = QtWidgets.QLabel(parent=self.entryPage)
        self.label_9.setObjectName("label_9")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_9)
        self.entryXpSpin = QtWidgets.QDoubleSpinBox(parent=self.entryPage)
        self.entryXpSpin.setObjectName("entryXpSpin")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.entryXpSpin)
        self.entryEndCheck = QtWidgets.QCheckBox(parent=self.entryPage)
        self.entryEndCheck.setText("")
        self.entryEndCheck.setObjectName("entryEndCheck")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.entryEndCheck)
        self.horizontalLayout_3.addLayout(self.formLayout_2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_10 = QtWidgets.QLabel(parent=self.entryPage)
        self.label_10.setObjectName("label_10")
        self.verticalLayout.addWidget(self.label_10)
        self.entryTextEdit = HTPlainTextEdit(parent=self.entryPage)
        self.entryTextEdit.setReadOnly(True)
        self.entryTextEdit.setObjectName("entryTextEdit")
        self.verticalLayout.addWidget(self.entryTextEdit)
        self.horizontalLayout_3.addLayout(self.verticalLayout)
        self.questPages.addWidget(self.entryPage)
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 948, 22))
        self.menubar.setObjectName("menubar")
        self.menuNew = QtWidgets.QMenu(parent=self.menubar)
        self.menuNew.setObjectName("menuNew")
        MainWindow.setMenuBar(self.menubar)
        self.actionOpen = QtGui.QAction(parent=MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QtGui.QAction(parent=MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSave_As = QtGui.QAction(parent=MainWindow)
        self.actionSave_As.setObjectName("actionSave_As")
        self.actionNew = QtGui.QAction(parent=MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionRevert = QtGui.QAction(parent=MainWindow)
        self.actionRevert.setObjectName("actionRevert")
        self.actionExit = QtGui.QAction(parent=MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.menuNew.addAction(self.actionNew)
        self.menuNew.addAction(self.actionOpen)
        self.menuNew.addAction(self.actionSave)
        self.menuNew.addAction(self.actionSave_As)
        self.menuNew.addAction(self.actionRevert)
        self.menuNew.addSeparator()
        self.menuNew.addAction(self.actionExit)
        self.menubar.addAction(self.menuNew.menuAction())

        self.retranslateUi(MainWindow)
        self.questPages.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label.setText(_translate("MainWindow", "Name:"))
        self.label_2.setText(_translate("MainWindow", "Planet ID:"))
        self.label_5.setText(_translate("MainWindow", "Tag:"))
        self.label_3.setText(_translate("MainWindow", "Plot Index:"))
        self.label_4.setText(_translate("MainWindow", "Priority:"))
        self.categoryPrioritySelect.setItemText(0, _translate("MainWindow", "Highest"))
        self.categoryPrioritySelect.setItemText(1, _translate("MainWindow", "High"))
        self.categoryPrioritySelect.setItemText(2, _translate("MainWindow", "Medium"))
        self.categoryPrioritySelect.setItemText(3, _translate("MainWindow", "Low"))
        self.categoryPrioritySelect.setItemText(4, _translate("MainWindow", "Lowest"))
        self.label_6.setText(_translate("MainWindow", "Comment:"))
        self.label_8.setText(_translate("MainWindow", "ID:"))
        self.label_7.setText(_translate("MainWindow", "End:"))
        self.label_9.setText(_translate("MainWindow", "XP Percentage:"))
        self.label_10.setText(_translate("MainWindow", "Text:"))
        self.menuNew.setTitle(_translate("MainWindow", "File"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionSave.setText(_translate("MainWindow", "Save"))
        self.actionSave_As.setText(_translate("MainWindow", "Save As"))
        self.actionNew.setText(_translate("MainWindow", "New"))
        self.actionRevert.setText(_translate("MainWindow", "Revert"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
from toolset.gui.editors.dlg import RobustTreeView
from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit
from toolset.gui.widgets.edit.plaintext import HTPlainTextEdit

from toolset.rcc import resources_rc_pyqt6
