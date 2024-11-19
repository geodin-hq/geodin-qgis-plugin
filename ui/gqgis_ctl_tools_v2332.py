""" Controls of maptool 'Hotlink' and tool 'Selection'

Classes:
    GQgis_Act_LayersReload      - QAction to reload layers into QComboBox (GQgis_Cbo_Layers)
    GQgis_Act_ToolHotlink       - QAction of maptool 'Hotlink' to identify object in GOM
    GQgis_Act_ToolSelection     - QAction of tool 'Selection' to create selection groups in GOM
    GQgis_Cbo_Layers            - QComboBox to select GeODin plugin layer
    GQgis_MapToolHotlink        - QgsMapToolIdentifyFeature to identify object in GOM

15.08.2023 j.ebert
"""
import datetime
import json
from pathlib import Path

CONTEXT_RES = "GQgis_Act"
"""context for resource translation of QWidgets"""

from GeODinQGIS.ui.gqgis_bas import *
from GeODinQGIS import (
    app
)
from GeODinQGIS.dm.database import GoDatabase
import GeODinQGIS.gx as gx
import qgis.gui


class GQgis_Act_LayersReload(QtWidgets.QAction, GQgis_Bas_Widget):
    """ QAction to testing

    09.08.2023 j.ebert
    """
    # seealso: https://docs.qgis.org/3.4/en/docs/pyqgis_developer_cookbook/canvas.html#writing-custom-map-tools
    def __init__(self, parent=None, slot=None):
        # init QtWidgets.QAction here to set parent
        # (QAction.Text will be set in translateUi())
        QtWidgets.QAction.__init__(self, "DummyText", parent)
        GQgis_Bas_Widget.__init__(self)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("")
        self._parent = parent
        self._context = CONTEXT_RES
        # set up QAction
        self.setObjectName(self.__class__.__name__)
        self.setIcon(self.QIcon("gLyrsReload"))
        if slot:
            self.triggered.connect(slot)
        else:
            self.triggered.connect(self.execute)
        # translate QAction
        self.translateUi()
        # register QAction for translation
        res.Ui.append(self)

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        self.setText(self.trans("Update layer selection"))
        self.setToolTip(self.trans("Update layer selection for GeODin plugin tools"))

    def updateUi(
        self,
        widget=None             # Parent QWidget that is activated/deactivated
    ):
        """updates QWidget of this QAction

        args:
            widget (QWidget)    - QWidget that is activated/deactivated

        03.05.2021 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        enabled = app.isConnected()
        if (
            isinstance(widget, QtWidgets.QWidget) and
            (widget.isEnabled() != enabled)
        ):
            widget.setEnabled(enabled)
        return

    def execute(self):
        GQgis_Cbo_Layers.instance().reloadGoLayers()


class GQgis_Act_ToolHotlink(QtWidgets.QAction, GQgis_Bas_Widget):
    """ QAction GeODin plugin tool 'Hotlink'

    07.08.2023 j.ebert
    """

    def __init__(self, parent=None, slot=None):
        # init QtWidgets.QAction here to set parent
        # (QAction.Text will be set in translateUi())
        QtWidgets.QAction.__init__(self, "DummyText", parent)
        GQgis_Bas_Widget.__init__(self)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("")
        self._parent = parent
        self._context = CONTEXT_RES
        # set up QAction
        self.setObjectName(self.__class__.__name__)
        self.setIcon(self.QIcon("gToolHotlink"))
        # init settings for QgsMapTool
        self.setCheckable(True)
        self.triggered.connect(self.execute)
        self.canvas = qgis.utils.iface.mapCanvas()
        self.mapTool = GQgis_MapToolHotlink(self.canvas)
        self.mapTool.setAction(self)
        # translate QAction
        self.translateUi()
        # register QAction for translation
        res.Ui.append(self)

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        self.setText(self.trans("Select object"))
        self.setToolTip(self.trans("Select object"))

    def updateUi(
        self,
        widget=None             # Parent QWidget that is activated/deactivated
    ):
        """updates QWidget of this QAction

        args:
            widget (QWidget)    - QWidget that is activated/deactivated

        03.05.2021 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        enabled = app.isConnected()
        if (
            isinstance(widget, QtWidgets.QWidget) and
            (widget.isEnabled() != enabled)
        ):
            if (not enabled) and self.mapTool.isActive():
                self.mapTool.deactivate()
            widget.setEnabled(enabled)
        return

    def execute(self):
        self.canvas.setMapTool(self.mapTool)


class GQgis_Act_ToolSelection(QtWidgets.QAction, GQgis_Bas_Widget):
    """ QAction to testing

    09.08.2023 j.ebert
    """
    def __init__(self, parent=None, slot=None):
        # init QtWidgets.QAction here to set parent
        # (QAction.Text will be set in translateUi())
        QtWidgets.QAction.__init__(self, "DummyText", parent)
        GQgis_Bas_Widget.__init__(self)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("")
        self._parent = parent
        self._context = CONTEXT_RES
        # set up QAction
        self.setObjectName(self.__class__.__name__)
        self.setIcon(self.QIcon("gToolSelection"))
        if slot:
            self.triggered.connect(slot)
        else:
            self.triggered.connect(self.execute)
        # translate QAction
        self.translateUi()
        # register QAction for translation
        res.Ui.append(self)
        # GoLayers QComboBox referenzieren
        self._GoLyr= None
        self._GoLyrAttrName = ""
        self._GoLyrQry = None
        self._GoLyrText = ""
        self.cboLayers().currentIndexChanged.connect(self.onGoLyrChanged)


    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        self.setText(self.trans("Create object group"))
        self.setToolTip(self.trans("Create object group"))

    def updateUi(
        self,
        widget=None             # Parent QWidget that is activated/deactivated
    ):
        """updates QWidget of this QAction

        args:
            widget (QWidget)    - QWidget that is activated/deactivated

        03.05.2021 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        enabled = app.isConnected()
        if (
            isinstance(widget, QtWidgets.QWidget) and
            (widget.isEnabled() != enabled)
        ):
            widget.setEnabled(enabled)
        return

    @property
    def GoLyr(self):
        return self._GoLyr

    @property
    def GoLyrAttrName(self):
        return self._GoLyrAttrName

    @property
    def GoLyrQry(self):
        return self._GoLyrQry

    @property
    def GoLyrText(self):
        return self._GoLyrText

    @property
    def QSleepTime(self):
        """timer in millisecond

        02.08.2023 j.ebert
        """
        return 100

    def cboLayers(self):
        return GQgis_Cbo_Layers.instance()

    def onGoLyrChanged(self, val):
        QtCore.QTimer.singleShot(self.QSleepTime, self.updateGoLyr)
        return

    def execute(self):
        self.log.log(gqc._LOG_TRACE,"TRACE")
        try:
            # FeatureIds (INVIDs) der selektierten Feature ermitteln...
            if self.GoLyr.selectedFeatureCount() == 0:
                raise gqb.GxToolError("Features not selected in layer '%s'", self.GoLyrText)
            lyrFIds = [row.attribute(self.GoLyrAttrName) for row in self.GoLyr.selectedFeatures()]
            self.log.debug(
                "Layer  %sn\tSelected features (Attr '%s')\n\t%s",
                self.GoLyrText, self.GoLyrAttrName,
                json.dumps(lyrFIds, indent=4).replace("\n", "\n\t")
            )
            # GeODin-Methode 'createObjectSelection' ausführen...
            gx.gApp.createObjectSelection(self.GoLyrQry, lyrFIds)
        except (gqb.GxDDXException, gqb.GxToolError) as exc:
            self.log.error(exc.msg(), exc_info=True)
            GQgis_MsgBox.error(self._parent,self.text(), exc.msg())
            # Layer in TOC selektieren...
            # 08/2023 j.ebert, Achtung ggf. exitiert der Layer nicht!
            if self.GoLyr:
                try:
                    qgis.utils.iface.layerTreeView().setCurrentLayer(self.GoLyr)
                except:
                    self.log.debug(
                        "Layer could not be activated in the TOC...\n\t%s (LayerId '%s')",
                        self.GoLyrText, self.GoLyr.id()
                    )
        except:
            self.log.critical("Unkown error on 'Create object group'", exc_info=True)
            GQgis_MsgBox.critical(
                self._parent,
                self.text(),
                "Unkown error on 'Create object group'"
            )

    def updateGoLyr(self):
        self.log.log(gqc._LOG_TRACE,"TRACE")
        qActEnabled = True
        qActToolTip = ""
        if not self.cboLayers().GoLyrExc:
            qActToolTip = self.cboLayers().GoLyrQry.LongLabel
            self._GoLyr = self.cboLayers().GoLyr
            self._GoLyrAttrName = self.cboLayers().GoLyrAttrName
            self._GoLyrQry = self.cboLayers().GoLyrQry
            self._GoLyrText = self.cboLayers().GoLyrText
        else:
            qActEnabled = False
            qActToolTip = self.cboLayers().GoLyrExc.msg()
            self.log.debug(self.cboLayers().GoLyrExc.msg())
            self._GoLyr= None
            self._GoLyrAttrName = ""
            self._GoLyrQry = None
            self._GoLyrText = ""

        self.setToolTip(qActToolTip)
        if (self.isEnabled() != qActEnabled):
            self.setEnabled(qActEnabled)
        return


class GQgis_Cbo_Layers(QtWidgets.QComboBox, GQgis_Bas_Widget):
    """QComboBox to select GeODin Plugin layer

    08.08.2023 j.ebert
    """

    _instance = None
    """singleton instance from this class connected current QgsProject

    10.08.2023 j.ebert
    """
    def __init__(
        self,
        parent
    ):
        super().__init__()
##        QtWidgets.QComboBox.__init__(self, parent)
##        GQgis_Bas_Widget.__init__(self)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("")
        self._context = CONTEXT_RES
        # QtWidgets.QComboBox initialisieren...
        self.setMinimumContentsLength(36)
##        self.setPlaceholderText('Select GeODin layer')
##        self.setPlaceholderText(self.trans('Select GeODin Plugin layer'))
        self.currentIndexChanged.connect(self.onGoLyrChanged)
        # Initialisierung
        self._text = 'Select Layer'
        self._QgsProj = qgis.core.QgsProject.instance()
        self._QgsRoot = self._QgsProj.layerTreeRoot()
        self._DDXData = ""
        """DDX DataFolder (str)"""
        self._GoDBPrefix = GoDatabase.prefix()
        """GoDatabas Prefix (str)"""
        self._GoLyrs = []
        """GoLayers (list(tuple(lyrId (str), longName (str), sortText (str), lyr (QgsVectorLayer))))"""
        self._GoLyrPrms = (None, None, None, "", "", "")
        """GoLayer parameters (tuple( exc, qry, lyr, lyrId, lyrText, lyrAttrName))"""

        self._connect()

    @property
    def GoLyr(self):
        """current layer/QgsVectorLayer

        15.08.2023 j.ebert
        """
        return self._GoLyrPrms[2]

    @property
    def GoLyrAttrName(self):
        """Attribute in current layer to identify feature

        15.08.2023 j.ebert
        """
        return self._GoLyrPrms[5]

    @property
    def GoLyrExc(self):
        """Exception message from current layer

        15.08.2023 j.ebert
        """
        return self._GoLyrPrms[0]

    @property
    def GoLyrId(self):
        """ID of the current layer/QgsVectorLayer (QCombobox current data)

        15.08.2023 j.ebert
        """
        return self._GoLyrPrms[3]

    @property
    def GoLyrQry(self):
        """Query/GoQuery of the current layer

        15.08.2023 j.ebert
        """
        return self._GoLyrPrms[1]

    @property
    def GoLyrText(self):
        """Long name of the current layer (QCombobox current text)

        15.08.2023 j.ebert
        """
        return self._GoLyrPrms[4]

    @property
    def QSleepTime(self):
        """timer in millisecond

        02.08.2023 j.ebert
        """
        return 100

    def currentGoLayer(self):
        """
        returns:
            data (tuple)        - (GoLayerId (str), GoLayerLongName (str), GoLayer (QgsVectorLayer))

        15.08.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        exc = None
        lyrId = self.currentData()
        lyrText = self.currentText()
        lyr = None
        lyrAttrName = 'INVID'
        if not lyrId:
            exc = gqb.GxToolError("GeODin layer not selected")
        else:
            lyr = qgis.core.QgsProject.instance().mapLayers().get(lyrId)
            if not lyr:
                exc = gqb.GxToolError("GeODin layer not found  by ID '%s'", lyrId)
            elif lyrAttrName not in [fld.name() for fld in lyr.fields()]:
                exc = gqb.GxToolError("Field '%s' not found in layer '%s'", lyrAttrName, lyrText)
        return exc, lyr, lyrId, lyrText, lyrAttrName

    def currentGoQuery(self):
        """
        returns:
            data (tuple)        - exc, qry, lyr, lyrId, lyrText, lyrAttrName
                                    exc (GQgisException)
                                    qry (GoQuery)
                                    lyr (QgsVectorLayer)
                                    lyrId (str)
                                    lyrText (str)
                                    lyrAttrName (str)

        15.08.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        exc, lyr, lyrId, lyrText, lyrAttrName = self.currentGoLayer()
        qry = None
        if not exc:
            # GoQuery ermitteln...
            lyrDataSource = lyr.source().split('|')[0]
            exc, qry = app.DDX.findQueryByDataSource(lyrDataSource)
        if exc:
            self.log.debug(exc.msg())
        else:
            self.log.debug(
                "Layer ID       %s\n\tLayer LongName %s\n\tLayer AttrName %s\n\tQuery          %s",
                lyrId, lyrText, lyrAttrName, str(qry)
            )
        return exc, qry, lyr, lyrId, lyrText, lyrAttrName

    @classmethod
    def instance(
        cls,
        parent=None
    ):
        """singleton instance from this class connected current QgsProject

        10.08.2023 j.ebert
        """
        # 08/2023 j.ebert, Achtung folgende if-Expression genau so und nicht anders!
        if cls._instance is None:
            cls._instance = cls(parent)
        return cls._instance

    def onGoLyrChanged(self):
        self.log.log(gqc._LOG_TRACE,"TRACE")
        self._GoLyrPrms = self.currentGoQuery()
        self.log.debug(str(self._GoLyrPrms))
        if not self.GoLyrExc:
            self.setToolTip("")
        elif self.count() == 0:
            # 08/2023 j.ebert, Anmerkung
            #   Wenn kein GoLayer existiert (z. B. beim Beenden von QGIS),
            #   dann keine Fehlermeldsung/MessageBox anzeigen
            self.setToolTip("")
        else:
            self.setToolTip(self.GoLyrExc.msg())
            self.log.error(self.GoLyrExc.msg())
            GQgis_MsgBox.error(self.parentWidget(), self._text, self.GoLyrExc.msg())
        return

    def onLayerRemoved(
        self,
    ):
        self.log.log(gqc._LOG_TRACE,"TRACE")

    def onLayerWasAdded(
        self,
        lyr
    ):
        # void QgsProject::layerWasAdded(QgsMapLayer * layer) - signal
        #   https://api.qgis.org/api/classQgsProject.html#a4405ac8f69192afdef3fdba9eaadc623
        self.log.log(gqc._LOG_TRACE,"TRACE")


    def onLayersAdded(
        self,
        lyrs                    # QList< QgsMapLayer * > & layers
    ):
        # void QgsProject::layersAdded(const QList< QgsMapLayer * > & layers) - signal
        #   https://api.qgis.org/api/classQgsProject.html#ae57b2d2f9bbed7d3c84d7d5a1d8ed8e0
        # 08/2023 j.ebert, Probleme bei der Synchronisation mit QgsProject.layerTreeRoot()
        #   Event-Rountine wird ausgeführt, aber neue Layer werden in layerTreeRoot nicht gefunden.
        QtCore.QTimer.singleShot(self.QSleepTime, lambda: self._addLayers(lyrs))

    def onLayersRemoved(
        self,
        lyrIds                  # QStringList & layerIds
    ):
        # void QgsProject::layersRemoved(const QStringList & layerIds) - signal
        #   https://api.qgis.org/api/classQgsProject.html#a0eb37ca99c74c28e445674768d6f2d21
        self.log.log(gqc._LOG_TRACE,"TRACE")
        self.log.debug("Removed layer IDs: %s", json.dumps(lyrIds, indent=4).replace("\n", "\n\t"))
        goLyrIds = [goLyr[0] for goLyr in self._GoLyrs]
        curLyrIds = [lyrId for lyrId in lyrIds if lyrId in goLyrIds]
        if curLyrIds:
            self.log.debug(
                "Remove GoLayers with IDs: %s",
                json.dumps(curLyrIds, indent=4).replace("\n", "\n\t")
            )
            for curLyrId in curLyrIds:
                curIdx = [goLyr[0] for goLyr in self._GoLyrs].index(curLyrId)
                self._GoLyrs.pop(curIdx)
            self._updateCboItems()


    def reinit(self):
        """Reinitialises this QComboBox

        10.08.2023 j.ebert
        """

    def reloadGoLayers(self):
        """reloads GeODin layers

        10.08.2023 j.ebert
        """
        # DDX DataFolder aktualisieren
        self._DDXData = app.DDXData
        # QgsVectorLayer (valid QgsVectorlayer) listen
        vlyrs = [
            lyr for lyr in self._QgsProj.mapLayers().values() if (
                isinstance(lyr, qgis.core.QgsVectorLayer) and lyr.isValid()
            )
        ]
        # GoLayers aktualisieren...
        self._GoLyrs = []
        for lyr in vlyrs:
            goLyr = self._convertVectorLayer(lyr)
            if goLyr:
                self.log.debug("Append layer '%s' ", lyr.name())
                self._GoLyrs.append(goLyr)
            else:
                self.log.debug("Ignore layer '%s' ", lyr.name())
        # QCombobox Items aktualiseren
        self._updateCboItems()

    def _addLayers(
        self,
        lyrs
    ):
        self.log.log(gqc._LOG_TRACE,"TRACE")
        oldCntGoLyrs = len(self._GoLyrs)
        for lyr in lyrs:
            goLyr = self._convertVectorLayer(lyr)
            if goLyr:
                self.log.debug("Append layer '%s' ", lyr.name())
                self._GoLyrs.append(goLyr)
            else:
                self.log.debug("Ignore layer '%s' ", lyr.name())
        if oldCntGoLyrs < len(self._GoLyrs):
            self._reinitGoLayers()
            self._updateCboItems()

    def _connect(self):
##        self._QgsProj.layerRemoved.connect(self.onLayerRemoved)
##        self._QgsProj.layerWasAdded.connect(self.onLayerWasAdded)
        self._QgsProj.layersAdded.connect(self.onLayersAdded)
        self._QgsProj.layersRemoved.connect(self.onLayersRemoved)

    def _convertVectorLayer(
        self,
        lyr,                    # QgsVectorLayer
    ):
        """Converts argument 'lyr' to a GoLayer if possible

        returns:
            None                if arg 'lyr' is not a QgsVectorLayer based on current DDX
            GoLayer (tuple)     if arg 'lyr' is a QgsVectorLayer based on current DDX
                                tuple(lyrId (str), longName (str), sortText (str), lyr (QgsVectorLayer))

        09.08.2023 j.ebert
        """
        goLyr = None
        try:
            if (
                isinstance(lyr, qgis.core.QgsVectorLayer) and
                lyr.isValid() and
                (lyr.id() not in [goLyr[0] for goLyr in self._GoLyrs])
            ):
                lyrSource = lyr.source().split('|')[0]
                lyrSrcPath = Path(lyr.source().split('|')[0])
                self.log.debug(
                    "DDXData %s\n\tSourcs  %s\n\t\tIf-Expr (%s and %s and %s)",
                    self._DDXData,
                    lyrSource,
                    str(lyrSrcPath.parents[1].samefile(self._DDXData)),
                    str(lyrSrcPath.parent.stem.startswith(self._GoDBPrefix)),
                    str(lyrSrcPath.stem.startswith(lyrSrcPath.parent.stem))
                )
                if (
                    lyrSrcPath.parents[1].samefile(self._DDXData) and
                    lyrSrcPath.parent.stem.startswith(self._GoDBPrefix) and
                    lyrSrcPath.stem.startswith(lyrSrcPath.parent.stem)
                ):
                    lyrNode = self._QgsRoot.findLayer(lyr)
                    lyrLongName = lyrNode.name()
                    lyrSortText = "%04d" % lyrNode.parent().children().index(lyrNode)
                    grpNode = lyrNode.parent()
                    while grpNode.parent() is not None:
                        lyrLongName = "%s\%s" % (grpNode.name(), lyrLongName)
                        lyrSortText = "%04d %s" % (
                            grpNode.parent().children().index(grpNode), lyrSortText
                        )
                        grpNode = grpNode.parent()
                    goLyr = (lyr.id(), lyrLongName, lyrSortText, lyr)
        except FileNotFoundError as exc:
            self.log.debug("Excepted FileNotFoundError: '%s'", exc.filename)
        except:
            self.log.error("Convert QgsLayer '%s' faild", lyr.id(), exc_info=True)
        return goLyr

    def _disconnect(self):
##        self._QgsProj.layerRemoved.disconnect(self.onLayerRemoved)
##        self._QgsProj.layerWasAdded.disconnect(self.onLayerWasAdded)
        self._QgsProj.layersAdded.disconnect(self.onLayersAdded)
        self._QgsProj.layersRemoved.disconnect(self.onLayersRemoved)

    def _reinitGoLayers (self):
        lyrs = [goLyr[-1] for goLyr in self._GoLyrs]
        for idx, lyr in enumerate(lyrs):
            lyrNode = self._QgsRoot.findLayer(lyr)
            lyrLongName = lyrNode.name()
            lyrSortText = "%04d" % lyrNode.parent().children().index(lyrNode)
            grpNode = lyrNode.parent()
            while grpNode.parent() is not None:
                lyrLongName = "%s\%s" % (grpNode.name(), lyrLongName)
                lyrSortText = "%04d %s" % (
                    grpNode.parent().children().index(grpNode), lyrSortText
                )
                grpNode = grpNode.parent()
            self._GoLyrs[idx] = (lyr.id(), lyrLongName, lyrSortText, lyr)

    def _updateCboItems(self):
        # GoLayers sortieren...
        self._GoLyrs.sort(key = lambda row : row[2])
        # GoLayers debuggen...
        if self.log.level <= gqc._LOG_DATA:
            logRows = [str(row[1]) for row in self._GoLyrs]
            self.log.log(gqc._LOG_DATA,
                "GoLayers (longName): \n\t%s", json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
            logRows = [str(row[2]) for row in self._GoLyrs]
            self.log.log(gqc._LOG_DATA,
                "GoLayers (sortText): \n\t%s", json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
        # QCombobox Items aktualiseren
        oldData = self.currentData()
        self.clear()
        newIdx = None
        for idx, goLyr in enumerate(self._GoLyrs):
            self.addItem(goLyr[1], goLyr[0])
            if ((oldData is not None) and (goLyr[0] == oldData)):
                newIdx = idx
        if newIdx is not None:
            self.setCurrentIndex(newIdx)
        return


class GQgis_MapToolHotlink(qgis.gui.QgsMapToolIdentifyFeature):
    """QgsMapToolIdentifyFeature to identify object in GeODin object manager

    15.08.2023 j.ebert
    """

    def __init__(
        self,
        canvas,                 # QgsMapCanvas
        vl=None                 # QgsVectorLayer
    ):
        super().__init__(canvas, vl)
        self.log  = logging.getLogger(f"{gqc._LOG_PARENTS}{self.__class__.__name__}")
        self.log.log(gqc._LOG_TRACE,"")
        # QgsMapToolIdentifyFeature initialisieren...
        self.featureIdentified.connect(self.onFeatureIdentified)
        # GoLayers QComboBox referenzieren
        self.cboLayers().currentIndexChanged.connect(self.onGoLyrChanged)
        self._GoLyrAttrName = ""
        self._GoLyrPrmsSelectObject = {}

    @property
    def GoLyrAttrName(self):
        return self._GoLyrAttrName

    @property
    def GoLyrPrmsSelectObject(self):
        return self._GoLyrPrmsSelectObject

    @property
    def QSleepTime(self):
        """timer in millisecond

        02.08.2023 j.ebert
        """
        return 100

    def cboLayers(self):
        return GQgis_Cbo_Layers.instance()

    def onGoLyrChanged(self, val):
        QtCore.QTimer.singleShot(self.QSleepTime, self.updateGoLyr)
        return

    def onFeatureIdentified(self, feature):
        self.log.log(gqc._LOG_TRACE,"TRACE")
        self.log.debug(str(self.GoLyrPrmsSelectObject))
        if self.GoLyrPrmsSelectObject:
            self.log.debug("...")
            try:
                self.GoLyrPrmsSelectObject['ObjectID'] = feature.attribute(self.GoLyrAttrName)
                self.log.debug(str(self.GoLyrPrmsSelectObject))
                gx.gApp.selectObject(self.GoLyrPrmsSelectObject)
            except gqb.GQgisException as exc:
                self.log.error(exc.msg(), exc_info=True)
##                GQgis_MsgBox.error(self._parent, self.text(), exc.msg())
                GQgis_MsgBox.error(None, 'Hotlink Tool', exc.msg())
                # Layer in TOC selektieren...
                # 08/2023 j.ebert, Achtung ggf. exitiert der Layer nicht!
                if lyr:
                    try:
                        qgis.utils.iface.layerTreeView().setCurrentLayer(lyr)
                    except:
                        self.log.debug(
                            "Layer could not be activated in the TOC...\n\t%s (LayerId '%s')",
                            lyrText, lyrId
                        )
            except:
                self.log.critical("Unkown error on 'Identify Object'", exc_info=True)
##                GQgis_MsgBox.critical(
##                    self._parent,
##                    self.text(),
##                    "Unkown error on 'Identify Object'"
##                )
                GQgis_MsgBox.critical(
                    None,
                    'Hotlink Tool',
                    "Unkown error on 'Identify Object'"
                )

    def updateGoLyr(self):
        self.log.log(gqc._LOG_TRACE,"TRACE")
        qActEnabled = True
        qActToolTip = ""
        if not self.cboLayers().GoLyrExc:
            qActToolTip = self.cboLayers().GoLyrQry.LongLabel
            self._GoLyrAttrName = self.cboLayers().GoLyrAttrName
            self._GoLyrPrmsSelectObject = self.cboLayers().GoLyrQry.prmsSelectObject()
            # MapTool aktualisieren und ggf. erneut aktivieren(?)...
            self.setLayer(self.cboLayers().GoLyr)
##            if self.isActive():
##                self.activate()
        else:
            qActEnabled = False
            qActToolTip = self.cboLayers().GoLyrExc.msg()
            self.log.debug(self.cboLayers().GoLyrExc.msg())
            self._GoLyrAttrName = ""
            self._GoLyrPrmsSelectObject = {}
            self.deactivate()

        if self.action():
            self.action().setToolTip(qActToolTip)
            if (self.action().isEnabled() != qActEnabled):
                self.action().setEnabled(qActEnabled)
        return

def main():
    pass

if __name__ == '__main__':
    main()
