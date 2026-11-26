""" General framework

"""
__version__ = '0.1.0'
__author__ = 'J. Ebert'
__license__ = 'GPL-2.0-or-later'
__author_email__ = 'J.Ebert@fugro.com'
__maintainer_email__ = 'support@geodin.com'
__url__ = 'www.geodin.com'

# LogConfigurator importieren
# - initialisiert das Python Logging für die Anwendung
# - Default Logging Konfiguration wird in fg_logging.LogConfigurator.default_dictConfig() gesetzt
# - Default Logging wird jedoch mit fg_logging.LogConfigurator.load_jsonConfig() überladen
# - logging.json wird aus fg_logging.LogConfigurator.app_folder()/config geladen
#   08/2022 App Folder noch fix %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\GeODinQGIS
from .fg_logging import LogConfigurator

from .fg_env import Env
env = Env()
from .fg_res import Res
res = Res()