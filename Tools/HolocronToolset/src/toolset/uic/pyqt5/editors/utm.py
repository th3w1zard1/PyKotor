# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '..\ui\editors\utm.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(414, 335)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.tab)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_6 = QtWidgets.QLabel(self.tab)
        self.label_6.setObjectName("label_6")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_6)
        self.horizontalLayout_18 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_18.setObjectName("horizontalLayout_18")
        self.nameEdit = LocalizedStringLineEdit(self.tab)
        self.nameEdit.setMinimumSize(QtCore.QSize(0, 23))
        self.nameEdit.setObjectName("nameEdit")
        self.horizontalLayout_18.addWidget(self.nameEdit)
        self.formLayout.setLayout(0, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_18)
        self.label_14 = QtWidgets.QLabel(self.tab)
        self.label_14.setObjectName("label_14")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_14)
        self.horizontalLayout_19 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_19.setObjectName("horizontalLayout_19")
        self.tagEdit = QtWidgets.QLineEdit(self.tab)
        self.tagEdit.setObjectName("tagEdit")
        self.horizontalLayout_19.addWidget(self.tagEdit)
        self.tagGenerateButton = QtWidgets.QPushButton(self.tab)
        self.tagGenerateButton.setMaximumSize(QtCore.QSize(26, 16777215))
        self.tagGenerateButton.setObjectName("tagGenerateButton")
        self.horizontalLayout_19.addWidget(self.tagGenerateButton)
        self.formLayout.setLayout(1, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_19)
        self.label_38 = QtWidgets.QLabel(self.tab)
        self.label_38.setObjectName("label_38")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_38)
        self.horizontalLayout_20 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_20.setObjectName("horizontalLayout_20")
        self.resrefEdit = QtWidgets.QLineEdit(self.tab)
        self.resrefEdit.setMaxLength(16)
        self.resrefEdit.setObjectName("resrefEdit")
        self.horizontalLayout_20.addWidget(self.resrefEdit)
        self.resrefGenerateButton = QtWidgets.QPushButton(self.tab)
        self.resrefGenerateButton.setMaximumSize(QtCore.QSize(26, 16777215))
        self.resrefGenerateButton.setObjectName("resrefGenerateButton")
        self.horizontalLayout_20.addWidget(self.resrefGenerateButton)
        self.formLayout.setLayout(2, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_20)
        self.label_39 = QtWidgets.QLabel(self.tab)
        self.label_39.setObjectName("label_39")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_39)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.idSpin = QtWidgets.QSpinBox(self.tab)
        self.idSpin.setMinimum(-2147483648)
        self.idSpin.setMaximum(2147483647)
        self.idSpin.setObjectName("idSpin")
        self.horizontalLayout.addWidget(self.idSpin)
        spacerItem = QtWidgets.QSpacerItem(29, 17, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.formLayout.setLayout(3, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout)
        self.verticalLayout_3.addLayout(self.formLayout)
        self.inventoryButton = QtWidgets.QPushButton(self.tab)
        self.inventoryButton.setObjectName("inventoryButton")
        self.verticalLayout_3.addWidget(self.inventoryButton)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.groupBox = QtWidgets.QGroupBox(self.tab)
        self.groupBox.setObjectName("groupBox")
        self.formLayout_2 = QtWidgets.QFormLayout(self.groupBox)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.markUpSpin = QtWidgets.QSpinBox(self.groupBox)
        self.markUpSpin.setMaximum(1000000)
        self.markUpSpin.setObjectName("markUpSpin")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.markUpSpin)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.markDownSpin = QtWidgets.QSpinBox(self.groupBox)
        self.markDownSpin.setMaximum(1000000)
        self.markDownSpin.setObjectName("markDownSpin")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.markDownSpin)
        self.horizontalLayout_2.addWidget(self.groupBox)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.frame_2 = QtWidgets.QFrame(self.tab)
        self.frame_2.setObjectName("frame_2")
        self.formLayout_3 = QtWidgets.QFormLayout(self.frame_2)
        self.formLayout_3.setObjectName("formLayout_3")
        self.label_3 = QtWidgets.QLabel(self.frame_2)
        self.label_3.setObjectName("label_3")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.onOpenEdit = QtWidgets.QLineEdit(self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.onOpenEdit.sizePolicy().hasHeightForWidth())
        self.onOpenEdit.setSizePolicy(sizePolicy)
        self.onOpenEdit.setMaxLength(16)
        self.onOpenEdit.setObjectName("onOpenEdit")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.onOpenEdit)
        self.label_4 = QtWidgets.QLabel(self.frame_2)
        self.label_4.setObjectName("label_4")
        self.formLayout_3.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.storeFlagSelect = QtWidgets.QComboBox(self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.storeFlagSelect.sizePolicy().hasHeightForWidth())
        self.storeFlagSelect.setSizePolicy(sizePolicy)
        self.storeFlagSelect.setObjectName("storeFlagSelect")
        self.storeFlagSelect.addItem("")
        self.storeFlagSelect.addItem("")
        self.storeFlagSelect.addItem("")
        self.formLayout_3.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.storeFlagSelect)
        self.verticalLayout_2.addWidget(self.frame_2, 0, QtCore.Qt.AlignVCenter)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 2)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.tabWidget.addTab(self.tab, "")
        self.commentsTab = QtWidgets.QWidget()
        self.commentsTab.setObjectName("commentsTab")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.commentsTab)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.commentsEdit = QtWidgets.QPlainTextEdit(self.commentsTab)
        self.commentsEdit.setObjectName("commentsEdit")
        self.gridLayout_2.addWidget(self.commentsEdit, 0, 0, 1, 1)
        self.tabWidget.addTab(self.commentsTab, "")
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 414, 22))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.actionNew = QtWidgets.QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen = QtWidgets.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QtWidgets.QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSaveAs = QtWidgets.QAction(MainWindow)
        self.actionSaveAs.setObjectName("actionSaveAs")
        self.actionRevert = QtWidgets.QAction(MainWindow)
        self.actionRevert.setObjectName("actionRevert")
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label_6.setText(_translate("MainWindow", "Name:"))
        self.label_14.setText(_translate("MainWindow", "Tag:"))
        self.tagGenerateButton.setText(_translate("MainWindow", "-"))
        self.label_38.setText(_translate("MainWindow", "ResRef:"))
        self.resrefGenerateButton.setText(_translate("MainWindow", "-"))
        self.label_39.setText(_translate("MainWindow", "ID:"))
        self.inventoryButton.setText(_translate("MainWindow", "Edit Inventory"))
        self.groupBox.setTitle(_translate("MainWindow", "Pricing"))
        self.label.setText(_translate("MainWindow", "Mark Up"))
        self.label_2.setText(_translate("MainWindow", "Mark Down"))
        self.label_3.setText(_translate("MainWindow", "OnOpenStore"))
        self.label_4.setText(_translate("MainWindow", "Store"))
        self.storeFlagSelect.setItemText(0, _translate("MainWindow", "Only Buy"))
        self.storeFlagSelect.setItemText(1, _translate("MainWindow", "Only Sell"))
        self.storeFlagSelect.setItemText(2, _translate("MainWindow", "Buy and Sell"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Basic"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.commentsTab), _translate("MainWindow", "Comments"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionNew.setText(_translate("MainWindow", "New"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionSave.setText(_translate("MainWindow", "Save"))
        self.actionSaveAs.setText(_translate("MainWindow", "Save As"))
        self.actionRevert.setText(_translate("MainWindow", "Revert"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit

from toolset.rcc import resources_rc_pyqt5
