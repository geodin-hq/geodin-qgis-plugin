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
    QtCore,
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
        # 10/2026: gear icon (with menu arrow) instead of the '?' icon, the menu contains
        #   language, layer styles, help, support and about
        #   Rollback: uncomment the next line and remove the two lines after it
        # self.setIcon(self.QIcon("gApp"))
        # gear icon only, like the other toolbar buttons (res/svg/menu_gear.svg, alias gMenu;
        #   the QGIS icon mActionOptions.svg looked like a wrench in the small size)
        self.setText("GeoDinQGIS")      # accessible name / shown only if the toolbar shows texts
        self.setIcon(self.QIcon("gMenu"))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setMenu(GQgis_Mnu_Help(parent))
        self.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        # translate QToolButton
        self.translateUi()
        # register QToolButton for translation
        res.Ui.append(self)

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        self.setToolTip(self.trans("GeoDinQGIS menu: language, layer styles, help, support"))       # 10/2026, before: "Help"


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
        # 10/2026: style files (*.qml) for object and measurement point layers
        self.addAction(self._initActionStyles())
        # 11/2026: selection radius of the selection tool
        self.addAction(self._initActionSelectionRadius())
        # 10/2026: open the object data in GeoDin with the tools 'Hotlink' and 'Selection'
        #   replaced by the menu of the toolbar button 'Selection' (gqgis_ctl_tools_v2332.py)
        # self.addAction(self._initActionObjectData())
        self.__ActionObjectData = None
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
        # 10/2026: 'About' -> 'About GeoDinQGIS...' (as in QGIS: Help » About)
        self.__ActionInfo.setText(self.trans("About GeoDinQGIS..."))
        self.__ActionInfo.setToolTip(self.trans("Show version and system information"))
        # translate QAction 'Layer styles' (10/2026)
        self.__ActionStyles.setText(self.trans("Layer styles..."))
        self.__ActionStyles.setToolTip(self.trans("Style files for object and measurement point layers"))
        # translate QAction 'Selection radius' (11/2026)
        self.__ActionSelectionRadius.setText(self.trans("Selection radius..."))
        self.__ActionSelectionRadius.setToolTip(
            self.trans("Selection tool: distance in pixels in which a click finds an object")
        )
        # translate QAction 'Open object data' (10/2026)
        if self.__ActionObjectData:
            self.__ActionObjectData.setText(self.trans("Open object data in GeoDin"))
            self.__ActionObjectData.setToolTip(
                self.trans("Hotlink and selection: open the object data of the object in GeoDin")
            )
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

    def _initActionStyles(self):
        """ returns QAction to define the layer styles (*.qml) for objects and measurement points

        10/2026
        """
        from qgis.core import QgsApplication
        icon = QgsApplication.getThemeIcon("propertyicons/symbology.svg")
        action = QtWidgets.QAction(icon, "Layer styles...", self._parent)
        action.setObjectName("action_Styles")
        action.triggered.connect(self.execActionStyles)
        self.__ActionStyles = action
        return action

    def _initActionObjectData(self):
        """ returns checkable QAction: open the object data in GeoDin (Hotlink, Selection)

        10/2026
        """
        from GeODinQGIS.ui.gqgis_options import openObjectDataEnabled
        action = QtWidgets.QAction("Open object data in GeoDin", self._parent)
        action.setObjectName("action_ObjectData")
        action.setCheckable(True)
        action.setChecked(openObjectDataEnabled())
        action.toggled.connect(self.execActionObjectData)
        self.__ActionObjectData = action
        return action

    def execActionObjectData(self, checked):
        from GeODinQGIS.ui.gqgis_options import setAfterSelectionMode
        setAfterSelectionMode("hotlink", "objectdata" if checked else "select")

    def _initActionSelectionRadius(self):
        """ returns QAction to set the selection radius of the selection tool (11/2026)"""
        from qgis.core import QgsApplication
        icon = QgsApplication.getThemeIcon("mActionSelectRectangle.svg")
        action = QtWidgets.QAction(icon, "Selection radius...", self._parent)
        action.setObjectName("action_SelectionRadius")
        action.triggered.connect(self.execActionSelectionRadius)
        self.__ActionSelectionRadius = action
        return action

    def execActionSelectionRadius(self):
        from GeODinQGIS.ui import gqgis_options as opts
        lo, hi = opts.SELECTION_RADIUS_RANGE
        val, ok = QtWidgets.QInputDialog.getInt(
            self._parent,
            self.trans("Selection radius"),
            self.trans("Selection tool: a click finds the nearest object within (pixels, default %d):")
            % opts.SELECTION_RADIUS_DEFAULT,
            opts.selectionRadiusPx(), lo, hi, 1
        )
        if ok:
            opts.setSelectionRadiusPx(val)
        return

    def execActionStyles(self):
        from GeODinQGIS.ui.gqgis_styles import showStylesDialog
        showStylesDialog(self._parent)

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
        # webbrowser.open_new(hlpFile)
        # 10/2026: webbrowser.open_new(Path) did not open the PDF (QGIS 4 / Python 3.12+,
        #   no error) - open it with the default PDF program, message if it fails
        self.log.info("Help file: %s", hlpFile)
        if not hlpFile.is_file():
            self.log.error("Help file not found: %s", hlpFile)
            QtWidgets.QMessageBox.warning(
                self._parent, self.trans("Help"),
                "%s\n%s" % (self.trans("The help file was not found:"), hlpFile)
            )
            return
        try:
            os.startfile(str(hlpFile))
        except Exception:
            self.log.warning("os.startfile failed: %s", hlpFile, exc_info=True)
            opened = QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(hlpFile)))
            if not opened:
                QtWidgets.QMessageBox.warning(
                    self._parent, self.trans("Help"),
                    "%s\n%s" % (self.trans("The help file could not be opened (is a PDF reader installed?):"), hlpFile)
                )
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
        # 10/2026: support e-mail with system information, COM state and optional DDX/geodin.ini
        #   (Outlook draft with ZIP attached, fallback mailto), see ui/gqgis_support.py
        #   Rollback: remove the next 3 lines and uncomment the old code below.
        from GeODinQGIS.ui.gqgis_support import createSupportMail
        createSupportMail(self._parent)
        return
##        zipName = "GeODinQGIS_logs_%s.zip" % datetime.datetime.now().strftime("%y%m%d%H%M%S")
##        zipFile = gqc.zipLogFiles(env.TmpFolder / zipName)
##        subject = "GeODinQGIS"
##        body = self.trans("Please attach the following zip file with GeoDinQGIS logs:")
##        body += "%0D%0A" + zipFile
##        self.log.log(gqc._LOG_TRACE,"")
##        url_mailto = "mailto:%s?%ssubject=%s&body=%s" % (
##            gqc.SUPPORT_MAIL_TO,
##            f"cc={gqc.SUPPORT_MAIL_CC}&" if  env.isFugroDE() else "",
##            subject.replace (' ', '%20'),
##            body.replace (' ', '%20')
##        )
##        webbrowser.open(url_mailto, new=1)
##        return


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
        # 10/2026: texts/icons of the language entries (current setting marked)
        if getattr(self, '_langActions', None):
            self._updateLanguageActions()

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
        # 10/2026: first entry 'Automatic (QGIS language)' (default)
        #   The current setting is marked with a green check mark on the flag and bold text.
        #   (Qt check marks are not visible in QGIS/Windows for menu entries with an icon, so the
        #    actions are not checkable; the check mark is drawn in _checkedIcon().)
        self._langNames = {code: name for code, _slot, _icon, name in lang_prms}
        self._langIcons = {code: icon for code, _slot, icon, _name in lang_prms}
        self._langActions = {}
        self._actionAuto = QtWidgets.QAction("Automatic (QGIS language)", self._parent)
        self._actionAuto.triggered.connect(lambda: res.changeLanguage("auto"))
        self.addAction(self._actionAuto)
        self._langActions["auto"] = self._actionAuto
        self.addSeparator()
        # QAction zur Auswahl der Sprache instanziieren und dem Menü hinzufügen
        for lang_code, lang_slot, lang_icon, lang_name in lang_prms:
            action = QtWidgets.QAction(self.QIcon(lang_icon), lang_name, self._parent)
            action.triggered.connect(lang_slot)
            # enable/disable QAction nicht unbedingt notw., wenn
            # bereits die Sparchen gefiltert wurden, für die ein ResFile existiert
            action.setEnabled(lang_code in res.ResFileCodes)
            self._langActions[lang_code] = action
            self.addAction(action)
        self.aboutToShow.connect(self._updateLanguageActions)
        return

    def _updateLanguageActions(self):
        """updates text and icon of the language entries; marks the current setting

        'Automatic' shows the flag and the name of the detected QGIS language.

        10/2026
        """
        mode = getattr(res, 'LanguageMode', None) or res.LanguageCode
        autoCode = res.AutoLanguageCode if hasattr(res, 'AutoLanguageCode') else res.LanguageCode
        self._actionAuto.setText(
            self.trans("Automatic (QGIS language: %s)") % self._langNames.get(autoCode, autoCode)
        )
        self._actionAuto.setToolTip(self.trans("Use the language of the QGIS user interface"))
        for code, action in self._langActions.items():
            iconAlias = self._langIcons.get(autoCode if code == "auto" else code, "")
            current = (code == mode)
            action.setIcon(self._checkedIcon(iconAlias) if current else self.QIcon(iconAlias))
            font = action.font()
            font.setBold(current)
            action.setFont(font)
        return

    def _checkedIcon(self, alias, size=32):
        """returns the flag icon with a green check mark (bottom right)

        10/2026
        """
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtGui.QColor(0, 0, 0, 0))
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.QIcon(alias).paint(painter, QtCore.QRect(0, 0, size, size))
        # green circle with white border and white check mark
        d = int(size * 0.62)
        badge = QtCore.QRectF(size - d - 0.5, size - d - 0.5, d, d)
        painter.setPen(QtGui.QPen(QtGui.QColor("#ffffff"), size * 0.06))
        painter.setBrush(QtGui.QColor("#2e9d4a"))
        painter.drawEllipse(badge)
        pen = QtGui.QPen(QtGui.QColor("#ffffff"), size * 0.09)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        x, y = badge.x(), badge.y()
        path = QtGui.QPainterPath()
        path.moveTo(x + d * 0.27, y + d * 0.52)
        path.lineTo(x + d * 0.44, y + d * 0.69)
        path.lineTo(x + d * 0.74, y + d * 0.35)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        painter.end()
        return QtGui.QIcon(pixmap)

def main():
    pass

if __name__ == '__main__':
    main()
