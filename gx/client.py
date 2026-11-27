"""
Classes:
    GxBaseClient                - blueprint/abtsract class of GeODin client class
    GxBaseCOMClient             - abtsract class of GeODin client useing GeODin COM interface
    GxCOMClient                 - GeODin client useing GeODin COM interface (and SQL access)

09.03.2023 j.ebert
"""
import json
import logging
import os
import re

from .geodin import *
from .gxdbcnn import (
    GxDbConnection
)
import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gqgis_config as gqc
from GeODinQGIS import res


class GxBaseClient:
    """Base classes with the declaration of the client methods

    07.03.2023 j.ebert
    """

    def __init__(self):
        self.log = logging.getLogger(f"{gqc._LOG_PARENTS}{self.__class__.__name__}")
        self._context = "gx"    # Context für Transaltion/Übersetzung vom Modul gx
        self._AppFolder = ""
        """Applicationfolder (directory where a geodin.ini is stored)"""

        self._gSYS = GxSys()
        """GeODin System (Singleton!)"""

    @property
    def AppFolder(self):
        """Applicationfolder (directory where a geodin.ini is stored)

        08.03.2023 j.ebert
        """
        return self._AppFolder

    def is_installed(self):
        """True, if GeODin 64 Bit is installed

        07.03.2023 j.ebert
        """
        raise NotImplementedError(f"{self.__class__.__name__}.is_installed not implemented")

    def is_running(self):
        """True, if GeODin application (geodin.exe) is running

        09.03.2023 j.ebert
        """
        return self._gSYS.is_running()

    def databases(self):
        """returns GeODin DatabaseSettingsList

        30.05.2023 j.ebert
        """
        raise NotImplementedError(f"{self.__class__.__name__}.databases not implemented")


    def reg_UserLId(self):
        """GeODin System RegKey 'UserLId' (REG_DWORD)
        02.08.2023 j.ebert
        """
        return GxReg.query_UserLId()

class GxBaseCOMClient(GxBaseClient):
    """Base class that implements the GeODin COM interface

    06.03.2023 j.ebert
    """

    def __init__(self):
        super().__init__()
        self._gApp = GxCOM()
        """GeODin COM Interface (Singleton!)"""

    @property
    def AppFolder(self):
        """Applicationfolder (directory where a geodin.ini is stored)

        23.05.2023 j.ebert
        """
        return self._gApp.AppFolder

    @classmethod
    def info(cls):
        """About...

        09.03.2023 J.Ebert
        """
        return GxCOM.info()

    def is_installed(self):
        """True, if GeODin application (geodin.exe) is installed/registered

        09.03.2023 j.ebert
        """
        return self._gApp.is_installed()


class GxCOMClient(GxBaseCOMClient):
    """GeODin client with SQL access (Singleton!)

    06.03.2023 j.ebert
    """
##    log = logging.getLogger(f"{_log_parents}GxSQLInterface")

    def __new__(cls):
        if not hasattr(cls, 'instance'):
##            cls.instance = cls.__init__(cls)
            cls.instance = super(GxCOMClient, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        super().__init__()

    def databases(self):
        """returns GeODin DatabaseSettingsList

        exceptions:
            GxGComException             if a GeODin COM function failed
            GxGComResError              if unexpected COM response

        30.05.2023 j.ebert
        """
        res = self._gApp._gCOM_Databases()
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
        try:
            obj = json.loads(res)
            lst = obj['TGClass_DatabaseSettingsList']
        except json.JSONDecodeError:
            self.log.error("Error on DatabaseSettingsList (%s)", "JSON", exc_info=True)
            raise gqb.GxGComResError("Error on DatabaseSettingsList (%s)", "JSON")
        except KeyError:
            self.log.error("Error on DatabaseSettingsList (%s)", "TGClass", exc_info=True)
            raise gqb.GxGComResError("Error on DatabaseSettingsList (%s)", "TGClass")
        else:
            # erforderlichen Parameter prüfen...
            errorOnRequiredPrms = False
            for idx, dbSettinngs in enumerate(lst):
                keys = dbSettinngs.keys()
                # 07/2023 j.ebert, Anmerkung
                #   Beim Testen mit MSSQL-Datenbanken war der Parameter 'Schema' nicht gesetzt.
                #   DB.Nutzer mit default Schema?!
##                for key in ["DisplayName", "ConnectionString", "Schema"]:
                for key in ["DisplayName", "ConnectionString"]:
                    if not (
                        # key muss im Dict dbSettinngs existieren
                        (key in keys) and
                        (
                            # key (bzw. dessen value) muss gesetzt
                            bool(dbSettinngs.get(key)) or
                            # außer es ist 'Schema' und 'ConnectionString' enthält "DriverID=MSAcc"
                            # (also für MS Access DB muss 'Schema' nicht gesetzt sein)
                            (
                                (key == 'Schema') and
                                ('DRIVERID=MSACC' in dbSettinngs.get('ConnectionString', "").upper())
                            )
                        )
                    ):
                        errorOnRequiredPrms = True
                        self.log.error(
                            "Error on DatabaseSettingsList: Idx %2d ('%s'), Prm '%s'",
                            idx, dbSettinngs.get("DisplayName",""), key
                        )
##            if errorOnRequiredPrms:
##                # Wenn ein Fehler bei den erforderlichen Paramtern gefunden wurde,
##                # dann mit Exception abbrechen...
##                raise gqb.GxGComResError("Error on DatabaseSettingsList (%s)", "Prms")
            # 11/2026 skip invalid database entries instead of aborting the whole list
            #   (one faulty connection in GeoDin, e.g. without ConnectionString, made it
            #   impossible to open any database in the plugin)
            self.skippedDatabases = []
            if errorOnRequiredPrms:
                valid = []
                for dbSettinngs in lst:
                    if dbSettinngs.get("DisplayName") and dbSettinngs.get("ConnectionString"):
                        valid.append(dbSettinngs)
                    else:
                        self.skippedDatabases.append(
                            dbSettinngs.get("DisplayName") or "<%s>" % ("no name")
                        )
                self.log.warning(
                    "DatabaseSettingsList: invalid entries skipped: %s", self.skippedDatabases
                )
                lst = valid
            # optionale Parameter...
            #   "AutoOpen"                -> default: False
            #   "HideLocationTypes"       -> default: False
            #   "HideEmptyLocationTypes"  -> ALWAYS:  True (False würde ggf. eine leere FCls ergeben?!)
            #   "HideMesPointTypes"       -> default: False
            #   "HideEmptyMesPointTypes"  -> ALWAYS:  True (False würde ggf. eine leere FCls ergeben?!)
            #   "GOMGroup":               -> default: ""
            #   "Schema":                 -> default: ""
        return lst

    @classmethod
    def dbConnection(
        cls,
        gDB                     # Referenz auf GoDatabase
    ):
        return GxDbConnection(gDB)

    @classmethod
    def info(cls):
        """About...

        09.03.2023 J.Ebert
        """
        return super().info() + GxSQL.info()

    def is_open(self):
        """True, if GeODin application (geodin.exe) is open/activated

        30.03.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        return self._gApp.is_open()

    def connect(
        self,
        gDB,                    # GoDatabase
        usr=None,               # database login user
        pwd=None                # database login password
    ):
        """creates a direct connection to the SQL database

        24.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "")
        return GxSQL.connect(gDB, usr, pwd)

    def systemQueries(self, reload=False):
        """returns the GeoDin system queries (*.GSQ in <ProgramData>\\QUERYDEF\\, 11/2026)

        returns:
            list of dict {'Name', 'Grp' (LOC|INV), 'File'} (see gx.sysquery), [] on error
        """
        if (not reload) and (getattr(self, '_SystemQueries', None) is not None):
            return self._SystemQueries
        from .sysquery import systemQueries
        res = []
        try:
            excVal, progData = self._gApp._gCOM_ProgramData()
            if (not excVal) and bool(progData):
                res = systemQueries(os.path.join(progData, "QUERYDEF"))
            else:
                self.log.error("Load ProgramDataFolder failed\n\tExcVal %s: '%s'", excVal, progData)
        except Exception:
            self.log.error("Load system queries failed", exc_info=True)
        self._SystemQueries = res
        return res

    def loadSYSALIAS(self):
        """loads SYSALIAS dictionary from GeODin configuration

        15.08.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        res = []
        try:
            excVal, progData = self._gApp._gCOM_ProgramData()
            if (not excVal) and bool(progData):
                res.append(['%GEODINROOT', progData])
            else:
                self.log.error("Load ProgramDataFolder failed\n\tExcVal %s: '%s'", excVal, progData)
        except Exception as exc:
            self.log.error("Load ProgramDataFolder failed", exc_info=True)
        return res

    def open(
        self,
        appFolder=""
    ):
        """opens GeODin Connection

        returns:
            hdl

        exceptions:
            ...

        12.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        self._SystemQueries = None   # 11/2026: reload system queries of this GeoDin
        return self._gApp.open(appFolder)

    def renew(self):
        self.log.log(gqc._LOG_TRACE,"")
        return self._gApp.renew()

    def reset(self):
        self.log.log(gqc._LOG_TRACE,"")
        return self._gApp.reset()

    def createObjectSelection(
        self,
        goQry,
        objectIDs,
        refName="",
        methodID=-1,
        methodPrms=""
    ):
        try:
            #
            prms = goQry.prmsCreateObjectSelection()
            prms['ObjectIDs'] = "\n".join(objectIDs)
            if isinstance(refName, str) and bool(refName):
                prms['RefName'] = refName
            prms['MethodID'] = methodID
            prms['MethodParams'] = methodPrms
            res = self._gApp._gCOM_CreateObjectSelection(prms)
        except gqb.GxException:
            raise
        except Exception:
            self.log.critical("Major disaster...", exc_info=True)
            raise
        return

    def createObjectSelection_v01(
        self,
        dbRef,
        objectIDs,
        objectType=None,
        refName="",
        methodID=-1,
        methodPrms=""
    ):
        try:
            #
            prms = dbRef.prmsSelectObject()
            prms.pop('ParentNode', None)
            prms.pop('Query', None)
            prms.pop('ObjectID', None)
            prms.pop('Expand', None)
            prms['ObjectIDs'] = "\n".join(objectIDs)
            # Prm ObjectType validieren...
            if (isinstance(objectType, int) and (objectType in (0, 1))):
                prms['ObjectType'] = objectType
            else:
                # 08/2023 j.ebert, quick and dirty
                #   FIDs analysieren, ob aus LOCREG und nur dann ObjectType 0 setzen
                prms['ObjectType'] = 1
            prms['RefName'] = refName
            if not prms['RefName']:
                prms['RefName'] = "Gx%s_%s" % (
                    'LOC' if prms['ObjectType'] == 0 else 'INV',
                    datetime.datetime.now().strftime("%H%M%S")
                )
            prms['MethodID'] = methodID
            prms['MethodParams'] = methodPrms
            res = self._gApp._gCOM_CreateObjectSelection(prms)
        except gqb.GxException:
            raise
        except Exception:
            self.log.critical("Major disaster...", exc_info=True)
            raise
        return

    # 10/2026: GeoDin method 'edit object data' (base editor) and its EditType
    METHOD_EDIT_OBJECT_DATA = 1
    EDIT_TYPE_OBJECT_DATA = 1

    def editObjectData(self, editType=EDIT_TYPE_OBJECT_DATA):
        """opens the object data (base editor) of the selected object in GeoDin

        10/2026
        """
        self.log.log(gqc._LOG_TRACE,"")
        try:
            self._gApp._gCOM_ExecuteMethodParams(
                self.METHOD_EDIT_OBJECT_DATA, f"EditType={editType}"
            )
        except gqb.GxException:
            raise
        except Exception:
            self.log.critical("Major disaster...", exc_info=True)
            raise
        return

    METHOD_GRAPHIC = 2

    def executeMethod(self, methodID, prms=""):
        """executes a GeoDin method at the selected GOM node (see GEODIN_COM.md)

        10/2026
        """
        self.log.log(gqc._LOG_TRACE,"")
        try:
            self._gApp._gCOM_ExecuteMethodParams(methodID, prms)
        except gqb.GxException:
            raise
        except Exception:
            self.log.critical("Major disaster...", exc_info=True)
            raise
        return

    def showGraphic(self):
        """opens the graphic window ('Print and edit graphics') of the selected object in GeoDin

        10/2026
        """
        self.log.log(gqc._LOG_TRACE,"")
        try:
            self._gApp._gCOM_ExecuteMethodParams(self.METHOD_GRAPHIC, "")
        except gqb.GxException:
            raise
        except Exception:
            self.log.critical("Major disaster...", exc_info=True)
            raise
        return

    def exportFeatureCollection(
        self,
        filename
    ):
        self.log.log(gqc._LOG_TRACE,"")
        try:
            res = self._gApp._gCOM_exportFeatureCollection(filename)
        except gqb.GxException:
            raise
        except Exception:
            self.log.critical("Major disaster...", exc_info=True)
            raise
        return

    def selectObject(
        self,
        item,
        expand=None
    ):
        self.log.log(gqc._LOG_TRACE,"")
        try:
            prms = item
            if not isinstance(prms, dict):
                prms = item.prmsSelectObject()
            if isinstance(expand, bool):
                prms['Expand'] = str(expand).lower()
            # prms = '[Params]\n%s' % "\n".join(["%s=%s" % (key, val) for key, val in prms.items()])
            # res = self._gApp._gCOM_SelectObject(prms)
            # 10/2026: names from the database may contain several spaces in a row (e.g.
            #   'samples  (geot. borehole)'), the GeoDin object manager shows them with one
            #   space -> 'not found'; then select again with the normalized name
            # 10/2026: alternative names of the query in the GeoDin object manager
            #   (GoQuery.gomLabelCandidates), keys with '_' are not passed to GeoDin
            prms = dict(prms)
            candidates = list(prms.pop('_QueryCandidates', None) or [])
            goQry = prms.pop('_GoQuery', None)
            query = str(prms.get('Query', "") or "")
            if query:
                normalized = " ".join(query.split())
                if normalized not in candidates:
                    candidates.append(normalized)
            if goQry is not None and getattr(goQry, '_GOMLabel', None):
                prms['Query'] = goQry._GOMLabel
            txt = '[Params]\n%s' % "\n".join(["%s=%s" % (key, val) for key, val in prms.items()])
            try:
                res = self._gApp._gCOM_SelectObject(txt)
            except gqb.GxGComException as firstExc:
                if not query:
                    raise
                res = None
                for name in candidates:
                    if name == prms.get('Query'):
                        continue
                    self.log.info("Query '%s' not found, select again as '%s'", prms.get('Query'), name)
                    tryPrms = dict(prms, Query=name)
                    txt = '[Params]\n%s' % "\n".join(["%s=%s" % (key, val) for key, val in tryPrms.items()])
                    try:
                        res = self._gApp._gCOM_SelectObject(txt)
                    except gqb.GxGAppBusyError:
                        raise
                    except gqb.GxGComException:
                        continue
                    if goQry is not None:
                        goQry._GOMLabel = name
                    self.log.info("Query '%s' selected as '%s' in GeoDin", query, name)
                    break
                else:
                    raise firstExc
        except gqb.GxException:
            raise
        except Exception:
            self.log.critical("Major disaster...", exc_info=True)
            raise
        return

    def validateCnnPrps(
        self,
        settings                # GeODin configuration (TGClass_DatabaseSettingsList)
    ):
        """validates GeODin configuration (from TGClass_DatabaseSettingsList)

        31.08.2023 j.ebert
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
            prps['schema'] = settings.get('Schema', '')
            # GeODin ConnectionString analysieren/splitten....
            pattern = re.compile(r'''
                ([\w]+)     # group 1/key - Zeichen von a-z, A-Z oder 0-9 oder Unterstrich
                =           # Trennung zwischen group 1/key und group 2/val
                ([^;]+)     # group 2/val - alle Zeichen außer Semikolon
            ''', re.IGNORECASE | re.VERBOSE)
            for match in re.finditer(pattern, prps['connectionstring']):
                # 08/2023 j.ebert, führende und abschließende Leerzeichen beim Prm-Wert entfernen!?
                prps[match.group(1).lower()] = match.group(2).strip()
            # 10/2026: an invalid connection string (e.g. without DriverID) must not abort
            #   the GeoDin connection -> only this database is marked as invalid
            prps['driverid'] = prps.get('driverid', '').upper()
            self.log.debug(json.dumps(prps, indent=4).replace('\n','\n\t'))
            if not prps['driverid']:
                prps['error'] = gqb.res.translate(
                    self._context,
                    "Invalid connection string (DriverID missing)"
                )
                self.log.warning(
                    "Database '%s': invalid connection string (DriverID missing)",
                    settings.get('DisplayName', '')
                )
                return prps
            # Parameter für Plugin Connection validieren...
            # - Default ErrorMessage setzen...
            #   Default: Datenbank vom Typ (bzw. mit FireDAC-DirverID) wird nicht unterstützt
            prps['error'] = gqb.res.translate(
                self._context,
                "%s-Databases not supported"
            ) % prps['driverid']
            # - Methode zur Validierung der ConnectionProperties für die akt. FireDAC-DirverID
            #   ermitteln und ausführen, wenn sie existiert
            func4DriverID = getattr(GxSQL, "_validateCnnPrps4%s" % prps['driverid'], None)
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


def main():
    return

if __name__ == '__main__':
    main()
