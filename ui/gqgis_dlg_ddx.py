"""
Classes:
    GQgis_Act_DDX               - PyQt Action to open PyQt DDX Dialog
    GQgis_Dlg_DDX               - PyQt DDX Dialog (Singleton!)

25.04.2023 J.Ebert
"""
CONTEXT_RES = "GQgis_Dlg_DDX"
"""context for resource translation of QWidgets"""
CONTEXT_HLP = "GQgis_DDX"
"""context for resource translation of the help pages (type str)"""
import logging
import os
from pathlib import Path

from qgis.PyQt import (
    QtCore,
    QtWidgets
    )

import GeODinQGIS.gqgis_config as gqc
import GeODinQGIS.gqgis_base as gqb

from GeODinQGIS import (
    app,
    res,
)
from GeODinQGIS.ui.gqgis_bas import (
    GQgis_Bas_Widget,
    GQgis_MsgBox as MsgBox
)
from GeODinQGIS.ui.ui_gqgis_dlg_ddx import Ui_GQgis_Dlg_DDX
from GeODinQGIS.dm.ddx import GxDDX
from GeODinQGIS.gx.comreg import GxComReg
import GeODinQGIS.ui.gqgis_comreg as comreg


# 10/2026: recently used DDX files (QGIS user settings) ------------------------------------
_KEY_RECENT_DDX = "GeODinQGIS/recentDDXFiles"
_MAX_RECENT_DDX = 10


def recentDDXFiles():
    """recently used DDX files (list(str)), most recent first"""
    try:
        import qgis.core
        val = qgis.core.QgsSettings().value(_KEY_RECENT_DDX, [])
    except Exception:
        return []
    if isinstance(val, str):
        val = [val] if val else []
    return [str(v) for v in (val or []) if v]


def addRecentDDXFile(path):
    """puts the DDX file at the top of the recently used DDX files"""
    try:
        import qgis.core
        path = os.path.abspath(path)
        files = [f for f in recentDDXFiles()
                 if os.path.normcase(os.path.abspath(f)) != os.path.normcase(path)]
        files.insert(0, path)
        qgis.core.QgsSettings().setValue(_KEY_RECENT_DDX, files[:_MAX_RECENT_DDX])
    except Exception:
        logging.getLogger(f"{gqc._LOG_PARENTS}GQgis_Dlg_DDX").debug("", exc_info=True)

class GQgis_Act_DDX(QtWidgets.QAction, GQgis_Bas_Widget):
    """PyQt Action to open PyQt DDX Dialog

    25.04.2023 J.Ebert
    """
    def __init__(self, parent):
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
        self.setIcon(self.QIcon("gDDX"))
        self.triggered.connect(self.execute)
        # translate QAction
        self.translateUi()
        # register QAction for translation
        res.Ui.append(self)

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        self.setText(self.trans("GeoDinQGIS DDX file"))
        self.setToolTip(self.trans("GeoDinQGIS DDX file"))

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
        # 10/2026: the DataDictionary dialog is always available, also if the GeoDin COM server
        #   is not registered (app.isAvailable() is False), because the GeoDin COM server
        #   can be registered in this dialog
        enabled = True
        if (
            isinstance(widget, QtWidgets.QWidget) and
            (widget.isEnabled() != enabled)
        ):
            widget.setEnabled(enabled)
        return

    def execute(self):
        """executes QAction

        25.04.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        GQgis_Dlg_DDX.open(self._parent)
        return

class GQgis_Dlg_DDX(QtWidgets.QDialog, GQgis_Bas_Widget):
    """PyQt DDX Dialog (Singleton!)"""
##    _instance = None
##    """reference of the instance of the Singleton/Help Dialog"""
    _FileDlgFilter_File = f"%s (*{GxDDX.suffix()})"
    _FileDlgFilter_Conf = "%s (geodin.ini)"

    _INFO = 20
    _WARNING = 30
    _ERROR = 40

    # 10/2026, QGIS 4: PyQt6/sip crashes (segfault) if __new__ of a Qt class is overridden,
    #   so the singleton is no longer implemented via __new__
    #   a new (modal) dialog is created for each call of open()

    def __init__(self, parent):
        super().__init__(parent)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.log(gqc._LOG_TRACE,"")
        self._context = CONTEXT_RES
        # 10/2026: status symbols rendered at 16 px - the SVG icons have different sizes
        #   (info.svg 36 px, status_*.svg 20 px), QPixmap(alias) used their own size
        #   (old: self.QPixmap("GenericInfo_16") etc.)
        statusSize = QtCore.QSize(16, 16)
        self._QPixmap = {
            self._INFO: self.QIcon("GenericInfo_16").pixmap(statusSize),
##            self._INFO: self.QPixmap("GenericNew_16"),
            self._WARNING: self.QIcon("GenericWarning_16").pixmap(statusSize),
            self._ERROR: self.QIcon("GenericError_16").pixmap(statusSize),
        }
        # initialize DDX-Dialog properties
        self._DDX = None
        # 04/2023 j.ebert, Anmerkung
        #   Damit alle Parameter bei der Initialisierung des Widgets validiert werden,
        #   Files mit Zeichen initialisieren, das im Windows-Filenamen nicht erlaubt ist
        self.__oldFile = "?"
        self.__oldData = "?"
        self.__oldConf = "?"
        self.__oldSave = True
        self.__hasFileError = False
        self.__hasDataError = False
        self.__hasConfError = False
        # set up QWidget
        self.ui = Ui_GQgis_Dlg_DDX()
        self.ui.setupUi(self)
        # 10/2026: button 'Save' next to OK/Cancel (instead of the small icon button next to
        #   the DDX file); the icon button stays as hidden state holder (pushButton_Save)
        self._btnSave = self.ui.buttonBox.addButton(
            "Save", QtWidgets.QDialogButtonBox.ButtonRole.ActionRole
        )
        self._btnSave.setEnabled(False)
        self._btnSave.clicked.connect(self._clicked_BtnSave)
        self.ui.pushButton_Save.setVisible(False)
        # 10/2026: only 'Apply' (OK: save if changed, load the DDX, close) and 'Close' (Cancel)
        #   - the separate 'Save' button is hidden (see accept())
        self._btnSave.setVisible(False)
        # 10/2026: DDX file as editable combo box with the recently used DDX files and the
        #   entries 'Open other DDX file...' / 'Create new DDX file...'
        #   (replaces the buttons 'Open' next to the field and 'New' top right - both hidden;
        #   the line edit lineEdit_File is kept as line edit of the combo box)
        self._cboFile = QtWidgets.QComboBox(self)
        self._cboFile.setEditable(True)
        self._cboFile.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
        self._cboFile.setSizeAdjustPolicy(
            QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self._cboFile.setMinimumContentsLength(30)
        self.ui.gridLayout_2.replaceWidget(self.ui.lineEdit_File, self._cboFile)
        self._cboFile.setLineEdit(self.ui.lineEdit_File)
        self._cboFile.activated.connect(self._activated_CboFile)
        self.ui.pushButton_File.setVisible(False)
        self.ui.pushButton_New.setVisible(False)
        # 10/2026: initial dialog size, see _initDialogSize()
        self._initDialogSize()
        # initialize ...
        self.validateUi()
        self.connectUi()
        # translate QWidget
        self.translateUi()
        # register QWidget for translation
        res.Ui.append(self)

    def connectUi(self):
        """connect QWidget signals

        14.04.2023 j.ebert
        """
        self.ui.checkBox_SaveRelPaths.stateChanged.connect(self._changed_checkBox)
        self.ui.lineEdit_File.editingFinished.connect(self._editingFinished_EdtFile)
        self.ui.lineEdit_Data.editingFinished.connect(self._editingFinished_EdtData)
        self.ui.lineEdit_Conf.editingFinished.connect(self._editingFinished_EdtConf)
        self.ui.pushButton_Save.clicked.connect(self._clicked_BtnSave)
        self.ui.pushButton_New.clicked.connect(self._clicked_BtnNew)
        self.ui.pushButton_File.clicked.connect(self._clicked_BtnFile)
        self.ui.pushButton_Data.clicked.connect(self._clicked_BtnData)
        self.ui.pushButton_Conf.clicked.connect(self._clicked_BtnConf)
        # 10/2026: GeoDin COM server registration
        self.ui.pushButton_ComReg.clicked.connect(self._clicked_BtnComReg)
        return

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        # translate Ui/QWidget
        try:
            self.setWindowTitle(self.trans("GeoDinQGIS - DataDictionary"))
            self.ui.label_File.setText(
                self._FileDlgFilter_File % self.trans("GeoDinQGIS DDX file")
            )
            self.ui.label_Data.setText(self.trans("GeoDinQGIS data folder"))
            self.ui.label_Conf.setText(
                self._FileDlgFilter_Conf % self.trans("GeoDin configuration file")
            )
            self.ui.checkBox_SaveRelPaths.setText(self.trans("Save relative paths"))
            self.ui.checkBox_AutoLoad.setText(
                self.trans("Load this configuration automatically when QGIS starts")
            )
            self.ui.pushButton_ComReg.setText(self.trans("Register GeoDin COM server..."))
            self.ui.pushButton_ComReg.setToolTip(
                self.trans("Registers the GeoDin application of the chosen GeoDin configuration as COM server (administrator rights required)")
            )
            self.ui.checkBox_AutoLoad.setToolTip(
                self.trans("The DDX file is loaded at QGIS start and for QGIS projects without GeoDinQGIS settings")
            )
            self.ui.pushButton_New.setToolTip(self.trans("New GeoDinQGIS DDX file"))
            self.ui.pushButton_Save.setToolTip(self.trans("Save GeoDinQGIS DDX file"))
            # 10/2026: buttons of the button box (independent of the QGIS/Qt language)
            self._btnSave.setText(self.trans("Save"))
            self._btnSave.setToolTip(self.trans("Save GeoDinQGIS DDX file"))
            # self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setText(
            #     self.trans("Cancel")
            # )
            # 10/2026: 'Apply' (save if changed, load the DDX, close) and 'Close'
            btnOk = self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
            btnOk.setText(self.trans("Apply"))
            btnOk.setToolTip(self.trans("Save the DDX file (if changed), load it in GeoDinQGIS and close the dialog"))
            btnCancel = self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
            btnCancel.setText(self.trans("Close"))
            btnCancel.setToolTip(self.trans("Close the dialog without loading the DDX file (unsaved changes are discarded)"))
            self.ui.pushButton_File.setToolTip(self.trans("Open GeoDinQGIS DDX file"))
            self.ui.pushButton_Data.setToolTip(self.trans("Open GeoDinQGIS data folder"))
            self.ui.pushButton_Conf.setToolTip(self.trans("Open GeoDin configuration file"))
            # 10/2026: combo box with the recently used DDX files
            self._cboFile.setToolTip(self.trans("Recently used DDX files, open another or create a new DDX file"))
            self._fillCboFile()
        except Exception:
            self.log.error("", exc_info=True)
        return

    def validateUi(self):
        """validate DDX Dialog

        29.04.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # 04/2023 j.ebert, Anmerkung
        #   Python-Befehle zum Setzen von dlg_OK genau so und NICHT anders(!!!), da
        #   sowohl die Logik, als auch die Reihenfolge der Abarbeitung und Auswertung relevant ist.
        dlg_OK = True
        dlg_OK = bool(self._validate_File()) and dlg_OK
        dlg_OK = bool(self._validate_Data()) and dlg_OK
        dlg_OK = bool(self._validate_Conf()) and dlg_OK

        if (dlg_OK and bool(self._DDX)):
            self.log.debug('%s ...', self.__class__.__name__)
            self._DDX.SaveRelPaths = self.ui.checkBox_SaveRelPaths.isChecked()
            self._DDX.Data = self.ui.lineEdit_Data.text()
            self._DDX.Conf = self.ui.lineEdit_Conf.text()
            self.log.debug(f"""
    DDX.File            {self._DDX.File}
    DDX.SaveRelPaths    {str(self._DDX.SaveRelPaths)}
    DDX.Data            {self._DDX.Data}
    DDX.Conf            {self._DDX.Conf}
    DDX.isDirty         {str(self._DDX.isDirty)}
    DDX.isNew           {str(self._DDX.isNew)}
            """)
        elif not self.ui.lineEdit_File.text():
            self.log.debug("DDX file is not set")
        else:
            self.log.debug("DDX file error")

        # Save-Button aktivieren/deaktivieren...
        self.ui.pushButton_Save.setEnabled(
            dlg_OK and
            (bool(self._DDX) and self._DDX.isDirty)
        )
        # 10/2026: button 'Save' in the button box
        if getattr(self, '_btnSave', None) is not None:
            self._btnSave.setEnabled(self.ui.pushButton_Save.isEnabled())
            self._btnSave.setDefault(self.ui.pushButton_Save.isEnabled())
        # 10/2026: status of the GeoDin COM server registration for the chosen geodin.ini
        self._update_ComReg(dlg_OK)
        # 10/2026: option 'auto-load' is only enabled for a valid DDX file
        self.ui.checkBox_AutoLoad.setEnabled(
            dlg_OK and bool(self.ui.lineEdit_File.text())
        )
        # OK-Button aktivieren/deaktivieren...
        #   OK-Button kann nur aktiv sein...
        #   wenn der Dlg okay is, also alle Prms fehlerfrei validiert wurden und
        #   wenn der Save-Button nicht aktiv ist, also das DDX gespeichert/nicht geändert wurde
        # self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(
        #     dlg_OK and
        #     (not self.ui.pushButton_Save.isEnabled())
        # )
        # 10/2026: 'Apply' saves a changed DDX itself (accept()), so it only depends on dlg_OK
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(dlg_OK)
        return

    def _validate_Conf(self):
        self.log.log(gqc._LOG_TRACE,"")
        prm_ToolTip = ()
        if ((not self.ui.lineEdit_Conf.isEnabled()) or self.__hasFileError):
            # Wenn Widget Conf NICHT enable ist oder
            # wenn Prm File einen Fehler hat...
            self.ui.lineEdit_Conf.setText("")
            self.__oldConf = "?"
        else:
            # Wenn Prm File keinen Fehler ToolTip hat...
            # 10/2026: empty field -> geodin.ini of the GeoDin application started last
            #   (registry HKCU\Software\GeODin-System\System\RootDir); the user still has to save
            lastIni = ""
            if not self.ui.lineEdit_Conf.text():
                try:
                    from GeODinQGIS.gx.system import GxReg
                    lastIni = GxReg.lastGeoDinIni()
                except Exception:
                    self.log.debug("", exc_info=True)
                if lastIni:
                    self.log.info("geodin.ini of the GeoDin application started last: %s", lastIni)
                    self.ui.lineEdit_Conf.setText(lastIni)
            if not self.ui.lineEdit_Conf.text():
                # Wenn kein GeODin-File gesetzt ist...
                prm_ToolTip = (self._ERROR, "GeoDin file is required")
            else:
                ddx_Conf = self.ui.lineEdit_Conf.text()
                try:
                    ddx_Path = Path(ddx_Conf)
                    ddx_Path.resolve()
                    if ddx_Path.name.lower() != 'geodin.ini':
                        prm_ToolTip = (self._ERROR, self.trans("No GeoDin file (geodin.ini)!"))
                    elif not ddx_Path.is_absolute():
                        prm_ToolTip = (self._ERROR, self.trans("No absolute GeoDin file path!"))
                    elif not Path(self.ui.lineEdit_Conf.text()).is_file():
                        prm_ToolTip = (self._ERROR, self.trans("No such GeoDin file"))
                    elif lastIni:
                        prm_ToolTip = (self._INFO, self.trans(
                            "geodin.ini of the GeoDin application started last (please check and save)"))
                    self.ui.lineEdit_Conf.setText(str(ddx_Path))
                except OSError:
                    self.log.error("OS error with GeoDin file '%s'", ddx_Conf, exc_info=True)
                    prm_ToolTip = (self._ERROR, self.trans("OS error with GeoDin file!"))
                except Exception:
                    self.log.error(
                        "Unkown error with data folder '%s'", ddx_Conf,
                        exc_info=True
                    )
                    prm_ToolTip = (self._ERROR, self.trans("Unkown error with data folder!"))
            # Attr. __oldFile und __hasFileError aktualisieren - Prm File wurde validiert
            self.__oldConf = self.ui.lineEdit_Conf.text()
            self.__hasConfError = bool(prm_ToolTip) and (prm_ToolTip[0] == self._ERROR)
            # Aktualisierung der Error-Message
            if prm_ToolTip:
                self.ui.label_ConfImg.setPixmap(self._QPixmap[prm_ToolTip[0]])
                self.ui.label_ConfImg.setToolTip(prm_ToolTip[1])
            else:
                self.ui.label_ConfImg.setToolTip("")
        # Data Widgets aktualisieren...
        # 05.05.2023 j.ebert, Anmerkung
        #   Widget 'lineEdit_Conf' selbst wird nur in _validate_File() enable/disable gesetzt in
        #   Abhängigkeit von Attr. '__hasFileError' und auch davon, ob Prm File gesetzt ist.
        self.ui.pushButton_Conf.setEnabled(self.ui.lineEdit_Conf.isEnabled())
        self.ui.label_ConfImg.setVisible(
            self.ui.lineEdit_Conf.isEnabled() and bool(self.ui.label_ConfImg.toolTip())
        )
        # Validierung von Prm Conf ist OK,
        # wenn der Prm Conf keinen Fehler hat
        return (not self.__hasConfError)

    def _validate_Data(self):
        self.log.log(gqc._LOG_TRACE,"")
        prm_ToolTip = ()
        if ((not self.ui.lineEdit_Data.isEnabled()) or self.__hasFileError):
            # Wenn Widget Data NICHT enable ist oder
            # wenn Prm File einen Fehler hat...
            self.ui.lineEdit_Data.setText("")
            self.__oldData = "?"
        elif self.__oldData == self.ui.lineEdit_Data.text():
            # Wenn Attr. __oldData und Prm Data identisch sind, also
            # wenn der Prm data bereits validiert wurde,
            # dann bleiben hasDataError und ToolTip/Error-Message unverändert
            pass
        else:
            # Wenn Prm File keinen Fehler hat und
            # wenn Attr. __oldData und Prm data NICHT identisch sind, also
            # wenn der Prm Data noch nicht validiert wurde...
            if not self.ui.lineEdit_Data.text():
                # Wenn kein Data-Folder gesetzt ist...
                prm_ToolTip = (self._ERROR, "Data folder is required")
            else:
                ddx_Data = self.ui.lineEdit_Data.text()
                try:
                    ddx_Path = Path(ddx_Data)
                    ddx_Path.resolve()
                    if not ddx_Path.is_absolute():
                        prm_ToolTip = (self._ERROR, self.trans("No absolute data folder path!"))
                    elif self._DDX.isNew:
                        if Path(ddx_Data).exists():
                            prm_ToolTip = (self._WARNING, self.trans("Data folder already exists!"))
                        else:
                            prm_ToolTip = (self._INFO, self.trans("New data folder..."))
                    elif not Path(ddx_Data).exists():
                        prm_ToolTip = (self._ERROR, self.trans("No such data folder!"))
                    self.ui.lineEdit_Data.setText(str(ddx_Path))
                except OSError:
                    self.log.error("OS error with data folder '%s'", ddx_Data, exc_info=True)
                    prm_ToolTip = (self._ERROR, self.trans("OS error with data folder!"))
                except Exception:
                    self.log.error(
                        "Unkown error with data folder '%s'", ddx_Data,
                        exc_info=True
                    )
                    prm_ToolTip = (self._ERROR, self.trans("Unkown error with data folder!"))
            # Attr. __oldFile und __hasFileError aktualisieren - Prm File wurde validiert
            self.__oldData = self.ui.lineEdit_Data.text()
            self.__hasDataError = bool(prm_ToolTip) and (prm_ToolTip[0] == self._ERROR)
            # Aktualisierung der Error-Message
            if prm_ToolTip:
                self.ui.label_DataImg.setPixmap(self._QPixmap[prm_ToolTip[0]])
                self.ui.label_DataImg.setToolTip(prm_ToolTip[1])
            else:
                self.ui.label_DataImg.setToolTip("")
        # Data Widgets aktualisieren...
        # 05.05.2023 j.ebert, Anmerkung
        #   Widget 'lineEdit_Data' selbst wird nur in _validate_File() enable/disable gesetzt in
        #   Abhängigkeit von Attr. '__hasFileError' und auch davon, ob Prm File gesetzt ist.
        self.ui.pushButton_Data.setEnabled(self.ui.lineEdit_Data.isEnabled())
        self.ui.label_DataImg.setVisible(
            self.ui.lineEdit_Data.isEnabled() and bool(self.ui.label_DataImg.toolTip())
        )
        # Validierung von Prm Data ist OK,
        # wenn der Prm Data keinen Fehler hat
        return (not self.__hasDataError)

    def _validate_File(self):
        self.log.log(gqc._LOG_TRACE,"")
        prm_ToolTip = ()
        if self.__oldFile == self.ui.lineEdit_File.text():
            # Wenn Attr. __oldFile und Prm File identisch sind, also
            # wenn der Prm File bereits validiert wurde,
            # dann bleiben hasFileError und ToolTip/Error-Message unverändert
            pass
        else:
            # Wenn Attr. __oldFile und Prm File NICHT identisch sind, also
            # Wenn der Prm File noch nicht validiert wurde...
            self._DDX = None
            ddx_Path = None
            ddx_Save = True
            ddx_Data = ""
            ddx_Conf = ""
            if not self.ui.lineEdit_File.text():
                # Wenn kein DDX-File gesetzt ist...
##                prm_ToolTip = (self._ERROR, "DDX file required")
                # dann keinen ToolTip/keinen Fehler setzen
                # dann wird GeODinQGIS für das aktuelle QGIS-Projekt deaktiviert
                pass
            else:
                # Wenn ein DDX-File gesetzt ist...
                try:
                    ddx_Path = Path(self.ui.lineEdit_File.text())
                    ddx_Path.resolve()
                    if not ddx_Path.is_absolute():
                        raise gqb.GxFileError("No absolute file path '%s'", ddx_Path)
                    ddx_Path = ddx_Path.with_suffix(GxDDX.suffix())
                    self.ui.lineEdit_File.setText(str(ddx_Path))
                    if ddx_Path.exists():
                        self._DDX = GxDDX.open(self.ui.lineEdit_File.text())
                    else:
                        prm_ToolTip = (self._INFO, self.trans("New DDX file..."))
                        self._DDX = GxDDX(str(ddx_Path))
                    ddx_Save = self._DDX.SaveRelPaths
                    ddx_Data = self._DDX.Data
                    ddx_Conf = self._DDX.Conf
                except OSError:
                    self.log.error(
                        "OS error with DDX file '%s'", str(self.ui.lineEdit_File.text()),
                        exc_info=True
                    )
                    prm_ToolTip = (self._ERROR, self.trans("OS error with DDX file!"))
                except gqb.GxFileError as exc:
                    self.log.info(exc.msg())
                    prm_ToolTip = (self._ERROR, exc.msg())
                except Exception:
                    self.log.error(
                        "Unkown error with DDX file '%s'", str(self.ui.lineEdit_File.text()),
                        exc_info=True
                    )
                    prm_ToolTip = (self._ERROR, self.trans("Unkown error on loading DDX file!"))
            # Attr. __oldFile und __hasFileError aktualisieren - Prm File wurde validiert
            self.__oldFile = self.ui.lineEdit_File.text()
            self.__hasFileError = bool(prm_ToolTip) and (prm_ToolTip[0] == self._ERROR)
            # Attr. __oldData und __oldConf zurücksetzen - Validierung der Prm erzwingen
            self.__oldData = "?"
            self.__oldConf = "?"
            self.__oldSave = ddx_Save
            # Aktualisierung der Error-Message
            if prm_ToolTip:
                self.ui.label_FileImg.setPixmap(self._QPixmap[prm_ToolTip[0]])
                self.ui.label_FileImg.setToolTip(prm_ToolTip[1])
            else:
                self.ui.label_FileImg.setToolTip("")
            self.ui.label_FileImg.setVisible(bool(prm_ToolTip))
            # Aktualisierung, der abhängigen Widgets...
            enableDDXPrpCtls = (bool(self.ui.lineEdit_File.text()) and (not self.__hasFileError))
            self.ui.checkBox_SaveRelPaths.setEnabled(enableDDXPrpCtls)
            self.ui.checkBox_SaveRelPaths.setChecked(ddx_Save)
            self.ui.lineEdit_Data.setEnabled(enableDDXPrpCtls)
            self.ui.lineEdit_Data.setText(ddx_Data)
            self.ui.lineEdit_Conf.setEnabled(enableDDXPrpCtls)
            self.ui.lineEdit_Conf.setText(ddx_Conf)
        # Validierung von Prm File ist OK,
        # wenn der Prm File keinen Fehler hat
        return (not self.__hasFileError)

    def _update_ComReg(self, dlg_OK=True):
        """shows the status of the GeoDin COM server registration for the chosen geodin.ini

        10/2026
        """
        conf = self.ui.lineEdit_Conf.text()
        show = bool(dlg_OK) and bool(conf) and not self.__hasConfError
        result = None
        if show:
            try:
                result = GxComReg.check(conf, with_running=False)
            except Exception:
                self.log.error("GeoDin COM server check failed", exc_info=True)
        if result is None:
            self.ui.label_Com.setText("")
            self.ui.label_ComImg.setVisible(False)
            self.ui.pushButton_ComReg.setVisible(False)
            self._fitDialogHeight()
            return
        level, text = comreg.statusText(result)
        self.ui.label_Com.setText(text)
        self.ui.label_Com.setToolTip(text)
        pixmap = {
            'info': self._QPixmap[self._INFO],
            'warning': self._QPixmap[self._WARNING],
            'error': self._QPixmap[self._ERROR],
        }.get(level)
        if pixmap is not None:
            self.ui.label_ComImg.setPixmap(pixmap)
        self.ui.label_ComImg.setVisible(pixmap is not None)
        self.ui.pushButton_ComReg.setVisible(
            result['state'] in (GxComReg.NOT_REGISTERED, GxComReg.WRONG_EXE, GxComReg.BOTH_BITS) and
            result['supported']
        )
        self._fitDialogHeight()
        return

    # 10/2026: dialog size
    #   ui_gqgis_dlg_ddx.py fixes the dialog to 422 x 283 px (minimum/maximum height 283).
    #   With the rows for auto-load and the GeoDin COM server state the content no longer fits
    #   (squeezed rows, cut COM messages). The width is now larger and the height follows the
    #   content (incl. word-wrapped COM messages); the dialog can still only be resized horizontally.
    #   Rollback: remove the call of _initDialogSize() in __init__.
    _DLG_MIN_WIDTH = 560
    _DLG_INIT_WIDTH = 620

    def _initDialogSize(self):
        """overrides the fixed size of ui_gqgis_dlg_ddx.py (see comment above)

        10/2026
        """
        self.setMinimumSize(QtCore.QSize(self._DLG_MIN_WIDTH, 0))
        self.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.resize(self._DLG_INIT_WIDTH, self.height())
        self._fitDialogHeight()

    def _fitDialogHeight(self):
        """sets the (fixed) dialog height to the height the content needs at the current width

        10/2026
        """
        lay = self.layout()
        if lay is None:
            return
        lay.invalidate()
        lay.activate()
        h = lay.heightForWidth(self.width()) if lay.hasHeightForWidth() else -1
        if h <= 0:
            h = lay.sizeHint().height()
        h = max(h, lay.minimumSize().height())
        if h != self.minimumHeight() or h != self.maximumHeight():
            self.setFixedHeight(h)

    def showEvent(self, event):
        super().showEvent(event)
        self._fitDialogHeight()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # word wrap of the COM message depends on the width
        if event.size().width() != event.oldSize().width():
            QtCore.QTimer.singleShot(0, self._fitDialogHeight)

    def _clicked_BtnComReg(self):
        """registers the GeoDin application of the chosen geodin.ini as COM server

        10/2026
        """
        self.log.log(gqc._LOG_TRACE,"")
        comreg.ensureComRegistration(self, self.ui.lineEdit_Conf.text(), force=True)
        self._update_ComReg()
        # toolbar buttons (e.g. Connect) depend on the registration -> update them
        try:
            app.updateUI()
        except Exception:
            self.log.debug("", exc_info=True)
        return

    def _changed_checkBox(self):
        self.log.log(gqc._LOG_TRACE,"")
        self.validateUi()
        return

    def _clicked_BtnConf(self):
        """
        17.04.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        dlg = QtWidgets.QFileDialog(self)
        dlg.setWindowTitle(self.trans("Open GeoDin configuration file"))
        # 04/2023 j.ebert, Anmerkung
        #   Translation hier genau so, damit der FileDialog-Filter immer richtig gesetzt wird.
        dlg.setNameFilter(self._FileDlgFilter_Conf % self.trans("GeoDin file"))
        dlg.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        if dlg.exec():
            selFiles = dlg.selectedFiles()
            self.log.debug(selFiles)
            self.ui.lineEdit_Conf.setText(selFiles[0])
            self.validateUi()
        return

    def _clicked_BtnData(self):
        """
        14.04.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        dlg = QtWidgets.QFileDialog(self)
        dlg.setWindowTitle(self.trans("Open GeoDinQGIS data folder"))
        dlg.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
        if dlg.exec():
            selFiles = dlg.selectedFiles()
            self.log.debug(selFiles)
            self.ui.lineEdit_Data.setText(selFiles[0])
            self.validateUi()
        return

    def _clicked_BtnFile(self):
        """
        05.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # check if the keyboard modifier 'Ctrl' is pressed
        # https://stackoverflow.com/questions/8772595/how-can-i-check-if-a-keyboard-modifier-is-pressed-shift-ctrl-or-alt
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.KeyboardModifier.ControlModifier:
            # Bei 'Control+Click'...
            # Prm File zurücksetzen und keinen FileDialog öffnen
            self.ui.lineEdit_File.setText("")
            self.validateUi()
        else:
            dlg = QtWidgets.QFileDialog(self)
            dlg.setWindowTitle(self.trans("Open GeoDinQGIS DDX file"))
            # 04/2023 j.ebert, Anmerkung
            #   Translation hier genau so, damit der FileDialog-Filter immer richtig gesetzt wird.
            dlg.setNameFilter(self._FileDlgFilter_File % self.trans("DDX file"))
            dlg.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
            if dlg.exec():
                selFiles = dlg.selectedFiles()
                self.log.debug(selFiles)
                self.ui.lineEdit_File.setText(selFiles[0])
                self.validateUi()
        return

    def _clicked_BtnNew(self):
        """
        21.04.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        dlg = QtWidgets.QFileDialog(self)
        dlg.setWindowTitle(self.trans("New GeoDinQGIS DDX file"))
        # 04/2023 j.ebert, Anmerkung
        #   Translation hier genau so, damit der FileDialog-Filter immer richtig gesetzt wird.
        dlg.setNameFilter(self._FileDlgFilter_File % self.trans("DDX file"))
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        if dlg.exec():
            selFiles = dlg.selectedFiles()
            self.log.debug(selFiles)
            self.ui.lineEdit_File.setText(selFiles[0])
            # DDX-File-Management nach "New GeODinQGIS DDX file" (!!!)
            self.validateUi()
        return

    _ITEM_OPEN = "__open__"
    _ITEM_NEW = "__new__"

    def _fillCboFile(self):
        """fills the combo box with the recently used DDX files (10/2026)"""
        cbo = getattr(self, '_cboFile', None)
        if cbo is None:
            return
        text = self.ui.lineEdit_File.text()
        cbo.blockSignals(True)
        try:
            cbo.clear()
            for path in recentDDXFiles():
                cbo.addItem(path, path)
                idx = cbo.count() - 1
                if not os.path.isfile(path):
                    # missing file: shown disabled
                    item = cbo.model().item(idx)
                    if item is not None:
                        item.setEnabled(False)
                    cbo.setItemData(idx, self.trans("File not found"), QtCore.Qt.ItemDataRole.ToolTipRole)
            if cbo.count():
                cbo.insertSeparator(cbo.count())
            cbo.addItem(self.trans("Open other DDX file..."), self._ITEM_OPEN)
            cbo.addItem(self.trans("Create new DDX file..."), self._ITEM_NEW)
            cbo.setCurrentIndex(-1)
            self.ui.lineEdit_File.setText(text)
        finally:
            cbo.blockSignals(False)
        return

    def _activated_CboFile(self, index):
        """entry of the combo box chosen: recent DDX file, 'Open...' or 'New...' (10/2026)"""
        data = self._cboFile.itemData(index)
        oldText = self.__oldFile if self.__oldFile != "?" else ""
        if data == self._ITEM_OPEN:
            self.ui.lineEdit_File.setText(oldText)
            self._clicked_BtnFile()
        elif data == self._ITEM_NEW:
            self.ui.lineEdit_File.setText(oldText)
            self._clicked_BtnNew()
        elif data:
            self.ui.lineEdit_File.setText(data)
            self.validateUi()
        return

    def accept(self):
        """'Apply': saves a changed DDX file, then the dialog is closed and the DDX is loaded

        10/2026 (before: OK only enabled after saving with the 'Save' button)
        """
        if self.ui.pushButton_Save.isEnabled():
            try:
                self._clicked_BtnSave()
            except Exception:
                self.log.error("DDX file could not be saved", exc_info=True)
                MsgBox.error(self, self.trans("Apply"), self.trans("The DDX file could not be saved."))
                return
        super().accept()

    def reject(self):
        """'Close' (also Esc / window close): asks if the DDX file was changed but not saved

        10/2026
        """
        if self.ui.pushButton_Save.isEnabled():
            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Icon.Question)
            msg.setWindowTitle(self.windowTitle())
            msg.setText(self.trans("The changes of the DDX file have not been saved."))
            msg.setInformativeText(self.trans("Do you want to apply the changes before closing?"))
            btnApply = msg.addButton(self.trans("Apply"), QtWidgets.QMessageBox.ButtonRole.AcceptRole)
            btnDiscard = msg.addButton(self.trans("Discard"), QtWidgets.QMessageBox.ButtonRole.DestructiveRole)
            btnCancel = msg.addButton(self.trans("Cancel"), QtWidgets.QMessageBox.ButtonRole.RejectRole)
            msg.setDefaultButton(btnApply)
            msg.setEscapeButton(btnCancel)
            msg.exec()
            clicked = msg.clickedButton()
            if clicked == btnApply:
                self.accept()
                return
            if clicked != btnDiscard:
                return          # back to the dialog
            self.log.info("DDX changes discarded")
        super().reject()

    def _clicked_BtnSave(self):
        """
        02.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        try:
            self._DDX.save()
            # Save-Button und DialogButtonbox aktualisieren
            self.validateUi()
        except Exception:
            self.log.error("Unknown error", exc_info=True)
            raise
        return

    def _editingFinished_EdtFile(self):
        """
        14.04.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        if (self.__oldFile != self.ui.lineEdit_File.text()):
            self.log.debug("Prm 'File' was modified by the user")
            self.validateUi()
        return

    def _editingFinished_EdtData(self):
        """
        14.04.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        if (self.__oldData != self.ui.lineEdit_Data.text()):
            self.log.debug("Prm 'Data' was modified by the user")
            self.validateUi()
        return

    def _editingFinished_EdtConf(self):
        """
        14.04.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        if (self.__oldConf != self.ui.lineEdit_Conf.text()):
            self.log.debug("Prm 'Conf' was modified by the user")
            self.validateUi()
        return

    @classmethod
    def open(
        cls,
        parent=None
        ):
        """Opens the Package Dialog

        Args:
            page    (str)
        KWArgs:
            parent  (QtWidget)

        22.05.2023 j.ebert
        """
        # 05/2023 j.ebert, Anmerkung
        # Vorbedingung, wenn bereits ein DDX File gesetzt ist
        if app.DDXFile:
            try:
                GxDDX.open(app.DDXFile)
            except gqb.GxFileError as exc:
                MsgBox.error(parent, 'DataDictionary', exc.msg())
        # DDX-Dialog öffnen/ausführen...
        # 10/2026: the current DDX file is part of the recently used DDX files
        if app.DDXFile and os.path.isfile(app.DDXFile):
            addRecentDDXFile(app.DDXFile)
        dlg = cls(parent)
        try:
            dlg._fillCboFile()
            dlg.ui.lineEdit_File.setText(app.DDXFile)
            # 10/2026: check option 'auto-load' if the current DDX file is the one
            #   saved for auto-load
            autoLoadFile = app.autoLoadDDXFile()
            wasAutoLoad = (
                bool(autoLoadFile) and bool(app.DDXFile) and
                (os.path.normcase(os.path.abspath(autoLoadFile)) ==
                 os.path.normcase(os.path.abspath(app.DDXFile)))
            )
            dlg.ui.checkBox_AutoLoad.setChecked(wasAutoLoad)
            dlg.validateUi()
            if dlg.exec():
                ddxFile = dlg.ui.lineEdit_File.text()
                # 10/2026: save option 'auto-load'
                if dlg.ui.checkBox_AutoLoad.isChecked() and ddxFile:
                    app.setAutoLoadDDXFile(os.path.abspath(ddxFile), True)
                elif wasAutoLoad:
                    # option was unchecked for the saved configuration -> disable auto-load
                    app.setAutoLoadDDXFile("", False)
                app.updateDDXFile(ddxFile)
                # 10/2026: list of the recently used DDX files
                if ddxFile:
                    addRecentDDXFile(ddxFile)
        finally:
            # unregister and delete the dialog
            if dlg in res.Ui:
                res.Ui.remove(dlg)
            dlg.deleteLater()
        return


def main():
    pass

if __name__ == '__main__':
    main()
