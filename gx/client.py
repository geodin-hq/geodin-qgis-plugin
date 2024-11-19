"""
Classes:
    GxBaseClient                - blueprint/abtsract class of GeODin client class
    GxBaseCOMClient             - abtsract class of GeODin client useing GeODin COM interface
    GxCOMClient                 - GeODin client useing GeODin COM interface (and SQL access)

09.03.2023 j.ebert
"""
import json
import logging
import random
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
            if errorOnRequiredPrms:
                # Wenn ein Fehler bei den erforderlichen Paramtern gefunden wurde,
                # dann mit Exception abbrechen...
                raise gqb.GxGComResError("Error on DatabaseSettingsList (%s)", "Prms")
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
            prms = '[Params]\n%s' % "\n".join(["%s=%s" % (key, val) for key, val in prms.items()])
            res = self._gApp._gCOM_SelectObject(prms)
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
            prps['schema'] = settings['Schema']
            # GeODin ConnectionString analysieren/splitten....
            pattern = re.compile(r'''
                ([\w]+)     # group 1/key - Zeichen von a-z, A-Z oder 0-9 oder Unterstrich
                =           # Trennung zwischen group 1/key und group 2/val
                ([^;]+)     # group 2/val - alle Zeichen außer Semikolon
            ''', re.IGNORECASE | re.VERBOSE)
            for match in re.finditer(pattern, prps['connectionstring']):
                # 08/2023 j.ebert, führende und abschließende Leerzeichen beim Prm-Wert entfernen!?
                prps[match.group(1).lower()] = match.group(2).strip()
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
