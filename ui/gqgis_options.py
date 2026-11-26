r"""Options of GeoDinQGIS (10/2026)

GeoDin method after the tools 'Selection' and 'Hotlink' (menu at the toolbar buttons, arrow).

Functions:
    afterSelectionMode          - current mode of a tool (TOOL_SELECTION, TOOL_HOTLINK)
    setAfterSelectionMode       - saves the mode in the QGIS user settings
    runAfterSelection           - executes the GeoDin method of the current mode

Settings (QGIS user settings, QgsSettings):
    GeODinQGIS/afterSelection   - Selection: 'select' (default), 'graphic', 'section', 'siteplan'
    GeODinQGIS/afterHotlink     - Hotlink:   'select', 'objectdata' (default), 'graphic', 'mesdata'
    GeODinQGIS/selectionRadiusPx - Selection: selection radius in pixels (default 6, 11/2026)

GeoDin methods (COM ExecuteMethodParams, see GEODIN_COM.md):
    1, 'EditType=1'     object data (base editor)
    2                   print and edit graphics
    3                   measurement data editor
    5                   cross section wizard  (only at a node with several objects)
    6                   site plan             (only at a node with several objects)
"""
import logging

import qgis.core

import GeODinQGIS.gqgis_config as gqc
from GeODinQGIS import res
import GeODinQGIS.gx as gx

CONTEXT = "GQgis_Options"
log = logging.getLogger(f"{gqc._LOG_PARENTS}GQgis_Options")

TOOL_SELECTION = "selection"
TOOL_HOTLINK = "hotlink"

MODE_SELECT = "select"
MODE_OBJECT_DATA = "objectdata"
MODE_GRAPHIC = "graphic"
MODE_SECTION = "section"
MODE_SITE_PLAN = "siteplan"
MODE_MES_DATA = "mesdata"

TOOL_MODES = {
    TOOL_SELECTION: (MODE_SELECT, MODE_GRAPHIC, MODE_SECTION, MODE_SITE_PLAN),
    TOOL_HOTLINK: (MODE_SELECT, MODE_OBJECT_DATA, MODE_GRAPHIC, MODE_MES_DATA),
}
"""modes per tool in the order of the menu"""
TOOL_DEFAULT = {
    TOOL_SELECTION: MODE_SELECT,
    TOOL_HOTLINK: MODE_OBJECT_DATA,
}
_TOOL_KEY = {
    TOOL_SELECTION: "GeODinQGIS/afterSelection",
    TOOL_HOTLINK: "GeODinQGIS/afterHotlink",
}
MODE_TEXT = {
    MODE_SELECT: "Select object",
    MODE_OBJECT_DATA: "Open object data",
    MODE_GRAPHIC: "Print and edit graphics",
    MODE_SECTION: "Cross section",
    MODE_SITE_PLAN: "Site plan",
    MODE_MES_DATA: "Measurement data editor",
}
"""menu texts (translated in context 'GQgis_Act')"""
AFTER_SELECTION_TEXT = MODE_TEXT    # compatibility
MODE_METHOD = {
    MODE_OBJECT_DATA: (1, "EditType=1"),
    MODE_GRAPHIC: (2, ""),
    MODE_SECTION: (5, ""),
    MODE_SITE_PLAN: (6, ""),
    MODE_MES_DATA: (3, ""),
}
"""GeoDin method (MethodID, MethodParams) per mode"""

METHOD_CREATE_OBJECT = 39
"""GeoDin method ID 'Create object' (CMVUID_CreateNewObject), tested 10/2026 (GeoDin 15.6.32)"""


def _trans(key):
    return res.translate(CONTEXT, key)


def pushMessage(text, level="info", duration=6, tooltip=None, widgets=()):
    """message in the QGIS message bar with word wrap (10/2026)

    The standard messages (pushInfo/pushWarning) show the text in one line, it is cut off in
    a small QGIS window - here the text is a QLabel with word wrap.

    returns:
        item (QgsMessageBarItem) or None
    """
    try:
        import qgis.utils
        from qgis.PyQt import QtWidgets
        bar = qgis.utils.iface.messageBar()
        item = bar.createMessage("GeoDinQGIS", "")
        lbl = QtWidgets.QLabel(text)
        lbl.setWordWrap(True)
        lbl.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        lbl.setMinimumWidth(80)
        if tooltip:
            lbl.setToolTip(tooltip)
        item.layout().addWidget(lbl)
        for w in widgets:
            item.layout().addWidget(w)
        levels = {"info": "Info", "warning": "Warning", "critical": "Critical", "success": "Success"}
        name = levels.get(level, "Info")
        try:
            lvl = getattr(qgis.core.Qgis.MessageLevel, name)
        except AttributeError:
            lvl = getattr(qgis.core.Qgis, name)
        bar.pushWidget(item, lvl, duration)
        return item
    except Exception:
        log.debug("", exc_info=True)
        return None


SELECTION_RADIUS_KEY = "GeODinQGIS/selectionRadiusPx"
SELECTION_RADIUS_DEFAULT = 6
SELECTION_RADIUS_RANGE = (1, 50)
"""selection radius of the selection tool in pixels (11/2026)"""


def selectionRadiusPx():
    """selection radius of the selection tool in pixels (QGIS user settings, 11/2026)"""
    try:
        val = int(qgis.core.QgsSettings().value(SELECTION_RADIUS_KEY, SELECTION_RADIUS_DEFAULT))
    except (TypeError, ValueError):
        val = SELECTION_RADIUS_DEFAULT
    lo, hi = SELECTION_RADIUS_RANGE
    return min(max(val, lo), hi)


def setSelectionRadiusPx(px):
    lo, hi = SELECTION_RADIUS_RANGE
    px = min(max(int(px), lo), hi)
    qgis.core.QgsSettings().setValue(SELECTION_RADIUS_KEY, px)
    log.info("Selection radius of the selection tool: %d px", px)
    return px


def afterSelectionMode(tool=TOOL_SELECTION):
    """current mode of the tool"""
    val = qgis.core.QgsSettings().value(_TOOL_KEY[tool], TOOL_DEFAULT[tool])
    return val if val in TOOL_MODES[tool] else TOOL_DEFAULT[tool]


def setAfterSelectionMode(tool, mode):
    if mode not in TOOL_MODES[tool]:
        raise ValueError(f"unknown mode '{mode}' for tool '{tool}'")
    qgis.core.QgsSettings().setValue(_TOOL_KEY[tool], mode)
    log.info("GeoDin method after %s: %s", tool, mode)


def openObjectDataEnabled():
    """compatibility: True if the Hotlink tool opens the object data"""
    return afterSelectionMode(TOOL_HOTLINK) == MODE_OBJECT_DATA


def selectionMethod(tool=TOOL_SELECTION):
    """(MethodID, MethodParams) of the current mode, (-1, "") = select only"""
    return MODE_METHOD.get(afterSelectionMode(tool), (-1, ""))


def warnMethodFailed(tool, exc, logger=None):
    """warning in the QGIS message bar if the GeoDin method failed"""
    logger = logger or log
    mode = afterSelectionMode(tool)
    msg = exc.msg() if hasattr(exc, "msg") else str(exc)
    logger.warning("GeoDin method '%s' failed: %s", mode, msg, exc_info=True)
    try:
        import qgis.utils
        pushMessage(
            "%s (%s): %s" % (
                _trans("The GeoDin function could not be executed"),
                res.translate("GQgis_Act", MODE_TEXT.get(mode, mode)), msg
            ), "warning", 10
        )
    except Exception:
        pass


def runAfterSelection(tool=TOOL_SELECTION, logger=None):
    """executes the GeoDin method of the current mode at the node selected in GeoDin

    Errors are only shown in the QGIS message bar, because the object is already
    selected in GeoDin (Hotlink) or the selection was already created (Selection).
    """
    logger = logger or log
    mode = afterSelectionMode(tool)
    if mode not in MODE_METHOD:
        return False
    methodID, prms = MODE_METHOD[mode]
    try:
        gx.gApp.executeMethod(methodID, prms)
        return True
    except Exception as exc:
        msg = exc.msg() if hasattr(exc, "msg") else str(exc)
        logger.warning("GeoDin method '%s' (%d) failed: %s", mode, methodID, msg, exc_info=True)
        try:
            import qgis.utils
            pushMessage(
                "%s (%s): %s" % (
                    _trans("The GeoDin function could not be executed"),
                    res.translate("GQgis_Act", MODE_TEXT[mode]), msg
                ), "warning", 10
            )
        except Exception:
            pass
    return False
