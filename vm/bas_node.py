"""
classes:
    GoNode                      - base node/bas class of ViewModel/QTreeWidgetItem

globals:
    _GONODE_SETTINGS (dict)     - settings for nodes inherited from the base class GoNode

01.06.2023 j.ebert
"""
import logging
import traceback

from qgis.PyQt import (
    QtCore,
    QtGui,
    QtWidgets
)

import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gqgis_config as gqc
import GeODinQGIS.dm as dm
import GeODinQGIS.gx as gx
from GeODinQGIS.ui.gqgis_bas import (
    cursor,
    plugin,
    GQgis_MsgBox as MsgBox
)

from GeODinQGIS import res


_GONODE_SETTINGS = {
    'GoNode':           (
        0,                      # order index (int)
        ('gNode',),             # icon aliases (tuple (<normal>, <open>, ...)
        False                   # True to add DummyChild
    ),
    'GoNodeDBRoot':     (3, ('gDBRoot',), False),
    'GoNodeDBGroup':    (3, ('gDBGroup',), False),
    'GoNodeDatabase':   (4, ('gDB', 'gDBOpen'), True),
    'GoNodeProject':    (5, ('gPRJ', 'gPRJOpen'), True),
    'GoNodeGrpLOC':     (10, ('gGrpLOC',), True),
    'GoNodeGrpINV':     (12, ('gGrpINV',), True),
    'GoNodeGrpADC':     (14, ('gGrpADC',), True),
    'GoNodeLnkADC':     (41, ('gLnkADC',), False),
    'GoNodeQuery':      (20, ('gLnkADC',), False)
}
"""settings for nodes inherited from the base class GoNode

15.06.2023 j.ebert
"""

class GoNode(QtWidgets.QTreeWidgetItem):
    """View Model Base Class

    25.05.2023 j.ebert
    """

    DummyNodeID = "DummyNode"
    """QTreeWidgetItem text identifying a dummy node"""

    def __init__(
        self,
        parent,                 # parent QTreeWidgetItem/Node
        tag=None                # data, DataModel object (GoBaseClass)
    ):
        QtWidgets.QTreeWidgetItem.__init__(self, parent)
        self.log  = logging.getLogger(f"{gqc._LOG_PARENTS}{self.__class__.__name__}")
        self.log.log(gqc._LOG_TRACE,"")
        self._context = "vm"    # Context für Transaltion/Übersetzung vom Modul vm
        self._tag = tag
        # QTreeWidgetItem initialisieren...
        self.setIcon(0, GoNode.QIcon(self.iconAlias()))
##        self.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ShowIndicator)
        self.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.DontShowIndicatorWhenChildless)
        name = self.__class__.__name__
        if hasattr(self._tag, 'goDict'):
            name = self._tag.goDict(name)
        self.setText(self.textColumn(), name)
##        self.setText(self.textColumn(), self.translate(self.__class__.__name__))
        self.orderText()
        self.update()
        self._addDummyChild()

        # Relikt aus GeODinQGIS_Main.py (Z 879)
##        self.setData(0, QtCore.Qt.WhatsThisRole, prj.id)
##        self.extraInformation = prj
##        self.itemType = PROJECTITEM
##        self.normalString = prj.name

    @property
    def DbRef(self):
        """returns GoDatabase object

        27.07.2023 j.ebert
        """
        if not hasattr(self, '_DbRef'):
            if hasattr(self.tag(), 'DbRef'):
                # Wenn das tag Object ein Attr DbRef hat, also
                # wenn das Tag Object vom Typ GoBaseClass oder eine davon abgeleiteten Klasse ist,
                # dann deren DbRef (Verweis auf GoDatabase) zurückgeben
                self._dbRef = self.tag().DbRef
            else:
                # sonst DbRef (Verweis auf GoDatabase) vom Parent-Node/QTreeWidgetItem zurückgeben
                self._dbRef = self.parent().DbRef
        return self._dbRef

    @property
    def PrjID(self):
        """returns GeODin PrjID

        27.07.2023 j.ebert
        """
        if not hasattr(self, '_PrjID'):
            if hasattr(self.tag(), 'PrjID'):
                # Wenn das tag Object ein Attr PrjID hat, also
                # wenn das Tag Object vom Typ GoBaseClass oder eine davon abgeleiteten Klasse ist,
                # dann deren PrjID (GeODin PrjID) zurückgeben
                self._PrjID = self.tag().PrjID
            else:
                # sonst deren PrjID (GeODin PrjID) vom Parent-Node/QTreeWidgetItem zurückgeben
                self._PrjID = self.parent().PrjID
        return self._PrjID

    @classmethod
    def QIcon(
        cls,
        alias,                  # recource alias/image alias
        disabled=False
        ):
        """ returns QIcon for recource alias/image alias

        Args:
            alias (str)         recource alias

        02.09.2022 J.Ebert
        """
        icon = QtGui.QIcon(f":/plugins/GeODinQGIS/{alias}")
        if disabled:
            icon = QtGui.QIcon(icon.pixmap(QtCore.QSize(32, 32), QtGui.QIcon.Disabled))
        return icon

    def tag(self):
        """returns data or DataModel object (GoBaseClass) from this GoNode

        27.07.2023 j.ebert
        """
        return self._tag

    def translate(
        self,
        key
    ):
        """translate souerce text 'key' using instance context

        Args:
            key (str)               source text
        Returns:
            sourceText (str)

        25.05.2023 j.ebert
        """
        return  res.translate(self._context, key)

    @classmethod
    def orderColumn(cls):
        """returns QTreeWidgetItem column for sorting QTreeWidget - never overload/change this attribute

        09.06.2023 j.ebert
        """
        return cls.textColumn() + 1

    def orderIndex(self):
        """returns QTreeWidgetItem class index for sorting QTreeWidget

        01.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "")
        idx = _GONODE_SETTINGS.get(self.__class__.__name__, _GONODE_SETTINGS['GoNode'])[0]
        return idx

    def orderText(self):
        """retruns text for sorting QTreeWidget and updates QTreeWidgetItem column

        01.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "")
        text = self.text(0)
        text = self.text(self.textColumn())
        if not text:
            text = ""
        text = "%03d-%s" % (self.orderIndex(), text)
        self.setText(self.orderColumn(), text)
        self.log.log(gqc._LOG_TRACE, "%s - %s", self.tag().__class__.__name__, text)
        return text

    def hasDummyChild(self):
        """True if QTreeWidgetItem has only one DummyChild

        15.06.2023 j.ebert
        """
        val = (
            (self.childCount() == 1) and
            (str(self.child(0).text(self.textColumn())) == self.DummyNodeID)
        )
        return val

    def iconAlias(
        self,
        mode=0                  # alias index (0-normal|1-open)
        ):
        """retruns icon alias

        01.06.2023 j.ebert
        """
##        self.log.log(gqc._LOG_TRACE, "")
        names = _GONODE_SETTINGS.get(self.__class__.__name__, _GONODE_SETTINGS['GoNode'])[1]
        alias = names[mode] if mode < len(names) else names[0]
        self.log.log(gqc._LOG_TRACE, alias)
        return alias

    def loadChildren(self):
        """loads QTreeWidget child items

        25.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "Not overloaded in class %s", self.__class__.__name__)
        return

    def onContextMenu(self):
        """returns QTreeWidget context menu

        25.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "Not overloaded in class %s", self.__class__.__name__)
        menu = QtWidgets.QMenu()
        return menu

    def onCollapsed(self):
        """event function for QTreeWidget signal 'itemCollapsed'

        25.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "Not overloaded in class %s", self.__class__.__name__)
        return

    def onDoubleClicked(self):
        """event function for QTreeWidget signal 'itemDoubleClicked'

        15.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "Not overloaded in class %s", self.__class__.__name__)
        # 06/2023 j.ebert, Achtung!!!
        #   Im Qt Designer ist für QTreeWidget die Option expandsOnDoubleClick aktiviert!
        #   Daher hier NICHT den Knoten/das QTreeWidgetItem auf- oder zusammenklappen mit
        #       self.setExpanded(not self.isExpanded())
        #   Auf- und Zusammenklappen entweder über QTreeWidget-Option oder Event-Funktion!
        return

    def onExpanded(self):
        """event function for QTreeWidget signal 'itemExpanded'

        14.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "Not overloaded in class %s", self.__class__.__name__)
        self.setSelected(True)
        if (self.isExpanded() and self.hasDummyChild()):
            # Wenn der Knoten aufgeklappt ist und
            # wenn der Knoten NUR GENAU ein DummyChild hat,
            # dann das DummyChild entfernten und Children laden
            self.takeChild(0)
            self.log.debug(str(self.isExpanded()))
            self.loadChildren()
        return

    def onGeODin(self):
        """selects Database in the GeODin object manager

        01.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        if isinstance(self._tag, dm.GoBaseClass):
            try:
                gx.gApp.selectObject(self._tag)
            except gqb.GxException as exc:
                MsgBox.error(plugin().parent(), 'GeODin', exc.msg())
            except Exception:
                MsgBox.error(
                    plugin().parent(),
                    'GeODin',
                    self.translate("Unknown error on select object")
                )
        return

    def onRefresh(self):
        """removes Database/QTreeWidgetItem

        31.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "Not overloaded in class %s", self.__class__.__name__)
        return

    def onRemove(self):
        """removes Database/QTreeWidgetItem

        31.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "Not overloaded in class %s", self.__class__.__name__)
        return

    @classmethod
    def palette(cls):
        """ returns QPalette from Explorer/Catalog (QTreeWidget)

        09.06.2023 j.ebert
        """
        # seealso:  https://doc.qt.io/qtforpython-5/PySide2/QtGui/QPalette.html
        from GeODinQGIS.ui.gqgis_frm_gcat import GQgis_Frm_GCat as GCat
        return GCat.instance.ui.treeWidget.palette()

    @classmethod
    def textColumn(cls):
        """returns QTreeWidgetItem column for text/display name - never overload/change this attribute

        09.06.2023 j.ebert
        """
        return 0

    def update(
        self,
        mode=0                  # icon/alias (0-normal|1-open)
        ):
        """updates the node/QTreeWidgetItem

        13.06.2023 j.ebert
        """
        disabled = False
        if isinstance(self._tag, dm.GoBaseClass):
            self.setToolTip(self.textColumn(), self._tag.Info)
        if (hasattr(self._tag, 'isDisabled') and (self._tag.isDisabled())):
            # 06/2023 j.ebert, Anmerkung
            #   QTreeWidgetItem.setDisabled() ist nicht so günstig, da dann
            #   der komplette Node disabled ist unter anderem auch das Kontext-Menü.
            self.log.debug("%s - isDisabled: %s", self._tag.Name, str(self._tag.isDisabled()))
            disabled = self._tag.isDisabled()
            self.setForeground(
                self.textColumn(),
                self.palette().brush(QtGui.QPalette.Disabled, QtGui.QPalette.Text)
            )
            # 06/2023 j.ebert Anmerkung
            #   Wenn QTreeWidgetItem disabled ist/dragestellt wird,
            #   dann IMMER 'normal' Icon ( default, mode=0) nutzen
            mode = 0
        else:
            self.setForeground(
                self.textColumn(),
                self.palette().brush(QtGui.QPalette.Normal, QtGui.QPalette.Text)
            )
        self.setIcon(0, GoNode.QIcon(self.iconAlias(mode), disabled))
        return

    def _addDummyChild(self):
        """ adds a DummyChild if configured

        15.06.2023 j.ebert
        """
        if _GONODE_SETTINGS.get(self.__class__.__name__, _GONODE_SETTINGS['GoNode'])[2]:
            dummyNode = GoNode(self, self.DummyNodeID)
            dummyNode.setText(self.textColumn(), self.DummyNodeID)

    def nodeContextMenu(self):
        """
        15.06.2023
        """
        self.log.warning(
            "Method '%s' is superseded by property '%s'\n\t%s",
            'nodeContextMenu()', 'onContextMenu', traceback.format_stack()[-2].strip()
        )
        return self.onContextMenu()

    def nodeCollapsed(self):
        """
        15.06.2023 j.ebert
        """
        self.log.warning(
            "Method '%s' is superseded by property '%s'\n\t%s",
            'nodeCollapsed()', 'onCollapsed', traceback.format_stack()[-2].strip()
        )
        return self.onCollapsed()

    def nodeDoubleClicked(self):
        """
        15.06.2023 j.ebert
        """
        self.log.warning(
            "Method '%s' is superseded by property '%s'\n\t%s",
            'nodeDoubleClicked()', 'onDoubleClicked', traceback.format_stack()[-2].strip()
        )
        return self.onDoubleClicked()

    def nodeExpanded(self):
        """
        15.06.2023 j.ebert
        """
        self.log.warning(
            "Method '%s' is superseded by property '%s'\n\t%s",
            'nodeExpanded()', 'onExpanded', traceback.format_stack()[-2].strip()
        )
        return self.onExpanded()

def main():
    pass

if __name__ == '__main__':
    main()
