# Form implementation generated from reading ui file '..\ui\widgets\renderer\lyt_editor.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_LYTEditor(object):
    def setupUi(self, LYTEditor):
        LYTEditor.setObjectName("LYTEditor")
        LYTEditor.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(LYTEditor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.graphicsView = QtWidgets.QGraphicsView(parent=LYTEditor)
        self.graphicsView.setObjectName("graphicsView")
        self.verticalLayout.addWidget(self.graphicsView)

        self.retranslateUi(LYTEditor)
        QtCore.QMetaObject.connectSlotsByName(LYTEditor)

    def retranslateUi(self, LYTEditor):
        _translate = QtCore.QCoreApplication.translate
        LYTEditor.setWindowTitle(_translate("LYTEditor", "LYT Editor"))

from toolset.rcc import resources_rc_pyqt6