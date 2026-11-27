r"""Support e-mail with GeoDinQGIS logs and system information (10/2026)

Functions:
    createSupportMail           - asks which files to include, creates the support ZIP and
                                  opens a new e-mail (Outlook with attachment, else mailto)

Classes:
    GQgis_Dlg_Support           - dialog: contents of the support ZIP

The ZIP is saved in <LocalAppData>\Support (not in the temporary folder of the QGIS session,
which is deleted when QGIS is closed) and contains:
    - GeoDinQGIS logs (always)
    - GeoDinQGIS_info.txt       system information (as in 'About GeoDinQGIS')    [default on]
    - GeoDinQGIS_comreg.txt     state of the GeoDin COM server registration       [default on]
    - <ddx>.gddx                current DataDictionary                            [optional]
    - geodin.ini                GeoDin configuration (may contain passwords!)     [optional]

E-mail:
    The default e-mail program is used:
    - classic Outlook: an unsent e-mail (*.eml, X-Unsent: 1) with recipients, subject, text and
      the ZIP attached is opened with 'outlook.exe /eml'; the user checks and sends it.
    - other programs (e.g. new Outlook for Windows): mailto with recipients, subject and text;
      the ZIP has to be attached by hand (it is selected in the Windows Explorer).
    (No COM automation: Outlook did not answer the COM calls and QGIS froze.) Without (classic) Outlook a mailto e-mail is opened
    (no attachments possible) and the folder with the ZIP is shown in the Windows Explorer.
"""
import datetime
import logging
import platform
import urllib.parse
import webbrowser
import zipfile

import win32api
import win32con
from pathlib import Path

from qgis.PyQt import (
    QtCore,
    QtGui,
    QtWidgets
)

import GeODinQGIS.gqgis_config as gqc
from GeODinQGIS import (
    env,
    res
)
from GeODinQGIS.ui.gqgis_bas import (
    cursor,
    GQgis_Bas_Widget,
    GQgis_MsgBox as MsgBox
)

CONTEXT = "GQgis_Support"
log = logging.getLogger(f"{gqc._LOG_PARENTS}GQgis_Support")

_MAILTO_MAX = 1800
"""maximum length of a mailto URL (Windows/mail programs truncate longer URLs)"""


def trans(key):
    return res.translate(CONTEXT, key)


# -------------------------------------------------------------------------------------- dialog
class GQgis_Dlg_Support(QtWidgets.QDialog):
    """dialog: which files are included in the support ZIP

    10/2026
    """

    def __init__(self, parent=None, ddxFile="", iniFile=""):
        super().__init__(parent)
        self.setWindowTitle(trans("GeoDinQGIS - Support request"))
        self.setWindowIcon(GQgis_Bas_Widget.QIcon("GenericMail"))
        self.setMinimumWidth(520)
        lay = QtWidgets.QVBoxLayout(self)
        lbl = QtWidgets.QLabel(trans(
            "A ZIP file for the GeoDin support is created and attached to a new e-mail.\n"
            "Please choose what it should contain:"))
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        self.chkLogs = QtWidgets.QCheckBox(trans("GeoDinQGIS logs"))
        self.chkLogs.setChecked(True)
        self.chkLogs.setEnabled(False)
        self.chkInfo = QtWidgets.QCheckBox(trans("System information (as in 'About GeoDinQGIS')"))
        self.chkInfo.setChecked(True)
        self.chkCom = QtWidgets.QCheckBox(trans("State of the GeoDin COM server registration"))
        self.chkCom.setChecked(True)
        self.chkDDX = QtWidgets.QCheckBox(trans("Current DataDictionary (DDX file)") +
                                          (f"  –  {Path(ddxFile).name}" if ddxFile else ""))
        self.chkDDX.setChecked(False)
        self.chkDDX.setEnabled(bool(ddxFile) and Path(ddxFile).exists())
        self.chkIni = QtWidgets.QCheckBox(trans("GeoDin configuration (geodin.ini)"))
        self.chkIni.setChecked(False)
        self.chkIni.setEnabled(bool(iniFile) and Path(iniFile).exists())
        for chk in (self.chkLogs, self.chkInfo, self.chkCom, self.chkDDX, self.chkIni):
            lay.addWidget(chk)
        note = QtWidgets.QLabel(trans(
            "Note: the geodin.ini can contain connection data and passwords of the databases. "
            "Only include it if the support asks for it."))
        note.setWordWrap(True)
        note.setStyleSheet("color: #9a6700;")
        lay.addWidget(note)
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        btns.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText(trans("Create e-mail"))
        btns.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setText(trans("Cancel"))
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def options(self):
        return {
            'info': self.chkInfo.isChecked(),
            'com': self.chkCom.isChecked(),
            'ddx': self.chkDDX.isChecked() and self.chkDDX.isEnabled(),
            'ini': self.chkIni.isChecked() and self.chkIni.isEnabled(),
        }


class GQgis_Dlg_NoMailProgram(QtWidgets.QDialog):
    """dialog: no e-mail program - support address and ZIP file with copy buttons

    10/2026
    """

    def __init__(self, parent, to, zipFile):
        super().__init__(parent)
        self.setWindowTitle(trans("GeoDinQGIS - Support request"))
        self.setWindowIcon(GQgis_Bas_Widget.QIcon("GenericMail"))
        self.setMinimumWidth(720)
        lay = QtWidgets.QVBoxLayout(self)
        lbl = QtWidgets.QLabel(trans(
            "No e-mail program was found.\n"
            "Please send the ZIP file and a detailed description of the problem to the GeoDin support:"))
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel(trans("E-mail:")), 0, 0)
        self._addCopyRow(grid, 0, to)
        grid.addWidget(QtWidgets.QLabel(trans("ZIP file:")), 1, 0)
        self._addCopyRow(grid, 1, str(zipFile))
        btnFolder = QtWidgets.QPushButton(trans("Show in folder"))
        btnFolder.clicked.connect(lambda: _showFile(zipFile))
        grid.addWidget(btnFolder, 2, 1, 1, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
        lay.addLayout(grid)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        btns.accepted.connect(self.accept)
        lay.addWidget(btns)

    @staticmethod
    def _copyIcon():
        from qgis.core import QgsApplication
        icon = QgsApplication.getThemeIcon("mActionEditCopy.svg")
        return None if icon.isNull() else icon

    def _addCopyRow(self, grid, row, text):
        edit = QtWidgets.QLineEdit(text)
        edit.setReadOnly(True)
        edit.setCursorPosition(0)
        grid.addWidget(edit, row, 1)
        btn = QtWidgets.QToolButton()
        icon = self._copyIcon()
        if icon is not None:
            btn.setIcon(icon)
        else:
            btn.setText(trans("Copy"))
        btn.setToolTip(trans("Copy to clipboard"))
        btn.clicked.connect(lambda checked=False, t=text: QtWidgets.QApplication.clipboard().setText(t))
        grid.addWidget(btn, row, 2)


# ------------------------------------------------------------------------------------ contents
def _iniFile(app):
    """geodin.ini of the current DDX ('' if unknown)"""
    try:
        conf = str(app.DDXConf or "")
        if conf and Path(conf).exists():
            return conf
        if app.GAppFolder:
            ini = Path(app.GAppFolder) / "geodin.ini"
            if ini.exists():
                return str(ini)
    except Exception:
        log.debug("", exc_info=True)
    return ""


def _comState(app):
    """returns (short text, detail text) of the GeoDin COM server registration"""
    try:
        from GeODinQGIS.gx.comreg import GxComReg
        from GeODinQGIS.ui import gqgis_comreg as comreg
        ini = _iniFile(app) or app.GAppFolder
        result = GxComReg.check(ini, with_running=True)
        level, text = comreg.statusText(result)
        details = "\n".join([
            text,
            "",
            comreg._details(result),
            "state: %s, supported: %s, running: %s" % (
                result.get('state'), result.get('supported'), result.get('running')),
            "geodin.ini: %s" % (ini or "-"),
        ])
        return text, details
    except Exception as exc:
        log.debug("", exc_info=True)
        return f"unknown ({exc})", f"COM check failed: {exc}"


def _summary(app, comText):
    """short system summary for the e-mail text"""
    from qgis.core import Qgis
    rows = [
        "GeoDinQGIS: %s" % app.Version,
        "QGIS: %s" % Qgis.QGIS_VERSION,
    ]
    rows.append("Qt: %s, Python: %s" % (QtCore.QT_VERSION_STR, platform.python_version()))
    rows.append("Windows: %s" % platform.platform())
    rows.append("GeoDin COM server: %s" % comText)
    rows.append("DDX: %s" % (app.DDXFile or "-"))
    rows.append("Language: %s (%s)" % (res.LanguageCode, getattr(res, 'LanguageMode', '')))
    return "\n".join(rows)


def _createZip(app, opts):
    """creates the support ZIP and returns (zip path, list of contents)"""
    folder = Path(env.LocalAppData) / "Support"
    folder.mkdir(parents=True, exist_ok=True)
    zipName = folder / ("GeoDinQGIS_support_%s.zip" % datetime.datetime.now().strftime("%y%m%d%H%M%S"))
    # logs (same as before, see gqc.zipLogFiles)
    gqc.zipLogFiles(zipName)
    contents = [trans("GeoDinQGIS logs")]
    comText, comDetails = _comState(app) if opts.get('com') else ("", "")
    with zipfile.ZipFile(zipName, "a", compression=zipfile.ZIP_DEFLATED) as zf:
        if opts.get('info'):
            try:
                zf.writestr("GeoDinQGIS_info.txt", app.InfoText())
            except Exception as exc:
                zf.writestr("GeoDinQGIS_info.txt", f"InfoText failed: {exc}")
            contents.append("GeoDinQGIS_info.txt")
        if opts.get('com'):
            zf.writestr("GeoDinQGIS_comreg.txt", comDetails)
            contents.append("GeoDinQGIS_comreg.txt")
        if opts.get('ddx') and app.DDXFile and Path(app.DDXFile).exists():
            zf.write(app.DDXFile, Path(app.DDXFile).name)
            contents.append(Path(app.DDXFile).name)
        ini = _iniFile(app)
        if opts.get('ini') and ini:
            zf.write(ini, Path(ini).name)
            contents.append(Path(ini).name)
    return str(zipName), contents, comText


def _mailBody(app, zipFile, contents, comText):
    return "\n".join([
        trans("Please describe the problem:"),
        "", "", "",
        trans("Steps to reproduce the problem:"),
        "", "", "",
        "--- " + trans("System information") + " ---",
        _summary(app, comText or "-"),
        "",
        trans("Attachment:") + " %s" % Path(zipFile).name,
        "    " + ", ".join(contents),
    ])


# ---------------------------------------------------------------------------------------- mail
def _outlookExe():
    """returns outlook.exe of the classic Outlook ('' if not installed)

    'App Paths' only exists for the classic Outlook (the new Outlook for Windows is olk.exe).
    """
    try:
        import winreg
        key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\OUTLOOK.EXE"
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(root, key) as hKey:
                    exe = winreg.QueryValue(hKey, None)
                if exe and Path(exe.strip('"')).exists():
                    return exe.strip('"')
            except OSError:
                continue
    except Exception:
        log.debug("", exc_info=True)
    return ""


def _defaultMailProgId():
    """returns the ProgId of the default e-mail program (mailto handler), '' if unknown"""
    try:
        import winreg
        key = r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\mailto\UserChoice"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as hKey:
            return str(winreg.QueryValueEx(hKey, "ProgId")[0])
    except Exception:
        return ""


def _isClassicOutlookDefault():
    """True if the classic Outlook is the default e-mail program (ProgId 'Outlook.URL.mailto.*')"""
    return _defaultMailProgId().lower().startswith("outlook.url.mailto")


def _writeEml(to, subject, body, zipFile):
    """writes an unsent e-mail (*.eml, header X-Unsent: 1) with the ZIP attached"""
    from email.message import EmailMessage
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg["X-Unsent"] = "1"                   # opens as new e-mail (draft), not as received mail
    msg.set_content(body)
    with open(zipFile, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="zip",
                           filename=Path(zipFile).name)
    emlFile = Path(zipFile).with_suffix(".eml")
    with open(emlFile, "wb") as f:
        from email import policy
        f.write(msg.as_bytes(policy=policy.SMTP))     # CRLF line endings
    return emlFile


def _sendOutlook(parent, to, subject, body, zipFile):
    """opens a new e-mail with the ZIP attached in the classic Outlook

    Only if the classic Outlook is the default e-mail program: an unsent e-mail (*.eml with
    X-Unsent: 1, recipients, subject, text, ZIP attached) is opened with 'outlook.exe /eml'.
    Otherwise (e.g. new Outlook for Windows, which has neither COM nor command line switches
    for attachments) the default e-mail program is opened via mailto (see _sendMailto).

    10/2026 history: 1. Outlook COM (pywin32) - QGIS froze, Outlook did not answer the COM calls;
                     2. outlook.exe /m ... /a ... - /m only accepts recipients (subject/body ended
                        up in the address) and it always started the classic Outlook.

    returns:
        'ok'        - classic Outlook started with the e-mail
        'error'     - classic Outlook is not the default e-mail program / could not be started
    """
    progId = _defaultMailProgId()
    if not _isClassicOutlookDefault():
        log.info("Default e-mail program '%s' (not classic Outlook), mailto is used", progId)
        return 'error'
    exe = _outlookExe()
    if not exe:
        log.info("Classic Outlook not found, mailto is used")
        return 'error'
    try:
        emlFile = _writeEml(to, subject, body, zipFile)
        log.debug("Outlook: %s /eml %s", exe, emlFile)
        win32api.ShellExecute(0, "open", exe, f'/eml "{emlFile}"', None, win32con.SW_SHOWNORMAL)
        return 'ok'
    except Exception:
        log.info("Outlook could not be started, mailto is used", exc_info=True)
        return 'error'


def _copyFileToClipboard(zipFile):
    """copies the ZIP as file to the clipboard (as 'Copy' in the Windows Explorer)

    In the e-mail (e.g. new Outlook) Ctrl+V attaches the file.
    10/2026
    """
    try:
        from qgis.PyQt import QtGui
        mime = QtCore.QMimeData()
        mime.setUrls([QtCore.QUrl.fromLocalFile(str(zipFile))])
        QtGui.QGuiApplication.clipboard().setMimeData(mime)
        return True
    except Exception:
        log.debug("", exc_info=True)
        return False


def _showFile(zipFile):
    """shows the ZIP in the Windows Explorer"""
    try:
        win32api.ShellExecute(0, "open", "explorer.exe", f'/select,"{zipFile}"', None, win32con.SW_SHOWNORMAL)
    except win32api.error:
        log.debug("", exc_info=True)


def _hasMailtoHandler():
    """True if an e-mail program is registered for mailto (user choice or system default)"""
    if _defaultMailProgId():
        return True
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"mailto\shell\open\command") as hKey:
            return bool(winreg.QueryValue(hKey, ""))
    except Exception:
        return False


def _sendMailto(to, subject, body, zipFile):
    """opens a mailto e-mail (without attachment) and shows the ZIP in the Windows Explorer

    10/2026: the ZIP is also copied to the clipboard -> Ctrl+V in the e-mail attaches it
    """
    inClipboard = _copyFileToClipboard(zipFile)
    hint = trans("Please attach the following zip file with GeoDinQGIS logs:")
    if inClipboard:
        hint = (trans("The ZIP file is in the clipboard: click into the e-mail and press Ctrl+V to attach it.") + "\n" +
                trans("Alternatively, you can attach the following ZIP file manually:"))
    body = body + "\n\n" + hint + "\n" + str(zipFile)
    body = body.replace("\r\n", "\n").replace("\n", "\r\n")   # CRLF for the e-mail programs
    query = {"subject": subject, "body": body}
    url = "mailto:%s?%s" % (to, urllib.parse.urlencode(query, quote_via=urllib.parse.quote))
    if len(url) > _MAILTO_MAX:
        # mail programs truncate long mailto URLs -> short text, details are in the ZIP
        query["body"] = (trans("Please describe the problem:") + "\n\n\n" +
                         trans("Please attach the following zip file with GeoDinQGIS logs:") + "\n" + str(zipFile))
        url = "mailto:%s?%s" % (to, urllib.parse.urlencode(query, quote_via=urllib.parse.quote))
    # 10/2026: no e-mail program -> no Windows 'choose an app' prompt, but a dialog with the
    #   support address and the ZIP file (copy buttons); returns False in this case
    opened = False
    if _hasMailtoHandler():
        opened = QtGui.QDesktopServices.openUrl(QtCore.QUrl(url, QtCore.QUrl.ParsingMode.StrictMode))
        if not opened:
            log.info("mailto could not be opened: %s", url[:200])
    _showFile(zipFile)
    return opened


def createSupportMail(parent=None):
    """asks for the contents, creates the support ZIP and opens a new e-mail

    10/2026
    """
    from GeODinQGIS import app
    ddxFile = str(app.DDXFile or "")
    dlg = GQgis_Dlg_Support(parent, ddxFile, _iniFile(app))
    if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
        return
    try:
        with cursor(QtCore.Qt.CursorShape.WaitCursor):
            zipFile, contents, comText = _createZip(app, dlg.options())
            to = gqc.SUPPORT_MAIL_TO
            subject = "GeoDinQGIS Support (GeoDinQGIS %s)" % app.Version
            body = _mailBody(app, zipFile, contents, comText)
        state = _sendOutlook(parent, to, subject, body, zipFile)
        if state != 'ok':
            if _sendMailto(to, subject, body, zipFile):
                state = 'mailto'
            else:
                state = 'no e-mail program'
                GQgis_Dlg_NoMailProgram(parent, to, zipFile).exec()
        log.info("Support e-mail created (%s, %s)", zipFile, state)
    except Exception:
        log.error("Support e-mail could not be created", exc_info=True)
        MsgBox.error(parent, "GeoDinQGIS", trans("The support e-mail could not be created."))
    return
