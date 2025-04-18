# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '..\ui\widgets\settings\application.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ApplicationSettingsWidget(object):
    def setupUi(self, ApplicationSettingsWidget):
        ApplicationSettingsWidget.setObjectName("ApplicationSettingsWidget")
        ApplicationSettingsWidget.resize(800, 600)
        self.verticalLayout = QtWidgets.QVBoxLayout(ApplicationSettingsWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.resetAttributesButton = QtWidgets.QPushButton(ApplicationSettingsWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.resetAttributesButton.sizePolicy().hasHeightForWidth())
        self.resetAttributesButton.setSizePolicy(sizePolicy)
        self.resetAttributesButton.setMaximumSize(QtCore.QSize(16777215, 50))
        self.resetAttributesButton.setObjectName("resetAttributesButton")
        self.verticalLayout_4.addWidget(self.resetAttributesButton)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem)
        self.verticalLayout.addLayout(self.verticalLayout_4)
        self.scrollArea = QtWidgets.QScrollArea(ApplicationSettingsWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 780, 580))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBoxFontSettings = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxFontSettings.setObjectName("groupBoxFontSettings")
        self.verticalLayout_font = QtWidgets.QVBoxLayout(self.groupBoxFontSettings)
        self.verticalLayout_font.setObjectName("verticalLayout_font")
        self.currentFontLabel = QtWidgets.QLabel(self.groupBoxFontSettings)
        self.currentFontLabel.setObjectName("currentFontLabel")
        self.verticalLayout_font.addWidget(self.currentFontLabel)
        self.fontButton = QtWidgets.QPushButton(self.groupBoxFontSettings)
        self.fontButton.setObjectName("fontButton")
        self.verticalLayout_font.addWidget(self.fontButton)
        self.verticalLayout_2.addWidget(self.groupBoxFontSettings)
        self.groupBoxEnvVariables = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxEnvVariables.setObjectName("groupBoxEnvVariables")
        self.verticalLayout_env = QtWidgets.QVBoxLayout(self.groupBoxEnvVariables)
        self.verticalLayout_env.setObjectName("verticalLayout_env")
        self.tableWidget = QtWidgets.QTableWidget(self.groupBoxEnvVariables)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setObjectName("tableWidget")
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        self.verticalLayout_env.addWidget(self.tableWidget)
        self.horizontalLayout_buttons = QtWidgets.QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName("horizontalLayout_buttons")
        self.addButton = QtWidgets.QPushButton(self.groupBoxEnvVariables)
        self.addButton.setObjectName("addButton")
        self.horizontalLayout_buttons.addWidget(self.addButton)
        self.editButton = QtWidgets.QPushButton(self.groupBoxEnvVariables)
        self.editButton.setObjectName("editButton")
        self.horizontalLayout_buttons.addWidget(self.editButton)
        self.removeButton = QtWidgets.QPushButton(self.groupBoxEnvVariables)
        self.removeButton.setObjectName("removeButton")
        self.horizontalLayout_buttons.addWidget(self.removeButton)
        self.verticalLayout_env.addLayout(self.horizontalLayout_buttons)
        self.verticalLayout_2.addWidget(self.groupBoxEnvVariables)
        self.groupBoxMiscSettings = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxMiscSettings.setObjectName("groupBoxMiscSettings")
        self.verticalLayout_misc = QtWidgets.QVBoxLayout(self.groupBoxMiscSettings)
        self.verticalLayout_misc.setObjectName("verticalLayout_misc")
        self.verticalLayout_2.addWidget(self.groupBoxMiscSettings)
        self.groupBoxAASettings = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.groupBoxAASettings.setObjectName("groupBoxAASettings")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBoxAASettings)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_2.addWidget(self.groupBoxAASettings)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)

        self.retranslateUi(ApplicationSettingsWidget)
        QtCore.QMetaObject.connectSlotsByName(ApplicationSettingsWidget)

    def retranslateUi(self, ApplicationSettingsWidget):
        _translate = QtCore.QCoreApplication.translate
        ApplicationSettingsWidget.setWindowTitle(_translate("ApplicationSettingsWidget", "Application Settings"))
        self.resetAttributesButton.setText(_translate("ApplicationSettingsWidget", "Reset All on this Page"))
        self.groupBoxFontSettings.setTitle(_translate("ApplicationSettingsWidget", "Global Font Settings"))
        self.currentFontLabel.setText(_translate("ApplicationSettingsWidget", "Current Font: Default"))
        self.fontButton.setText(_translate("ApplicationSettingsWidget", "Select Font..."))
        self.groupBoxEnvVariables.setTitle(_translate("ApplicationSettingsWidget", "Environment Variables"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("ApplicationSettingsWidget", "Variable"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("ApplicationSettingsWidget", "Value"))
        self.addButton.setText(_translate("ApplicationSettingsWidget", "Add"))
        self.editButton.setText(_translate("ApplicationSettingsWidget", "Edit"))
        self.removeButton.setText(_translate("ApplicationSettingsWidget", "Remove"))
        self.groupBoxMiscSettings.setTitle(_translate("ApplicationSettingsWidget", "Miscellaneous Settings"))
        self.groupBoxAASettings.setTitle(_translate("ApplicationSettingsWidget", "Experimental settings (may cause app crashes)"))

from toolset.rcc import resources_rc_pyqt5
