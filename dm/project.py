"""
Classes:
    GoProject                   - Data Model of GeODin project

17.04.2023 j.ebert
"""
from GeODinQGIS.dm.bas import *

class GoProject(GoBaseClass):
    """Data Model Base Class

    17.04.2023 j.ebert
    """
    SQL_FldNames = """
    PRJ_ID, PRJ_NAME, PRJ_ALIAS, PRJ_TYPE, PRJ_OPT, PRJ_USER, PRJ_DATE, PRJ_PATH, GEODINGUID
    """
    SQL_FldIdxs = {}

    _DumpDateFormat = "%d.%m.%Y"

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
        info = f"{self.PrjID}: {self._PRJ_NAME}".strip(' :')
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

    def isUsed(
        self,
        value=None              # None to get current setting, True/False to set setting
    ):
        """ True, wenn das Projekt genutzt wird und im DataDictionary gespeichert werden muss.

        03.08.2023 j.ebert
        """
        if value is not None:
            self.log.warning(
                "Argument 'value' is ignored in %s.isUsed()\n\t%s",
                self.__class__.__name__, traceback.format_stack()[-2].strip()
            )
        value = bool(
            [qry for qry in self.DbRef._Queries if (qry.PrjID == self.PrjID) and qry.isUsed()]
        )
        return value

    def prmsSelectObject(
        self,
        mode='COM'
    ):
        """ returns parameters to select item in GeODin application

        args:
            mode                - GeODin API (COM, SQL, ...)

        returns:
            prms (dict)         {<key/paramter name>: <val/parameter value>}

        28.07.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "")
        # Paramater der Datenbank laden...
        prms = self.DbRef.prmsSelectObject(mode)
        # Parameter für Item/Knoten im GOM aktualisieren/überschreiben...
        prms.update({
            'ObjectType': "0",
            'ParentNode': "Project",
            'Query': "",
            'ObjectID': self.PrjID,
            'Expand': "false",
        })
        return prms

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
        obj._PRJ_ALIAS = data[cls.idxSQLFld('PRJ_ALIAS')]
        obj._PRJ_USER = data[cls.idxSQLFld('PRJ_USER')]
        obj._PRJ_DATE = data[cls.idxSQLFld('PRJ_DATE')]
        if isinstance(obj._PRJ_DATE, datetime.datetime):
            obj._PRJ_DATE = obj._PRJ_DATE.strftime("%d.%m.%Y")
        elif obj._PRJ_DATE is None:
            obj._PRJ_DATE = ""
        else:
            obj._PRJ_DATE = str(obj._PRJ_DATE)
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
            fldNames = [item.strip().split('.')[-1] for item in cls.SQL_FldNames.split(',')]
            cls.SQL_FldIdxs = {fld: idx for idx, fld in enumerate(fldNames)}
        return cls.SQL_FldIdxs.get(name)

    def overload(
        self,
        other                   # GoProject reloaded from GeODin database
    ):
        """overloads this project with 'other' project (loaded from the GeODin database)

        03.08.2023 j.ebert
        """
        assert type(other) is type(self), \
            "Type '%s' is expected, but type '%s' was given" % (
                type(self).__name__, type(other).__name__
            )
        if (id(other) != id(self)) and (self == other):
            # - Referenz ist PrjID, also
            #   Attr _PrjID nicht aktualisieren/überladen
            #   (Ref sowohl innerhalb vom DDX, als auch zwischen DDX und GeODin-Datenbank)
            # - Attr _tag übernehmen (Daten der Abfrage, die aus der GeODin-DB geladen wurden)
            #   08/2023 j.ebert, Attr _tag wird in GoQuery.from_json() nicht gesetzt
            self._tag = other._tag
            # - Attr _PRJ_ALIAS, _PRJ_USER, _PRJ_DATE aktualisieren/überladen
            #   (Spalten in Tbl LOCPRMGR PRJ_ALIAS, PRJ_USER, PRJ_DATE, aber
            #    Achtung Attr _PRJ_DATE ist vom Typ Str und nicht datetime.datetime)
            self._PRJ_ALIAS = other._PRJ_ALIAS
            self._PRJ_USER = other._PRJ_USER
            self._PRJ_DATE = other._PRJ_DATE
            # - Attr _error aktualisieren/überladen
            #   08/2023 j.ebert, Anmerkung
            #       Attr _error nicht zurücksetzen, ggf. hat other auch einen Fehler
            #       (z. B. Name einer GeODin-Abfrage (SYS_PRJDEFS::OBJ_NAME) nicht eindeutig)
            self._error = other._error
        return

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
        assert isinstance(json_dct, dict), \
            f"arg 'json_dct': type 'dict' expected, but '{type(json_dct).__name__}' received"
        dmpDict = json_dct
        # Objekt erstellen
        obj = cls(dbRef, dmpDict.get('PrjID',"PrjID°"), dmpDict.get('Name',""))
        obj._PRJ_ALIAS = dmpDict.get('Alias', "")
        obj._PRJ_USERv= dmpDict.get('User', "")
        obj._PRJ_DATE = dmpDict.get('Date', "")
        # 08/2023 j.ebert, Anmerkung
        #   Derzeit wird diese Methode ausschließlich zum laden aus dem DDX genutzt.
        #   - Attr _error setzen und beim Überladen mit GoProject aus der GeODin-DB überschreiben
        #     (Attr isDisabled ist abhängig vom Attr _isError)
        obj._error = "No longer in GeODin database"
        obj.log.log(gqc._LOG_TRACE, "%s '%s' (PrjID %s)...", cls.__name__, obj.Name, obj.PrjID)
        return obj

    def dumps(self):
        return json.dumps({self.__class__.__name__: self.to_json()}, indent=_JSON_DUMP_IDENT)

    def __members(self):
        # seeaslo: https://stackoverflow.com/questions/45164691/recommended-way-to-implement-eq-and-hash
        prps = (self._DbRef, self._PrjID)
        return prps

    def __eq__(self, other):
        return (type(other) is type(self)) and (self.__members() == other.__members())

    def __hash__(self):
        return hash(self.__members())

    def __iter__(self):
        yield from {
            'PrjID': self._PrjID,
            'Name': self._Name,
            'Alias': self._PRJ_ALIAS,
            'User': self._PRJ_USER,
            'Date': self._PRJ_DATE
##            'InsUser': obj._InsUser,
##            'InsDate': obj._InsDate,
##            'UpdUser': obj._UpdUser,
##            'UpdDate': obj._UpdDate
        }.items()

def main():
    pass

if __name__ == '__main__':
    main()
