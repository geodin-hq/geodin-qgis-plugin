""" UserInterface framework

classes:
    GQgis_Bas_Widget            - widget base class

functions:
    busy()                      - context manager showing a 'please wait' status dialog (10/2026)
    qsleep()                    - waits and keeps the QGIS user interface responsive (10/2026)
    cursor()                    - context manager for setting a custom cursor
    plugin()                    - returns GeODinQGIS plugin instance

22.09.2022 J.Ebert
"""
import logging
from contextlib import contextmanager

import qgis.utils
from qgis.PyQt import (
    QtCore,
    QtGui,
    QtWidgets
)
##from qgis import utils
##from qgis.PyQt.QtWidgets import (
##    QApplication,
##    QMessageBox
##)


import GeODinQGIS.gqgis_config as gqc
import GeODinQGIS.gqgis_base as gqb
from GeODinQGIS import (
    res
)

class GQgis_Bas_Widget:
    """ GeODinQGIS widget base class

    02.09.2022 J.Ebert
    """

    def __init__(self):
        # default context to translate source text (see also method translate())
        self._context = "GQgis_Bas"

    @staticmethod
    def QIcon(
        alias                   # recource alias/image alias
        ):
        """ returns QIcon for recource alias/image alias

        Args:
            alias (str)         recource alias

        02.09.2022 J.Ebert
        """
        return QtGui.QIcon(f":/plugins/GeODinQGIS/{alias}")

    @staticmethod
    def QPixmap(
        alias                   # recource alias/image alias
        ):
        """ returns QPixmap for recource alias/image alias

        Args:
            alias (str)         recource alias

        02.09.2022 J.Ebert
        """
        return QtGui.QPixmap(f":/plugins/GeODinQGIS/{alias}")

    def translateUi(self):
        """ translates the UserInterfase

        06.09.2022 J.Ebert
        """
        return

    def translate(
        self,
        context,
        key,
        disambiguation=None,
        n=-1
        ):
        """translate souerce text 'key'

        args:
            context (str)           typically a class name (e.g., “MyDialog”)
            key (str)               source text

        kwargs:
            disambiguation (str)    is ignored - for compatibility only
            n (int)                 is ignored - for compatibility only

        return:
            sourceText (str)

        01.09.2022 J.Ebert
        """
        return res.translate(context, key)

    def trans(
        self,
        key,
        disambiguation=None,
        n=-1
        ):
        """translate souerce text 'key' using instance context

        Args:
            key (str)               source text
        KWArgs:
            disambiguation (str)    is ignored - for compatibility only
            n (int)                 is ignored - for compatibility only
        Returns:
            sourceText (str)

        07.09.2022 J.Ebert
        """
        return  self.translate(self._context, key, disambiguation, n)

class GQgis_MsgBox(QtWidgets.QMessageBox, GQgis_Bas_Widget):
    """ GeODinQGIS message box

    29.03.2023 j.ebert
    """

    # QtWidgets.QMessageBox.StandardButton
    # 29.03.2023 j.ebert, Anmerkung
    #   Enums/Konstanten zur besseren Programmierung/inkl. Kodeeingabe übernommen/implementiert
    #   vgl. https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QMessageBox.html
    Ok = QtWidgets.QMessageBox.StandardButton.Ok
    """An 'OK' button defined with the AcceptRole. (QtWidgets.QMessageBox.StandardButton)"""
    Open = QtWidgets.QMessageBox.StandardButton.Open
    """An 'Open' button defined with the AcceptRole. (QtWidgets.QMessageBox.StandardButton)"""
    Save = QtWidgets.QMessageBox.StandardButton.Save
    """A 'Save' button defined with the AcceptRole. (QtWidgets.QMessageBox.StandardButton)"""
    Cancel = QtWidgets.QMessageBox.StandardButton.Cancel
    """A 'Cancel' button defined with the RejectRole. (QtWidgets.QMessageBox.StandardButton)"""
    Close = QtWidgets.QMessageBox.StandardButton.Close
    """A 'Close' button defined with the RejectRole. (QtWidgets.QMessageBox.StandardButton)"""
    Discard = QtWidgets.QMessageBox.StandardButton.Discard
    """A 'Discard' or 'Don’t Save' button, depending on the platform, defined with the DestructiveRole. (QtWidgets.QMessageBox.StandardButton)"""
    Apply = QtWidgets.QMessageBox.StandardButton.Apply
    """An 'Apply' button defined with the ApplyRole. (QtWidgets.QMessageBox.StandardButton)"""
    Reset = QtWidgets.QMessageBox.StandardButton.Reset
    """A 'Reset' button defined with the ResetRole. (QtWidgets.QMessageBox.StandardButton)"""
    RestoreDefaults = QtWidgets.QMessageBox.StandardButton.RestoreDefaults
    """A 'Restore Defaults' button defined with the ResetRole. (QtWidgets.QMessageBox.StandardButton)"""
    Help = QtWidgets.QMessageBox.StandardButton.Help
    """A 'Help' button defined with the HelpRole. (QtWidgets.QMessageBox.StandardButton)"""
    SaveAll = QtWidgets.QMessageBox.StandardButton.SaveAll
    """A 'Save All' button defined with the AcceptRole. (QtWidgets.QMessageBox.StandardButton)"""
    Yes = QtWidgets.QMessageBox.StandardButton.Yes
    """A 'Yes' button defined with the YesRole. (QtWidgets.QMessageBox.StandardButton)"""
    YesToAll = QtWidgets.QMessageBox.StandardButton.YesToAll
    """A 'Yes to All' button defined with the YesRole. (QtWidgets.QMessageBox.StandardButton)"""
    No = QtWidgets.QMessageBox.StandardButton.No
    """A 'No' button defined with the NoRole. (QtWidgets.QMessageBox.StandardButton)"""
    NoToAll = QtWidgets.QMessageBox.StandardButton.NoToAll
    """A 'No to All' button defined with the NoRole. (QtWidgets.QMessageBox.StandardButton)"""
    Abort = QtWidgets.QMessageBox.StandardButton.Abort
    """An 'Abort' button defined with the RejectRole. (QtWidgets.QMessageBox.StandardButton)"""
    Retry = QtWidgets.QMessageBox.StandardButton.Retry
    """A 'Retry' button defined with the AcceptRole. (QtWidgets.QMessageBox.StandardButton)"""
    Ignore = QtWidgets.QMessageBox.StandardButton.Ignore
    """An 'Ignore' button defined with the AcceptRole. (QtWidgets.QMessageBox.StandardButton)"""
    NoButton = QtWidgets.QMessageBox.StandardButton.NoButton
    """An invalid button."""

    log = logging.getLogger(f"{gqc._LOG_PARENTS}GQgis_MsgBox")

    def __init__(
        self,
        parent,
    ):
        super().__init__(parent)
        self.setWindowIcon(self.QIcon("gIcon"))
        self.setWindowTitle(gqc.PRODUCT)

    # 10/2026: texts of the message box translated in context 'GQgis_MsgBox'
    #   (literal texts in the code, e.g. "Unknown error on 'Create object'")
    @staticmethod
    def _msgTrans(text):
        if not isinstance(text, str) or not text:
            return text
        try:
            return res.translate("GQgis_MsgBox", text)
        except Exception:
            return text

    def setText(self, text):
        super().setText(self._msgTrans(text))

    def setInformativeText(self, text):
        super().setInformativeText(self._msgTrans(text))

    def setWindowTitle(self, title):
        # "<product> - <title>": translate the title part
        if isinstance(title, str) and " - " in title:
            head, _sep, tail = title.partition(" - ")
            title = "%s - %s" % (head, self._msgTrans(tail))
        super().setWindowTitle(title)
##        self.setCursor(QtCore.Qt.ArrowCursor)
##        self.setCursor(QtCore.Qt.WhatsThisCursor)

    @classmethod
    def about(
        cls,
        parent,
        title,
        text,
        info=None,              # InformativeText
    ):
        """shows GeODinQGIS Infromation message box

        22.05.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE,"")
        msg = cls(parent)
        if title:
            msg.setWindowTitle("%s - %s" % (msg.windowTitle(), str(title)))
        msg.setText(text)
        msg.setIconPixmap(msg.QIcon("gIcon").pixmap(64, 64))
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg.setInformativeText(info)
        return msg.exec()

    @classmethod
    def critical(
        cls,
        parent,
        title,
        text,
        info=None,              # InformativeText
        buttons=QtWidgets.QMessageBox.StandardButton.Ok,
        defaultButton=QtWidgets.QMessageBox.StandardButton.NoButton
    ):
        """shows GeODinQGIS Infromation message box

        22.05.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE,"")
##        QtWidgets.QMessageBox.critical(
##            parent,
##            title,
##            text,
##            buttons,
##            defaultButton
##        )
        msg = cls(parent)
        if title:
            msg.setWindowTitle("%s - %s" % (msg.windowTitle(), str(title)))
        msg.setText(text)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        msg.setStandardButtons(buttons)
        msg.setInformativeText(info)
        return msg.exec()

    @classmethod
    def error(
        cls,
        parent,
        title,
        text,
        info=None,              # InformativeText
        buttons=QtWidgets.QMessageBox.StandardButton.Ok,
        defaultButton=QtWidgets.QMessageBox.StandardButton.NoButton
    ):
        """shows GeODinQGIS Infromation message box

        22.05.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE,"")
        msg = cls(parent)
        if title:
            msg.setWindowTitle("%s - %s" % (msg.windowTitle(), str(title)))
        msg.setText(text)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        msg.setStandardButtons(buttons)
        msg.setInformativeText(info)
        return msg.exec()

    @classmethod
    def information(
        cls,
        parent,
        title,
        text,
        info=None,              # InformativeText
        buttons=QtWidgets.QMessageBox.StandardButton.Ok,
        defaultButton=QtWidgets.QMessageBox.StandardButton.NoButton
    ):
        """shows GeODinQGIS Infromation message box

        22.05.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE,"")
        msg = cls(parent)
        if title:
            msg.setWindowTitle("%s - %s" % (msg.windowTitle(), str(title)))
        msg.setText(text)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg.setStandardButtons(buttons)
        msg.setInformativeText(info)
        return msg.exec()

    @classmethod
    def question(
        cls,
        parent,
        title,
        text,
        info=None,              # InformativeText
        buttons=QtWidgets.QMessageBox.StandardButton.Yes|QtWidgets.QMessageBox.StandardButton.No,
        defaultButton=QtWidgets.QMessageBox.StandardButton.NoButton
    ):
        """shows GeODinQGIS Question message box

        22.05.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE,"")
        msg = cls(parent)
        if title:
            msg.setWindowTitle("%s - %s" % (msg.windowTitle(), str(title)))
        msg.setText(text)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Question)
        msg.setStandardButtons(buttons)
        msg.setInformativeText(info)
        return msg.exec()

    @classmethod
    def warning(
        cls,
        parent,
        title,
        text,
        info=None,              # InformativeText
        buttons=QtWidgets.QMessageBox.StandardButton.Ok,
        defaultButton=QtWidgets.QMessageBox.StandardButton.NoButton
    ):
        """shows GeODinQGIS Infromation message box

        22.05.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE,"")
        msg = cls(parent)
        if title:
            msg.setWindowTitle("%s - %s" % (msg.windowTitle(), str(title)))
        msg.setText(text)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msg.setStandardButtons(buttons)
        msg.setInformativeText(info)
        return msg.exec()


def plugin():
    """Plugin instance

    exception:
        KeyError                if GeODinQGIS plugin ist not installed

    27.04.2023 j.ebert
    """
    return qgis.utils.plugins['GeODinQGIS']

def qsleep(seconds):
    """waits 'seconds' and keeps the user interface (e.g. a status dialog) responsive

    10/2026
    """
    timer = QtCore.QElapsedTimer()
    timer.start()
    app = QtWidgets.QApplication.instance()
    while timer.elapsed() < seconds * 1000:
        if app is not None:
            app.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 50)
        QtCore.QThread.msleep(20)


@contextmanager
def busy(parent, text, title=None):
    """context manager for a modal 'please wait' status dialog (busy indicator, no cancel)

    usage:
        with busy(parent, "GeoDin is starting...") as dlg:
            ...                         # long running task
            dlg.setLabelText("...")     # optional: update the text

    10/2026
    """
    dlg = QtWidgets.QProgressDialog(text, "", 0, 0, parent)
    dlg.setWindowTitle(title or gqc.PRODUCT)
    dlg.setWindowIcon(GQgis_Bas_Widget.QIcon("gIcon"))
    dlg.setCancelButton(None)
    dlg.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
    dlg.setMinimumDuration(0)
    dlg.setAutoClose(False)
    dlg.setAutoReset(False)
    dlg.setMinimumWidth(420)
    dlg.show()
    QtWidgets.QApplication.instance().processEvents()
    try:
        yield dlg
    finally:
        dlg.close()
        dlg.deleteLater()


@contextmanager
def cursor(shape=None):
    """context manager for setting the custom cursor

    args:
        shape                   - Qt CursorShape
                                  https://doc.qt.io/qtforpython-5/PySide2/QtGui/QCursor.html
    see also:
        https://stackoverflow.com/questions/8218900/how-can-i-change-the-cursor-shape-with-pyqt

    22.05.2023 j.ebert
    """
    try:
        if shape is None:
            shape = QtCore.Qt.CursorShape.ArrowCursor
        QtWidgets.QApplication.instance().setOverrideCursor(QtGui.QCursor(shape))
        yield
    finally:
        QtWidgets.QApplication.instance().restoreOverrideCursor()

#---------------------------------------------------------------------------------------------------
#   08/2022 J.Ebert, sample code
#
# Transformation in Context-Key für translateUi()
#   z.B. von File-Base-Name
##import re
##regex = re.compile('^Gqgis')
##regex.sub('GQgis',"GQGIS_MNU_HELP".title())     # -> 'GQgis_Mnu_Help'
##regex.sub('GQgis',"gqgis_mnu_help".title())     # -> 'GQgis_Mnu_Help'


##class Window(QMainWindow):
##    def __init__(self, parent=None):
##        super().__init__(parent)
##        self.ui = Ui_MainWindow()
##        self.ui.setupUi(self)
##        self.connectSignalsSlots()
##
##    def connectSignalsSlots(self):
##        self.ui.action_Exit.triggered.connect(self.close)
##        self.ui.action_Find_Replace.triggered.connect(
##            self.findAndReplace
##        )
##        self.ui.action_About.triggered.connect(self.about)
##    # Snip...
#---------------------------------------------------------------------------------------------------

def main():
    pass

if __name__ == '__main__':
    main()
