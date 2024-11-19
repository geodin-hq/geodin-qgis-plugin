"""
Classes:
    GQgis_Dlg_Help              - PyQt Help Dialog (Singleton!)

05.09.2022 J.Ebert
"""
CONTEXT_RES = "GQgis_Mnu_Help"
"""context for resource translation of QWidgets"""
CONTEXT_HLP = "GQgis_Help"
"""context for resource translation of the help pages (type str)"""
import logging

from qgis.PyQt import (
    QtCore,
    QtWidgets
    )

from GeODinQGIS import (
    env,
    res
    )
from GeODinQGIS.ui.gqgis_bas import GQgis_Bas_Widget
from GeODinQGIS.ui.ui_gqgis_dlg_help import Ui_GQgis_Dlg_Help

class GQgis_Dlg_Help(QtWidgets.QDialog, GQgis_Bas_Widget):
    """PyQt Help Dialog (Singleton!)"""
    _instance = None
    """reference of the instance of the Singleton/Help Dialog"""

    def __init__(self, parent):
        super().__init__(parent)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("")
        self._context = CONTEXT_RES
        # set up QWidget
        self.ui = Ui_GQgis_Dlg_Help()
        self.ui.setupUi(self)
        # initialize help
        self._HelpFolder = env.AppHelpFolder
        """ help folder/prefix for help pages (type Path)"""
        self._HelpContext = CONTEXT_HLP
        """context for resource translation of the help pages (type str)"""
        self._HelpPage = ""
        """resource of the current help page (type str)"""
        # translate QWidget
        self.translateUi()
        # register QWidget for translation
        res.Ui.append(self)

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        # translate Ui/QWidget
        try:
            self.setWindowTitle(self.trans("GeODinQGIS - Help"))
        except:
##            self.log.error(self.ui.__dir__())
            self.log.error("", exc_info=True)
        # reload the help page for the current language setting
        if self._HelpPage:
            self.load(self._HelpPage)
        return

    def load(self, page):
        # akt. Seite speichern/merken
        self._HelpPage = page
        # akt. Seite "übersetzen"/entsprechend der akt. Sparcheinstellung wählen
        page = self._HelpFolder / res.translate(CONTEXT_HLP, page)
        # akt. Seite laden/anzeigen
        # Hinweis:  QtCore.QUrl("file:///C:/Users/.../GeODinQGIS/help/index.html?language=en")
        self.ui.webView.load(QtCore.QUrl(f"file:///{page.as_posix()}"))
        return

    @classmethod
    def open(
        cls,
        page,
        parent=None
        ):
        """Opens the Help Dialog and loads the Help Page

        Args:
            page    (str)
        KWArgs:
            parent  (QtWidget)

        """
        if not cls._instance:
            # cls._instance = cls({None|parent})
            #   parent  -> Help Dialog immer vor dem Parent-Window
            #   None    -> Parent-Window kann auch in den Vodergrund geholt werden
            cls._instance = cls(None)
            # Nur beim Instanziieren des Help Dialogs ggf. Default Help Page setzen
            if not page:
                page = "help_en.htm"
        cls._instance.log.debug(f"GQgis_Dlg_Help ID: {id(cls._instance)}")
        if page:
            cls._instance.load(page)
        cls._instance.show()
        return

def main():
    pass

if __name__ == '__main__':
    main()
