""" UserInterface framework

classes:
    GQgis_Bas_Widget            - widget base class

functions:
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
    Ok = QtWidgets.QMessageBox.Ok
    """An 'OK' button defined with the AcceptRole. (QtWidgets.QMessageBox.StandardButton)"""
    Open = QtWidgets.QMessageBox.Open
    """An 'Open' button defined with the AcceptRole. (QtWidgets.QMessageBox.StandardButton)"""
    Save = QtWidgets.QMessageBox.Save
    """A 'Save' button defined with the AcceptRole. (QtWidgets.QMessageBox.StandardButton)"""
    Cancel = QtWidgets.QMessageBox.Cancel
    """A 'Cancel' button defined with the RejectRole. (QtWidgets.QMessageBox.StandardButton)"""
    Close = QtWidgets.QMessageBox.Close
    """A 'Close' button defined with the RejectRole. (QtWidgets.QMessageBox.StandardButton)"""
    Discard = QtWidgets.QMessageBox.Discard
    """A 'Discard' or 'Don’t Save' button, depending on the platform, defined with the DestructiveRole. (QtWidgets.QMessageBox.StandardButton)"""
    Apply = QtWidgets.QMessageBox.Apply
    """An 'Apply' button defined with the ApplyRole. (QtWidgets.QMessageBox.StandardButton)"""
    Reset = QtWidgets.QMessageBox.Reset
    """A 'Reset' button defined with the ResetRole. (QtWidgets.QMessageBox.StandardButton)"""
    RestoreDefaults = QtWidgets.QMessageBox.RestoreDefaults
    """A 'Restore Defaults' button defined with the ResetRole. (QtWidgets.QMessageBox.StandardButton)"""
    Help = QtWidgets.QMessageBox.Help
    """A 'Help' button defined with the HelpRole. (QtWidgets.QMessageBox.StandardButton)"""
    SaveAll = QtWidgets.QMessageBox.SaveAll
    """A 'Save All' button defined with the AcceptRole. (QtWidgets.QMessageBox.StandardButton)"""
    Yes = QtWidgets.QMessageBox.Yes
    """A 'Yes' button defined with the YesRole. (QtWidgets.QMessageBox.StandardButton)"""
    YesToAll = QtWidgets.QMessageBox.YesToAll
    """A 'Yes to All' button defined with the YesRole. (QtWidgets.QMessageBox.StandardButton)"""
    No = QtWidgets.QMessageBox.No
    """A 'No' button defined with the NoRole. (QtWidgets.QMessageBox.StandardButton)"""
    NoToAll = QtWidgets.QMessageBox.NoToAll
    """A 'No to All' button defined with the NoRole. (QtWidgets.QMessageBox.StandardButton)"""
    Abort = QtWidgets.QMessageBox.Abort
    """An 'Abort' button defined with the RejectRole. (QtWidgets.QMessageBox.StandardButton)"""
    Retry = QtWidgets.QMessageBox.Retry
    """A 'Retry' button defined with the AcceptRole. (QtWidgets.QMessageBox.StandardButton)"""
    Ignore = QtWidgets.QMessageBox.Ignore
    """An 'Ignore' button defined with the AcceptRole. (QtWidgets.QMessageBox.StandardButton)"""
    NoButton = QtWidgets.QMessageBox.NoButton
    """An invalid button."""

    log = logging.getLogger(f"{gqc._LOG_PARENTS}GQgis_MsgBox")

    def __init__(
        self,
        parent,
    ):
        super().__init__(parent)
        self.setWindowIcon(self.QIcon("gIcon"))
        self.setWindowTitle(gqc.PRODUCT)
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
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.setInformativeText(info)
        return msg.exec_()

    @classmethod
    def critical(
        cls,
        parent,
        title,
        text,
        info=None,              # InformativeText
        buttons=QtWidgets.QMessageBox.Ok,
        defaultButton=QtWidgets.QMessageBox.NoButton
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
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setStandardButtons(buttons)
        msg.setInformativeText(info)
        return msg.exec_()

    @classmethod
    def error(
        cls,
        parent,
        title,
        text,
        info=None,              # InformativeText
        buttons=QtWidgets.QMessageBox.Ok,
        defaultButton=QtWidgets.QMessageBox.NoButton
    ):
        """shows GeODinQGIS Infromation message box

        22.05.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE,"")
        msg = cls(parent)
        if title:
            msg.setWindowTitle("%s - %s" % (msg.windowTitle(), str(title)))
        msg.setText(text)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setStandardButtons(buttons)
        msg.setInformativeText(info)
        return msg.exec_()

    @classmethod
    def information(
        cls,
        parent,
        title,
        text,
        info=None,              # InformativeText
        buttons=QtWidgets.QMessageBox.Ok,
        defaultButton=QtWidgets.QMessageBox.NoButton
    ):
        """shows GeODinQGIS Infromation message box

        22.05.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE,"")
        msg = cls(parent)
        if title:
            msg.setWindowTitle("%s - %s" % (msg.windowTitle(), str(title)))
        msg.setText(text)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setStandardButtons(buttons)
        msg.setInformativeText(info)
        return msg.exec_()

    @classmethod
    def question(
        cls,
        parent,
        title,
        text,
        info=None,              # InformativeText
        buttons=QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No,
        defaultButton=QtWidgets.QMessageBox.NoButton
    ):
        """shows GeODinQGIS Question message box

        22.05.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE,"")
        msg = cls(parent)
        if title:
            msg.setWindowTitle("%s - %s" % (msg.windowTitle(), str(title)))
        msg.setText(text)
        msg.setIcon(QtWidgets.QMessageBox.Question)
        msg.setStandardButtons(buttons)
        msg.setInformativeText(info)
        return msg.exec_()

    @classmethod
    def warning(
        cls,
        parent,
        title,
        text,
        info=None,              # InformativeText
        buttons=QtWidgets.QMessageBox.Ok,
        defaultButton=QtWidgets.QMessageBox.NoButton
    ):
        """shows GeODinQGIS Infromation message box

        22.05.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE,"")
        msg = cls(parent)
        if title:
            msg.setWindowTitle("%s - %s" % (msg.windowTitle(), str(title)))
        msg.setText(text)
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setStandardButtons(buttons)
        msg.setInformativeText(info)
        return msg.exec_()


def plugin():
    """Plugin instance

    exception:
        KeyError                if GeODinQGIS plugin ist not installed

    27.04.2023 j.ebert
    """
    return qgis.utils.plugins['GeODinQGIS']

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
            shape = QtCore.Qt.ArrowCursor
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
