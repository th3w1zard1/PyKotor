# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '..\ui\editors\lyt.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_LYTEditor(object):
    def setupUi(self, LYTEditor):
        LYTEditor.setObjectName("LYTEditor")
        LYTEditor.resize(800, 600)
        self.verticalLayout = QtWidgets.QVBoxLayout(LYTEditor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtWidgets.QSplitter(LYTEditor)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.leftPanel = QtWidgets.QWidget(self.splitter)
        self.leftPanel.setObjectName("leftPanel")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.leftPanel)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.graphicsView = QtWidgets.QGraphicsView(self.leftPanel)
        self.graphicsView.setObjectName("graphicsView")
        self.verticalLayout_2.addWidget(self.graphicsView)
        self.zoomSlider = QtWidgets.QSlider(self.leftPanel)
        self.zoomSlider.setOrientation(QtCore.Qt.Horizontal)
        self.zoomSlider.setObjectName("zoomSlider")
        self.verticalLayout_2.addWidget(self.zoomSlider)
        self.rightPanel = QtWidgets.QWidget(self.splitter)
        self.rightPanel.setObjectName("rightPanel")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.rightPanel)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.tabWidget = QtWidgets.QTabWidget(self.rightPanel)
        self.tabWidget.setObjectName("tabWidget")
        self.roomsTab = QtWidgets.QWidget()
        self.roomsTab.setObjectName("roomsTab")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.roomsTab)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.roomsList = QtWidgets.QListWidget(self.roomsTab)
        self.roomsList.setObjectName("roomsList")
        self.verticalLayout_4.addWidget(self.roomsList)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.addRoomButton = QtWidgets.QPushButton(self.roomsTab)
        self.addRoomButton.setObjectName("addRoomButton")
        self.horizontalLayout.addWidget(self.addRoomButton)
        self.editRoomButton = QtWidgets.QPushButton(self.roomsTab)
        self.editRoomButton.setObjectName("editRoomButton")
        self.horizontalLayout.addWidget(self.editRoomButton)
        self.deleteRoomButton = QtWidgets.QPushButton(self.roomsTab)
        self.deleteRoomButton.setObjectName("deleteRoomButton")
        self.horizontalLayout.addWidget(self.deleteRoomButton)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.tabWidget.addTab(self.roomsTab, "")
        self.tracksTab = QtWidgets.QWidget()
        self.tracksTab.setObjectName("tracksTab")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.tracksTab)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.tracksList = QtWidgets.QListWidget(self.tracksTab)
        self.tracksList.setObjectName("tracksList")
        self.verticalLayout_5.addWidget(self.tracksList)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.addTrackButton = QtWidgets.QPushButton(self.tracksTab)
        self.addTrackButton.setObjectName("addTrackButton")
        self.horizontalLayout_2.addWidget(self.addTrackButton)
        self.editTrackButton = QtWidgets.QPushButton(self.tracksTab)
        self.editTrackButton.setObjectName("editTrackButton")
        self.horizontalLayout_2.addWidget(self.editTrackButton)
        self.deleteTrackButton = QtWidgets.QPushButton(self.tracksTab)
        self.deleteTrackButton.setObjectName("deleteTrackButton")
        self.horizontalLayout_2.addWidget(self.deleteTrackButton)
        self.verticalLayout_5.addLayout(self.horizontalLayout_2)
        self.tabWidget.addTab(self.tracksTab, "")
        self.obstaclesTab = QtWidgets.QWidget()
        self.obstaclesTab.setObjectName("obstaclesTab")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.obstaclesTab)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.obstaclesList = QtWidgets.QListWidget(self.obstaclesTab)
        self.obstaclesList.setObjectName("obstaclesList")
        self.verticalLayout_6.addWidget(self.obstaclesList)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.addObstacleButton = QtWidgets.QPushButton(self.obstaclesTab)
        self.addObstacleButton.setObjectName("addObstacleButton")
        self.horizontalLayout_3.addWidget(self.addObstacleButton)
        self.editObstacleButton = QtWidgets.QPushButton(self.obstaclesTab)
        self.editObstacleButton.setObjectName("editObstacleButton")
        self.horizontalLayout_3.addWidget(self.editObstacleButton)
        self.deleteObstacleButton = QtWidgets.QPushButton(self.obstaclesTab)
        self.deleteObstacleButton.setObjectName("deleteObstacleButton")
        self.horizontalLayout_3.addWidget(self.deleteObstacleButton)
        self.verticalLayout_6.addLayout(self.horizontalLayout_3)
        self.tabWidget.addTab(self.obstaclesTab, "")
        self.doorhooksTab = QtWidgets.QWidget()
        self.doorhooksTab.setObjectName("doorhooksTab")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.doorhooksTab)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.doorhooksList = QtWidgets.QListWidget(self.doorhooksTab)
        self.doorhooksList.setObjectName("doorhooksList")
        self.verticalLayout_7.addWidget(self.doorhooksList)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.addDoorhookButton = QtWidgets.QPushButton(self.doorhooksTab)
        self.addDoorhookButton.setObjectName("addDoorhookButton")
        self.horizontalLayout_4.addWidget(self.addDoorhookButton)
        self.editDoorhookButton = QtWidgets.QPushButton(self.doorhooksTab)
        self.editDoorhookButton.setObjectName("editDoorhookButton")
        self.horizontalLayout_4.addWidget(self.editDoorhookButton)
        self.deleteDoorhookButton = QtWidgets.QPushButton(self.doorhooksTab)
        self.deleteDoorhookButton.setObjectName("deleteDoorhookButton")
        self.horizontalLayout_4.addWidget(self.deleteDoorhookButton)
        self.verticalLayout_7.addLayout(self.horizontalLayout_4)
        self.tabWidget.addTab(self.doorhooksTab, "")
        self.verticalLayout_3.addWidget(self.tabWidget)
        self.generateWalkmeshButton = QtWidgets.QPushButton(self.rightPanel)
        self.generateWalkmeshButton.setObjectName("generateWalkmeshButton")
        self.verticalLayout_3.addWidget(self.generateWalkmeshButton)
        self.verticalLayout.addWidget(self.splitter)

        self.retranslateUi(LYTEditor)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(LYTEditor)

    def retranslateUi(self, LYTEditor):
        _translate = QtCore.QCoreApplication.translate
        LYTEditor.setWindowTitle(_translate("LYTEditor", "LYT Editor"))
        self.addRoomButton.setText(_translate("LYTEditor", "Add Room"))
        self.editRoomButton.setText(_translate("LYTEditor", "Edit Room"))
        self.deleteRoomButton.setText(_translate("LYTEditor", "Delete Room"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.roomsTab), _translate("LYTEditor", "Rooms"))
        self.addTrackButton.setText(_translate("LYTEditor", "Add Track"))
        self.editTrackButton.setText(_translate("LYTEditor", "Edit Track"))
        self.deleteTrackButton.setText(_translate("LYTEditor", "Delete Track"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tracksTab), _translate("LYTEditor", "Tracks"))
        self.addObstacleButton.setText(_translate("LYTEditor", "Add Obstacle"))
        self.editObstacleButton.setText(_translate("LYTEditor", "Edit Obstacle"))
        self.deleteObstacleButton.setText(_translate("LYTEditor", "Delete Obstacle"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.obstaclesTab), _translate("LYTEditor", "Obstacles"))
        self.addDoorhookButton.setText(_translate("LYTEditor", "Add Doorhook"))
        self.editDoorhookButton.setText(_translate("LYTEditor", "Edit Doorhook"))
        self.deleteDoorhookButton.setText(_translate("LYTEditor", "Delete Doorhook"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.doorhooksTab), _translate("LYTEditor", "Doorhooks"))
        self.generateWalkmeshButton.setText(_translate("LYTEditor", "Generate Walkmesh"))

from toolset.rcc import resources_rc_pyqt5