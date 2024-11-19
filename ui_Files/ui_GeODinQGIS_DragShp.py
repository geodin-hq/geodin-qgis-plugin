# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\OSGeo4W64\apps\qgis\python\plugins\GeODinQGIS\ui_Files\ui_GeODinQGIS_DragShp.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DragShape(object):
    def setupUi(self, DragShape):
        DragShape.setObjectName("DragShape")
        DragShape.setWindowModality(QtCore.Qt.ApplicationModal)
        DragShape.resize(620, 435)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DragShape.sizePolicy().hasHeightForWidth())
        DragShape.setSizePolicy(sizePolicy)
        DragShape.setMaximumSize(QtCore.QSize(620, 16777215))
        self.verticalLayout = QtWidgets.QVBoxLayout(DragShape)
        self.verticalLayout.setObjectName("verticalLayout")
        self.shape_tab = QtWidgets.QTableWidget(DragShape)
        self.shape_tab.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.shape_tab.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.shape_tab.setColumnCount(2)
        self.shape_tab.setObjectName("shape_tab")
        self.shape_tab.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.shape_tab.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.shape_tab.setHorizontalHeaderItem(1, item)
        self.shape_tab.horizontalHeader().setDefaultSectionSize(300)
        self.verticalLayout.addWidget(self.shape_tab)
        self.buttonBox = QtWidgets.QDialogButtonBox(DragShape)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(DragShape)
        self.buttonBox.accepted.connect(DragShape.accept)
        self.buttonBox.rejected.connect(DragShape.reject)
        QtCore.QMetaObject.connectSlotsByName(DragShape)

    def retranslateUi(self, DragShape):
        _translate = QtCore.QCoreApplication.translate
        DragShape.setWindowTitle(_translate("DragShape", "Dialog"))
        item = self.shape_tab.horizontalHeaderItem(0)
        item.setText(_translate("DragShape", "Name"))
        item = self.shape_tab.horizontalHeaderItem(1)
        item.setText(_translate("DragShape", "Filepath"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    DragShape = QtWidgets.QDialog()
    ui = Ui_DragShape()
    ui.setupUi(DragShape)
    DragShape.show()
    sys.exit(app.exec_())

