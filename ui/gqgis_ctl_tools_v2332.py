""" Controls of maptool 'Hotlink' and tool 'Selection'

Classes:
    GQgis_Act_LayersReload      - QAction to reload layers into QComboBox (GQgis_Cbo_Layers)
    GQgis_Act_ToolHotlink       - QAction of maptool 'Hotlink' to identify object in GOM
    GQgis_Act_ToolSelection     - QAction of tool 'Selection' to create selection groups in GOM
    GQgis_Cbo_Layers            - QComboBox to select GeODin plugin layer
    GQgis_MapToolHotlink        - QgsMapToolIdentifyFeature to identify object in GOM

23.04.2024 j.ebert
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


def _goLyrExcText(cbo):
    """reason why there is no valid GeoDin layer in the combo box (10/2026)"""
    exc = cbo.GoLyrExc
    if exc:
        return exc.msg()
    return res.translate(CONTEXT_RES, "No GeoDin layer selected")


def _modeText(mode):
    from GeODinQGIS.ui.gqgis_options import MODE_TEXT
    return MODE_TEXT.get(mode, mode)


def updateGoLayerData(qry, lyr, log, parent=None, title="GeoDinQGIS"):
    """exports the query again from GeoDin and reloads the layer (10/2026)

    as 'Update layer(s)' in the Explorer (vm/query_node.py onLayerUpdate)
    """
    import tempfile
    from pathlib import Path as _Path
    QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CursorShape.WaitCursor))
    try:
        dataPath = _Path(lyr.source().split("|")[0])
        gx.gApp.selectObject(qry)
        with tempfile.TemporaryFile(
            prefix=(dataPath.stem + '_'), suffix=dataPath.suffix, dir=dataPath.parent
        ) as tempFile:
            tempPath = _Path(tempFile.name)
        gx.gApp.exportFeatureCollection(str(tempPath))
        dataPath.write_text(tempPath.read_text())
        tempPath.unlink()
        lyr.reload()
        lyr.triggerRepaint()
        log.info("Layer data updated: %s (%d features)", lyr.name(), lyr.featureCount())
        return True
    except gqb.GQgisException as exc:
        log.error(exc.msg(), exc_info=True)
        QtWidgets.QApplication.restoreOverrideCursor()
        GQgis_MsgBox.error(parent, title, exc.msg())
    except Exception:
        log.critical("Unknown error on 'Update layer'", exc_info=True)
        QtWidgets.QApplication.restoreOverrideCursor()
        GQgis_MsgBox.critical(parent, title, "Unknown error on 'Update layer'")
    finally:
        if QtWidgets.QApplication.overrideCursor() is not None:
            QtWidgets.QApplication.restoreOverrideCursor()
    return False


class _GQgis_ModeMenu:
    """menu (arrow at the toolbar button) with the GeoDin method after the tool (10/2026)

    The class using it sets self._modeTool (TOOL_SELECTION/TOOL_HOTLINK) and
    self._modeTitle (translation key of the tooltip) and implements executeMode(mode).
    """

    def _initModeMenu(self):
        from GeODinQGIS.ui.gqgis_options import TOOL_MODES
        self._modeActions = {}
        menu = QtWidgets.QMenu(self._parent)
        for mode in TOOL_MODES[self._modeTool]:
            action = QtWidgets.QAction(mode, menu)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, m=mode: self.executeMode(m))
            menu.addAction(action)
            self._modeActions[mode] = action
        menu.aboutToShow.connect(self._updateModeMenu)
        self._modeMenu = menu
        self.setMenu(menu)
        return

    def _updateModeMenu(self):
        """texts and check marks of the menu, tooltip with the current mode"""
        if not getattr(self, '_modeActions', None):
            return
        from GeODinQGIS.ui.gqgis_options import afterSelectionMode
        current = afterSelectionMode(self._modeTool)
        for mode, action in self._modeActions.items():
            action.setText(self.trans(_modeText(mode)))
            action.setChecked(mode == current)
        tip = "%s: %s" % (self.trans(self._modeTitle), self.trans(_modeText(current)))
        lyrTip = getattr(self, '_lyrToolTip', "")
        self.setToolTip(f"{tip}\n{lyrTip}" if lyrTip else tip)
        return

    def setLyrToolTip(self, text):
        """tooltip of the GeoDin layer (below the mode)"""
        self._lyrToolTip = text
        self._updateModeMenu()

    def _saveMode(self, mode):
        from GeODinQGIS.ui.gqgis_options import setAfterSelectionMode
        setAfterSelectionMode(self._modeTool, mode)
        self._updateModeMenu()


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
        # self.setToolTip(self.trans("Update layer selection for GeoDin plugin tools"))
        # 10/2026: also updates the data of the selected layer (export from GeoDin)
        self.setToolTip(self.trans("Update layer selection and the data of the selected GeoDin layer"))

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
        # GQgis_Cbo_Layers.instance().reloadGoLayers()
        # 10/2026: reload the layer selection, keep the selected layer and update its data
        cbo = GQgis_Cbo_Layers.instance()
        lyrId = cbo.currentData()
        cbo.reloadGoLayers()
        idx = cbo.findData(lyrId) if lyrId else -1
        if idx >= 0 and idx != cbo.currentIndex():
            cbo.setCurrentIndex(idx)
        if cbo.GoLyr is None or cbo.GoLyrQry is None:
            return
        updateGoLayerData(cbo.GoLyrQry, cbo.GoLyr, self.log, self._parent, self.text())


class GQgis_Act_ToolHotlink(QtWidgets.QAction, GQgis_Bas_Widget, _GQgis_ModeMenu):
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
        # 10/2026: menu (arrow) - GeoDin method after the click (select only / object data /
        #   print and edit graphics), the chosen entry is remembered
        from GeODinQGIS.ui.gqgis_options import TOOL_HOTLINK
        self._modeTool = TOOL_HOTLINK
        self._modeTitle = "Select object"
        self._initModeMenu()
        # translate QAction
        self.translateUi()
        # register QAction for translation
        res.Ui.append(self)

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        self.setText(self.trans("Select object"))
        # self.setToolTip(self.trans("Select object"))    # 10/2026 see _updateModeMenu()
        self._updateModeMenu()

    def executeMode(self, mode):
        """remembers the GeoDin method and activates the Hotlink tool (10/2026)"""
        self._saveMode(mode)
        if self.isEnabled():
            self.setChecked(True)
            self.execute()
        return

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


class GQgis_Act_ToolSelection(QtWidgets.QAction, GQgis_Bas_Widget, _GQgis_ModeMenu):
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
        # if slot:
        #     self.triggered.connect(slot)
        # else:
        #     self.triggered.connect(self.execute)
        # 10/2026: map tool - select the objects in the map (rectangle or click), afterwards
        #   the object selection is created in GeoDin and the function of the menu is executed
        self.setCheckable(True)
        if slot:
            self.triggered.connect(slot)
        else:
            self.triggered.connect(self.activateTool)
        self.canvas = qgis.utils.iface.mapCanvas()
        self.mapTool = GQgis_MapToolSelection(self.canvas, self.onFeaturesSelected)
        self.mapTool.setAction(self)
        # 10/2026: menu (arrow at the toolbar button) - GeoDin method after the selection
        #   (select only / open object data / print and edit graphics); the chosen entry is
        #   executed and remembered for the next click on the button
        from GeODinQGIS.ui.gqgis_options import TOOL_SELECTION
        self._modeTool = TOOL_SELECTION
        self._modeTitle = "Create object group"
        self._initModeMenu()
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
        # self.setToolTip(self.trans("Create object group"))    # 10/2026 see _updateModeMenu()
        self._updateModeMenu()

    def activateTool(self):
        """activates the map tool to select objects in the GeoDin layer (10/2026)"""
        self.updateGoLyr()
        if self.GoLyr is None:
            self.setChecked(False)
            GQgis_MsgBox.error(self._parent, self.text(), _goLyrExcText(self.cboLayers()))
            return
        self.mapTool.setLayer(self.GoLyr)
        self.setChecked(True)
        self.canvas.setMapTool(self.mapTool)
        try:
            # qgis.utils.iface.messageBar().pushInfo(
            #     "GeoDinQGIS",
            #     self.trans("Select objects in layer '%s' (rectangle or click, Shift adds): %s")
            #     % (self.GoLyrText, self.trans(_modeText(self._currentMode())))
            # )
            # 10/2026: short text with word wrap (was cut off in a small QGIS window)
            from GeODinQGIS.ui.gqgis_options import pushMessage
            pushMessage(
                self.trans("Select objects (rectangle or click, Shift adds): %s")
                % self.trans(_modeText(self._currentMode())),
                tooltip=self.GoLyrText
            )
        except Exception:
            pass
        return

    def _currentMode(self):
        from GeODinQGIS.ui.gqgis_options import afterSelectionMode
        return afterSelectionMode(self._modeTool)

    def onFeaturesSelected(self, count):
        """called by the map tool after a selection in the map (10/2026)"""
        if count > 0:
            self.execute()
        else:
            # 11/2026: no feature of the GeoDin layer hit (e.g. click beside the symbol or on
            #   a feature of another layer) - before nothing happened without a notice
            try:
                from GeODinQGIS.ui.gqgis_options import pushMessage
                pushMessage(
                    self.trans("No object of the GeoDin layer '%s' found at this place.")
                    % self.GoLyrText,
                    level="warning"
                )
            except Exception:
                pass
        return

    def executeMode(self, mode):
        """remembers the GeoDin method and activates the map tool (10/2026)"""
        self._saveMode(mode)
        if self.isEnabled():
            self.activateTool()
        return

    def executeMode_v01(self, mode):
        """remembers the GeoDin method after the selection and creates the selection (10/2026)"""
        self._saveMode(mode)
        # execute only if features are selected in the GeoDin layer, else only remember
        self.updateGoLyr()
        self._switchToSelectedGoLayer()
        if self.isEnabled() and self.GoLyr is not None and self.GoLyr.selectedFeatureCount() > 0:
            self.execute()
        else:
            try:
                from GeODinQGIS.ui.gqgis_options import pushMessage
                pushMessage(
                    self.trans("%s - select features in the GeoDin layer and click the button.")
                    % self.trans(_modeText(mode))
                )
            except Exception:
                pass
        return

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
                self.canvas.unsetMapTool(self.mapTool)
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

    def _switchToSelectedGoLayer(self):
        """switches the layer selection to a GeoDin layer with selected features (10/2026)

        If the GeoDin layer of the combo box has no selected features, the active layer of the
        QGIS layer tree (if it is a GeoDin layer with selected features) or otherwise the first
        GeoDin layer with selected features is used (e.g. the same layer was added twice).
        """
        if self.GoLyr is not None and self.GoLyr.selectedFeatureCount() > 0:
            return False
        cbo = self.cboLayers()
        project = qgis.core.QgsProject.instance()
        candidates = []
        try:
            active = qgis.utils.iface.activeLayer()
            if active is not None:
                candidates.append(active.id())
        except Exception:
            pass
        candidates += [cbo.itemData(i) for i in range(cbo.count())]
        for lyrId in candidates:
            idx = cbo.findData(lyrId)
            lyr = project.mapLayers().get(lyrId) if lyrId else None
            if idx < 0 or lyr is None or not hasattr(lyr, 'selectedFeatureCount'):
                continue
            if lyr.selectedFeatureCount() > 0:
                if idx != cbo.currentIndex():
                    self.log.info("Layer selection switched to '%s' (selected features)", cbo.itemText(idx))
                    cbo.setCurrentIndex(idx)
                self.updateGoLyr()
                return True
        return False

    def execute(self):
        self.log.log(gqc._LOG_TRACE,"TRACE")
        try:
            # 10/2026: use the current layer of the combo box (updateGoLyr() is deferred with a
            #   timer) and give a clear message if there is no valid GeoDin layer - before:
            #   AttributeError 'NoneType' object has no attribute 'selectedFeatureCount'
            #   (e.g. layer of another DDX or of a database that is not in the current DDX)
            self.updateGoLyr()
            # 10/2026: GeoDin layer with selected features (active layer or other GeoDin layer)
            self._switchToSelectedGoLayer()
            if self.GoLyr is None:
                cboExc = self.cboLayers().GoLyrExc
                raise gqb.GxToolError("%s", _goLyrExcText(self.cboLayers()))
            # FeatureIds (INVIDs) der selektierten Feature ermitteln...
            if self.GoLyr.selectedFeatureCount() == 0:
                # raise gqb.GxToolError("Features not selected in layer '%s'", self.GoLyrText)
                raise gqb.GxToolError(
                    self.trans("No features selected in layer '%s'.\nSelect the objects in QGIS first (e.g. with 'Select Features by Area or Single Click')."),
                    self.GoLyrText
                )
            lyrFIds = [row.attribute(self.GoLyrAttrName) for row in self.GoLyr.selectedFeatures()]
            self.log.debug(
                "Layer  %sn\tSelected features (Attr '%s')\n\t%s",
                self.GoLyrText, self.GoLyrAttrName,
                json.dumps(lyrFIds, indent=4).replace("\n", "\n\t")
            )
            # GeODin-Methode 'createObjectSelection' ausführen...
            # gx.gApp.createObjectSelection(self.GoLyrQry, lyrFIds)
            # 10/2026: GeoDin method of the menu (arrow) is passed to CreateObjectSelection,
            #   GeoDin executes it at the new object selection (MethodID -1 = select only)
            from GeODinQGIS.ui.gqgis_options import selectionMethod, warnMethodFailed, TOOL_SELECTION
            methodID, methodPrms = selectionMethod(TOOL_SELECTION)
            try:
                gx.gApp.createObjectSelection(
                    self.GoLyrQry, lyrFIds, methodID=methodID, methodPrms=methodPrms
                )
            except gqb.GxGComException as exc:
                # selection created, but the method failed (e.g. cross section with one object)
                if methodID == -1:
                    raise
                warnMethodFailed(TOOL_SELECTION, exc, self.log)
        # 10/2026: + GxGComError (e.g. GeoDin busy) - before: "Unknown error on 'Create object group'"
        except (gqb.GxDDXException, gqb.GxToolError, gqb.GxGComError) as exc:
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
        # 10/2026: also without GeoDin layer (empty combo box: GoLyrExc and GoLyrQry None)
        if not self.cboLayers().GoLyrExc and self.cboLayers().GoLyrQry is not None:
            qActToolTip = self.cboLayers().GoLyrQry.LongLabel
            self._GoLyr = self.cboLayers().GoLyr
            self._GoLyrAttrName = self.cboLayers().GoLyrAttrName
            self._GoLyrQry = self.cboLayers().GoLyrQry
            self._GoLyrText = self.cboLayers().GoLyrText
        else:
            qActEnabled = False
            qActToolTip = _goLyrExcText(self.cboLayers())
            self.log.debug(qActToolTip)
            self._GoLyr= None
            self._GoLyrAttrName = ""
            self._GoLyrQry = None
            self._GoLyrText = ""

        # 10/2026: layer of the map tool
        if getattr(self, 'mapTool', None) is not None:
            self.mapTool.setLayer(self._GoLyr)
            if self._GoLyr is None and self.mapTool.isActive():
                self.canvas.unsetMapTool(self.mapTool)
        # self.setToolTip(qActToolTip)   # 10/2026: tooltip with mode, see _updateModeMenu()
        self.setLyrToolTip(qActToolTip)
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
            exc = gqb.GxToolError("GeoDin layer not selected")
        else:
            lyr = qgis.core.QgsProject.instance().mapLayers().get(lyrId)
            if not lyr:
                exc = gqb.GxToolError("GeoDin layer not found  by ID '%s'", lyrId)
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
                    "DDXData %s\n\tSourcs  %s\n\t\tIf-Expr (%s and %s and %s and %s)",
                    self._DDXData,
                    lyrSource,
                    str(lyrSrcPath.parents[1].samefile(self._DDXData)),
                    str(lyrSrcPath.parent.stem.startswith(self._GoDBPrefix)),
                    str(lyrSrcPath.stem.startswith(lyrSrcPath.parent.stem)),
                    # 07/2024 j.ebert, Bugfixing: Layer aus verwaisten DatabaseFolder ignorieren
                    str(app.DDX.hasValidDbRef(str(lyrSrcPath)))
                )
                if (
                    lyrSrcPath.parents[1].samefile(self._DDXData) and
                    lyrSrcPath.parent.stem.startswith(self._GoDBPrefix) and
                    lyrSrcPath.stem.startswith(lyrSrcPath.parent.stem) and
                    # 07/2024 j.ebert, Bugfixing: Layer aus verwaisten DatabaseFolder ignorieren
                    app.DDX.hasValidDbRef(str(lyrSrcPath))
                ):
                    lyrNode = self._QgsRoot.findLayer(lyr)
                    lyrLongName = lyrNode.name()
                    lyrSortText = "%04d" % lyrNode.parent().children().index(lyrNode)
                    grpNode = lyrNode.parent()
                    while grpNode.parent() is not None:
                        lyrLongName = "%s\\%s" % (grpNode.name(), lyrLongName)
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
                lyrLongName = "%s\\%s" % (grpNode.name(), lyrLongName)
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
        # GoLayer Porpteries initialisieren...
        # (Properties werden in onGoLyrChanged() gesetzt nach GQgis_CBo_Layers.currentIndexChanged)
        self._GoLyr = None                  # akt. QgsLayer vom MapTool
        self._GoLyrAttrName = ""            # Attributname des QgsLayer mit INVID
        self._GoLyrPrmsSelectObject = {}    # SelectObject-Parmater für GeoDin-Schnittstelle
        # QComboBox-Event/GQgis_CBo_Layers.currentIndexChanged verbinden
        self.cboLayers().currentIndexChanged.connect(self.onGoLyrChanged)
        # QgsMapToolIdentifyFeature initialisieren...
        self.featureIdentified.connect(self.onFeatureIdentified)

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
        """
        23.04.2024 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        self.log.debug(str(self.GoLyrPrmsSelectObject))
        if self.GoLyrPrmsSelectObject:
            self.log.debug("...")
            try:
                self.GoLyrPrmsSelectObject['ObjectID'] = feature.attribute(self.GoLyrAttrName)
                self.log.debug(str(self.GoLyrPrmsSelectObject))
                gx.gApp.selectObject(self.GoLyrPrmsSelectObject)
                # 10/2026: GeoDin method after the selection (menu of the 'Selection' button)
                from GeODinQGIS.ui.gqgis_options import runAfterSelection, TOOL_HOTLINK
                runAfterSelection(TOOL_HOTLINK, self.log)
            except gqb.GQgisException as exc:
                self.log.error(exc.msg(), exc_info=True)
                GQgis_MsgBox.error(None, 'Hotlink Tool', exc.msg())
                # Layer in TOC selektieren...
                # 08/2023 j.ebert, Achtung ggf. exitiert der Layer nicht!
                if self._GoLyr:
                    try:
                        qgis.utils.iface.layerTreeView().setCurrentLayer(self._GoLyr)
                    except:
                        self.log.debug(
                            "Layer could not be activated in the TOC...\n\t%s (LayerId '%s')",
                            self._GoLyr.name(), self._GoLyr.id()
                        )
            except:
                self.log.critical("Unkown error on 'Identify Object'", exc_info=True)
                GQgis_MsgBox.critical(
                    None,
                    'Hotlink Tool',
                    "Unkown error on 'Identify Object'"
                )

    def updateGoLyr(self):
        """
        23.04.2024 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        qActEnabled = True
        qActToolTip = ""
        # 10/2026: also without GeoDin layer (empty combo box: GoLyrExc and GoLyrQry None)
        if not self.cboLayers().GoLyrExc and self.cboLayers().GoLyrQry is not None:
            qActToolTip = self.cboLayers().GoLyrQry.LongLabel
            # 04/2024 j.ebert, QgsLayer speichern, den das QgsMapToolIdentifyFeature nutzt
            #                  Der Layer ist write only (QgsMapToolIdentifyFeaturesetLayer())!? :(
            self._GoLyr = self.cboLayers().GoLyr
            self._GoLyrAttrName = self.cboLayers().GoLyrAttrName
            self._GoLyrPrmsSelectObject = self.cboLayers().GoLyrQry.prmsSelectObject()
            # MapTool aktualisieren und ggf. erneut aktivieren(?)...
            self.setLayer(self._GoLyr)
##            if self.isActive():
##                self.activate()
        else:
            qActEnabled = False
            qActToolTip = _goLyrExcText(self.cboLayers())
            self.log.debug(qActToolTip)
            self._GoLyrAttrName = ""
            self._GoLyrPrmsSelectObject = {}
            self.deactivate()

        if self.action():
            # 10/2026: tooltip with the mode of the menu (arrow)
            if hasattr(self.action(), 'setLyrToolTip'):
                self.action().setLyrToolTip(qActToolTip)
            else:
                self.action().setToolTip(qActToolTip)
            if (self.action().isEnabled() != qActEnabled):
                self.action().setEnabled(qActEnabled)
        return

class GQgis_MapToolSelection(qgis.gui.QgsMapTool):
    """map tool to select objects of the GeoDin layer by rectangle or click (10/2026)

    After each selection (mouse button released) the callback is called with the number of
    selected features; the action 'Selection' then creates the object selection in GeoDin
    and executes the function of the menu (arrow).
        drag            select by rectangle
        click           select the object at the point (search radius of QGIS)
        Shift           add to the current selection
        Ctrl            remove from the current selection (no GeoDin function)
    """

    def __init__(self, canvas, callback=None):
        super().__init__(canvas)
        self.log = logging.getLogger(f"{gqc._LOG_PARENTS}{self.__class__.__name__}")
        self._callback = callback
        self._layer = None
        self._start = None          # (pixel point, map point)
        self._rubberBand = None
        try:
            self.setCursor(qgis.core.QgsApplication.getThemeCursor(
                qgis.core.QgsApplication.Cursor.Select
            ))
        except Exception:
            self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.CrossCursor))

    def setLayer(self, layer):
        self._layer = layer

    @staticmethod
    def _nearestFeatureId(layer, rect, point):
        """returns the id of the feature in rect nearest to point (layer coordinates) or None"""
        best, bestDist = None, None
        pt = qgis.core.QgsGeometry.fromPointXY(qgis.core.QgsPointXY(point))
        req = qgis.core.QgsFeatureRequest().setFilterRect(rect)
        try:
            req.setNoAttributes()
        except AttributeError:
            pass
        for feat in layer.getFeatures(req):
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue
            dist = geom.distance(pt)
            if bestDist is None or dist < bestDist:
                best, bestDist = feat.id(), dist
        return best

    def _newRubberBand(self):
        try:
            geomType = qgis.core.Qgis.GeometryType.Polygon
        except AttributeError:
            geomType = qgis.core.QgsWkbTypes.PolygonGeometry
        rb = qgis.gui.QgsRubberBand(self.canvas(), geomType)
        rb.setStrokeColor(QtGui.QColor(255, 0, 0, 200))
        rb.setFillColor(QtGui.QColor(255, 0, 0, 40))
        rb.setWidth(1)
        return rb

    def _resetRubberBand(self):
        if self._rubberBand is not None:
            self._rubberBand.reset()
            self.canvas().scene().removeItem(self._rubberBand)
            self._rubberBand = None

    def canvasPressEvent(self, e):
        if e.button() != QtCore.Qt.MouseButton.LeftButton:
            return
        self._start = (e.pixelPoint(), e.mapPoint())

    def canvasMoveEvent(self, e):
        if self._start is None:
            return
        if self._rubberBand is None:
            self._rubberBand = self._newRubberBand()
        rect = qgis.core.QgsRectangle(self._start[1], e.mapPoint())
        self._rubberBand.setToGeometry(qgis.core.QgsGeometry.fromRect(rect), None)

    def canvasReleaseEvent(self, e):
        if self._start is None or e.button() != QtCore.Qt.MouseButton.LeftButton:
            return
        startPx, startMap = self._start
        self._start = None
        self._resetRubberBand()
        layer = self._layer
        if layer is None:
            return
        try:
            dx = abs(e.pixelPoint().x() - startPx.x())
            dy = abs(e.pixelPoint().y() - startPx.y())
            isClick = dx < 3 and dy < 3
            if isClick:
                # click: rectangle with the QGIS search radius
                # r = qgis.gui.QgsMapTool.searchRadiusMU(self.canvas())
                # 11/2026: selection radius in pixels (settings menu, default 6 px), the QGIS
                #   search radius (default 2 mm) needed a very exact click
                from GeODinQGIS.ui.gqgis_options import selectionRadiusPx
                r = selectionRadiusPx() * self.canvas().mapUnitsPerPixel()
                p = e.mapPoint()
                rect = qgis.core.QgsRectangle(p.x() - r, p.y() - r, p.x() + r, p.y() + r)
            else:
                rect = qgis.core.QgsRectangle(startMap, e.mapPoint())
            rect = self.toLayerCoordinates(layer, rect)
            mods = e.modifiers()
            behavior = _selectBehavior("SetSelection")
            if mods & QtCore.Qt.KeyboardModifier.ShiftModifier:
                behavior = _selectBehavior("AddToSelection")
            elif mods & QtCore.Qt.KeyboardModifier.ControlModifier:
                behavior = _selectBehavior("RemoveFromSelection")
            # layer.selectByRect(rect, behavior)
            if isClick:
                # 11/2026: click selects only the object nearest to the clicked point
                fid = self._nearestFeatureId(layer, rect, self.toLayerCoordinates(layer, e.mapPoint()))
                layer.selectByIds([fid] if fid is not None else [], behavior)
            else:
                layer.selectByRect(rect, behavior)
            count = layer.selectedFeatureCount()
            self.log.debug("Selected features in '%s': %d", layer.name(), count)
            if mods & QtCore.Qt.KeyboardModifier.ControlModifier:
                return
            if self._callback:
                self._callback(count)
        except Exception:
            self.log.critical("Unknown error on 'Select objects'", exc_info=True)

    def deactivate(self):
        self._start = None
        self._resetRubberBand()
        super().deactivate()


def _selectBehavior(name):
    """Qgis.SelectBehavior (QGIS >= 3.22) or QgsVectorLayer.SelectBehavior (10/2026)"""
    try:
        return getattr(qgis.core.Qgis.SelectBehavior, name)
    except AttributeError:
        return getattr(qgis.core.QgsVectorLayer, name)


def main():
    pass

if __name__ == '__main__':
    main()
