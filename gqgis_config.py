#-------------------------------------------------------------------------------
# Name:        Modul1
# Purpose:
#
# Author:      j.ebert
#
# Created:     28.03.2023
# Copyright:   (c) j.ebert 2023
# Licence:     <your licence>
#-------------------------------------------------------------------------------
__company__ = 'Fugro'
__product__ = 'GeODinQGIS'
__version__ = '4.0.2.2648'   # fallback, the version is read from metadata.txt (before: '3.0.2300.99')
__author__ = 'j.ebert'
__license__ = 'GPL-2.0-or-later'
__author_email__ = 'j.ebert@fugro.com'
__maintainer_email__ = 'support@geodin.com'
__url__ = 'www.geodin.com'

import configparser
import logging
from pathlib import Path

# load metadata of QGIS plugin...
_METADATA = configparser.ConfigParser()
"""GeODinQGIS plugin metadata (ConfigParser)"""
_METADATA.read(str(Path(__file__).parent / "metadata.txt"))
# overload globals with current GeODinQGIS plugin metadata
__product__ = _METADATA.get('general', 'name', fallback=__product__)
__version__ = _METADATA.get('general', 'version', fallback=__version__)
__maintainer_email__ = _METADATA.get('general', 'email', fallback=__maintainer_email__)
__url__ = _METADATA.get('general', 'homepage', fallback=__url__)

VERSION = __version__
PRODUCT = __product__

SUPPORT_MAIL_TO = __maintainer_email__
SUPPORT_MAIL_CC = __author_email__

GEODIN_STARTUP_DELAY_TIME = 3
"""GeODin Apllication/COM Server startup delay time (seconds)

Wenn GeODin Apllication/COM Server noch nicht ausgeführt wird,
dann ist nach dem Instanzieren des GeODin-COM-Objektes/-Servers in Python
eine Verzögerung des Aufrufs der ersten GeODin COM-Funktion notwendig.

Anmerkung
- 10 (oder auch 5) Sekunden - quick and dirty
  funktioniert mit GeODin 9.6.264.0 (Release Build: G2640722 vom 27.10.2022) (@FDE-3W6X493)
- deaktivieren durch Setzen auf 0

30.03.2023 j.ebert
"""


_LOG_TRACE = 5
"""Logging-Level für Einzelschritte/für den Programmablauf (kleiner als 10/logging.INFO)"""
_LOG_DATA = 9
"""Logging-Level für Daten/Listen (kleiner als 10/logging.INFO)"""

_LOG_GxCOM = 14
"""Logging-Level für GeODin COM Interface (insbesondere für Aufrufe der GeODin COM-Funktionen)"""

_LOG_GxSQL = 15
"""Logging-Level für SQL-Ditrektzugriff auf ein GeODin-Datenbank"""

_LOG_LEVEL = _LOG_TRACE
_LOG_LEVEL = logging.DEBUG
""" Logging-Level für GeODin QGIS Modul"""

_LOG_PARENTS = "GeODinQGIS."
""" Parents-Logger für GeODin QGIS Modul"""

GAPP_OPEN_BREAKTIME = 180
""" Timeout beim Starten/Verbinden mit GeODin (in Sekunden) """
GAPP_OPEN_SLEEPTIME = max(1, int(GAPP_OPEN_BREAKTIME / 3))
""" Wartezeit beim Starten/Verbinden mit GeODin (in Sekunden) """


from GeODinQGIS.fw.fg_logging import (
    LogFilterByLevel,
    zipLogFiles as fw_zipLogFiles
)

class LogFilterCOM(LogFilterByLevel):
    """Logging Filter to filter GxCOM-Level

    17.08.2023 j.ebert
    """

    def __init__(self):
        super().__init__(_LOG_GxCOM)


class LogFilterSQL(LogFilterByLevel):
    """Logging Filter to filter GxSQL-Level

    17.08.2023 j.ebert
    """

    def __init__(self):
        super().__init__(_LOG_GxSQL)


class LogFilterTRACE(LogFilterByLevel):
    """Logging Filter to filter TRACE-Logs

    21.08.2023 j.ebert
    """

    def __init__(self):
        super().__init__(_LOG_TRACE)


def zipLogFiles(
    zipName=""
):
    prefix = _LOG_PARENTS.rstrip(".")
    return fw_zipLogFiles(prefix, zipName)

def main():
    pass

if __name__ == '__main__':
     main()
