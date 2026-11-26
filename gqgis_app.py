"""
Classes:
    GQgis_App           - central GeODinQGIS object (Singleton!)

08.09.2022 J.Ebert
"""
import inspect
import logging
import os
import struct
import time
import traceback
from pathlib import Path

import qgis.core
import qgis.utils
from qgis.PyQt import QtWidgets

from GeODinQGIS import env
import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gqgis_config as gqc
from GeODinQGIS.dm.ddx import GxDDX
from GeODinQGIS.dm.database import GoDatabase
from GeODinQGIS.ui.gqgis_bas import (
    cursor,
    plugin,
    GQgis_MsgBox as MsgBox
)

import GeODinQGIS.gx as gx

class GQgis_App:
    """central GeODinQGIS object (Singleton!)

    05.09.2022 J:Ebert
    """

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GQgis_App, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("")
        self._context = "gqgis" # Context für Transaltion/Übersetzung vom Modul GeODinQGIS

        self._Version = self.__initVersion()
        self._Plugin = None
        self._DDX = None
        self._isDDXReloaded = False
        self._DDXFile = ""
        self._PrjPrps = {}
        self._MaskUpdateUI = ()

        self.DBs = []
        pass

    def __initVersion(self):
        """initialize GeODinQGIS version

        03.05.2023 j.ebert
        """
        # 03.05.2023 j.ebert, Anmerkung
        #   Besser GeODinQGIS Version aus Datei '.\metadata.txt' laden.
        #   Default Version setzen wenn Fehler beim Laden aus Datei.
        self._Version = gqc.VERSION
        if (
            ('xx' in self._Version) or
            (self._Version[-3:-1] == '.9')
        ):
            self._Version +=  " (experimental)"
        return self._Version

    def InfoText(self):
        """ returns info text

        05.09.2022 J.Ebert
        """
        from GeODinQGIS import plugin
        txt = ""
##        txt += type(plugin()).__name__ + "\n"
        txt += self.info_QGIS()
        txt += self.info_Plugin()
        txt += gx.gApp.info()
        txt += env.InfoText_OS()
        txt += env.InfoText()
        self.log.info(txt)
        return(txt)

    def info_Plugin(self):
        """ returns plugin info text

        01.06.2023 J.Ebert
        """
        rows = [
            "%s %s" % (gqc.PRODUCT, self.Version),
            str(Path(__file__).parent),
            ""
        ]
        txt = "\n    ".join(rows) + "\n"
        return txt

    def info_QGIS(self):
        """ returns QGIS info text

        01.06.2023 J.Ebert
        """
        # seealso
        #   https://stackoverflow.com/questions/26239144/python-qgis-version-information
        rows = []
        if hasattr(qgis.utils, 'Qgis'):
            rows = [
                "QGIS %s" % qgis.utils.Qgis.QGIS_VERSION,
                qgis.core.QgsApplication.prefixPath(),
                ""
            ]
        elif hasattr(qgis.utils, 'QGis'):
            rows = [
                "\nQGIS %s\n\n" % qgis.utils.QGis.QGIS_VERSION
            ]
        txt = "\n    ".join(rows) + "\n"
        return txt


    @property
    def Version(self):
        """GeODinQGIS Version

        03.05.2023 j.ebert
        """
        return self._Version

    @property
    def DDX(self):
        """Data Dictionary

        03.05.2023 j.ebert
        """
        return self._DDX

    @property
    def DDXFile(self):
        """DDX file (*.gddx)

        03.05.2023 j.ebert
        """
        return self._DDXFile

    @property
    def DDXData(self):
        """DDX data folder

        03.05.2023 j.ebert
        """
        value = ""
        if self._DDX:
            value = self._DDX.Data
        return value

    @property
    def DDXConf(self):
        """GeODin configuration file (geodin.ini)

       03.05.2023 j.ebert
        """
        value = ""
        if self._DDX:
            value = self._DDX.Conf
        return value

    @property
    def GAppFolder(self):
        """GeODin Applicationfolder (directory where the geodin.ini is stored)

        04.05.2023 j.ebert
        """
        value = ""
        if self._DDX:
            value = self._DDX.AppFolder
        return value

    @property
    def Plugin(self):
        """QGIS Plugin (reference to GQgis object)

        04.05.2023 j.ebert
        """
        # 04.05.2023 j.ebert, Anmerkung
        #   Genau so auf Grund der Reihenfolge beim Import und beim Instanzieren der Objekte.
        if not self._Plugin:
            self._Plugin = plugin()
        return self._Plugin

    # 10/2026: auto-load of the DDX configuration when QGIS starts
    #   (stored in the QGIS user settings (QgsSettings), not in the QGIS project)
    _SETTINGS_AUTOLOAD = "GeODinQGIS/autoLoadDDX"
    _SETTINGS_AUTOLOAD_FILE = "GeODinQGIS/autoLoadDDXFile"

    def autoLoadDDXFile(self):
        """DDX file to be loaded automatically when QGIS starts

        returns:
            ddxFile (str)       - DDX file or empty string if auto-load is disabled

        10/2026
        """
        settings = qgis.core.QgsSettings()
        enabled = settings.value(self._SETTINGS_AUTOLOAD, False, type=bool)
        ddxFile = settings.value(self._SETTINGS_AUTOLOAD_FILE, "", type=str)
        return ddxFile if (enabled and ddxFile) else ""

    def setAutoLoadDDXFile(self, ddxFile, enabled=True):
        """saves/resets the DDX file to be loaded automatically when QGIS starts

        10/2026
        """
        settings = qgis.core.QgsSettings()
        if enabled and ddxFile:
            settings.setValue(self._SETTINGS_AUTOLOAD, True)
            settings.setValue(self._SETTINGS_AUTOLOAD_FILE, str(ddxFile))
            self.log.info("DDX file '%s' is loaded automatically when QGIS starts", ddxFile)
        else:
            settings.setValue(self._SETTINGS_AUTOLOAD, False)
            self.log.info("Auto-load of DDX file is disabled")
        return

    def ddxFile(self):
        self.log.warning(
            "Method '%s' is superseded by property '%s'\n\t%s",
            'ddxFile()', 'DDXFile', traceback.format_stack()[-2].strip()
        )
        return self._DDXFile

    def updateDDXFile(
        self,
        ddxFile                 # DDX-File
    ):
        self.log.log(gqc._LOG_TRACE,"")
        # 'maskable' UI-Update registrieren
        self._regUpdateUI()
        if not ddxFile:
            ddxFile = ""
        try:
            self._DDXFile = ddxFile
            self._reopenDDX()
            self._updateGAppCnn()
            # 05/2023 j.ebert, Achtung
            #   Die GeODin-Verbindung muss nicht in jedem Fall neu erstellt werden, also
            #   auch hier die Methode _reloadDDX() unbedingt aufrufen. Ob der DDX-Content
            #   neu geladen werden muss, wird in der Methode selbst geprüft.
            self._reloadDDX()
        except gqb.GQgisBreak:
            pass
        except:
            self.log.critical("Major Disaster...", exc_info=True)
        # 'maskable' UI-Update ggf. ausführen
        self._updateUI()
        return

    def isAvailable(self):
        """True, if GeODinQGIS is available

        03.05.2023 j.ebert
        """
        return gx.gApp.is_installed()

    def isConfigured(self):
        """True, if GeODinGQIS is configured/has DDX

        03.05.2023 j.ebert
        """
        # 04.05.2023 j.ebert, Anmerkung
        #   Prüfen, ob DDX-Conf gesetzt ist und existiert?!
        return self.isAvailable() and bool(self._DDX)

    def isConnected(self):
        """True, if GeODinQGIS is connected to GeODin application

        04.05.2023 j.ebert
        """
        return self.isAvailable() and gx.gApp.is_open()

    def translate(
        self,
        key
    ):
        """translate souerce text 'key' using instance context

        Args:
            key (str)               source text
        Returns:
            sourceText (str)

        25.05.2023 j.ebert
        """
        return  gqb.res.translate(self._context, key)

    def _reopenDDX(self):
        """ updates/reopens DataDictionary

        exceptions:
            GQgisBreak          after errro handling to abort the calling function

        23.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # 05/2023 j.ebert, Anmerkung
        #   Diese Methode wird auch in Folge von QgsPorject.readProject ausgeführt,
        #   dann ist von QGIS jedoch QtCore.Qt.WaitCursor gesetzt. Daher wird hier
        #   während der Anzeige von Fehlermeldungen explizit QtCore.Qt.ArrowCursor
        #   gesetzt (default beim Context Manager cursor()).
        try:
            oldDDX, self._DDX, self._isDDXReloaded = self._DDX, None, False
            if self._DDXFile:
                self._DDX = GxDDX.open(self._DDXFile)
                # 06/2023 j.ebert, Anmerkung
                #   Wenn sich das DDX nicht geändert hat, also
                #   wenn File, Data und Conf vom DDX sich nicht geändert haben,
                #   dann muss das DDX nich neu geladen werden
                self._isDDXReloaded = (
                    bool(oldDDX) and
                    Path(self._DDX.File).samefile(oldDDX.File) and
                    Path(self._DDX.Data).samefile(oldDDX.Data) and
                    Path(self._DDX.Conf).samefile(oldDDX.Conf)
                )
        except gqb.GxException as exc:
            with cursor():
                MsgBox.error(self.Plugin.parent(), 'DataDictionary', exc.msg())
            raise gqb.GQgisBreak()
        except Exception:
            self.log.critical("Unknown error...", exc_info=True)
            with cursor():
                MsgBox.error(
                    self.Plugin.parent(),
                    'DataDictionary',
                    "Unknown error on update DDX file\n%s" % self._DDXFile
                )
            raise gqb.GQgisBreak()
        return

    def _reloadDDX(self):
        """ reloads DataDictionary content

        exceptions:
            GQgisBreak          after errro handling to abort the calling function

        25.05.2023 j.ebert
        """
        from GeODinQGIS.ui.gqgis_frm_gcat import GQgis_Frm_GCat as GCat
        from GeODinQGIS.ui.gqgis_ctl_tools_v2332 import GQgis_Cbo_Layers as CboLayers

        self.log.log(gqc._LOG_TRACE,"")
        if (
            (not self._isDDXReloaded) and
            self.isConnected()
        ):
            # Wenn der DDX-Content noch nicht geladen wurde und
            # wenn eine GeODin-Verbindung besteht,
            # dann den DDX-Content laden...
            # 05/2023 j.ebert, Anmerkung
            # - ein DDX muss gesetzt sein, sonst GeODin nicht verbunden sein
            # - die GeODin-Verbindung ist zur Abfrage der DB-Verbindungen notwendig
            # - Ablauf etwas kompliziert, aber beim Aufbau einer GeODin-Verbindung muss
            #   bekannt sein, ob der DDX-Content bereits geladen wurde oder nicht
            try:
                self.log.debug(self.DDXFile)
                # Explorer/Catalog zurücksetzen
                GCat.instance.updateTree()
                # DB-Verbindungen von GeODin aktualsieren...
                gDBConf = gx.gApp.databases()
                self.log.debug(str(gDBConf))
                # 11/2026 notice about skipped (invalid) database entries
                skipped = getattr(gx.gApp, "skippedDatabases", [])
                if skipped:
                    from GeODinQGIS.ui.gqgis_options import pushMessage
                    pushMessage(
                        self.translate(
                            "Invalid database connection in GeoDin skipped (missing name or connection string): %s"
                        ) % ", ".join(skipped),
                        level="warning", duration=15
                    )
                gDBList = [GoDatabase.from_TGClass(settings) for settings in gDBConf]
                # DDX-Conten laden...
                self.DBs = self.DDX.restore(gDBList)
                # DDX-Conten geladen -> Flag _isDDXReloaded setzen
                self._isDDXReloaded = True
                # Explorer/Catalog aktualisieren
                GCat.instance.updateTree(self.DDX.DBGroups)
                # QCombobox mit GoLayers aktualisieren...
                CboLayers.instance().reloadGoLayers()
            except gqb.GxException as exc:
                with cursor():
                    MsgBox.error(self.Plugin.parent(), 'DataDictionary', exc.msg())
                raise gqb.GQgisBreak()
            except Exception:
                self.log.critical("Unknown error...", exc_info=True)
                with cursor():
                    MsgBox.error(
                        self.Plugin.parent(),
                        'DataDictionary',
                        "Unknown error on reload DDX \n%s" % self._DDXFile
                    )
                raise gqb.GQgisBreak()
        return

    def _reloadDDX_v01(self):
        """ reloads DataDictionary content

        exceptions:
            GQgisBreak          after errro handling to abort the calling function

        25.05.2023 j.ebert
        """
        from GeODinQGIS.ui.gqgis_frm_gcat import GQgis_Frm_GCat as GCat

        self.log.log(gqc._LOG_TRACE,"")
        if (
            (not self._isDDXReloaded) and
            self.isConnected()
        ):
            # Wenn der DDX-Content noch nicht geladen wurde und
            # wenn eine GeODin-Verbindung besteht,
            # dann den DDX-Content laden...
            # 05/2023 j.ebert, Anmerkung
            # - ein DDX muss gesetzt sein, sonst GeODin nicht verbunden sein
            # - die GeODin-Verbindung ist zur Abfrage der DB-Verbindungen notwendig
            # - Ablauf etwas kompliziert, aber beim Aufbau einer GeODin-Verbindung muss
            #   bekannt sein, ob der DDX-Content bereits geladen wurde oder nicht
            try:
                self.log.debug(self.DDXFile)
                # Explorer/Catalog zurücksetzen
                GCat.instance.updateTree()
                # DB-Verbindungen von GeODin aktualsieren...
                dbDict = gx.gApp.databases()
                self.log.debug(str(dbDict))
                self.DBs = [GoDatabase.from_TGClass(settings) for settings in dbDict]
                # DDX-Conten laden...
                pass
                # DDX-Conten geladen -> Flag _isDDXReloaded setzen
                self._isDDXReloaded = True
                # Explorer/Catalog aktualisieren
                gomGroups = set([gDB.GOMGroup for gDB in self.DBs if gDB.GOMGroup])
                GCat.instance.updateTree(gomGroups)

            except gqb.GxException as exc:
                with cursor():
                    MsgBox.error(self.Plugin.parent(), 'DataDictionary', exc.msg())
                raise gqb.GQgisBreak()
            except Exception:
                self.log.critical("Unknown error...", exc_info=True)
                with cursor():
                    MsgBox.error(
                        self.Plugin.parent(),
                        'DataDictionary',
                        self.translate("Unknown error on reload DDX \n%s") % self._DDXFile
                    )
                raise gqb.GQgisBreak()
        return

    def updatePrjProperties(
        self,
        prps={}
    ):
        """ updates QGIS-Project-Settings

        02.05.2023 j.ebert
        """
        if not prps:
            # keine Project-Properties übergeben...
            pass
        else:
            pass

    def _askRetryGeoDin(self):
        """asks the user to confirm the license selection in GeoDin; True for 'Retry'

        10/2026
        """
        msg = MsgBox(self.Plugin.parent())
        msg.setWindowTitle("%s - %s" % (gqc.PRODUCT, self.translate("Connection to GeoDin")))
        msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msg.setText(self.translate("The connection to GeoDin could not be established yet."))
        msg.setInformativeText(self.translate(
            "1. Bring the GeoDin window to the front (if necessary via the taskbar)\n"
            "2. Confirm the license selection\n"
            "3. Click 'Retry'"))
        btnRetry = msg.addButton(self.translate("Retry"), QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        msg.addButton(self.translate("Cancel"), QtWidgets.QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(btnRetry)
        msg.exec()
        return msg.clickedButton() is btnRetry

    def openGAppCnn(self):
        """ opens GeODin-App-Connection

        04.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        # 'maskable' UI-Update registrieren
        self._regUpdateUI()
        # Verbidung mit GeODin-App herstellen
        try:
            # 10/2026: check the GeoDin COM server registration for the chosen geodin.ini
            #   and offer to register the matching geodin.exe (see ui/gqgis_comreg.py)
            if self.GAppFolder:
                from GeODinQGIS.ui.gqgis_comreg import ensureComRegistration
                ensureComRegistration(self.Plugin.parent(), self.GAppFolder, onConnect=True)
            # GeODin starten/verbinden...
            # 10/2026: status dialog while GeoDin is started/connected (the first start after
            #   a new registration of the GeoDin COM server can take a while)
            from GeODinQGIS.ui.gqgis_bas import busy, qsleep
            self.log.debug("GAppFolder %s", self.GAppFolder)
            with busy(
                self.Plugin.parent(),
                self.translate("GeoDin is being started and connected ...") + "\n\n" +
                self.translate("Preparing the connection. Please wait.")
            ):
                hdl = gx.gApp.open(self.GAppFolder)
            # GeODin Startup/Lizenz abwarten...
            while (hdl == 0):
                sleepTime = 1
                breakTime = time.time() + 5 * sleepTime
                with busy(
                    self.Plugin.parent(),
                    self.translate("Waiting for GeoDin (license selection) ...")
                ):
                    while (
                        (time.time() < breakTime) and
                        (hdl == 0)
                    ):
                        hdl = gx.gApp.renew()
                        if not hdl:
                            self.log.debug("")
                            qsleep(sleepTime)
                if not hdl:
                    # 10/2026: GeoDin window to the front (license selection) and clearer dialog
                    #   (before: information box 'Check GeoDin application!' with Retry/Cancel)
                    _bringGeoDinToFront()
                    with cursor():
                        if not self._askRetryGeoDin():
                            raise gqb.GQgisCanceldByUser("Canceld by user!")
            # 05/2023 j.ebert, Achtung
            #   Die Methode _reloadDDX() immer nach erfolgreichen Verbinden mit GeODin aufrufen.
            #   Ob der DDX-Content neu geladen werden muss, wird in der Methode selbst geprüft.
            self._reloadDDX()
        except gqb.GQgisCanceldByUser as exc:
            gx.gApp.reset()
            self.log.warning(exc.msg())
        except gqb.GxGAppRestartRequiredError as exc:
            # 10/2026: the running GeoDin was started with another configuration (geodin.ini)
            #   -> short, translated message (before: English exception text with both folders,
            #      the folders are only written to the log now)
            gx.gApp.reset()
            self.log.warning(exc.msg().replace("\n", "\n\t"))
            with cursor():
                MsgBox.warning(
                    self.Plugin.parent(),
                    self.translate("Connection to GeoDin"),
                    self.translate("Please close GeoDin and connect again."),
                    self.translate("The running GeoDin was started with another configuration.")
                )
        except gqb.GxException as exc:
            gx.gApp.reset()
            msg = exc.msg()
            self.log.warning(msg.replace("\n","\n\t"))
            with cursor():
                MsgBox.error(self.Plugin.parent(), 'GeoDin', msg.replace("\n","\n   "))
        except:
            gx.gApp.reset()
            self.log.critical("Major disater...", exc_info=True)
            with cursor():
                MsgBox.error(
                    self.Plugin.parent(),
                    'GeoDin',
                    "Unknown error on update GeoDin connection"
                )
        # 'maskable' UI-Update ggf. ausführen
        self._updateUI()
        return

    def closeGAppCnn(self):
        """ closes GeODin-App-Connection

        04.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        # 'maskable' UI-Update registrieren
        self._regUpdateUI()
        # Verbidung mit GeODin-App beenden
        gx.gApp.reset()
        # 'maskable' UI-Update ggf. ausführen
        self._updateUI()
        return

    def _updateGAppCnn(self):
        """ updates GeODin-App-Connection

        exceptions:
            GQgisBreak          after errro handling to abort the calling function

        02.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        self.log.debug(f"""
    gQGIS   {self.GAppFolder}
    GeoDin  {gx.gApp.AppFolder}
        """)
        if not self.isAvailable:
            # Wenn GeODin nicht verfügbar/nich insatlliert ist,
            # dann kein Aktion bzgl. der Verbindung mit GeODin
            pass
        elif not self.GAppFolder:
            # Wenn kein GeODin Application Folder gesetzt ist, also
            # wenn kein DDX gesetzt/geöffnet ist,
            # dann Verbindung mit GeODin beenden
            self.closeGAppCnn()
        elif (
            self.isConnected() and
            bool(gx.gApp.AppFolder) and
            Path(self.GAppFolder).samefile(gx.gApp.AppFolder)
        ):
            # Wenn eine Verbindung mit GeODin besteht, und
            # wenn das Plugin und GeODin mit die selbe Konfiguration (geodin.ini) arbeiten, also
            # wenn die GeODin Application Folder vom Plugin und von GeODin identisch sind,
            # dann Verbindung mit GeODin Appliction unverändert lassen
            pass
        else:
            # Wenn keine Verbindung mit GeODin besteht, oder
            # wenn das Plugin und GeODin mit unterschiedleichen Konfigurationen arbeiten,
            # dann Verbindung mit GeODin Appliction erstellen/neu erstellen...
            # 05/2023 j.ebert, Achtung
            #   Wenn GeODin nicht über das Plugin gestartet wurde,
            #   dann wird GeODin mit dem Beenden der Verbindung nicht geschlossen und
            #   dann verursacht das Aktuelisieren der Verbindung einen Fehler,
            #   weil GeODin wieterhin mit einer anderen Konfiguartion (geODin.ini) arbeitet
            try:
                self.closeGAppCnn()
                self.openGAppCnn()
            except Exception:
                self.log.critical("Unknown error...", exc_info=True)
                with cursor():
                    MsgBox.error(
                        self.Plugin.parent(),
                        'GeoDin',
                        "Unknown error on update GeoDin connection"
                    )
                raise gqb.GQgisBreak()
        return

    def _regUpdateUI(self):
        """ registers UI update

        03.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        # UI-Update registrieren, wenn noch keine Registrierung existiert
        if not self._MaskUpdateUI:
            self._MaskUpdateUI = (len(inspect.stack()), inspect.stack()[1].function)
        return()

    def _updateUI(
        self,
        non_maskable=False
    ):
        """ optionally executes a UI update if...

        UI update is executed
        - if argument 'non_maskable' is set to True or
        - if UI update is not registered, i.e. if the attribute '_MaskUpdateUI' is not set or
        - if UI update is registered by the calling function

        03.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        if (
            non_maskable or
            (not bool(self._MaskUpdateUI)) or
            (self._MaskUpdateUI == (len(inspect.stack()), inspect.stack()[1].function))
        ):
            # Registrierung vom UI-Update zurücksetzen
            self._MaskUpdateUI = ()
            # UI aktualisieren...
            self.Plugin.updateGui()
        return

    def updateUI(self):
        """ executes a UI update

        03.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"TRACE")
        self._updateUI(True)



def _bringGeoDinToFront():
    """brings the window of the running GeoDin application (geodin.exe) to the front

    Windows may refuse SetForegroundWindow (focus stealing prevention), then the window only
    flashes in the taskbar - the dialog text explains what to do. (10/2026)
    """
    try:
        import win32api
        import win32con
        import win32gui
        import win32process
    except Exception:
        return False
    found = []

    def _enum(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd) or not win32gui.GetWindowText(hwnd):
                return True
            _tid, pid = win32process.GetWindowThreadProcessId(hwnd)
            hProc = win32api.OpenProcess(0x1000 | 0x0010, False, pid)   # QUERY_LIMITED_INFORMATION | VM_READ
            try:
                exe = win32process.GetModuleFileNameEx(hProc, 0)
            finally:
                win32api.CloseHandle(hProc)
            if os.path.basename(exe).lower() == "geodin.exe":
                found.append(hwnd)
        except win32api.error:
            pass
        return True

    try:
        win32gui.EnumWindows(_enum, None)
        for hwnd in found:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                win32gui.FlashWindow(hwnd, True)
        return bool(found)
    except Exception:
        logging.getLogger(f"{gqc._LOG_PARENTS}GQgis_App").debug("", exc_info=True)
        return False


def main():
    app = GQgis_App()
    return app

if __name__ == '__main__':
    app = main()
