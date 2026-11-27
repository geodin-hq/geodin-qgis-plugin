"""
classes:
    GoNode                      - base node/bas class of ViewModel/QTreeWidgetItem

globals:
    _GONODE_SETTINGS (dict)     - settings for nodes inherited from the base class GoNode

01.06.2023 j.ebert
"""
import logging
import os
import traceback

import qgis.core
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
    plugin,
    GQgis_MsgBox as MsgBox,
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
        self.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicatorWhenChildless)
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

    @property
    def GoLayerPattern(self):
        """Pattern (str) of GoLayer DataSource

        24.07.2024 j.ebert
        """
        raise NotImplementedError(
            "Property '%s.GoLayerPattern' not implemented" % self.__class__.__name__
        )
        return None

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
            icon = QtGui.QIcon(icon.pixmap(QtCore.QSize(32, 32), QtGui.QIcon.Mode.Disabled))
        return icon

    @property
    def QSleepTime(self):
        """timer in millisecond

        24.07.2024 j.ebert (bisher nur GoNodeQuery.QSleepTime)
        """
        # 07/2024 j.ebert, Anmerkung
        #   Property QSleepTime bisher nur in der abgeleiteten Klasse GoNodeQuery, aber
        #   für Methode removeLayers() ist die Property QSleepTime jetzt in allen GoNode-Klassen
        #   notwendig. Daher verschoben in die Basis-Klasse GoNode.
        return 100

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
        # 10/2026: make the expanded node the current (and only) selected item;
        #   setSelected(True) added it to the selection, so several nodes were
        #   selected at the same time and the context menu did not open any more
        if self.treeWidget() is not None:
            self.treeWidget().setCurrentItem(self)
        else:
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
                MsgBox.error(plugin().parent(), 'GeoDin', exc.msg())
            except Exception:
                MsgBox.error(
                    plugin().parent(),
                    'GeoDin',
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
                self.palette().brush(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Text)
            )
            # 06/2023 j.ebert Anmerkung
            #   Wenn QTreeWidgetItem disabled ist/dragestellt wird,
            #   dann IMMER 'normal' Icon ( default, mode=0) nutzen
            mode = 0
        else:
            self.setForeground(
                self.textColumn(),
                self.palette().brush(QtGui.QPalette.ColorGroup.Normal, QtGui.QPalette.ColorRole.Text)
            )
        self.setIcon(0, GoNode.QIcon(self.iconAlias(mode), disabled))
        return

    def listGoLayers(self):
        """returns a QgsVectorLayer/GoLayer list of this GoNode or all its ChildNodes

        24.07.2024 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # https://gis.stackexchange.com/questions/211960/selecting-several-layers-programmatically-using-pyqgis
        lyrs = None
        self.log.log(gqc._LOG_TRACE, self.GoLayerPattern)
        if self.GoLayerPattern:
            # Wenn für diesen GoNode das Attr. GoLayerPattern gesetzt ist,
            # dann GeoDin-Object-Layer listen...
            # - validen/potentiellen GoLayer (QgsVectorLayer, GeoJSON, ...) listen...
            self.log.log(gqc._LOG_TRACE,"")
            mapLyrs = [lyr for lyr in qgis.core.QgsProject.instance().mapLayers().values() if (
                self.validGoLayer(lyr)
            )]
            self.log.debug("\n\t".join(
                [lyr.source().split('|')[0].lower() for lyr in mapLyrs]
            ))
            # - Liste der validen/potentiellen GoLayer prüfen...
            #   07/2024 j.ebert, Anmerkung
            #       Prüfen, ob DataSource dem GoLayerPattern entspricht, funktioniert hier
            #       nur über den String-Vergleich (und nicht mit Path.samefile()).
            #       - GoNodeQuery       - Pattern ist das GeoJSON-File
            #         GoNodeProject     - Pattern enthält nicht den vollständigen GeoJSON-Filenamen
            #         GoNodeDatabase    - Pattern ist das Directory vom GeoJSON-File
            #       - Path(<filename>).samefile() verursacht einen FileNotFoundError, wenn
            #         das Fiel <filename> nicht eixtiert, also bie not Path(<filename>).exists()
            #   07/2024 j.ebert, QGIS 3.22.9-Białowieża
            #       QgsMapLayer.source()    - undefiniert mit os.sep oder mit os.altsep :(
            #                                 (ggf. abhängig davon, ob der Layer beim Öffnen des
            #                                  QGIS-Projektes in diesem bereits existiert hat???)
            #       ... aber damit funktioniert der String-Vergleich nicht, ohne weiteres
##            pattern = str(self.GoLayerPattern).lower()
##            lyrs = [lyr for lyr in mapLyrs if (
##                lyr.source().split('|')[0].lower().startswith(pattern)
##            )]
            pattern = str(self.GoLayerPattern).lower().replace(os.sep, os.altsep)
            lyrs = []
            for lyr in mapLyrs:
                lyrSource = lyr.source().split('|')[0].lower().replace(os.sep, os.altsep)
                if lyrSource.startswith(pattern):
                    lyrs.append(lyr)
            # Liste der  validen/potentiellen GoLayer löschen, damit
            # keine unnötigen Referenzen auf Layer (und damit auf deren DataSource) bestehen
            del mapLyrs
            self.log.debug("\n\t".join(
                [lyr.source().split('|')[0].lower() for lyr in lyrs]
            ))
        self.log.log(gqc._LOG_TRACE,"Done")
        return lyrs

    def removeGoLayers(
        self,
        refresh=False           # refresh mapCanvas (False|True)
        ):
        """deletes all QgsVectorLayer/GoLayer of this GoNode or all its ChildNodes

        return:
            True    if layers were found/deleted in QGIS project
            False   if layers were not found/deleted in QGIS project

        24.07.2024 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        lyrs = self.listGoLayers()
        lyrsFound = bool(lyrs)
        if lyrsFound:
            qgis.core.QgsProject.instance().removeMapLayers([lyr.id() for lyr in lyrs])
            if refresh:
                # wenn Refresh-Option über Argumnet explicit gesetzt ist
                # dann Refresh mapCanvas
                QtWidgets.QApplication.processEvents()
                plugin().iface().mapCanvas().refresh()
        del lyrs
        return lyrsFound

    def validGoLayer(
        self,
        qgsLayer
    ):
        """True if 'qgsLayer' can be a GoLayer (QgsVectorLayer, GeoJSON, ...)

        24.07.2024 j.ebert
        """
        # 07/2024 j.ebert, Anmerkung
        #   Die Methode validGoLayer() bisher nur in der abgeleiteten Klasse GoNodeQuery, aber
        #   für Methode removeGoLayers() ist die Methode validGoLayer() jetzt in allen
        #   GoNode-Klassen notwendig. Daher verschoben in die Basis-Klasse GoNode.
        self.log.log(gqc._LOG_TRACE, "")
        val = False
        if (
            isinstance(qgsLayer, qgis.core.QgsVectorLayer) and
            (qgsLayer.dataProvider().storageType() == 'GeoJSON')
        ):
            try:
                os.stat(qgsLayer.source().split('|')[0])
                # -> Die WindowsPath-Syntax ist richitg und die Layer Source existiert
                # -> Der QgsVectorLayer kann ein GoLayer sein.
                val = True
            except FileNotFoundError:
                # FileNotFoundError: [WinError 3] Das System kann den angegebenen Pfad nicht finden:
                # -> Die WindowsPath-Syntax ist richitg, aber die Layer Source existiert nicht
                # -> Der QgsVectorLayer kann ein GoLayer sein.
                val = True
            except Exception:
                # OSError: [WinError 123] Die Syntax für den Dateinamen, Verzeichnisnamen oder die Datenträgerbezeichnung ist falsch:
                # -> Die WindowsPath-Syntax ist falsch!
                # -> Der QgsVectorLayer kann kein GoLayer sein.
                self.log.warning(
                    "Ignore layer \"%s\"\n\t%s", str(qgsLayer), qgsLayer.source(),
                    exc_info=True
                )
        return val

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
