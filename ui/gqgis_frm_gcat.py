"""
classes:
    GQgis_Frm_GCat              - PyQt GeODin Explorer/Catalog (Singleton!)

24.05.2023 j.ebert
"""
CONTEXT_RES = "GQgis_Frm_GCat"
"""context for resource translation of QWidgets"""
import logging
import types
from pathlib import Path

import qgis.gui
from qgis.PyQt import (
    QtCore,
    QtGui,
    QtWidgets
    )

import GeODinQGIS.gqgis_config as gqc
import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.vm as vm

from GeODinQGIS import (
    env,
    res
    )
from GeODinQGIS.ui.gqgis_bas import (
    GQgis_Bas_Widget,
    GQgis_MsgBox as MsgBox
)
from GeODinQGIS.ui.ui_gqgis_frm_gcat import Ui_GQgis_Frm_GCat

class GQgis_Frm_GCat(qgis.gui.QgsDockWidget, GQgis_Bas_Widget):
    """PyQt GeODin Catalog (Singleton!)

    24.05.2023 j.ebert
    """

    log = logging.getLogger(f"{__name__}.GQgis_Frm_GCat")

    _INFO = 20
    _WARNING = 30
    _ERROR = 40

    def __new__(cls, parent):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GQgis_Frm_GCat, cls).__new__(cls)
            cls.log.debug("initialized")
        cls.log.log(gqc._LOG_TRACE,"")
        return cls.instance

    def __init__(self, parent):
        super().__init__(parent)
##        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.log(gqc._LOG_TRACE,"")
        self._context = CONTEXT_RES
        # initialize GCatalog properties
        # set up QWidget
        self.ui = Ui_GQgis_Frm_GCat()
        self.ui.setupUi(self)
        # initialize...
        self.ui.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # 05/2023 j.ebert, Anmerkung
        # - Im Qt Designer default SelectionMode 'SingleSelection'
        #   -> SelectionMode 'SingleSelection' muss nicht zwingend gesetzt werden
        # - SelectionMode 'ExtendedSelection' in GeODinQGIS Plugin Verison 2?!
        #   (dgf. weil im TreeView auch einzelne Objekte angezeigt und gemanaged wurden)
##        self.ui.treeWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        # 05/2023 j.ebert, Anmerkung
        #   DBRoot-Node/QTreeWidgetItem erstellen und QTreeWidget als Prm 'parent' übergeben
        #   -> Node/QTreeWidgetItem wird damit dem QTreeWidget als TopLevelItem hinzugefügt
        tvwDBRoot = vm.GoNodeDBRoot(self.ui.treeWidget, None)
        self.validateUi()
        self.connectUi()
        # translate QWidget
        self.translateUi()
        # register QWidget for translation
        res.Ui.append(self)

    def connectUi(self):
        """connect QWidget signals

        14.04.2023 j.ebert
        """
        # QTreeWidget Signale verbinden...
        self.ui.treeWidget.customContextMenuRequested.connect(self.onContextMenu)
        self.ui.treeWidget.itemCollapsed.connect(self.onCollapsed)
        self.ui.treeWidget.itemExpanded.connect(self.onExpanded)
        self.ui.treeWidget.itemDoubleClicked.connect(self.onDoubleClicked)
        return

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        # translate Ui/QWidget
        try:
            self.setWindowTitle(self.trans("GeODinQGIS - Explorer"))
            if hasattr(self, '_showAction'):
                self._showAction.setText(self.trans("GeODinQGIS Explorer"))
                self._showAction.setToolTip(self.trans("GeODinQGIS Explorer"))
        except:
            self.log.error("", exc_info=True)
        return

    def validateUi(self):
        """validate DDX Dialog

        29.04.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        return

    def updateTree(
        self,
        gomgroups=[]            # GOMGroup name list
    ):
        self.log.log(gqc._LOG_TRACE,"")
        dbRoot = self.ui.treeWidget.topLevelItem(0)
        dbRoot.onTakeNode()
        if gomgroups:
            for name in gomgroups:
                dbGroup = vm.GoNodeDBGroup(dbRoot, name)
                dbGroup.updateTree()
        dbRoot.updateTree()

    def updateTree_v01(
        self,
        databases=[]            # GoDatabase list
    ):
        self.log.log(gqc._LOG_TRACE,"")
        dbRoot = self.ui.treeWidget.topLevelItem(0)
        dbRoot.onTakeNode()
        if databases:
            for name in set([gDB.GOMGroup for gDB in databases if gDB.GOMGroup]):
                vm.GoNodeDBGroup(dbRoot, name)
            dbRoot.setExpanded(True)


    def onSelected(self):
        """returns selected GoNode/QTreeWidgetItem

        25.05.2023 j.ebert
        """
        item = None
        if (len(self.ui.treeWidget.selectedIndexes()) == 1):
            item = self.ui.treeWidget.itemFromIndex(self.ui.treeWidget.selectedIndexes()[0])
        if not isinstance(item, vm.GoNode):
            item = None
        return item

    def onContextMenu(self, position):
        """returns ContextMenu for selected GoNode/QTreeWidgetItem

        31.05.2023 j.ebert
        """
        menu = None
        item = self.onSelected()
        if item:
            menu = item.onContextMenu()
            self.log.debug(
                "%s context menu (%d actions)...", type(item).__name__, len(menu.actions())
            )
            menu.exec_(self.ui.treeWidget.viewport().mapToGlobal(position))
        return menu

    def onCollapsed(self, item):
        """event function for QTreeWidget signal 'itemCollapsed'

        25.05.2023 j.ebert
        """
        if isinstance(item, vm.GoNode):
           item.onCollapsed()
        return

    def onExpanded(self, item):
        """event function for QTreeWidget signal 'itemExpanded'

        25.05.2023 j.ebert
        """
        if isinstance(item, vm.GoNode):
           item.onExpanded()
        return

    def onDoubleClicked(self, item, column):
        """event function for QTreeWidget signal 'itemDoubleClicked'

        25.05.2023 j.ebert
        """
        if isinstance(item, vm.GoNode):
           item.onDoubleClicked()
        return

    @classmethod
    def showAction(
        cls,
        parent=None
    ):
        """
        returns:
            QAction

        24.05.2023 j.ebert
        """
        if not hasattr(cls, '_showAction'):
            frm = cls(parent)
            cls._showAction = frm.toggleViewAction()
            cls._showAction.log = logging.getLogger(f"{__name__}.GQgis_Act_GCat")
            cls._showAction.setObjectName('GQgis_Act_GCat')
            cls._showAction.setIcon(frm.QIcon("gExplorer"))
            # Funktion _showAction_updateUi an Instanz _showAction 'binden' als Methode updateUi()
            # https://stackoverflow.com/questions/972/adding-a-method-to-an-existing-object-instance-in-python
            cls._showAction.updateUi = types.MethodType(_showAction_updateUi, cls._showAction)
            # 05/2023 j.ebert, Anmerkung
            #   Translation von _showAction findet in GQgis_Frm_GCat.translateUi() statt, weil
            #   _showAction nicht die notwendigen Methoden von GQgis_Bas_Widget erbt.
            if True:
                # entweder GQgis_Frm_GCat.translateUi() wie folgt aufrufen,
                # dann wird translateUi() zwei mal ausgeführt
                # (beim Instanzioeren der Klasse, aber da ist _showAction nicht gesetzt und hier)
                frm.translateUi()
            else:
                # oder die Texte von _showAction hier setzen,
                # dann ist das setzen der Texte redundant in GQgis_Frm_GCat.translateUi() und hier
                cls._showAction.setText(frm.trans("GeODinQGIS Explorer"))
                cls._showAction.setToolTip(frm.trans("GeODinQGIS Explorer"))
        cls._showAction.log.log(gqc._LOG_TRACE,"")
        return cls._showAction

def _showAction_updateUi(
    self,
    widget=None             # Parent QWidget that is activated/deactivated
):
    """updates QWidget of this QAction

    args:
        widget (QWidget)    - QWidget that is activated/deactivated

    26.05.2023 j.ebert
    """
    from GeODinQGIS import app
    self.log.log(gqc._LOG_TRACE,"TRACE")
    enabled = app.isConnected()
    if (
        isinstance(widget, QtWidgets.QWidget) and
        (widget.isEnabled() != enabled)
    ):
        # 05/2023 j.ebert, Achtung
        #   Reihenfolge genau so - zuerst QgsDockWidget und danach widget/QAbstractButton handeln!
        #   Der Button ist mit dem QgsDockWidget verbunden und ist davon abhängig, dadurch
        #   wird der Button beim Ausführen von QgsDockWidget.setUserVisible() aktualisiert/enabled.
        # QgsDockWidget beim Deaktivieren(!) schließen...
        if (
            (not enabled) and
            hasattr(GQgis_Frm_GCat, 'instance')
        ):
            # 05/2023 j.ebert, Anmerkung
            # - hier Attr 'instance' nutzen - quick and dirty, weil Prm 'parent' nicht bekannt ist
            # - QgsDockWidget in den Fordergrund holen, sonst wird es nicht geschlossen
            #   https://qgis.org/pyqgis/3.6/gui/QgsDockWidget.html#qgis.gui.QgsDockWidget.setUserVisible
            frm = GQgis_Frm_GCat.instance
            if not frm.isUserVisible():
                frm.setUserVisible(True)
            frm.setUserVisible(False)
        # widget/QAbstractButton aktivieren/deaktivieren
        widget.setEnabled(enabled)
    return

def main():
    pass

if __name__ == '__main__':
    main()
