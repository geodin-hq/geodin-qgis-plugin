""" UserInterface Help Menu

Classes:
    GQgis_TBtn_Help             - PyQt Help ToolButton
    GQgis_Mnu_Help              - PyQt Help Menu

05.09.2022 J.Ebert
"""
CONTEXT_RES = "GQgis_Mnu_Help"
"""context for resource translation of QWidgets"""
import datetime
import logging
import logging.handlers
import os
import webbrowser
import zipfile

from pathlib import Path

from qgis.PyQt import (
    QtGui,
    QtWidgets
    )
import GeODinQGIS.gqgis_config as gqc
from GeODinQGIS import (
    env,
    res
)
from GeODinQGIS.ui.gqgis_bas import GQgis_Bas_Widget
from GeODinQGIS.ui.gqgis_dlg_help import GQgis_Dlg_Help
from GeODinQGIS.ui.gqgis_dlg_info import GQgis_Dlg_Info

class GQgis_TBtn_Help(QtWidgets.QToolButton, GQgis_Bas_Widget):
    """ help QToolButton for GeODinQGIS toolbar

    02.09.2022 J.Ebert
    """
    def __init__(self, parent=None):
        super().__init__()
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("")
        self._parent = parent
        self._context = CONTEXT_RES
        # set up QToolButton
        self.setObjectName(self.__class__.__name__)
        self.setIcon(self.QIcon("gApp"))
        self.setMenu(GQgis_Mnu_Help(parent))
        self.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        # translate QToolButton
        self.translateUi()
        # register QToolButton for translation
        res.Ui.append(self)

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        self.setToolTip(self.trans("Help"))


class GQgis_Mnu_Help(QtWidgets.QMenu, GQgis_Bas_Widget):
    """ help QMenu

    02.09.2022 J.Ebert
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("")
        self._parent = parent
        self._context = CONTEXT_RES
        self.__ActionHelp = None        #reference to QAction 'Help'    ~> _initActionHelp()
        self.__ActionInfo = None        #reference to QAction 'Info'    ~> _initActionInfo()
        # set up QMenu
        self.setObjectName(self.__class__.__name__)
        self.addMenu(GQgis_Mnu_Language(self))
        self.addSeparator()
        self.addAction(self._initActionHelp())
        self.addAction(self._initActionMail())
        self.addAction(self._initActionInfo())
##        self.__ActionHelp.setEnabled(False)
        # translate QMenu
        self.translateUi()
        # register QWidget for translation
        res.Ui.append(self)

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        # translate QAction 'Help'...
        self.__ActionHelp.setText(self.trans("Help"))
        self.__ActionHelp.setToolTip(self.trans("open Help..."))
        # translate QAction 'Settings'...
        self.__ActionInfo.setText(self.trans("About"))
        self.__ActionInfo.setToolTip(self.trans("show About..."))
        # translate QAction 'Mail'...
        self.__ActionMail.setText(self.trans("Support"))
        self.__ActionMail.setToolTip(gqc.SUPPORT_MAIL_TO)

    def _initActionHelp(self):
        """ returns QAction to show the help dialog/window

        02.09.2022 J.Ebert
        """
        alias = "GenericHelp"
        action = QtWidgets.QAction(self.QIcon(alias), alias, self._parent)
        action.setObjectName(f"action_{alias}")
        # for multilingual settings, see also method translateUi()
        action.setShortcut(self.trans("Alt+G"))
        # connect QAction task
        action.triggered.connect(self.execActionHelp)
        # save QAction reference
        self.__ActionHelp = action
        return action

    def _initActionInfo(self):
        """ returns QAction to show the info dialog/window

        02.09.2022 J.Ebert
        """
        alias = "GenericInfo"
        action = QtWidgets.QAction(self.QIcon(alias), alias, self._parent)
        action.setObjectName("action_Info")
        # for multilingual settings, see also method translateUi()
        action.setShortcut(self.trans("Alt+I"))
        # connect QAction task
        action.triggered.connect(self.execActionInfo)
        # save QAction reference
        self.__ActionInfo = action
        return action

    def _initActionMail(self):
        """ returns QAction to contact GeODin support

        16.08.2023 j.ebert
        """
        alias = "GenericMail"
        action = QtWidgets.QAction(self.QIcon(alias), alias, self._parent)
        action.setToolTip(gqc.SUPPORT_MAIL_TO)
        action.setObjectName("action_Mail")
        # for multilingual settings, see also method translateUi()
##        action.setShortcut(self.trans("Alt+I"))
        # connect QAction task
        action.triggered.connect(self.execActionMail)
        # save QAction reference
        self.__ActionMail = action
        return action

    def execActionHelp(self):
        """ function/Qt slot to show the info dialog/window

        16.08.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        hlpFile = env.AppHelpFolder / self.trans("GeODinQGIS_Help_en.pdf")
        webbrowser.open_new(hlpFile)
        return

    def execActionHelp_v01(self):
        """ function/Qt slot to show the info dialog/window

        02.09.2022 J.Ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        GQgis_Dlg_Help.open(None, parent=self._parent)
        return

    def execActionInfo(self):
        """ function/Qt slot to show the info dialog/window

        02.09.2022 J.Ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        GQgis_Dlg_Info(self._parent).show()
        return

    def execActionMail(self):
        """ function/Qt slot to show the info dialog/window

        02.09.2022 J.Ebert
        """
        zipName = "GeODinQGIS_logs_%s.zip" % datetime.datetime.now().strftime("%y%m%d%H%M%S")
        zipFile = gqc.zipLogFiles(env.TmpFolder / zipName)
        subject = "GeODinQGIS"
        body = self.trans("Please attach the following zip file with GeODinQGIS logs:")
        body += "%0D%0A" + zipFile
        self.log.log(gqc._LOG_TRACE,"")
        url_mailto = "mailto:%s?%ssubject=%s&body=%s" % (
            gqc.SUPPORT_MAIL_TO,
            f"cc={gqc.SUPPORT_MAIL_CC}&" if  env.isFugroDE() else "",
            subject.replace (' ', '%20'),
            body.replace (' ', '%20')
        )
        webbrowser.open(url_mailto, new=1)
        return


class GQgis_Mnu_Language(QtWidgets.QMenu, GQgis_Bas_Widget):
    """ language QMenu

    06.09.2022 J.Ebert
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("")
        self._parent = parent
        self._context = CONTEXT_RES
        # set up QMenu
        self.setupUi()
        # translate QMenu
        self.translateUi()
        # register QWidget for translation
        res.Ui.append(self)

    def translateUi(self):
        self.log.debug("")
        self.setTitle(self.trans("Language"))
        self.setIcon(self.QIcon(self.trans("gLang_EN")))

    def setupUi(self):
        """ initialises the submenu for language selection

        06.09.2022 J.Ebert
        """
        # Hinweis, zur Unterstützung der Sprache ist zusätzlich ein ResFile notwendig
        #          GeODinQGIS\res\resources_<en|de|...>.json
        # Parameter-Liste der Sprachen initialisieren (list(tuple()))
        lang_prms = [(                                  # tuple of language parameters
                "en",                                   #   language code
                (lambda: res.changeLanguage("en")),     #   function to change the language
                "gLang_EN",                             #   icon alias in resources.qrc
                u"English"),                            #   language name/menu text/QAction text
            ("de", (lambda: res.changeLanguage("de")), "gLang_DE", u"Deutsch"),
            ("fr", (lambda: res.changeLanguage("fr")), "icons/i_372F.png", u"Fran\u00E7ais", ),
            ("ru", (lambda: res.changeLanguage("ru")), "icons/i_373F.png", u"русский"),
            ("po", (lambda: res.changeLanguage("po")), "icons/flag_poland.png", u"Polski")
            ]
        # Sprachen filtern, für die ein ResFile existiert
        lang_prms = [lang for lang in lang_prms if lang[0] in res.ResFileCodes]
        # QAction zur Auswahl der Sprache instanziieren und dem Menü hinzufügen
        for lang_code, lang_slot, lang_icon, lang_name in lang_prms:
            action = QtWidgets.QAction(self.QIcon(lang_icon), lang_name, self._parent)
            action.triggered.connect(lang_slot)
            # enable/disable QAction nicht unbedingt notw., wenn
            # bereits die Sparchen gefiltert wurden, für die ein ResFile existiert
            action.setEnabled(lang_code in res.ResFileCodes)
            self.addAction(action)
        return

def main():
    pass

if __name__ == '__main__':
    main()
