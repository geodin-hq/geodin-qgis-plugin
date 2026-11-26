r"""GeoDin system queries (11/2026)

Functions:
    readSystemQuery(path)       - reads the name and the group (LOC|INV) of a *.GSQ file
    systemQueries(folder)       - list of the system queries in <ProgramData>\QUERYDEF\

GeoDin shows the system queries ("Systemabfragen", *.GSQ files in <ProgramData>\QUERYDEF\
incl. subfolders, see GEODIN_DATA.md) in the GeoDin object manager (GOM) under every project
(node "Objects" or "Measurement points"). The files are binary (Delphi stream
'GeODin30-LOCMESQUERY'); only the name shown in the GOM and the tables are read here:

    <len><'GeODin30-LOCMESQUERY'> ... 02 01 <int32 byte length> <name UTF-16-LE> ...

Remarks:
    - the name in the file is the name in the GOM (not the file name)
    - conditions of a system query (LocType, DatType, ADOConnectionHas, Username) are not
      evaluated by the plugin; if GeoDin does not show a query in a project, selecting it fails
    - the place in the GOM is the setting "Requirements > Display conditions > Query beneath
      the object type" (property 0x01AE, first value, see LEVELS); the plugin offers only the
      levels that the COM function SelectObject can select (ParentNode ProjectQueries,
      DatabaseQueries): 3 - project queries, 1 - database queries
"""
import logging
import os
import struct
from pathlib import Path

import GeODinQGIS.gqgis_config as gqc

_SIGNATURE = b'GeODin30-LOCMESQUERY'
_log = logging.getLogger(f"{gqc._LOG_PARENTS}gx.sysquery")

# tables of measurement points (-> group INV), otherwise objects (-> group LOC)
_INV_TABLES = ('LOC_FILREG', 'LOC_PRBREG', 'MES_MESREG')

# "Query beneath the object type" (GeoDin query editor, Requirements > Display conditions)
LEVEL_DATABASE = 0
LEVEL_DATABASE_QUERIES = 1
LEVEL_PROJECT = 2
LEVEL_PROJECT_QUERIES = 3
LEVEL_OBJECT = 4
LEVEL_MESPOINT = 5
LEVELS = {
    LEVEL_DATABASE: "Database",
    LEVEL_DATABASE_QUERIES: "Database queries",
    LEVEL_PROJECT: "Project",
    LEVEL_PROJECT_QUERIES: "Project queries",
    LEVEL_OBJECT: "Object",
    LEVEL_MESPOINT: "Measurement point",
}
# property 0x01AE: 01 02 AE 01 <int32 count> 03 01 <level> ...
_LEVEL_TAG = b'\x01\x02\xae\x01'


def _readLevel(data, start):
    """returns the level (0..5, see LEVELS) or None if not found"""
    idx = data.find(_LEVEL_TAG, start)
    if idx < 0:
        return None
    pos = idx + len(_LEVEL_TAG) + 4
    if data[pos:pos + 2] != b'\x03\x01' or pos + 2 >= len(data):
        return None
    level = data[pos + 2]
    return level if level in LEVELS else None


def readSystemQuery(path):
    """reads a GeoDin system query file (*.GSQ)

    returns:
        dict {'Name': <name in the GOM>, 'Grp': 'LOC'|'INV', 'Level': 0..5|None, 'File': <path>}
        or None
    """
    try:
        data = Path(path).read_bytes()
    except OSError:
        _log.warning("System query '%s' could not be read", path, exc_info=True)
        return None
    pos = data.find(_SIGNATURE)
    if pos < 0:
        _log.warning("System query '%s': unknown format", path)
        return None
    pos += len(_SIGNATURE)
    name = ""
    # first string (02 01 <int32 length> <UTF-16-LE>) after the signature is the name
    idx = data.find(b'\x02\x01', pos)
    while 0 <= idx < pos + 64:
        try:
            size = struct.unpack_from('<i', data, idx + 2)[0]
            if 0 < size <= 1024 and size % 2 == 0:
                name = data[idx + 6: idx + 6 + size].decode('utf-16-le').strip()
                break
        except (struct.error, UnicodeDecodeError):
            pass
        idx = data.find(b'\x02\x01', idx + 1)
    if not name:
        name = Path(path).stem
        _log.warning("System query '%s': name not found, file name used", path)
    text = data.decode('utf-16-le', errors='ignore').upper()
    grp = 'INV' if any(tbl in text for tbl in _INV_TABLES) else 'LOC'
    level = _readLevel(data, pos)
    if level is None:
        _log.warning("System query '%s': display level not found", path)
    return {'Name': name, 'Grp': grp, 'Level': level, 'File': str(path)}


def systemQueries(folder):
    r"""returns the system queries (list of dict, see readSystemQuery) in folder and subfolders

    args:
        folder (str|Path)       - <ProgramData>\QUERYDEF\ of the GeoDin configuration
    """
    res = []
    if not folder or not os.path.isdir(folder):
        _log.info("No folder of system queries ('%s')", folder)
        return res
    for root, dirs, files in os.walk(folder):
        dirs.sort()
        for fileName in sorted(files):
            if fileName.upper().endswith('.GSQ'):
                qry = readSystemQuery(os.path.join(root, fileName))
                if qry:
                    res.append(qry)
    _log.info(
        "System queries in '%s': %s", folder,
        [(q['Name'], q['Grp'], LEVELS.get(q['Level'], q['Level'])) for q in res]
    )
    return res
