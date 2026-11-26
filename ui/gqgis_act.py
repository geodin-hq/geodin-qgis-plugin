""" QActions

Classes:
    GQgis_Act_Connect           - QAction to connect/disconnect GeODin application
    GQgis_Act_MsgBox            - QAction to test QMessageBox
    GQgis_Act_Refresh           - QAction to refresh temp data/feature classes

16.08.2022 J.Ebert
"""

CONTEXT_RES = "GQgis_Act"
"""context for resource translation of QWidgets"""

import logging
import time

import qgis.gui
import qgis.utils
from qgis.PyQt import (
    QtGui,
    QtWidgets
    )
from GeODinQGIS.ui.gqgis_bas import (
    GQgis_Bas_Widget,
    GQgis_MsgBox as MsgBox
)

import GeODinQGIS.gqgis_config as gqc
import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gx as gx
from GeODinQGIS import (
    app,
    res
)
class GQgis_Act_MsgBox(QtWidgets.QAction, GQgis_Bas_Widget):
    """ QAction to test QMessageBox

    29.03.2023 J.Ebert
    """
    def __init__(self, parent=None, slot=None):
        # init QtWidgets.QAction here to set parent
        # (QAction.Text will be set in translateUi())
        QtWidgets.QAction.__init__(self, "DummyText", parent)
        GQgis_Bas_Widget.__init__(self)
##        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log = logging.getLogger(f"{gqc._LOG_PARENTS}.{self.__class__.__name__}")
        self.log.log(gqc._LOG_TRACE,"")
        self._parent = parent
        self._context = CONTEXT_RES
        # set up QAction
        self.setObjectName(self.__class__.__name__)
        self.setIcon(self.QIcon("gTiger"))
##        if slot:
##            self.triggered.connect(slot)
        self.triggered.connect(self.execute)
        # translate QAction
        self.translateUi()
        # register QAction for translation
        res.Ui.append(self)

    def execute(self):
        """executes QAction

        29.03.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        res = MsgBox.information(
            self._parent,
            None,
            "Check GeoDin application!",
            "Bring the GeoDin window to the front\nand check the license selection!",
            MsgBox.Retry|MsgBox.Cancel
        )
        self.log.info("MsgBox result %s (%s, %s)", str(res), type(res), repr(res))
        app.updateUI()

        return

    def execute_01(self):
        """executes QAction

        29.03.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        MsgBox.about(
            self._parent,
            "Titel",
            "This is some random text",
            "This is some extra informative text"
        )
        MsgBox.critical(
            self._parent,
            "Titel",
            "This is some random text",
            "This is some extra informative text"
        )
        MsgBox.information(
            self._parent,
            "Titel",
            "This is some random text",
            "This is some extra informative text"
        )
        MsgBox.question(
            self._parent,
            "Titel",
            "This is some random text",
            "This is some extra informative text"
        )
        MsgBox.warning(
            self._parent,
            "Titel",
            "This is some random text",
            "This is some extra informative text"
        )

        return

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        self.setText(self.trans("MsgBox"))
        self.setToolTip(self.trans("Tiger"))

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
        enabled = True
        if (
            isinstance(widget, QtWidgets.QWidget) and
            (widget.isEnabled() != enabled)
        ):
            widget.setEnabled(enabled)
        return

class GQgis_Act_Connect(QtWidgets.QAction, GQgis_Bas_Widget):
    """ QAction to connect/disconnect GeODin application

    13.09.2022 J.Ebert
    """
    def __init__(self, parent=None, slot=None):
        # init QtWidgets.QAction here to set parent
        # (QAction.Text will be set in translateUi())
        QtWidgets.QAction.__init__(self, "DummyText", parent)
        GQgis_Bas_Widget.__init__(self)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.log(gqc._LOG_TRACE,"")
        self._parent = parent
        self._context = CONTEXT_RES
        # set up QAction
        self.setObjectName(self.__class__.__name__)
        self.setIcon(self.QIcon("gIcon"))
        self.triggered.connect(self.execute)
        self.changed.connect(self.translateUi)
        self.setCheckable(True)
        # translate QAction
        self.translateUi()
        # register QAction for translation
        res.Ui.append(self)

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        self.setText(self.trans("GeoDin"))
        if self.isChecked():
            self.setToolTip(self.trans("Close GeoDin"))
        else:
            self.setToolTip(self.trans("Open GeoDin"))

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
        enabled = app.isConfigured()
        self.log.debug("isConfigured()  - %s", str(app.isConfigured()))
        self.setChecked(app.isConnected())
        if (
            isinstance(widget, QtWidgets.QWidget) and
            (widget.isEnabled() != enabled)
        ):
            widget.setEnabled(enabled)
        return

    def execute(self):
        """executes QAction

        28.03.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        self.log.debug(str(self.isChecked()))
        try:
            if not self.isChecked():
                # GeODin beenden/Verbindung trennen...
                app.closeGAppCnn()
            else:
                # GeODin starten/verbinden...
                app.openGAppCnn()
        except:
            self.log.critical("Major disater...", exc_info=True)
            gx.gApp.reset()
            app.updateUI()
        return

    def execute_v01(self):
        """executes QAction

        28.03.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")

        self.log.debug(str(self.isChecked()))
        try:
            if not self.isChecked():
                # GeODin beenden/Verbindung trennen...
                app.closeGAppCnn()
            else:
                # GeODin starten/verbinden...
                hdl = gx.gApp.open()
                # GeODin Startup/Lizenz abwarten...
                while (hdl == 0):
                    sleepTime = 1
                    breakTime = time.time() + 5 * sleepTime
                    while (
                        (time.time() < breakTime) and
                        (hdl == 0)
                    ):
                        hdl = gx.gApp.renew()
                        print(hdl, res)
                        if not hdl:
                            self.log.debug("")
                            time.sleep(sleepTime)
                    if not hdl:
                        dlgRes = MsgBox.information(
                            self._parent,
                            None,
                            "Check GeoDin application!",
                            "Bring the GeoDin window to the front\nand check the license selection!",
                            MsgBox.Retry|MsgBox.Cancel
                        )
                        if (dlgRes != MsgBox.Retry):
                            raise gqb.GQgisCanceldByUser("Canceld by user!")
        except gqb.GQgisCanceldByUser as exc:
            gx.gApp.reset()
            self.log.warning(exc.msg())
        except gqb.GxException as exc:
            gx.gApp.reset()
            msg = exc.msg()
            self.log.warning(msg.replace("\n","\n\t"))
            MsgBox.error(self._parent, None, msg.replace("\n","\n   "))
        except:
            gx.gApp.reset()
            self.log.critical("Major disater...", exc_info=True)
        finally:
            self.setChecked(gx.gApp.is_open())
        return


class GQgis_Act_Refresh(QtWidgets.QAction, GQgis_Bas_Widget):
    """QAction to refresh temp data/feature classes

    13.09.2022 J.Ebert
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
        self.setIcon(self.QIcon("GenericRefresh"))
        if slot:
            self.triggered.connect(slot)
        # translate QAction
        self.translateUi()
        # register QAction for translation
        res.Ui.append(self)

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        self.setText(self.trans("Refresh"))
        self.setToolTip(self.trans("Refresh"))

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


