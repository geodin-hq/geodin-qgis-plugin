# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeODinQGIS
                                 A QGIS plugin
 This plugin connects GeODin with QGIS
                             -------------------
        begin                : 2015-02-16
        copyright            : (C) 2021 by Fugro Germany Land GmbH
        email                : www.fugro.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
__version__ = '4.1.1.2648'   # 10/2026 (before: '3.0.22xx'), the plugin version is in metadata.txt
__license__ = 'GPL-2.0-or-later'
__maintainer_email__ = 'support@geodin.com'
__url__ = 'www.geodin.com'
import logging
##from fw.fg_logging import LogConfigurator
##LogConfigurator.config()

import importlib.util
import sys


def _missing_requirement():
    if sys.platform != 'win32':
        return 'GeoDinQGIS requires Windows and GeoDin.'
    if importlib.util.find_spec('win32com') is None:
        return ('GeoDinQGIS requires the Python package pywin32: run "python -m pip install pywin32" '
                'in the OSGeo4W Shell as administrator, then restart QGIS.')
    return None


_MISSING_REQUIREMENT = _missing_requirement()

if _MISSING_REQUIREMENT is None:
    from pathlib import Path  # noqa: F401 - re-export
    # Achtung, Reihenfolge beachten!!!
    #   1a) fw.fg_env und fw.fg_res importieren
    #   1b) globals env und res instanziieren
    #   2a) gqgis_app importieren
    #   2b) globlas app instanziieren
    from GeODinQGIS.fw.fg_logging import (  # noqa: F401 - re-export
        LogFormatterTrace
    )
    from GeODinQGIS.gqgis_config import (  # noqa: F401 - re-export
        LogFilterCOM,
        LogFilterSQL,
        LogFilterTRACE
    )
    from .fw import (  # noqa: F401 - re-export
        env,
        res
    )
    from .gqgis_app import GQgis_App
    app = GQgis_App()

from qgis import utils


class _UnavailablePlugin:
    def __init__(self, iface, message):
        self._iface = iface
        self._message = message

    def initGui(self):
        self._iface.messageBar().pushCritical('GeoDinQGIS', self._message)

    def unload(self):
        pass


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GeODinQGIS class from file GeODinQGIS.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    if _MISSING_REQUIREMENT is not None:
        return _UnavailablePlugin(iface, _MISSING_REQUIREMENT)
    from .fw import LogConfigurator
    LogConfigurator.config()
    log = logging.getLogger('GeODinQGIS')
    log.info('GeoDinQGIS load')

##    from .GeODinQGIS import GeODinQGIS
##    return GeODinQGIS(iface)
    from .gqgis import GQgis
    return GQgis(iface)

def name():
    """Plugin name

    27.04.2023 j.ebert
    """
    # __file__      <QGIS_PLUGINPATH>/<Plugin/Modul>/__init__.py
    # __name__                        <Plugin/Modul>
    return __name__

def plugin():
    """Plugin instance

    exception:
        KeyError                if GeODinQGIS Plugin ist not installed

    27.04.2023 j.ebert
    """
    # __file__      <QGIS_PLUGINPATH>/<Plugin/Modul>/__init__.py
    # __name__                        <Plugin/Modul>
    return utils.plugins[__name__]
