# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\OSGeo4W64\apps\qgis\python\plugins\GeODinQGIS\ui_Files\ui_GeODinQGIS_SelectCoords.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SelectCoords(object):
    def setupUi(self, SelectCoords):
        SelectCoords.setObjectName("SelectCoords")
        SelectCoords.setWindowModality(QtCore.Qt.ApplicationModal)
        SelectCoords.resize(400, 300)
        self.buttonBox = QtWidgets.QDialogButtonBox(SelectCoords)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.lbl_xcol = QtWidgets.QLabel(SelectCoords)
        self.lbl_xcol.setGeometry(QtCore.QRect(50, 30, 60, 13))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.lbl_xcol.setFont(font)
        self.lbl_xcol.setObjectName("lbl_xcol")
        self.lbl_ycol = QtWidgets.QLabel(SelectCoords)
        self.lbl_ycol.setGeometry(QtCore.QRect(50, 70, 60, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.lbl_ycol.setFont(font)
        self.lbl_ycol.setObjectName("lbl_ycol")
        self.cmb_xcol = QtWidgets.QComboBox(SelectCoords)
        self.cmb_xcol.setGeometry(QtCore.QRect(120, 30, 141, 22))
        self.cmb_xcol.setObjectName("cmb_xcol")
        self.cmb_ycol = QtWidgets.QComboBox(SelectCoords)
        self.cmb_ycol.setGeometry(QtCore.QRect(120, 70, 141, 22))
        self.cmb_ycol.setObjectName("cmb_ycol")

        self.retranslateUi(SelectCoords)
        self.buttonBox.accepted.connect(SelectCoords.accept)
        self.buttonBox.rejected.connect(SelectCoords.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectCoords)

    def retranslateUi(self, SelectCoords):
        _translate = QtCore.QCoreApplication.translate
        SelectCoords.setWindowTitle(_translate("SelectCoords", "Dialog"))
        self.lbl_xcol.setText(_translate("SelectCoords", "X column:"))
        self.lbl_ycol.setText(_translate("SelectCoords", "Y column:"))

