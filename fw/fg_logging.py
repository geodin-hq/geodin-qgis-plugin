""" General methods for configuring logging

"""
__version__ = '0.1.0'
__author__ = 'J. Ebert'
__license__ = 'GPL-2.0-or-later'
__author_email__ = 'J.Ebert@fugro.com'
__maintainer_email__ = 'support@geodin.com'
__url__ = 'www.geodin.com'

_company = 'Fugro'
_product = 'GeODinQGIS'
_py_file = __file__

import json
import logging
import logging.config
import logging.handlers
import os
from pathlib import Path
import re
import traceback
import zipfile

class LogConfigurator:
    """ Class with methods for configuring logging
    """
    @classmethod
    def default_dictConfig(cls):
        """ default logging dictConfig

        19.08.2022 J.Ebert
        """
        # Log folder (vom Typ pathlib.Path)
        log_folder = cls.log_folder()
        # default logging coniguration
        log_config = {
            'version':1,
            'disable_existing_loggers': False,
        ##    "root":{
        ##        "handlers" : ["hdl_console"],
        ##        "level": "DEBUG"
        ##    },
            "loggers": {
                "GeODinQGIS" : {
                    "handlers" : ["hdl_console"],
##                    "level": "DEBUG",
                    "level": "NOTSET",
                    "propagate":False
                    }
                },
            "handlers":{
                "hdl_console":{
                    "formatter": "std_out",
                    "class": "logging.StreamHandler",
##                    "level": "DEBUG",
                    "level": "NOTSET",
                }
            },
            "formatters":{
                "std_out": {
                    "format": "%(asctime)s.%(msecs)03d %(levelname)-8s : %(module)s : %(funcName)s : %(lineno)d : (Process Details : (%(process)d, %(processName)s), Thread Details : (%(thread)d, %(threadName)s))\n\t%(message)s",
        ##            "datefmt":"%d-%m-%Y %I:%M:%S"
                    "datefmt":"%I:%M:%S"
                }
            }
            }
        return log_config

    @classmethod
    def load_jsonConfig(
            cls
        ):
        """loads JSON-File with logging dictConfig

        19.08.2022 J.Ebert
        """
        dictConfig = None
        try:
            # akt. JSON-File mit Logging dictConfig laden
            cfg_file = cls.cfg_folder() / 'logging.json'
            with open(cfg_file, 'rt') as f:
                dictConfig = json.load(f)
            print(str(cls.cfg_folder() / 'logging.json'))
        except:
            # Wenn das Laden eine Exception verursacht hat,
            # dann das Default JSON-File aus dem AppFolder laden
            cfg_file = cls.app_folder() / 'config' / 'logging.json'
            with open(cfg_file, 'rt') as f:
                dictConfig = json.load(f)
            print(str(cls.app_folder() / 'config' / 'logging.json'))
        finally:
            # Log-Folder im dictConfig aktualisieren...
            for key, hdls in dictConfig.items():
                if key.lower() == 'handlers':
                    for hdl_name, prms in hdls.items():
                        for prm_name, val in prms.items():
                            if prm_name.lower() == 'filename':
                                # {.., 'handlers': {<hdl_name>: {.., 'filename': <val>, ..}}, ..}, ..}
##                                print(key, hdl_name, prm_name, val)
                                prms[prm_name] = cls.replace_env(val)
            print(json.dumps(dictConfig,indent=4))
        return dictConfig

    @classmethod
    def log_folder(cls):
        """ log folder

        Retruns:
            log_folder (Path)   - Log Folder <LOCALAPPDATA>/<Company>/<Product>/Logs

        19.08.2022 J.Ebert
        """
        # Wenn die Systemvariable LOCALAPPDATA nicht existiert,
        # dann wird der Benutzerordner/das Benutzerverzeichnis auf dem Computer genutzt
        log_folder = Path(os.getenv('LOCALAPPDATA', Path.home()), _company, _product, "Logs")
        log_folder.mkdir(parents=True, exist_ok=True)
        return log_folder

    @classmethod
    def app_folder(cls):
        """ app folder

        If __file__  is             <any Path>/<Py Package>/fw/fg_logging.py
        then app_folder() returns   <any Path>/<Py Package>

        Returns:
            app_folder (Path)   - App Folder

        19.08.2022 J.Ebert
        """
##        return Path(__file__).parents[1]
        return Path(_py_file).parents[1]

    @classmethod
    def cfg_folder(cls):
        """ config folder

        Returns:
            cfg_folder (Path>   - Config Folder <App Folder>/config

        19.08.2022 J.Ebert
        """
        # Mit der Umgebungsvariable <Product>_CONFIG_DIR kann
		# der default Config Folder <App Folder>/config übersteuert werden.
        config_dir = os.getenv(f"{_product.upper()}_CONFIG_DIR", str(cls.app_folder() / 'config'))
        print(f"{_product.upper()}_CONFIG_DIR", config_dir)
        return Path(config_dir)

    @classmethod
    def replace_env(
            cls,
            val
        ):
        """ ersetzt Systemvariablen im String/Parameter val

        Im String/Parameter val werden Systemvariablen gesucht und ersetzt, wenn sie definiert sind.
        Systemvariablen müssen in einem % Zeichenpaar eingeschlossen sein - %<Systemvariable>%.
        Der Namen einer Systemvariable darf nur Buchstaben, Ziffern und Unterstrich enthalten.
        Die Systemvariablen werden im internen Default Dict und auf Systemebene in Großschreibung
        abgefragt/gesucht. Systemvariablen auf Systemebene haben Priorität und überladen ggf. den
        Wert aus dem internen Default Dict.

        Args:
            val (str)       - Zeichenkette, in der Systemvariablen ersetzt werden

        Returns:
            new_val (str)   - neue Zeichenkette mit ersetzten Systemvariablen

        22.08.2022 J.Ebert
        """
        # Initialsierung....
        # - Zeichenkette, die innerhalb der Funktion bearbeitet wird
        new_val = val
        # - Default Dict, mit Default Werten der Systemvariablen
        #   Achtung
        #       - Namen der Systemvariablen/Dict Key immer in Großschreibung
        #       - Werte aus Default Dict werden ggf. durch Systemvariablen überschrieben.
        default_env = {
                'GEODINQGIS_LOG_FOLDER': str(cls.log_folder())
            }
        # - Regex-Object zur Analyse der Systemvariablen in der Zeichenkette
        #   Systemvariable - %<Name (nur Bustaben, Ziffern und Unterstrich erlaubt)>%
        env_Regex = re.compile(r"""(
            %               # Trennzeichen/Kennzeichen Beginn der Systemvariable
            (\w+)           # Name der Systemvariable [a-zA-Z0-9_]
            %               # Trennzeichen/Kennzeichen Ende der Systemvariable
            )""", re.IGNORECASE | re.VERBOSE)
        # Systemvariablen in val/in der Zeichenkette suchen und ersetzen...
        env_MObjs = env_Regex.findall(new_val)
        for grps in env_MObjs:
            # Gruppen/grps sind von der Reg. Expression abhängig - sieh oben (%(\w+)%)
            env_val = grps[0]           # Systemvariable inkl. Trennzeichen am Abfang und Ende
                                        # ist der Teilstring, der ersetzt wird
            env_key = grps[1].upper()   # Name der Systemvariable (in Großschreibung!)
                                        # über der im Default Dict oder auf dem System defniert ist
##            print('replace_env ', env_key, '-', env_val)
            # Name der Systemvariable im Default Dict suchen
            env_val = default_env.get(env_key, env_val)
            # Name der Systemvariable auf Systemebene suchen, damit
            # wird ggf. der Wert aus dem Default Dict überschrieben
            env_val = os.getenv(env_key, env_val)
##            print('replace_env ', grps[0], '-', env_val)
            # Systemvariable (inkl. Trennzeichen) durch deren Wert ersetzen,
            # wenn die Systemvariable im Default Dict oder/und auf Systemebene gefunden wurde, also
            # wenn der Wert nicht mehr gleich der Systemvariable (inkl. Trennzeichen) ist
            if grps[0] != env_val:
                # Achtung
                #   Das Ersetzen von Systemvariablen insbesondere mit Verzeichnissen/Pfadangaben
                #   ist mit Regex nicht trivial, weil Pfadangaben Zeichen enthalten, die in Regex
                #   zu maskieren sind. Folgende Zeichen haben in Regex eine besondere Bedeutng
                #       ^ * + \ { } [ ] \ | ( )
                new_val = new_val.replace(grps[0], env_val)
##        print('replace_env\n\t', val, '\n\t', new_val)
        return new_val

    @classmethod
    def make_log_folders(
        cls,
        dictConfig
        ):
        """ erstellt Log-Folder, die im dictConfig enthalten sind

        23.09.2022 J.Ebert
        """
        # Log-Folder im dictConfig aktualisieren...
        for key, hdls in dictConfig.items():
            if key.lower() == 'handlers':
                for hdl_name, prms in hdls.items():
                    for prm_name, val in prms.items():
                        if prm_name.lower() == 'filename':
                            # {.., 'handlers': {<hdl_name>: {.., 'filename': <val>, ..}}, ..}, ..}
                            try:
                                log_file = Path(val)
                                log_file.parent.mkdir(parents=True, exist_ok=True)
                            except:
                                pass
        return
    @classmethod
    def config(cls):
        dictConfig = cls.load_jsonConfig()
        cls.make_log_folders(dictConfig)
        logging.config.dictConfig(dictConfig)
        cls.mask_passwords()
        return

    @classmethod
    def mask_passwords(cls):
        loggers = [logging.getLogger()] + [
            lgr for lgr in logging.Logger.manager.loggerDict.values() if isinstance(lgr, logging.Logger)
        ]
        for lgr in loggers:
            for hdl in lgr.handlers:
                if not isinstance(hdl.formatter, LogFormatterMasked):
                    hdl.setFormatter(LogFormatterMasked(hdl.formatter or logging.Formatter()))


_MASK = '*****'
_PASSWORD_PATTERNS = [
    (re.compile(r'''\b(\w*(?:password|pwd)\s*=\s*)(?:\{[^}]*\}|[^;'"\r\n]*)''', re.IGNORECASE), rf'\g<1>{_MASK}'),
    (re.compile(r'''(["']\w*(?:password|pwd)\w*["']\s*:\s*)"(?:[^"\\]|\\.)*"''', re.IGNORECASE), rf'\g<1>"{_MASK}"'),
    (re.compile(r'''(["']\w*(?:password|pwd)\w*["']\s*:\s*)'(?:[^'\\]|\\.)*\'''', re.IGNORECASE), rf"\g<1>'{_MASK}'"),
    (re.compile(r'''(\w+://[^:/\s@]+:)[^@\s/]+(?=@)'''), rf'\g<1>{_MASK}'),
]


def maskPasswords(text):
    for pattern, replacement in _PASSWORD_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class LogFormatterMasked(logging.Formatter):
    """replaces passwords (connection strings, JSON and dict values) in every formatted log record"""

    def __init__(self, formatter):
        super().__init__()
        self._formatter = formatter

    def format(self, record):
        return maskPasswords(self._formatter.format(record))

class LogFilterByLevel(logging.Filter):
    """Logging filer by Level number

    17.08.2023 j.ebert
    """

    def __init__(self, levelNo=None):
        self.__level = levelNo if isinstance(levelNo, int) else None

    def filter(self, logRecord):
        return (self.__level is None) or (logRecord.levelno == self.__level)

class LogFormatterTrace(logging.Formatter):

##    def format(self, record: logging.LogRecord) -> str:
    def format(self, record):
##        stack_lines = traceback.format_stack()
##        stack_lines_without_logging_intermediary_calls = list(filter(
##            lambda line: (
##                ("lib/logging/__init__.py" not in line[0]) and
##                ("lib\\logging\\__init__.py" not in line[0])
##            ),
##            stack_lines[:-1]
##        ))
##        msg = "\n\t%s" % "\n\t".join(stack_lines_without_logging_intermediary_calls[-4])
##        if len(stack_lines_without_logging_intermediary_calls) > 1:
##            record.msg += " (Z %4d in %s)" % (
##                stack_lines_without_logging_intermediary_calls[-2][1],
##                stack_lines_without_logging_intermediary_calls[-2][0]
##            )
##        return "Test LogFormatterTrace"
##        record.msg = "Stack %3d -> %3d %s" % (
##            len(stack_lines), len(stack_lines_without_logging_intermediary_calls), msg
##        )

        stack_rows = traceback.extract_stack()
        stack_rows_without_logging_intermediary_calls = list(filter(
            lambda row: (
                ("lib/logging/__init__.py" not in row[0]) and
                ("lib\\logging\\__init__.py" not in row[0])
            ),
            stack_rows
        ))
##        msg = "\n\t%s" % "\n\t".join([str(row) for row in stack_rows_without_logging_intermediary_calls[-4:]])

##        msg = "LogFormatterTrace"
        idx = -3
        msg = stack_rows_without_logging_intermediary_calls[idx][2]
        if len(stack_rows_without_logging_intermediary_calls) > 1:
            msg += " (Z %5d in %s)\n\t%s" % (
                stack_rows_without_logging_intermediary_calls[idx - 1][1],
                stack_rows_without_logging_intermediary_calls[idx - 1][0],
                "\n\t".join([str(row) for row in stack_rows_without_logging_intermediary_calls])
            )
        record.msg = "Stack %3d -> %3d %s" % (
            len(stack_rows), len(stack_rows_without_logging_intermediary_calls), msg
        )
        return super(LogFormatterTrace, self).format(record)
##        return record.msg + "\nOrigin :\n" + "".join(stack_lines_without_logging_intermediary_calls)
        # beware of : https://stackoverflow.com/q/8162419/11384184

def listLogFiles(
    prefix=""
):
    assert isinstance(prefix, str)
    logfiles = []
    for name in [
        name for name in logging.root.manager.loggerDict if name.startswith(prefix)
    ]:
        log = logging.getLogger(name)
        logfiles += [
            h.stream.name for h in log.handlers if isinstance(h, logging.FileHandler)
        ]
    return logfiles

def listLogFolders(
    prefix=""
):
    assert isinstance(prefix, str)
    return list(set([Path(name).parent for name in listLogFiles(prefix)]))

def zipLogFiles(
    prefix="",
    zipName=""
):
    assert isinstance(prefix, str)
    assert isinstance(zipName, (str, Path)) and bool(zipName)
##    zipName = "GeODinQGIS_logs_%s.zip" % datetime.datetime.now().strftime("%y%m%d%H%M%S")
##    zipName = Path(r"C:\Data\GeODinQGIS\temp") / zipName
    with zipfile.ZipFile(zipName, "w") as zipFile:
        for name in [Path(name) for name in listLogFiles(prefix) if Path(name).exists()]:
            for log in [log for log in name.parent.glob(name.stem + '*')]:
                zipFile.write(log)
    return str(zipName)



if __name__ == '__main__':
    import sys
    sys.path.append(Path(__file__).parents[0])
    import fg_logging
