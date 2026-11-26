"""
Globals:
    DEFAULT_LANGUAGE    - default Language code [''|<language code of operating syste]

Classes:
    Res                 - Res class to manage and translate resources


09.09.2022 J.Ebert
"""
import contextlib
import json
import logging
from pathlib import Path
import re

from .fg_env import Config

DEFAULT_LANGUAGE = ''
"""default langauge code for selecting the resource file"""
# use language of operating system, if possible
with contextlib.suppress(ImportError, KeyError):
    from ctypes import windll
    from locale import windows_locale
    DEFAULT_LANGUAGE = windows_locale[windll.kernel32.GetUserDefaultUILanguage()].split('_')[0]

AUTO_LANGUAGE = 'auto'
"""10/2026: language setting 'auto' - use the language of the QGIS user interface"""
FALLBACK_LANGUAGE = 'en'
"""10/2026: language code if the (QGIS) language is not supported"""


def qgisUiLanguage():
    """returns the language code of the QGIS user interface (e.g. 'de'), '' if unknown

    Order:
      1. QgsApplication.locale() - the language QGIS actually uses
      2. QGIS settings 'locale/overrideFlag' / 'locale/userLocale'
         (QGIS » Settings » Options » General » Override system locale), otherwise QLocale.system()
      3. '' (outside QGIS) - then DEFAULT_LANGUAGE (Windows UI language) is used

    10/2026
    """
    code = ''
    try:
        from qgis.core import QgsApplication
        code = QgsApplication.locale() or ''
    except Exception:
        code = ''
    if not code:
        try:
            from qgis.core import QgsSettings
            from qgis.PyQt.QtCore import QLocale
            settings = QgsSettings()
            if settings.value('locale/overrideFlag', False, type=bool):
                code = settings.value('locale/userLocale', '', type=str)
            if not code:
                code = QLocale.system().name()
        except Exception:
            code = ''
    # 'de_DE', 'de-DE', 'pt_BR' -> 'de', 'pt'
    return str(code).replace('-', '_').split('_')[0].lower()


class Res(object):
    """Res class to manage and translate resources

    08.09.2022 J.Ebert
    """

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Res, cls).__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self):
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.debug("self.__repr__()")
        self.__ResFolder = Path(__file__).parents[1] / 'res'
        """resource folder/folder with resource files 'resources_??.json'"""
        self.__LanguageCode = self._initLanguageCode()
        """current language code (en, de, ...)"""
        self.__LanguageDict = self._loadLanguageDict()
        """currenst language dictionary/dictionary for translations"""
        self.__Ui = []
        """List of widgests/objects to be translated when the language code changes"""

    def _initLanguageCode(self):
        # 10/2026: language of the QGIS user interface by default (setting 'auto');
        #   a language chosen in the GeoDinQGIS menu is saved as before and used instead
        #   (old code: code = Config().get('LANGUAGE', DEFAULT_LANGUAGE), i.e. Windows UI language)
        # one-time reset to 'auto' with this version (a language chosen afterwards is kept)
        if not Config().get('LANGUAGE_AUTO_2026', False):
            Config()['LANGUAGE'] = AUTO_LANGUAGE
            Config()['LANGUAGE_AUTO_2026'] = True
        mode = Config().get('LANGUAGE', AUTO_LANGUAGE) or AUTO_LANGUAGE
        self.__LanguageMode = mode
        code = self._autoLanguageCode() if mode == AUTO_LANGUAGE else mode
        if code and (code not in self.ResFileCodes):
            self.log.warning("Language '%s' is not supported! (OS '%s')", code, DEFAULT_LANGUAGE)
            code = FALLBACK_LANGUAGE if FALLBACK_LANGUAGE in self.ResFileCodes else ''
        self.log.info("Language '%s' (setting '%s')", code, mode)
        self.__LanguageCode = code
        return code

    def _autoLanguageCode(self):
        """returns the language code for the setting 'auto': QGIS UI language, else Windows UI language

        10/2026
        """
        code = qgisUiLanguage() or DEFAULT_LANGUAGE
        if code not in self.ResFileCodes:
            code = FALLBACK_LANGUAGE
        return code

    @property
    def AutoLanguageCode(self):
        """language code used for the setting 'auto' (QGIS UI language) (10/2026)"""
        return self._autoLanguageCode()

    @property
    def LanguageMode(self):
        """language setting: 'auto' (QGIS UI language) or the chosen language code (10/2026)"""
        return self.__LanguageMode

    def _loadLanguageDict(self):
        """ loads the translation dictionary of the language

        01.09.2022 J.Ebert
        """
        self.log.debug(str(self.ResFile))
        return self._loadDictionary(str(self.ResFile))

    def _loadDictionary(
        self,
        filename
    ):
        """ loads the translation dictionary of the language

        02.08.2023 j.ebert
        """
        self.log.debug(str(filename))
        outObj = {}
        try:
            # JSON-File vollständig einlesen...
            # 10/2026: encoding explicitly UTF-8 (resource files are UTF-8; default encoding on Windows is cp1252)
            with open(filename, 'r', encoding='utf-8') as fileObj:
                rows = fileObj.readlines()
##            self.log.debug("File content...\n\n%s\n\n", "".join(rows))
##            print("File content...\n\n%s\n\n" % "".join(rows))
            # JSON-Text/String extrahieren (bzw. Kommentare ignorieren)...
            regex = re.compile(r"""
                ^\s*        # am Anfang keine oder mehrere Leerzeichen bzw. nichtdruckbare Zeichen
                \#          # Kommentar beginnt einem #-Zeichen/Hash/Dopplekreuz
                """, re.VERBOSE)
            rows = [row for row in rows if not regex.match(row)]
##            self.log.debug("File content wihtout comments...\n\n%s\n\n", "".join(rows))
##            print("File content wihtout comments...\n\n%s\n\n" % "".join(rows))
            # JSON-Text/String in Python-Dictionary laden...
            outObj = json.loads( "".join(rows))
        except FileNotFoundError:
            self.log.warning("No such resource file: '%s'", str(filename))
        except:
            self.log.critical("", exc_info=True)
        return outObj

    def _loadLanguageDict(self):
        """ loads the translation dictionary of the language

        02.08.2023 j.ebert
        """
        self.log.debug(str(self.ResFile))
        return self._loadDictionary(str(self.ResFile))

    def _translateUi(self):
        """ translates the registered widgets/objects

        07.09.2022 J.Ebert
        """
        self.log.debug(self.LanguageCode)
        for item in [item for item in self.Ui if hasattr(item, 'translateUi')]:
                item.translateUi()
        return

    @property
    def LanguageCode(self):
        """current language code

        01.09.2022 J.Ebert
        """
        return self.__LanguageCode

    def changeLanguage(self, code):
        """changes the language settings

        Args:
            code (str)          - language code (en, de)

        08.09.2022 J.Ebert
        """
        self.log.info(code)
        # 10/2026: code 'auto' -> language of the QGIS user interface
        mode = code.lower()
        if mode != self.__LanguageMode:
            # save language setting ('auto' or language code) in the configuration
            self.__LanguageMode = mode
            Config()['LANGUAGE'] = mode
        code = self._autoLanguageCode() if mode == AUTO_LANGUAGE else mode
        if self.__LanguageCode != code.lower():
            self.__LanguageCode = code.lower()
            self.log.debug(self.LanguageCode)
            # load language dictionary
            self.__LanguageDict = self._loadLanguageDict()
            # translate registered widgests/objects
            self._translateUi()
        return

    @property
    def ResFolder(self):
        """ returns resource folder

        Returns:
            ResFolder (Path)

        05.09.2022 J.Ebert
        """
        return self.__ResFolder

    @property
    def ResFileCodes(self):
        """ returns list of resource file codes

        Returns:
            ResFileCodes    (list(str))

        05.09.2022 J.Ebert
        """
        # Ausgangspunkt
        #   <ResFolder>\resources_de.json
        #   <ResFolder>\resources_en.json
        # alle Files resources_??.json im ResFolder listen und
        # vom FileNamen (resFile.stem) die letzten beiden Zeichen in die Liste übernehmen
        return [resFile.stem[-2:] for resFile in self.ResFolder.glob("resources_??.json")]

    @property
    def ResFile(self):
        """ returns current resource file

        Returns:
            ResFile (Path)

        01.09.2022 J.Ebert
        """
        val = self.__ResFolder / f"resources_{self.__LanguageCode}.json"
        self.log.debug(str(val))
        return val

    @property
    def Ui(self):
        """ List of widgets/objects to be translated when the language code changes

        Returns:
            Ui  (list(obj))     - List of widgets/objects

        07.09.2022 J.Ebert
        """
        return self.__Ui

    def translate(
        self,
        context,
        key,
        disambiguation=None,
        n=-1
        ):
        """translate souerce text 'key'

        Args:
            context (str)       typically a class name (e.g., “MyDialog”)
            key (str)           source text
        Kwargs:
            disambiguation (str)
            n (int)
        Returns:
            sourceText (str)

static PySide2.QtCore.QCoreApplication.translate(context, key[, disambiguation=None[, n=-1]])¶

        21.08.2023 j.ebert
        """
        if self.log.level > logging.DEBUG:
            val = self.__LanguageDict.get(context,{}).get(key, key)
        else:
            val = self.__LanguageDict.get(context,{}).get(key, None)
            if val is None:
                val = key
                self.log.debug("Context::Key   %s::%s", context, key)
        return val

    def translate_v01(
        self,
        context,
        key,
        disambiguation=None,
        n=-1
        ):
        """translate souerce text 'key'

        Args:
            context (str)       typically a class name (e.g., “MyDialog”)
            key (str)           source text
        Kwargs:
            disambiguation (str)
            n (int)
        Returns:
            sourceText (str)

static PySide2.QtCore.QCoreApplication.translate(context, key[, disambiguation=None[, n=-1]])¶

        01.09.2022 J.Ebert
        """
        self.log.debug("Context::Key   %s::%s", context, key)
        try:
            key = self.__LanguageDict.get(context,{}).get(key, key)
        except:
            self.log.critical("Major disaster...", exc_info=True)
        return key

    def trans(
        self,
        context,
        key,
        *args
    ):
        self.log.debug("Context::Key   %s::%s", context, key)
        try:
            if self.log.level > logging.DEBUG:
                val = self.__LanguageDict.get(context,{}).get(key, key)
            else:
                val = self.__LanguageDict.get(context,{}).get(key, None)
                if val is None:
                    val = key
                    self.log.debug("Context::Key   %s::%s", context, key)
            if args:
                val = val % args
        except:
            self.log.critical("Major disaster...", exc_info=True)
        return val

    def trans_v01(
        self,
        context,
        key,
        *args
    ):
        self.log.debug("Context::Key   %s::%s", context, key)
        try:
            key = self.__LanguageDict.get(context,{}).get(key, key)
            if args:
                key = key % args
        except:
            self.log.critical("Major disaster...", exc_info=True)
        return key

def main():
    pass

if __name__ == '__main__':
    import sys
    sys.path.append(Path(__file__).parents[0])
    import fg_res
    res = Res()
    resx = Res()
    print (f"id(res)     {id(res)}\nid(resx)    {id(resx)}")
    print(__file__)
    main()
