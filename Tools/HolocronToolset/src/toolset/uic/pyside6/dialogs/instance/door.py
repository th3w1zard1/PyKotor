# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'door.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit
from toolset.gui.widgets.long_spinbox import LongSpinBox

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(374, 290)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.resrefEdit = QLineEdit(Dialog)
        self.resrefEdit.setObjectName(u"resrefEdit")
        self.resrefEdit.setMaximumSize(QSize(187, 16777215))
        self.resrefEdit.setMaxLength(16)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.resrefEdit)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.xPosSpin = QDoubleSpinBox(Dialog)
        self.xPosSpin.setObjectName(u"xPosSpin")
        self.xPosSpin.setMaximumSize(QSize(90, 16777215))
        self.xPosSpin.setWrapping(True)
        self.xPosSpin.setDecimals(6)
        self.xPosSpin.setMinimum(-1000000.000000000000000)
        self.xPosSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout.addWidget(self.xPosSpin)

        self.yPosSpin = QDoubleSpinBox(Dialog)
        self.yPosSpin.setObjectName(u"yPosSpin")
        self.yPosSpin.setMaximumSize(QSize(90, 16777215))
        self.yPosSpin.setWrapping(True)
        self.yPosSpin.setDecimals(6)
        self.yPosSpin.setMinimum(-1000000.000000000000000)
        self.yPosSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout.addWidget(self.yPosSpin)

        self.zPosSpin = QDoubleSpinBox(Dialog)
        self.zPosSpin.setObjectName(u"zPosSpin")
        self.zPosSpin.setMaximumSize(QSize(90, 16777215))
        self.zPosSpin.setWrapping(True)
        self.zPosSpin.setDecimals(6)
        self.zPosSpin.setMinimum(-1000000.000000000000000)
        self.zPosSpin.setMaximum(1000000.000000000000000)

        self.horizontalLayout.addWidget(self.zPosSpin)


        self.formLayout.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout)

        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_3)

        self.bearingSpin = QDoubleSpinBox(Dialog)
        self.bearingSpin.setObjectName(u"bearingSpin")
        self.bearingSpin.setMaximumSize(QSize(90, 16777215))
        self.bearingSpin.setDecimals(6)
        self.bearingSpin.setMinimum(-1000000.000000000000000)
        self.bearingSpin.setMaximum(1000000.000000000000000)

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.bearingSpin)

        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_4)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.color = QLabel(Dialog)
        self.color.setObjectName(u"color")
        self.color.setMinimumSize(QSize(16, 16))
        self.color.setMaximumSize(QSize(16, 16))
        self.color.setStyleSheet(u"background: black;")

        self.horizontalLayout_9.addWidget(self.color)

        self.colorSpin = LongSpinBox(Dialog)
        self.colorSpin.setObjectName(u"colorSpin")
        self.colorSpin.setMinimumSize(QSize(90, 0))
        self.colorSpin.setMaximumSize(QSize(90, 16777215))

        self.horizontalLayout_9.addWidget(self.colorSpin)

        self.colorButton = QPushButton(Dialog)
        self.colorButton.setObjectName(u"colorButton")
        self.colorButton.setMaximumSize(QSize(24, 20))

        self.horizontalLayout_9.addWidget(self.colorButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer)


        self.formLayout.setLayout(4, QFormLayout.FieldRole, self.horizontalLayout_9)

        self.label_8 = QLabel(Dialog)
        self.label_8.setObjectName(u"label_8")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_8)

        self.tagEdit = QLineEdit(Dialog)
        self.tagEdit.setObjectName(u"tagEdit")
        self.tagEdit.setMaximumSize(QSize(187, 16777215))

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.tagEdit)


        self.verticalLayout.addLayout(self.formLayout)

        self.line = QFrame(Dialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.noTransCheck = QRadioButton(Dialog)
        self.noTransCheck.setObjectName(u"noTransCheck")

        self.horizontalLayout_2.addWidget(self.noTransCheck)

        self.toDoorCheck = QRadioButton(Dialog)
        self.toDoorCheck.setObjectName(u"toDoorCheck")

        self.horizontalLayout_2.addWidget(self.toDoorCheck)

        self.toWaypointCheck = QRadioButton(Dialog)
        self.toWaypointCheck.setObjectName(u"toWaypointCheck")

        self.horizontalLayout_2.addWidget(self.toWaypointCheck)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_5 = QLabel(Dialog)
        self.label_5.setObjectName(u"label_5")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_5)

        self.linkToModuleEdit = QLineEdit(Dialog)
        self.linkToModuleEdit.setObjectName(u"linkToModuleEdit")
        self.linkToModuleEdit.setMaximumSize(QSize(187, 16777215))
        self.linkToModuleEdit.setMaxLength(16)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.linkToModuleEdit)

        self.label_6 = QLabel(Dialog)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_6)

        self.linkToTagEdit = QLineEdit(Dialog)
        self.linkToTagEdit.setObjectName(u"linkToTagEdit")
        self.linkToTagEdit.setMaximumSize(QSize(187, 16777215))

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.linkToTagEdit)

        self.label_7 = QLabel(Dialog)
        self.label_7.setObjectName(u"label_7")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_7)

        self.transNameEdit = LocalizedStringLineEdit(Dialog)
        self.transNameEdit.setObjectName(u"transNameEdit")
        self.transNameEdit.setMinimumSize(QSize(219, 23))
        self.transNameEdit.setMaximumSize(QSize(219, 16777215))

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.transNameEdit)


        self.verticalLayout.addLayout(self.formLayout_2)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Edit Door", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"ResRef:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Position:", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Bearing:", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Tweak Color:", None))
        self.color.setText("")
        self.colorButton.setText(QCoreApplication.translate("Dialog", u"...", None))
        self.label_8.setText(QCoreApplication.translate("Dialog", u"Tag:", None))
        self.noTransCheck.setText(QCoreApplication.translate("Dialog", u"No Transition", None))
        self.toDoorCheck.setText(QCoreApplication.translate("Dialog", u"Links to Door", None))
        self.toWaypointCheck.setText(QCoreApplication.translate("Dialog", u"Links to Waypoint", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"Link To Module:", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"Link To Tag:", None))
        self.label_7.setText(QCoreApplication.translate("Dialog", u"Transition Name:", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
