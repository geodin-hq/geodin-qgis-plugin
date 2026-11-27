"""
Classes:
    GxDDX                 - Data Dictionary

Functions:
    default()

05.07.2023 j.ebert
"""
import os
import datetime
import hashlib
import json
import logging
import tempfile
import traceback
import time
import zipfile
from pathlib import Path

import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gqgis_config as gqc
from GeODinQGIS.dm.database import GoDatabase as GxDB
from GeODinQGIS.dm.query import GoQuery as GxQry

_JSON_DUMP_IDENT = 4

def default(obj):
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

class GxDDX:
    """Data Dictionary

    17.04.2023 j.ebert
    """
    log  = logging.getLogger(f"{gqc._LOG_PARENTS}GxDxx")
    """Logger of this class"""
    _DumpFile = f"GxDDX.content".lower()
    """Dump file of this class stored in the data dictionary"""

    def __init__(
        self,
        ddxFile                 # DDX-File
        ):
##        self._DbRef = None
##        self._PrjID = 'GxDDX'
##        self._GxCls = self.__class__.__name__
##        self._Name = name
        self._File = ddxFile
        self._Data = ""
        self._Conf = ""
        self._Databases = []

        self._SaveRelPaths = True
        """Option to save relativ version of path to DDX-File directory"""
        self._DumpDict = {}
        """Dump dictionary, wich is updated by save() and open()"""
        self._isDirty = False
        if self._File:
            self._Data = str(Path(self._File).with_suffix(""))

    @property
    def File(self):
        """DDX file (*.gddx)

        17.04.2023 j.ebert
        """
        return self._File

    @File.setter
    def File(self, value):
        """DDX file (*.gddx)

        17.04.2023 j.ebert
        """
        self._File = value
        return

    @property
    def Data(self):
        """DDX data folder

        17.04.2023 j.ebert
        """
        return self._Data

    @Data.setter
    def Data(self, value):
        """DDX data folder

        17.04.2023 j.ebert
        """
        self._Data = value
        return

    @property
    def Conf(self):
        """GeODin configuration file (geodin.ini)

        17.04.2023 j.ebert
        """
        return self._Conf

    @Conf.setter
    def Conf(self, value):
        """GeODin configuration file (geodin.ini)

        17.04.2023 j.ebert
        """
        self._Conf = value
        return

    @property
    def AppFolder(self):
        """Applicationfolder (directory where a geodin.ini is stored)

        17.04.2023 j.ebert
        """
        val = None
        if self._Conf:
            val = str(Path(self._Conf).parent)
        return val

    @property
    def Databases(self):
        """GoDatabase list

        05.06.2023 j.ebert
        """
        return self._Databases

    @property
    def DBGroups(self):
        """DB group names (GOMGroups)

        05.06.2023 j.ebert
        """
        names = set()
        if self._Databases:
            names = set([gDB.GOMGroup for gDB in self._Databases if gDB.GOMGroup])
        return names


    @property
    def SaveRelPaths(self):
        """Option to save relativ version of path to DDX-File directory

        20.04.2023 j.ebert
        """
        return self._SaveRelPaths

    @SaveRelPaths.setter
    def SaveRelPaths(self, value):
        self._SaveRelPaths = bool(value)
        return

    @property
    def isNew(self):
        """True, if DDX has not been loaded and has not yet been saved

        29.04.2023 j.ebert
        """
        # Wenn DumpDict leer ist,
        # dann wurde das DDX neu erstellt,
        # also das DDX wurde nicht geladen und auch noch nicht gespeichert
        return not self._DumpDict

    @property
    def isDirty(self):
        """True, if the DDX needs to be saved

        29.04.2023 j.ebert
        """
        # True, wenn das DDX neu erstellt wurde, also
        #       wenn DDX nicht geladen und noch nicht gespeichert wurde
        value = self.isNew
        # Prüfen ob sich DDX Porperties geändert haben und gespeichert werden müssen,
        #   wenn bis jetzt noch nicht gespeichert werden muss, also
        #   wenn weder isDirty-Flag explizit gesetzt ist noch DDX neu erstellt wurde
        if not (self._isDirty or value):
            # 04/2023 j.ebert, Anmerkung
            # - dict vom DDX enthält realtive Pfade für Data und Conf, wenn die Option gestezt ist
            # - Porperty 'File' wird hier aktuell nicht geprüft
            #   wenn die relativen Pfade passen, muss das DDX nicht unbedingt gespeichert werden
            #   Motivation:  DDX wurde zentral im Netz gespeichert und
            #                es werden unterschiedliche Netzwerkverbindungen genutzt)
            curDict = dict(self)
            value = (
                (curDict.get('Data',"").lower() != self._DumpDict.get('Data',"").lower()) or
                (curDict.get('Conf',"").lower() != self._DumpDict.get('Conf',"").lower()) or
                (curDict.get('SaveRelPaths',True) != self._DumpDict.get('SaveRelPaths', True))
            )
        return self._isDirty or value

    @isDirty.setter
    def isDirty(self, value):
        self._isDirty = self._isDirty or bool(value)
        return

    def findByDataSource(
        self,
        dataSource              # GoQuery data source (str)
    ):
        """find GoDatabase by GoQuery dada source

        returns:
            prms (list)         - parameters/list
                                  [dbRef (GoDatabase), PrjID (str), QryKind (str), QryDesc (str)]

        11.08.2023 j.ebert
        """
        gxPrms = []
        try:
            srcPath = Path(dataSource)
            self.log.debug(
                "DDXData    %s\n\tdataSource %s\n\t\tIf-Expr (%s and %s and %s and %s and ???)",
                self.Data,
                dataSource,
                str(srcPath.parents[1].samefile(self.Data)),
                str(srcPath.parent.stem.startswith(GxDB._Prefix)),
                str(srcPath.stem.startswith(srcPath.parent.stem)),
                str(len(srcPath.parent.stem.split('_')) == 4)
            )
            if not (
                srcPath.parents[1].samefile(self.Data) and
                srcPath.parent.stem.startswith(GxDB._Prefix) and
                srcPath.stem.startswith(srcPath.parent.stem) and
                (len(srcPath.stem.split('_')) == 4) and
                (srcPath.stem.split('_')[2] in GxQry._Kinds)
            ):
                raise gqb.GxDDXException(
                    "Database not found\n\tWrong data source: '%s'", dataSource
                )
            dbRefs = [item for item in self.Databases if item._Desc == srcPath.parent.stem]
            if not dbRefs:
                raise gqb.GxDDXException(
                    "Database (Desc '%s') not defined\n\\Obsolete data source: '%s'",
                    srcPath.parent.stem, dataSource
                )
            dbRef = dbRefs[0]
            if not dbRef.isOpened():
                try:
                    dbRef.open()
                except:
                    self.log.debug("Failed to open database  '%s'", dbRef.Name, exc_info=True)
                    raise gqb.GxDDXException("Database '%s' not opened", dbRef.Name)
            gxPrms = srcPath.stem.split('_')
            if (
                (gxPrms[1] != GxDB.DBPrjID) and
                (gxPrms[1] not in [prj.PrjID for prj in dbRef.GoPrjs if not prj.isDisabled()])
            ):
                raise gqb.GxDDXException(
                    "Project ID '%s' not found in database '%s'", gxPrms[1], dbRef.Name
                )
            gxPrms[0] = dbRef
        except FileNotFoundError as exc:
            self.log.debug("Excepted FileNotFoundError: '%s'", exc.filename)
            raise gqb.GxDDXException("Database not found\n\tFile not found: '%s'", exc.filename)
        except gqb.GxDDXException:
            self.log.log(gqc._LOG_TRACE,"Reraise GxDDXException...", exc_info=True)
            raise
        except:
            self.log.critical("Major disaster...", exc_info=True)
            raise gqb.GxDDXException("Database not found by data source\n\t%s", dataSource)
        return gxPrms

    def findQueryByDataSource(
        self,
        dataSource              # GoQuery data source (str)
    ):
        """find GoDatabase by GoQuery dada source

        returns:
            prms (list)         - parameters/list
                                  [dbRef (GoDatabase), PrjID (str), QryKind (str), QryDesc (str)]

        11.08.2023 j.ebert
        """
        exc, qry = None, None
        srcPath = Path(dataSource)
        self.log.debug(
            "DDXData    %s\n\tdataSource %s\n\t\tIf-Expr (%s and %s and %s and %s and ???)",
            self.Data,
            dataSource,
            str(srcPath.parents[1].samefile(self.Data)),
            str(srcPath.parent.stem.startswith(GxDB._Prefix)),
            str(srcPath.stem.startswith(srcPath.parent.stem)),
            str(len(srcPath.parent.stem.split('_')) == 4)
        )
        if not (
            srcPath.parents[1].samefile(self.Data) and
            srcPath.parent.stem.startswith(GxDB._Prefix) and
            srcPath.stem.startswith(srcPath.parent.stem) and
            (len(srcPath.stem.split('_')) == 4) and
            (srcPath.stem.split('_')[2] in GxQry._Kinds)
        ):
            exc = gqb.GxDDXException(
                "Database not found\n\tWrong data source: '%s'", dataSource
            )
        else:
            dbRefs = [item for item in self.Databases if item._Desc == srcPath.parent.stem]
            if not dbRefs:
                exc = gqb.GxDDXException(
                    "Database (Desc '%s') not defined\n\\Obsolete data source: '%s'",
                    srcPath.parent.stem, dataSource
                )
            else:
                dbRef = dbRefs[0]
                if not dbRef.isOpened():
                    try:
                        dbRef.open()
                    except:
                        self.log.debug("Failed to open database  '%s'", dbRef.Name, exc_info=True)
                        exc = gqb.GxDDXException("Database '%s' not opened", dbRef.Name)
                if dbRef.isOpened():
                    qry = dbRef.findGoQryByUID(srcPath.stem)
                    if not qry:
                        exc = gqb.GxDDXException(
                            "Query UID '%s' not found in database '%s'", srcPath.stem, dbRef.Name
                        )
                    elif (
                        (qry.PrjID != GxDB.DBPrjID) and
                        (qry.PrjID not in [
                            prj.PrjID for prj in dbRef.GoPrjs if not prj.isDisabled()
                        ])
                    ):
                        exc = gqb.GxDDXException(
                            "Project ID '%s' not found in database '%s'", qry.PrjID, dbRef.Name
                        )
        return exc, qry

    def hasValidDbRef(
        self,
        dataSource              # GoQuery data source (str)
    ):
        """True if Path 'dataSource' has a valid GoDatabase folder and also reference

        25.07.2024 j.ebert
        """
        val = False
        try:
            srcPath = dataSource if isinstance(dataSource, Path) else Path(dataSource)
            val = (
                # DataSource muss im DDX-Data-Folder gespeichert sein
                #   <DDX data folder>\<GoDatabase folder name>\<File der DataSource>
                srcPath.parents[1].samefile(self.Data) and
                # GoDatabase-Foldername muss mit GoDatabase-Prefix beginnen
                srcPath.parent.stem.startswith(GxDB._Prefix) and
                # GoDatabase-Foldername muss der Descriptor einer GoDatabase im DDX sein
                # (Damit werden verwaiste GoDatabase-Folder ignoriert.)
                (srcPath.parent.stem in [item._Desc for item in self.Databases if item.isPresent])
            )
        except:
            self.log.critical("Valid DbRef from '%s' faild", str(dataSource), exc_info=True)
        return val

    def delete(
        self,
        filename=""
    ):
        """
        06.06.2023 j.ebert
        """
        self.log.warning(
            "Method '%s' is superseded by method '%s'\n\t%s",
            'delete()', 'update()', traceback.format_stack()[-2].strip()
        )
        with zipfile.ZipFile(self.File) as ddxZip:
            existsFilename = (
                bool(filename) and
                (filename.lower() in [item.filename.lower() for item in ddxZip.filelist])
            )
        if not existsFilename:
            self.log.debug("File '%s' not found", filename)
        else:
            ddxFile = self.File
            tmpPath = Path(self._tmpFilename(ddxFile))
            try:
                with zipfile.ZipFile(ddxFile, "r") as ddxZip, zipfile.ZipFile(tmpPath, "w") as tmpZip:
                    for item in ddxZip.infolist():
                        buffer = ddxZip.read(item.filename)
                        if (item.filename.lower() != filename.lower()):
                            tmpZip.writestr(item.filename, buffer)
                        else:
                            self.log.debug("File '%s' skipped", filename)
                Path(ddxFile).unlink()
                tmpPath.rename(ddxFile)
            except:
                self.log.critical(
                    "File '%s' could not be deleted\n\t%s\n", filename, self.File,
                    exc_info=True
                )
                if tmpPath.exists():
                    tmpPath.unlink()
                raise
        return

    def delete_v01(
        self,
        filename=""
    ):
        """
        06.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        with zipfile.ZipFile(self.File) as ddxZip:
            existsFilename = (
                bool(filename) and
                (filename.lower() in [item.filename.lower() for item in ddxZip.filelist])
            )
        if not existsFilename:
            self.log.debug("File '%s' not found", filename)
        else:
            ddxFile = self.File
            ddxPath = Path(ddxFile)
            bakFile = str(ddxPath.with_suffix('%s.bak' % ddxPath.suffix))
            ddxPath.rename(bakFile)
            with zipfile.ZipFile(bakFile, "r") as bakZip, zipfile.ZipFile(ddxFile, "w") as ddxZip:
                for item in bakZip.infolist():
                    buffer = bakZip.read(item.filename)
                    if (item.filename.lower() != filename.lower()):
                        ddxZip.writestr(item.filename, buffer)
                    else:
                        self.log.debug("File '%s' skipped", filename)
            Path(bakFile).unlink()
        return

    @classmethod
    def open(
        cls,
        ddxFile                 # DDX-File
    ):
        """opens DDX from file 'ddxFile'

        args:
            ddxFile (str)       DDX-File

        returns:
            obj (GxDDX)         GxDDX load from ddxFile

        exceptions:
            AssertionError      if argument 'ddxFile' is not set or is not type 'str'
            GxFileError         if ddxFile not found/exists
            GxBadFileError      on loading bad or corrupted ddxFile
            GxException         when an unknown error occurs

        19.04.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE,"")
        if not (bool(ddxFile) and isinstance(ddxFile, str)):
            raise AssertionError("Argument 'ddxFile' is not set or is not type 'str'")
        obj = None
        try:
            with zipfile.ZipFile(ddxFile, "r") as zipFile:
                with zipFile.open(cls._DumpFile, "r") as dmpFile:
                    jsonObj = json.loads(dmpFile.read())
            jsonDct = jsonObj[cls.__name__]
            if not isinstance(jsonDct, dict):
                raise AssertionError("Type 'dict' is expected, but type '%s' was loaded" % type(jsonDct).__name__)
            obj = cls.from_json(jsonDct, ddxFile)
        except FileNotFoundError:
            # FileNotFoundError: [Errno 2] No such file or directory: '{ddxFile}'
            cls.log.warning("GxFileError: No such file '%s'", ddxFile)
            raise gqb.GxFileError("No such file '%s'", ddxFile)
        except (zipfile.BadZipFile, KeyError, AssertionError):
            # zipfile.BadZipFile: File is not a zip file
            # KeyError: "There is no item named 'gxddx.content' in the archive"
            # KeyError: 'GxDDX'
            # AssertionError: Type 'dict' is expected, but type 'list' was loaded
            cls.log.warning("GxBadFileError: Bad or corrupted file '%s'", ddxFile)
            raise gqb.GxBadFileError("Bad or corrupted file '%s'", ddxFile)
        except:
            cls.log.error(
                "GxException on loading %s from file '%s'", cls.__name__, ddxFile,
                exc_info=True
            )
            raise gqb.GxException("Error on loading %s from file '%s'", cls.__name__, ddxFile)
        return obj

    def save(self):
        """saves DDX

        12.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # DumpDict erstellen und aktualsieren
        dmpDict = dict(self)
        # - Update User/Date immer aktualisieren, wenn das Objekt gespeichert wird
        dmpDict['updUser'] = os.getlogin()
        dmpDict['updDate'] = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
        # - Insert User/Date nur aktualisieren, wenn sie nicht gesetzt sind/nicht geladen wurden
        dmpDict['insUser'] = self._DumpDict.get('insUser', dmpDict['updUser'])
        dmpDict['insDate'] = self._DumpDict.get('insDate', dmpDict['updDate'])
        # DDX speichern...
        if not Path(self.File).exists():
            # Wenn das DDX-File noch nicht existiert,
            # dann leeres DDX-File/ZIP-File erstellen
            # 07/2023 j.ebert, Anmerkung
            #   Wenn beim Erstellen eines neuen DDX das DDX-File nicht existiert,
            #   dann verursacht die Methode update() eine Exception.
            with zipfile.ZipFile(self.File, "w") as zipFile:
                pass
        dmpData = {self.__class__.__name__: dmpDict}
        self.update(self._DumpFile, json.dumps(dmpData, indent=4).encode("utf-8"))
        # DumpDict vom Objekt nach erfolgreichen Speichern aktualisieren
        self._DumpDict = dmpDict
        # isDirty-Flag zurücksetzen
        self._isDirty = False
        # DDX Data Folder erstellen, wenn er noch nicht existiert
        self._mkdata()
        return self._File

    @classmethod
    def suffix(cls):
        """returns default DDX file suffix

        26.04.2023 j.ebert
        """
        return ".gddx"

    def load(self):
        """loads DDX

        17.04.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        with zipfile.ZipFile(self.File, "r") as z:
            with z.open(self._DumpFile, "r") as c:
                o = json.loads( c.read())
        return o

    def restore(
        self,
        gDBList=[]              # GoDatabase list from GeODin configuration
    ):
        """restores DDX

        07.06.2023 j.ebert
        """
        # Datenbanken zurücksetzen
        self._Databases = []
        # Datenbanken aus DDX-File laden...
##        ddxDBList = []
        ddxDBDict = {}
        with zipfile.ZipFile(self.File, "r") as ddxZip:
            dumpFilenames = [
                item.filename.lower() for item in ddxZip.filelist
                if item.filename.lower().startswith(GxDB._Prefix)
            ]
            for filename in dumpFilenames:
                self.log.debug("%s - %s", self.File, filename)
                with ddxZip.open(filename, "r") as dmpFile:
                    jsonObj = json.loads(dmpFile.read())
                    self.log.debug("%s - %s...\n%s", self.File, filename, str(jsonObj))
                    gDB = GxDB.from_json(jsonObj, self)
                    if gDB:
                        ddxDBDict[gDB.Name] = gDB
                        gDB._isPresent = True
##                    data = dmpFile.read()
##                    self.log.debug("%s - %s...\n%s", self.File, filename, data)
                    pass
        # Datenbanken mit aktueller GeODin-Konfiguration überladen
##        ddxDBDict = {gDB.name: gDB for gDB in ddxDBList}
        for gDB in gDBList:
            # Datenbank aus Liste der GeODin-Konfiguration hinzufügen, wenn
            # der Datenbank-Name noch nicht im DDX existiert
            ddxDB = ddxDBDict.setdefault(gDB.Name, gDB)
            # Datenbank validieren...
            # entweder DB aus dem DDX mit akt. Settings aus der GeODin-Konfiguration überladen oder
            # DDX refernzieren, wenn DB nicht aus dem DDX, sondern nur aus der GeODin-Konfiguration
            ddxDB.overload(self, gDB)
        # 06/2023 j.ebert, Anmerkung vom GeODin Add-In für ArcGIS Pro
        #    Achtung, wenn der GeODin-Parameter AutOpen gesetzt ist,
        #    dann wird IsPresent gesetzt und die GeODin-DB automatisch im GoExplorer hinzugefügt.
        #    Die Methode GoNodeDBGroup.DBCnnADD_Click() wird dabei NICHT ausgeführt und daher
        #    muss die GeODin-DB mit AutoOpen hier sofort in das gXtn Package gespeichert werden.
        # Datenbanken als sortierte Liste  erstellen/setzen
        self._Databases = sorted(ddxDBDict.values(), key=lambda gDB: gDB.Name)
        return self._Databases

    def presentGoQrys(self):
        """returns GoQuery list

        07.08.2023 j.ebert
        """
        qrys = []
        for gdb in self.Databases():
            qrys += gdb.usedGoQrys()

    def to_json(self):
        """gibt ein mit JSON serialisierbares Objekt dieser Klasse zurück

        20.01.2023 j.ebert
        """
        return dict(self)

    @classmethod
    def from_json(
        cls,
        json_dct,               # JSON-Objekt (dict)
        ddxFile=""
        ):
        """erstellt ein neues Objekt dieser Klasse aus dem JSON-Objekt

        20.01.2023 j.ebert
        """
        if not isinstance(json_dct, dict):
            raise AssertionError(f"arg 'json_dct': type 'dict' expected, but '{type(json_dct).__name__}' received")
        # Objekt erstellen
        if not ddxFile:
            ddxFile = json_dct['File']
        obj = cls(ddxFile)
##        obj._Data = json_dct.get('DDX-Data', obj._Data)
##        obj._Conf = json_dct.get('DDX-Conf', obj._Conf)
        obj.Data = obj._abspath(json_dct.get('Data', obj.Data))
        obj.Conf = obj._abspath(json_dct.get('Conf', obj.Conf))
        obj.SaveRelPaths = json_dct.get('SaveRelPaths', obj.SaveRelPaths)
        obj._DumpDict = json_dct
        return obj

    def dumps(self):
        return json.dumps({self.__class__.__name__: self.to_json()}, indent=_JSON_DUMP_IDENT)

    def dumpFilenames(self):
        self.log.log(gqc._LOG_TRACE,"")
        dumpFilenames = []
        try:
            with zipfile.ZipFile(self.File) as ddxZip:
                dumpFilenames = [item.filename.lower() for item in ddxZip.filelist]
        except:
            self.log.critical(
                "Failed to Dump-Filenames of DDX file\n\t%s", self.File,
                exc_info=True
            )
        return dumpFilenames

    def update(
        self,
        filename,               # name of the file being updated/deleted
        data=""                 # data are written to the file
    ):
        """

        args:
            filename (str)      - name of the file being updated/deleted
            data (str)          - data are written to the file
                                  File 'filename' will be deleted if data is an empty string.

        06.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        if not (bool(filename) and isinstance(filename, str)):
            raise AssertionError(f"Argument 'filename': string is required and not emtpy")
        ddxFile = self.File
        tmpPath = None
        try:
            with zipfile.ZipFile(ddxFile) as ddxZip:
                existsFilename = (
                    filename.lower() in [item.filename.lower() for item in ddxZip.filelist]
                )
            if ((not existsFilename) and bool(data)):
                # Wenn filename im ZIP-File nicht existiert und
                # wenn Argumnet 'data' gesetzt ist,
                # dann File 'filename' (mit Inhalt) 'data' an das ZIP-File anhängen
                self.log.debug("File '%s' is added", filename)
                with zipfile.ZipFile(ddxFile, "a") as ddxZip:
                    ddxZip.writestr(filename, data)
            elif not existsFilename:
                # Wenn filename im ZIP-File nicht existiert und
                # wenn Argumnet 'data' NICHT gesetzt ist,
                # dann keine Aktion (weder hinzufügen noch aktualisieren/löschen
                self.log.debug("File '%s' not found", filename)
            else:
                # Wenn filename im ZIP-File existiert und
                # dann File 'filename' aktualisieren/löschen
                #   aktualisieren, wenn Argumnet 'data' gesetzt ist
                #   löschen, wenn Argumnet 'data' NICHT gesetzt ist
                tmpPath = Path(self._tmpFilename(ddxFile))
                with zipfile.ZipFile(ddxFile, "r") as ddxZip, zipfile.ZipFile(tmpPath, "w") as tmpZip:
                    for item in ddxZip.infolist():
                        buffer = ddxZip.read(item.filename)
                        if (item.filename.lower() != filename.lower()):
                            tmpZip.writestr(item.filename, buffer)
                        elif data:
                            self.log.debug("File '%s' is updated", filename)
                            tmpZip.writestr(filename, data)
                            # 06/2023 j.ebert Anmerkung
                            #   Variable data zurücksetzen, damit ggf. weitere Files mit dem
                            #   selben Namen im ZIP-File gelöscht werden (siehe elif Bedingung)
                            data = None
                        else:
                            self.log.debug("File '%s' is skipped", filename)
                Path(ddxFile).unlink()
                tmpPath.rename(ddxFile)
        except:
            self.log.critical(
                "DDX-File '%s' could not be updated\n\tfilename: %s\n\tdata:     %s\n",
                self.File, filename, str(data)[:25],
                exc_info=True
            )
            if (bool(tmpPath) and tmpPath.exists()):
                tmpPath.unlink()
            raise
        return

    def _mkdata(self):
        """ creates the DDX data folder and parent folders, if any

        returns:
            True|False          True if the DDX data folder exists when the function exits

        23.05.2023 j.ebert
        """
        dirPath = Path(self.Data)
        if not dirPath.exists():
            try:
                # Parent-Directories erstellen, wenn sie nicht existieren
                # 05/2023 j.ebert, Anmerkung
                # - Root muss existieren/wird nicht erstellt    -> start = len(dirPath.parents) - 2
                # - range() ist immer exklusiv des stop Wertes  -> stop = -1
                # - an der Root beginnen, also 'absteigend'     -> step = -1
                for idx in range(len(dirPath.parents) - 2, -1, -1):
                    dirPath.parents[idx].mkdir(exist_ok=True)
                # DDX Data Folder erstellen
                dirPath.mkdir(exist_ok=True)
            except:
                self.log.error("Failed to create DDX data folder '%s'", self.Data, exc_info=True)
        return dirPath.exists()

    def _relpath(
        self,
        path
    ):
        """return a relativ version of path to DDX-File directory

        20.04.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
##        assert bool(path) and isinstance(path, (str, Path)), \
##            "Argument 'path' is not set or is not type 'str' or 'Path'"
        if not isinstance(path, (str, Path)):
            raise AssertionError("Argument 'path' is not type 'str' or 'Path'")
        relpath = str(path)
        if (
            bool(path) and
            self.SaveRelPaths and
            bool(self.File) and
            Path(path).is_relative_to(Path(self.File).anchor)
        ):
            relpath = os.path.relpath(path, Path(self.File).parent)
        self.log.debug(f"""
    SaveRelPaths: {str(self.SaveRelPaths)}
    File:         {self.File}
    path:         {str(path)}
    relpath       {str(relpath)}
        """)
        return relpath

    def _abspath(
        self,
        path
    ):
        """return a absolute version of path to DDX-File directory

        20.04.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
##        assert bool(path) and isinstance(path, (str, Path)), \
##            "Argument 'path' is not set or is not type 'str' or 'Path'"
        if not isinstance(path, (str, Path)):
            raise AssertionError("Argument 'path' is not type 'str' or 'Path'")
        abspath = str(path)
        if (
            bool(path) and
            bool(self.File) and
            (not Path(path).is_absolute())
        ):
            abspath = str(Path(self.File).parent.joinpath(path).resolve())
        self.log.debug(f"""
    File:         {self.File}
    path:         {str(path)}
    abspath:      {str(abspath)}
        """)
        return abspath

    @classmethod
    def _tmpFilename(
        cls,
        filename
    ):
        """
        07.06.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE,"")
        tmpFilename = None
        curPath = Path(filename)
        with tempfile.NamedTemporaryFile(
            dir=curPath.parent, prefix=curPath.stem + '_', suffix=curPath.suffix
        ) as tmpFile:
            tmpFilename = tmpFile.name
        cls.log.debug("   filename   %s\n\ttmpFilename   %s", filename, tmpFilename)
        return tmpFilename

    def __iter__(self):
        yield from {
            'File': self.File,
            'Data': self._relpath(self.Data),
            'Conf': self._relpath(self.Conf),
            'SaveRelPaths': self.SaveRelPaths
        }.items()

def main():
    pass

def dev():
    """nur temporär zum Entwickln und Testen

    19.04.2023 j.ebert
    """
    ddxFile = r"C:\Data\GeODinQGIS\temp\test_22.gddx"
    ddxPath = Path(ddxFile)
    if ddxPath.exists():
        print ("Delete gDDX-File '%s'" % ddxFile)
        ddxPath.unlink()
    ddx = GxDDX(ddxFile)
    ddx.Data = r"C:\Data\GeODinQGIS\temp\test_22.gddx"
    ddx.Conf = r"C:\Data\GeODinQGIS\data\geodin\2303_gQGIS_SysDB_002\GEODIN.INI"
    ddx.save()
    return


if __name__ == '__main__':
    main()
    dev()
