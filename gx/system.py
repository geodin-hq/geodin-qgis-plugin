"""
Classes:
    GxReg                       - GeODin registry access
    GxSys                       - GeODin system

06.03.2023 j.ebert
"""

import datetime
import json
import logging
import os
import re
import struct
import time
from pathlib import Path
from win32api import (
    GetFileVersionInfo,
    HIWORD,
    LOWORD
    )
import winreg
import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gqgis_config as gqc

class GxReg:
    """GeODin registry access

    14.03.2023 j.ebert
    """
    log = logging.getLogger(f"{gqc._LOG_PARENTS}GxReg")

    @classmethod
    def key(cls, *args):
        """GeODin System Registry Key

        retruns:
            RegKey (str)        - GeODin System RegKey ""

        08.03.2023 j.ebert
        """
        regKey = r"SOFTWARE\GeODin-System"
        if args:
            regKey = "\\".join([regKey] + list(args))
        return regKey

    @classmethod
    def query(
        cls,
        keyname,                # subkey name|path from GeODin registry 'GeODin-System'
        valname="",             # value name GeODin registry
        default=None,           # default value
    ):
        """queries GeODin registry value specified by keyname and valname

        args:
            keyname (str|list)  - subkey name|path from GeODin registry 'GeODin-System'
            valname (str)       - value name GeODin registry
            default             - default value

        retruns:
            RegVal              - value from GeODin registry specified by keyname and valname

        08.03.2023 j.ebert
        """
        assert isinstance(keyname, (str, list))
        assert isinstance(valname, str)
        if isinstance(keyname, str):
            regKey = cls.key(keyname)
        else:
            regKey = cls.key(*keyname)
        regVal = default
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, regKey, 0, winreg.KEY_READ) as regKey:
                regVal, type_id = winreg.QueryValueEx(regKey, valname)
        except:
            pass
        return regVal

    @classmethod
    def lastGeoDinIni(cls):
        r"""returns the geodin.ini of the GeoDin application started last ('' if not found)

        HKEY_CURRENT_USER\Software\GeODin-System\System, value RootDir
        (folder of the GeoDin application; the geodin.ini is in this folder,
         the geodin.exe in its subfolder Bin)

        10/2026
        """
        rootDir = cls.query('System', 'RootDir', "")
        if not rootDir:
            return ""
        try:
            root = Path(str(rootDir).strip().strip('"'))
            folders = [root]
            if root.name.lower() == 'bin':
                # in case RootDir points to the Bin folder
                folders.append(root.parent)
            for folder in folders:
                for name in ('geodin.ini', 'GEODIN.INI'):
                    ini = folder / name
                    if ini.is_file():
                        return str(ini)
        except Exception:
            cls.log.debug("RootDir '%s'", rootDir, exc_info=True)
        cls.log.debug("No geodin.ini in RootDir '%s'", rootDir)
        return ""

    @classmethod
    def query_Database(
        cls,
        name                    # GeODin database name
    ):
        """loads the GeODin database porperties from the Windows registry

        args:
            name (str)          - GeODin database name

        returns:
            prps (dict)         - GeODin database ViewPorperties

        13.03.2023 j.ebert
        """
        prps = {}
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.key('Database', name),
                0,
                winreg.KEY_READ
            ) as regKey:
                # winreg.QueryInfoKey(key) returns a tuple of 3 items:
                #   0 - An integer giving the number of sub keys this key has.
                #   1 - An integer giving the number of values this key has.
                #   2 - An integer giving when the key was last modified (if available)
                #       as 100’s of nanoseconds since Jan 1, 1601.
                for idx in range(0, winreg.QueryInfoKey(regKey)[1]):
                    # winreg.EnumValue(key, index) returns a tuple of 3 items:
                    #   0 - A string that identifies the value name
                    #   1 - An object that holds the value data, and
                    #       whose type depends on the underlying registry type
                    #   2 - An integer that identifies the type of the value data
                    #       (see table in docs for SetValueEx())
                    regVal = winreg.EnumValue(regKey, idx)
                    print(f"RegKey Value {idx}", regVal)
                    # Werte ignorieren, deren Name (also Item 0) mit 'Connection' endet
                    # -> ADOConnection und FireDACConnection ignorieren/NICHT ins Dict speichern
                    if not regVal[0].endswith('Connection'):
                        prps[regVal[0]] = regVal[1]
        except:
            cls.log.warning("", exc_info=True)
        return prps

    @classmethod
    def query_Handle(cls):
        """GeODin System RegKey 'Handle' (REG_DWORD)

        retruns:
            RegKey              - GeODin System RegKey 'Handle' (REG_DWORD)

        08.03.2023 j.ebert
        """
        # 09.03.2023 j.ebert, Test mit GeODin 9.6 (27.10.2022)
        #   Handle ist 0, wenn GeODin nicht ausgeführt wird
        #   Handle ist noch 0, solange bis eine Lizenz ausgewählt wurde
        #   Handle ungleich 0, wenn GeODin ausgeführt wird
        #   Handle ungleich 0 und "anders", wenn GeODin neugestartet wurde
        # Fazit:
        #   RegSZ Handle zur Ablaufsteuerung nutzen
        #   (z.B. beim Warten auf die Lizenz, beim Pürfen der COM Verbindung, ...)
        return cls.query('System', 'Handle', 0)

    @classmethod
    def query_UserLId(cls):
        """GeODin System RegKey 'UserLId' (REG_DWORD)

        retruns:
            RegKey              - GeODin System RegKey 'UserLId' (REG_DWORD)

        20.09.2023 j.ebert
        """
        # 09/2023 j.ebert, Default UserLId 7 (Deutsch) - GeODin 9.6.264.0 (01.08.2023 - Win64)
        return cls.query('System', 'UserLId', 7)

    @classmethod
    def prog_info(cls):
        """About...

        14.09.2022 J.Ebert
        """
        cls._query_prog_prps()
        if (
            bool(cls._prog_path_key64) and bool(cls._prog_path_key32) and
            bool(cls._prog_path)
        ):
            # Warning: GeODin 64 Bit and also GeODin 32 Bit registered
            # 06/2023 j.ebert, Anmerkung
            #   Wenn Attr cls._prog_path (in der Methode cls.__query_prog_prps() gesetzt wird,
            #   dann wird die Regsitrierung/INstallation prinzipiell akzeptiert/unterstützt und
            #   dann wird der Text nur mit einer Warnung zurückgegeben
            version = ".".join([str(item) for item in cls.get_FileVersion(cls._prog_path_key64)])
            rows = [
                'GeoDin %s' % version,
                'Warning: GeoDin 64 bit and also GeoDin 32 bit are registered',
                '         %s' % cls._prog_path_key64,
                '         %s' % cls._prog_path_key32,
                ]
        elif (
            bool(cls._prog_path_key64) and bool(cls._prog_path_key32) and
            not bool(cls._prog_path)
        ):
            # Error: GeODin 64 Bit and also GeODin 32 Bit registered
            rows = [
                'GeoDin',
                'Error: GeoDin 64 bit and also GeoDin 32 bit are registered',
                '       %s' % cls._prog_path_key64,
                '       %s' % cls._prog_path_key32,
                ]
        elif cls._prog_path_key64:
            # GeODin 64 Bit registered
            rows = cls.prog_info_lines(cls._prog_path_key64, 'Win64')
        elif cls._prog_path_key32:
            # GeODin 32 Bit registered
            rows = cls.prog_info_lines(cls._prog_path_key32, 'Win32')
            # 06/2023 j.ebert, Anmerkung
            #   GeODinQGIS Plugin unterstützt prinzipiell nur noch GeODin 64 Bit.
            #   (siehe auch Methode cls._query_prog_prps())
            #   Dieser Text 'About...' wird druchgereicht und muss eine klare Aussage haben:
            #   32 Bit Registrierung ist ein Error (unabhängig welche geodin.exe)!!!
            rows = [
                'GeoDin',
                'Error: GeoDin 32 bit is registered but not supported',
                '       %s' % cls._prog_path_key32,
                ]
        else:
            # Warning: neither GeODin 64 bit nor GeODin 32 bit registered
            rows = [
                'GeoDin',
                'Error: GeoDin is not installed/registered'
                ]
        txt = "\n    ".join(rows) + "\n"
        return txt

    @classmethod
    def prog_info_lines(
        cls,
        fname,                  # filename of GeODin application
        *args                   # additional token (for example 'Win64'|'Win32')
        ):
        """retunrs GeODin application info

        Args:
            fname   (str)       - filename of GeODin application
            *args               - additional token (for example 'Win64'|'Win32')

        Returns:
            rows    (list(str)) - info lines

        14.09.2022 J.Ebert
        """
        if not os.path.exists(fname):
            rows = [
                'GeoDin',
                'Error: registered GeoDin not found',
                '       %s' % fname]
        else:
            desc = [str(item) for item in args]
            desc.insert(
                0,
                datetime.datetime.fromtimestamp(os.path.getctime(fname)).strftime( "%d.%m.%Y")
            )
            text = " - ".join(desc)
            version = ".".join([str(item) for item in cls.get_FileVersion(fname)])
            rows = [
                f"GeoDin {version} ({text})",
                fname,
                ]
        return rows

    @classmethod
    def prog_alias(cls):
        """Alias for GeODin Application

        07.03.2023 j.ebert
        """
        return "GeoDin (64 Bit)"

    @classmethod
    def prog_clsid(cls):
        """GeODin ClassID

        Returns:
            ClsID   (str)   - ""|GeODin ClassID from the windows registry

        07.03.2023 j.ebert
        """
        cls._query_prog_prps()
        return cls._prog_clsid

    @classmethod
    def prog_id(cls):
        """GeODin ProgID

        Returns:
            ProgID  (str)   - GeODin ProgID "geodin.GeODinApplication"

        12.09.2022 J.Ebert
        """
        return "geodin.GeODinApplication"

    @classmethod
    def prog_path(cls):
        """GeODin Path

        Returns:
            Path   (str)   - ""|GeODin Path

        07.03.2023 j.ebert
        """
        cls._query_prog_prps()
        return cls._prog_path

    @classmethod
    def set_COMSrvAppFolder(
        cls,
        appFolder               # Applicationfolder (directory where a geodin.ini is stored)
    ):
        """tests Applicationfolder

        args:
            appFolder (str)     - Applicationfolder (directory where a geodin.ini is stored)

        returns:
            appFolder (str)     - Applicationfolder (directory where a geodin.ini is stored)

        exceptions:
            AssertionError      if argument 'appFolder' is not of type string or is empty
            GxAppFolderError    if Applictionfolder itself or file geodin.ini not found

        22.03.2023 j.ebert
        """
        # AppFolder prüfen...
        appFolder = GxSys.assert_AppFolder(appFolder)
        # GeODin RegSZ zum Starten als COM Server setzen
        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            cls.key('ComServer'),
            0,
            winreg.KEY_SET_VALUE
        ) as regKey:
            winreg.SetValueEx(regKey, 'ApplicationFolder', 0, winreg.REG_SZ, appFolder)
        return appFolder

    @classmethod
    def _default(cls, value, default=None):
        """returns value or default if value is not set

        13.09.2022 J.Ebert
        """
        if value:
            return value
        else:
            return default

    @classmethod
    def get_FileVersion(cls, fname):
        """returns file version or None if file not found (or in case of another exception)

        Returns:
            Version (tuple)     (Major, Minor, Build, Patch)

        https://www.programcreek.com/python/example/104579/win32api.GetFileVersionInfo
        """
        try:
            info = GetFileVersionInfo (fname, "\\")
            ms = info['FileVersionMS']
            ls = info['FileVersionLS']
            return HIWORD (ms), LOWORD (ms), HIWORD (ls), LOWORD (ls)
        except:
            cls.log.debug(fname, exc_info=True)
            return None

    @classmethod
    def _get_FileProperties(cls, fname):
        """read all properties of the given file return them as a dictionary.

        https://www.programcreek.com/python/example/104579/win32api.GetFileVersionInfo
        """
        import win32api
        propNames = ('Comments', 'InternalName', 'ProductName',
            'CompanyName', 'LegalCopyright', 'ProductVersion',
            'FileDescription', 'LegalTrademarks', 'PrivateBuild',
            'FileVersion', 'OriginalFilename', 'SpecialBuild')

        props = {'FixedFileInfo': None, 'StringFileInfo': None, 'FileVersion': None}

        try:
            # backslash as parm returns dictionary of numeric info corresponding to VS_FIXEDFILEINFO struc
            fixedInfo = win32api.GetFileVersionInfo(fname, '\\')
            props['FixedFileInfo'] = fixedInfo
            props['FileVersion'] = "%d.%d.%d.%d" % (
                    int(fixedInfo['FileVersionMS'] / 65536), fixedInfo['FileVersionMS'] % 65536,
                    int(fixedInfo['FileVersionLS'] / 65536), fixedInfo['FileVersionLS'] % 65536
                    )

            # \VarFileInfo\Translation returns list of available (language, codepage)
            # pairs that can be used to retreive string info. We are using only the first pair.
            lang, codepage = win32api.GetFileVersionInfo(fname, '\\VarFileInfo\\Translation')[0]

            # any other must be of the form \StringfileInfo\%04X%04X\parm_name, middle
            # two are language/codepage pair returned from above

            strInfo = {}
            for propName in propNames:
                strInfoPath = u'\\StringFileInfo\\%04X%04X\\%s' % (lang, codepage, propName)
                ## print str_info
                strInfo[propName] = win32api.GetFileVersionInfo(fname, strInfoPath)

            props['StringFileInfo'] = strInfo
        except:
            pass

        return props

    @classmethod
    def _query_prog_prps(cls):
        """querys GeODinApplication properties from Windows registry

        Notes:
            GeODin 8   32 Bit   ClsID = "{44A32582-B618-11D4-8601-00E0293462B8}"
            GeODin 9   32 Bit   ClsID = "{44A32582-B618-11D4-8601-00E0293462B8}"
            GeODin 9.5 64 Bit   ClsID = "{44A32582-B618-11D4-8601-00E0293462B8}"
            GeODin 9.6 64 Bit   ClsID = "{44A32582-B618-11D4-8601-00E0293462B8}"    Stand 09/2022

        12.09.2022 J.Ebert
        """
        if not hasattr(cls, '_prog_clsid'):
            cls._prog_clsid = cls._query_regkey(
                winreg.HKEY_CLASSES_ROOT,
                f"{cls.prog_id()}\\Clsid",
                default="")
            cls._prog_path_key64 = cls._query_regkey(
                winreg.HKEY_CLASSES_ROOT,
                f"CLSID\\{cls._prog_clsid}\\LocalServer32",
                default="",
                access=winreg.KEY_WOW64_64KEY)
            cls._prog_path_key32 = cls._query_regkey(
                winreg.HKEY_CLASSES_ROOT,
                f"CLSID\\{cls._prog_clsid}\\LocalServer32",
                default="",
                access=winreg.KEY_WOW64_32KEY)
            cls.log.debug(f"""GeoDinApllication porperties from Windows registry
        GeoDin ProgID   {cls.prog_id()}
        GeoDin ClsID    {cls._prog_clsid}
        GeoDin 64 Bit   {cls._default(cls._prog_path_key64, "not registered")}
        GeoDin 32 Bit   {cls._default(cls._prog_path_key32, "not registered")}
        """)
            # Anmerkung, nur GeODin 64 Bit wird unterstützt.
            #   _prog_path initialisieren (_prog_path_key64 oder auch Leerstring!)
            #   _prog_path ggf. zurücksetzen, wenn GeODin 32 Bit "anders" als 64 Bit registriert ist
            cls._prog_path = cls._prog_path_key64
            if (bool(cls._prog_path_key32) and (cls._prog_path_key32 != cls._prog_path_key64)):
                cls._prog_path = ""
        return

    @classmethod
    def _query_regkey(
        cls,
        rootkey,
        keyname,
        valname="",
        default=None,
        access=0
        ):
        regKey, regVal = None, None
        try:
            with winreg.OpenKey(rootkey, keyname, 0, winreg.KEY_READ | access) as regKey:
                regVal, type_id = winreg.QueryValueEx(regKey, valname)
        except Exception as exc:
            access_dict = {
                winreg.KEY_WOW64_32KEY: 'winreg.KEY_WOW64_32KEY',
                winreg.KEY_WOW64_64KEY: 'winreg.KEY_WOW64_64KEY',
            }
            access_dict.get(access, access)
            cls.log.debug(f"""{str(exc)}
        rootkey     {rootkey}
        keyname     {keyname}
        valname     {valname}
        access      winreg.KEY_READ | {access_dict.get(access, access)}""")
            regVal=default
        return regVal

class GxSys:
    """GeODin configuration

    16.03.2023 j.ebert
    """
    log = logging.getLogger(f"{gqc._LOG_PARENTS}GxConf")

    @classmethod
    def extract_CnnPrps(
        cls,
        settings                # GeODin configuration (TGClass_DatabaseSettingsList)
    ):
        """transforms GeODin configuration (from TGClass_DatabaseSettingsList)

        12.06.2023 j.ebert
        """
        cls.log.log(gqc._LOG_TRACE, "")
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
        prps = {}
        try:
            prps['connectionstring'] = settings['ConnectionString']
            prps['schema'] = settings.get('Schema', '')
##            pattern = re.compile(r'(([\w]+)=([^;]+))*(;|$)', re.IGNORECASE)
##            pattern = re.compile(r'(([\w]+)=([^;]+))', re.IGNORECASE)
##            for match in re.finditer(pattern, prps['connectionstring']):
##                prps[m.group(2).lower()] = m.group(3)
            pattern = re.compile(r'''
                ([\w]+)     # group 1/key - Zeichen von a-z, A-Z oder 0-9 oder Unterstrich
                =           # Trennung zwischen group 1/key und group 2/val
                ([^;]+)     # group 2/val - alle Zeichen außer Semikolon
            ''', re.IGNORECASE | re.VERBOSE)
            for match in re.finditer(pattern, prps['connectionstring']):
                prps[match.group(1).lower()] = match.group(2)
            prps['driverid'] = prps.get('driverid', '').upper()
            cls.log.debug(json.dumps(prps, indent=4).replace('\n','\n\t'))
        except:
            cls.log.error(
                "Error extracting DBConnection\n\t%s",
                str(settings),
                exc_info=True
            )
            prps = {}
            raise gqb.GxException('Error extracting DBConnection')
        return prps

    @classmethod
    def read_SystemDatabases(
        cls,
        programData             # GeODin ProgramData folder (str)
    ):
        """SystemDatabases of GeODin configuration

        returns:
            programData (str)   - GeODin ProgramData folder
            dbNames (list(str)) - list of SystemDatabase names

        exceptions:
            AssertionError, if argument 'programData' is not set
            AssertionError, if folder 'programData' not found

        13.03.2023 j.ebert
        """
        assert bool(programData) and isinstance(programData, str), \
            f"Argument 'programData': string is required and not emtpy"
        dataPath = Path(programData)
        assert dataPath.exists() and dataPath.is_dir(), \
            f"Folder '{str(dataPath)}' not found"
        # Liste der SystemDatabase Namen laden/einlesen...
        confPath = dataPath / 'Config'
        if confPath.exists() and confPath.is_dir():
            # Verzeichnis <ProgramData>\Config existiert...
            cls.log.debug("GeoDin config folder...\n\t%s", str(confPath))
            # Liste der SystemDatabase Namen laden/einlesen...
            #   SysDB configuration files     <ProgramData>\Config\*.con
            #   SysDB 1                       <ProgramData>\Config\<SysDB 1 Displayname>.con
            sysDBNames = [
                con.stem for con in confPath.iterdir() if (
                    con.is_file() and (con.suffix.lower() == ".con")
                )
            ]
        else:
            # Verzeichnis <ProgramData>\Config existiert nicht?!
            cls.log.error("GeoDin config folder not found\n\t%s", str(confPath))
            # Liste der SystemDatabase Namen ist eine leere Liste
            sysDBNames = []
        # ProgramData und Liste der SystemDatabase zurückgeben
        return (str(dataPath), sysDBNames)

    @classmethod
    def assert_AppFolder(
        cls,
        appFolder               # Applicationfolder (directory where a geodin.ini is stored)
    ):
        """tests Applicationfolder

        args:
            appFolder (str)     - Applicationfolder (directory where a geodin.ini is stored)

        returns:
            appFolder (str)     - Applicationfolder (directory where a geodin.ini is stored)

        exceptions:
            AssertionError      if argument 'appFolder' is not of type string or is empty
            GxAppFolderError    if Applictionfolder itself or file geodin.ini not found

        22.03.2023 j.ebert
        """
        cls.log.debug("appFolder    %s", appFolder)
        assert bool(appFolder) and isinstance(appFolder, str), \
            f"Argument 'appFolder': string is required and not emtpy"
        appPath = Path(appFolder)
        if (not appPath.exists()) and (not appPath.is_dir()):
            raise gqb.GxAppFolderError( "Folder '%s' not found", str(appPath))
        iniPath = appPath / 'geodin.ini'
        if (not iniPath.exists()) and (not iniPath.is_file()):
            raise gqb.GxAppFolderError( "File '%s' not found", str(iniPath))
        return str(appPath)



def main():
    pass

if __name__ == '__main__':
    main()
