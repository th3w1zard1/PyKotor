# Form implementation generated from reading ui file '..\ui\editors\tlk.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(463, 577)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QtWidgets.QSplitter(parent=self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.splitter.setObjectName("splitter")
        self.layoutWidget = QtWidgets.QWidget(parent=self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.searchBox = QtWidgets.QGroupBox(parent=self.layoutWidget)
        self.searchBox.setObjectName("searchBox")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.searchBox)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.searchEdit = QtWidgets.QLineEdit(parent=self.searchBox)
        self.searchEdit.setObjectName("searchEdit")
        self.horizontalLayout_2.addWidget(self.searchEdit)
        self.searchButton = QtWidgets.QPushButton(parent=self.searchBox)
        self.searchButton.setObjectName("searchButton")
        self.horizontalLayout_2.addWidget(self.searchButton)
        self.horizontalLayout_3.addWidget(self.searchBox)
        self.jumpBox = QtWidgets.QGroupBox(parent=self.layoutWidget)
        self.jumpBox.setObjectName("jumpBox")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.jumpBox)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.jumpSpinbox = QtWidgets.QSpinBox(parent=self.jumpBox)
        self.jumpSpinbox.setMinimum(-2147483648)
        self.jumpSpinbox.setMaximum(2147483647)
        self.jumpSpinbox.setObjectName("jumpSpinbox")
        self.horizontalLayout_4.addWidget(self.jumpSpinbox)
        self.jumpButton = QtWidgets.QPushButton(parent=self.jumpBox)
        self.jumpButton.setObjectName("jumpButton")
        self.horizontalLayout_4.addWidget(self.jumpButton)
        self.horizontalLayout_3.addWidget(self.jumpBox)
        self.horizontalLayout_3.setStretch(0, 5)
        self.horizontalLayout_3.setStretch(1, 3)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.talkTable = RobustTableView(parent=self.layoutWidget)
        self.talkTable.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.talkTable.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.talkTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.talkTable.setObjectName("talkTable")
        self.talkTable.horizontalHeader().setVisible(False)
        self.talkTable.horizontalHeader().setHighlightSections(False)
        self.talkTable.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout.addWidget(self.talkTable)
        self.layoutWidget1 = QtWidgets.QWidget(parent=self.splitter)
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.textEdit = QtWidgets.QPlainTextEdit(parent=self.layoutWidget1)
        self.textEdit.setEnabled(False)
        self.textEdit.setMaximumSize(QtCore.QSize(16777215, 200))
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout_2.addWidget(self.textEdit)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(parent=self.layoutWidget1)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.soundEdit = QtWidgets.QLineEdit(parent=self.layoutWidget1)
        self.soundEdit.setEnabled(False)
        self.soundEdit.setMaxLength(16)
        self.soundEdit.setObjectName("soundEdit")
        self.horizontalLayout.addWidget(self.soundEdit)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 463, 21))
        self.menubar.setObjectName("menubar")
        self.menuView = QtWidgets.QMenu(parent=self.menubar)
        self.menuView.setObjectName("menuView")
        self.menuFile = QtWidgets.QMenu(parent=self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuLanguage = QtWidgets.QMenu(parent=self.menubar)
        self.menuLanguage.setObjectName("menuLanguage")
        MainWindow.setMenuBar(self.menubar)
        self.actionGoTo = QtGui.QAction(parent=MainWindow)
        self.actionGoTo.setObjectName("actionGoTo")
        self.actionFind = QtGui.QAction(parent=MainWindow)
        self.actionFind.setObjectName("actionFind")
        self.actionNew = QtGui.QAction(parent=MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen = QtGui.QAction(parent=MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QtGui.QAction(parent=MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSaveAs = QtGui.QAction(parent=MainWindow)
        self.actionSaveAs.setObjectName("actionSaveAs")
        self.actionRevert = QtGui.QAction(parent=MainWindow)
        self.actionRevert.setObjectName("actionRevert")
        self.actionClose = QtGui.QAction(parent=MainWindow)
        self.actionClose.setObjectName("actionClose")
        self.actionInsert = QtGui.QAction(parent=MainWindow)
        self.actionInsert.setObjectName("actionInsert")
        self.actionAuto_detect_slower = QtGui.QAction(parent=MainWindow)
        self.actionAuto_detect_slower.setObjectName("actionAuto_detect_slower")
        self.menuView.addAction(self.actionGoTo)
        self.menuView.addAction(self.actionFind)
        self.menuView.addAction(self.actionInsert)
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionClose)
        self.menuLanguage.addAction(self.actionAuto_detect_slower)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuLanguage.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.searchBox.setTitle(_translate("MainWindow", "Search"))
        self.searchButton.setText(_translate("MainWindow", "Search"))
        self.jumpBox.setTitle(_translate("MainWindow", "Go To Line"))
        self.jumpButton.setText(_translate("MainWindow", "Jump"))
        self.label.setText(_translate("MainWindow", "Sound ResRef:"))
        self.menuView.setTitle(_translate("MainWindow", "Tools"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuLanguage.setTitle(_translate("MainWindow", "Language"))
        self.actionGoTo.setText(_translate("MainWindow", "Go to"))
        self.actionFind.setText(_translate("MainWindow", "Find"))
        self.actionNew.setText(_translate("MainWindow", "New"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionSave.setText(_translate("MainWindow", "Save"))
        self.actionSaveAs.setText(_translate("MainWindow", "Save As"))
        self.actionRevert.setText(_translate("MainWindow", "Revert"))
        self.actionClose.setText(_translate("MainWindow", "Exit"))
        self.actionInsert.setText(_translate("MainWindow", "Insert"))
        self.actionAuto_detect_slower.setText(_translate("MainWindow", "Auto-detect (slower)"))
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTableView

from toolset.rcc import resources_rc_pyqt6
