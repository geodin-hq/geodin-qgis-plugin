# -*- coding: utf-8 -*-
"""
/***************************************************************************
GeODinQGIS
                             A QGIS plugin
This plugin connects GeODin with QGIS
                          -------------------
    begin                : 2015-02-16
    git sha              : $Format:%H$
    copyright            : (C) 2021 by Fugro Germany Land GmbH
    email                : www.fugro.com
***************************************************************************/

/***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************/
"""
# EbJo clean code - Python 3 (keine Kompatibilität zu/Unterstützung von Python 2 also QGIS 2)
##from __future__ import print_function
##from __future__ import absolute_import
##from builtins import str
##from builtins import range
##from builtins import object
# Python imports
import logging
import os.path
from pathlib import Path
import sys

# QGIS imports
from qgis.PyQt.QtCore import QObject, Qt
from qgis.PyQt.QtWidgets import QDialog, QAction, QMenu, QToolButton, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import *
from qgis.gui import *
from win32api import GetSystemMetrics


from GeODinQGIS.resources_rc import *


# GeODinQGIS imports...
from GeODinQGIS import res
import GeODinQGIS.ui as ui

from .GeODinQGIS_Main import GeODinQGISMain
##from .GeODinQGIS_Settings import Settings
from .ui_Files.ui_GeODinQGIS_Help import Ui_HelpDialog
from .pythonmodules.helpFunction import Database, Project, Object
from .extras.layout import ImageLayout


def my_processor(path):
    return path.replace('$GeODinPy$', 'C:/Data/Repos/GeODinQGIS')

QgsPathResolver.setPathPreprocessor(my_processor)

class GeODinQGIS:

    def __init__(self, iface):
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("")
        # Save reference to the QGIS interface
        self.iface = iface
        # locate main function in "GeODinQGIS_Main"
        self.main = GeODinQGISMain(iface)
        if self.main.error:
            return

        #initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # create language and dictionary
        self.language = self.main.lang
        self.dictionary = self.main.dictionary

        self._connect()
        self._disconnect()

    def initGui(self):
        self.log.debug("")
        if self.main.error:
            return
        parent = self.iface.mainWindow()
        # Create actionmain that will start plugin configuration
        self.actionmain = QAction(QIcon(":/plugins/GeODinQGIS/icons/logo.png"), u"GeODin", self.iface.mainWindow())

        # connect the actionmain to the run method
        self.actionmain.triggered.connect(self.openMain)

        # Add Plugin to toolbar
        self.toolBar = self.iface.addToolBar("GeODin")
        self.toolBar.addAction(self.actionmain)

        self.toolBar.addAction(ui.GQgis_Act_DDX(parent))
        self.toolBar.addAction(ui.GQgis_Act_Connect(parent, None))
        self.toolBar.addAction(ui.GQgis_Act_Refresh(parent, self.refresh))
        self.toolBar.addWidget(ui.GQgis_TBtn_Help(parent))
        self.toolBar.addAction(ui.GQgis_Act_MsgBox(parent, None))

    def unload(self):
        # unload plugin
        if not self.main.error:
            # Remove the buttons
            self.iface.removeToolBarIcon(self.actionmain)

            # remove tool bar
            del self.toolBar

        self.main = None

        self.plugin_dir = None
        self.language = None

    def _connect(self):
        """connects functions/receiver to QGIS signals

        15.09.2022 J.Ebert
        """
        self.log.debug("")
        # QgisInterface signals
        #   https://qgis.org/pyqgis/3.28/gui/QgisInterface.html#qgis.gui.QgisInterface
        self.iface.initializationCompleted.connect(self.onInitializationCompleted)
        self.iface.projectRead.connect(self.onProjectRead)
        self.iface.newProjectCreated.connect(self.onNewProjectCreated)
        # QgsProject signals
        #   https://qgis.org/pyqgis/3.28/core/QgsProject.html#qgis.core.QgsProject
        QgsProject.instance().cleared.connect(self.onCleared)
        QgsProject.instance().readProject.connect(self.onReadProject)
        QgsProject.instance().writeProject.connect(self.onWriteProject)

    def _disconnect(self):
        """disconnects functions/receiver to QGIS signals

        15.09.2022 J.Ebert
        """
        self.log.debug("")
        QgsProject.instance().readProject.disconnect(self.onReadProject)

    def onInitializationCompleted(self):
        """event function/receiver is triggered when a QGIS interface ...

        15.09.2022 J.Ebert
        """
        self.log.debug("")

    def onProjectRead(self):
        """event function/receiver is triggered when a QGIS interface ...

        15.09.2022 J.Ebert
        """
        self.log.debug("")
        self._logProjectAttr()

    def onNewProjectCreated(self):
        """event function/receiver is triggered when a QGIS interface ...

        15.09.2022 J.Ebert
        """
        self.log.debug("")
        self._logProjectAttr()

    def onCleared(self):
        """event function/receiver is triggered when a QGIS project is loaded

        15.09.2022 J.Ebert
        """
        self.log.debug("")
        self._logProjectAttr()

    def onReadProject(self):
        """event function/receiver is triggered when a QGIS project is loaded

        15.09.2022 J.Ebert
        """
        self.log.debug("")
        self._logProjectAttr()

    def onWriteProject(self):
        """event function/receiver is triggered when a QGIS project is writen/saved

        15.09.2022 J.Ebert
        """
        self.log.debug("")

    def _logProjectAttr(self):
        proj = QgsProject.instance()
        self.log.debug(f"""
        fileName            {proj.fileName()}
        absoluteFilePath    {proj.absoluteFilePath()}
        absolutePath        {proj.absolutePath()}
        """)

    def openMain(self):
        # show main functions in a right docked widget
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.main)
        #self.main.getBuild()
        self.main.checkVersion()


    def refresh(self):
        #Warning message box with two buttons
        msgBox = QMessageBox()
        msgBox.setInformativeText(self.main.dictionary.getWord(self.main.lang,"Do you want to accept the changes and discard all layer informations?"))
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Cancel)
        msgBox.setWindowTitle('Warning')
        canvas = self.iface.mapCanvas()
        allLayers = canvas.layers()

        for layerid, layer in enumerate(allLayers):
            databases = []
            try:
                for feature in layer.getFeatures():
                    database = Database(feature["database"]+str(layerid), feature["database"])
                    database.options["connection"] = feature["dbtype"]
                    if not database in databases:
                        databases.append(database)
                    else:

                        database = databases[databases.index(database)]
                    project = Project(feature["prjname"], database)
                    project.id = feature["prjid"]
                    if not project in database.projects:
                        database.projects.append(project)
                    else:
                        project = database.projects[database.projects.index(project)]

                    object = Object(feature["longname"], project)
                    object.shortname = feature["shortname"]
                    object.locname = feature["objecttype"]
                    object.invid = feature["invid"]
                    object.coordinates = (feature["xcoord"], feature["ycoord"])
                    object.data = []
                    for i in range(10, len(feature.attributes())):
                        object.data.append(feature.attributes()[i])
                    project.objects.append(object)
            except Exception as e :
                # fix_print_with_import
                print(str(e))

            changes = False
            features = []
            for database in databases:
                # fix_print_with_import
                print (database.options)
                for project in database.projects:
                    query = """SELECT GEODIN_LOC_LOCREG.INVID, GEODIN_LOC_LOCREG.SHORTNAME, GEODIN_LOC_LOCREG.LONGNAME, GEODIN_LOC_LOCREG.XCOORD, GEODIN_LOC_LOCREG.YCOORD, GEODIN_SYS_LOCTYPES.Gen_name
                                FROM GEODIN_LOC_LOCREG INNER JOIN GEODIN_SYS_LOCTYPES ON GEODIN_LOC_LOCREG.LOCTYPE = GEODIN_SYS_LOCTYPES.GEN_DESC
                                WHERE GEODIN_LOC_LOCREG.PRJ_ID = '{0}';""".format(project.id)

                    result = self.main.connectToDatabase(database, query)

                    for row in result:
                        #get the data from database and check if something has changed
                        if project.getObject(row[0]):
                            object = project.getObject(row[0])
                            if row[1] != object.shortname or row[2] != object.name or row[3] != object.coordinates[0] or row[4] != object.coordinates[1] or row[5] != object.locname:
                                changes = True
                        else:
                            changes = True
                        feat = QgsFeature()
                        feat.setGeometry(QgsGeometry.fromPoint(QgsPoint(row[3], row[4])))
                        attributes = [row[0], row[1], row[2], row[3], row[4], database.options["connection"], database.filepath, project.name, project.id, row[5]]
                        attributes += object.data
                        feat.setAttributes(attributes)
                        features.append(feat)
            if changes:
                #if something has changed, open message box and ask for changing
                msgBox.setText(layer.name().split('_')[0]+self.main.dictionary.getWord(self.main.lang," has been modified."))
                if msgBox.exec_() == 1024:
                    provider = layer.dataProvider()
                    provider.deleteFeatures([f.id() for f in layer.getFeatures()])
                    provider.addFeatures(features)
                    layer.commitChanges()
        canvas.refresh()

    def changeLanguage(self, lan):
        # Version 2 - Aufruf nach Ändern der Sprache, aber
        #   - Button bereits migriert
        #   - Funktion wird also nicht mehr aufgerufen
        #   - nur zur Migration von main und dem refreshButton
        self.main.changeLang(lan)
        self.language = lan
        # EbJo clean code - UI-Elemente der Version 2 bereits migriert
##        self.refreshButton.setToolTip(self.dictionary.getWord(self.language,"Refresh"))
##        self.preferenceButton.setToolTip(self.dictionary.getWord(self.language,"Settings"))
##        self.languageMenu.setIcon(self.main.activeIcon)
##        self.languageMenu.setTitle(self.dictionary.getWord(self.language,"Language"))
##        self.settingsButton.setText(self.dictionary.getWord(self.language,"Settings"))
##        self.helpButton.setToolTip(self.dictionary.getWord(self.language,"GeODinQGIS Help"))


