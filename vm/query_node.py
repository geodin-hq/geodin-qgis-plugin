"""
Classes:
    GoNodeQuery                 - Query ViewModel/QTreeWidgetItem

26.03.2024 j.ebert
"""
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path

import qgis.core
import qgis.utils
from qgis.PyQt import (
    QtCore,
    QtWidgets
)

import GeODinQGIS.gqgis_config as gqc
from GeODinQGIS import (
    app
)
from GeODinQGIS.ui.gqgis_bas import (
    cursor,
    plugin,
    GQgis_MsgBox as MsgBox
)
from GeODinQGIS.vm.bas_node import *

class GoNodeQuery(GoNode):
    """Project (GeODin Projekt) ViewModel/QTreeWidgetItem

    26.03.2024 j.ebert
    """

    _GxSettings = {
        'Default':      (20, ('gQry',), False),
        'GxAllLOC':     (21, ('gTypLOC',), False),
        'GxTypALL':     (21, ('gTypLOC',), False),
        'GxTypLOC':     (22, ('gTypLOC',), False),
        'GxTypINV':     (23, ('gTypINV',), False),
        'GxQryLOC':     (24, ('gQry',), False),
        'GxQryINV':     (24, ('gQry',), False),
        # 11/2026: GeoDin system queries (same icon as GeoDin queries, see gx/sysquery.py)
        'GxSysLOC':     (25, ('gQry',), False),
        'GxSysINV':     (25, ('gQry',), False),
    }


    def __init__(
        self,
        parent,                 # parent QTreeWidgetItem/Node
        tag                     # data, DataModel object (GoBaseClass)
    ):
        super().__init__(parent, tag)
        self.setText(self.textColumn(), self.tag().Label)
        self.orderText()
        # 10/2026: number of objects/measurement points in brackets, e.g. 'Boreholes (42)'
        #   only displayed - sorting (orderText) and layer names (layerName) use the label
        self.setText(self.textColumn(), self.displayText())
        self._DataPath = None

    @property
    def DataPath(self):
        if not self._DataPath:
            self._DataPath = Path(self.tag().dataSource())
        return self._DataPath

    def iconAlias(
        self,
        mode=0                  # alias index (0-normal|1-open)
        ):
        """retruns icon alias

        01.06.2023 j.ebert
        """
##        self.log.log(gqc._LOG_TRACE, "")
        names = self._GxSettings.get(self.tag().Kind, self._GxSettings['Default'])[1]
        alias = names[mode] if mode < len(names) else names[0]
        self.log.log(gqc._LOG_TRACE, alias)
        return alias

    def displayText(self):
        """returns the text shown in the Explorer: label and number of objects/measurement points

        10/2026
        """
        text = self.tag().Label
        count = getattr(self.tag(), 'Count', None)
        if count is not None:
            text = f"{text} ({count})"
        return text

    def layerName(self):
        """returns QGIS layer name for this GoQuery

        25.04.2024 j.ebert
        """
        # v2335.4, Name der Abfrage
        #   -> Name/Displayname vom QgsMapLayer nicht entsprechend der GeoDin-Sparcheinstellung
        #   -> keine Differnezierung bzgl. der GeoDin-Projekte (z. B: immer 'All objets')
        #      (-> sehr unschön bei Auswahl in ComboBox für Hotlink-/Selection-Tool)
        # lyrName = self.tag().Name
        # 04/2024 j.ebert, Name der Abfrage...
        #   - entsprechend der (aktuellen) GeoDin-Sparcheinstellung wie im GeoDinExplorer
        #   - mit Namen von Projekt bzw. Datenbank als Zusatz
        #   Anmerkung:
        #     Projekt/Datenbank ist im GeoDinExplorer/QTreeWidget der Parent vom Parent der Abfrage
        #     (Projekt/Datenbank > Objekte/Messpunkte > Abfragen (ganz allg.))
        lyrName = self.tag().Label
        if hasattr(self.parent().parent().tag(), 'Label'):
            lyrName += " (%s)" % self.parent().parent().tag().Label
        return lyrName

    def layers(self):
        """returns a QgsVectorLayer/GoLayer list of this GoQuery

        24.07.2024 j.ebert
        """
        # TODO: CleanCode - Klasse/Methode anpassen auf GoNode
        #                   (GoNode.GoLayerPattern, GoNode.listGoLayers(), GoNode.removeGoLayers())
        lyrs = []
        # validen/potentiellen GeoDin-Object-Layer (QgsVectorLayer, GeoJSON, ...) listen...
        mapLyrs = [lyr for lyr in qgis.core.QgsProject.instance().mapLayers().values() if (
            self.validGoLayer(lyr)
        )]
        # Liste der validen/potentiellen GeoDin-Object-Layer prüfen...
        if self.DataPath.exists():
            # 08/2023 j.ebert, Anmerkung
            #   Path(<filename>).samefile() verursacht einen FileNotFoundError, wenn
            #   das Fiel <filename> nicht eixtiert, also bie not Path(<filename>).exists()
            for lyr in mapLyrs:
                if self.DataPath.samefile(lyr.source().split('|')[0]):
                    lyrs.append(lyr)
        else:
            # 07/2024 j.ebert, aktualisiert (Pfad immer mit os.altsep für String-Vergleich)
            #   seealso: GeODinQGIS.vm.bas_node.GoNode.listGoLayers()
##            dataSource = str(self.DataPath).lower()
##            for lyr in mapLyrs:
##                if (lyr.source().split('|')[0].lower() == dataSource):
##                    lyrs.append(lyr)
            pattern = str(self.DataPath).lower().replace(os.sep, os.altsep)
            for lyr in mapLyrs:
                lyrSource = lyr.source().split('|')[0].lower().replace(os.sep, os.altsep)
                if lyrSource == pattern:
                    lyrs.append(lyr)
        # Liste der  validen/potentiellen GoLayer löschen, damit
        # keine unnötigen Referenzen auf Layer (und damit auf deren DataSource) bestehen
        del mapLyrs
        return lyrs

    def loadChildren(self):
        """loads QTreeWidget child items

        28.07.2023 j.ebert
        """
        return

    def onContextMenu(self):
        """returns QTreeWidget context menu

        31.05.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"")
        # QMenu/Context-Menü instanziieren
        menu = QtWidgets.QMenu()
##        # QAction vom GeODin Projekt instanziieren und dem Menü hinzufügen
##        action = menu.addAction(self.QIcon('GenericRefresh'), self.translate("Refresh..."))
##        action.triggered.connect(self.onRefresh)
##        action.setEnabled(False)
####        if self._tag.isOpened():
##        if self.isExpanded():
##            action = menu.addAction(self.QIcon(self.iconAlias(0)), self.translate("Close..."))
##            action.triggered.connect(self.onClose)
##        else:
##            # 07/2023 j.ebert, Anmerkung
##            #   Zum Öffnen des Projektes nur den Konten/das QTreeWidgetItem aufklappen.
##            action = menu.addAction(self.QIcon(self.iconAlias(1)), self.translate("Open..."))
##            action.triggered.connect(lambda checked, expand=True: self.setExpanded(expand))
##            action.setEnabled(not self._tag.isDisabled())
        hasLyrs = bool(self.layers())
        action = menu.addAction(self.translate("Add layer"))
        action.triggered.connect(self.onLayerAdd)
        action.setEnabled(not self._tag.isDisabled())
        # 10/2026: context menu texts reviewed (German translation in res/resources_de.json)
        action = menu.addAction(self.translate("Zoom to layer(s)"))
        action.triggered.connect(self.onLayerZoomTo)
        action.setEnabled((not self._tag.isDisabled()) and hasLyrs)
        action = menu.addAction(self.translate("Select layer(s)"))
        action.triggered.connect(self.onLayerSelect)
        action.setEnabled((not self._tag.isDisabled()) and hasLyrs)
        action = menu.addAction(self.translate("Update layer(s)"))
        action.triggered.connect(self.onLayerUpdate)
        action.setEnabled((not self._tag.isDisabled()) and hasLyrs)
        action = menu.addAction(self.translate("Remove layer(s)"))
        action.triggered.connect(self.onLayerRemove)
        action.setEnabled((not self._tag.isDisabled()) and hasLyrs)
        menu.addSeparator()
        # 10/2026: 'Remove' -> 'Remove exported data' (only active if there is no layer, but an export file)
        action = menu.addAction(self.translate("Remove exported data"))
        action.triggered.connect(self.onLayerRemove)
        action.setEnabled(self.DataPath.exists() and (not hasLyrs))
        menu.addSeparator()
        action = menu.addAction(self.QIcon('gIcon'), self.translate("Show in GeoDin"))
        action.triggered.connect(self.onGeODin)
        action.setEnabled(not self._tag.isDisabled())
        self.log.debug('ContextMenu (ActionCount %d) exce_', len(menu.actions()))
        return menu

    def onDoubleClicked(self):
        """event function for QTreeWidget signal 'itemDoubleClicked'

        15.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "TRACE")
        self.onLayerAdd()
        return

    def onGeODin(self):
        """selects Database in the GeODin object manager

        01.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"Query '%s'...", self.tag().Name)
        # 10/2026: returns True if the query was selected in GeoDin - the export (method 60)
        #   exports the node selected in GeoDin, so it must not run after a failed selection
        #   (before: the data of the previously selected node were added as layer)
        try:
            gx.gApp.selectObject(self._tag)
            return True
        except gqb.GxGAppBusyError as exc:
            MsgBox.error(plugin().parent(), 'GeoDin', exc.msg())
        except gqb.GxGComException as exc:
            self.tag()._error = "Query '%s' not found in GeoDin object manager" % self.tag().Name
            self.update()
            MsgBox.error(plugin().parent(), 'GeoDin', exc.msg())
        except gqb.GxException as exc:
            MsgBox.error(plugin().parent(), 'GeoDin', exc.msg())
        except Exception:
            MsgBox.error(
                plugin().parent(),
                'GeoDin',
                self.translate("Unknown error on select query")
            )
        return False

    def onLayerAdd(self):
        """updates query result/GEOJSON file

        25.04.2024 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"Query '%s'...", self.tag().Name)
        # Abfrage im GOM selektieren...
        # self.onGeODin()
        # 10/2026: no layer if the query could not be selected in GeoDin
        if not self.onGeODin():
            return
        # DataSource der Abfrage aktualsieren...
        try:
            # DataSource der Abfrage/des Layers prüfen und ggf. erstellen...
            if not self.DataPath.exists():
                # 10/2026: GeoDin may report an error during the export (e.g. access
                #   violation, GIX-10201) but still writes the file -> add the layer only
                #   if the file exists and is valid
                self.onLayerUpdate()
            if not self.DataPath.exists():
                raise gqb.GxException(
                    "Layer data file '%s' was not created by GeoDin", str(self.DataPath)
                )
            # QGIS Layer erstellen
##            newLyr = qgis.core.QgsVectorLayer(str(self.DataPath), self.tag().Name, "ogr")
            newLyr = qgis.core.QgsVectorLayer(str(self.DataPath), self.layerName(), "ogr")
            if not newLyr.isValid():
                raise gqb.GxException(
                    "Layer data file '%s' could not be opened", str(self.DataPath)
                )
            # EPSG ermitteln...
            # 01.03.2023 j.ebert, Anmerkung
            #   Nach GeoJSON Specification (RFC 7946) ist kein CRS enhalten, sondern immer WGS 1983.
            #   GeoJSON von GeODin enthält "gespeicherte" Koordinaten sowie das Feld EPSG.
            # Fazit: EPSG aus dem Layer-Daten auslesen.
            #   Wenn das Feld EPSG enthalten ist und gesetzt ist, dann diesen EPSG-Code nutzen.
            #   Wenn mit diesem EPSG-Code ein CRS erstellt werden kann, dann dieses CRS nutzen.
            #   Wenn kein CRS erstellt werden konnte, dann wird automatischn WGS 1984 genutzt.
            newLyrEPSGFld = 'EPSG'
            newLyrEPSGVal = ""
            if newLyrEPSGFld in [fld.name() for fld in newLyr.fields()]:
                firstFeat = next(newLyr.getFeatures(), None)
                if firstFeat is not None:
                    newLyrEPSGVal = firstFeat.attribute(newLyrEPSGFld)
            if newLyrEPSGVal:
                newLyrCRS = qgis.core.QgsCoordinateReferenceSystem(f"EPSG:{newLyrEPSGVal}")
                if newLyrCRS.isValid():
                    newLyr.setCrs(newLyrCRS)
            # 10/2026: layer style - style file (*.qml) from 'Layer styles...' (toolbar menu),
            #   otherwise objects: red circles with labels (long name), see ui/gqgis_styles.py
            try:
                from GeODinQGIS.ui.gqgis_styles import applyLayerStyle
                styleMsg = applyLayerStyle(newLyr, self.tag().Kind[-3:])
                if styleMsg:
                    plugin().iface().messageBar().pushWarning("GeoDinQGIS", styleMsg.replace("\n", " "))
            except Exception:
                self.log.error("Layer style could not be applied", exc_info=True)
            # QGIS Layer der akt. Map hizufügen
            qgis.core.QgsProject.instance().addMapLayer(newLyr)
        except gqb.GxException as exc:
            self.log.debug("", exc_info=True)
            MsgBox.error(plugin().parent(), 'GeoDin', exc.msg())
        except Exception:
            self.log.debug("Major disaster...", exc_info=True)
            MsgBox.error(
                plugin().parent(),
                'GeoDin',
                self.translate("Unknown error on add layer")
            )
        return

    def onLayerRemove(self):
        """deletes query result/GEOJSON file and also layer

        01.08.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"Query '%s'...", self.tag().Name)
        # Abfrage im GOM selektieren...
        self.onGeODin()
        # Layer sowie DataSource der Abfrage löschen...
##        dataPath = Path(self.tag().dataSource())
##        lyrs = []
##        try:
##            # Layer löschen...
##            lyrs = self.layers()
##            if lyrs:
##                qgis.core.QgsProject.instance().removeMapLayers([lyr.id() for lyr in lyrs])
##                QtWidgets.QApplication.processEvents()
##                plugin().iface().mapCanvas().refresh()
        try:
            # Layer löschen...
            self.removeLayers(refresh=True)
            # DataSource löschen...
            if self.DataPath.exists():
                QtCore.QTimer.singleShot(self.QSleepTime, self._remove)
            self.tag().isUsed(False)
            self.log.debug("Remove query '%s' successfully", self.tag().Name)
        except gqb.GxException as exc:
            self.log.debug("", exc_info=True)
            MsgBox.error(plugin().parent(), 'GeoDin', exc.msg())
        except Exception:
            self.log.debug("Major disaster...", exc_info=True)
            MsgBox.error(
                plugin().parent(),
                'GeoDin',
                self.translate("Unknown error on remove layers")
            )
        return

    def onLayerSelect(self):
        """select query layers

        07.08.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE,"Query '%s'...", self.tag().Name)
        lyrTvw = qgis.utils.iface.layerTreeView()
        try:
            lyrTvw.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection )
            # Layer selektieren...
            lyrs = self.layers()
            for lyr in lyrs:
                lyrTvw.setCurrentLayer(lyr)
        except Exception:
            self.log.debug("Major disaster...", exc_info=True)
            MsgBox.error(
                plugin().parent(),
                'GeoDin',
                self.translate("Unknown error on select layers")
            )
        finally:
            lyrTvw.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection )
        return

    def onLayerUpdate(self):
        """updates query result/GEOJSON file

        returns:
            True if the GEOJSON file was created/updated successfully, otherwise False

        01.08.2023 j.ebert
        """
        success = False
        self.log.log(gqc._LOG_TRACE,"Query '%s'...", self.tag().Name)
        # Abfrage im GOM selektieren...
        # self.onGeODin()
        # 10/2026: no export if the query could not be selected in GeoDin
        if not self.onGeODin():
            return success
        # DataSource der Abfrage aktualsieren...
        dataPath = self.DataPath
        try:
            if not dataPath.exists():
                self.log.debug("Create %s", str(dataPath))
                gx.gApp.exportFeatureCollection(str(dataPath))
                self.tag().isUsed(True)
            else:
                self.log.debug("Update %s", str(dataPath))
                # https://gis.stackexchange.com/questions/159950/making-qgis-layer-update-from-changed-data-source
                # General approach
                #   If you have the possibility to control how the file is being overwritten
                #   you can open the existing files with write permissions and change the content
                #   instead of replacing the files completely (delete/recreate) on disk.
                with tempfile.TemporaryFile(
                    prefix=(dataPath.stem + '_'),
                    suffix=dataPath.suffix,
                    dir=dataPath.parent
                ) as tempFile:
                    tempPath = Path(tempFile.name)
                gx.gApp.exportFeatureCollection(str(tempPath))
                dataPath.write_text(tempPath.read_text())
                tempPath.unlink()
            self.log.debug("Update %s successfully", str(dataPath))
            success = True
            # Layer der Query "aktualisieren"...
            for lyr in self.layers():
##                lyr.dataProvider().reloadData()
                lyr.reload()
            QtWidgets.QApplication.processEvents()
            # .refresh()            - repaints the canvas map
            # .refreshAllLayers()   - reloads all layers, clear the cache and refresh the canvas
##            plugin().iface().mapCanvas().refresh()
##            plugin().iface().mapCanvas().refreshAllLayers()
        except gqb.GxException as exc:
            self.log.debug("", exc_info=True)
            MsgBox.error(plugin().parent(), 'GeoDin', exc.msg())
        except Exception:
            self.log.debug("Major disaster...", exc_info=True)
            MsgBox.error(
                plugin().parent(),
                'GeoDin',
                self.translate("Unknown error on update query")
            )
        return success

    def onLayerZoomTo(self):
        self.log.log(gqc._LOG_TRACE,"Query '%s'...", self.tag().Name)
        lyrs = self.layers()
        if lyrs:
            try:
                extent = qgis.core.QgsRectangle()
                for lyr in lyrs:
                    extent.combineExtentWith(lyr.extent())
                extent.scale(1.1)
                qgis.utils.iface.mapCanvas().setExtent(extent)
                qgis.utils.iface.mapCanvas().refresh()
            except:
                self.log.error("Unkown error in onLayerZoomTo()...", exc_info=True)
        return

    def orderIndex(self):
        """returns QTreeWidgetItem class index for sorting QTreeWidget

        01.06.2023 j.ebert
        """
        self.log.log(gqc._LOG_TRACE, "")
        idx = self._GxSettings.get(self.tag().Kind, self._GxSettings['Default'])[0]
        return idx

    def removeLayers(
        self,
        refresh=False           # refresh mapCanvas (False|True)
        ):
        """ deletes query layers from QGIS project

        return:
            True    if query layers were found/deleted in QGIS project
            False   if query layers were not found/deleted in QGIS project

        24.07.2024 j.ebert
        """
        lyrs = self.layers()
        if lyrs:
            qgis.core.QgsProject.instance().removeMapLayers([lyr.id() for lyr in lyrs])
            if refresh:
                # wenn Refresh-Option über Argumnet explicit gesetzt ist
                # dann Refresh mapCanvas
                QtWidgets.QApplication.processEvents()
                plugin().iface().mapCanvas().refresh()
        return bool(lyrs)

    def _remove(self):
        # DataSource löschen...
        if self.DataPath.exists():
            self.log.debug("Remove %s", str(self.DataPath))
            self.DataPath.unlink()

    def _update(self):
        # https://gis.stackexchange.com/questions/194867/refreshing-mapcanvas-while-pyqgis-script-is-running
        pass


def main():
    pass

if __name__ == '__main__':
    main()
