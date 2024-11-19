"""
Globals:
    COMPANY             - company name (type: str)
    PRODUCT             - product name (type: str)
    LOCALAPPDATA        - local data folder (type: Path)

Classes:
    Config              - Config Class to manage configuration (Singleton!)
    Env                 - Env Class to manage environment (Singleton!)
    EnvDict             - customiced Python dict class


08.09.2022 J.Ebert
"""
import logging
import os
from pathlib import Path
import shelve
import tempfile

# global settings...
COMPANY = 'Fugro'
"""company name (type: str)"""
PRODUCT = Path(__file__).parents[1].name
"""product name (type: str)"""
LOCALAPPDATA = Path(os.getenv('LOCALAPPDATA', Path.home()), COMPANY, PRODUCT)
"""local data folder (type: Path)"""
LOCALAPPDATA.mkdir(parents=True, exist_ok=True)

class EnvDict(dict):
    """ customiced Python dict class

    19.11.2021 j.ebert
    """
    __getattr__= dict.__getitem__
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__

class Env(object):
    """ environment class (Singleton!)

    08.09.2022 J.Ebert
    """
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Env, cls).__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self):
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("")
        self._LocalAppData = None
        self._TmpFolder = None

        self.__Default_TmpFolder = None

    @property
    def Company(self):
        """ company name (str)

        26.08.2022 J.Ebert
        """
        return COMPANY

    @property
    def Product(self):
        """ produkt name (str)

        26.08.2022 J.Ebert
        """
        return PRODUCT

    @property
    def AppName(self):
        """ application name (str)

        26.08.2022 J.Ebert
        """
        return Path(__file__).parents[1].name

    @property
    def AppPath(self):
        """ application path/location (Path)

        26.08.2022 J.Ebert
        """
        return Path(__file__).parents[1]

    @property
    def AppHelpFolder(self):
        """ application help folder/prefix (Path)

        05.09.2022 J.Ebert
        """
        return self.AppPath / "help"

    @property
    def LocalAppData(self):
        """ local application data folder (Path)

        26.08.2022 J.Ebert
        """
        if not self._LocalAppData:
            # Wenn die Systemvariable LOCALAPPDATA nicht existiert,
            # dann wird der Benutzerordner/das Benutzerverzeichnis auf dem Computer genutzt
            self._LocalAppData = Path(
                os.getenv('LOCALAPPDATA', Path.home()), self.Company, self.Product)
            self._LocalAppData.mkdir(parents=True, exist_ok=True)
        return self._LocalAppData

    @property
    def Default_TmpFolder(self):
        """ local temp Folder (Path)

        26.08.2022 J.Ebert
        """
        if not self.__Default_TmpFolder:
            self.__Default_TmpFolder = Path(self.LocalAppData / 'tmp')
            self.__Default_TmpFolder.mkdir(parents=True, exist_ok=True)
        return self.__Default_TmpFolder

    @property
    def TmpFolder(self):
        """ local temp Folder (Path)

        17.08.2023
        """
        # 17.08.2023 j.ebert, Anmerkung
        #   Das Verzeichnis 'TmpFolder' war leer - wurde bis 08/2023 offensichltich nicht genutzt!
        #   Das Verzeichnis 'TmpFolder' wurde mit Path(self.LocalAppData / 'tmp') gesetzt.
        #   Änderung:  intern tempfile.TemporaryDirectory, aber Property weiterhin Path
        #       Damit ist TmpFolder ein Verzeichnis, das nur während einer Session existiert.
        #       Das Verzeichnis und deren Inhalt wird gelöscht,
        #       wenn das Attr _TmpFolder gelöscht oder neu gesetzt wird, also
        #       wenn das tempfile.TemporaryDirectory-Objekt nicht mehr refenziert ist.
        if not self._TmpFolder:
            self._TmpFolder = tempfile.TemporaryDirectory(prefix=f"{PRODUCT}_")
        return Path(self._TmpFolder.name)

    @property
    def TmpFolder_v01(self):
        """ local temp Folder (Path)

        26.08.2022 J.Ebert
        """
        if not self._TmpFolder:
            self._TmpFolder = Path(self.LocalAppData / 'tmp')
            self._TmpFolder.mkdir(parents=True, exist_ok=True)
        return self._TmpFolder

    def InfoText(self):
        """ returns Info Text

        05.09.2022 J.Ebert
        """
        txt = f"""
Application environment:
    AppName             {self.AppName}
    AppPath             {str(self.AppPath)}

    LocalAppData        {str(self.LocalAppData)}
    TmpFolder           {str(self.TmpFolder)}
"""
        # 06/2023 j.ebert, AppHelpFolder aus InfoText entfernt, da es noch keine Hilfe gibt
##    AppHelpFolder       {str(self.AppHelpFolder)}
        self.log.debug(txt)
        return txt

    def InfoText_OS(self):
        """ returns info text about os environment

        05.09.2022 J.Ebert
        """
        txt = f"""
System environment:
    QGIS_PLUGINPATH         {os.getenv('QGIS_PLUGINPATH', "environment variable doesn't exist!")}

    GEODINQGIS_CONFIG_DIR   {os.getenv('GEODINQGIS_CONFIG_DIR', "environment variable doesn't exist!")}
    GEODINQGIS_LOG_FOLDER   {os.getenv('GEODINQGIS_LOG_FOLDER', "environment variable doesn't exist!")}
"""
        self.log.debug(txt)
        return txt

    @classmethod
    def isFugroDE(cls):
        val = (
            ('FUGRO' in os.environ.get('USERDOMAIN',"").upper()) and
            ('FUGRO' in os.environ.get('USERDNSDOMAIN',"").upper()) and
            ('DE' == os.environ.get('LOGONSERVER', "").lstrip("\\").upper()[0:2])
            # 08/2023 j.ebert, Test mit PrHa -> Systemvariablen PSDistrict_* existieren nicht :(
            # ('DE' == os.environ.get('PSDistrict_FugroCountryCode',"").upper())
        )
        return val


class Config(object):
    """configuration class (Silgleton!)

    08.09.2022 J.Ebert
    """
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self):
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("self.__repr__()")
        self.__ConfigFile = LOCALAPPDATA / 'config'
        """configuartion file"""

    def __getitem__(self, key):
        with shelve.open(str(self.__ConfigFile)) as sFile:
            value = sFile[key]
        return value

    def __setitem__(self, key, value):
        with shelve.open(str(self.__ConfigFile)) as sFile:
            sFile[key] = value
        return

    def __delitem__(self, key):
        with shelve.open(str(self.__ConfigFile)) as sFile:
            value = sFile.pop(key)
        return value

    def get(self, key, default=None):
        with shelve.open(str(self.__ConfigFile)) as sFile:
            value = sFile.get(key, default)
        return value

    def pop(self, key, default=None):
        with shelve.open(str(self.__ConfigFile)) as sFile:
            value = sFile.pop(key, default)
        return value

    @property
    def ConfigFile(self):
        """configuration file

        08.09.2022 J.Ebert
        """
        return self.__ConfigFile

def main():
    env = Env()
    print(f"""
    env.Company             {env.Company}
    env.Product             {env.Product}

    env.AppName             {env.AppName}
    env.AppPath             {env.AppPath}
    env.AppHelpFolder       {env.AppHelpFolder}

    env.LocalAppData        {env.LocalAppData}
    env.TmpFolder           {env.TmpFolder}

    """)

    print (env.InfoText())
    return env
if __name__ == '__main__':
     env = main()
     cfg = Config()

