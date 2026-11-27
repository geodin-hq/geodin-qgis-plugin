"""
Globals:
    COMPANY             - company name (type: str)
    PRODUCT             - product name (type: str)
    LOCALAPPDATA        - local data folder (type: Path)

Classes:
    Config              - Config Class to manage configuration (Singleton!), JSON file
    Env                 - Env Class to manage environment (Singleton!)
    EnvDict             - customiced Python dict class


08.09.2022 J.Ebert
"""
import json
import logging
import os
from pathlib import Path
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
        # 10/2026: the variables are optional - show 'not set (default: ...)' instead of
        #   "environment variable doesn't exist!" (looked like an error)
        # (old: os.getenv('QGIS_PLUGINPATH', "environment variable doesn't exist!") etc.)
        try:
            from qgis.core import QgsApplication
            dftPluginPath = str(Path(QgsApplication.qgisSettingsDirPath()) / 'python' / 'plugins')
        except Exception:
            dftPluginPath = str(self.AppPath.parent)
        dftConfigDir = str(self.AppPath / 'config')
        dftLogFolder = str(Path(os.getenv('LOCALAPPDATA', Path.home()), COMPANY, PRODUCT, 'Logs'))
        txt = f"""
System environment:
    QGIS_PLUGINPATH         {self._envText('QGIS_PLUGINPATH', dftPluginPath)}

    GEODINQGIS_CONFIG_DIR   {self._envText('GEODINQGIS_CONFIG_DIR', dftConfigDir)}
    GEODINQGIS_LOG_FOLDER   {self._envText('GEODINQGIS_LOG_FOLDER', dftLogFolder)}
"""
        self.log.debug(txt)
        return txt

    @staticmethod
    def _envText(name, default=""):
        """returns the value of the environment variable or 'not set (default: ...)'

        10/2026
        """
        val = os.getenv(name)
        if val:
            return val
        return f"not set (default: {default})" if default else "not set"

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
        self.__ConfigFile = LOCALAPPDATA / 'config.json'
        """configuration file (11/2026: JSON, before shelve file 'config')"""

    def _load(self):
        try:
            return json.loads(self.__ConfigFile.read_text(encoding='utf-8'))
        except FileNotFoundError:
            return {}
        except ValueError:
            self.log.warning("Invalid configuration file '%s' ignored", self.__ConfigFile)
            return {}

    def _save(self, data):
        self.__ConfigFile.write_text(json.dumps(data, indent=4), encoding='utf-8')

    def __getitem__(self, key):
        return self._load()[key]

    def __setitem__(self, key, value):
        data = self._load()
        data[key] = value
        self._save(data)

    def __delitem__(self, key):
        data = self._load()
        value = data.pop(key)
        self._save(data)
        return value

    def get(self, key, default=None):
        return self._load().get(key, default)

    def pop(self, key, default=None):
        data = self._load()
        value = data.pop(key, default)
        self._save(data)
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

