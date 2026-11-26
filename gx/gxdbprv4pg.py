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
import psycopg2
from GeODinQGIS.gx.gxdbprv import *

class GxDbProvider4PG (GxDbProvider):
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
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Connect_to_PostgreSQL_%28FireDAC%29
        #
        #
        self.log.log(gqc._LOG_TRACE, "")
        # Python-Modul und Treiber prüfen...
        # 07/2023 j.ebert, hier nicht notwendig
        #   GxDbProvider wird unmittelbar nach dem Instanzieren validiert/geprüft.
        try:
##            connection = psycopg2.connect("dbname={0} user={1} host={2} password={3}".format(database.options["database"], database.options["uname"], database.options["ip"], database.options["upassword"]))

            # psycopg2-Connection-String erstellen
            cnnPrms = []
            if self._Parent._CnnPrps.get('server', ''):
                cnnPrms += ["host=%s" % self._Parent._CnnPrps['server']]
            if self._Parent._CnnPrps.get('port', ''):
                cnnPrms += ["port=%s" % self._Parent._CnnPrps['port']]
            if self._Parent._CnnPrps.get('database', ''):
                cnnPrms += ["dbname=%s" % self._Parent._CnnPrps['database']]
            # Nutzer/Passwort analysieren/setzen
            if usr:
                # Wenn dieser Methode das Argumente 'usr' übergeben wurde,
                # dann Connection-Properties 'user_name' und 'password' setzen/überschreiben
                self._Parent._CnnPrps['user_name'] = usr
                self._Parent._CnnPrps['password'] = pwd
            if self._Parent._CnnPrps.get('user_name',''):
                cnnPrms += ["user=%s" % self._Parent._CnnPrps['user_name']]
                if self._Parent._CnnPrps.get('password',''):
                    cnnPrms += ["password=%s" % self._Parent._CnnPrps['password']]
            cnnStr = " ".join(cnnPrms)
            # Connection-Prps/Prms/Str loggen, aber mit "maskierten" Passwort(!!!)
            self.log.debug(
                "cnnPrps = %s\n\tcnnPrms = %s\n\tcnnStr = \"%s\"",
                re.sub(
                    "\"password\": \"\\S+\"",
                    "\"password\": \"%s\"" % self.hiddenPwd(),
                    json.dumps(self._Parent._CnnPrps, indent=4).replace("\n", "\n\t"),
                    re.IGNORECASE
                ),
                re.sub(
                    "\"password=\\S+\"",
                    "\"password=%s\"" % self.hiddenPwd(),
                    json.dumps(cnnPrms, indent=4).replace("\n", "\n\t"),
                    re.IGNORECASE
                ),
                re.sub(
                    "password=\\S+",
                    "password=%s" % self.hiddenPwd(),
                    cnnStr,
                    re.IGNORECASE
                )
            )
            # psycopg2-Connection testen
            self.log.debug(cnnStr)
            cnnObj = psycopg2.connect(cnnStr)
            cnnObj.close()
            self.log.debug(
                "%s database '%s' could be connected successfully" , self.DriverID, self.DbName
            )
            self._Cnn = cnnObj
            self._CnnTag = cnnStr
        except:
            self.log.warning(
                "%s database '%s' could not be connected", self.DriverID, self.DbName,
                exc_info=True
            )
            raise gqb.GxSQLCnnError(
                "Failed to connect %s database '%s'", self.DriverID, self.DbName
            )
        return cnnObj

    def exists_Tbl(
        self,
        tblName
    ):
        self.log.log(gqc._LOG_TRACE,"\n%s\n", tblName)
        res = None
        with psycopg2.connect(self._CnnTag) as cnn:
            crs = cnn.cursor()
            res = False
            try:
                crs.execute(f"SELECT * FROM {tblName} WHERE 0=9")
                res = True
            except psycopg2.errors.UndefinedTable:
                pass
            except:
                raise
        return res

    def load_Data(
        self,
        cmdText
    ):
        """
        27.03.2024 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "\n%s\n", cmdText)
        res = []
        with psycopg2.connect(self._CnnTag) as cnn:
            # conn.commit() will automatically be called when Python leaves the outer `with` statement
            # Neither crs.close() nor conn.close() will be called upon leaving the `with` statement!!
            # https://stackoverflow.com/questions/3783238/python-database-connection-close
            crs = cnn.cursor()
            crs.execute(cmdText)
            res = crs.fetchall()
        self.log.log(gqc._LOG_DATA, "\n%s", str(res))
        return res

    def validate(self):
        # keine weitere Validierung notwendig
        return

def main():
    pass

if __name__ == '__main__':
    main()
