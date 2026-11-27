#-------------------------------------------------------------------------------
# Name:        Modul1
# Purpose:
#
# Author:      j.ebert
#
# Created:     21.03.2023
# Copyright:   (c) j.ebert 2023
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import logging

from GeODinQGIS.fw import res

class GQgisException(Exception):
    """ GeODinQGIS BaseExpetion

    29.03.2023 j.ebert
    """

    def msg(self):
        if not self.args:
            txt = self.__class__.__name__
        else:
            txt = self.args[0]
            # 10/2026: message (format string) translated in context 'GQgisException'
            try:
                if isinstance(txt, str):
                    txt = res.translate("GQgisException", txt)
            except Exception:
                logging.getLogger(__name__).debug("message not translated: %s", txt, exc_info=True)
            if len(self.args) > 1:
                txt = txt % self.args[1:]
        return txt

class GQgisCanceldByUser(GQgisException):
    """is raised if action was canceld by user

    29.03.2023 j.ebert
    """

class GQgisBreak(GQgisException):
    """is raised to abort an action without error handling

    29.03.2023 j.ebert
    """

class GxDDXException(GQgisException):
    """BaseException of DataDictionary (DDX)

    19.04.2023 j.ebert
    """

class GxException(GQgisException):
    """is raised if undefined error occurs (also BaseException)

    29.03.2023 j.ebert
    """

class GxFileError(GxException):
    """is raised if an error occurs when loading a file

    19.04.2023 j.ebert
    """

class GxBadFileError(GxFileError):
    """is raised if an error occurs when loading a file

    19.04.2023 j.ebert
    """


class GxAppFolderError(GxException):
    """is raised if Applictionfolder itself or file geodin.ini not found

    22.03.2023 j.ebert
    """

class GxGAppError(GxException):
    """is raised in case of a GeODin application error (not installed, not found, ...)

    27.03.2023 j.ebert
    """

class GxGAppRestartRequiredError(GxGAppError):
    """is raised if the GeODin application has to be restarted

    27.03.2023 j.ebert
    """

class GxAppNotFoundError(GxException):
    """is raised if GeODin applicationn not found

    21.03.2023 j.ebert
    """

class GxAppNotInstalledError(GxException):
    """is raised if GeODin application is not installed

    21.03.2023 j.ebert
    """

class GxAppIsRunningError(GxException):
    """is raised if the GeODin application is already running with a different configuration

    21.03.2023 j.ebert
    """

class GxDMError(GxException):
    """is raised when a function in the GeODin Plugin data model fails

    11.08.2023 j.ebert
    """

class GxGComError(GxException):
    """is raised in case of a GeODin COM error

    30.05.2023 j.ebert
    """

class GxGComCnnError(GxGComError):
    """is raised in case of a GeODin COM connection error

    27.03.2023 j.ebert
    """

class GxGComException(GxGComError):
    """is raised in case of a GeODin COM Exception

    30.05.2023 j.ebert
    """

class GxGAppBusyError(GxGComError):
    """is raised if GeoDin is busy (modal dialog open or a method that cannot be left) (10/2026)

    The COM call is not executed (modal dialog) or was refused by GeoDin.
    """

class GxGComResError(GxGComError):
    """is raised in case of a GeODin COM Exception

    30.05.2023 j.ebert
    """

class GxSQLError(GxException):
    """is raised in case of a GxSQL error

    13.07..2023 j.ebert
    """

class GxSQLCnnError(GxSQLError):
    """is raised in case of a GxSQL connection error

    13.07.2023 j.ebert
    """

class GxToolError(GxSQLError):
    """is raised in tools (Hotlink, Seelection)

    11.08.2023 j.ebert
    """




def main():
    pass

if __name__ == '__main__':
    main()
