r"""Layer styles for GeoDin layers (10/2026)

Functions:
    styleFile                   - style file (*.qml) for objects ('LOC') or measurement points ('INV')
    setStyleFile                - saves the style file in the QGIS user settings
    applyLayerStyle             - applies the style to a new GeoDin layer

Classes:
    GQgis_Dlg_Styles            - dialog: style files for objects and measurement points

Settings (QGIS user settings, QgsSettings):
    GeODinQGIS/styleFileLOC     - style file for object layers (all objects, object types,
                                  user queries on objects)
    GeODinQGIS/styleFileINV     - style file for measurement point layers

Without style file (or if it cannot be loaded):
    objects             red circle markers, label with the long name (field LONGNAME)
    measurement points  QGIS default style

A style file is created in QGIS: Layer properties » Symbology » Style » Save Style...
(QGIS layer style file *.qml). It is applied when a GeoDin layer is added; 'Update layer(s)'
keeps the current style of the layer.
"""
import logging
from pathlib import Path

import qgis.core
from qgis.PyQt import (
    QtGui,
    QtWidgets,
)

import GeODinQGIS.gqgis_config as gqc
from GeODinQGIS import res
from GeODinQGIS.ui.gqgis_bas import GQgis_Bas_Widget

CONTEXT = "GQgis_Styles"
log = logging.getLogger(f"{gqc._LOG_PARENTS}GQgis_Styles")

_SETTINGS_KEY = "GeODinQGIS/styleFile%s"
GROUPS = ('LOC', 'INV')
"""query groups: LOC - objects, INV - measurement points (see GoQuery.Kind)"""

LABEL_FIELDS = ('LONGNAME', 'longname', 'LongName')
"""field with the long name of the objects (GeoDin GeoJSON export)"""

# 10/2026: label expressions - attribute(@feature, '<field>') returns NULL if the layer has no
#   such field (a field reference "<field>" would make the whole expression invalid);
#   empty texts count as missing (nullif(trim(...), ''))
LABEL_EXPRESSION_LOC = """coalesce(
  nullif(trim(to_string(attribute(@feature, 'LONGNAME'))), ''),
  nullif(trim(to_string(attribute(@feature, 'SHORTNAME'))), ''),
  attribute(@feature, 'INVID')
)"""
"""objects: long name, else short name, else INVID"""

LABEL_EXPRESSION_INV = """with_variable('name',
  coalesce(
    nullif(trim(to_string(attribute(@feature, 'LONGNAME'))), ''),
    nullif(trim(to_string(attribute(@feature, 'SHORTNAME'))), '')
  ),
  with_variable('inv', nullif(trim(to_string(attribute(@feature, 'INVNAME'))), ''),
    with_variable('zb', attribute(@feature, 'INVZBEG'),
      with_variable('ze', attribute(@feature, 'INVZEND'),
        coalesce(
          nullif(
            concat(
              @name,
              if(@name IS NOT NULL AND @inv IS NOT NULL, ' - ', ''),
              @inv,
              CASE
                WHEN @zb IS NOT NULL AND @ze IS NOT NULL
                  THEN ' (' || to_string(@zb) || ' m - ' || to_string(@ze) || ' m)'
                WHEN @zb IS NOT NULL THEN ' (' || to_string(@zb) || ' m)'
                WHEN @ze IS NOT NULL THEN ' (' || to_string(@ze) || ' m)'
                ELSE ''
              END
            ),
            ''
          ),
          attribute(@feature, 'INVID')
        )
      )
    )
  )
)"""
"""measurement points: 'LONGNAME/SHORTNAME - INVNAME (INVZBEG m - INVZEND m)'
    (filters, samples and boreholes have different fields: missing parts are left out;
    nothing at all -> INVID)"""


def trans(key):
    return res.translate(CONTEXT, key)


# ------------------------------------------------------------------------------------ settings
def styleFile(group):
    """returns the style file (*.qml) for the query group 'LOC' or 'INV' ('' if not set)"""
    return str(qgis.core.QgsSettings().value(_SETTINGS_KEY % group, "", type=str) or "")


def setStyleFile(group, filename):
    qgis.core.QgsSettings().setValue(_SETTINGS_KEY % group, str(filename or ""))


# ------------------------------------------------------------------------------------ styles
def _pointGeometryType():
    try:
        return qgis.core.Qgis.GeometryType.Point            # QGIS >= 3.30
    except AttributeError:
        return qgis.core.QgsWkbTypes.PointGeometry


def _labelField(layer):
    names = {fld.name().lower(): fld.name() for fld in layer.fields()}
    for name in LABEL_FIELDS:
        if name.lower() in names:
            return names[name.lower()]
    return ""


def _setLabels(layer, expression):
    """labels with an expression, 9 pt with white buffer (10/2026)"""
    pal = qgis.core.QgsPalLayerSettings()
    pal.fieldName = expression
    pal.isExpression = True
    pal.enabled = True
    fmt = qgis.core.QgsTextFormat()
    fmt.setSize(9)
    fmt.setColor(QtGui.QColor(30, 30, 30))
    buf = qgis.core.QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setSize(0.8)
    buf.setColor(QtGui.QColor(255, 255, 255))
    fmt.setBuffer(buf)
    pal.setFormat(fmt)
    layer.setLabeling(qgis.core.QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)


# 10/2026: symbols of the measurement point types (INVID characters 11-13, e.g. WYYYL40002FIL001)
MESPOINT_SYMBOLS = (
    # (types, label, marker, fill color, outline color)
    #   SEP3/SEP1: BRG, FIL, PRB - EN ISO (E2): E2L, E2F, E2S - G1 Location: G1L, G1F, G1S
    (('BRG', 'E2L', 'G1L'), 'Bohrung / borehole', 'circle', '230,30,30', '120,0,0'),
    (('FIL', 'E2F', 'G1F'), 'Filter / screen', 'circle', '30,90,220', '0,30,120'),
    (('PRB', 'E2S', 'G1S'), 'Proben / samples', 'square', '30,90,220', '0,30,120'),
)
"""default symbols per measurement point type; other types: grey circle"""


def _marker(name, color, outline, size='2.6'):
    return qgis.core.QgsMarkerSymbol.createSimple({
        'name': name,
        'color': color,
        'outline_color': outline,
        'outline_width': '0.3',
        'size': size,
    })


def _defaultMesPointStyle(layer):
    """measurement points: symbol per type, labels 'name - INVNAME (depths)' (10/2026)

    Rule-based renderer with the type from the INVID (also for user queries with several
    measurement point types): boreholes red circles, filters blue circles, samples blue
    squares, other types grey circles.
    """
    # _setLabels(layer, LABEL_EXPRESSION_INV)
    if layer.geometryType() == _pointGeometryType():
        root = qgis.core.QgsRuleBasedRenderer.Rule(None)
        typeExpr = "substr(to_string(attribute(@feature, 'INVID')), 11, 3)"
        for invTypes, label, marker, color, outline in MESPOINT_SYMBOLS:
            values = ", ".join(f"'{t}'" for t in invTypes)
            root.appendChild(qgis.core.QgsRuleBasedRenderer.Rule(
                _marker(marker, color, outline), 0, 0, f"{typeExpr} IN ({values})", label
            ))
        # 'ELSE' rule (filter expression ELSE): only if no other rule matches
        root.appendChild(qgis.core.QgsRuleBasedRenderer.Rule(
            _marker('circle', '150,150,150', '70,70,70'), 0, 0, "ELSE", "other"
        ))
        layer.setRenderer(qgis.core.QgsRuleBasedRenderer(root))
    _setLabels(layer, LABEL_EXPRESSION_INV)


def _defaultObjectStyle(layer):
    """red circle markers and labels with the long name"""
    if layer.geometryType() == _pointGeometryType():
        symbol = qgis.core.QgsMarkerSymbol.createSimple({
            'name': 'circle',
            'color': '230,30,30',
            'outline_color': '120,0,0',
            'outline_width': '0.3',
            'size': '2.6',
        })
        layer.setRenderer(qgis.core.QgsSingleSymbolRenderer(symbol))
    # 10/2026: label expression long name / short name / INVID instead of the field LONGNAME
    _setLabels(layer, LABEL_EXPRESSION_LOC)
    return
    field = _labelField(layer)
    if field:
        pal = qgis.core.QgsPalLayerSettings()
        pal.fieldName = field
        pal.enabled = True
        fmt = qgis.core.QgsTextFormat()
        fmt.setSize(9)
        fmt.setColor(QtGui.QColor(30, 30, 30))
        buf = qgis.core.QgsTextBufferSettings()
        buf.setEnabled(True)
        buf.setSize(0.8)
        buf.setColor(QtGui.QColor(255, 255, 255))
        fmt.setBuffer(buf)
        pal.setFormat(fmt)
        layer.setLabeling(qgis.core.QgsVectorLayerSimpleLabeling(pal))
        layer.setLabelsEnabled(True)
    else:
        log.info("Layer '%s': no field LONGNAME for the labels", layer.name())


def applyLayerStyle(layer, group):
    """applies the style to a new GeoDin layer

    args:
        layer (QgsVectorLayer)  - new GeoDin layer (not yet added to the project)
        group (str)             - 'LOC' (objects) or 'INV' (measurement points)

    returns:
        message (str)           - warning text if the style file could not be loaded, else ''
    """
    message = ""
    qml = styleFile(group)
    if qml:
        if Path(qml).is_file():
            try:
                msg, ok = layer.loadNamedStyle(qml)
                if ok:
                    log.debug("Layer '%s': style '%s'", layer.name(), qml)
                    return ""
                message = trans("The layer style could not be loaded:") + f"\n{qml}\n{msg}"
            except Exception as exc:
                message = trans("The layer style could not be loaded:") + f"\n{qml}\n{exc}"
        else:
            message = trans("The layer style file does not exist:") + f"\n{qml}"
        log.warning(message)
    if group == 'LOC':
        try:
            _defaultObjectStyle(layer)
        except Exception:
            log.error("Default style for layer '%s' failed", layer.name(), exc_info=True)
    elif group == 'INV':
        # 10/2026: labels for measurement points
        try:
            _defaultMesPointStyle(layer)
        except Exception:
            log.error("Default style for layer '%s' failed", layer.name(), exc_info=True)
    return message


# -------------------------------------------------------------------------------------- dialog
class GQgis_Dlg_Styles(QtWidgets.QDialog):
    """dialog: style files (*.qml) for object and measurement point layers

    10/2026
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(trans("GeoDinQGIS - Layer styles"))
        self.setWindowIcon(GQgis_Bas_Widget.QIcon("gQgis"))
        self.setMinimumWidth(620)
        lay = QtWidgets.QVBoxLayout(self)
        lbl = QtWidgets.QLabel(trans(
            "Style files (QGIS layer style *.qml) that are applied when a GeoDin layer is added.\n"
            "Create a style file in QGIS: Layer properties » Symbology » Style » Save Style..."))
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        grid = QtWidgets.QGridLayout()
        self._edits = {}
        rows = (
            # 10/2026: default labels with long name / short name (objects) and
            #   name - INVNAME (depths) (measurement points)
            ('LOC', trans("Objects"), trans("empty: red circles, label long name or short name")),
            ('INV', trans("Measurement points"), trans("empty: boreholes red, filters blue, samples blue squares")),
        )
        for row, (group, title, hint) in enumerate(rows):
            grid.addWidget(QtWidgets.QLabel(title), row * 2, 0)
            edit = QtWidgets.QLineEdit(styleFile(group))
            edit.setPlaceholderText(hint)
            edit.setClearButtonEnabled(True)
            grid.addWidget(edit, row * 2, 1)
            btn = QtWidgets.QToolButton()
            btn.setIcon(GQgis_Bas_Widget.QIcon("FolderOpen"))
            btn.setToolTip(trans("Choose style file..."))
            btn.clicked.connect(lambda checked=False, e=edit: self._browse(e))
            grid.addWidget(btn, row * 2, 2)
            self._edits[group] = edit
        lay.addLayout(grid)
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        btns.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setText(trans("Cancel"))
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _browse(self, edit):
        start = edit.text() or str(Path.home())
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, trans("Choose style file..."), start,
            trans("QGIS layer style") + " (*.qml)")
        if filename:
            edit.setText(filename)

    def _accept(self):
        for group, edit in self._edits.items():
            qml = edit.text().strip()
            if qml and not Path(qml).is_file():
                QtWidgets.QMessageBox.warning(
                    self, self.windowTitle(),
                    trans("The layer style file does not exist:") + f"\n{qml}")
                return
        for group, edit in self._edits.items():
            setStyleFile(group, edit.text().strip())
        self.accept()


def showStylesDialog(parent=None):
    GQgis_Dlg_Styles(parent).exec()
