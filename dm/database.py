"""
Classes:
    GxDDX                 - Data Dictionary

Functions:
    default()

24.04.2024 j.ebert
"""
import os
import datetime
import hashlib
import json
import logging
import random
import shutil
import string
import time
import traceback
import zipfile
from  collections import Counter
from pathlib import Path

import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gqgis_config as gqc
import GeODinQGIS.dm.bas as bas
from GeODinQGIS import res
from GeODinQGIS.dm.lnkadc import GoLnkADC
from GeODinQGIS.dm.project import GoProject
from GeODinQGIS.dm.query import GoQuery
import GeODinQGIS.gx as gx
from GeODinQGIS.gx.system import GxSys
#from GeODinQGIS.ui.gqgis_dlg_login import GQgis_Dlg_Login

class GoDatabase(bas.GoBaseClass):
    """ GeODin Database object

    30.05.2023 j.ebert
    """
    DBPrjID = 'DBDEF'
    DBCount = 0

##    _NoDesc = 'dbxxx'
##    _DumpPrefix = 'gxdb'
    _NoDesc = 'gxdbXXXX'
    _Prefix = 'gxdb'

    def __init__(self):
        super().__init__(None, self.DBPrjID, "")
        GoDatabase.DBCount += 1
        self._DbRef = self
        self._DDX = None
        self._Desc = self._NoDesc
        self._Idx = self.DBCount
        self._Name = 'Database [%02d]' % self._Idx
        self._Settings = {}
        """Settings Dict from 'TGClass_DatabaseSettingsList'"""
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
        self._CnnPrps = {}
        """Connection properties"""
        self._GoDict = {}
        """GeODin dictionary with names of INV types, LOC types, etc."""
        self._GoPrjs = []
        self._GoQrys = []

        self._DumpDict = {}
        """Dump dictionary, wich is updated by store() and restore()"""

        self._isOpened = False
        self._isPresent = False
        # GeODin Tabellen/Strukturen initialisieren/zurücksetzen
        self.unload()

    @property
    def CRef(self):
        """ corss reference (for class 'GoDatabase' GeODin DisplayName)

        06.06.2023 j.ebert
        """
        return self.Name

    @property
    def DataPath(self):
        val = None
        if bool(self._DDX):
            val = Path(self._DDX.Data) / self.dumpFilename()
        return val

    @property
    def Desc(self):
        """ description/classification

        06.06.2023 j.ebert
        """
        if self._Desc == self._NoDesc:
            # Wenn Attr Desc nocht nicht gesetzt ist,
            # dann unique/eindeutige Eintrag für DDX ermitteln
            self.log.log(gqc._LOG_TRACE,"")
            # - DDX-Data-Path (als Perant vom GoDatabase DataPath)
            #   06/2023 j.ebert, Anmerkung
            #       Zum Prüfen, ob ggf. der DataPath bereits existiert (also irgendein Überbleibsel)
            ddxDataPath = Path(self._DDX.Data)
            # - belegte/vergebene Einträge im DDX ermitteln
            #   06/2023 j.ebert, Achtung
            #       In der Schleife nicht self.Desc, sondern auf self._Desc nutzen, sonst
            #       wird dieser Code 'rekursive' für alle Datenbanken des DDX aufgerufen.
            takenDesc = [gDB._Desc for gDB in self._DDX.Databases if gDB._Desc != self._NoDesc]
            # - unique/eindeutige Eintrag ermitteln
            ddxDumpFilenames = self._DDX.dumpFilenames()
            for idx in range(1,4096):
                self._Desc = "%s%04x" % (self._Prefix, idx)
                if (
                    (self._Desc not in takenDesc) and
                    (self.dumpFilename() not in ddxDumpFilenames) and
                    (not (ddxDataPath / self.dumpFilename()).exists())
                ):
                    break
            else:
                self._Desc = self._NoDesc
                self.log.critical(
                    "%s.Desc could not be set unique!", self.__class__.__name__
                )
                raise gqb.GQgisException(
                    "%s.Desc could not be set unique!", self.__class__.__name__
                )
            self.log.debug("Database [%02d] '%s': Desc = '%s'", self._Idx, self.Name, self._Desc)
        return self._Desc

    @property
    def DriverID(self):
        """FireDAC DriverID (MSACC, MSSQL, PG, ...)

        13.07.2023 j.ebert
        """
        return self._CnnPrps.get('driverid', '')

    @property
    def Info(self):
        """ info/ToolTip

        13.06.2023 j.ebert
        """
        info = self._CnnPrps.get('info',self.Name)
        if self._CnnPrps.get('error',""):
            info = "%s\n%s" % (info, self._CnnPrps.get('error', ""))
        return info

    @property
    def UID(self):
        """ unique identiyfyer (for class "GeoDatabase" same as property 'Desc')

        06.06.2023 j.ebert
        """
        return self.Desc

    @property
    def GOMGroup(self):
        return self._Settings.get('GOMGroup', "")

    @property
    def GoPrjs(self):
        return self._GoPrjs

    @property
    def GoQrys(self):
        return self._GoQrys

    @property
    def _Queries(self):
        self.log.critical(
            "Attribute '%s' is superseded by atttribute '%s'\n\t%s",
            '_Queries', 'GoQrys', traceback.format_stack()[-2].strip()
        )
        return self._GoQrys

    @property
    def GT_ADCDATA(self):
        return self._GT_ADCDATA

    @property
    def GT_GLQEXEC(self):
        return self._GT_GLQEXEC

    @property
    def GT_INVTYPES(self):
        return self._GT_INVTYPES

    @property
    def GT_LOCPRMGR(self):
        return self._GT_LOCPRMGR

    @property
    def GT_LOCTABTY(self):
        return self._GT_LOCTABTY

    @property
    def GT_LOCTYPES(self):
        return self._GT_LOCTYPES

    @property
    def GT_PRJDEFS(self):
        return self._GT_PRJDEFS

    def findGoQryByUID(
        self,
        uid
    ):
        assert isinstance(uid, str) and bool(uid), \
            "Argument 'uid' of type str is required"
        goQry = None
        # 08/2023 j.ebert, Anmerkung
        #   Hier nicht über das Attr UID suchen, da
        #   beim Aufruf des Attr UID das Attr Desc für GeODin-Abfragen gesetzt wird.
        #   Das ist hier unnötig, hier besser UID der Query "zusammensetzen" und vergleichen.
        goQrys = [qry for qry in self.GoQrys if (
            ("%s_%s_%s_%s" % (qry.DbRef.Desc, qry.PrjID, qry.Kind, qry._Desc)) == uid
        )]
        if len(goQrys) == 1:
            goQry = goQrys[0]
        return goQry

    def hasADCDATA(self):
        """True, if Database has ADCDATA

        25.07.2023 j.ebert
        """
        return (self.GT_ADCDATA is not None)

    def isDirty(self):
        """True, if ...

        06.06.2023 j.ebert
        """
        return True

    def isDisabled(self):
        """True, if database is not configured, not supoorted and so on

        09.06.2023 j.ebert
        """
        enabled = (
            bool(self._Settings) and
            (not bool(self._CnnPrps.get('error', "Unknwon Database-Error")))
        )
        return not enabled

    def isOpened(self):
        """True, if GeODin Database/Database Connection is opened

        30.05.2023 j.ebert
        """
        return self._isOpened

    def isPresent(self):
        """True, if GeODin Database in GeODinQGIS Explorer/Catalog

        30.05.2023 j.ebert
        """
        return self._isPresent

    def list_GrpADC(
        self,
        prjID
    ):
        idxFld_PRJ_ID = GoLnkADC.idxADCDATAFld('PRJ_ID')
        rows = [row for row in self._GT_ADCDATA if row[idxFld_PRJ_ID] == prjID]
        lnks = [GoLnkADC.fromADCDATA(self, prjID, row) for row in rows]
        return lnks

    def list_GrpINV(
        self,
        prjID
    ):
        self.log.log(gqc._LOG_TRACE,"")
        qrys = [
            qry for qry in self._GoQrys if (qry.PrjID == prjID) and (qry.Kind[-3:] == 'INV')
        ]
        if self.log.level <= logging.DEBUG:
            logRows = [str(row) for row in qrys]
            self.log.debug(
                "INV-Abfragen (PrjID '%s'): \n\t%s",
                prjID, json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
        return qrys

    def list_GrpLOC(
        self,
        prjID
    ):
        self.log.log(gqc._LOG_TRACE,"")
        qrys = [
            qry for qry in self._GoQrys if (qry.PrjID == prjID) and (qry.Kind[-3:] == 'LOC')
        ]
        if self.log.level <= logging.DEBUG:
            logRows = [str(row) for row in qrys]
            logRows = [row.Kind for row in qrys]
            self.log.debug(
                "LOC-Abfragen (PrjID '%s'): \n\t%s",
                prjID, json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
        return qrys

    def list_Project(self):
        self.log.critical(
            "Methode '%s' is superseded by atttribute '%s'\n\t%s",
            'list_Project()', 'GoPrjs', traceback.format_stack()[-2].strip()
        )
        return self._GoPrjs
        # 07/2023 j.ebert, Anmerkung
        #   Zur Zeit ist die erste List-Comprehension sinnfrei, aber
        #   für GeODin-Datenbanken mit Projekten die mehr als 9999 Objekte/Lokationen haben können,
        #   müssen die "echten" Projekten identifiziert werden, entweder hier oder
        #   bereits breits bei der SQL-Abfrage von LOCPRMGR
        idxFld_PRJ_ID = GoProject.idxSQLFld('PRJ_ID')
        rows = [row for row in self._GT_LOCPRMGR if row[idxFld_PRJ_ID]]
        prjs = [GoProject.fromSQL(self, row) for row in rows]
        return prjs

    def add(self):
        self.log.log(gqc._LOG_TRACE,"")
        # 06/2023 j.ebert, Achtung!
        #   Mit dem folgenden Log und der Abfrage der Prp 'Desc' wird 'Desc' ermittelt/gesetzt.
        self.log.debug("Database [%02d] '%s': Desc = '%s'", self._Idx, self.Name, self.Desc)        # DumpDict erstellen und aktualsieren
        if (
            # 06/2023 j.ebert, Anmerkung
            #   Wenn die DB aus dem DDX geladen wird,
            #   dann wird dabei Attr '_isPresent' gesetzt und die DB muss nicht gespeichert werden
            #   Wenn aber die DB im gQGIS Explorere/Catalog hinzugefügt wird,
            #   dann ist Attr '_isPresent' noch nicht gesetzt und die DB muss gespeichert werde
            (not self.isPresent())
        ):
            self.store()
        self._isPresent = True
        return

    def dumpFilename(self):
        """ returns GoDatabase dump filename

        15.06.2023 j.ebert
        """
        # 06/2023 j.ebert, Anmerkung
        #   Decsription (self.Desc) und Dump-Filename (self.dumpFilename) einheitlich (inkl. 'gx')
        #       return self.Desc    # bis 15.06.2023 ("gx%s" % self.Desc)
        return self.Desc

    def store(self):
        """stores GoDatabase into DDX

        31.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        dmpDict = dict(self)
        # - genutzte Projekte und Abfragen akualisieren
        usedPrjIDs = set([qry.PrjID for qry in self.GoQrys if qry._isUsed])
        dmpDict['GoProjects'] = [dict(prj) for prj in self.GoPrjs if prj._PrjID in usedPrjIDs]
        dmpDict['GoQueries'] = [dict(qry) for qry in self.GoQrys if qry._isUsed]
        # - Update User/Date immer aktualisieren, wenn das Objekt gespeichert wird
        dmpDict['updUser'] = os.getlogin()
        dmpDict['updDate'] = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
        # - Insert User/Date nur aktualisieren, wenn sie nicht gesetzt sind/nicht geladen wurden
        dmpDict.setdefault('insUser', dmpDict['updUser'])
        dmpDict.setdefault('insDate', dmpDict['updDate'])
        # GoDatabase speichern...
        dmpThis = {self.__class__.__name__: dmpDict}
        dmpText = json.dumps(dmpThis, indent=4).encode("utf-8")
        self.log.debug("%s", dmpText)
        self._DDX.update(self.dumpFilename(), dmpText)
        # DumpDict vom Objekt nach erfolgreichen Speichern aktualisieren
        self._DumpDict = dmpDict
        # isDirty-Flag zurücksetzen
        # 06/2023 j.ebert, self.isDirty() derzeit immer True!!!
        self._isDirty = False
        # GoDatabase Folder erstellen, wenn er noch nicht existiert
        self._mkdata()
        return

    def open(
        self,
        usr="",
        pwd=""
    ):
        """opens gDB

        13.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        try:
            # Attr _isOpened zurücksetzen
            self._isOpened = False
            # 07/2023 j.ebert, Achtung
            #   Zuerst Direktverbindung der gDB öffnen und danach in GeODin, damit
            #   ggf. Nutzer und Passwort abgefragt werden können.
            #   (Andersrum müssen Nutzer und Passwort ggf. zwei mal eingegeben werden.)
            # erster Schritt: Direktverbindung der Datenbank öffnen
##            gxCnn = gx.gApp.connect(self, usr, pwd)
            self._GxCnn.connect(usr, pwd)
            # zweiter Schritt: Datenbank in GeODin öffnen
            gx.gApp.selectObject(self, expand=True)
            # GeODin Tabellen/Struktur laden...
            self.reload()
            # Attr _isOpened setzen
            self._isOpened = True
            self.log.debug(
                "%s database '%s' could be opened successfully" , self.DriverID, self.Name
            )
        except gqb.GxException as exc:
            self.log.debug(exc.msg(), exc_info=True)
            raise
        except:
            self.log.critical(
                "Major disaster opening %s database '%s'",
                self.DriverID, self.Name,
                exc_info=True
            )
            raise gqb.GxException("Unknown error opening %s database!", self.DriverID)
        return

    def close(self):
        """closes gDB

        26.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")

    def reload(self):
        """loads the GeODin tables/structure

        26.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # GeODin-Tabellen/Structur zurücksetzen
        self.unload()
        # GeODin-Parameter laden
        # Registry-Settings der GeODin-DB neu laden (oder Default-Werte setzen)
        pass
        # Daten gDB laden...
        # Achtung
        #   Das Laden der GeODin-Tabellen SYS_PRJDEFS und GLQ_EXECUTE erfolgt nicht beim Öffnen
        #   der GeODin-DB, sondern beim Laden der Abfragen für ein Projekt oder die Datenbank.
        self._GT_LOCPRMGR = self._GxCnn.load_LOCPRMGR()
        self._GT_PRJDEFS = self._GxCnn.load_PRJDEFS()
        self._GT_GLQEXEC = None
        self._GT_LOCTYPES = self._GxCnn.load_LOCTYPES()
        # self._GT_LOCTABTY = None
        # 10/2026: tables of the object types (names of the measurement point types in GeoDin)
        try:
            self._GT_LOCTABTY = self._GxCnn.load_LOCTABTY()
        except Exception:
            self._GT_LOCTABTY = None
        self._GT_INVTYPES = self._GxCnn.load_INVTYPES()
        self._GT_ADCDATA = self._GxCnn.load_ADCDATA()
        # Daten aus DDX laden...
        pass
        # Aktualisierung auf Datenbank-Ebene...
        self.reload_GoDict()
        self.reload_GoPrjs()
        self.reload_GoQrys(self.DBPrjID)
        return

    def reload_GoDict(self):
        """loads GeODin dictionary

        02.08.2023 j.ebert
        """
        goLID = gx.gApp.reg_UserLId()
        goFile = Path(res.ResFolder) / ("geodin_dict_%02d.json" % goLID)
        self.log.info("Reload GoDictionary (UserLId %s)...\n\t%s", goLID, str(goFile))
        self._GoDict = res._loadDictionary(goFile)
        return

    def reload_GoPrjs(self):
        """
        24.04.2024 j.ebert
        """
        # Projekte aus der GeODin-DB laden/initialisieren
        # 07/2023 j.ebert, Anmerkung
        #   Zur Zeit ist die erste List-Comprehension sinnfrei, aber
        #   für GeODin-Datenbanken mit Projekten die mehr als 9999 Objekte/Lokationen haben können,
        #   müssen die "echten" Projekten identifiziert werden, entweder hier oder
        #   bereits breits bei der SQL-Abfrage von LOCPRMGR
##        idxFld_PRJ_ID = GoProject.idxSQLFld('PRJ_ID')
##        rows = [row for row in self._GT_LOCPRMGR if row[idxFld_PRJ_ID]]
        # 04/2024 j.ebert, Auswahl der Porjekte mit weniger als 10.000 Locationen ~~~~~~~~~~~~~~~~~~
        # - Index vom Feld mit der GEODINGUID ermitteln
        # - Frequency/Häufigkeit der GEODINGUIDs ermitteln
        #   Achtung, folgedende Datensätze werden ignoriert
        #     bool(row[idxFld_UID])     -> GEODINGUID nicht gesetzt (None oder leere Zeichenkette)
        #     row[idxFld_UID].strip()   -> GEODINGUID enthält nur Leerzeichen
        # - Zeilen ermitteln, deren GEODINGUID nicht mehrfach enthalten ist
        #   Achtung, hier wieder die Ausnahmen wie oben, also inklusive(!) der Zeilen
        #     deren GEODINGUID nicht im Dict frqUID enthalten sind
        # - Error-Logging, wenn GEODINGUIDs mehrfach enhalten sind
        idxFld_UID = GoProject.idxSQLFld('GEODINGUID')
        frqUID = Counter(
            row[idxFld_UID] for row in self._GT_LOCPRMGR if (
                bool(row[idxFld_UID]) and row[idxFld_UID].strip()
            )
        )
        rows = [row for row in self._GT_LOCPRMGR if (frqUID.get(row[idxFld_UID], 0) < 2)]
        errUIDs = [ key for  key, val in frqUID.items() if val > 1]
        if errUIDs:
            self.log.error(
                "Projects with more than 9,999 locations are not yet supported! \n\t%s : %s",
                'GEODINGUID',
                json.dumps(errUIDs, indent=4).replace("\n", "\n\t")
            )
        # 04/2024 j.ebert ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        newPrjs = [GoProject.fromSQL(self, row) for row in rows]
        # Projekte der GoDatabase aktualisieren/überladen
        # - Projekte in der GoDatabase identifizieren
        #   Nur Projekte mit genutzt(!!!) Abfragen, alle anderen ignorieren
        usedPrjIDs = set([qry.PrjID for qry in self.GoQrys if qry._isUsed])
        self._GoPrjs = [prj for prj in self._GoPrjs if prj._PrjID in usedPrjIDs]
        if self.log.level <= logging.DEBUG:
            logRows = [str(row) for row in self._GoPrjs]
            self.log.debug(
                "Projekte mit genutzte Abfragen: \n\t%s",
                json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
        # - Projekte aktualisieren/überladen
        for usedPrj in self._GoPrjs:
            tmpPrjs = [prj for prj in newPrjs if usedPrj == prj]
            if not tmpPrjs:
                # Wenn kein 'neues' Projekt gefunden wurde,
                # dann exitistiert das Projekt nicht mehr in der GeODin-DB
                usedPrj._error = "No longer in GeoDin database"
            else:
                # Wenn eine 'neues' Projekt gefunden wurde,
                # dann Projekt mit dem 'neuen' Projekt überladen
                usedPrj.overload(tmpPrjs[0])
                newPrjs.remove(tmpPrjs[0])
        # - restliche neue Projekte hinzufügen,
        self._GoPrjs += newPrjs
        if self.log.level <= logging.DEBUG:
            logRows = [str(prj) for prj in self._GoPrjs]
            self.log.debug(
                "GoPrjs/list(GoProject): \n\t%s",
                json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
        return

    def reload_GoQrys(
        self,
        prjID
    ):
        """load queries

        31.07.2023
        """
        self.log.log(gqc._LOG_TRACE,"Database '%s' (PrjID '%s')...", self.Name, prjID)
        newQrys = []
        # Abfragen der Objektarten laden/initialisieren...
        lstTypes = self._GxCnn.load_ExistingLOCTYPES(prjID)
        # 10/2026: number of objects per object type (None if not available)
        locCounts = self._GxCnn.load_LOCTYPECounts(prjID)
        if self.log.level <= logging.DEBUG:
            logRows = [str(row) for row in self._GT_LOCTYPES]
            self.log.debug(
                "GT_LOCTYPES (PrjID %s): \n\t%s",
                prjID, json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
        for prm in [row for row in self._GT_LOCTYPES if row[0] in lstTypes]:
            newQrys.append(GoQuery.from_TypLOC(self, prjID, prm))
            if locCounts is not None:
                newQrys[-1]._Count = locCounts.get(prm[0], 0)
        if lstTypes:
            # Wenn die Liste der Objektarten nicht leer ist,
            # dann Abfrage 'Alle Objekte' hinzufügen...
            newQrys.insert(0, GoQuery.from_TypALL(self, prjID))
            if locCounts is not None:
                newQrys[0]._Count = sum(locCounts.values())
        # Abfragen der Messpunktarten laden/initialisieren...
        # 10/2026: number of measurement points per type, the keys are the existing INV_TYPES
        #   (same query as load_ExistingINVTYPES(), so no additional database access)
        # lstTypes = self._GxCnn.load_ExistingINVTYPES(prjID)
        invCounts = self._GxCnn.load_ExistingINVTYPECounts(prjID)
        lstTypes = list(invCounts)
        if self.log.level <= logging.DEBUG:
            logRows = [str(row) for row in self._GT_INVTYPES]
            self.log.debug(
                "GT_INVTYPES (PrjID %s): \n\t%s",
                prjID, json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
        for prm in [row for row in self._GT_INVTYPES if row[0] in lstTypes]:
            newQrys.append(GoQuery.from_TypINV(self, prjID, prm))
            newQrys[-1]._Count = invCounts.get(prm[0], 0)
        # GeODin-Abfragen laden/initialisieren...
        if self.log.level <= logging.DEBUG:
            logRows = [str(row) for row in self._GT_PRJDEFS]
            self.log.debug(
                "GT_PRJDEFS (PrjID %s): \n\t%s",
                prjID, json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
        for prm in [row for row in self._GT_PRJDEFS if row[0] == prjID]:
            newQrys.append(GoQuery.from_PrjDEF(self, prjID, prm))
        # 11/2026: GeoDin system queries (*.GSQ)
        #   GeoDin setting "Query beneath the object type" (gx/sysquery.py LEVELS):
        #   project queries -> under every project, database queries -> under the database;
        #   database, project, object, measurement point can't be selected with SelectObject
        #   (GIX-10364) and are not offered; unknown level -> project queries
        from GeODinQGIS.gx import sysquery
        wanted = (
            sysquery.LEVEL_DATABASE_QUERIES if prjID == self.DBPrjID
            else sysquery.LEVEL_PROJECT_QUERIES
        )
        try:
            sysQrys = gx.gApp.systemQueries()
        except Exception:
            self.log.error("System queries not available", exc_info=True)
            sysQrys = []
        names = set(qry.Name for qry in newQrys if qry.Kind in ('GxQryLOC', 'GxQryINV'))
        for prm in sysQrys:
            level = prm.get('Level')
            if level is None:
                level = sysquery.LEVEL_PROJECT_QUERIES
            if level != wanted:
                continue
            if prm['Name'] in names:
                # a GeoDin query of the project with the same name is preferred
                continue
            names.add(prm['Name'])
            newQrys.append(GoQuery.from_SysQRY(self, prjID, prm))
        # Abfragen der akt. PrjID aktualisieren/überladen....
        if self.log.level <= logging.DEBUG:
            logRows = [str(row) for row in newQrys]
            self.log.debug(
                "'neue' Abfragen (PrjID '%s'): \n\t%s",
                prjID, json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
        # Abfragen der GoDatabase aktualsieren/überladen
        # - Abfragen mit akt. PrjID in der GoDatabase identifizieren
        #   Nur genutzt(!!!) Abfrage mit der akt. PrjID, alle anderen ignorieren
        prjQrys = [qry for qry in self._GoQrys if (qry.PrjID == prjID) and qry._isUsed]
        if self.log.level <= logging.DEBUG:
            logRows = [str(row) for row in prjQrys]
            self.log.debug(
                "vorhandene/genutzte Abfragen (PrjID '%s'): \n\t%s",
                prjID, json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
        # - Abfragen mit akt. PrjID aktualisieren/überladen
        for prjQry in prjQrys:
            tmpQrys = [qry for qry in newQrys if prjQry == qry]
            if not tmpQrys:
                # Wenn keine 'neue' Abfrage gefunden wurde,
                # dann exitistiert die Abfrage nicht mehr in der GeODin-DB
                prjQry._error = "No longer in GeoDin database"
            else:
                # Wenn eine 'neue' Abfrage gefunden wurde,
                # dann Abfrage mit der 'neue' Abfrage überladen
                prjQry.overload(tmpQrys[0])
                newQrys.remove(tmpQrys[0])
        # - restliche neue Abfragen hinzufügen,
        # - Abfragen mit akt. PrjID ergänzen mit den'neuen' Abfragen, die noch nicht existieren
        prjQrys += newQrys
        # - Abfragen der GoDatabase  aktualisieren/überladen
        #   08/2023 j.ebert, Achtung
        #       Hier alle Abfragen mit der akt. PrjID entfernen/löschen, auch wenn
        #       oben zuerst nur die genutzten Abfragen identifiziert wurden.
        self._GoQrys = [qry for qry in self._GoQrys if qry.PrjID != prjID] + prjQrys
        if self.log.level <= logging.DEBUG:
            logRows = [str(qry) for qry in self._GoQrys if qry.PrjID == prjID]
            self.log.debug(
                "GoQrys/list(GoQuery) (PrjID '%s'): \n\t%s",
                prjID, json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
        return

    def uniqueQryDesc(
        self,
        prjID,
        qryKind
    ):
        """returns a key/QryDesc to build unique query ID <DbDesc>_<PrjID>_<QryKind>_<QryDesc>

        21.02.2024 j.ebert, Bug fixing
        """
        newKey = ""
        # Keys ermitteln die bereits existieren...
        #   Suche innerhalb der Datenbank auf Projekt und Abfrage-Art einschränken
        #   Nicht gesetzte Keys (Attr _Desc) ignorieren
        qryKeys = [
            qry._Desc for qry in self._GoQrys if (
                (qry.PrjID == prjID) and (qry.Kind == qryKind) and bool(qry._Desc))
        ]
        # Key setzen und prüfen, ob dieser ggf. bereits existiert
        # 08/2023 j.ebert, Anmerkung
        #   Key ist NICHT(!) case-sensitive, da die UID der Abfrage (inkl. des Keys)
        #   als Filename für die DataSource der Abfage genutzt wird (OS Windows).
        while (not newKey) or (newKey in qryKeys):
            newKey = ''.join(random.sample(string.ascii_uppercase + string.digits, 8))
        return newKey

    @classmethod
    def prefix(cls):
        return cls._Prefix

    def presentGoQrys(
        self,
        prjID=None,             # GeODin PrjID
        qryGrp=None             # GoQuery group ('INV', 'LOC')
    ):
        """returns GoQuery list

        07.08.2023 j.ebert
        """
        self.log.log(
            gqc._LOG_TRACE,
            "GoQrys/list(GoQuery) (%s, %s, %s)...", self.Desc, str(prjID), str(qryGrp)
        )
        # Arg qryGrp prüfen und definiert setzen 'INV', 'LOC' oder ''
        qryGrp = {'INV': 'INV', 'LOC': 'LOC'}.get(str(qryGrp).upper(), '')
        qrys =[]
        if bool(prjID) and bool(qryGrp):
            self.log.debug("GoQrys/list(GoQuery) (%s, %s, %s)...", self.Desc, prjID, qryGrp)
            qrys = [qry for qry in self.GoQrys if (
                (qry.PrjID == prjID) and (qry.Kind[-3:] == qryGrp) and qry.isPresent()
            )]
        if bool(prjID):
            self.log.debug("GoQrys/list(GoQuery) (%s, %s)...", self.Desc, prjID)
            qrys = [qry for qry in self.GoQrys if (qry.PrjID == prjID) and qry.isPresent()]
        else:
            self.log.debug("GoQrys/list(GoQuery) (%s)...", self.Desc)
            qrys = [qry for qry in self.GoQrys if qry.isPresent()]
        if self.log.level <= logging.DEBUG:
            logRows = [str(qry) for qry in qrys]
            self.log.debug(
                "GoQrys/list(GoQuery) (%s, %s, %s): \n\t%s",
                self.Desc, prjID, qryGrp, json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
        return qrys

    def unload(self):
        """unloads/resets the GeODin tables/structure

        26.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # Daten zurücksetzen
        self._GT_ADCDATA = None
        self._GT_INVTYPES = None
        self._GT_LOCTABTY = None
        self._GT_LOCTYPES = None
        self._GT_GLQEXEC = None
        self._GT_PRJDEFS = None
        self._GT_LOCPRMGR = []

    def overload(
        self,
        ddx,                    # current DDX
        gDB                     # GoDatabase from GeODin configuration
    ):
        """set DDX referenz and overloads settings/configuration form gDB

        05.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        self._DDX = ddx
        if id(self) != id(gDB):
            # Wenn die GoDatabase Objekte identisch sind,
            # dann muss nicht überladen werden bzw.
            # dann bringt das Überladen nichts
            # 06/2023 j.ebert, Anmerkung
            #   Die GoDatabase Objekte sind identisch, wenn die DB noch nicht im DDX enthalten ist.
            #   Die DB aus der GeODin-Konfiguration wird dem DDX hinzugefügt und
            #   würde hier mit sich selbst überladen.
            self.log.debug("overload %s '%s'", self.__class__.__name__, self.Name)
            self._Settings = gDB._Settings
            self._GxCnn = gDB._GxCnn
            self._CnnPrps = gDB._GxCnn._CnnPrps
##            self._CnnPrps = gDB._CnnPrps

    def remove(self):
        """removes GeODin Database from DDX

        31.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        try:
            # GoDatabase aus DDX löschen
            self._DDX.update(self.dumpFilename())
            # GoDatabase Objekt zurücksetzen
            self._isPresent = False
            # GoDatabase-Folder im DDX-Folder löschen...
            if self.DataPath.exists():
                # 07/2024 j.ebert, Anmerkung
                #   Löschen des GoDatabase-Folder kann ggf. eine Exception auslösen, wenn
                #   GeoJSON-Files noch "in anderen Prozessen" verwendet werden.
                try:
                    # Achtung,
                    #   Die Funktion shutil.rmtree() löscht den Ordner samt
                    #   allen darin enthalten Dateien und Ordnern!!!
                    shutil.rmtree(self.DataPath)
                except:
                    self.log.error(
                    "GoDatabase-Folder '%s' is orphaned but could not be removed\n\t%s",
                    self.dumpFilename(), str(self.DataPath),
                    exc_info=True
                    )
        except:
            self.log.critical(
            "GoDatabase '%s' could not be completely removed\n\t%s\n\t%s",
            self.Name, str(self.DataPath), str(Path(self._DDX.File) / self.dumpFilename()),
            exc_info=True
            )
            raise gqb.GxDDXException("Database '%s' could not be removed", self.Name)
        return

    def geodin(self):
        """select GeODin Database in GOM

        31.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        return

    def prmsSelectObject(
        self,
        mode='COM'
    ):
        """ returns parameters to select item in GeODin application

        args:
            mode                - GeODin API (COM, SQL, ...)

        returns:
            prms (dict)         {<key/paramter name>: <val/parameter value>}
        01.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "Not overloaded in class %s", self.__class__.__name__)
        prms = {
            'Database': self.Name,
            'UserName': self._CnnPrps.get('user_name', ""),
            'Password': self._CnnPrps.get('password', ""),
            'ObjectType': "0",
            'ParentNode': "Database",
            'Query': "",
            'ObjectID': "",
            'Expand': "false",
        }
        #zum testen
##        prms['UserName'] = 'Scott'
        if (
            (self._CnnPrps.get('dirverid', "") == 'MSACC') and
            (prms['UserName' == ""])
        ):
            (prms['UserName' == " "])
            (prms['Password' == " "])
        return prms

    @classmethod
    def from_TGClass(
        cls,
        settings                # GeODin configuration (TGClass_DatabaseSettingsList)
    ):
        """creates GoDatabase object from GeODin configuration (TGClass_DatabaseSettingsList)

        args:
            settings            - GeODin configuration (TGClass_DatabaseSettingsList)

        returns:
            obj (GoDatabase)

        01.06.2023 j.ebert
        """
        gDB = cls()
        gDB.log.log(gqc._LOG_TRACE, gDB.Name)
        gDB._Settings = settings
##        gDB._CnnPrps = gx.gApp.validateCnnPrps(gDB._Settings)
        gDB._GxCnn = gx.gApp.dbConnection(gDB)
        gDB._CnnPrps = gDB._GxCnn._CnnPrps
        gDB._Name = gDB._Settings.get('DisplayName', gDB._Name)
        return gDB

    @classmethod
    def from_json(
        cls,
        json_dct,               # JSON object (dict)
        ddx=None                # reference to DDX
        ):
        """creates GoDatabase object from JSON-Object (dict)

        args:
            json_dct (dict)     - JSON object (dict)
                                  {'GoDatabase': {}}
            ddx                 - reference to DDX

        20.01.2023 j.ebert
        """
        assert isinstance(json_dct, dict), \
            f"arg 'json_dct': type 'dict' expected, but '{type(json_dct).__name__}' received"
        dmpDict = json_dct[cls.__name__]
        # Objekt erstellen
        obj = cls()
        obj._DDX = ddx
        obj._Name = dmpDict.get('Name')
        obj._Desc = dmpDict.get('Desc')
        obj.log.log(gqc._LOG_TRACE, obj.Name)
        # GoProjects und GoQueries laden...
        obj._GoPrjs = [GoProject.from_json(item, obj) for item in dmpDict.get('GoProjects', [])]
        obj._GoQrys = [GoQuery.from_json(item, obj) for item in dmpDict.get('GoQueries', [])]
        if obj.log.level <= logging.DEBUG:
            logRows = [str(row) for row in obj._GoPrjs]
            obj.log.debug(
                "GoProjects: \n\t%s", json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
            logRows = [str(row) for row in obj._GoQrys]
            obj.log.debug(
                "GoQueries: \n\t%s", json.dumps(logRows, indent=4).replace("\n", "\n\t")
            )
##        obj._Data = json_dct.get('DDX-Data', obj._Data)
##        obj._Conf = json_dct.get('DDX-Conf', obj._Conf)
##        obj.Data = obj._abspath(json_dct.get('Data', obj.Data))
##        obj.Conf = obj._abspath(json_dct.get('Conf', obj.Conf))
##        obj.SaveRelPaths = json_dct.get('SaveRelPaths', obj.SaveRelPaths)
        obj._DumpDict = dmpDict
        return obj

    def _mkdata(self):
        """ creates the GeDatabase folder

        returns:
            True|False          True if the GoDatabase folder exists when the function exits

        06.06.2023 j.ebert
        """
        dataPath = self.DataPath
        if not dataPath.exists():
            try:
                # 06/2023 j.ebert, Anmerkung
                #   Parent-Directory ist der Data-Folder vom DDX muss also existieren.
                # GoDatabase Folder erstellen
                dataPath.mkdir(exist_ok=True)
                with open(dataPath / (self.Name + '.con'), 'w') as conFile:
                    pass
            except:
                self.log.error(
                    "Failed to create GoDatabase folder '%s'", self.DataPath, exc_info=True
                )
        return dataPath.exists()

    def __iter__(self):
        yield from {
            'PrjID': self._PrjID,
            'Name': self.Name,
            'CRef': self.CRef,
            'Desc': self.Desc,
            'UID': self.UID
        }.items()



def main():
    pass

if __name__ == '__main__':
    main()
