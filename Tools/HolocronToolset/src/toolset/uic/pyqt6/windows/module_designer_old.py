# Form implementation generated from reading ui file '..\ui\windows\module_designer_old.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(970, 650)
        MainWindow.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.lockInstancesCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.lockInstancesCheck.setMaximumSize(QtCore.QSize(28, 16777215))
        self.lockInstancesCheck.setStyleSheet("                                        \n"
"    QCheckbox {\n"
"    spacing: 0px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator {\n"
"    image: url(:/images/icons/lock.png);\n"
"    border: 1px solid rgba(30, 144, 255, 0.0);\n"
"    width: 26px;\n"
"    height: 26px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"    background: rgba(30, 144, 255, 0.2);\n"
"    border: 1px solid rgba(30, 144, 255, 0.4);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked {\n"
"    background: rgba(30, 144, 255, 0.4);\n"
"    border:1px solid rgba(30, 144, 255, 0.6);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked:hover {\n"
"    background: rgba(30, 144, 255, 0.5);\n"
"    border:1px solid rgba(30, 144, 255, 0.7);\n"
"    }\n"
"    \n"
"")
        self.lockInstancesCheck.setText("")
        self.lockInstancesCheck.setChecked(False)
        self.lockInstancesCheck.setObjectName("lockInstancesCheck")
        self.horizontalLayout_2.addWidget(self.lockInstancesCheck)
        self.line_2 = QtWidgets.QFrame(parent=self.centralwidget)
        self.line_2.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line_2.setObjectName("line_2")
        self.horizontalLayout_2.addWidget(self.line_2)
        self.cursorCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.cursorCheck.setMaximumSize(QtCore.QSize(28, 16777215))
        self.cursorCheck.setStyleSheet("                                        \n"
"    QCheckbox {\n"
"    spacing: 0px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator {\n"
"    image: url(:/images/icons/cursor.png);\n"
"    border: 1px solid rgba(30, 144, 255, 0.0);\n"
"    width: 26px;\n"
"    height: 26px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"    background: rgba(30, 144, 255, 0.2);\n"
"    border: 1px solid rgba(30, 144, 255, 0.4);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked {\n"
"    background: rgba(30, 144, 255, 0.4);\n"
"    border:1px solid rgba(30, 144, 255, 0.6);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked:hover {\n"
"    background: rgba(30, 144, 255, 0.5);\n"
"    border:1px solid rgba(30, 144, 255, 0.7);\n"
"    }\n"
"    \n"
"")
        self.cursorCheck.setText("")
        self.cursorCheck.setChecked(True)
        self.cursorCheck.setObjectName("cursorCheck")
        self.horizontalLayout_2.addWidget(self.cursorCheck)
        self.backfaceCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.backfaceCheck.setMaximumSize(QtCore.QSize(28, 16777215))
        self.backfaceCheck.setStyleSheet("                                        \n"
"    QCheckbox {\n"
"    spacing: 0px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator {\n"
"    image: url(:/images/icons/backface.png);\n"
"    border: 1px solid rgba(30, 144, 255, 0.0);\n"
"    width: 26px;\n"
"    height: 26px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"    background: rgba(30, 144, 255, 0.2);\n"
"    border: 1px solid rgba(30, 144, 255, 0.4);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked {\n"
"    background: rgba(30, 144, 255, 0.4);\n"
"    border:1px solid rgba(30, 144, 255, 0.6);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked:hover {\n"
"    background: rgba(30, 144, 255, 0.5);\n"
"    border:1px solid rgba(30, 144, 255, 0.7);\n"
"    }\n"
"    \n"
"")
        self.backfaceCheck.setText("")
        self.backfaceCheck.setChecked(True)
        self.backfaceCheck.setObjectName("backfaceCheck")
        self.horizontalLayout_2.addWidget(self.backfaceCheck)
        self.lightmapCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.lightmapCheck.setMaximumSize(QtCore.QSize(28, 16777215))
        self.lightmapCheck.setStyleSheet("                                        \n"
"    QCheckbox {\n"
"    spacing: 0px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator {\n"
"    image: url(:/images/icons/lightmap.png);\n"
"    border: 1px solid rgba(30, 144, 255, 0.0);\n"
"    width: 26px;\n"
"    height: 26px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"    background: rgba(30, 144, 255, 0.2);\n"
"    border: 1px solid rgba(30, 144, 255, 0.4);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked {\n"
"    background: rgba(30, 144, 255, 0.4);\n"
"    border:1px solid rgba(30, 144, 255, 0.6);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked:hover {\n"
"    background: rgba(30, 144, 255, 0.5);\n"
"    border:1px solid rgba(30, 144, 255, 0.7);\n"
"    }\n"
"    \n"
"")
        self.lightmapCheck.setText("")
        self.lightmapCheck.setChecked(True)
        self.lightmapCheck.setObjectName("lightmapCheck")
        self.horizontalLayout_2.addWidget(self.lightmapCheck)
        self.line = QtWidgets.QFrame(parent=self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout_2.addWidget(self.line)
        self.viewCreatureCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.viewCreatureCheck.setMaximumSize(QtCore.QSize(28, 16777215))
        self.viewCreatureCheck.setStyleSheet("                                        \n"
"    QCheckbox {\n"
"    spacing: 0px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/creature.png);\n"
"    border: 1px solid rgba(30, 144, 255, 0.0);\n"
"    width: 26px;\n"
"    height: 26px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"    background: rgba(30, 144, 255, 0.2);\n"
"    border: 1px solid rgba(30, 144, 255, 0.4);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked {\n"
"    background: rgba(30, 144, 255, 0.4);\n"
"    border:1px solid rgba(30, 144, 255, 0.6);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked:hover {\n"
"    background: rgba(30, 144, 255, 0.5);\n"
"    border:1px solid rgba(30, 144, 255, 0.7);\n"
"    }\n"
"    \n"
"")
        self.viewCreatureCheck.setText("")
        self.viewCreatureCheck.setChecked(True)
        self.viewCreatureCheck.setObjectName("viewCreatureCheck")
        self.horizontalLayout_2.addWidget(self.viewCreatureCheck)
        self.viewDoorCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.viewDoorCheck.setMaximumSize(QtCore.QSize(28, 16777215))
        self.viewDoorCheck.setStyleSheet("                                        \n"
"    QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/door.png);\n"
"    border: 1px solid rgba(30, 144, 255, 0.0);\n"
"    width: 26px;\n"
"    height: 26px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"    background: rgba(30, 144, 255, 0.2);\n"
"    border: 1px solid rgba(30, 144, 255, 0.4);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked {\n"
"    background: rgba(30, 144, 255, 0.4);\n"
"    border:1px solid rgba(30, 144, 255, 0.6);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked:hover {\n"
"    background: rgba(30, 144, 255, 0.5);\n"
"    border:1px solid rgba(30, 144, 255, 0.7);\n"
"    }\n"
"    \n"
"")
        self.viewDoorCheck.setText("")
        self.viewDoorCheck.setChecked(True)
        self.viewDoorCheck.setObjectName("viewDoorCheck")
        self.horizontalLayout_2.addWidget(self.viewDoorCheck)
        self.viewPlaceableCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.viewPlaceableCheck.setMaximumSize(QtCore.QSize(28, 16777215))
        self.viewPlaceableCheck.setStyleSheet("                                        \n"
"    QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/placeable.png);\n"
"    border: 1px solid rgba(30, 144, 255, 0.0);\n"
"    width: 26px;\n"
"    height: 26px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"    background: rgba(30, 144, 255, 0.2);\n"
"    border: 1px solid rgba(30, 144, 255, 0.4);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked {\n"
"    background: rgba(30, 144, 255, 0.4);\n"
"    border:1px solid rgba(30, 144, 255, 0.6);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked:hover {\n"
"    background: rgba(30, 144, 255, 0.5);\n"
"    border:1px solid rgba(30, 144, 255, 0.7);\n"
"    }\n"
"    \n"
"")
        self.viewPlaceableCheck.setText("")
        self.viewPlaceableCheck.setChecked(True)
        self.viewPlaceableCheck.setObjectName("viewPlaceableCheck")
        self.horizontalLayout_2.addWidget(self.viewPlaceableCheck)
        self.viewStoreCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.viewStoreCheck.setMaximumSize(QtCore.QSize(28, 16777215))
        self.viewStoreCheck.setStyleSheet("                                        \n"
"    QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/merchant.png);\n"
"    border: 1px solid rgba(30, 144, 255, 0.0);\n"
"    width: 26px;\n"
"    height: 26px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"    background: rgba(30, 144, 255, 0.2);\n"
"    border: 1px solid rgba(30, 144, 255, 0.4);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked {\n"
"    background: rgba(30, 144, 255, 0.4);\n"
"    border:1px solid rgba(30, 144, 255, 0.6);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked:hover {\n"
"    background: rgba(30, 144, 255, 0.5);\n"
"    border:1px solid rgba(30, 144, 255, 0.7);\n"
"    }\n"
"    \n"
"")
        self.viewStoreCheck.setText("")
        self.viewStoreCheck.setChecked(True)
        self.viewStoreCheck.setObjectName("viewStoreCheck")
        self.horizontalLayout_2.addWidget(self.viewStoreCheck)
        self.viewSoundCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.viewSoundCheck.setMaximumSize(QtCore.QSize(28, 16777215))
        self.viewSoundCheck.setStyleSheet("                                        \n"
"    QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/sound.png);\n"
"    border: 1px solid rgba(30, 144, 255, 0.0);\n"
"    width: 26px;\n"
"    height: 26px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"    background: rgba(30, 144, 255, 0.2);\n"
"    border: 1px solid rgba(30, 144, 255, 0.4);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked {\n"
"    background: rgba(30, 144, 255, 0.4);\n"
"    border:1px solid rgba(30, 144, 255, 0.6);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked:hover {\n"
"    background: rgba(30, 144, 255, 0.5);\n"
"    border:1px solid rgba(30, 144, 255, 0.7);\n"
"    }\n"
"    \n"
"")
        self.viewSoundCheck.setText("")
        self.viewSoundCheck.setChecked(True)
        self.viewSoundCheck.setObjectName("viewSoundCheck")
        self.horizontalLayout_2.addWidget(self.viewSoundCheck)
        self.viewWaypointCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.viewWaypointCheck.setMaximumSize(QtCore.QSize(28, 16777215))
        self.viewWaypointCheck.setStyleSheet("                                        \n"
"    QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/waypoint.png);\n"
"    border: 1px solid rgba(30, 144, 255, 0.0);\n"
"    width: 26px;\n"
"    height: 26px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"    background: rgba(30, 144, 255, 0.2);\n"
"    border: 1px solid rgba(30, 144, 255, 0.4);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked {\n"
"    background: rgba(30, 144, 255, 0.4);\n"
"    border:1px solid rgba(30, 144, 255, 0.6);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked:hover {\n"
"    background: rgba(30, 144, 255, 0.5);\n"
"    border:1px solid rgba(30, 144, 255, 0.7);\n"
"    }\n"
"    \n"
"")
        self.viewWaypointCheck.setText("")
        self.viewWaypointCheck.setChecked(True)
        self.viewWaypointCheck.setObjectName("viewWaypointCheck")
        self.horizontalLayout_2.addWidget(self.viewWaypointCheck)
        self.viewCameraCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.viewCameraCheck.setMaximumSize(QtCore.QSize(28, 16777215))
        self.viewCameraCheck.setStyleSheet("                                        \n"
"    QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/camera.png);\n"
"    border: 1px solid rgba(30, 144, 255, 0.0);\n"
"    width: 26px;\n"
"    height: 26px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"    background: rgba(30, 144, 255, 0.2);\n"
"    border: 1px solid rgba(30, 144, 255, 0.4);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked {\n"
"    background: rgba(30, 144, 255, 0.4);\n"
"    border:1px solid rgba(30, 144, 255, 0.6);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked:hover {\n"
"    background: rgba(30, 144, 255, 0.5);\n"
"    border:1px solid rgba(30, 144, 255, 0.7);\n"
"    }\n"
"    \n"
"")
        self.viewCameraCheck.setText("")
        self.viewCameraCheck.setChecked(True)
        self.viewCameraCheck.setObjectName("viewCameraCheck")
        self.horizontalLayout_2.addWidget(self.viewCameraCheck)
        self.viewEncounterCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.viewEncounterCheck.setMaximumSize(QtCore.QSize(28, 16777215))
        self.viewEncounterCheck.setStyleSheet("                                        \n"
"    QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/encounter.png);\n"
"    border: 1px solid rgba(30, 144, 255, 0.0);\n"
"    width: 26px;\n"
"    height: 26px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"    background: rgba(30, 144, 255, 0.2);\n"
"    border: 1px solid rgba(30, 144, 255, 0.4);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked {\n"
"    background: rgba(30, 144, 255, 0.4);\n"
"    border:1px solid rgba(30, 144, 255, 0.6);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked:hover {\n"
"    background: rgba(30, 144, 255, 0.5);\n"
"    border:1px solid rgba(30, 144, 255, 0.7);\n"
"    }\n"
"    \n"
"")
        self.viewEncounterCheck.setText("")
        self.viewEncounterCheck.setChecked(True)
        self.viewEncounterCheck.setObjectName("viewEncounterCheck")
        self.horizontalLayout_2.addWidget(self.viewEncounterCheck)
        self.viewTriggerCheck = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.viewTriggerCheck.setMaximumSize(QtCore.QSize(28, 16777215))
        self.viewTriggerCheck.setStyleSheet("                                        \n"
"    QCheckBox::indicator {\n"
"    image: url(:/images/icons/k1/trigger.png);\n"
"    border: 1px solid rgba(30, 144, 255, 0.0);\n"
"    width: 26px;\n"
"    height: 26px;\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:unchecked:hover {\n"
"    background: rgba(30, 144, 255, 0.2);\n"
"    border: 1px solid rgba(30, 144, 255, 0.4);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked {\n"
"    background: rgba(30, 144, 255, 0.4);\n"
"    border:1px solid rgba(30, 144, 255, 0.6);\n"
"    }\n"
"    \n"
"    QCheckBox::indicator:checked:hover {\n"
"    background: rgba(30, 144, 255, 0.5);\n"
"    border:1px solid rgba(30, 144, 255, 0.7);\n"
"    }\n"
"    \n"
"")
        self.viewTriggerCheck.setText("")
        self.viewTriggerCheck.setChecked(True)
        self.viewTriggerCheck.setObjectName("viewTriggerCheck")
        self.horizontalLayout_2.addWidget(self.viewTriggerCheck)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.resourceTree = QtWidgets.QTreeWidget(parent=self.centralwidget)
        self.resourceTree.setMaximumSize(QtCore.QSize(200, 16777215))
        self.resourceTree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.resourceTree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.resourceTree.setHeaderHidden(True)
        self.resourceTree.setObjectName("resourceTree")
        self.resourceTree.headerItem().setText(0, "1")
        self.horizontalLayout.addWidget(self.resourceTree)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.splitter = QtWidgets.QSplitter(parent=self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.splitter.setObjectName("splitter")
        self.mainRenderer = ModuleRenderer(parent=self.splitter)
        self.mainRenderer.setMouseTracking(True)
        self.mainRenderer.setObjectName("mainRenderer")
        self.flatRenderer = WalkmeshRenderer(parent=self.splitter)
        self.flatRenderer.setMouseTracking(True)
        self.flatRenderer.setObjectName("flatRenderer")
        self.verticalLayout_2.addWidget(self.splitter)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.instanceList = QtWidgets.QListWidget(parent=self.centralwidget)
        self.instanceList.setMaximumSize(QtCore.QSize(200, 16777215))
        self.instanceList.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.instanceList.setObjectName("instanceList")
        self.horizontalLayout.addWidget(self.instanceList)
        self.verticalLayout.addLayout(self.horizontalLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 970, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(parent=self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuHelp = QtWidgets.QMenu(parent=self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionUndo = QtGui.QAction(parent=MainWindow)
        self.actionUndo.setObjectName("actionUndo")
        self.actionRedo = QtGui.QAction(parent=MainWindow)
        self.actionRedo.setObjectName("actionRedo")
        self.actionSave = QtGui.QAction(parent=MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actiona = QtGui.QAction(parent=MainWindow)
        self.actiona.setObjectName("actiona")
        self.actionInstructions = QtGui.QAction(parent=MainWindow)
        self.actionInstructions.setObjectName("actionInstructions")
        self.actionOpen = QtGui.QAction(parent=MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionHide3DView = QtGui.QAction(parent=MainWindow)
        self.actionHide3DView.setObjectName("actionHide3DView")
        self.actionHide2DView = QtGui.QAction(parent=MainWindow)
        self.actionHide2DView.setObjectName("actionHide2DView")
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionUndo)
        self.menuFile.addAction(self.actionRedo)
        self.menuHelp.addAction(self.actionInstructions)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.lockInstancesCheck.setToolTip(_translate("MainWindow", "Lock all instances in place"))
        self.cursorCheck.setToolTip(_translate("MainWindow", "Display cursor at mouse"))
        self.backfaceCheck.setToolTip(_translate("MainWindow", "Enable backface culling"))
        self.lightmapCheck.setToolTip(_translate("MainWindow", "Enable lightmaps"))
        self.viewCreatureCheck.setToolTip(_translate("MainWindow", "Creatures"))
        self.viewDoorCheck.setToolTip(_translate("MainWindow", "Doors"))
        self.viewPlaceableCheck.setToolTip(_translate("MainWindow", "Placeables"))
        self.viewStoreCheck.setToolTip(_translate("MainWindow", "Merchants"))
        self.viewSoundCheck.setToolTip(_translate("MainWindow", "Sounds"))
        self.viewWaypointCheck.setToolTip(_translate("MainWindow", "Waypoints"))
        self.viewCameraCheck.setToolTip(_translate("MainWindow", "Cameras"))
        self.viewEncounterCheck.setToolTip(_translate("MainWindow", "Encounters"))
        self.viewTriggerCheck.setToolTip(_translate("MainWindow", "Triggers"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.actionUndo.setText(_translate("MainWindow", "Undo"))
        self.actionUndo.setShortcut(_translate("MainWindow", "Ctrl+Z"))
        self.actionRedo.setText(_translate("MainWindow", "Redo"))
        self.actionRedo.setShortcut(_translate("MainWindow", "Ctrl+Shift+Z"))
        self.actionSave.setText(_translate("MainWindow", "Save GIT"))
        self.actiona.setText(_translate("MainWindow", "Placeholdewr"))
        self.actionInstructions.setText(_translate("MainWindow", "Instructions"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionHide3DView.setText(_translate("MainWindow", "Hide 3D View"))
        self.actionHide2DView.setText(_translate("MainWindow", "Hide 2D View"))
from modulerenderer import ModuleRenderer
from walkmeshrenderer import WalkmeshRenderer

from toolset.rcc import resources_rc_pyqt6