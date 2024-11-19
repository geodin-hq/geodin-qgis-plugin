"""
Classes:
    GQgis_Tbr                   - PyQt ToolBar from GeODinQGIS

27.04.2023 J.Ebert
"""
##https://stackoverflow.com/questions/36434706/pyqt-proper-use-of-emit-and-pyqtsignal
##https://zetcode.com/gui/pyqt5/eventssignals/
CONTEXT_RES = "GQgis_Tbr"
"""context for resource translation of QWidgets"""
CONTEXT_HLP = "GQgis_Tbr"
"""context for resource translation of the help pages (type str)"""
import logging
from pathlib import Path

from qgis.PyQt import (
    QtCore,
    QtWidgets
    )

import GeODinQGIS.gqgis_config as gqc
import GeODinQGIS.gqgis_base as gqb

from GeODinQGIS import (
    app,
    env,
    res
    )

from .gqgis_act import *
from .gqgis_dlg_ddx import GQgis_Act_DDX
from .gqgis_mnu_help import GQgis_TBtn_Help

class GQgis_Tbr(QtWidgets.QToolbar):
    """PyQt ToolBar from GeODinQGIS

    27.04.2023 J.Ebert
    """

    def __new__(cls, parent):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GQgis_Tbr, cls).__new__(cls)
        return cls.instance

    def __init__(self, parent):
        super().__init__(parent)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.log(gqc._LOG_TRACE,"")
        self._context = CONTEXT_RES

        self.setObjectName(self.__class__.__name__)

        self.toolBar.addAction(GQgis_Act_DDX(parent))
        self.toolBar.addAction(GQgis_Act_Connect(parent, None))
        self.toolBar.addAction(GQgis_Act_Refresh(parent, self.refresh))
        self.toolBar.addAction(GQgis_Act_Pan(parent))
        self.toolBar.addWidget(GQgis_TBtn_Help(parent))
        self.toolBar.addAction(GQgis_Act_MsgBox(parent, None))


