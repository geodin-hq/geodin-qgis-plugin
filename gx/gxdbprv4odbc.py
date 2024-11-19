#-------------------------------------------------------------------------------
# Name:        Modul1
# Purpose:
#
# Author:      j.ebert
#
# Created:     25.07.2023
# Copyright:   (c) j.ebert 2023
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import pyodbc
from GeODinQGIS.gx.gxdbprv import *

class GxDbProvider4ODBC (GxDbProvider):
    """ abstract DbProvider for ODBC
    25.07.2023 j.ebert
    """
    def __init__(
        self,
        parent                  # Referenz auf GxDbConnection
    ):
        super().__init__(parent)

    def exists_Tbl(
        self,
        tblName
    ):
        self.log.log(gqc._LOG_TRACE,"\n%s\n", tblName)
        res = None
        with pyodbc.connect(self._CnnTag) as cnn:
            crs = cnn.cursor()
            res = crs.tables(table=tblName).fetchone()
        return res

    def load_Data(
        self,
        cmdText
    ):
        self.log.log(gqc._LOG_TRACE,"\n%s\n", cmdText)
        res = []
        with pyodbc.connect(self._CnnTag) as cnn:
            # conn.commit() will automatically be called when Python leaves the outer `with` statement
            # Neither crs.close() nor conn.close() will be called upon leaving the `with` statement!!
            # https://stackoverflow.com/questions/3783238/python-database-connection-close
            crs = cnn.cursor()
            crs.execute(cmdText)
            res = crs.fetchall()
        self.log.debug("\n%s", str(res))
        return res

    def validate(self):
        # ODBC Treiber prüfen...
        if not self._pyodbcDriver():
            raise gqb.GxSQLError("ODBC driver driver is not defined in %s", self.__class__.__name__)
        elif self._pyodbcDriver() not in pyodbc.drivers():
            # 64 Bit ODBC Treiber nicht gefunde/nicht installiert
            raise gqb.GxSQLError("ODBC driver '%s' not found", self._pyodbcDriver())
        return

    @classmethod
    def _pyodbcDriver(cls):
        return ""

class GxDbProvider4MSACC (GxDbProvider4ODBC):
    """
    25.07.2023 j.ebert
    """

    def connect(
        self,
        usr=None,               # database login user
        pwd=None                # database login password
    ):
        # seealso:
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Defining_Connection_(FireDAC)
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Connect_to_Microsoft_Access_Database_(FireDAC)
        self.log.log(gqc._LOG_TRACE, "")
        # Python-Modul und Treiber prüfen...
        # 07/2023 j.ebert, hier nicht notwendig
        #   GxDbProvider wird unmittelbar nach dem Instanzieren validiert/geprüft.
        try:
            # pyodbc-Connection-String erstellen
            cnnPrms = [
                "DRIVER={%s}" % self._pyodbcDriver(),
                "DBQ=%s" % self._Parent._CnnPrps['database']
            ]
            # Nutzer/Passwort für MSSQL nur analysieren/setzen, wenn
            if usr:
                # Wenn dieser Methode das Argumente 'usr' übergeben wurde,
                # dann Connection-Properties 'user_name' und 'password' setzen/überschreiben
                self._Parent._CnnPrps['user_name'] = usr
                self._Parent._CnnPrps['password'] = pwd
            if self._Parent._CnnPrps.get('user_name',''):
                cnnPrms += ["UID=%s" % self._Parent._CnnPrps['user_name']]
                if self._Parent._CnnPrps.get('password',''):
                    cnnPrms += ["PWD=%s" % self._Parent._CnnPrps['password']]
            cnnStr = ";".join(cnnPrms + [""])
            # Connection-Prps/Prms/Str loggen, aber mit "maskierten" Passwort(!!!)
            self.log.debug(
                "cnnPrps = %s\n\tcnnPrms = %s\n\tcnnStr = \"%s\"",
                re.sub(
                    "\"password\": \"\S+\"",
                    "\"password\": \"%s\"" % self.hiddenPwd(),
                    json.dumps(self._Parent._CnnPrps, indent=4).replace("\n", "\n\t"),
                    re.IGNORECASE
                ),
                re.sub(
                    "\"PWD=\S+\"",
                    "\"PWD=%s\";" % self.hiddenPwd(),
                    json.dumps(cnnPrms, indent=4).replace("\n", "\n\t"),
                    re.IGNORECASE
                ),
                re.sub(
                    "PWD=\S+;",
                    "PWD=%s;" % self.hiddenPwd(),
                    cnnStr,
                    re.IGNORECASE
                )
            )
            # pyodbc-Connection testen
            cnnObj = pyodbc.connect(cnnStr)
            cnnObj.close()
            self.log.info(
                "%s database '%s' could be connected successfully" , self.DriverID, self.DbName
            )
            self._Cnn = cnnObj
            self._CnnTag = cnnStr
        except pyodbc.Error:
            self.log.warning(
                "%s database '%s' could not be connected", self.DriverID, self.DbName,
                exc_info=True
            )
            raise gqb.GxSQLCnnError(
                "Failed to connect %s database '%s'", self.DriverID, self.DbName
            )
        return cnnObj

    @classmethod
    def _pyodbcDriver(cls):
        return "Microsoft Access Driver (*.mdb, *.accdb)"

class GxDbProvider4MSSQL (GxDbProvider4ODBC):
    """
    25.07.2023 j.ebert
    """

    def connect(
        self,
        usr="",                 # database login user
        pwd=""                  # database login password
    ):
        # seealso:
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Defining_Connection_(FireDAC)
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Connect_to_Microsoft_SQL_Server_(FireDAC)
        #
        #   https://learn.microsoft.com/en-us/sql/connect/python/pyodbc/step-3-proof-of-concept-connecting-to-sql-using-pyodbc?view=sql-server-ver16
        #   https://learn.microsoft.com/en-us/openspecs/sql_server_protocols/ms-odbcstr/6c134f58-30b6-48bd-be5b-ed3a8492d870?redirectedfrom=MSDN#Appendix_A_2
        #   https://stackoverflow.com/questions/53273146/python-pyodbc-connect-to-sql-server-using-sql-server-authentication
        self.log.log(gqc._LOG_TRACE, "")
        # Python-Modul und Treiber prüfen...
        # 07/2023 j.ebert, hier nicht notwendig
        #   GxDbProvider wird unmittelbar nach dem Instanzieren validiert/geprüft.
        try:
            # pyodbc-Connection-String erstellen
            cnnPrms = [
                "DRIVER={%s}" % self._pyodbcDriver(),
            ]
            if self._Parent._CnnPrps.get('database', ''):
                cnnPrms += ["DATABASE=%s" % self._Parent._CnnPrps['database']]
            if self._Parent._CnnPrps.get('server', ''):
                cnnPrms += ["SERVER=%s" % self._Parent._CnnPrps['server']]
            # 07/2023 j.ebert, Hinweis
            #   FireDAC-Connection-Parameter 'Port' nur für macOS, sonst
            #   alternativer Port in Parameter 'Server' mit Komma getrennt.
            #   (z. B. Server=SrvHost, 4000)
            if self._Parent._CnnPrps.get('osauthent', 'No').lower() == 'yes':
                # FireDAC Connection Parameter 'OSAuthent'
                cnnPrms += ["Trusted_Connection=Yes"]
                # 07/2023 j.ebert, Anmerkung zur pyodbc Connection(!)
                #   Wenn der Parameter 'Trusted_Connection' nicht auf No gesetzt ist
                #   dann werden die Parameter UID und PWD ignoriert
            else:
                # pyodbc Connection Parameter 'Trusted_Connection'
                #   Yes -- use Windows authentication. This is the default value.
                #   No  -- use DBMS authentication.
                # 07/2023 j.ebert, Fazit
                #   Parameter 'Trusted_Connection' muss hier zwingend auf No gesetzt werden.
                cnnPrms += ["Trusted_Connection=No"]
                # Nutzer/Passwort für MSSQL nur analysieren/setzen, wenn
                # Parameter Trusted_Connection auf No gesetzt ist
                if usr:
                    # Wenn dieser Methode das Argumente 'usr' übergeben wurde,
                    # dann Connection-Properties 'user_name' und 'password' setzen/überschreiben
                    self._Parent._CnnPrps['user_name'] = usr
                    self._Parent._CnnPrps['password'] = pwd
                if self._Parent._CnnPrps.get('user_name',''):
                    cnnPrms += ["UID=%s" % self._Parent._CnnPrps['user_name']]
                    if self._Parent._CnnPrps.get('password',''):
                        cnnPrms += ["PWD=%s" % self._Parent._CnnPrps['password']]
                else:
                    # 07/2023 j.ebert, Anmerkung (aus div. Tests)
                    #   Cnn-String mit "Trusted_Connection=No;"  reicht nicht aus und auch
                    #   Cnn-String mit "Trusted_Connection=No;UID=;" reicht nicht aus!
                    # Fazit:
                    #   Damit sicher keine OSAuthent genutzt wird muss der Benutzername im
                    #   Cnn-String enthalten sein.
                    #   Warnung protokollieren und mit GxSQLCnnError das Öffnen der gDB abbrechen.
                    # Hinweis:
                    #   Im ViewModel gibt es beim Öffnen eine GeODinDatenbank zwei Versuche:
                    #   - erster Versuch ohne Nutzereingabe - einfach drauf los/try and error
                    #   - zweiter Versuch mit Login-Abfrage, wenn der erste fehlgeschlagen ist
                    self.log.warning(
                        "Failed to connect %s database '%s'\n\t%s",
                        self._Parent.DriverID, self._Parent.DbName, "User name (UID) required!"
                    )
                    raise gqb.GxSQLCnnError(
                        "Failed to connect %s database '%s'",
                        self._Parent.DriverID, self._Parent.DbName
                    )
            cnnStr = ";".join(cnnPrms + [""])
            # Connection-Prps/Prms/Str loggen, aber mit "maskierten" Passwort(!!!)
            self.log.debug(
                "cnnPrps = %s\n\tcnnPrms = %s\n\tcnnStr = \"%s\"",
                re.sub(
                    "\"password\": \"\S+\"",
                    "\"password\": \"%s\"" % self.hiddenPwd(),
                    json.dumps(self._Parent._CnnPrps, indent=4).replace("\n", "\n\t"),
                    re.IGNORECASE
                ),
                re.sub(
                    "\"PWD=\S+\"",
                    "\"PWD=%s\";" % self.hiddenPwd(),
                    json.dumps(cnnPrms, indent=4).replace("\n", "\n\t"),
                    re.IGNORECASE
                ),
                re.sub(
                    "PWD=\S+;",
                    "PWD=%s;" % self.hiddenPwd(),
                    cnnStr,
                    re.IGNORECASE
                )
            )
            # pyodbc-Connection testen
            cnnObj = pyodbc.connect(cnnStr)
            cnnObj.close()
            self.log.debug(
                "%s database '%s' could be connected successfully" , self.DriverID, self.DbName
            )
            self._Cnn = cnnObj
            self._CnnTag = cnnStr
        except pyodbc.Error:
            self.log.warning(
                "%s database '%s' could not be connected", self.DriverID, self.DbName,
                exc_info=True
            )
            raise gqb.GxSQLCnnError(
                "Failed to connect %s database '%s'", self.DriverID, self.DbName
            )
        return cnnObj

    @classmethod
    def _pyodbcDriver(cls):
        return "SQL Server"

def main():
    pass

if __name__ == '__main__':
    main()
