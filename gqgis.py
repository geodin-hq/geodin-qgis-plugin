"""
Classes:
    GQgis               - QGIS Plugin object
    GQgis_App           - central GeODinQGIS object (Singleton!)

08.09.2022 J.Ebert
"""
import logging
import os
import struct
import time
from pathlib import Path
from qgis.core import (
    QgsProject
)
from qgis.PyQt import (
    QtCore,
    QtWidgets
    )

from GeODinQGIS.resources_rc import *
from GeODinQGIS.gqgis_app import GQgis_App
from GeODinQGIS import env
import GeODinQGIS.gx as gx
import GeODinQGIS.ui as ui
import GeODinQGIS.gqgis_config as gqc

class GQgis:

    def __init__(self, iface):
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.log(gqc._LOG_TRACE,"")
        # save reference to the GeODinQGIS app (singleton!)
        self._app = GQgis_App()
        # save reference to the QGIS interface
        self._iface = iface
        # initialize GeODinQGIS project Settings
        self._resetProjSettings()
        # connect functions/receiver to QGIS signals
        self._connect()

    def initGui(self):
        self.log.log(gqc._LOG_TRACE,"")
        # Add Plugin to toolbar
        self.toolBar = self.iface().addToolBar("GeODin")
        self.toolBar.addWidget(ui.GQgis_TBtn_Help(self.parent()))
        self.toolBar.addAction(ui.GQgis_Act_DDX(self.parent()))
        self.toolBar.addSeparator()
        self.toolBar.addAction(ui.GQgis_Act_Connect(self.parent(), None))
        self.toolBar.addAction(ui.GQgis_Frm_GCat.showAction(self.parent()))
        # 08/2023 j.ebert, Anmerkung
        #   Aktion zum Aktualisieren der Abfragen aller Datenbanken noch nicht implementiert!
        #   Menu-Aktionen sind nur aktiv, wenn Abfragen zum Aktualisieren auch existieren.
        #   Wie wird die Aktion Synchronisiert bzgl. der Abfragen zum Aktualisieren?!
        #   Achtung, nur geöffnete Datenbanken berücksichtigen!
##        self.toolBar.addAction(ui.GQgis_Act_Refresh(self.parent(), None))
        self.toolBar.addSeparator()
        cboLayers = ui.GQgis_Cbo_Layers.instance(self.parent)
        self.toolBar.addAction(ui.GQgis_Act_LayersReload(self.parent(), cboLayers.reloadGoLayers))
        self.toolBar.addWidget(cboLayers)
        self.toolBar.addAction(ui.GQgis_Act_ToolSelection(self.parent(), None))
        self.toolBar.addAction(ui.GQgis_Act_ToolHotlink(self.parent(), None))
##        self.toolBar.addAction(ui.GQgis_Act_Pan(self.parent(), None))
##        self.toolBar.addAction(ui.GQgis_Act_MsgBox(self.parent(), None))
        self.updateGui()

    def updateGui(self):
        self.log.log(gqc._LOG_TRACE,"")
        # ToolButton der ToolBar aktualisieren
        # 02.05.2023 j.ebert, Anmerkung
        #   QAction der GUI werden über ObjectName gefunden, aber haben kein Attr. Enabled.
        #   Alle QToolButton der ToolBar analysieren und deren QAction analysieren/auswerten.
        for btn in self.toolBar.findChildren(
            QtWidgets.QToolButton, '', QtCore.Qt.FindDirectChildrenOnly
        ):
            acts = [act for act in btn.actions() if act.objectName().startswith('GQgis')]
            if (
                bool(acts) and
                hasattr(acts[0], 'updateUi')
            ):
                acts[0].updateUi(btn)

    def unload(self):
        # unload plugin
        self.log.log(gqc._LOG_TRACE,"")
        # reset TmpFolder
        env._TmpFolder = None
        # disconnect functions/receiver to QGIS signals
        self._disconnect()
        # remove tool bar
        del self.toolBar

    def iface(self):
        """QGIS Interface
        returns:
            iface (qgis.gui.QgisInterface)

        24.05.2023 j.ebert
        """
        return self._iface

    def parent(self):
        return self._iface.mainWindow()


    def proj(self):
        """QGIS project

        17.05.2023 j.ebert
        """
        return QgsProject.instance()

    def projScope(self):
        """GeODinQGIS scope for QGIS project settings

        notes:
            scope is used
                QgsProject.instance().entryList(self.projScope(),'')
                QgsProject.instance().readNumEntry(self.projScope(), key: str, def_: int = 0)
                QgsProject.instance().writeEntry(self.projScope(), key: str, value: int)
            and so on

        17.05.2023 j.ebert
        """
        return 'GeODinQGIS'

    def projSettings(self):
        """GeODinQGIS project settings (dict)

        17.05.2023 j.ebert
        """
        return self._projSettings

    def _resetProjSettings(self):
        """resets GeODinQGIS project settings (dict)

        17.05.2023 j.ebert
        """
        self._projSettings = {
            "version": "",
            "ddxFile": "",
            "updUser": "",
            "updDate": ""        }
        return self._projSettings

    def _relpath(
        self,
        path
    ):
        """return a relativ version of path to QGIS-Project-File directory

        17.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        assert  isinstance(path, (str, Path)), \
            "Argument 'path' is not type 'str' or 'Path'"
        relpath = str(path)
        if (
            bool(path) and
            bool(self.proj().absolutePath()) and
            Path(path).is_relative_to(Path(self.proj().absolutePath()).anchor)
        ):
            relpath = os.path.relpath(path, self.proj().absolutePath())
        self.log.debug(f"""
    absoluteFilePath:   {self.proj().absoluteFilePath()}
    absolutePath:       {self.proj().absolutePath()}
    path:               {str(path)}
    relpath             {str(relpath)}
        """)
        return relpath

    def _abspath(
        self,
        path
    ):
        """return a absolute version of path to QGIS-Project-File directory

        17.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        assert isinstance(path, (str, Path)), \
            "Argument 'path' is not type 'str' or 'Path'"
        abspath = str(path)
        if (
            bool(path) and
            bool(self.proj().absolutePath()) and
            (not Path(path).is_absolute())
        ):
            abspath = str(Path(self.proj().absolutePath()).joinpath(path).resolve())
        self.log.debug(f"""
    absoluteFilePath:   {self.proj().absoluteFilePath()}
    absolutePath:       {self.proj().absolutePath()}
    path:               {str(path)}
    abspath:            {str(abspath)}
        """)
        return abspath


    def _connect(self):
        """connects functions/receiver to QGIS signals

        15.09.2022 J.Ebert
        """
        self.log.debug("")
        # QgisInterface signals
        #   https://qgis.org/pyqgis/3.28/gui/QgisInterface.html#qgis.gui.QgisInterface
        # - Signal 'initializationCompleted' nicht nutzbar
        #   04/2023 j.ebert, Anmerkung
        #       Das Signal 'initializationCompleted' wird nur beim Starten von QGIS gesendet.
        #       Es gibt aber zwei Szenario für das Starten de Plugins
        #       - Das Plugin ist bereits aktiviert und zusammen mit QGIS gestratet,
        #         dann wird dieses Signal gesendet und es kann darauf reagiert werden
        #       - Das Plugin ist noch nicht aktiviert und wird erst später aktiviert/gestartet,
        #         dann wird dieses Signal nicht mehr gesendet
##        self.iface().initializationCompleted.connect(self.onInitializationCompleted)
        # - Signal 'projectRead' ???
        #   05/2023 j.ebert, wird nach QgsProject.readProject ausgeführt?!
        #   self.iface().projectRead.connect(self.onProjectRead)
        # - Signal 'newProjectCreated'
        #   04/2023 j.ebert, Anmerkung
        #       Das Signal wird gesendet beim
        #       - beim Erstellen eines neuen Projektes und
        #       - beim Starten von QGIS (also nicht nach Doppel-klick auf eine QGIS-Projekt-Datei)
        self.iface().newProjectCreated.connect(self.onNewProjectCreated)
        # QgsProject signals
        #   https://qgis.org/pyqgis/3.28/core/QgsProject.html#qgis.core.QgsProject
        # - Signal 'cleared'
        #   04/2023 j.ebert, Anmerkung
        #       Das Signal wird immer zwei mal gesendet?!
        #       Das Signal wird auch beim beim Starten von QGIS ohne Projekt gesendet.
        QgsProject.instance().cleared.connect(self.onCleared)
        QgsProject.instance().readProject.connect(self.onReadProject)
        QgsProject.instance().writeProject.connect(self.onWriteProject)

    def _disconnect(self):
        """disconnects functions/receiver to QGIS signals

        15.09.2022 J.Ebert
        """
        self.log.debug("")
        # QgisInterface signals
        self.iface().newProjectCreated.disconnect(self.onNewProjectCreated)
        # QgsProject signals
        QgsProject.instance().cleared.disconnect(self.onCleared)
        QgsProject.instance().readProject.disconnect(self.onReadProject)
        QgsProject.instance().writeProject.disconnect(self.onWriteProject)

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
        self.log.log(gqc._LOG_TRACE,"")
        self._logProjectAttr()
        # GeODinQGIS project settings zurücksetzen...
        self._resetProjSettings()
        # DDX-File der QGIS-App zurücksetzen
        self._app.updateDDXFile("")

    def onCleared(self):
        """event function/receiver is triggered when a QGIS project is loaded

        15.09.2022 J.Ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        self._logProjectAttr()
        # GeODinQGIS project settings zurücksetzen...
        self._resetProjSettings()
        # DDX-File der QGIS-App zurücksetzen
        self._app.updateDDXFile("")

    def onReadProject(self):
        """event function/receiver is triggered when a QGIS project is loaded

        17.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        self._logProjectAttr()
        # GeODinQGIS project settings zurücksetzen...
        self._resetProjSettings()
        # GeODinQGIS project settings laden...
        qgsProj = self.proj()
        if qgsProj.entryList(self.projScope(),''):
            # 05/2023 j.ebert, Anmerkung
            #   Derzeit sind alle Einträge vom Typ str und daher können auch alle Einträge
            #   mit der selben Methode QgsProject.readEntry() gelesen/geladen werden.
            self.log.debug(
                "QGIS project: %s\n\tQGIS project settings:\n\t\t%s",
                self.proj().absoluteFilePath(),
                "\n\t\t".join([
                    "%s/%s: %s" % (
                        self.projScope(), key, qgsProj.readEntry(self.projScope(), key, "")[0]
                    ) for key in qgsProj.entryList(self.projScope(),'')
                ])
            )
            for key in ['ddxFile', 'version', 'updUser', 'updDate', 'insUser', 'insDate']:
                self.projSettings()[key] = qgsProj.readEntry(self.projScope(), key, "")[0]
            self.log.info(
                "QGIS project: %s\n\tGeODinQGIS settings:\n\t\t%s",
                self.proj().absoluteFilePath(),
                "\n\t\t".join(["%s: %s" % item for item in self.projSettings().items()])
            )
        # DDX-File der QGIS-App setzen (und vorher ggf. prüfen?!)
        self._app.updateDDXFile(self._abspath(self.projSettings().get('ddxFile', "")))

    def onWriteProject(self):
        """event function/receiver is triggered when a QGIS project is writen/saved

        15.09.2022 J.Ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        ddxFile = ""
        if self._app.DDXFile:
            ddxFile = self._relpath(self._app.DDXFile)
        # GeODinQGIS project settings speichern...
        qgsProj = self.proj()
        if not ddxFile:
            # Wenn das DDX-File nicht gesetzt ist (bzw. zurückgesetzt wurde),
            # dann wird mit diesem QGIS Projekt das GeODinQGIS Plugin nicht genutzt und
            # dann alle GeODinQGIS-Entries vom QGIS Projekt löschen...
            # - projSettings zurücksetzen
            self._resetProjSettings()
            # - GeODinQGIS-Entries vom QGIS Projekt löschen...
            #   05/2023 j.ebert, analysiert/probiert mit QGIS 3.22.9-Białowieża
            #       qgsProj.writeEntry('GeODinQGIS','DDX','ddxFile')    -> True
            #       qgsProj.readEntry('GeODinQGIS','DDX')               -> ('ddxFile', True)
            #       qgsProj.entryList('GeODinQGIS','DDX')               -> []
            #       qgsProj.entryList('GeODinQGIS','')                  -> ['DDX']
            #       qgsProj.removeEntry('GeODinQGIS','DDX')             -> True
            #       qgsProj.readEntry('GeODinQGIS','DDX')               -> ('', False)
            #       qgsProj.readEntry('GeODinQGIS','DDX','defaultStr')  -> ('defaultStr', False)
            #       qgsProj.entryList('GeODinQGIS','DDX')               -> []
            #       qgsProj.entryList('GeODinQGIS','')                  -> []
            self.log.debug("GeODinQGIS-Entries are removed from QGIS project")
            for key in qgsProj.entryList(self.projScope(),''):
                qgsProj.removeEntry(self.projScope(), key)
        elif self.projSettings().get('ddxFile',"").lower() != ddxFile.lower():
            # Wenn das DDX-File gesetzt ist und
            # wenn GeODinQGIS project settings geändert wurden,
            # dann GeODinQGIS-Entries vom QGIS Projekt aktualisieren
            # - projSettings aktualisieren
            self.projSettings()['ddxFile'] = ddxFile
            self.projSettings()['version'] = self._app.Version
            # - - Update User/Date immer aktualisieren
            self.projSettings()['updUser'] = os.getlogin()
            self.projSettings()['updDate'] = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
            # - - Insert User/Date nur aktualisieren, wenn sie nicht gesetzt sind/nicht geladen wurden
            self.projSettings().setdefault('insUser', self.projSettings()['updUser'])
            self.projSettings().setdefault('insDate', self.projSettings()['updDate'])
            # - GeODinQGIS-Entries vom QGIS Projekt aktualisieren...
            self.log.debug("GeODinQGIS-Entries are updated in QGIS project")
            for key, val in self.projSettings().items():
                qgsProj.writeEntry(self.projScope(), key, val)
            # - alte/nicht mehr unterstützte GeODinQGIS-Entries vom QGIS Projekt löschen...
            prjKeys = self.projSettings().keys()
            oldKeys = [key for key in qgsProj.entryList(self.projScope(),'') if key not in prjKeys]
            if oldKeys:
                self.log.warning(
                    "Obsolate GeODinQGIS-Entries are removed from QGIS project \n\t\t%s",
                    "\n\t".join(["%s\\%s" % (self.projScope(), key) for key in oldKeys])
                )
                for key in oldKeys:
                    qgsProj.removeEntry(self.projScope(), oldKey)
        else:
            # Wenn das DDX-File gesetzt ist und
            # wenn keine GeODinQGIS project settings geändert wurden,
            # dann GeODinQGIS-Entries vom QGIS Projekt unverändert lassen
            pass
        return


    def _logProjectAttr(self):
        proj = QgsProject.instance()
        self.log.debug(f"""
        fileName            {proj.fileName()}
        absoluteFilePath    {proj.absoluteFilePath()}
        absolutePath        {proj.absolutePath()}
        """)


##class GQgis_App:
##    """central GeODinQGIS object (Singleton!)
##
##    05.09.2022 J:Ebert
##    """
##    def __new__(cls, version=""):
##        if not hasattr(cls, 'instance'):
##            cls.instance = super(GQgis_App, cls).__new__(cls)
##        return cls.instance
##
##    def __init__(
##        self,
##        version=""):
##        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
##        self.log.debug("")
##        self._Version = version
##        pass
##
##    def InfoText(self):
##        """ returns info text
##
##        05.09.2022 J.Ebert
##        """
##        txt = ""
##        txt += gx.gApp.info()
##        txt += env.InfoText_OS()
##        txt += env.InfoText()
##        self.log.info(txt)
##        return(txt)
##
##    @property
##    def Version(self):
##        return self._Version


##def main():
##    app = GQgis_App()
##    return app

if __name__ == '__main__':
    pass
##    app = main()
