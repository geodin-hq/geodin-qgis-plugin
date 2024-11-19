# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\OSGeo4W64\apps\qgis\python\plugins\GeODinQGIS\ui_Files\ui_GeODinQGIS_Info.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_InfoDialog(object):
    def setupUi(self, InfoDialog):
        InfoDialog.setObjectName("InfoDialog")
        InfoDialog.resize(379, 272)
        self.gridLayoutWidget = QtWidgets.QWidget(InfoDialog)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(80, 100, 297, 80))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.lbl_from = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lbl_from.setObjectName("lbl_from")
        self.gridLayout.addWidget(self.lbl_from, 0, 2, 1, 1)
        self.lbl_date = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lbl_date.setObjectName("lbl_date")
        self.gridLayout.addWidget(self.lbl_date, 0, 3, 1, 1)
        self.lbl_build = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lbl_build.setObjectName("lbl_build")
        self.gridLayout.addWidget(self.lbl_build, 0, 0, 1, 1)
        self.lbl_buildnumb = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lbl_buildnumb.setObjectName("lbl_buildnumb")
        self.gridLayout.addWidget(self.lbl_buildnumb, 1, 2, 1, 1)
        self.lbl_build_2 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lbl_build_2.setObjectName("lbl_build_2")
        self.gridLayout.addWidget(self.lbl_build_2, 0, 1, 1, 1)
        self.label = QtWidgets.QLabel(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 1, 1, 1)
        self.lbl_buildnumb_2 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lbl_buildnumb_2.setObjectName("lbl_buildnumb_2")
        self.gridLayout.addWidget(self.lbl_buildnumb_2, 2, 0, 1, 1)

        self.retranslateUi(InfoDialog)
        QtCore.QMetaObject.connectSlotsByName(InfoDialog)

    def retranslateUi(self, InfoDialog):
        _translate = QtCore.QCoreApplication.translate
        InfoDialog.setWindowTitle(_translate("InfoDialog", "GeODin QGIS Info"))
        self.lbl_from.setText(_translate("InfoDialog", "from:"))
        self.lbl_date.setText(_translate("InfoDialog", "1234"))
        self.lbl_build.setText(_translate("InfoDialog", "Build number:"))
        self.lbl_buildnumb.setText(_translate("InfoDialog", "1234"))
        self.lbl_build_2.setText(_translate("InfoDialog", "Build number:"))
        self.label.setText(_translate("InfoDialog", "GeODin QGIS 1.0"))
        self.label_2.setText(_translate("InfoDialog", "GeODin QGIS 1.0"))
        self.lbl_buildnumb_2.setText(_translate("InfoDialog", "1234"))

