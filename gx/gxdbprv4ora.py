import oracledb
from GeODinQGIS.gx.gxdbprv import *

_ORA_TABLE_NOT_FOUND = 942


def _lobsAsValues(cursor, metadata):
    if metadata.type_code is oracledb.DB_TYPE_CLOB:
        return cursor.var(oracledb.DB_TYPE_LONG, arraysize=cursor.arraysize)
    if metadata.type_code is oracledb.DB_TYPE_NCLOB:
        return cursor.var(oracledb.DB_TYPE_LONG_NVARCHAR, arraysize=cursor.arraysize)
    if metadata.type_code is oracledb.DB_TYPE_BLOB:
        return cursor.var(oracledb.DB_TYPE_LONG_RAW, arraysize=cursor.arraysize)


class GxDbProvider4ORA (GxDbProvider):
    """DbProvider for Oracle (FireDAC DriverID Ora), python-oracledb in thin mode

    FireDAC parameter 'Database' is a TNS alias (tnsnames.ora via TNS_ADMIN),
    an Easy Connect string (host:port/service) or a full connect descriptor.
    """

    def connect(
        self,
        usr=None,               # database login user
        pwd=None                # database login password
    ):
        # seealso:
        #   https://docwiki.embarcadero.com/RADStudio/Sydney/en/Connect_to_Oracle_Server_(FireDAC)
        #   https://python-oracledb.readthedocs.io/en/latest/user_guide/connection_handling.html
        self.log.log(gqc._LOG_TRACE, "")
        if usr:
            self._Parent._CnnPrps['user_name'] = usr
            self._Parent._CnnPrps['password'] = pwd
        if not self._Parent._CnnPrps.get('user_name', ''):
            # python-oracledb thin mode supports no OS authentication (FireDAC OSAuthent):
            # without a user name the ViewModel asks for a login
            self.log.warning(
                "Failed to connect %s database '%s'\n\t%s",
                self.DriverID, self.DbName, "User name required!"
            )
            raise gqb.GxSQLCnnError("Failed to connect %s database '%s'", self.DriverID, self.DbName)
        cnnPrms = {
            'user': self._Parent._CnnPrps['user_name'],
            'password': self._Parent._CnnPrps.get('password', ''),
            'dsn': self._Parent._CnnPrps.get('database', ''),
        }
        self.log.debug("dsn = \"%s\", user = \"%s\"", cnnPrms['dsn'], cnnPrms['user'])
        try:
            cnnObj = oracledb.connect(**cnnPrms)
            cnnObj.close()
            self.log.debug(
                "%s database '%s' could be connected successfully", self.DriverID, self.DbName
            )
            self._Cnn = cnnObj
            self._CnnTag = cnnPrms
        except oracledb.Error:
            self.log.warning(
                "%s database '%s' could not be connected", self.DriverID, self.DbName,
                exc_info=True
            )
            raise gqb.GxSQLCnnError("Failed to connect %s database '%s'", self.DriverID, self.DbName)
        return cnnObj

    def exists_Tbl(
        self,
        tblName
    ):
        self.log.log(gqc._LOG_TRACE, "\n%s\n", tblName)
        with oracledb.connect(**self._CnnTag) as cnn:
            try:
                cnn.cursor().execute(f"SELECT * FROM {tblName} WHERE 0=9")  # nosec B608 - table names from the GeoDin configuration
            except oracledb.DatabaseError as exc:
                if exc.args[0].code == _ORA_TABLE_NOT_FOUND:
                    # Oracle reports a table without SELECT privilege as missing, too
                    self.log.info(
                        "Table '%s' does not exist or user '%s' has no SELECT privilege",
                        tblName, self._CnnTag['user']
                    )
                    return False
                raise
        return True

    def load_Data(
        self,
        cmdText
    ):
        self.log.log(gqc._LOG_TRACE, "\n%s\n", cmdText)
        with oracledb.connect(**self._CnnTag) as cnn:
            crs = cnn.cursor()
            crs.outputtypehandler = _lobsAsValues
            crs.execute(cmdText.strip())
            res = crs.fetchall()
        self.log.log(gqc._LOG_DATA, "\n%s", str(res))
        return res

    def validate(self):
        return
