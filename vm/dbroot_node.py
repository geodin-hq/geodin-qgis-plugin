"""
Classes:
    GoNodeDBGroup               - DBGroup (GOMGroup) ViewModel/QTreeWidgetItem
    GoNodeDBRoot                - DBRoot ('Databases') ViewModel/QTreeWidgetItem

31.05.2023 j.ebert
"""

from qgis.PyQt import (
    QtCore,
    QtWidgets
)


import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gqgis_config as gqc
import GeODinQGIS.vm.bas_node as bas
from GeODinQGIS.vm.database_node import (
    GoNodeDatabase
)
from GeODinQGIS import (
    app
)
from GeODinQGIS.ui.gqgis_bas import (
    cursor,
    plugin,
    GQgis_MsgBox as MsgBox
)

class GoNodeDBGroup(bas.GoNode):
    """DBGroup (GOMGroup) ViewModel/QTreeWidgetItem

    31.05.2023 j.ebert
    """

    def __init__(
        self,
        parent,                 # parent QTreeWidgetItem/Node
        tag                     # DBGroup/GOMGroup name
    ):
        super().__init__(parent, tag)
        self._GOMGroup = str(tag)
        self.setText(self.textColumn(), self._GOMGroup)
        self.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.DontShowIndicatorWhenChildless)

    @property
    def DbRef(self):
        """returns GoDatabase object

        27.07.2023 j.ebert
        """
        # Datenbank-Gruppen haben prinzipiell keinen Verweis auf ein GoDatabase Objekt
        return None

    @property
    def GOMGroup(self):
        return self._GOMGroup

    @property
    def PrjID(self):
        """returns GeODin PrjID

        27.07.2023 j.ebert
        """
        # Datenbank-Gruppen haben prinzipiell keine GeODin PrjID
        return None

    def addDatabase(
        self,
        gDB,                    # GoDatabase
        expandNode=True
    ):
        """adds GoDatabase to QTreeWidget

        12.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, gDB.Name)
        try:
            # Database dem DDX hinzufügen
            gDB.add()
            # Database dem Explorer/Catalog (QTreeWidget) hinzufügen...
            node = GoNodeDatabase(self, gDB)
            self.sortChildren(self.orderColumn(), QtCore.Qt.AscendingOrder)
            self.setExpanded(expandNode)
        except gqb.GxException as exc:
            MsgBox.error(plugin().parent(), self.translate("Add Database"), exc.msg())
        except Exception:
            self.log.error("Unknown error on add database", exc_info=True)
            MsgBox.error(
                plugin().parent(),
                self.translate("Add Database"),
                self.translate("Unknown error on add database")
            )
        return

    def onContextMenu(self):
        """returns QTreeWidget context menu

        31.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # QMenu/Context-Menü instanziieren
        menu = QtWidgets.QMenu()
        # QAction zur Auswahl der Datenbank instanziieren und dem Menü hinzufügen
        for gDB in [item for item in app.DBs if (item.GOMGroup == self.GOMGroup)]:
            self.log.debug("ActIdx %2d - %s", len(menu.actions()), gDB.Name)
            action = menu.addAction(self.QIcon('gDB'), gDB.Name)
            action.triggered.connect(lambda checked, gDB=gDB: self.addDatabase(gDB))
            # enable/disable QAction...
            #   enable QAction, wenn die Datenbank noch nicht im QTreeWidget enthalten ist
            #   Also prinzipiell bleiben alle Datenbanken im Context-Menü, aber
            #   nur die Datenbanken sind im QMenu aktiv, die noch nicht im QTreeWidget sind
            action.setEnabled(not gDB.isPresent())

        self.log.debug('ContextMenu (ActionCount %d) exce_', len(menu.actions()))
        return menu

    def onTakeNode(self):
        for node in self.takeChildren():
            node.onTakeNode()

    def updateTree(self):
        """
        09.06.2023 j.ebert
        """
        for gDB in [
            item for item in app.DBs if (item.GOMGroup == self.GOMGroup) and item.isPresent()
        ]:
            self.addDatabase(gDB, expandNode=False)
        if self.childCount():
            self.setExpanded(True)



class GoNodeDBRoot(GoNodeDBGroup):
    """DBRoot ('Databases') ViewModel/QTreeWidgetItem

    25.05.2023 j.ebert
    """

    def __new__(cls, parent, tag=""):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GoNodeDBRoot, cls).__new__(cls, parent, tag)
        return cls.instance

    def __init__(
        self,
        parent,                 # QTreeWidget
        tag=""                  # argument 'tag' is always ""
    ):
        # 05/2023 j.ebert, Anmerkung
        #   DBRoot hat immer den Text "Databases" und als tag/GOMGroup ""!
        #   -> init Superclass 'GoNodeDBGroup' mit Argumenten parent (QTreeWidget) und tag=""
        super().__init__(parent, "")
        self.setText(self.textColumn(), self.translate("Databases"))


def main():
    pass

if __name__ == '__main__':
    main()
