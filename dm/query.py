
"""
Classes:
    GoQuery                     - Data Model of GeODin query

17.04.2023 j.ebert
"""
import tempfile
from GeODinQGIS.dm.bas import *

class GoQuery(GoBaseClass):
    """Data Model Base Class

    17.04.2023 j.ebert
    """
    _Kinds = [
        'GxAllLOC',
        'GxTypLOC',
        'GxTypINV',
        'GxQryLOC',
        'GxQryINV',
        # 11/2026: GeoDin system queries (*.GSQ, see gx/sysquery.py)
        'GxSysLOC',
        'GxSysINV'
    ]
    # kinds referenced by the name in the GOM (not by INV_TYPE/GEN_DESC)
    _NamedKinds = ('GxQryLOC', 'GxQryINV', 'GxSysLOC', 'GxSysINV')

    def __init__(
        self,
        dbRef,
        prjID,
        name
        ):
        super().__init__(dbRef, prjID, name)
        self.log.log(gqc._LOG_TRACE,"")
        # 04/2024 j.ebert, Achtung
        #     Attribut _Label in dieser Klasse NICHT nutzen, sondern nur Property Label!
        #   (siehe auch Kommentar in Property GoQuery.Label)
        # self._Label = self.goDict(name)
        self._Desc = ""
        self._Kind = ""
        self._Opts = None
        # 10/2026: number of objects/measurement points (GxAllLOC, GxTypLOC, GxTypINV),
        #   None if unknown (user queries, not loaded); not saved in the DDX
        self._Count = None
        # 10/2026: name of the query in the GeoDin object manager, if it differs from Label
        #   (found by GxCOMClient.selectObject, not saved in the DDX)
        self._GOMLabel = None

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
    def Count(self):
        """number of objects/measurement points of this query or None if unknown (10/2026)"""
        return self._Count

    @property
    def Desc(self):
        """ description/classification

        31.07.2023 j.ebert
        """
        if not self._Desc:
            # Wenn Attr _Desc nicht gesetzt ist,
            # dann unique Value in der Datenbank ermitteln...
            self._Desc = self.DbRef.uniqueQryDesc(self.PrjID, self.Kind)
        return self._Desc

    @property
    def Info(self):
        """ info/ToolTip

        13.06.2023 j.ebert
        """
        info = f"{self.PrjID} {self.Kind} ({self._Desc})".rstrip(' ()')
        if self._Kind in ('GxSysLOC', 'GxSysINV'):
            # 11/2026: system query - file of the query
            info = "%s\n%s: %s" % (
                info, self.translate("GeoDin system query"), (self._Opts or [""])[0])
        if self._error:
            info = "%s\n%s" % (info, self._error)
        return info

    @property
    def Kind(self):
        """query kind/type

        13.06.2023 j.ebert
        """
        return self._Kind

    @property
    def Label(self):
        """label/displayname

        24.04.2024 j.ebert
        """
        # 04/2024 j.ebert, Überladen der Property Label für class GoQuery
        #     Label ist nicht nur der Displayname im GeoDinExplorer, sondern auch
        #   Parameter bei GeoDin-COM-Funktionen. Daher muss der Displayname im GeoDinExplorer
        #   vom Plugin identisch mit dem Displaynamen im Objekt-Manager von GeoDin (GOM) sein.
        #     Der Label/Displayname von GeoDin-Abfragen (GxQryINV, GxQryLOC) ist unabhängig von
        #   der GeoDin-Spracheinstellung, aber NICHT der Label/Displayname von Standard-Abfragen
        #   (GxTypINV, GxTypLOC, GxAllLOC).
        # 04/2024 j.ebert, Achtung
        #     Die Poroperty Label wird für Abfragen überladen, weil das Setzen des Attr _Label
        #   bei der Instanzierung einer Anfrage nicht zuverlässig funktioniert, offensichtlich
        #   auf Grund der Reihenfolge der Instanzierung von Abfragen, die aus dem DDX geladen
        #   werden und dem Laden vom Dictionary in Abhängigkeit der der GeoDin-Spracheinstellung.
        #   Damit wird das Attribut _Label in dieser Klasse nicht mehr unterstützt!!!
##        return self._Label if self._Label else self._Name
##        return self._Name if self._Kind in ('GxQryINV', 'GxQryLOC') else self.goDict(self._Name)
        # 11/2026: system queries (GxSys*) like GeoDin queries - name as shown in the GOM
        return self._Name if self._Kind in self._NamedKinds else self.goDict(self._Name)

    @property
    def UID(self):
        """unique identiyfyer

        06.06.2023 j.ebert
        """
        return "%s_%s_%s_%s" % (self.DbRef.Desc, self.PrjID, self.Kind, self.Desc)

    @property
    def LongLabel(self):
        """...

        15.08.2023 j.ebert
        """
        lbls = [self.DbRef.Label, self.Label]
        if self.PrjID != self.DbRef.PrjID:
            prjLabels = [prj.Label for prj in self.DbRef.GoPrjs if prj.PrjID == self.PrjID]
            if prjLabels:
                lbls.insert(1, prjLabels[0])
            else:
                lbls.insert(1, self.PrjID)
        return "\\".join(lbls)

    def dataSource(self):
        """returns current data source/JSON file of query

        06.06.2023 j.ebert
        """
        return str((Path(self.DbRef.DataPath) / self.UID).with_suffix('.json'))

    def isDisabled(self):
        """True, if object is disabled, not error-free, ...

        09.06.2023 j.ebert
        """
        return bool(self._error)

    def isPresent(self):
        return (
            (not self.isDisabled()) and
            self._isUsed and
            Path(self.dataSource()).exists()
        )

    def isUsed(
        self,
        value=None              # None to get current setting, True/False to set setting
    ):
        """ True, wenn die Query genutzt wird und im DataDictionary gespeichert werden muss.

        03.08.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "")
        if isinstance(value, bool) and (value != self._isUsed):
            # Wenn True oder False als Wert übergeben wurde und
            # wenn sich damit das Attr '_isUsed' ändert,
            # dann die Abfrage im DDX (also die Datenbank) speichern
            self.log.debug("Qry (UID %s) store...", self.UID)
            try:
                self._isUsed = value
                self.DbRef.store()
            except:
                self.log.critical("Major disaster...", exc_info=True)
                self._isUsed = not value
        return self._isUsed

    def updateDataSource(self):
        """ updates query dataSource

        08.08.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "")
        dataPath = Path(self.dataSource())
        gx.gApp.selectObject(self)
        if not dataPath.exists():
            gx.gApp.exportFeatureCollection(str(dataPath))
        else:
            # https://gis.stackexchange.com/questions/159950/making-qgis-layer-update-from-changed-data-source
            # General approach
            #   If you have the possibility to control how the file is being overwritten
            #   you can open the existing files with write permissions and change the content
            #   instead of replacing the files completely (delete/recreate) on disk.
            tempPath = self.tempPath()
            gx.gApp.exportFeatureCollection(str(tempPath))
            dataPath.write_text(tempPath.read_text())
            tempPath.unlink()
        return

    def prmsCreateObjectSelection(
        self,
        mode='COM'
    ):
        """ returns parameters to create selection group in GeODin application

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
        prms.pop('ParentNode', None)
        prms.pop('Query', None)
        prms.pop('ObjectID', None)
        prms.pop('Expand', None)
        prms['ObjectIDs'] = ""
        prms['ObjectType'] = "0" if self.Kind[-3:] == 'LOC' else "1"
        prms['RefName'] = "Gx%s_%s" % (
            'LOC' if prms['ObjectType'] == "0" else 'INV',
            datetime.datetime.now().strftime("%H%M%S")
        )
        prms['MethodID'] = -1
        prms['MethodParams'] = ""
        return prms

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
        # 10/2026: name in the GeoDin object manager (if known) and alternative names
        #   ('_QueryCandidates' is not passed to GeoDin, see GxCOMClient.selectObject)
        prms['_QueryCandidates'] = self.gomLabelCandidates()
        prms['_GoQuery'] = self
        # Parameter für Item/Knoten im GOM aktualisieren/überschreiben...
        # 08/2023 j.ebert, Achtung, Prm Query hier mit Attr Label setzen
        #   Attr Name   - Definition in der GeODin-DB (INV_NAME, GEN_NAME, ...)
        #   Attr Label  - Anzeige im GOM in Abhängikeit von derSprache (RegSZ UserLId)
        if self.PrjID == self.DbRef.DBPrjID:
            # Abfrage auf Datenbank-Ebene...
            prms.update({
                'ObjectType': "1" if self.Kind[-3:] == 'LOC' else "2",
                'ParentNode': "DatabaseQueries",
                'Query': self.Label,
                'ObjectID': "",
                'Expand': "false",
            })
        else:
            # Abfrage auf Projekt-Ebene...
            prms.update({
                'ObjectType': "1" if self.Kind[-3:] == 'LOC' else "2",
                'ParentNode': "ProjectQueries",
                'Query': self.Label,
                'ObjectID': self.PrjID,
                'Expand': "false",
            })
        return prms

    def gomLabelCandidates(self):
        """possible names of the query in the GeoDin object manager (10/2026)

        GeoDin does not always show the name from the database (SYS_INVTYPES.INV_NAME) for
        measurement point types, e.g. INV_NAME 'samples  (geot. borehole)' is shown as
        '(G1) Samples' (prefix of the object type + table name in SYS_LOCTABTY). The names are
        tried in this order until GeoDin finds the query.
        """
        import re
        label = self.Label
        names = []
        if self._GOMLabel:
            names.append(self._GOMLabel)
        names += [label, " ".join(str(label).split())]
        if self._Kind == 'GxTypINV':
            invType = (self._Desc or "")[:3]
            try:
                locTypes = {row[0]: row[1] for row in (self.DbRef.GT_LOCTYPES or [])}
                for row in (self.DbRef.GT_LOCTABTY or []):
                    if len(row) < 7 or row[6] != invType:
                        continue
                    genName = str(locTypes.get(row[0], "") or "")
                    tabName = " ".join(str(row[2] or "").split())
                    m = re.match(r"^\(\s*[^)]*\)", genName)
                    if m and tabName:
                        names.append(f"{m.group(0)} {tabName}")
                    if tabName:
                        names.append(tabName)
                    if genName and str(row[3]) == "1":
                        # measurement point type of the object itself (table type 1, general
                        #   information), e.g. '(G1) Location' -> '(G1) Locations'
                        names.append(f"{genName}s")
                        names.append(genName)
            except Exception:
                self.log.debug("", exc_info=True)
        unique = []
        for name in names:
            if name and name not in unique:
                unique.append(name)
        return unique

    def tempPath(self):
        dataPath = Path(self.dataSource())
        with tempfile.TemporaryFile(
            prefix=(dataPath.stem + '_'),
            suffix=dataPath.suffix,
            dir=dataPath.parent
        ) as tempFile:
            filename = tempFile.name
        return Path(filename)

    def validate(self):
        self._error = ""
        return not bool(self._error)

    @classmethod
    def from_TypINV(
        cls,
        dbRef,
        prjID,
        data                    # tuple (INV_TYPE, INV_NAME, INV_OPT)
    ):
        """
        31.07.2023 j.ebert
        """
        obj = cls(dbRef, prjID, data[1])
        obj._tag = data
        # 07/2023 j.ebert Anmerkung
        #   - INV_TYPE (Text) hat immer 3 Stellen -> erste drei Stellen vom Attr _Desc
        #   - INV_OPT  (Zahl)                     -> letzten fünf Stellen (inkl. führende Nullen)
        #   -> Attr _Desc mit 8 Stellen wie GEN_DESC (in LOCTYPES)
        #   -> INV_OPT  könnte Key für Tabellen sein (1-LOC_LOCREG|2-LOC_FILREG|3-LOC_PRBREG)?!
        #      ABER INV_TYPE und INV_OPT sind auch noch im Attr _tag gespeichert.
        obj._Desc = "%s%05d" % (data[0], data[2])
        obj._Kind = 'GxTypINV'
        obj._Opts = data[-1:]
        obj.validate()
        return obj

    @classmethod
    def from_TypLOC(
        cls,
        dbRef,
        prjID,
        data                    # tuple (GEN_DESC, GEN_NAME, GEN_OPT, GEN_VERS)
    ):
        """
        31.07.2023 j.ebert
        """
        obj = cls(dbRef, prjID, data[1])
        obj._tag = data
        obj._Desc = data[0]
        obj._Kind = 'GxTypLOC'
        obj._Opts = data[-2:]
        obj.validate()
        return obj

    @classmethod
    def from_TypALL(
        cls,
        dbRef,
        prjID
    ):
        """
        31.07.2023 j.ebert
        """
        obj = cls.from_TypLOC(dbRef, prjID, ('LOCTYPES', 'All objects', None, None))
        obj._Kind = 'GxAllLOC'
        obj.validate()
        return obj

    @classmethod
    def from_PrjDEF(
        cls,
        dbRef,
        prjID,
        data                    # tuple (PRJ_ID, OBJ_DESC, OBJ_NAME, OBJ_CNT)
    ):
        """
        25.04.2024 j.ebert
        """
        obj = cls(dbRef, prjID, data[2])
        obj._tag = data
        obj._Desc = ""
        obj._Kind = {
            'MESQUERY': 'GxQryINV',
            'LOCQUERY': 'GxQryLOC',
        }.get(data[1], 'GxQry???')
        obj._Opts = [data[-1], data[1]]
        if data[-1] != 1:
            obj._error = "Query name in GeoDin object manager not unique!"
        obj.validate()
        return obj

    @classmethod
    def from_SysQRY(
        cls,
        dbRef,
        prjID,
        data                    # dict {'Name', 'Grp' (LOC|INV), 'File'} (see gx.sysquery)
    ):
        """GeoDin system query (*.GSQ in <ProgramData>\\QUERYDEF\\, 11/2026)"""
        obj = cls(dbRef, prjID, data['Name'])
        obj._tag = data
        obj._Desc = ""
        obj._Kind = 'GxSysINV' if data.get('Grp') == 'INV' else 'GxSysLOC'
        obj._Opts = [data.get('File', ""), 'SYSQUERY']
        obj.validate()
        return obj

    def overload(
        self,
        other                   # GoQuery reloaded from GeODin database
    ):
        """overloads this query with 'other' query (loaded from the GeODin database)

        24.04.2024 j.ebert
        """
        assert type(other) is type(self), \
            "Type '%s' is expected, but type '%s' was given" % (
                type(self).__name__, type(other).__name__
            )
        if (id(other) != id(self)) and (self == other):
            # Differenzierung GxTyp* und GXQry*
            # (siehe auch GoQuery.__eq__() und GoQuery.__members())
            # - Referenz innerhalb vom DDX ist UID, also
            #   Attr _DbRef, _PrjID, _Kind und _Desc nicht aktualisieren/überladen
##            if self._Kind in ('GxQryINV', 'GxQryLOC'):
            if self._Kind in self._NamedKinds:
                # Abfragen GxQryINV, GxQryLOC (11/2026: und Systemabfragen GxSysINV, GxSysLOC)...
                # - Referenz zwischen DDX und GeODin-Datenbank ist Namen, also
                #   Attr _Name nicht aktualisieren/überladen
                #   (in der GeODin-DB SYS_PRJDEFS::OBJ_NAME)
                pass
            else:
                # Abfragen GxTypINV, GxTypLOC
                # - Referenz zwischen DDX und GeODin-Datenbank ist DESC,
                #   Attr _Desd nicht aktualisieren/überladen
                #   (in der GeODin-DB SYS_INVTYPES::INV_TYPE+INV_OPT bzw. SYS_LOCTYPES::GEN_DESC)
                # - Attr _Name aktualisieren/überladen(!!!)
                #   Notw. weil die GeODin-COM-Funktion den GOM-Namen als Paramerter haben.
                self._Name = other._Name
                # - Attr _Label aktualisieren (siehe auch GoQuery.__init__())
                #   04/2024 j.ebert, Achtung
                #       Attribut _Label in dieser Klasse NICHT nutzen, sondern nur Property Label!
                #     (siehe auch Kommentar in Property GoQuery.Label)
                # self._Label = self.goDict(self._Name)
            # - Attr _tag übernehmen (Daten der Abfrage, die aus der GeODin-DB geladen wurden)
            #   08/2023 j.ebert, Attr _tag wird in GoQuery.from_json() nicht gesetzt
            self._tag = other._tag
            # - 10/2026: Attr _Count (number of objects/measurement points) übernehmen
            self._Count = other._Count
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
        obj._Kind = dmpDict.get('Kind', 'Kind°°°°')
        obj._Desc = dmpDict.get('Desc', 'Desc°°°°')
        obj._Opts = dmpDict.get('Opts')
        obj._error = "No longer in GeoDin database"
        # 08/2023 j.ebert, Anmerkung
        #   Derzeit wird diese Methode ausschließlich zum laden aus dem DDX genutzt.
        #   - Attr _error setzen und beim Überladen mit GoQuery aus der GeODin-DB überschreiben
        #     (Attr isDisabled ist abhängig vom Attr _isError)
        #   - Attr _isUsed setzen, damit die GoQuery im DDX wieder mit gespeichert wird und
        #     nicht beim Speichern der GoDatabase im DDX "verloren" geht
        obj._error = "No longer in GeoDin database"
        obj._isUsed = True
        obj.log.log(gqc._LOG_TRACE, "%s (Desc %s)...", cls.__name__, obj.UID)
        return obj

    def dumps(self):
        return json.dumps({self.__class__.__name__: self.to_json()}, indent=_JSON_DUMP_IDENT)

    def __members(self):
        # seeaslo: https://stackoverflow.com/questions/45164691/recommended-way-to-implement-eq-and-hash
        prps = (self._DbRef, self._PrjID, self._Kind, self._Desc)
##        if self._Kind in ('GxQryINV', 'GxQryLOC'):
        if self._Kind in self._NamedKinds:
            prps = (self._DbRef, self._PrjID, self._Kind, self._Name)
        return prps

    def __eq__(self, other):
        return (type(other) is type(self)) and (self.__members() == other.__members())

    def __hash__(self):
        return hash(self.__members())

    def __iter__(self):
        yield from {
            'PrjID': self._PrjID,
            'Kind': self._Kind,
            'Desc': self._Desc,
            'Name': self._Name,
            'Opts': self._Opts,
##            'InsUser': obj._InsUser,
##            'InsDate': obj._InsDate,
##            'UpdUser': obj._UpdUser,
##            'UpdDate': obj._UpdDate
        }.items()

def main():
    pass

if __name__ == '__main__':
    main()
