"""
Classes:
    GoGrpPrj                    - Data Model of GeODin project

17.04.2023 j.ebert
"""
import GeODinQGIS.gqgis_config as gqc
import json
from GeODinQGIS.dm.bas import (
    _JSON_DUMP_IDENT,
    GoBaseClass,
)

class GoGrpPrj(GoBaseClass):
    """Data Model Base Class

    17.04.2023 j.ebert
    """
    SQL_FldNames = """
    PRJ_ID, PRJ_NAME, PRJ_ALIAS, PRJ_TYPE, PRJ_OPT, PRJ_USER, PRJ_DATE, PRJ_PATH, GEODINGUID
    """
    SQL_FldIdxs = {}


    def __init__(
        self,
        dbRef,
        prjID,
        name
        ):
        super().__init__(dbRef, prjID, name)
        self.log.log(gqc._LOG_TRACE,"")
        self._PRJ_NAME = self._Name
        self._PRJ_ALIAS = ""
        self._PRJ_USER = ""
        self._PRJ_DATE = ""

    @property
    def CRef(self):
        """ corss reference

        06.06.2023 j.ebert
        """
        raise NotImplementedError(f"{self.__class__.__name__}.CRef is not implemented")
        return ""

    @property
    def DbRef(self):
        """returns GoDatabase object

        27.07.2023 j.ebert
        """
        return self._DbRef


    @property
    def Desc(self):
        """ description/classification

        06.06.2023 j.ebert
        """
        raise NotImplementedError(f"{self.__class__.__name__}.Desc is not implemented")
        return ""

    @property
    def Name(self):
        return self._Name

    @property
    def Info(self):
        """ info/ToolTip

        13.06.2023 j.ebert
        """
        info = f"{self._ADC_TYPE}: {self._ADC_FILE}".strip(' :')
        if self._error:
            info = "%s\n%s" % (info, self._error)
        return info

    @property
    def UID(self):
        """ unique identiyfyer

        06.06.2023 j.ebert
        """
        return ""

    def isDisabled(self):
        """True, if object is disabled, not error-free, ...

        09.06.2023 j.ebert
        """
        return bool(self._error)

    def validate(self):
        self._error = ""
        return not bool(self._error)

    @classmethod
    def fromSQL(
        cls,
        dbRef,
        data
    ):
        """
        27.07.2023 j.ebert
        """
        obj = cls(dbRef, data[cls.idxSQLFld('PRJ_ID')], data[cls.idxSQLFld('PRJ_NAME')])
        obj._tag = data
        obj._PRJ_ALIAS = data[cls.idxADCDATAFld('PRJ_ALIAS')]
        obj._PRJ_USER = data[cls.idxADCDATAFld('PRJ_USER')]
        obj._PRJ_DATE = data[cls.idxADCDATAFld('PRJ_DATE')]
        obj.validate()
        return obj

    @classmethod
    def idxSQLFld(
        cls,
        name
    ):
        """
        27.07.2023 j.ebert
        """
        if not cls.SQL_FldIdxs:
            fldNames = [item.strip().split('.')[1] for item in cls.SQL_FldNames.split(',')]
            cls.SQL_FldIdxs = {fld: idx for idx, fld in enumerate(fldNames)}
        return cls.SQL_FldIdxs.get(name)

    def to_json(self):
        """gibt ein mit JSON serialisierbares Objekt dieser Klasse zurück

        20.01.2023 j.ebert
        """
        return dict(self)

    @classmethod
    def from_json(
        cls,
        json_dct,               # JSON-Objekt (dict)
        dbRef=None              # Verweis auf GxDatabase-Objekt
        ):
        raise NotImplementedError(f"{cls.__name__}.from_json is not implemented")
        return

    def dumps(self):
        return json.dumps({self.__class__.__name__: self.to_json()}, indent=_JSON_DUMP_IDENT)

    def prmsSelectObject(
        self,
        mode='COM'
    ):
        raise NotImplementedError(f"{self.__class__.__name__}.prmsSelectObject is not implemented")
        return

    def __iter__(self):
        yield from {
            'PrjID': self._PrjID,
            'Name': self._Name,
            'Type': self._ADC_TYPE,
            'File': self._ADC_FILE
##            'InsUser': obj._InsUser,
##            'InsDate': obj._InsDate,
##            'UpdUser': obj._UpdUser,
##            'UpdDate': obj._UpdDate
        }.items()

def main():
    pass

if __name__ == '__main__':
    main()
