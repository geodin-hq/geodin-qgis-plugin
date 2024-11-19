"""
Classes:
    GoNodeDatabase              - GoDatabase ViewModel/QTreeWidgetItem

31.05.2023 j.ebert
"""
import json
import logging
import os
from qgis.PyQt import (
    QtCore,
    QtWidgets
)


import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gqgis_config as gqc
import GeODinQGIS.gx as gx
import GeODinQGIS.vm.bas_node as bas
import GeODinQGIS.vm.group_node as vm_grps

##from GeODinQGIS import (
##    app
##)
from GeODinQGIS.ui.gqgis_bas import (
    cursor,
    plugin,
    GQgis_MsgBox as MsgBox
)
from GeODinQGIS.ui.gqgis_dlg_login import GQgis_Dlg_Login

class GoNodeDatabase(bas.GoNode):
    """GoDatabase ViewModel/QTreeWidgetItem

    31.05.2023 j.ebert
    """

    def __init__(
        self,
        parent,                 # parent QTreeWidgetItem/Node
        tag                     # DBGroup/GOMGroup name
    ):
        super().__init__(parent, tag)
        self._gDB = tag
        self.setText(self.textColumn(), self._gDB.Name)
        self.orderText()
        self._presentQrys = []

    @property
    def GoLayerPattern(self):
        """Pattern (str) of GoLayer DataSource

        24.07.2024 j.ebert
        """
        val = str(self._gDB.DataPath).lower()
        if val[-1] != '\\':
            val = os.path.join(val,"").lower()
        return val

    @property
    def GOMGroup(self):
        return self._GOMGroup

    def loadChildren(self):
        """loads QTreeWidget child items

        31.08.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "Not overloaded in class %s", self.__class__.__name__)
        # 06/2023 j.ebert, Anmerkung
        #   Referenz auf GoDatabase vom Parent-Node an GroupNodes setzen oder nicht!?
        #   Wenn das Tag mit der Referenz auf GoDatabase an Group-Node übergeben wird.
        #   dann werden die Group-Nodes automatisch wie deren Parent-Node disabled dargestellt.
        #   (Attr isDisabled kann auch für GeODin-Projekte im DataModel implementiert werden,
        #    aber es funktioniert im ViewModel, da QTreeWidgetItem diese Attr. bereits hat.)
        if True:
            prjs = self.DbRef.GoPrjs
            if self.log.level <= logging.DEBUG:
                logRows = [str(row) for row in prjs]
                self.log.debug(
                    "DbName '%s': \n\t%s",
                    self.DbRef.Name, json.dumps(logRows, indent=4).replace("\n", "\n\t")
                )
            for prj in prjs:
                nodePrj = vm_grps.GoNodeProject(self, prj)
            nodeGrpLOC = vm_grps.GoNodeGrpLOC(self, self._tag)
            nodeGrpINV = vm_grps.GoNodeGrpINV(self, self._tag)
            if self._tag.hasADCDATA():
                nodeGrpADC = vm_grps.GoNodeGrpADC(self, self._tag)
        else:
            nodeGrpLOC = vm_grps.GoNodeGrpLOC(self, None)
            nodeGrpINV = vm_grps.GoNodeGrpINV(self, None)
            nodeGrpADC = vm_grps.GoNodeGrpADC(self, None)
        return

    def onContextMenu(self):
        """returns QTreeWidget context menu

        31.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # akt. Queries der Datenbank identifizieren...
        self._presentQrys = self.DbRef.presentGoQrys()
        # QMenu/Context-Menü instanziieren
        menu = QtWidgets.QMenu()
        # QAction der Datenbank instanziieren und dem Menü hinzufügen
        if self._tag.isOpened():
            action = menu.addAction(self.QIcon(self.iconAlias(0)), self.translate("Close..."))
            action.triggered.connect(self.onClose)
        else:
            # 06/2023 j.ebert, Anmerkung
            #   Zum Öffnen der Datenbank nur den Konten/das QTreeWidgetItem aufklappen.
            #   Beim Aufklappen des Knotens muss die Datenbank sowieso geöffnet werden, wenn
            #   sie noch nicht geöffnet ist. Daher ist hier das Aufklappen völlig ausreichend.
            action = menu.addAction(self.QIcon(self.iconAlias(1)), self.translate("Open..."))
            action.triggered.connect(lambda checked, expand=True: self.setExpanded(expand))
            action.setEnabled(not self._tag.isDisabled())
        action = menu.addAction(self.QIcon('GenericDelete'), self.translate("Remove..."))
        action.triggered.connect(self.onRemove)
        menu.addSeparator()
        action = menu.addAction(self.QIcon('GenericRefresh'), self.translate("Update queries"))
        action.triggered.connect(self.onUpdateGoQrys)
        action.setEnabled(self._tag.isOpened() and bool(self._presentQrys))
        menu.addSeparator()
        action = menu.addAction(self.QIcon('gIcon'), self.translate("GeODin"))
        action.triggered.connect(self.onGeODin)
        action.setEnabled(not self._tag.isDisabled())
        self.log.debug('ContextMenu (ActionCount %d) exce_', len(menu.actions()))
        return menu

    def onClose(self):
        """opens Database/QTreeWidgetItem

        31.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        try:
            # 06/2023 j.ebert, Anmerkung
            #   Kein Aufruf einer GeODin-COM-Funktion notwendig.
            #   Damit weder der Knoten einer Datenbank im GOM zusammengekalppt noch
            #   die Datenbank selbst (in GeODin) geschlossen werden.
            self._tag._isOpened = False
            if not self.hasDummyChild():
                self.takeChildren()
                self._addDummyChild()
        except gqb.GxException as exc:
            MsgBox.error(plugin().parent(), 'GeODin', exc.msg())
        except Exception:
            MsgBox.error(
                plugin().parent(),
                'GeODin',
                self.translate("Unknown error on close database")
            )
        finally:
            # QTreeWidgetItem aktualisieren
            mode = 1 if self._tag.isOpened() else 0
            self.setExpanded(self._tag.isOpened())
            self.update(mode)
        return

    def onExpanded(self):
        """event function for QTreeWidget signal 'itemExpanded'

        14.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "")
        if not self._tag.isOpened():
            self.onOpen()

        if not self._tag.isOpened():
            # Wenn die DB nicht geöffnet ist, also
            # wenn die DB auch nicht geöffnet werden konnte,
            # dann Knoten der DB wieder zusammen klappen
            self.setExpanded(False)
        else:
            # Wenn die DB geöffnet ist,
            # dann ...
            super().onExpanded()
        mode = 1 if self._tag.isOpened() else 0
        self.update(mode)
        return

    def onOpen(self):
        """opens Database/QTreeWidgetItem

        13.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        try:
            try:
                # Datenbank öffnen
                self._tag.open()
##            except gqb.GxSQLCnnError:
            except gqb.GxException:
                # Wenn die Datenbank nicht erfolgreich geöffnet werden konnte,
                # dann Login abfragen und Datenbank erneut öffnen
                dlg = GQgis_Dlg_Login.instance(
                    self._tag.Name,
                    dbUser="",
                    dbPassword="",
                    parent=None
                )
                if dlg.exec_():
                    # Wenn Login-Dialog nicht vom Nutzer abgebrochen wurde,
                    # dann erneuter Versuch mit Login-Eingabe vom Nutzer
                    usr, pwd = dlg.login()
                    self._tag.open(usr, pwd)
            if self._tag.isOpened():
                self.log.info(
                    "Database '%s' could be opened successfully" , self._tag.Name
                )
        except gqb.GxException as exc:
            self.log.warning(
                "Database '%s' could not be opened\n\t%s", self._tag.Name, exc.msg()
            )
            MsgBox.error(plugin().parent(), 'GeODin', exc.msg())
        except Exception:
            self.log.critical( "Major disaster...", exc_info=True )
            MsgBox.error(
                plugin().parent(),
                'GeODin',
                self.translate("Unknown error on open database")
            )
        finally:
            # QTreeWidgetItem aktualisieren
            mode = 1 if self._tag.isOpened() else 0
            self.update(mode)
        return

    def onRefresh(self):
        """removes Database/QTreeWidgetItem

        31.05.2023 j.ebert
        """
        self.log.debug("Not implemnted for %s", self.__class__.__name__)
        return

    def onRemove(self):
        """removes Database/QTreeWidgetItem

        24.07.2024 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        try:
            # Alle Layer der GeODin-Database im QGIS-Projekt löschen, sonst
            # verursacht das Löschen der DataSources/der GeoJSON-Files eine Exception
            self.removeGoLayers(refresh=True)
            # Database (aus DDX) entfernen...
            # (Sleep zur Sychronisation, damit Löschen der DataSources keine Exception verursacht)
            QtCore.QTimer.singleShot(self.QSleepTime, self._gDB.remove)
            self.parent().removeChild(self)
        except gqb.GxException as exc:
            self.log.error("Unknown error on remove database", exc_info=True)
            MsgBox.error(plugin().parent(), self.translate("Remove Database"), exc.msg())
        except Exception:
            self.log.critical("Unknown error on remove database", exc_info=True)
            MsgBox.error(
                plugin().parent(),
                self.translate("Remove Database"),
                self.translate("Unknown error on remove database")
            )
        return

    def onTakeNode(self):
        # GoDatabase aus QTreeWidget entfernen, jedoch NICHT(!!!) aus DDX
        self._gDB._isPresent = False
        self._gDB = None

    def onUpdateGoQrys(self):
        """updates query dataSource

        08.08.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # 08.08.2023 j.ebert, Anmerkung
        #   Attr _presentQrys (die Liste) wird in onContextMenu() gesetzt/aktualisiert, weil
        #   die Aktion 'Updates queries' nur dann enabled wird, wenn "present" Queries existieren
        try:
            for qry in self._presentQrys:
                qry.updateDataSource()
            self._presentQrys= []
        except gqb.GxException as exc:
            self.log.debug("", exc_info=True)
            MsgBox.error(plugin().parent(), '', exc.msg())
        except Exception:
            self.log.critical("Major disaster...", exc_info=True)
            MsgBox.error(
                plugin().parent(),
                '',
                self.translate("Unknown error on update queries")
            )
        return

    def update(
        self,
        mode=0                  # alias index (0-normal|1-open)
    ):
        """updates GoDatabase node/QTreeWidgetItem

        13.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "")
        if self._tag.isOpened():
            pass
        else:
            self.log.log(gqc._LOG_TRACE, "xxxx")
        super().update(mode)
        return


def main():
    pass

if __name__ == '__main__':
    main()
