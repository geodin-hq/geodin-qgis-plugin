# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\OSGeo4W64\apps\qgis\python\plugins\GeODinQGIS\ui_Files\ui_GeODinQGIS_Help.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_HelpDialog(object):
    def setupUi(self, HelpDialog):
        HelpDialog.setObjectName("HelpDialog")
        HelpDialog.resize(1200, 800)
        self.horizontalLayout = QtWidgets.QHBoxLayout(HelpDialog)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.webView = QtWebKitWidgets.QWebView(HelpDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.webView.sizePolicy().hasHeightForWidth())
        self.webView.setSizePolicy(sizePolicy)
        self.webView.setMinimumSize(QtCore.QSize(750, 300))
        self.webView.setObjectName("webView")
        self.horizontalLayout.addWidget(self.webView)

        self.retranslateUi(HelpDialog)
        QtCore.QMetaObject.connectSlotsByName(HelpDialog)

    def retranslateUi(self, HelpDialog):
        _translate = QtCore.QCoreApplication.translate
        HelpDialog.setWindowTitle(_translate("HelpDialog", "GeODin QGIS Help"))

from PyQt5 import QtWebKitWidgets
