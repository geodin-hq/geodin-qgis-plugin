r"""GeoDin COM server registration – user interface (10/2026)

Functions:
    ensureComRegistration       - checks the GeoDin COM server registration for a geodin.ini
                                  and offers to register the matching geodin.exe
    statusText                  - short status text for the DataDictionary dialog

See gx/comreg.py (GxComReg) for the rules and the registration itself.
"""
import logging

from qgis.PyQt import QtWidgets

import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gqgis_config as gqc
from GeODinQGIS import res
from GeODinQGIS.gx.comreg import GxComReg
from GeODinQGIS.ui.gqgis_bas import (
    busy,
    GQgis_MsgBox as MsgBox,
)

CONTEXT = "GQgis_ComReg"
log = logging.getLogger(f"{gqc._LOG_PARENTS}GQgis_ComReg")

_declined = set()
"""expected geodin.exe files for which the user declined the registration in this session"""


def trans(key):
    return res.translate(CONTEXT, key)


def statusText(result):
    """returns (level, text) for the DataDictionary dialog; level 'ok'|'warning'|'error'|'info'"""
    st = result['state']
    reg = result['registered'] or result['registered32']
    if st == GxComReg.OK:
        return 'ok', trans("GeoDin COM server registered: %s (%s)") % (reg, result['registered_version'])
    if st == GxComReg.UNKNOWN:
        return 'info', trans("No GeoDin application next to the geodin.ini (%s); registration not checked.") % result['expected']
    if not result['supported']:
        return 'error', trans("GeoDin version %s of %s is not supported.") % (result['expected_version'], result['expected'])
    if st == GxComReg.NOT_REGISTERED:
        return 'error', trans("GeoDin COM server is not registered.")
    if st == GxComReg.BOTH_BITS:
        return 'error', trans("GeoDin 64 bit and 32 bit are registered as COM server.")
    return 'warning', trans("Another GeoDin application is registered: %s (%s), expected: %s (%s)") % (
        reg, result['registered_version'], result['expected'], result['expected_version'])


def _problemText(result):
    return {
        GxComReg.NOT_REGISTERED: trans("The GeoDin COM server is not registered."),
        GxComReg.BOTH_BITS: trans("GeoDin 64 bit and 32 bit are registered as COM server."),
        GxComReg.WRONG_EXE: trans("Another GeoDin application is registered as COM server than the one of the chosen GeoDin configuration."),
    }.get(result['state'], "")


def _details(result):
    rows = [
        trans("Registered:") + " %s (%s)" % (result['registered'] or result['registered32'] or "-", result['registered_version']),
        trans("Matching the GeoDin configuration:") + " %s (%s)" % (result['expected'], result['expected_version']),
    ]
    return "\n".join(rows)


def _commandsText(result):
    txt = (trans("Commands to run as administrator (e.g. by IT):") + "\n\n" +
           "\n".join(GxComReg.commands(result)))
    restore = GxComReg.restore_commands(result)
    if restore:
        txt += ("\n\n" + trans("To restore the previous registration instead:") + "\n\n" +
                "\n".join(restore))
    return txt


def ensureComRegistration(parent, iniFile, onConnect=False, force=False):
    """checks the GeoDin COM server registration and offers to register the matching geodin.exe

    args:
        parent              - parent widget for the message boxes
        iniFile (str)       - geodin.ini (or its folder) of the current DataDictionary
        onConnect (bool)    - True, if called before connecting to GeoDin
                              (a declined registration is not offered again in this session)
        force (bool)        - True, if the user asked for the registration (button in the dialog)

    returns:
        result (dict|None)  - check result after the function (see GxComReg.check()),
                              None if the check failed
    """
    try:
        result = GxComReg.check(iniFile)
    except Exception:
        log.error("GeoDin COM server check failed", exc_info=True)
        return None
    if result['state'] in (GxComReg.OK, GxComReg.UNKNOWN):
        return result
    if onConnect and (result['expected'].lower() in _declined):
        log.warning("GeoDin COM server registration was declined before; connecting anyway")
        return result
    if not result['supported']:
        MsgBox.error(parent, 'GeoDin', statusText(result)[1])
        return result
    # GeoDin must not run while the COM server is registered again
    while result['running']:
        dlgRes = MsgBox.warning(
            parent, 'GeoDin',
            _problemText(result),
            _details(result) + "\n\n" + trans("Please close GeoDin first, then click Retry."),
            MsgBox.Retry | MsgBox.Cancel
        )
        if dlgRes != MsgBox.Retry:
            if onConnect:
                _declined.add(result['expected'].lower())
            return result
        result = GxComReg.check(iniFile)
        if result['state'] in (GxComReg.OK, GxComReg.UNKNOWN):
            return result
    # ask the user
    msg = MsgBox(parent)
    msg.setIcon(QtWidgets.QMessageBox.Icon.Question)
    msg.setText(_problemText(result))
    msg.setInformativeText(
        _details(result) + "\n\n" +
        trans("Register the matching GeoDin application as COM server now?\nAdministrator rights are required (Windows will ask for them).")
    )
    msg.setDetailedText(_commandsText(result))
    msg.setStandardButtons(MsgBox.Yes | MsgBox.No)
    msg.setDefaultButton(MsgBox.Yes)
    if msg.exec() != MsgBox.Yes:
        if onConnect:
            _declined.add(result['expected'].lower())
        log.info("GeoDin COM server registration declined by user")
        return result
    # register (UAC prompt)
    before = result
    try:
        # 10/2026: status dialog while the registration runs and becomes available
        with busy(parent, trans("The GeoDin COM server is being registered ...") + "\n\n" +
                  trans("Please confirm the Windows prompt for administrator rights.\nThe new registration may only be available after a short delay.")):
            result = GxComReg.register(result)
    except gqb.GQgisCanceldByUser:
        log.info("GeoDin COM server registration cancelled (UAC)")
        return result
    except gqb.GxException as exc:
        MsgBox.error(parent, 'GeoDin', exc.msg(), _commandsText(result))
        return result
    if result['state'] == GxComReg.OK:
        MsgBox.information(parent, 'GeoDin', trans("The GeoDin COM server was registered successfully."), _details(result))
    else:
        MsgBox.error(parent, 'GeoDin', trans("The GeoDin COM server could not be registered."),
                     _details(result) + "\n\n" + _commandsText(before))
    return result
