"""
Classes:
    GoNodeGrpADC                - GrpDAC (GOM 'Documents') ViewModel/QTreeWidgetItem
    GoNodeGrpINV                - GrpINV (GOM 'MPoints') ViewModel/QTreeWidgetItem
    GoNodeGrpLOC                - GrpLOC (GOM 'Objects') ViewModel/QTreeWidgetItem

15.06.2023 j.ebert
"""
import json
import logging
from pathlib import Path

from qgis.PyQt import (
    QtCore,
    QtWidgets
)

import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gqgis_config as gqc
import GeODinQGIS.vm.bas_node as bas
from GeODinQGIS.vm.query_node import GoNodeQuery
from GeODinQGIS.ui.gqgis_bas import (
    cursor,
    plugin,
    GQgis_MsgBox as MsgBox
)

class GoNodeProject(bas.GoNode):
    """Project (GeODin Projekt) ViewModel/QTreeWidgetItem

    28.07.2023 j.ebert
    """

    def __init__(
        self,
        parent,                 # parent QTreeWidgetItem/Node
        tag                     # data, DataModel object (GoBaseClass)
    ):
        super().__init__(parent, tag)
        self.setText(self.textColumn(), self.tag().Name)
        self.orderText()
        self._presentQrys = []

    def loadChildren(self):
        """loads QTreeWidget child items

        28.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "Not overloaded in class %s", self.__class__.__name__)
        # 07/2023 j.ebert, quick and dirty
        #   Wenn die Children des Porjektes geladen werden, also
        #   wenn das Porjekt geöffnet/das erste mal aufgeklappt wird,
        #   dann Abfragendes Projektes nachladen
        self.DbRef.reload_GoQrys(self.PrjID)
        # 06/2023 j.ebert, Anmerkung
        #   Referenz auf GoDatabase vom Parent-Node an GroupNodes setzen oder nicht!?
        #   Wenn das Tag mit der Referenz auf GoDatabase an Group-Node übergeben wird.
        #   dann werden die Group-Nodes automatisch wie deren Parent-Node disabled dargestellt.
        #   (Attr isDisabled kann auch für GeODin-Projekte im DataModel implementiert werden,
        #    aber es funktioniert im ViewModel, da QTreeWidgetItem diese Attr. bereits hat.)
        GoNodeGrpLOC(self, self.tag())
        GoNodeGrpINV(self, self.tag())
        if self.DbRef.hasADCDATA():
            GoNodeGrpADC(self, self.tag())
        # QTreeWidgetItem aktualisieren
        self.update(1)
        return

    def onContextMenu(self):
        """returns QTreeWidget context menu

        31.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # akt. Queries identifizieren...
        self._presentQrys = self.DbRef.presentGoQrys(self.PrjID)
        # QMenu/Context-Menü instanziieren
        menu = QtWidgets.QMenu()
        # QAction vom GeODin Projekt instanziieren und dem Menü hinzufügen
##        if self._tag.isOpened():
        if self.isExpanded():
            action = menu.addAction(self.QIcon(self.iconAlias(0)), self.translate("Close..."))
            action.triggered.connect(self.onClose)
        else:
            # 07/2023 j.ebert, Anmerkung
            #   Zum Öffnen des Projektes nur den Konten/das QTreeWidgetItem aufklappen.
            action = menu.addAction(self.QIcon(self.iconAlias(1)), self.translate("Open..."))
            action.triggered.connect(lambda checked, expand=True: self.setExpanded(expand))
            action.setEnabled(not self._tag.isDisabled())
        menu.addSeparator()
        # 10/2026: menu text 'Update queries' -> 'Update layer data' (the action exports the data
        #   of the queries that already have a layer again; it does not reload the queries)
        action = menu.addAction(self.QIcon('GenericRefresh'), self.translate("Update layer data"))
        action.triggered.connect(self.onUpdateGoQrys)
        action.setEnabled(not self._tag.isDisabled() and bool(self._presentQrys))
        # 10/2026: reload the queries (object types, measurement point types, number of objects)
        action = menu.addAction(self.QIcon('GenericRefresh'), self.translate("Refresh"))
        action.triggered.connect(self.onRefresh)
        action.setEnabled(not self._tag.isDisabled() and not self.hasDummyChild())
        menu.addSeparator()
        action = menu.addAction(self.QIcon('gIcon'), self.translate("Show in GeoDin"))
        action.triggered.connect(self.onGeODin)
        action.setEnabled(not self._tag.isDisabled())
        self.log.debug('ContextMenu (ActionCount %d) exce_', len(menu.actions()))
        return menu

    def onRefresh(self):
        """reloads the queries of the project from the GeoDin database and rebuilds the child nodes

        The query nodes are created again (new object/measurement point types, number of
        objects/measurement points); expanded groups stay expanded. Existing QGIS layers are
        not changed (see 'Update layer data').

        10/2026
        """
        self.log.log(gqc._LOG_TRACE, "")
        if self.hasDummyChild():
            # children not loaded yet -> they are loaded when the project is expanded
            return
        try:
            with cursor(QtCore.Qt.CursorShape.WaitCursor):
                expanded = [
                    type(self.child(i)).__name__ for i in range(self.childCount())
                    if self.child(i).isExpanded()
                ]
                self.takeChildren()
                self.loadChildren()
                for i in range(self.childCount()):
                    child = self.child(i)
                    if type(child).__name__ in expanded:
                        # expanding a group loads its query nodes (DummyChild, see GoNode.onExpanded())
                        child.setExpanded(True)
                if self.treeWidget() is not None:
                    self.treeWidget().setCurrentItem(self)
        except Exception:
            self.log.error("Unknown error on refresh project", exc_info=True)
            MsgBox.error(plugin().parent(), self.translate("Refresh"),
                         self.translate("Unknown error on refresh project"))
        return

    def onClose(self):
        """opens Database/QTreeWidgetItem

        28.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        self.setExpanded(False)
        self.takeChildren()
        self._addDummyChild()
        # QTreeWidgetItem aktualisieren
        self.update(0)
        return

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
                self.translate("Unknown error on update layer data")
            )
        return

class GoNodeGrpLOC(bas.GoNode):
    """GrpLOC (GeODin Knoten "Objekte") ViewModel/QTreeWidgetItem

    31.05.2023 j.ebert
    """

    def __init__(
        self,
        parent,                 # parent QTreeWidgetItem/Node
        tag                     # data, DataModel object (GoBaseClass)
    ):
        super().__init__(parent, tag)
        self.setToolTip(self.textColumn(), f"{self.PrjID}: {self.text(self.textColumn())}")

    def loadChildren(self):
        """loads QTreeWidget child items

        28.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"gDB '%s' (PrjID '%s')...", self.DbRef.Name, self.PrjID)
        for qry in self.DbRef.list_GrpLOC(self.PrjID):
            GoNodeQuery(self, qry)
        self.sortChildren(self.orderColumn(), QtCore.Qt.SortOrder.AscendingOrder)
        return


class GoNodeGrpINV(bas.GoNode):
    """GrpLOC (GeODin Knoten "Objekte") ViewModel/QTreeWidgetItem

    31.05.2023 j.ebert
    """

    def __init__(
        self,
        parent,                 # parent QTreeWidgetItem/Node
        tag                     # data, DataModel object (GoBaseClass)
    ):
        super().__init__(parent, tag)
        self.setToolTip(self.textColumn(), f"{self.PrjID}: {self.text(self.textColumn())}")

    def loadChildren(self):
        """loads QTreeWidget child items

        28.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"gDB '%s' (PrjID '%s')...", self.DbRef.Name, self.PrjID)
        for qry in self.DbRef.list_GrpINV(self.PrjID):
            self.log.debug(str(qry))
            GoNodeQuery(self, qry)
        self.sortChildren(self.orderColumn(), QtCore.Qt.SortOrder.AscendingOrder)
        return


class GoNodeGrpADC(bas.GoNode):
    """GrpLOC (GeODin Knoten "Objekte") ViewModel/QTreeWidgetItem

    31.05.2023 j.ebert
    """

    def __init__(
        self,
        parent,                 # parent QTreeWidgetItem/Node
        tag                     # data, DataModel object (GoBaseClass)
    ):
        super().__init__(parent, tag)
        self.setToolTip(self.textColumn(), f"{self.PrjID}: {self.text(self.textColumn())}")
        # parent ist Node von GoDatabase oder GoProject

    def loadChildren(self):
        """loads QTreeWidget child items

        25.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "DbName '%s' (PrjID '%s')", self.DbRef.Name, self.PrjID)
##        self.log.debug(
##            "PrjID: %s\n\nACDDATA: %s\n",
##            str(self.PrjID), str(self.DbRef.GT_ADCDATA)
##        )
        if self.DbRef.hasADCDATA():
            lnks = self.DbRef.list_GrpADC(self.PrjID)
            if self.log.level <= logging.DEBUG:
                logRows = [str(row) for row in lnks]
                self.log.debug(
                    "DbName '%s' (PrjID '%s'): \n\t%s",
                    self.DbRef.Name, self.PrjID, json.dumps(logRows, indent=4).replace("\n", "\n\t")
                )
            for lnk in lnks:
                GoNodeLnkADC(self, lnk)
            self.sortChildren(self.orderColumn(), QtCore.Qt.SortOrder.AscendingOrder)
        return

class GoNodeLnkADC(bas.GoNode):
    """LnkADC (GeODin Knoten "Document") ViewModel/QTreeWidgetItem

    27.07.2023 j.ebert
    """

    def __init__(
        self,
        parent,                 # parent QTreeWidgetItem/Node
        tag                     # DBGroup/GOMGroup name
    ):
        super().__init__(parent, tag)
        self.setText(self.textColumn(), self.tag().Name)
        self.orderText()
        if self.tag()._ADC_TYPE in ('TIF',):
            self.setIcon(0, self.QIcon('gLnkTIF'))

    def lyrName(self):
        return self.text(self.textColumn())

    def lyrSource(self):
        return  Path(self.tag()._ADC_FILE).as_posix()

    def lyrType(self):
        val = 'Vector'
        if self.tag()._ADC_TYPE in ('TIF',):
            val = 'Raster'
        return val

    def onContextMenu(self):
        """returns QTreeWidget context menu

        31.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # QMenu/Context-Menü instanziieren
        menu = QtWidgets.QMenu()
        # QAction der Datenbank instanziieren und dem Menü hinzufügen
##        action = menu.addAction(self.QIcon('GenericRefresh'), self.translate("Add layer..."))
        # 10/2026: 'Add layer...' -> 'Add layer' (no dialog follows)
        action = menu.addAction(self.translate("Add layer"))
        action.triggered.connect(self.onDoubleClicked)
        action.setEnabled(not self.tag().isDisabled())
        return menu

    def onDoubleClicked(self):
        """event function for QTreeWidget signal 'itemDoubleClicked'

        28.07.2023 j.ebert
        """
        self.log.log(
            gqc._LOG_TRACE,
            "DbName '%s' (PrjID '%s'). %s", self.DbRef.Name, self.PrjID, self.lyrName()
        )
        if self.lyrType() == 'Raster':
##            newLyr = qgis.core.QgsRasterLayer(self.lyrSource(), self.lyrName())
##            qgis.core.QgsProject.instance().addMapLayer(newLyr)
            plugin().iface().addRasterLayer(self.lyrSource(), self.lyrName())
        else:
            # 07/2023 j.ebert, Anmerkung
            #   Beide Varianten sind quasiu identisch
            #   https://docs.qgis.org/3.28/en/docs/pyqgis_developer_cookbook/loadlayer.html#vector-layers
##            newLyr = qgis.core.QgsVectorLayer(self.lyrSource(), self.lyrName(), "ogr")
##            qgis.core.QgsProject.instance().addMapLayer(newLyr)
            plugin().iface().addVectorLayer(self.lyrSource(), self.lyrName(), "ogr")
        return

def main():
    pass

if __name__ == '__main__':
    main()
