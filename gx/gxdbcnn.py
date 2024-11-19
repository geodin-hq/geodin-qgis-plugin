"""
Classes:
    GxDbConnection              - class for direct access to a GeODin database

20.09.2023 j.ebert
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
import traceback
import win32com.client
from pathlib import Path

import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gqgis_config as gqc
import GeODinQGIS.gx as gx

_log = logging.getLogger(f"{gqc._LOG_PARENTS}{Path(__file__).stem}")
try:
    import psycopg2
    from GeODinQGIS.gx.gxdbprv4pg import (
        GxDbProvider4PG
    )
except:
    _log.critical("Failed to import %s modules", 'psycopg2', exc_info=True)
try:
    import pyodbc
    from GeODinQGIS.gx.gxdbprv4odbc import (
        GxDbProvider4MSACC,
        GxDbProvider4MSSQL
    )
except:
    _log.critical("Failed to import %s modules", 'pyodbc', exc_info=True)

_log_password = "".ljust(random.randint(8,17), '*')
"""general password for logging"""

class GxTables:
    """

    20.09.2023 j.ebert
    """

    def __init__(
        self,
        tblSchema="",
        tblPrefix="GEODIN"
    ):
        self._Schema = tblSchema.strip()
        self._Prefix = tblPrefix.strip()
        self._SchemaPrefix = f"{self._Schema}.{self._Prefix}".lstrip(".")

    @property
    def Schema(self):
        """DB-Schema in der GeODin-DB (GeODin-Parameter Owner)
        """
        return self._Schema

    @property
    def Prefix(self):
        """Table-Prefix der GeODin-DB (GeODin-Parameter OneTableSetPrefix)
        """
        return self._Prefix

    @property
    def SchemaPrefix(self):
        """Table-Prefix inkl. DB-Schema
        """
        return self._SchemaPrefix

    @property
    def ADC_ADCDALIAS(self):
        return f"{self.SchemaPrefix}_ADC_ADCALIAS"

    @property
    def ADC_ADCDATA(self):
        return f"{self.SchemaPrefix}_ADC_ADCDATA"

    @property
    def ADC_ADCLINK(self):
        return f"{self.SchemaPrefix}_ADC_ADCLINK"

    @property
    def GLQ_EXECUTE(self):
        return f"{self.SchemaPrefix}_GLQ_EXECUTE"

    @property
    def LOC_FILREG(self):
        return f"{self.SchemaPrefix}_LOC_FILREG"

    @property
    def LOC_LOCREG(self):
        return f"{self.SchemaPrefix}_LOC_LOCREG"

    @property
    def LOC_PRBREG(self):
        return f"{self.SchemaPrefix}_LOC_PRBREG"

    @property
    def SYS_INVTYPES(self):
        return f"{self.SchemaPrefix}_SYS_INVTYPES"

    @property
    def SYS_LOCTABS(self):
        return f"{self.SchemaPrefix}_SYS_LOCTABS"

    @property
    def SYS_LOCTABTY(self):
        return f"{self.SchemaPrefix}_SYS_LOCTABTY"

    @property
    def SYS_LOCTYPES(self):
        return f"{self.SchemaPrefix}_SYS_LOCTYPES"

    @property
    def SYS_PRJDEFS(self):
        return f"{self.SchemaPrefix}_SYS_PRJDEFS"

    @property
    def LOCPRMGR(self):
        return f"{self._Schema}.LOCPRMGR".lstrip(".")


class GxDbCommandText:
    """

    25.07.2023 j.ebert
    """
    def __init__(
        self,
        parent                  # Referenz auf GxDbConnection
    ):
        self.log = logging.getLogger(f"{gqc._LOG_PARENTS}{self.__class__.__name__}")
        self._context = "gx"    # Context für Transaltion/Übersetzung vom Modul gx
        self._Parent = parent
        """reference to GxDbConnection"""
        self.Tbl = GxTables(
            self._Parent._CnnPrps.get('schema', ''),
            'GEODIN'
        )

    def fullTableName(self, shortTblName):
        return f"{self.Tbl.Prefix}_{shortTblName}"

    def existsTable(self, shortTblName):
        dbSQL = f"SELECT * FROM {self.Tbl.SchemaPrefix}_{shortTblName} WHERE 0=9"
        return dbSQL

    def load_ExistingINVTYPES(self, prjID=''):
        where_clause = "" if not prjID else f" WHERE PRJ_ID = '{prjID}'"
        dbSQL = f"""
SELECT INVID FROM {self.Tbl.LOC_FILREG} {where_clause}
UNION
SELECT INVID FROM {self.Tbl.LOC_LOCREG} {where_clause}
UNION
SELECT INVID FROM {self.Tbl.LOC_PRBREG} {where_clause}
        """
        return dbSQL

    def load_ExistingLOCTYPES(self, prjID=''):
        where_clause = "" if not prjID else f" WHERE PRJ_ID = '{prjID}'"
        dbSQL = f"""SELECT DISTINCT LOCTYPE FROM {self.Tbl.LOC_LOCREG} {where_clause}"""
        return dbSQL

    def load_LOCPRMGR(self, name=''):
        if not name:
            name = self.Tbl.LOCPRMGR
        dbSQL = f"""
SELECT PRJ_ID, PRJ_NAME, PRJ_ALIAS, PRJ_TYPE, PRJ_OPT, PRJ_USER, PRJ_DATE, PRJ_PATH, GEODINGUID
FROM {name}"""
        return dbSQL

    def load_PRJDEFS(self, owner=''):
        # 07/2023 j.ebert, Anmerkung
        #   31.07.2023 EbJo/ScRo/HoSe (Team Meetning Support)
        #       Was ist LOCPRMGR::OBJ_OWNER - nutzer vom DB-Login oder vom Windows-Login?
        #       - LOCPRMGR::OBJ_OWNER - Windows-Login!?
        #       - GeODin 9 (mit Benutzerverwaltung):
        #         OBJ_OWNER wird nicht mehr gesetzt/ wird in LOCPRMGR::OBJ_DATA (Blob) gespeichert
        #   Fazit:
        #       LOCPRMGR::OBJ_OWNER - überholt -> ignorieren (gar nicht mehr laden/einlesen)
        #       Kein Zugriff auf GeODin-Benutzerverwaltung -> alle Abfragen laden
        #       (erst beim Ausführen zeigt sich, ob die Abfrage verfügbar/nutzbar ist)
        if owner:
            self.log.warning("Argument 'owner' is ignored/is no longer supported")
            sqlWhere = "OBJ_OWNER = '{owner}'"
        else:
            sqlWhere = "OBJ_OWNER = '' OR OBJ_OWNER IS Null"

        dbSQL = f"""
SELECT
    PRJ_ID, OBJ_ID, OBJ_DESC, OBJ_NAME, OBJ_OPT
FROM {self.Tbl.SYS_PRJDEFS}
WHERE (OBJ_DESC = 'MESQUERY') OR (OBJ_DESC = 'LOCQUERY')
        """
        # 08/2023 j.ebert, SQL-Statement inkl. Anmerkung aus GeODinXtn für ArcMap 10 übernommen
        #                  Stand vor 2017(!) <- GeODinXtn für ArcMap 10 wurde 12/2017 eingefroren
        #   Achtung!
        #   - OBJ_ID ist nicht immer unique in der GeODin-Datenbank
        #     (in Test-DB traten OBJ_IDs mehrfach auf, vielleicht nach Kopieren einer GeODin-Porjektes)
        #   - Aggregat-Funktion FIRST() ist NICHT Standard (in Oracle funktioniert First() nicht wie in Access)
        #   - Oracle akzeptiert AS vor dem Tabellen-Alias NICHT!!!
        #   SQL-Statement getestet mit Access, MS SQL, MySQL, Posrtgre, Oracle
        dbSQL = f"""
SELECT PD.PRJ_ID, PD.OBJ_DESC, PD.OBJ_NAME, Q.OBJ_CNT
FROM {self.Tbl.SYS_PRJDEFS} PD INNER JOIN (
    SELECT P2.PRJ_ID, Max(P2.OBJ_ID) AS OBJ_ID, Count(P2.OBJ_ID) AS OBJ_CNT
    FROM {self.Tbl.SYS_PRJDEFS} P2
    WHERE (OBJ_DESC = 'MESQUERY') OR (OBJ_DESC = 'LOCQUERY')
    GROUP BY P2.PRJ_ID, P2.OBJ_NAME
) Q ON (PD.PRJ_ID = Q.PRJ_ID) AND (PD.OBJ_ID = Q.OBJ_ID)
        """
        return dbSQL

    def load_LOCTYPES(self):
        dbSQL = f"SELECT * FROM {self.Tbl.SYS_LOCTYPES} WHERE GEN_OPT <> 129"
        return dbSQL

    def load_LOCTABTY(self):
        dbSQL = f"""
SELECT
    LOCTABS.GEN_DESC AS GEN_DESC,
    TY.TAB_DESC AS TAB_DESC, TY.TAB_NAME AS TAB_NAME, TY.TAB_TYPE AS TAB_TYPE, TY.TAB_OPT AS TAB_OPT, TY.TAB_TRC AS TAB_TRC, TY.INV_TYPE AS INV_TYPE
FROM {self.Tbl.SYS_LOCTABS} LOCTABS
INNER JOIN {Tbl.SYS_LOCTABTY} TY ON LOCTABS.TAB_DESC = TY.TAB_DESC
        """
        return dbSQL

    def load_INVTYPES(self):
        dbSQL = f"SELECT * FROM {self.Tbl.SYS_INVTYPES}"
        return dbSQL

    def load_ADCALIAS(self):
        dbSQL = f"""
SELECT ALIAS_NAME, ALIAS_TEXT
FROM {self.Tbl.ADC_ADCDALIAS}
        """
        return dbSQL

    def load_ADCDATA(self):
        # 07/2023 j.ebert, Achtung
        #   Die Reihenfolge und Position der Felder/Spalten beim SELECT ist relevant!!!
        #   Auch in GxDbConnection.load_ADCDATA() wird die Position von 'ADC_FILE' beim Ersetzen
        #   der Alias benötigt und außerdem beim Logging 'PRJ_ID' (Pos 0), 'ADC_ID' (Pos 1) und
        #   'ADC_NAME' vor 'ADC_FILE'.
        dbSQL = f"""
SELECT
    LINK.PRJ_ID,
    DATA.ADC_ID, DATA.ADC_TYPE, DATA.ADC_DESC, DATA.ADC_OPT, DATA.ADC_NAME, DATA.ADC_FILE,
    DATA.ADC_DATE, DATA.ADC_TIME, DATA.GEODINGUID
FROM {self.Tbl.ADC_ADCDATA} DATA
LEFT JOIN {self.Tbl.ADC_ADCLINK} LINK ON DATA.ADC_ID = LINK.ADC_ID
WHERE (DATA.ADC_FILE IS NOT NULL)
        """
        return dbSQL

    def select_TypLOC(self, prjID, desc, tblName):
        raise NotImplementedError()

    def select_TypINV(self, prjID, desc, tblName):
        raise NotImplementedError()

    def select_QryGLQ(self, prjID, id):
        raise NotImplementedError()

class GxDbConnection:
    """class for direct access to a GeODin database

    25.07.2023 j.ebert
    """

    def __init__(
        self,
        gDB                     # Referenz auf GoDatabase
    ):
        self.log = logging.getLogger(f"{gqc._LOG_PARENTS}{self.__class__.__name__}")
        self._context = "gx"    # Context für Transaltion/Übersetzung vom Modul gx
        self._gDB = gDB
        """Referenz auf GoDatabase"""
        self._CnnPrps = {}
        """Connection properties"""
        self._CnnPrv = None
        """Database provider (GxDbProvider)"""
        self._CnnPwd = ""
        """current database login password"""
        self._CnnUsr = ""
        """current database login user"""
        # Initialiserung...
        # Achtung
        #   Erste _CnnPrps initialisiern und danach _CmdText, da
        #   bei der Initialisierung von _CmdText bereits _CnnPrps['schema'] gesetzt sein muss
        self._CnnPrps = self._validateCnnPrps(self._gDB._Settings)
        self._CmdText = GxDbCommandText(self)

    @property
    def DbName(self):
        return self._gDB.Name

    @property
    def DriverID(self):
        """FireDAC DriverID (MSACC, MSSQL, PG, ...)

        25.07.2023 j.ebert
        """
        return self._CnnPrps.get('driverid', '')

    @property
    def CmdText(self):
        """FireDAC DriverID (MSACC, MSSQL, PG, ...)

        25.07.2023 j.ebert
        """
        return self._CmdText

    def connect(
        self,
        usr=None,               # database login user
        pwd=None                # database login password
    ):
        return self._CnnPrv.connect(usr, pwd)

    def load_ADCDATA(self):
        """loads relevant data from the table ADC_ADCDATA

        returns:
            None    - wenn die Tabelle'ADC_ADCDATA' in der GeODin-Datenbank nicht existiert
            []      - wenn die Tabelle'ADC_ADCDATA' existiert, aber keine relevanten Daten
            [....]  - wenn die Tabelle'ADC_ADCDATA' mit relevanten Daten existiert

        26.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "%s Database '%s'...", self.DriverID, self.DbName)
        # Index der Spalte 'ADC_FILE' in der Liste 'resData' setzen - also wo ALIAS ersetzt werden soll
        # Achtung
        #   Der Index ist letztendlich vom SQL-Statement abhängig, an welcher Position
        #   die Spalte/das Feld 'ADC_FILE' beim SELECT im SQL-Statement steht.
        #   siehe dazu GxDbCommandText.load_ADCDATA()
        idxPosFile = 6
        # Initialisierung...
        res = None
        resData = None
        resAlias = []
        if not self._CnnPrv.exists_Tbl(self.CmdText.Tbl.ADC_ADCDATA):
            self.log.debug(
                "gDB '%s': Table '%s%' not exists", self.DbName, self.CmdText.Tbl.ADC_ADCDATA
            )
        else:
            # Wenn die Tabelle 'ADC_ADCDATA' existiert,
            # dann resData eine leere Listre zuweisen - notw. für den Fall einer Exception!!!
            # (Exception beim laden der Daten/im SQL-Statement -> leere Liste und Error-Logging)
            resData = []
            cmdText= ""
            try:
                cmdText = self.CmdText.load_ADCDATA()
                self._log_GxSQL(cmdText)
                resData = self._CnnPrv.load_Data(cmdText)
                self._log_GxSQL()
                if not resData:
                    pass
                elif not self._CnnPrv.exists_Tbl(self.CmdText.Tbl.ADC_ADCDALIAS):
                    self.log.warning(
                        "gDB '%s': Table '%s%' not exists", self.DbName, self.CmdText.Tbl.ADC_ADCDALIAS
                    )
                else:
                    cmdText = self.CmdText.load_ADCALIAS()
                    self._log_GxSQL(cmdText)
                    resAlias = self._CnnPrv.load_Data(cmdText)
                    self._log_GxSQL()
            except:
                self.log.error(
                    "%s Database '%s': Unknown error...\n\n%s\n",
                    self.DriverID, self.DbName, cmdText,
                    exc_info=True
                )
        # 07/2023 j.ebert, Achtung
        #   Folgende if-Bedingung genau so und nicht anders (wie bool(resData) zum Beispiel)!!!
        #   - resData is None   - ADCDATA gibt es nicht in der GeODin-Datenbank
        #   - resData == []     - ADCDATA existiert prinzipiell, aber keine relevanten Daten
        #   - resData == [....] - ADCDATA existiert mit relevanten Daten (also List ist nicht leer)
        if resData is not None:
            # Alias laden und für Ersetzung modifizieren
            #   resAlias                - Alias aus der GeODin-Datenbank
            #   self.load_SYSALIAS()    - Alias der GeODin-Konfiguration (%DBROOT, %GEODINROOT,...)
            tmpAlias = [(f"${alias[0]}$", alias[1]) for alias in (resAlias + self.load_SYSALIAS())]
            self.log.debug("tmpAlias: %s", str(tmpAlias))
            # Alias ersetzen...
            # - Output-Liste vorbereiten
            #   07/2023 Anmerkung
            #       Elemente müssen vom Typ list sein, damit ADC_FILE ersetzt werden kann.
            #       Elemente, bei denen ADC_FILE nicht gesetzt ist, werden ignoriert/eliminiert.
            res = [list(row) for row in resData if row[idxPosFile]]
            # - Alias in der Output-Liste ersetzen
            for row in res:
                for alias in tmpAlias:
                    if isinstance(row[idxPosFile], str) and  (alias[0] in row[idxPosFile]):
                        row[idxPosFile] = row[idxPosFile].replace(alias[0],alias[1])
            # - Output-Liste protokollieren
            #   (Ausgabe "reduzieren", damit Liste mit JSON serialisierbar ist.)
            logRes = [[row[1], row[2], row[idxPosFile-1], row[idxPosFile]] for row in res]
            self.log.debug(
                "gDB '%s': PRJ_ID, ADC_ID, ADC_NAME, ADC_FILE\n\t%s",
                self.DbName,
                json.dumps(logRes, indent=4).replace("\n", "\n\t")
            )
        return res

    def load_ExistingINVTYPES(self, prjID):
        """loads GeODin table INVTYPES

        returns:
            res (list())        # list of messurment point types (INV_TYPE)


        26.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "%s Database '%s'...", self.DriverID, self.DbName)
        res = []
        try:
            cmdText = self.CmdText.load_ExistingINVTYPES(prjID)
            self._log_GxSQL(cmdText)
            res = self._CnnPrv.load_Data(cmdText)
            self._log_GxSQL()
            if self.log.level <= logging.DEBUG:
                logRows = [row[0] for row in res[:6]]
                self.log.debug(
                    "INVIDs (PrjID '%s'): \n\t%s",
                    prjID, json.dumps(logRows, indent=4).replace("\n", "\n\t")
                )
            # 07/2023 j.ebert, Anmerkung
            #   list(...)   - Ergebnis der Methode ist als list definiert
            #   set(...)    - unique Items/INV_TYPES der inneren Liste
            #   [...]       - list comprehension zum Filtern der INV_TYPES aus dem Abfrageergebnis
            #   ...[10:13]  - INV_TYPE aus der INVID Extrahieren
            #   row[0]      - INVID aus Tuple extrahieren
            #                 Ergebnis einer SQL-Abfrage ist immer List of Tuple!!!
            res = list(set([row[0][10:13] for row in res]))
            if self.log.level <= logging.DEBUG:
                self.log.debug(
                    "INV_TYPES (PrjID '%s'): \n\t%s",
                    prjID, json.dumps(res, indent=4).replace("\n", "\n\t")
                )
        except:
            self.log.critical("Major disaster...", exc_info=True)
        return res

    def load_ExistingLOCTYPES(self, prjID):
        """loads GeODin table INVTYPES

        returns:
            res (list())        # list of messurment point types (INV_TYPE)


        26.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "%s Database '%s'...", self.DriverID, self.DbName)
        res = []
        try:
            cmdText = self.CmdText.load_ExistingLOCTYPES(prjID)
            self._log_GxSQL(cmdText)
            res = self._CnnPrv.load_Data(cmdText)
            self._log_GxSQL()
            # 07/2023 j.ebert, Anmerkung
            #   Ergebnis der SQL-Abfrage ist eine List of Tuple!!!
            #   Jeder Eintrag ist ein Tuple, auch wenn nur genau eine Spalten enthalten ist.
            #   Ergebnis transformieren list(tuple) -> list(str)
            #       Wenn Provider unterscheidliche Ergebnisse liefern,
            #       dann Transformation in die Provider Methode verschieben,
            #       aber Achtung, Trasnformation in load_Data() nur wenn len(row) == 1
            res = [row[0] for row in res]
        except:
            self.log.critical("Major disaster...", exc_info=True)
        return res

    def load_INVTYPES(self):
        """loads GeODin table INVTYPES

        returns:
            res (list())        # list of messurment point types/tuples
                                # (INV_TYPE, INV_NAME, INV_OPT)

        26.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "%s Database '%s'...", self.DriverID, self.DbName)
        res = []
        try:
            cmdText = self.CmdText.load_INVTYPES()
            self._log_GxSQL(cmdText)
            res = self._CnnPrv.load_Data(cmdText)
            self._log_GxSQL()
        except:
            self.log.critical("Major disaster...", exc_info=True)
        return res

    def load_LOCPRMGR(
        self,
        qualifiedTblName=''
    ):
        """loads GeODin projects from table/view (default from LOCPRMGR)

        returns:
            res (list())        # list of projects/tuples
                                # (PRJ_ID, PRJ_NAME, PRJ_ALIAS, PRJ_TYPE, PRJ_OPT, PRJ_USER, PRJ_DATE, PRJ_PATH, GEODINGUID)

        26.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "%s Database '%s'...", self.DriverID, self.DbName)
        res = []
        try:
            # 09/2023 j.ebert, default Leerstring übergeben (und den Namen 'LOCPRMGR')!
            #   Wenn eine TableName übergeben wird,
            #   dann muss der qualifizierte TableName sein (<Schema>.<TableName>)!
            #   (Wenn kein TableName übergeben wird, dann wird <Schema>.LOCPRMGR genutzt.)
            cmdText = self.CmdText.load_LOCPRMGR(qualifiedTblName)
            self._log_GxSQL(cmdText)
            res = self._CnnPrv.load_Data(cmdText)
            self._log_GxSQL()
        except:
            self.log.critical("Major disaster...", exc_info=True)
        return res

    def load_LOCTYPES(self):
        """loads GeODin table LOCTYPES but not GEN_OPT = 129 (Document Types)

        returns:
            res (list())        # list of object types/tuples
                                # (GEN_DESC, GEN_NAME, GEN_OPT, GEN_VERS)

        26.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "%s Database '%s'...", self.DriverID, self.DbName)
        res = []
        try:
            cmdText = self.CmdText.load_LOCTYPES()
            self._log_GxSQL(cmdText)
            res = self._CnnPrv.load_Data(cmdText)
            self._log_GxSQL()
        except:
            self.log.critical("Major disaster...", exc_info=True)
        return res

    def load_PRJDEFS(self):
        """loads GeODin table PRJDEFS for current owner

        returns:
            res (list())        # list of queries/tuples
                                # (PRJ_ID, OBJ_ID, OBJ_DESC, OBJ_NAME, OBJ_OPT, OBJ_OWNER)

        26.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "%s Database '%s'...", self.DriverID, self.DbName)
        res = []
        try:
            owner = ""
            cmdText = self.CmdText.load_PRJDEFS(owner)
            self._log_GxSQL(cmdText)
            res = self._CnnPrv.load_Data(cmdText)
            self._log_GxSQL()
        except:
            self.log.critical("Major disaster...", exc_info=True)
        return res

    def load_SYSALIAS(self):
        """loads SYSALIAS dictionary

        15.08.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "%s Database '%s'...", self.DriverID, self.DbName)
        res = []
        # Alias der GeODin-Konfiguration laden...
        res += gx.gApp.loadSYSALIAS()
        # Alias '%DBRROT' für filebasierte Datenbanken setzen...
        if (
            (self.DriverID == "MSACC") and
            bool(self._CnnPrps.get('database', ''))
        ):
            res.append(['%DBROOT', str(Path(self._CnnPrps['database']).parent)])
        # Alias protokollieren...
        self.log.info(
            "SYSALIAS (NAME, ALIAS):\n\t%s",
            json.dumps(res, indent=4).replace("\n", "\n\t")
        )
        return res


    def _log_GxSQL(
        self,
        cmdText=""
    ):
##        msg = f"\n{cmdText}" if cmdText else ""
##        self.log.log(gqc._LOG_GxSQL, "-------- GxSQL --------%s", msg)
        if cmdText:
            self.log.log(gqc._LOG_GxSQL, "-------- SQL (%s) --------\n%s", self.DriverID, cmdText)
        else:
            self.log.log(gqc._LOG_GxSQL, "")
        return

    def _validateCnnPrps(
        self,
        settings                # GeODin configuration (TGClass_DatabaseSettingsList)
    ):
        """validates GeODin configuration (from TGClass_DatabaseSettingsList)

        12.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "")
        # 05/2023 j.ebert, GeODin 9.6.264.0 (13.01.2023 - Win64)
        #    Ergebnis der GeODin-COM-Funktion sysInfo("RequestData=Databases"):
        #    "TGClass_DatabaseSettingsList": [
        #        {
        #            "DisplayName": "Berlin_SEP3 (PG)",
        #            "ConnectionString": "Database=geodin_berlin_sep3;User_Name=geodin;Password=*****;DriverID=PG",
        #            "AutoOpen": false,
        #            "HideLocationTypes": false,
        #            "HideEmptyLocationTypes": true,
        #            "HideMesPointTypes": false,
        #            "HideEmptyMesPointTypes": true,
        #            "GOMGroup": "",
        #            "Schema": "geodin"
        #        }
        #    ]
        prps = {
            'error': ''                 # error message|empty string
        }
        try:
            # Paramter aus GeODin Configuration übernehmen...
            prps['connectionstring'] = settings['ConnectionString']
            prps['schema'] = settings['Schema']
            # GeODin ConnectionString analysieren/splitten....
            pattern = re.compile(r'''
                ([\w]+)     # group 1/key - Zeichen von a-z, A-Z oder 0-9 oder Unterstrich
                =           # Trennung zwischen group 1/key und group 2/val
                ([^;]+)     # group 2/val - alle Zeichen außer Semikolon
            ''', re.IGNORECASE | re.VERBOSE)
            for match in re.finditer(pattern, prps['connectionstring']):
                prps[match.group(1).lower()] = match.group(2)
            prps['driverid'] = prps['driverid'].upper()
            self.log.debug(json.dumps(prps, indent=4).replace('\n','\n\t'))
            # Parameter für Plugin Connection validieren...
            # - Default ErrorMessage setzen...
            #   Default: Datenbank vom Typ (bzw. mit FireDAC-DirverID) wird nicht unterstützt
            prps['error'] = gqb.res.translate(
                self._context,
                "%s-Databases not supported"
            ) % prps['driverid']
            # - Methode zur Validierung der ConnectionProperties für die akt. FireDAC-DirverID
            #   ermitteln und ausführen, wenn sie existiert
            func4DriverID = getattr(self, "_validateCnnPrps4%s" % prps['driverid'], None)
            if func4DriverID:
                func4DriverID(prps)
            self.log.debug(
                json.dumps(prps, indent=4).replace("\n", "\n\t")
            )
        except:
            self.log.error(
                "Error extracting DBConnection\n\t%s",
                str(settings),
                exc_info=True
            )
            prps = {}
            raise gqb.GxException('Error extracting DBConnection')
        return prps

    def trans(
        self,
        key,
        *args
    ):
        return gqb.res.trans(self._context, key, *args)

    def _validateCnnPrps4MSACC(
        self,
        prps                    # Connection properties
    ):
        """validates connection propertie for MSACC

        13.06.2023 j.ebert
        """
        # seealso:
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Defining_Connection_(FireDAC)
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Connect_to_Microsoft_Access_Database_(FireDAC)
        #   GeODinQGIS_Main.py/GeODinQGISMain.connectToDatabase(self, database, query, create = False, param=None)
        self.log.log(gqc._LOG_TRACE, "")
        try:
            prps['info'] = prps.get('database', "")
            if  not prps.get('database'):
                error = gqb.res.translate(self._context, "Database/File not defined")
            elif not Path(prps.get('database')).exists():
                error = gqb.res.translate(self._context, "Database/File not found")
            else:
                error = gqb.res.translate(
                    self._context,
                    "Failed to validate %s connection"
                ) % prps['driverid']
                # GxDbProvider prüfen/setzen/validieren
                if 'GxDbProvider4MSACC' not in globals():
                    raise gqb.GxSQLError("%s database provider not found", prps['driverid'])
                else:
                    self._CnnPrv = GxDbProvider4MSACC(self)
                    self._CnnPrv.validate()
            # erfolgreich -> Fehler(-Meldung) zurücksetzen
            error = ""
        except gqb.GQgisException as exc:
            self.log.error(exc.msg())
        except:
            self.log.error("Failed to validate %s connection", prps['driverid'], exc_info=True)
        finally:
            prps['error'] = error
        return

    def _validateCnnPrps4MSSQL(
        self,
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
        self.log.log(gqc._LOG_TRACE, "")
        try:
            error = self.trans("Failed to validate %s connection", prps['driverid'])
            prps['info'] = ("%s:%s" % (prps.get('server', ""), prps.get('port', ""))).strip(' :')
            prps['info'] = ("%s/%s" % (prps['info'], prps.get('database', ""))).strip(' /')
            # GxDbProvider prüfen/setzen/validieren
            if 'GxDbProvider4MSSQL' not in globals():
                raise gqb.GxSQLError("%s database provider not found", prps['driverid'])
            else:
                self._CnnPrv = GxDbProvider4MSSQL(self)
                self._CnnPrv.validate()
            # erfolgreich -> Fehler(-Meldung) zurücksetzen
            error = ""
        except gqb.GQgisException as exc:
            self.log.error(exc.msg())
        except:
            self.log.error("Failed to validate %s connection", prps['driverid'], exc_info=True)
        finally:
            prps['error'] = error
        return

    def _validateCnnPrps4PG(
        self,
        prps                    # Connection properties
    ):
        """validates connection propertie for P

        13.06.2023 j.ebert
        """
        # seealso:
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Defining_Connection_(FireDAC)
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Connect_to_PostgreSQL_%28FireDAC%29
        self.log.log(gqc._LOG_TRACE, "")
        try:
            error = self.trans("Failed to validate %s connection", prps['driverid'])
            prps['info'] = ("%s:%s" % (prps.get('server', ""), prps.get('port', ""))).strip(' :')
            prps['info'] = ("%s/%s" % (prps['info'], prps.get('database', ""))).strip(' /')
            # GxDbProvider prüfen/setzen/validieren
            if 'GxDbProvider4PG' not in globals():
                raise gqb.GxSQLError("%s database provider not found", prps['driverid'])
            else:
                self._CnnPrv = GxDbProvider4PG(self)
                self._CnnPrv.validate()
            # erfolgreich -> Fehler(-Meldung) zurücksetzen
            error = ""
        except gqb.GQgisException as exc:
            self.log.error(exc.msg())
        except:
            self.log.error("Failed to validate %s connection", prps['driverid'], exc_info=True)
        finally:
            prps['error'] = error
        return


def main():
    pass

if __name__ == '__main__':
    main()
