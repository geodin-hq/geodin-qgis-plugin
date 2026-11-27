r"""Tool 'Create object' (10/2026)

Classes:
    GQgis_Act_ToolCreateObject  - QAction of the map tool 'Create object'
    GQgis_MapToolCreateObject   - QgsMapToolEmitPoint: click in the map -> GeoDin 'Create object'

Workflow:
    1. click on the toolbar button, then a click in the map
    2. the point is transformed into the CRS of the GeoDin layer (layer selection of the toolbar)
    3. the query of the layer is selected in GeoDin and the GeoDin method 'Create object' is
       started with the coordinates, the project and the object type of the layer
       (COM ExecuteMethodParams, see GEODIN_COM.md / ui/gqgis_options.py METHOD_CREATE_OBJECT)
    4. the dialog is completed in GeoDin; afterwards the layer is updated with the button
       'Update layer' in the QGIS message bar

MethodParams (GeoDin source Methods/meth_locationcreate.pas AssignStartParams):
    [Params]
    ApplyFieldValues=1
    XCOORD=<x>
    YCOORD=<y>
    PRJID=<project ID>
    Name=<long name>
    ObjectType=<object type descriptor>
    [FieldValues]
    EPSG=<EPSG code of the layer CRS>      (field 'Koordinatensystem', 10/2026)
"""
import logging

CONTEXT_RES = "GQgis_Act"
"""context for resource translation of QWidgets"""

import GeODinQGIS.gqgis_base as gqb
from GeODinQGIS import res
from qgis.PyQt import QtCore, QtGui, QtWidgets
from GeODinQGIS.ui.gqgis_bas import (
    GQgis_Bas_Widget,
    GQgis_MsgBox,
)
from GeODinQGIS import app
import GeODinQGIS.gx as gx
import qgis.core
import qgis.gui
from qgis.PyQt import sip

from GeODinQGIS.ui.gqgis_ctl_tools_v2332 import GQgis_Cbo_Layers, _goLyrExcText


class GQgis_Act_ToolCreateObject(QtWidgets.QAction, GQgis_Bas_Widget):
    """QAction of the map tool 'Create object' (10/2026)"""

    def __init__(self, parent=None, slot=None):
        QtWidgets.QAction.__init__(self, "DummyText", parent)
        GQgis_Bas_Widget.__init__(self)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._parent = parent
        self._context = CONTEXT_RES
        self.setObjectName(self.__class__.__name__)
        self.setIcon(self.QIcon("gToolCreateObject"))
        self.setCheckable(True)
        self.triggered.connect(slot if slot else self.activateTool)
        self.canvas = qgis.utils.iface.mapCanvas()
        self.mapTool = GQgis_MapToolCreateObject(self.canvas, self.onPointClicked)
        self.mapTool.setAction(self)
        self._lyrToolTip = ""
        self.translateUi()
        res.Ui.append(self)
        self.cboLayers().currentIndexChanged.connect(self.onGoLyrChanged)

    def translateUi(self):
        self.setText(self.trans("Create object"))
        tip = self.trans("Create object: click in the map, GeoDin opens 'Create object' with the coordinates")
        self.setToolTip(f"{tip}\n{self._lyrToolTip}" if self._lyrToolTip else tip)

    def cboLayers(self):
        return GQgis_Cbo_Layers.instance()

    def updateUi(self, widget=None):
        enabled = app.isConnected()
        if isinstance(widget, QtWidgets.QWidget) and (widget.isEnabled() != enabled):
            if (not enabled) and self.mapTool.isActive():
                self.canvas.unsetMapTool(self.mapTool)
            widget.setEnabled(enabled)
        return

    def onGoLyrChanged(self, val):
        QtCore.QTimer.singleShot(100, self.updateGoLyr)

    def updateGoLyr(self):
        cbo = self.cboLayers()
        qry = cbo.GoLyrQry
        enabled = (not cbo.GoLyrExc) and (qry is not None) and qry.Kind[-3:] == 'LOC'
        if cbo.GoLyrExc or qry is None:
            self._lyrToolTip = _goLyrExcText(cbo)
        elif qry.Kind[-3:] != 'LOC':
            self._lyrToolTip = self.trans("Only for object layers")
        else:
            self._lyrToolTip = qry.LongLabel
        self.translateUi()
        if not enabled and self.mapTool.isActive():
            self.canvas.unsetMapTool(self.mapTool)
        if self.isEnabled() != enabled:
            self.setEnabled(enabled)

    def activateTool(self):
        self.updateGoLyr()
        if not self.isEnabled():
            self.setChecked(False)
            return
        self.setChecked(True)
        self.canvas.setMapTool(self.mapTool)
        from GeODinQGIS.ui.gqgis_options import pushMessage
        pushMessage(
            self.trans("Click in the map where the new object is to be created."),
            tooltip=self.cboLayers().GoLyrText
        )

    def onPointClicked(self, point):
        """point (QgsPointXY, canvas CRS) -> GeoDin 'Create object'"""
        from GeODinQGIS.ui.gqgis_options import METHOD_CREATE_OBJECT
        cbo = self.cboLayers()
        lyr, qry = cbo.GoLyr, cbo.GoLyrQry
        try:
            if lyr is None or qry is None:
                raise gqb.GxToolError("%s", _goLyrExcText(cbo))
            if qry.PrjID == qry.DbRef.DBPrjID:
                raise gqb.GxToolError(self.trans(
                    "Objects can only be created in a query of a project, not of the database."
                ))
            if METHOD_CREATE_OBJECT is None:
                raise gqb.GxToolError(self.trans(
                    "The GeoDin method 'Create object' is not yet known (method ID, see GEODIN_COM.md)."
                ))
            # canvas CRS -> layer CRS (= coordinates of the GeoDin export)
            xform = qgis.core.QgsCoordinateTransform(
                self.canvas.mapSettings().destinationCrs(), lyr.crs(), qgis.core.QgsProject.instance()
            )
            pt = xform.transform(point)
            objType = qry.Desc if qry.Kind == 'GxTypLOC' else ""
            # 10/2026: coordinate system (field EPSG) - EPSG code of the layer CRS
            epsg = _layerEpsg(lyr)
            prms = "\n".join([
                "[Params]",
                "ApplyFieldValues=1",
                f"XCOORD={pt.x():.3f}",
                f"YCOORD={pt.y():.3f}",
                f"PRJID={qry.PrjID}",
                "Name=",
                f"ObjectType={objType}",
                "[FieldValues]",
                f"EPSG={epsg}" if epsg else "",
                "",
            ])
            self.log.info("Create object at %.3f/%.3f (%s, EPSG field %s), query '%s'",
                          pt.x(), pt.y(), lyr.crs().authid(), epsg, qry.LongLabel)
            # select the query in GeoDin, then start 'Create object'
            gx.gApp.selectObject(qry)
            gx.gApp.executeMethod(METHOD_CREATE_OBJECT, prms)
            self._pushUpdateMessage(qry, lyr)
        except gqb.GQgisException as exc:
            self.log.error(exc.msg(), exc_info=True)
            GQgis_MsgBox.error(self._parent, self.text(), exc.msg())
        except Exception:
            self.log.critical("Unknown error on 'Create object'", exc_info=True)
            GQgis_MsgBox.critical(self._parent, self.text(), "Unknown error on 'Create object'")

    def _pushUpdateMessage(self, qry, lyr):
        """message bar with the button 'Update layer' (GeoDin dialog runs asynchronously)"""
        # widget = bar.createMessage(
        #     "GeoDinQGIS",
        #     # self.trans("Complete the dialog 'Create object' in GeoDin, then update the layer.")
        #     self.trans("First complete or cancel the dialog 'Create object' in GeoDin, then click 'Update layer' (QGIS waits while the GeoDin dialog is open).")
        # )
        # 10/2026: the long text was cut off in a small QGIS window -> short text with word wrap,
        #   the full explanation as tooltip
        tip = self.trans("First complete or cancel the dialog 'Create object' in GeoDin, then click 'Update layer' (QGIS waits while the GeoDin dialog is open).")
        btn = QtWidgets.QPushButton(self.trans("Update layer"))
        btn.setToolTip(tip)
        from GeODinQGIS.ui.gqgis_options import pushMessage
        widget = pushMessage(
            self.trans("Complete the GeoDin dialog first, then update the layer."),
            "info", 0, tip, [btn]
        )
        btn.clicked.connect(lambda checked=False: self._updateLayer(qry, lyr, widget))

    def _updateLayer(self, qry, lyr, widget=None):
        """exports the query again and reloads the layer (as 'Update layer(s)' in the Explorer)"""
        from GeODinQGIS.ui.gqgis_ctl_tools_v2332 import updateGoLayerData
        if updateGoLayerData(qry, lyr, self.log, self._parent, self.text()) and widget is not None:
            if not sip.isdeleted(widget):
                qgis.utils.iface.messageBar().popWidget(widget)


def _layerEpsg(lyr):
    """EPSG code (str) for the field EPSG of the new object (10/2026)

    EPSG code of the layer CRS (= CRS of the coordinates passed to GeoDin); if the layer CRS
    is no EPSG CRS, the most frequent value of the field EPSG of the layer features.
    """
    authid = lyr.crs().authid() if lyr.crs().isValid() else ""
    if authid.upper().startswith("EPSG:"):
        return authid.split(":", 1)[1]
    if lyr.fields().indexOf("EPSG") >= 0:
        from collections import Counter
        values = Counter(str(f["EPSG"]) for f in lyr.getFeatures() if f["EPSG"] not in (None, ""))
        if values:
            return values.most_common(1)[0][0]
    return ""


class GQgis_MapToolCreateObject(qgis.gui.QgsMapToolEmitPoint):
    """click in the map -> callback(QgsPointXY in canvas CRS) (10/2026)"""

    def __init__(self, canvas, callback=None):
        super().__init__(canvas)
        self._callback = callback
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.CrossCursor))
        self.canvasClicked.connect(self._onClicked)

    def _onClicked(self, point, button):
        if button == QtCore.Qt.MouseButton.LeftButton and self._callback:
            self._callback(point)
