"""
Classes:
    GQgis_Dlg_Info              - PyQt Info Dialog (modal)

05.09.2022 J.Ebert
"""
CONTEXT_RES = "GQgis_Mnu_Help"
"""context for resource translation of QWidgets"""
import logging

from qgis.PyQt import QtWidgets

from GeODinQGIS import (
    app,
    res
    )
from GeODinQGIS.ui.gqgis_bas import GQgis_Bas_Widget
from GeODinQGIS.ui.ui_gqgis_dlg_info import Ui_GQgis_Dlg_Info

class GQgis_Dlg_Info(QtWidgets.QDialog, GQgis_Bas_Widget):
    """PyQt Info Dialog (modal)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("")
        self._context = CONTEXT_RES
        self.ui = Ui_GQgis_Dlg_Info()
        self.ui.setupUi(self)
        # translate QWidget
        self.translateUi()
        # register QWidget for translation
        # 09/2022 Note
        #   Registration for the translation is not necessary, since
        #   the dialogue is modal and is always instantiated anew
        ##  res.Ui.append(self)
        # rebuild and set About text...
        self.ui.textAbout.setPlainText(app.InfoText())

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        # translate Ui/QWidget
        try:
            self.setWindowTitle(self.trans("GeODinQGIS - About"))
            self.ui.labelAbout.setText(self.trans("GeODinQGIS   %s") % app.Version)
        except:
##            self.log.error(self.ui.__dir__())
            self.log.error("", exc_info=True)
        return

def main():
    pass

if __name__ == '__main__':
    main()
