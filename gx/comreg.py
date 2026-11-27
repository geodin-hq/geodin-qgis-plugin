r"""GeoDin COM server registration (10/2026)

Classes:
    GxComReg                    - checks and repairs the registration of the GeoDin COM server

The GeoDinQGIS plugin starts GeoDin as COM server (ProgID 'geodin.GeODinApplication').
Windows starts the geodin.exe that is registered for this ProgID. This module checks
whether the registered geodin.exe belongs to the GeoDin configuration (geodin.ini) chosen
in the DataDictionary and, if not, registers the matching geodin.exe.

Rule (GeoDin installation layout):
    <folder>\\geodin.ini        GeoDin configuration chosen in the DataDictionary
    <folder>\\Bin\\geodin.exe    GeoDin application that belongs to this configuration

Registration needs administrator rights (UAC prompt):
    "<new geodin.exe>" /regserver       registers the GeoDin application of the configuration;
                                        it overwrites the registration of another 64 bit geodin.exe
                                        (same ClassID), so that one is NOT unregistered first
    "<32 bit geodin.exe>" /unregserver  only if a (different) 32 bit GeoDin is registered as well

Network drives: mapped drive letters (e.g. I:) are not available in a process that runs with
administrator rights, so paths on mapped drives are converted to UNC paths (\\server\share\...).
"""
import contextlib
import logging
import os
import re
import winreg
from pathlib import Path

import GeODinQGIS.gqgis_base as gqb
import GeODinQGIS.gqgis_config as gqc
from GeODinQGIS.gx.system import GxReg


class GxComReg:
    """checks and repairs the registration of the GeoDin COM server

    10/2026
    """
    log = logging.getLogger(f"{gqc._LOG_PARENTS}GxComReg")

    PROG_ID = "geodin.GeODinApplication"
    CLSID = "{44A32582-B618-11D4-8601-00E0293462B8}"
    """GeoDin ClassID (identical for GeoDin 8 ... 15, see GxReg._query_prog_prps())"""
    MIN_VERSION = (9,)
    """minimum GeoDin version supported by the plugin (see GeoDin.assert_gApp())"""

    # check results (key 'state')
    OK = "ok"                           # registered geodin.exe belongs to the configuration
    NOT_REGISTERED = "not_registered"   # GeoDin COM server is not registered
    WRONG_EXE = "wrong_exe"             # another geodin.exe is registered
    BOTH_BITS = "both_bits"             # GeoDin 64 bit and 32 bit are registered
    UNKNOWN = "unknown"                 # no geodin.exe next to the configuration -> no check

    # ------------------------------------------------------------------------------------------
    # registry / file information
    # ------------------------------------------------------------------------------------------
    @classmethod
    def _exe_from_command(cls, command):
        """returns the exe path of a LocalServer32 command line (without quotes and arguments)"""
        command = (command or "").strip()
        if not command:
            return ""
        if command.startswith('"'):
            return command[1:].split('"', 1)[0]
        match = re.match(r'(.+?\.exe)\b', command, re.IGNORECASE)
        return match.group(1) if match else command

    @classmethod
    def _query_localserver(cls, access):
        """returns the registered geodin.exe for one registry view (64 or 32 bit)"""
        clsid = cls._query(winreg.HKEY_CLASSES_ROOT, f"{cls.PROG_ID}\\Clsid", "", "") or cls.CLSID
        command = cls._query(
            winreg.HKEY_CLASSES_ROOT, f"CLSID\\{clsid}\\LocalServer32", "", "", access
        )
        return cls._exe_from_command(command)

    @classmethod
    def _query(cls, root, keyname, valname="", default=None, access=0):
        try:
            with winreg.OpenKey(root, keyname, 0, winreg.KEY_READ | access) as key:
                return winreg.QueryValueEx(key, valname)[0]
        except OSError:
            return default

    @classmethod
    def registered_exes(cls):
        """returns the registered geodin.exe files (64 bit, 32 bit); empty string if missing"""
        return (
            cls._query_localserver(winreg.KEY_WOW64_64KEY),
            cls._query_localserver(winreg.KEY_WOW64_32KEY),
        )

    @classmethod
    def expected_exe(cls, iniFile):
        """returns the geodin.exe that belongs to a geodin.ini (<folder>\\Bin\\geodin.exe)

        args:
            iniFile (str|Path)  - geodin.ini or the folder that contains the geodin.ini
        """
        path = Path(iniFile)
        folder = path.parent if path.suffix.lower() == ".ini" else path
        return str(folder / "Bin" / "geodin.exe")

    @classmethod
    def version(cls, exe):
        """returns the file version of an exe as tuple, or None"""
        if exe and Path(exe).is_file():
            return GxReg.get_FileVersion(str(exe))
        return None

    @classmethod
    def version_text(cls, exe):
        ver = cls.version(exe)
        return ".".join(str(v) for v in ver) if ver else "-"

    @classmethod
    def is_running(cls):
        """True, if a geodin.exe process is running (all sessions, like tasklist)"""
        import pywintypes
        import win32ts
        try:
            processes = win32ts.WTSEnumerateProcesses(win32ts.WTS_CURRENT_SERVER_HANDLE, 1, 0)
            return any(name.lower() == "geodin.exe" for _sid, _pid, name, _user in processes)
        except pywintypes.error:
            cls.log.debug("process list failed", exc_info=True)
            # fall back to the GeoDin registry value 'System\\Handle'
            return bool(GxReg.query_Handle())

    @classmethod
    def _same(cls, a, b):
        return bool(a) and bool(b) and (
            os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))
        )

    # ------------------------------------------------------------------------------------------
    # check
    # ------------------------------------------------------------------------------------------
    @classmethod
    def check(cls, iniFile, with_running=True):
        """checks the GeoDin COM server registration against a geodin.ini

        args:
            iniFile (str)       - geodin.ini chosen in the DataDictionary (or its folder)

        returns:
            result (dict)
                state               - OK | NOT_REGISTERED | WRONG_EXE | BOTH_BITS | UNKNOWN
                registered          - registered geodin.exe (64 bit) or ""
                registered32        - registered geodin.exe (32 bit) or ""
                registered_version  - version text of the registered geodin.exe
                expected            - geodin.exe that belongs to the geodin.ini
                expected_exists     - True, if the expected geodin.exe exists
                expected_version    - version text of the expected geodin.exe
                supported           - True, if the expected geodin.exe has a supported version
                running             - True, if a GeoDin application is running
                                      (only checked if with_running is True)
                old                 - registered geodin.exe files to unregister (existing files)
        """
        reg64, reg32 = cls.registered_exes()
        expected = cls.expected_exe(iniFile) if iniFile else ""
        expVer = cls.version(expected)
        res = {
            'registered': reg64,
            'registered32': reg32,
            'registered_version': cls.version_text(reg64 or reg32),
            'expected': expected,
            'expected_exists': bool(expected) and Path(expected).is_file(),
            'expected_version': cls.version_text(expected),
            'supported': bool(expVer) and expVer >= cls.MIN_VERSION,
            'running': cls.is_running() if with_running else False,
            'ini': iniFile,
        }
        if not res['expected_exists']:
            # no GeoDin installation next to the geodin.ini (e.g. a central configuration)
            res['state'] = cls.UNKNOWN
        elif not (reg64 or reg32):
            res['state'] = cls.NOT_REGISTERED
        elif reg32 and not cls._same(reg32, reg64):
            res['state'] = cls.BOTH_BITS
        elif not cls._same(reg64, expected):
            res['state'] = cls.WRONG_EXE
        else:
            res['state'] = cls.OK
        # 10/2026: only a different 32 bit registration is removed before the registration;
        #   a 64 bit registration of another geodin.exe is overwritten by /regserver
        #   (unregistering it first would leave GeoDin unregistered if /regserver fails)
        res['old'] = [
            exe for exe in [reg32]
            if exe and not cls._same(exe, expected) and not cls._same(exe, reg64) and Path(exe).is_file()
        ]
        cls.log.info(
            "GeoDin COM server check: %s\n\tregistered  %s (%s)\n\tregistered32 %s\n\texpected    %s (%s)\n\trunning     %s",
            res['state'], reg64 or "-", res['registered_version'], reg32 or "-",
            expected or "-", res['expected_version'], res['running']
        )
        return res

    @classmethod
    def to_unc(cls, path):
        """returns the UNC path for a path on a mapped network drive, otherwise the path itself

        Mapped drive letters are not available in a process with administrator rights.
        """
        path = str(path)
        if re.match(r'^[A-Za-z]:', path):
            import pywintypes
            import win32wnet
            with contextlib.suppress(pywintypes.error):
                remote = win32wnet.WNetGetConnection(path[:2])
                if remote:
                    return remote.rstrip('\\') + path[2:]
        return path

    @classmethod
    def commands(cls, result):
        """returns the command lines for the (re-)registration (to run as administrator)"""
        cmds = [f'"{cls.to_unc(exe)}" /unregserver' for exe in result.get('old', [])]
        cmds.append(f'"{cls.to_unc(result["expected"])}" /regserver')
        return cmds

    @classmethod
    def restore_commands(cls, result):
        """returns the command line to restore the previous registration (if known)"""
        prev = result.get('registered') or result.get('registered32')
        if prev and not cls._same(prev, result.get('expected')):
            return [f'"{cls.to_unc(prev)}" /regserver']
        return []

    # ------------------------------------------------------------------------------------------
    # registration
    # ------------------------------------------------------------------------------------------
    @classmethod
    def register(cls, result, timeout=120, settle=15):
        """registers the geodin.exe that belongs to the geodin.ini (needs administrator rights)

        All commands run in ONE elevated cmd.exe, so Windows shows only one UAC prompt.

        args:
            result (dict)       - result of GxComReg.check()
        returns:
            result (dict)       - new check result after the registration
        exceptions:
            GQgisCanceldByUser  if the UAC prompt was cancelled
            GxGAppError         if the registration could not be executed
        """
        import pywintypes
        import win32con
        import win32event
        import win32process
        from win32com.shell import shell, shellcon

        if not result.get('expected_exists'):
            raise gqb.GxGAppError("GeoDin application not found\n%s", result.get('expected', ""))
        # 10/2026: only run the commands if the new geodin.exe is reachable for the elevated
        #   process (exit code 2 otherwise), so an existing registration is never removed for nothing
        newExe = cls.to_unc(result['expected'])
        params = (
            '/s /c "if not exist "' + newExe + '" (exit /b 2) else (' +
            " & ".join(cls.commands(result)) + ')"'
        )
        cls.log.info("Register GeoDin COM server (elevated): cmd.exe %s", params)
        try:
            info = shell.ShellExecuteEx(
                fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                lpVerb="runas",
                lpFile="cmd.exe",
                lpParameters=params,
                nShow=win32con.SW_HIDE,
            )
        except pywintypes.error as exc:
            if exc.winerror == 1223:            # ERROR_CANCELLED: UAC prompt cancelled
                raise gqb.GQgisCanceldByUser("Registration cancelled by user")
            raise gqb.GxGAppError("GeoDin COM server could not be registered\n%s", exc.strerror)
        hProcess = info['hProcess']
        try:
            # 10/2026: wait in small steps, so a status dialog stays responsive
            waited = 0.0
            while win32event.WaitForSingleObject(hProcess, 100) != win32event.WAIT_OBJECT_0:
                waited += 0.1
                cls._pump()
                if waited > timeout:
                    raise gqb.GxGAppError("Registration of the GeoDin COM server did not finish")
            exitCode = win32process.GetExitCodeProcess(hProcess)
            cls.log.info("Registration finished (exit code %s)", exitCode)
        finally:
            hProcess.Close()
        if exitCode == 2:
            raise gqb.GxGAppError(
                "GeoDin application not reachable with administrator rights\n%s", newExe
            )
        # cached registry values of GxReg are no longer valid
        for attr in ('_prog_clsid', '_prog_path', '_prog_path_key64', '_prog_path_key32'):
            if hasattr(GxReg, attr):
                delattr(GxReg, attr)
        # 10/2026: check again with the geodin.ini (not with the geodin.exe); Windows may need
        #   a moment until the new registration is visible, so check for up to 'settle' seconds
        res = cls.check(result['ini'])
        waited = 0.0
        while res['state'] != cls.OK and waited < settle:
            cls._pump(1.0)
            waited += 1.0
            res = cls.check(result['ini'])
        return res

    @classmethod
    def _pump(cls, seconds=0.0):
        """keeps the QGIS user interface responsive (status dialog) while waiting"""
        try:
            from GeODinQGIS.ui.gqgis_bas import qsleep
            qsleep(seconds)
        except Exception:
            import time
            time.sleep(seconds)
