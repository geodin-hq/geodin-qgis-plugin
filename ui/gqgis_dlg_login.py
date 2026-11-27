"""
Classes:
    GQgis_Dlg_Login             - PyQt Login Dialog (Singleton!)

25.04.2023 J.Ebert
"""
CONTEXT_RES = "GQgis_Dlg_Login"
"""context for resource translation of QWidgets"""
import logging

from qgis.PyQt import (
    QtWidgets
    )

import GeODinQGIS.gqgis_config as gqc

from GeODinQGIS import (
    res
    )
from GeODinQGIS.ui.gqgis_bas import (
    GQgis_Bas_Widget
)
from GeODinQGIS.ui.ui_gqgis_dlg_login import Ui_GQgis_Dlg_Login

class GQgis_Dlg_Login(QtWidgets.QDialog, GQgis_Bas_Widget):
    """PyQt Login Dialog (Singleton!)"""

    def __init__(self, parent):
        super().__init__(parent)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.log(gqc._LOG_TRACE,"")
        self._context = CONTEXT_RES
        # initialize DDX-Dialog properties
        pass
        # set up QWidget
        self.ui = Ui_GQgis_Dlg_Login()
        self.ui.setupUi(self)
        # translate QWidget
        self.translateUi()
        # register QWidget for translation
        res.Ui.append(self)

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        # translate Ui/QWidget
        try:
            self.setWindowTitle(self.trans("GeoDinQGIS - Login"))
            self.ui.dbNameLabel.setText(self.trans("Database:"))
            self.ui.dbUserLabel.setText(self.trans("Username:"))
            self.ui.dbPasswordLabel.setText(self.trans("Password:"))
        except Exception:
            self.log.error("", exc_info=True)
        return

    def login(self):
        return self.ui.dbUserLineEdit.text(), self.ui.dbPasswordLineEdit.text()

    @classmethod
    def instance(
        cls,
        dbName,
        dbUser='',
        dbPassword='',
        parent=None
        ):
        """Returns instance of login dialog 'GQgis_Dlg_Login'

        Args:
            dbName      (str)
        KWArgs:
            dbUser      (str)
            dbPassword  (str)
            parent      (QtWidget)

        20.07.2023 j.ebert
        """
        if not hasattr(cls, '_instance'):
            cls._instance = super(GQgis_Dlg_Login, cls).__new__(cls)
        # Login-Dialog öffnen/ausführen...
        cls._instance = cls(parent)
        cls._instance.ui.dbNameLabel2.setText(dbName)
        cls._instance.ui.dbUserLineEdit.setText(None)
        cls._instance.ui.dbPasswordLineEdit.setText(None)
        if dbUser:
            cls._instance.ui.dbUserLineEdit.setText(dbUser)
            if dbPassword:
                cls._instance.ui.dbPasswordLineEdit.setText(dbPassword)
        return cls._instance

def main():
    pass

if __name__ == '__main__':
    main()
