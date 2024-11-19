"""
Classes:
    GxCOM                       - GeODin COM interface (Singleton!)
    GxSQL                       - GeODin SQL direct access (Singleton!)

06.03.2023 j.ebert
"""

import datetime
import json
import logging
import os
import random
import re
import struct
import sys
import time
import win32com.client
from pathlib import Path

try:
    import psycopg2
except:
    pass
try:
    import pyodbc
except:
    pass

_log_password = "".ljust(random.randint(8,17), '*')
"""general password for logging"""

import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gqgis_config as gqc
from .system import (
    GxReg,
    GxSys
)

class GxCOM:
    """GeODin COM interface (Singleton!)

    22.03.2023 j.ebert
    """
    log = logging.getLogger(f"{gqc._LOG_PARENTS}GxCOM")

    __REGHANDLE_CLOSED = 0
    __gCOM_Alias = 'gCOM server'

    def __init__(self):
        # Logger nicht für jedes Objekt/jede Intstanz setzen, sondern für die Klasse,
        # damit der Logger auch in classmethods genutzt werden kann
        self._AppFolder = ""
        """Applicationfolder (directory where a geodin.ini is stored)"""
        self._gCOM = None
        """GeODin Application/COM Server object"""

    @property
    def AppFolder(self):
        """Applicationfolder (directory where a geodin.ini is stored)

        08.03.2023 j.ebert
        """
        return self._AppFolder

    @classmethod
    def info(cls):
        """About...

        16.09.2022 J.Ebert
        """
        return GxReg.prog_info()

    @classmethod
    def assert_gApp(cls):
        """tests GeODin application

        returns:
            progPath (str)      - GeODin application (geodin.exe with path)

        exeptions:
            GxGAppError         if GeODin is not installed/registered
            GxGAppError         if GeODin not found
            GxGAppError         if installed GeODin version not supoorted

        23.03.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE,"")
        if not GxReg.prog_path():
            raise gqb.GxGAppError('GeODin is not installed/registered')
        progPath = Path(GxReg.prog_path())
        if not progPath.exists():
            raise gqb.GxGAppError('GeODin not found\n%s', str(progPath))
        curVersion = GxReg.get_FileVersion(str(progPath))
        minVersion = (9,)
        if curVersion < minVersion:
            raise gqb.GxGAppError(
                'GeODin version %s not supported (version %s required)',
                '.'.join([str(val) for val in curVersion]),
                '.'.join([str(val) for val in minVersion])
            )
        return str(progPath)

    def assert_gCOM(self):
        """test GeODin COM connection

        exceptions:

        27.03.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "")
        # Existiert bereits eine COM Connection/ist das Attr. _gCOM gesetzt?
        if not self._gCOM:
            raise gqb.GxGComCnnError("GeODin connection not yet open")
        # GeODin RegSZ 'System\Handle' ermitteln...
        curRegHandle = GxReg.query_Handle()
        self.log.debug(
            "%n%tCnnHdl - %-25s %6d%n%tAppHdl - %-25s %6d",
            "GxCOM._gCOM_RegHandle", self._gCOM_RegHandle,
            "RegSZ 'System\Handle'", curRegHandle
        )
        # GeODinCOM Connection prüfen...
        if (
            (self._gCOM_RegHandle != self.__REGHANDLE_CLOSED) and
            (self._gCOM_RegHandle == curRegHandle)
        ):
            # Wenn _gCOM_RegHandle gesetzt ist und
            # wenn _gCOM_RegHandle gleich dem GeODin RegSZ 'System\Handle' ist,
            # dann ist die GeODin COM Connection aktuell
            pass
        elif (
            (self._gCOM_RegHandle != self.__REGHANDLE_CLOSED) and
            (self._gCOM_RegHandle != curRegHandle)
        ):
            # Wenn _gCOM_RegHandle gesetzt ist und
            # wenn _gCOM_RegHandle ungleich dem GeODin RegSZ 'System\Handle' ist,
            # dann ist die GeODin COM Connection NICHT aktuell
            raise gqb.GxGComCnnError(
                "GeODin connection interrupted\nPlease open the GeODin connection again"
            )
        else:
            # Wenn _gCOM_RegHandle ungleich dem GeODin RegSZ 'System\Handle' ist oder
            # wenn _gCOM_RegHandle NICHT gesetzt,
            # dann ist die GeODin COM Connection NICHT aktuell oder nicht gesetzt
            raise gqb.GxGComCnnError(
                "GeODin connection undefined (CnnHdl: %d, AppHdl: %d)",
                self._gCOM_RegHandle,
                curRegHandle
            )
        return

    @classmethod
    def is_installed(cls):
        """ True, if GeODin application (geodin.exe) is installed/registered

        16.03.2023 j.ebert
        """
        return (bool(GxReg.prog_path()) and Path(GxReg.prog_path()).exists())

    def is_open(self):
        """True, if GeODin application (geodin.exe) is open/activated

        16.03.2023 j.ebert
        """
        # 10.03.2023 j.ebert, Anmerkung
        #   _gCOM_RegHandle wird in dieser Methode NICHT zurückgesetzen, weil die Vraibale als Flag
        #   genutzen wird, ob eine COM Verbindung bereits aktiv war und reaktiviert werden kann.
        if (
            bool(self._gCOM) and
            (self._gCOM_RegHandle != GxReg.query_Handle())
        ):
            # Wenn ein GeODin COM Server/Object gesetzt ist,
            # aber sich der RegSZ 'Handle' von GeODin geändert hat,
            # dann wird die COM Verbindung nicht mehr funktionieren,
            # dann _gCOM zurücksetzen...
            # 10.03.2023 j.ebert, dieser Fall tritt auf...
            #   Wenn nachdem eine COM Verbindung aktiviert wurde,
            #   GeODin beendet und ggf. auch neu gestartet wurde.
            #   - GeODin beendet       -> RegSZ 'Handle' = 0
            #   - GeODin neu gestartet -> RegSZ 'Handle' = <anderer Wert>
            # 10.03.2023 j.ebert, Anmerkung
            #   _gCOM_RegHandle in dieser Methode nicht zurücksetzen, sonder als Flag benutzen,
            #   ob eine COM Verbindung bereits aktiv war und reaktiviert werden kann/darf
            self._gCOM = None
        return bool(self._gCOM)

    def is_running(cls):
        """True, if GeODin application (geodin.exe) is running

        08.03.2023 j.ebert
        """
        return bool(GxReg.query_Handle())

    def open(
        self,
        appFolder=""
    ):
        """opens GeODin COM Connection

        07.03.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # GeODin application prüfen
        #   GxGeODinAppError    if GeODin is not installed/registered
        #   GxGeODinAppError    if GeODin not found
        #   GxGeODinAppError    if installed GeODin version not supoorted
        self.assert_gApp()
        # AppFolder prüfen und setzen
        #   AssertionError      if argument 'appFolder' is not of type string or is empty
        #   GxAppFolderError    if Applictionfolder itself or file geodin.ini not found
        self._AppFolder = GxSys.assert_AppFolder(appFolder)
        self.log.debug("GAppFolder %s", self._AppFolder)
        # 04.05.2023 j.ebert, Anmerkung
        #   Hier Exception nicht abfangen mit mit try...except, damit
        #   beim Erstellen einer GeODin COM Verbindung ggf. sofort abgebrochen wird und
        #   nicht erst nach definierter Wartezeit(!!!) und erneuten Aufrauf der Methode renew()
##        try:
##            # GeODin COM Connection zurücksetzen
##            self.reset()
##            # GeODin COM Server starten/verbinden
##            self.renew()
##        except:
##            self.log.critical("Major disaster...", exc_info=True)            # GeODin COM Connection zurücksetzen
        # GeODin COM Connection zurücksetzen
        self.reset()
        # GeODin COM Server starten/verbinden
        self.renew()
        return self._gCOM_RegHandle

    def ping(self):
        """tests GeODin COM Connection

        returns:
            hdl (int)           GeODin RegSZ 'System\Handle'

        exceptions:
            AssertionError      if the GeODin COM connection is not yet open/instantiated

        27.03.2023 j.ebert
        """
        # 27.03.2023 j.ebert, Anmerkung
        #   Die Aktualisierung/der Neuaufbau der GeODin COM Connection funktioniert nur bedingt!
        #   Wenn beim Aufbau der COM Connection in GeODin eine Lizenz ausgewählt werden muss,
        #   dann funktioniert das Aktualisieren/der Neuaufbau nicht ohne Nutzereingabe und
        #   ggf. muss nach einem Timeout mit einer Fehlermeldung abgebrochen werden.
        #   Fazit:
        #       - akt. immer mit Fehlermeldung abbrechen, wenn
        #         die COM Connection nicht existiert oder 'verloren gegangen ist'
        #       - diese Methode NICHT beim Aufbau der GeODin COM Connection nutzen

        # Wenn noch keine GeODin COM Connection existiert, also
        # wenn _gCOM nicht gesetzt ist,
        # dann Abbruch der Methode mit AssertionError
        assert self._gCOM, \
            "GeODin COM connection is not opened/initialised"
        # GeODin COM Connection prüfen
        if (
            (self._gCOM_RegHandle != self.__REGHANDLE_CLOSED) and
            (self._gCOM_RegHandle == GxReg.query_Handle())
        ):
            # Wenn _gCOM_RegHandle gesetzt ist und
            # wenn _gCOM_RegHandle gleich dem GeODin RegSZ 'System\Handle' ist,
            # dann ist die GeODin COM Connection aktuell
            pass
        else:
            # Wenn _gCOM_RegHandle ungleich dem GeODin RegSZ 'System\Handle' ist oder
            # wenn _gCOM_RegHandle NICHT gesetzt,
            # dann ist die GeODin COM Connection NICHT aktuell oder nicht gesetzt
            self.renew()
        return self._gCOM_RegHandle

    def ping_01(self):
        """

        10.03.2023 j.ebert
        """
        # 10.02.2023 j.ebert, Gedanken...
        #   Test mit GeODin 9.6 (Release Build: G2640722 Datum 27.10.2022)
        #   Aufruf der COM-Funktionen SysInfo('GeODinINIFileName') und SysInfo('ProgramDataFolder')
        #   liefern auch schon ein "richitges" Ergebnis, wenn noch keine Lizenz ausgewählt wurde.
        #   Damit kann der AppFolder beim Aktivieren einer COM Verbindung sofort geprüft werden.
        #   Fazit:
        #       Die Rückgabe des AppFolders durch diese Ping-Methode scheint sinnfrei zu sein.
        #       Lizenz abfragen oder muss überhaupt ein zwieter Parameter übergeben werden?!
        #           Return    0   - GeODin noch nicht verfügbar/Liznez nicht gewählt
        #                     int - GeODin verfügbar
        #       Aber nur RegSZ 'Handle' abfragen ist nicht ausreichend, in dieser Methode soll
        #       der COM Server auch wirklich abgefragt, also die COM Verbindung getestet werden.
        hdl = 0
        res = ''
        sleepTime = 1
        breakTime = time.time() + 10 * sleepTime
        while (
            (time.time() < breakTime) and
            (hdl == 0)
        ):
            err, res = self._gCOM_AppFolder()
            hdl = GxReg.query_Handle()
            print(hdl, res)
            if not hdl:
                time.sleep(sleepTime)
        return hdl, res

    def renew(self):
        """renews GeODin COM Connection

        exceptions:
            AssertionError      if the attribute 'AppFolder' is not set

        23.03.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "")
        # Wenn das Attribut _AppFolder nicht gesetzt ist,
        # dann Abbruch der Methode mit AssertionError
        assert self._AppFolder, \
            "Attribute 'AppFolder' not set"
        # GeODin COM Connection (inkl. GeODin Konfiguration) prüfen...
        appFolder = ""
        try:
            appFolder = self._gCOM_AppFolder()[1]
        except:
            # GeODin COM Connection neu öffnen/instanzieren...
            # - GeODin Apllication/COM Server prüfen
            if GxReg.query_Handle():
                # Wenn GeODin Apllication/COM Server bereits ausgeführt wird,
                # dann eine Warnung loggen, weil
                # dann die Voreinstellung von AppFolder wirkungslos ist
                self.log.warning("A GeODin application (geodin.exe) is already running")
            # - AppFolder prüfen und RegSZ zum Starten vom GeODin COM Server setzen
            #       AssertionError      if argument 'appFolder' is not of type string or is empty
            #       GxAppFolderError    if Applictionfolder itself or file geodin.ini not found
            #   27.03.2023 j.ebert, Anmerkung
            #       Attr. _AppFolder wird nur in der Methode open() gesetzt und da auch geprüft,
            #       daher kann GxReg.set_COMSrvAppFolder() heir eigentlich keine Exception werfen.
            GxReg.set_COMSrvAppFolder(self._AppFolder)
            self.log.debug("GAppFolder %s", self._AppFolder)
            # - GeODin COM Server starten/verbinden
            self._gCOM = win32com.client.Dispatch(GxReg.prog_id())
            if (not GxReg.query_Handle()) and bool(self.StartupDelayTime):
                # 28.03.2023 j.ebert, Test mit GeODin 9.6
                # Wenn GeODin Apllication/COM Server noch nicht ausgeführt wird,
                # dann Verzögerung/Synchronisation beim GeODin Startup notwendig!
                # - GeODin RegSZ 'System\Handle' wird offensichtlich erst gesetzt, wenn
                #   in GeODin die Lizenz ausgewählt wurde, so dass diese if-Bedingung funktioniert
                # - GeODin COM-Funktion hat folgenden Fehler geliefert, wenn
                #   sie ohne Verzögerung aufgrerufen wurde
                #   GeODin ExcVal - ExcMsg:
                #       1 - Zugriffsverletzung bei Adresse 0000000001638F4B in Modul 'geodin.exe'.
                #           Lesen von Adresse 0000000000000068
                #   Fehlerbild:
                #       GeODin blinkt in der Windows-Taskleiste 2x kurz auf, wobei
                #       das GeODin Icon nicht zu zusehen/erkennen ist
                self.log.debug(
                    "%s.StartupDelayTime: %d seconds",
                    self.__class__.__name__, self.StartupDelayTime
                )
                time.sleep(self.StartupDelayTime)
            appFolder = self._gCOM_AppFolder()[1]
        finally:
            # GeODin COM Connection prüfen (immer!!!)...
            self.log.debug("GAppFolder %s\ngCOMFolder ", self._AppFolder, appFolder)
            if (
                bool(appFolder) and
                Path(appFolder).samefile(self._AppFolder)
            ):
                # Wenn Applicationfolder (bzw. GeODin Konfiguration) identisch sind,
                # dann kann die GeODin COM Connection genutzt werden...
                # 27.03.2023 j.ebert, Anmerkung
                #   GeODin RegSZ 'System\Handle' hier immer neu abfragen und setzen, da
                #   diese Methode auch von ping() beim Aufbau der COM Connection aufgerufen wird.
                self._gCOM_RegHandle = GxReg.query_Handle()
            else:
                # Wenn Applicationfolder (bzw. GeODin Konfiguration) NICHT identisch sind,
                # dann kann die GeODin COM Connection NICHT genutzt werden,
                # dann muss GeODin neu gestartet werden (mit entsprechender Applicatonfolder)
                self.reset()
                raise gqb.GxGAppRestartRequiredError(
                    "GeODin application has to be restarted\nGeODin App\t%s\nGeODin QGIS\t%s",
                    appFolder,
                    self._AppFolder
                )
        return self._gCOM_RegHandle

    def reset(self):
        """closes GeODin COM Connection

        07.03.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        self._gCOM = None
        self._gCOM_RegHandle = self.__REGHANDLE_CLOSED
        return self._gCOM_RegHandle

    @property
    def StartupDelayTime(self):
        """GeODin Apllication/COM Server startup delay time

        returns:
            seconds (int)       - startup delay time

        29.03.2023 j.ebert
        """
        # 28.03.2023 j.ebert, Test mit GeODin 9.6.264.0 (Release Build: G2640722 vom 27.10.2022)
        # Wenn GeODin Apllication/COM Server noch nicht ausgeführt wird,
        # dann ist nach dem Instanzieren des GeODin-COM-Objektes/-Servers in Python
        # eine Verzögerung des Aufrufs der ersten GeODin COM-Funktion notwendig.
        # - Fehler beim Aufruf der COM-Funktion SysInfo('GeODinINIFileName') ohne Verzögerung
        #   GeODin ExcVal - ExcMsg
        #       1 - Zugriffsverletzung bei Adresse 0000000001638F4B in Modul 'geodin.exe'.
        #           Lesen von Adresse 0000000000000068
        #   Fehlerbild:
        #       GeODin blinkt in der Windows-Taskleiste 2x kurz auf, wobei
        #       das GeODin Icon nicht zu zusehen/erkennen ist, aber
        #       GeODin wird danach nicht ausdgeführt/wird nicht im Task-Manager angezeigt
        # - Anmerkung
        #   - Verzögerung nur wenn GeODin noch nicht ausgeführt wird, also
        #     nur wenn der GeODin RegSZ 'System\Handle' nicht gesetzt ist
        #   - StartupDelayTime...
        #     - 10 (oder auch 5) Sekunden - quick and dirty - funktioniert @FDE-3W6X493
        #     - deaktivieren genau hier durch Rückgabe von 0
        #     - ändern oder ggf. auch konfigurieren (siehe import GeODinQGIS.gqgis_config as gqc)
        return gqc.GEODIN_STARTUP_DELAY_TIME

    def _gCOM_AppFolder(self):
        """GeODin Applicationfolder (directory where the geodin.ini is stored)

        Achtung, die Bedeutung von 'Applicationfolder' ist vom Context abhängig
            - Anwendungsverzeichnis von GeODin/Verzeichnis aus dem die geodin.ini gelesen wird
                - GeODin aufrufen mit Parameter -af
                - GeODin als COM-Server instanzieren RegSZ GeODin-System\ComServer\ApplicationFolder
                - im Context einer GeODin Extension
            - Pfad der Programmdatei (!!!)
                - GeODin COM Funktion SysInfo('ApplicationFolder')

        10.03.2023 j.ebert
        """
        assert self._gCOM, f"{self.__gCOM_Alias} not activated"
        res = self._gCOM.SysInfo('GeODinINIFileName')
        self._gCOM_ExcetpionVal = self._gCOM.ExceptionValue
        self._gCOM_ExcetpionMsg = self._gCOM.ExceptionMsg
        self.log.log(gqc._LOG_GxCOM,
            "exc: %s (%s)\n\tres: %s",
            str(self._gCOM_ExcetpionVal), self._gCOM_ExcetpionMsg, res
        )
        appFolder = ""
        if not self._gCOM_ExcetpionVal:
            appFolder = str(Path(res).parent)
        return self._gCOM_ExcetpionVal, appFolder

    def _gCOM_CreateObjectSelection(
        self,
        prms                    # COM function parameters
    ):
        """GeODin Databases

        exceptions:
            GxGComException             if a GeODin COM function failed

        30.05.2023 j.ebert
        """
        self.ping()
        if self.log.level <= gqc._LOG_GxCOM:
            self.log.log(
                gqc._LOG_GxCOM,
                "CreateObjectSelection: \n\t%s",
##                json.dumps(prms, indent=4).replace("\n", "\n\t")
                re.sub(
                    "\"Password\": \"\S+\"",
                    "\"Password\": \"%s\"" % _log_password,
                    json.dumps(prms, indent=4).replace("\n", "\n\t"),
                    re.IGNORECASE
                )
            )
        self._gCOM_ExcetpionVal = self._gCOM.CreateObjectSelection(
            prms['Database'],
            prms['UserName'],
            prms['Password'],
            prms['ObjectIDs'],
            prms.get('ObjectType', 1),
            prms.get('RefName', "GxSEL_%s" % datetime.datetime.now().strftime("%H%M%S")),
            prms.get('MethodID', -1),
            prms.get('MethodParams', ""),
        )
        self._gCOM_ExcetpionMsg = self._gCOM.ExceptionMsg
        self.log.log(
            gqc._LOG_GxCOM,
            "CreateObjectSelection:%4d (%s)", self._gCOM_ExcetpionVal, self._gCOM_ExcetpionMsg
        )
        if self._gCOM_ExcetpionVal:
            raise gqb.GxGComException(
                "COM Exception %02d (%s)", self._gCOM_ExcetpionVal,  self._gCOM_ExcetpionMsg
            )
        return

    def _gCOM_exportFeatureCollection(
        self,
        filename
        ):
        """exports FeatureCollection of selected GOM node

        Warning
            Die GeODin COM Funktion SysInfo('ApplicationFolder') liefert immer
            eine leere Zeichenkette
            GeODin 9.6 (Release Build: G2640722 Datum 27.10.2022 Liznez: Essentials|Professional)

        01.08.2023 j.ebert
        """
        assert self._gCOM, f"{__gCOM_Alias} not activated"
        assert isinstance(filename, str) and bool(filename), \
            "Argument 'filename' not set"
        prms = f"""
[Params]
Method=FeatureCollection
Filename={filename}
        """
        self.log.log(
            gqc._LOG_GxCOM,
            "ExecuteMethodParams (60): \n\t%s",
            prms.replace("\n","\n\t")
        )
##        res = sefl._gCOM.ExecuteMethodParams(60, prms)
        self._gCOM_ExcetpionVal = self._gCOM.ExecuteMethodParams(60, prms)
        self._gCOM_ExcetpionMsg = self._gCOM.ExceptionMsg
        self.log.log(
            gqc._LOG_GxCOM,
            "ExecuteMethodParams:%4d (%s)", self._gCOM_ExcetpionVal, self._gCOM_ExcetpionMsg
        )
        if self._gCOM_ExcetpionVal:
            raise gqb.GxGComException(
                "COM Exception %02d (%s)", self._gCOM_ExcetpionVal,  self._gCOM_ExcetpionMsg
            )
        return

    def _gCOM_GeODinFolder(self):
        """Folder of GeODin apllication/COM server

        Warning
            Die GeODin COM Funktion SysInfo('ApplicationFolder') liefert immer
            eine leere Zeichenkette
            GeODin 9.6 (Release Build: G2640722 Datum 27.10.2022 Liznez: Essentials|Professional)

        10.03.2023 j.ebert
        """
        assert self._gCOM, f"{__gCOM_Alias} not activated"
        res = self._gCOM.SysInfo('ApplicationFolder')
        self._gCOM_ExcetpionVal = self._gCOM.ExceptionValue
        self._gCOM_ExcetpionMsg = self._gCOM.ExceptionMsg
        self.log.log(gqc._LOG_GxCOM,
            "exc: %s (%s)\n\tres: %s",
            str(self._gCOM_ExcetpionVal), self._gCOM_ExcetpionMsg, res
        )
        if res:
            res = str(Path(res))
        return self._gCOM_ExcetpionVal, res

    def _gCOM_LicenceInfo(self):
        assert self._gCOM, f"{__gCOM_Alias} not activated"
        res = self._gCOM.LicenceInfo
        self._gCOM_ExcetpionVal = self._gCOM.ExceptionValue
        self._gCOM_ExcetpionMsg = self._gCOM.ExceptionMsg
        self.log.log(gqc._LOG_GxCOM,
            "exc: %s (%s)\n\tres: \n%s",
            str(self._gCOM_ExcetpionVal), self._gCOM_ExcetpionMsg, res
        )
        return self._gCOM_ExcetpionVal, res

    def _gCOM_ProgramData(self):
        """GeODin ProgramData Folder

        10.03.2023 j.ebert
        """
        assert self._gCOM, f"{__gCOM_Alias} not activated"
        res = self._gCOM.SysInfo('ProgramDataFolder')
        self._gCOM_ExcetpionVal = self._gCOM.ExceptionValue
        self._gCOM_ExcetpionMsg = self._gCOM.ExceptionMsg
        self.log.log(gqc._LOG_GxCOM,
            "exc: %s (%s)\n\tres: %s",
            str(self._gCOM_ExcetpionVal), self._gCOM_ExcetpionMsg, res
        )
        # Der Pfad im Ergebnis der GeODin COM Funktion enthält am Ende noch einen Backslash/
        # ein Windows-Path-Separator (GeODin 9.6 Release Build: G2640722 Datum 27.10.2022).
        if res:
            # Path-Separator am Ende entfernen
            res = str(Path(res))
        return self._gCOM_ExcetpionVal, res

    def _gCOM_Databases(self):
        """GeODin Databases

        exceptions:
            GxGComException             if a GeODin COM function failed

        30.05.2023 j.ebert
        """
        self.ping()
        res = self._gCOM.sysInfo("RequestData=Databases")
        self._gCOM_ExcetpionVal = self._gCOM.ExceptionValue
        self._gCOM_ExcetpionMsg = self._gCOM.ExceptionMsg
        self.log.log(gqc._LOG_GxCOM,
            "exc: %s (%s)\n\tres: %s",
            str(self._gCOM_ExcetpionVal), self._gCOM_ExcetpionMsg, res
        )
        if self._gCOM_ExcetpionVal:
            raise gqb.GxGComException(
                "COM Exception %02d (%s)", self._gCOM_ExcetpionVal,  self._gCOM_ExcetpionMsg
            )
        return res

    def _gCOM_SelectObject(
        self,
        prms
    ):
        """GeODin Databases

        exceptions:
            GxGComException             if a GeODin COM function failed

        30.05.2023 j.ebert
        """
        self.ping()
        self.log.log(
            gqc._LOG_GxCOM,
            "SelectObject: \n\t%s",
##            prms.replace("\n","\n\t")
            re.sub(
                "Password=\S+",
                "Password=%s" % _log_password,
                prms.replace("\n","\n\t"),
                re.IGNORECASE
            ),

        )
        self._gCOM_ExcetpionVal = self._gCOM.SelectObject(prms)
        self._gCOM_ExcetpionMsg = self._gCOM.ExceptionMsg
        self.log.log(
            gqc._LOG_GxCOM,
            "SelectObject:%4d (%s)", self._gCOM_ExcetpionVal, self._gCOM_ExcetpionMsg
        )
        if self._gCOM_ExcetpionVal:
            raise gqb.GxGComException(
                "COM Exception %02d (%s)", self._gCOM_ExcetpionVal,  self._gCOM_ExcetpionMsg
            )
        return


class GxSQL:
    """GeODin SQL Interface

    07.03.2023 j.ebert
    """
    log = logging.getLogger(f"{gqc._LOG_PARENTS}GxSQL")

    _context = 'GxSQL'
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GxGeODinCOM, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        # Logger nicht für jedes Objekt/jede Intstanz setzen, sondern für die Klasse,
        # damit der Logger in classmethods nicht genutzt werden kann
        self._gCOM = None
        """GeODin Application/COM object"""
        self._gINI = ""
        """GeODin Konfiguration (geodin.ini)"""

    @classmethod
    def connect(
        cls,
        gDB,                    # GoDatabase
        usr=None,               # database login user
        pwd=None                # database login password
    ):
        cls.log.log(gqc._LOG_TRACE, "")
        cnnLib, cnn = "", None
        # - Methode zur Validierung der ConnectionProperties für die akt. FireDAC-DirverID
        #   ermitteln und ausführen, wenn sie existiert
        func4DriverID = getattr(cls, "_connect4%s" % gDB.DriverID, None)
        if func4DriverID:
            cnnLib, cnn = func4DriverID(gDB, usr, pwd)
        else:
            raise gqb.GxSQLError("%s databases are not supported", gDB.DriverID)
        return cnnLib, cnn

    @classmethod
    def info(cls):
        """ returns info text about pyodbc drivers

        Returns:
            txt (str)

        05.09.2022 J.Ebert
        """
        txt = ""
        try:
            import pyodbc
            rows = pyodbc.drivers()
        except:
            cls.log.critical("Major disaster...", exc_info=True)
            rows = ['???']
        finally:
            rows.insert(0,f"\nODBC Drivers {struct.calcsize('P')*8} bit:")
            txt = "\n    ".join(rows) + "\n"
        return txt

    @classmethod
    def _connect4MSACC(
        cls,
        gDB,                    # GoDatabase
        usr=None,               # database login user
        pwd=None                # database login password
    ):
        # seealso:
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Defining_Connection_(FireDAC)
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Connect_to_Microsoft_Access_Database_(FireDAC)
        cls.log.log(gqc._LOG_TRACE, "")
        # Python-Modul prüfen...
        if 'pyodbc' not in sys.modules:
            cls.log.warning( "Python module '%s' not found", 'pyodbc')
            raise gqb.GxSQLError("%s databases are not supported", gDB.DriverID)
        # Treiber prüfen...
        if cls._pyodbcDriver4MSACC() not in pyodbc.drivers():
            # 64 Bit ODBC Treiber nicht gefunde/nicht installiert
            cls.log.warning("ODBC driver '%s' not found", cls._pyodbcDriver4MSACC())
            raise gqb.GxSQLError("%s databases are not supported", gDB.DriverID)
        try:
            # pyodbc-Connection-String erstellen
            cnnPrms = [
                "DRIVER={%s}" % cls._pyodbcDriver4MSACC(),
                "DBQ=%s" % gDB._CnnPrps['database']
            ]
            if usr:
                cnnPrms += [
                ]
            elif gDB._CnnPrps.get('user',''):
                cnnPrms += [
                ]
            cnnStr = ";".join(cnnPrms + [""])
            # Connection-Prps/Prms/Str loggen, aber mit "maskierten" Passwort(!!!)
            cls.log.debug(
                "cnnPrps = %s\n\tcnnPrms = %s\n\tcnnStr = \"%s\"",
                re.sub(
                    "\"password\": \"\S+\"",
                    "\"password\": \"%s\"" % _log_password,
                    json.dumps(gDB._CnnPrps, indent=4).replace("\n", "\n\t"),
                    re.IGNORECASE
                ),
                re.sub(
                    "\"PWD=\S+\"",
                    "\"PWD=%s\";" % _log_password,
                    json.dumps(cnnPrms, indent=4).replace("\n", "\n\t"),
                    re.IGNORECASE
                ),
                re.sub(
                    "PWD=\S+;",
                    "PWD=%s;" % _log_password,
                    cnnStr,
                    re.IGNORECASE
                )
            )
            # pyodbc-Connection testen
            cnn = pyodbc.connect(cnnStr)
            cnn.close()
            cls.log.info(
                "%s database '%s' could be connected successfully" , gDB.DriverID, gDB.Name
            )
        except pyodbc.Error:
            cls.log.warning(
                "%s database '%s' could not be connected", gDB.DriverID, gDB.Name,
                exc_info=True
            )
            raise gqb.GxSQLCnnError("Failed to connect %s database '%s'", gDB.DriverID, gDB.Name)
        return 'pyodbc', cnn

    @classmethod
    def _connect4MSSQL(
        cls,
        gDB,                    # GoDatabase
        usr="",                 # database login user
        pwd=""                  # database login password
    ):
        # seealso:
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Defining_Connection_(FireDAC)
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Connect_to_Microsoft_SQL_Server_(FireDAC)
        #
        #   https://learn.microsoft.com/en-us/sql/connect/python/pyodbc/step-3-proof-of-concept-connecting-to-sql-using-pyodbc?view=sql-server-ver16
        #   https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-odbcstr/6c134f58-30b6-48bd-be5b-ed3a8492d870?redirectedfrom=MSDN#Appendix_A_2
        #   https://stackoverflow.com/questions/53273146/python-pyodbc-connect-to-sql-server-using-sql-server-authentication
        cls.log.log(gqc._LOG_TRACE, "")
        # Python-Modul prüfen...
        if 'pyodbc' not in sys.modules:
            cls.log.warning( "Python module '%s' not found", 'pyodbc')
            raise gqb.GxSQLError("%s databases are not supported", gDB.DriverID)
        # Treiber prüfen...
        if cls._pyodbcDriver4MSSQL() not in pyodbc.drivers():
            # 64 Bit ODBC Treiber nicht gefunde/nicht installiert
            cls.log.warning("ODBC driver '%s' not found", cls._pyodbcDriver4MSSQL())
            raise gqb.GxSQLError("%s databases are not supported", gDB.DriverID)
        try:
            # pyodbc-Connection-String erstellen
            cnnPrms = [
                "DRIVER={%s}" % cls._pyodbcDriver4MSSQL(),
            ]
            if gDB._CnnPrps.get('database', ''):
                cnnPrms += ["DATABASE=%s" % gDB._CnnPrps['database']]
            if gDB._CnnPrps.get('server', ''):
                cnnPrms += ["SERVER=%s" % gDB._CnnPrps['server']]
            # 07/2023 j.ebert, Hinweis
            #   FireDAC-Connection-Parameter 'Port' nur für macOS, sonst
            #   alternativer Port in Parameter 'Server' mit Komma getrennt.
            #   (z. B. Server=SrvHost, 4000)
            if gDB._CnnPrps.get('osauthent', 'No').lower() == 'yes':
                # FireDAC Connection Parameter 'OSAuthent'
                cnnPrms += ["Trusted_Connection=Yes"]
                # 07/2023 j.ebert, Anmerkung zur pyodbc Connection(!)
                #   Wenn der Parameter 'Trusted_Connection' nicht auf No gesetzt ist
                #   dann werden die Parameter UID und PWD ignoriert
            else:
                # pyodbc Connection Parameter 'Trusted_Connection'
                #   Yes -- use Windows authentication. This is the default value.
                #   No  -- use DBMS authentication.
                # 07/2023 j.ebert, Fazit
                #   Parameter 'Trusted_Connection' muss hier zwingend auf No gesetzt werden.
                cnnPrms += ["Trusted_Connection=No"]
                # Nutzer/Passwort für MSSQL nur analysieren/setzen, wenn
                # Parameter Trusted_Connection auf No gesetzt ist
                if (bool(usr) and bool(pwd)):
                    # Wenn dieser Methode die Argumente 'usr' und 'pwd' übergeben wurden,
                    # dann Connection-Properties 'user_name' und 'password' setzen/überschreiben
                    gDB._CnnPrps['user_name'] = usr
                    gDB._CnnPrps['password'] = pwd
                if gDB._CnnPrps.get('user_name',''):
                    cnnPrms += ["UID=%s" % gDB._CnnPrps['user_name']]
                    if gDB._CnnPrps.get('password',''):
                        cnnPrms += ["PWD=%s" % gDB._CnnPrps['password']]
                else:
                    # 07/2023 j.ebert, Anmerkung (aus div. Tests)
                    #   Cnn-String mit "Trusted_Connection=No;"  reicht nicht aus und auch
                    #   Cnn-String mit "Trusted_Connection=No;UID=;" reicht nicht aus!
                    # Fazit:
                    #   Damit sicher keine OSAuthent genutzt wird muss der Benutzername im
                    #   Cnn-String enthalten sein.
                    #   Warnung protokollieren und mit GxSQLCnnError das Öffnen der gDB abbrechen.
                    # Hinweis:
                    #   Im ViewModel gibt es beim Öffnen eine GeODinDatenbank zwei Versuche:
                    #   - erster Versuch ohne Nutzereingabe - einfach drauf los/try and error
                    #   - zweiter Versuch mit Login-Abfrage, wenn der erste fehlgeschlagen ist
                    cls.log.warning(
                        "Failed to connect %s database '%s'\n\t%s",
                        gDB.DriverID, gDB.Name, "User name (UID) required!"
                    )
                    raise gqb.GxSQLCnnError(
                        "Failed to connect %s database '%s'", gDB.DriverID, gDB.Name
                    )
            cnnStr = ";".join(cnnPrms + [""])
            # Connection-Prps/Prms/Str loggen, aber mit "maskierten" Passwort(!!!)
            cls.log.debug(
                "cnnPrps = %s\n\tcnnPrms = %s\n\tcnnStr = \"%s\"",
                re.sub(
                    "\"password\": \"\S+\"",
                    "\"password\": \"%s\"" % _log_password,
                    json.dumps(gDB._CnnPrps, indent=4).replace("\n", "\n\t"),
                    re.IGNORECASE
                ),
                re.sub(
                    "\"PWD=\S+\"",
                    "\"PWD=%s\";" % _log_password,
                    json.dumps(cnnPrms, indent=4).replace("\n", "\n\t"),
                    re.IGNORECASE
                ),
                re.sub(
                    "PWD=\S+;",
                    "PWD=%s;" % _log_password,
                    cnnStr,
                    re.IGNORECASE
                )
            )
            # pyodbc-Connection testen
            cnn = pyodbc.connect(cnnStr)
            cnn.close()
            cls.log.debug(
                "%s database '%s' could be connected successfully" , gDB.DriverID, gDB.Name
            )
        except pyodbc.Error:
            cls.log.warning(
                "%s database '%s' could not be connected", gDB.DriverID, gDB.Name,
                exc_info=True
            )
            raise gqb.GxSQLCnnError("Failed to connect %s database '%s'", gDB.DriverID, gDB.Name)
        return 'pyodbc', cnn

    @classmethod
    def _connect4PG(
        cls,
        gDB,                    # GoDatabase
        usr=None,               # database login user
        pwd=None                # database login password
    ):
        # seealso:
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Defining_Connection_(FireDAC)
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Connect_to_PostgreSQL_%28FireDAC%29
        #
        #
        cls.log.log(gqc._LOG_TRACE, "")
        # Python-Modul prüfen...
        if 'psycopg2' not in sys.modules:
            cls.log.warning("Python module '%s' not found", 'psycopg2')
            raise gqb.GxSQLError("%s databases are not supported", gDB.DriverID)
        try:
##            connection = psycopg2.connect("dbname={0} user={1} host={2} password={3}".format(database.options["database"], database.options["uname"], database.options["ip"], database.options["upassword"]))

            # psycopg2-Connection-String erstellen
            cnnPrms = []
            if gDB._CnnPrps.get('server', ''):
                cnnPrms += ["host=%s" % gDB._CnnPrps['server']]
            if gDB._CnnPrps.get('port', ''):
                cnnPrms += ["port=%s" % gDB._CnnPrps['port']]
            if gDB._CnnPrps.get('database', ''):
                cnnPrms += ["dbname=%s" % gDB._CnnPrps['database']]
            if (bool(usr) and bool(pwd)):
                cnnPrms += [
                    "user=%s" % usr,
                    "password=%s" % pwd
                ]
            elif (bool(gDB._CnnPrps.get('user_name','')) and bool(gDB._CnnPrps.get('password',''))):
                cnnPrms += [
                    "user=%s" % gDB._CnnPrps['user_name'],
                    "password=%s" % gDB._CnnPrps['password']
                ]
            cnnStr = " ".join(cnnPrms)
            # Connection-Prps/Prms/Str loggen, aber mit "maskierten" Passwort(!!!)
            cls.log.debug(
                "cnnPrps = %s\n\tcnnPrms = %s\n\tcnnStr = \"%s\"",
                re.sub(
                    "\"password\": \"\S+\"",
                    "\"password\": \"%s\"" % _log_password,
                    json.dumps(gDB._CnnPrps, indent=4).replace("\n", "\n\t"),
                    re.IGNORECASE
                ),
                re.sub(
                    "\"password=\S+\"",
                    "\"password=%s\"" % _log_password,
                    json.dumps(cnnPrms, indent=4).replace("\n", "\n\t"),
                    re.IGNORECASE
                ),
                re.sub(
                    "password=\S+",
                    "password=%s" % _log_password,
                    cnnStr,
                    re.IGNORECASE
                )
            )
            # psycopg2-Connection testen
            cnn = psycopg2.connect(cnnStr)
            cnn.close()
            cls.log.debug(
                "%s database '%s' could be connected successfully" , gDB.DriverID, gDB.Name
            )
        except:
            cls.log.warning(
                "%s database '%s' could not be connected", gDB.DriverID, gDB.Name,
                exc_info=True
            )
            raise gqb.GxSQLCnnError("Failed to connect %s database '%s'", gDB.DriverID, gDB.Name)
        return 'psycopg2', cnn

    @classmethod
    def _pyodbcDriver4MSACC(cls):
        return "Microsoft Access Driver (*.mdb, *.accdb)"

    @classmethod
    def _pyodbcDriver4MSSQL(cls):
        return "SQL Server"

    @classmethod
    def _validateCnnPrps4MSACC(
        cls,
        prps                    # Connection properties
    ):
        """validates connection propertie for MSACC

        13.06.2023 j.ebert
        """
        # seealso:
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Defining_Connection_(FireDAC)
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Connect_to_Microsoft_Access_Database_(FireDAC)
        #   GeODinQGIS_Main.py/GeODinQGISMain.connectToDatabase(self, database, query, create = False, param=None)
        cls.log.log(gqc._LOG_TRACE, "")
        try:
            prps['info'] = prps.get('database', "")
            if  not prps.get('database'):
                error = gqb.res.translate(cls._context, "Database/File not defined")
            elif not Path(prps.get('database')).exists():
                error = gqb.res.translate(cls._context, "Database/File not found")
            else:
                error = gqb.res.translate(
                    cls._context,
                    "Failed to validate %s connection"
                ) % prps['driverid']
                # notwendiges Python Modul prüfen
                import pyodbc
                # Treiber prüfen...
                if cls._pyodbcDriver4MSACC() not in pyodbc.drivers():
                    # 64 Bit ODBC Treiber nicht gefunde/nicht installiert
                    cls.log.error("ODBC driver '%s' not found", cls._pyodbcDriver4MSACC())
                else:
                    # Connection wird prinzipiell unterstützt
                    error = ""
        except ImportError:
            cls.log.error("Import Python modul '%s' failed", 'pyodbc', exc_info=True)
        except:
            cls.log.error("Failed to validate %s connection", prps['driverid'], exc_info=True)
        finally:
            prps['error'] = error
        return

    @classmethod
    def _validateCnnPrps4MSSQL(
        cls,
        prps                    # Connection properties
    ):
        """validates connection propertie for MSSQL

        13.06.2023 j.ebert
        """
        # seealso:
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Defining_Connection_(FireDAC)
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Connect_to_Microsoft_SQL_Server_(FireDAC)
        #
        #   https://learn.microsoft.com/en-us/sql/connect/python/pyodbc/step-3-proof-of-concept-connecting-to-sql-using-pyodbc?view=sql-server-ver16
        cls.log.log(gqc._LOG_TRACE, "")
        try:
            prps['info'] = ("%s:%s" % (prps.get('server', ""), prps.get('port', ""))).strip(' :')
            prps['info'] = ("%s/%s" % (prps['info'], prps.get('database', ""))).strip(' /')
            error = gqb.res.translate(
                cls._context,
                "Failed to validate %s connection"
            ) % prps['driverid']
            # notwendige Python Module prüfen
            import pyodbc
            # Treiber prüfen...
            if cls._pyodbcDriver4MSSQL() not in pyodbc.drivers():
                # 64 Bit ODBC Treiber nicht gefunde/nicht installiert
                cls.log.error("ODBC driver '%s' not found", cls._pyodbcDriver4MSSQL())
            else:
                # Connection wird prinzipiell unterstützt
                error = ""
        except ImportError:
            cls.log.error("Import Python modul '%s' failed", 'pyodbc', exc_info=True)
        except:
            cls.log.error("Failed to validate %s connection", prps['driverid'], exc_info=True)
        finally:
            prps['error'] = error
        return

    @classmethod
    def _validateCnnPrps4PG(
        cls,
        prps                    # Connection properties
    ):
        """validates connection propertie for P

        13.06.2023 j.ebert
        """
        # seealso:
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Defining_Connection_(FireDAC)
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Connect_to_PostgreSQL_%28FireDAC%29
        cls.log.log(gqc._LOG_TRACE, "")
        try:
            prps['info'] = ("%s:%s" % (prps.get('server', ""), prps.get('port', ""))).strip(' :')
            prps['info'] = ("%s/%s" % (prps['info'], prps.get('database', ""))).strip(' /')
            error = gqb.res.translate(
                cls._context,
                "Failed to validate %s connection"
            ) % prps['driverid']
            # notwendige Python Module prüfen
            import psycopg2
            # erfolgreich -> Fehler(-Meldung) zurücksetzen
            error = ""
        except ImportError:
            cls.log.error("Import Python modul '%s' failed", 'psycopg2', exc_info=True)
        except:
            cls.log.error("Failed to validate %s connection", prps['driverid'], exc_info=True)
        finally:
            prps['error'] = error
        return


def main():
    pass

def default_dictConfig():
    """ default logging dictConfig

    19.08.2022 J.Ebert
    """
##    # Log folder (vom Typ pathlib.Path)
##    log_folder = cls.log_folder()
    # default logging coniguration
    log_config = {
        'version':1,
        'disable_existing_loggers': False,
        "loggers": {
            gqc._LOG_PARENTS[:-1]: {
                "handlers" : ["hdl_console"],
                "level": "DEBUG",
                "propagate":True
                },
##            f"{gqc._LOG_PARENTS}GxSQLInterface": {
##                "handlers" : ["hdl_console"],
##                "level": "DEBUG",
##                "propagate":False
##                },
            },
        "handlers":{
            "hdl_console":{
                "formatter": "fmt_console",
                "class": "logging.StreamHandler",
                "level": "DEBUG"
            }
        },
        "formatters":{
            "fmt_console": {
                "format": "%(asctime)s.%(msecs)03d %(levelname)-8s %(name)s.%(funcName)s (Z %(lineno)d) : (Process Details : (%(process)d, %(processName)s), Thread Details : (%(thread)d, %(threadName)s))\n\t%(message)s",
                "datefmt":"%I:%M:%S"
            },
            "std_out": {
                "format": "%(asctime)s.%(msecs)03d %(levelname)-8s : %(module)s : %(funcName)s : %(lineno)d : (Process Details : (%(process)d, %(processName)s), Thread Details : (%(thread)d, %(threadName)s))\n\t%(message)s",
    ##            "datefmt":"%d-%m-%Y %I:%M:%S"
                "datefmt":"%I:%M:%S"
            }
        }
    }
    return log_config

if __name__ == '__main__':
    import logging.config
    logging.config.dictConfig(default_dictConfig())
    main()
    AppFolder_v90 = r"C:\Data\GeODin\Data_v90\GeODinProject"
    AppFolder_BGE = r"C:\Data\GeODinDemo\2104_BGE\GeODinProject"