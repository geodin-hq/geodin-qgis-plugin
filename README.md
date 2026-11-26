# GeoDinQGIS

QGIS plugin that connects [GeoDin](https://www.geodin.com) with QGIS: it shows the GeoDin projects and queries in QGIS, adds them as layers and runs GeoDin functions (selection, hotlink, create object) from the map.

Published on plugins.qgis.org as [GeODinQGIS](https://plugins.qgis.org/plugins/GeODinQGIS/).

## Requirements

- Windows with GeoDin installed
- QGIS 3.28 or newer, or QGIS 4
- Python packages in the QGIS Python environment:
  - `pywin32` (always)
  - `pyodbc` for MS Access and MS SQL Server databases
  - `psycopg2` for PostgreSQL databases
  - `oracledb` 2.0 or newer for Oracle databases

Install missing packages in the OSGeo4W Shell of the QGIS version, run as administrator, then restart QGIS:

```
python -m pip install pywin32 pyodbc psycopg2-binary oracledb
```

## Documentation

The user guide is in `help/` (German and English) and opens from the plugin's help menu.

## Development

The package folder must be named `GeODinQGIS`. To run the working copy in QGIS, link it into the QGIS profile:

```
mklink /J "%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\GeODinQGIS" "<path to this repository>"
```

Use `QGIS4` instead of `QGIS3` for QGIS 4. Never use "Install from ZIP" or "Uninstall" in QGIS on a linked profile: QGIS deletes the folder content through the link.

Logs: `%LOCALAPPDATA%\Fugro\GeODinQGIS\Logs`.

## Release

1. Raise `version` in `metadata.txt` and add the changes to `changelog` there and to `changelog.txt`.
2. Build the package from a commit:

   ```
   git archive --format=zip --prefix=GeODinQGIS/ -o GeODinQGIS.zip HEAD
   ```

3. Upload `GeODinQGIS.zip` on plugins.qgis.org.

## License

GNU General Public License, version 2 or later, see `LICENSE`.

## Support

support@geodin.com
