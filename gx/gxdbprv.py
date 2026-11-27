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
import logging

import GeODinQGIS.gqgis_config as gqc

class GxDbProvider:
    """ abstract DbProvider

    25.07.2023 j.ebert
    """

    def __init__(
        self,
        parent                  # Referenz auf GxDbConnection
    ):
        self.log = logging.getLogger(f"{gqc._LOG_PARENTS}{self.__class__.__name__}")
        self._context = "gx"    # Context für Transaltion/Übersetzung vom Modul gx
        self._Parent = parent
        """reference to GxDbConnection"""
        self._Cnn = None
        """instance of database connection"""
        self._CnnTag = None
        """tag (instance or string) for managing the connection through derived DbProvider"""

    @property
    def DbName(self):
        return self._Parent.DbName

    @property
    def DriverID(self):
        return self._Parent.DriverID

    def open(
        self,
        usr=None,               # database login user
        pwd=None                # database login password
    ):
        raise NotImplementedError()

    def connect(
        self,
        usr=None,               # database login user
        pwd=None                # database login password
    ):
        raise NotImplementedError()

    def exists_Tbl(
        self,
        tblName
    ):
        raise NotImplementedError()

    def load_Data(
        self,
        cmdText
    ):
        raise NotImplementedError()

    def validate(self):
        raise NotImplementedError()


def main():
    pass

if __name__ == '__main__':
    main()
