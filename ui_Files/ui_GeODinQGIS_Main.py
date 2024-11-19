# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\OSGeo4W64\apps\qgis\python\plugins\GeODinQGIS\ui_Files\ui_GeODinQGIS_Main.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_GeODinQGISMain(object):
    def setupUi(self, GeODinQGISMain):
        GeODinQGISMain.setObjectName("GeODinQGISMain")
        GeODinQGISMain.resize(380, 636)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(GeODinQGISMain.sizePolicy().hasHeightForWidth())
        GeODinQGISMain.setSizePolicy(sizePolicy)
        GeODinQGISMain.setMinimumSize(QtCore.QSize(380, 300))
        GeODinQGISMain.setMaximumSize(QtCore.QSize(400, 1000))
        GeODinQGISMain.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.gridLayout_9 = QtWidgets.QGridLayout(self.dockWidgetContents)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(15)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.multipleImportButton = QtWidgets.QPushButton(self.dockWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.multipleImportButton.sizePolicy().hasHeightForWidth())
        self.multipleImportButton.setSizePolicy(sizePolicy)
        self.multipleImportButton.setMaximumSize(QtCore.QSize(200, 16777215))
        self.multipleImportButton.setObjectName("multipleImportButton")
        self.horizontalLayout.addWidget(self.multipleImportButton)
        self.singleImportButton = QtWidgets.QPushButton(self.dockWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.singleImportButton.sizePolicy().hasHeightForWidth())
        self.singleImportButton.setSizePolicy(sizePolicy)
        self.singleImportButton.setMaximumSize(QtCore.QSize(200, 16777215))
        self.singleImportButton.setObjectName("singleImportButton")
        self.horizontalLayout.addWidget(self.singleImportButton)
        self.gridLayout_9.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.treeWidget = QtWidgets.QTreeWidget(self.dockWidgetContents)
        self.treeWidget.setObjectName("treeWidget")
        self.horizontalLayout_2.addWidget(self.treeWidget)
        self.gridLayout_9.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)
        GeODinQGISMain.setWidget(self.dockWidgetContents)

        self.retranslateUi(GeODinQGISMain)
        QtCore.QMetaObject.connectSlotsByName(GeODinQGISMain)

    def retranslateUi(self, GeODinQGISMain):
        _translate = QtCore.QCoreApplication.translate
        GeODinQGISMain.setWindowTitle(_translate("GeODinQGISMain", "GeODin QGIS"))
        self.multipleImportButton.setText(_translate("GeODinQGISMain", "Load Database"))
        self.singleImportButton.setText(_translate("GeODinQGISMain", "Import Databases"))
        self.treeWidget.headerItem().setText(0, _translate("GeODinQGISMain", "GeODin Databases"))

