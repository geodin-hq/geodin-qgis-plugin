"""
Classes:
    GoBaseClass                 - Data Model Base Class

Functions:
    default()

17.04.2023 j.ebert
"""
import datetime
import hashlib
import json
import logging
import os
import time
import traceback
from pathlib import Path

import GeODinQGIS.gqgis_config as gqc
import GeODinQGIS.gx as gx
from GeODinQGIS import res


_JSON_DUMP_IDENT = 4

def default(obj):
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

class GoBaseClass:
    """Data Model Base Class

    17.04.2023 j.ebert
    """
    def __init__(
        self,
        dbRef,
        prjID,
        name
        ):
        self.log  = logging.getLogger(f"{gqc._LOG_PARENTS}{self.__class__.__name__}")
        self.log.log(gqc._LOG_TRACE,"")
        self._context = "dm"
        self._DbRef = dbRef
        self._PrjID = prjID
        self._GxCls = self.__class__.__name__
        self._Name = name
        self._Label = name
        self._InsUser = os.getlogin()
        self._InsDate = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
        self._UpdUser = self._InsUser
        self._UpdDate = self._InsDate
        self._isUsed = False

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
    def Label(self):
        return self._Label if self._Label else self._Name

    @property
    def Info(self):
        """ info/ToolTip

        13.06.2023 j.ebert
        """
        raise NotImplementedError(f"{self.__class__.__name__}.Info is not implemented")
        return ""

    @property
    def PrjID(self):
        """returns GeODin PrjID

        27.07.2023 j.ebert
        """
        return self._PrjID

    @property
    def UID(self):
        """ unique identiyfyer

        06.06.2023 j.ebert
        """
        raise NotImplementedError(f"{self.__class__.__name__}.isUsed() is not implemented")
        return ""

    def isDisabled(self):
        """True, if object is disabled, not error-free, ...

        09.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "Not overloaded in class %s", self.__class__.__name__)
        return False

    def isUsed(
        self,
        value=None              # None to get current setting, True/False to set setting
    ):
        """ True, wenn das Objekt genutzt wird und im DataDictionary gespeichert werden muss.

        20.01.2023 j.ebert
        """
        self.log.error(
            "%s.isUsed() is not implemented\n\t%s",
            self.__class__.__name__, traceback.format_stack()[-2].strip()
        )
        if value is not None:
            self.log.warning(
                "Argument 'value' is ignored in %s.isUsed()\n\t%s",
                self.__class__.__name__, traceback.format_stack()[-2].strip()
            )
        return self._isUsed

    def translate(
        self,
        key
    ):
        """translate souerce text 'key' using instance context

        Args:
            key (str)               source text
        Returns:
            sourceText (str)

        25.05.2023 j.ebert
        """
        return  res.translate(self._context, key)

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
        """erstellt ein neues Objekt dieser Klasse aus dem JSON-Objekt

        20.01.2023 j.ebert
        """
        assert isinstance(json_dct, dict), \
            f"arg 'json_dct': type 'dict' expected, but '{type(json_dct).__name__}' received"
        # Objekt erstellen
        obj = cls(dbRef, json_dct['PrjID'], json_dct['Name'])
        obj._InsUser = json_dct.get('InsUser', obj._InsUser)
        obj._InsDate = json_dct.get('InsDate', obj._InsDate)
        obj._UpdUser = json_dct.get('UpdUser', obj._UpdUser)
        obj._UpdDate = json_dct.get('UpdDate', obj._UpdDate)
        return obj

    def dumps(self):
        return json.dumps({self.__class__.__name__: self.to_json()}, indent=_JSON_DUMP_IDENT)

    def prmsSelectObject(
        self,
        mode='COM'
    ):
        """ returns parameters to select item in GeODin application

        args:
            mode                - GeODin API (COM, SQL, ...)

        returns:
            prms (dict)         {<key/paramter name>: <val/parameter value>}
        01.06.2023 j.ebert
        """
        # 06/2023 j.ebert, Parameter der COM-Funktion GeODin 9.6.264.0 (13.01.2023 - Win64)
        #    ObjectType = 0  # Datenbankzweig oder ein Projektzweig der Datenbank markieren
        #    ObjectType = 2  # Zweig Messpunkte oder eine Messpunktabfrage oder ein Messpunkt markieren
        #    ObjectType = 1  # Zweig 'Objekte' oder eine Objektabfrage oder ein Objekt markieren
        #    ParentNode = 'Database'
        #    ParentNode = 'DatabaseQueries'
        #    ParentNode = 'Project'
        #    ParentNode = 'ProjectQueries'
        #
        #    [Params]
        #    Database={db_prps[0]}
        #    UserName={db_prps[1]}
        #    Password={db_prps[2]}
        #    ObjectType=<0|1|2>
        #    ParentNode=<Database|DatabaseQueries|Project|ProjectQueries>
        #    Query={name}
        #    ObjectID={objectID}
        #    Expand=true
        self.log.log(gqc._LOG_TRACE, "Not overloaded in class %s", self.__class__.__name__)
        prms = {}
        return prms

    def goDict(
        self,
        key                     # term to translate
    ):
        """translates argument 'key' with GeODin dictionary

        02.08.2023 j.ebert
        """
        if hasattr(self._DbRef, '_GoDict'):
            key = self._DbRef._GoDict.get(key, key)
        return key

    def __iter__(self):
        yield from {
            'PrjID': self._PrjID,
            'Name': self._Name,
            'InsUser': self._InsUser,
            'InsDate': self._InsDate,
            'UpdUser': self._UpdUser,
            'UpdDate': self._UpdDate
        }.items()

    def __str__(self):
        return "<%s object (%s, %s)>" % (self.__class__.__name__, str(self._PrjID), str(self._Name))



def main():
    pass

if __name__ == '__main__':
    main()
