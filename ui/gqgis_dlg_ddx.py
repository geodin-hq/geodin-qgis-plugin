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
from GeODinQGIS.ui.gqgis_bas import (
    GQgis_Bas_Widget,
    GQgis_MsgBox as MsgBox
)
from GeODinQGIS.ui.ui_gqgis_dlg_ddx import Ui_GQgis_Dlg_DDX
from GeODinQGIS.dm.ddx import GxDDX

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
        self.setText(self.trans("GeODinQGIS DDX file"))
        self.setToolTip(self.trans("GeODinQGIS DDX file"))

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
        enabled = app.isAvailable()
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

    def __new__(cls, parent):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GQgis_Dlg_DDX, cls).__new__(cls)
        return cls.instance

    def __init__(self, parent):
        super().__init__(parent)
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.log(gqc._LOG_TRACE,"")
        self._context = CONTEXT_RES
        self._QPixmap = {
            self._INFO: self.QPixmap("GenericInfo_16"),
##            self._INFO: self.QPixmap("GenericNew_16"),
            self._WARNING: self.QPixmap("GenericWarning_16"),
            self._ERROR: self.QPixmap("GenericError_16"),
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
        return

    def translateUi(self):
        self.log.debug("translate in context '%s'", self._context)
        # translate Ui/QWidget
        try:
            self.setWindowTitle(self.trans("GeODinQGIS - DataDictionary"))
            self.ui.label_File.setText(
                self._FileDlgFilter_File % self.trans("GeODinQGIS DDX file")
            )
            self.ui.label_Data.setText(self.trans("GeODinQGIS data folder"))
            self.ui.label_Conf.setText(
                self._FileDlgFilter_Conf % self.trans("GeODin configuration file")
            )
            self.ui.checkBox_SaveRelPaths.setText(self.trans("Save relative paths"))
            self.ui.pushButton_New.setToolTip(self.trans("New GeODinQGIS DDX file"))
            self.ui.pushButton_Save.setToolTip(self.trans("Save GeODinQGIS DDX file"))
            self.ui.pushButton_File.setToolTip(self.trans("Open GeODinQGIS DDX file"))
            self.ui.pushButton_Data.setToolTip(self.trans("Open GeODinQGIS data folder"))
            self.ui.pushButton_Conf.setToolTip(self.trans("Open GeODin configuration file"))
        except:
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
        # OK-Button aktivieren/deaktivieren...
        #   OK-Button kann nur aktiv sein...
        #   wenn der Dlg okay is, also alle Prms fehlerfrei validiert wurden und
        #   wenn der Save-Button nicht aktiv ist, also das DDX gespeichert/nicht geändert wurde
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(
            dlg_OK and
            (not self.ui.pushButton_Save.isEnabled())
        )
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
            if not self.ui.lineEdit_Conf.text():
                # Wenn kein GeODin-File gesetzt ist...
                prm_ToolTip = (self._ERROR, "GeODin file is required")
            else:
                ddx_Conf = self.ui.lineEdit_Conf.text()
                try:
                    ddx_Path = Path(ddx_Conf)
                    ddx_Path.resolve()
                    if ddx_Path.name.lower() != 'geodin.ini':
                        prm_ToolTip = (self._ERROR, self.trans("No GeODin file (geodin.ini)!"))
                    elif not ddx_Path.is_absolute():
                        prm_ToolTip = (self._ERROR, self.trans("No absolute GeODin file path!"))
                    elif not Path(self.ui.lineEdit_Conf.text()).is_file():
                        prm_ToolTip = (self._ERROR, self.trans("No such GeODin file"))
                    self.ui.lineEdit_Conf.setText(str(ddx_Path))
                except OSError:
                    self.log.error("OS error with GeODin file '%s'", ddx_Conf, exc_info=True)
                    prm_ToolTip = (self._ERROR, self.trans("OS error with GeODin file!"))
                except:
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
                except:
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
            ddx_File = self.ui.lineEdit_File.text()
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
                        raise gqb.GxFileError("No absolute file path '%s'", ddxFile)
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
                except:
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
        dlg.setWindowTitle(self.trans("Open GeODin configuration file"))
        # 04/2023 j.ebert, Anmerkung
        #   Translation hier genau so, damit der FileDialog-Filter immer richtig gesetzt wird.
        dlg.setNameFilter(self._FileDlgFilter_Conf % self.trans("GeODin file"))
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        if dlg.exec_():
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
        dlg.setWindowTitle(self.trans("Open GeODinQGIS data folder"))
        dlg.setFileMode(QtWidgets.QFileDialog.Directory)
        if dlg.exec_():
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
        if modifiers == QtCore.Qt.ControlModifier:
            # Bei 'Control+Click'...
            # Prm File zurücksetzen und keinen FileDialog öffnen
            self.ui.lineEdit_File.setText("")
            self.validateUi()
        else:
            dlg = QtWidgets.QFileDialog(self)
            dlg.setWindowTitle(self.trans("Open GeODinQGIS DDX file"))
            # 04/2023 j.ebert, Anmerkung
            #   Translation hier genau so, damit der FileDialog-Filter immer richtig gesetzt wird.
            dlg.setNameFilter(self._FileDlgFilter_File % self.trans("DDX file"))
            dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
            if dlg.exec_():
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
        dlg.setWindowTitle(self.trans("New GeODinQGIS DDX file"))
        # 04/2023 j.ebert, Anmerkung
        #   Translation hier genau so, damit der FileDialog-Filter immer richtig gesetzt wird.
        dlg.setNameFilter(self._FileDlgFilter_File % self.trans("DDX file"))
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        if dlg.exec_():
            selFiles = dlg.selectedFiles()
            self.log.debug(selFiles)
            self.ui.lineEdit_File.setText(selFiles[0])
            # DDX-File-Management nach "New GeODinQGIS DDX file" (!!!)
            self.validateUi()
        return

    def _clicked_BtnSave(self):
        """
        02.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        try:
            self._DDX.save()
            # Save-Button und DialogButtonbox aktualisieren
            self.validateUi()
        except:
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
                newDDX = GxDDX.open(app.DDXFile)
            except gqb.GxFileError as exc:
                MsgBox.error(parent, 'DataDictionary', exc.msg())
        # DDX-Dialog öffnen/ausführen...
        dlg = cls(parent)
        dlg.ui.lineEdit_File.setText(app.DDXFile)
        dlg.validateUi()
        if dlg.exec_():
            app.updateDDXFile(dlg.ui.lineEdit_File.text())
        return


def main():
    pass

if __name__ == '__main__':
    main()
