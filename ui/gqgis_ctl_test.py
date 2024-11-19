""" Controls of testing

Classes:
    GQgis_Act_Pan               - QAction to pan/only for testing

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


class GQgis_Act_Pan(QtWidgets.QAction, GQgis_Bas_Widget):
    """ QAction to test QgsMapTool

    07.08.2023 j.ebert
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
        self.setIcon(self.QIcon("gScott"))
        # init settings for QgsMapTool
        self.setCheckable(True)
        self.triggered.connect(self.execute)
        self.canvas = qgis.utils.iface.mapCanvas()
        self.mapTool = qgis.gui.QgsMapToolPan(self.canvas)
        self.mapTool.setAction(self)
        # translate QAction
        self.translateUi()
        # register QAction for translation
        res.Ui.append(self)

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        self.setText(self.trans("MyPan"))
        self.setToolTip(self.trans("MyPan"))

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
        self.log.log(gqc._LOG_TRACE,"TRACE")

        self.canvas.setMapTool(self.mapTool)


def main():
    pass

if __name__ == '__main__':
    main()
