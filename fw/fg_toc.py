#-------------------------------------------------------------------------------
# Name:        Modul1
# Purpose:
#
# Author:      j.ebert
#
# Created:     26.09.2022
# Copyright:   (c) j.ebert 2022
# Licence:     <your licence>
#   How can I write a function in python to write the file names of directory with the output of my function to a dataframe?
#   https://stackoverflow.com/questions/68368837/how-can-i-write-a-function-in-python-to-write-the-file-names-of-directory-with-t
#   https://www.geeksforgeeks.org/python-get-list-of-files-in-directory-with-size/

#   https://stackoverflow.com/questions/64767131/remove-and-replace-pandas-dataframe-in-excel-sheet
#-------------------------------------------------------------------------------
import os
from pathlib import Path
import pandas as pd
import win32security


def win32owner(filename):
    """
    https://stackoverflow.com/questions/71018167/get-owner-of-a-file-using-python-on-windows-system
    """
    name = ''
    if 'win32security' in globals():
        sd = in32security.GetFileSecurity(file, win32security.OWNER_SECURITY_INFORMATION)
        owner_sid = sd.GetSecurityDescriptorOwner()
        name, domain, type = win32security.LookupAccountSid(None, owner_sid)
    return name

def write2excel(filename,sheetname,dataframe):
    """
    https://stackoverflow.com/questions/64767131/remove-and-replace-pandas-dataframe-in-excel-sheet
    """
    with pd.ExcelWriter(filename, engine='openpyxl', mode='a') as writer:
        workBook = writer.book
        try:
            workBook.remove(workBook[sheetname])
        except:
            print("There is no such sheet in this file")
        finally:
            dataframe.to_excel(writer, sheet_name=sheetname,index=False)
            writer.save()

def _load_patterns(ignore_file):
    """lädt die Pattern uas der Ignore-Datei

    Args:
        filname                 - Textdatei/Ignore-Datei

    Sytax einer Ignore-Datei:
        # Achtung
        #   Jockerzeichen "?" und "*" (sind ggf. vom abhängig vom OS)
        #
        # Einfacher Dateipfad
        irgendwie/unerwuenscht.txt
        #
        # Verzeichnisse werden mit einem "/" abgeschlossen
        generated/
        #
        # Dateitypen als glob-Ausdruck
        *.bak
        #
        # "!" markiert Ausnhamen
        # "demo.bak" wird eingschlossen, obwohl "*.bak" ausgenommen wurde.
        !demo.bak

    26.09.2022 J.Ebert
    """
    patterns = {
        # Exclude Pattern...
        'xaDir':    [],     # exakte/"absolte" Verz.-Pattern
        'xaFile':   [],     # exakte/"absolute" Datei-Pattern
        'xrDir':    [],     # einfache/relative Verz.-Pattern
        'xrFile':   [],     # einfache/relative Datei-Pattern
        # Include Pattern/Ausnahmen...
        'iaDir':    [],     # exakte/"absolute" Verz.-Pattern
        'iaFile':   [],     # exakte/"absolute" Datei-Pattern
        'irDir':    [],     # einfache/relative Verz.-Pattern
        'irFile':   [],     # einfache/relative Datei-Pattern
        }
    if ignore_file:
        # File mit Ignore-Pattern einlesen...
        # - jede Ziele in der Textdatei enthält genu ein Pattern
        # - Whitespaces (inkl. '\n') am Zeilen anfang und -ende entfernen
        with open(ignore_file, "r") as xfo:
            rows = rows = [row.strip() for row in xfo.readlines()]
        # Pattern differenzieren und formatieren... (also mit "/"
        # "!" am Zeilenanfang markiert Ausnahmen
        # "/" als Seperator/Verzeichnis-Trennzeichen
        # Achtung
        #   Hier muss mit String-Funktionen gearbeitet werden, da bei Path-Funktionen
        #   automatisch ein Verzeichnis-Trennzeichen am Ende gelöscht würde, aber damit
        #   würde die Differenzierung zwischen Dir-Pattern und File-Pattern gelöscht!
        #   Beispiel:
        #       Path('__pycache__/').as_posix()     ~> '__pycache__'
        #            '__pycache__/' - Dir-Pattern   ~> '__pycache__' - File-Pattern
        # - Include-Pattern, wenn die Zeile mit "!" beginnt - ist eine Ausnahme!
        iRows = [row[1:].replace("\\",'/') for row in rows if row.startswith("!")]
        # - Exclude-Pattern, wenn die Zeile NICHT mit "!" beginnt
        xRows = [row.replace("\\",'/') for row in rows if (not row.startswith("!"))]
        print(f"""
include Pattern...
{iRows}

exclude Pattern...
{xRows}
        """)
        # Pattern-Dictionary erstellen
        # - exakte/absolute Pattern beginnen mit "/" und
        #    werden nur ausgehend vom Wurzelverzeichnis berücksichtigt
        # - einfache/relative Pattern beginnen NICHT mit "/" und
        #   werden überall berücksichtigt
        patterns = {
            # Exclude Pattern...
            # - exakte/"absolte" Verz.-Pattern, beginnen mit "/" und enden mit "/"
            'xaDir':    [row[1:] for row in xRows if row.startswith("/") and row.endswith("/")],
            # - exakte/"absolute" Datei-Pattern, beginnen mit "/" und enden NICHT mit "/"
            'xaFile':   [row[1:] for row in xRows if row.startswith("/") and (not row.endswith("/"))],
            # - einfache/relative Verz.-Pattern, beginnen NICHT mit "/" und enden mit "/"
            'xrDir':    [row for row in xRows if (not row.startswith("/")) and row.endswith("/")],
            # - einfache/relative Datei-Pattern, beginnen NICHT mit "/" und enden NICHT mit "/"
            'xrFile':   [row for row in xRows if (not row.startswith("/")) and (not row.endswith("/"))],
            # Include Pattern/Ausnahmen...
            # - exakte/"absolute" Verz.-Pattern, beginnen mit "/" und enden mit "/"
            'iaDir':    [row[1:] for row in iRows if row.startswith("/") and row.endswith("/")],
            # - exakte/"absolute" Datei-Pattern, beginnen mit "/" und enden NICHT mit "/"
            'iaFile':   [row[1:] for row in iRows if row.startswith("/") and (not row.endswith("/"))],
            # - einfache/relative Verz.-Pattern, beginnen NICHT mit "/" und enden mit "/"
            'irDir':    [row for row in iRows if (not row.startswith("/")) and row.endswith("/")],
            # - einfache/relative Datei-Pattern, beginnen NICHT mit "/" und enden NICHT mit "/"
            'irFile':   [row for row in iRows if (not row.startswith("/")) and (not row.endswith("/"))],
            }
    # Pattern-Dictionary zurückgeben
    return patterns

def _glob_files(dirname, patterns):
    """Files entsprechend der Pattern listen

    Args:
        dirname     (str)       - Verzeichnis, ab dem die Files gelistet werden
        patterns    (list(str)) - Liste der File-Pattern
    Returns:
        files       (list(str)) - Liste der Filenamen (inkl. Path)

    26.09.2022 J.Ebert
    """
    files = []
    dirpath = Path(dirname)
    for pattern in patterns:
        files += [str(kind) for kind in dirpath.glob(pattern)]
    return files

def _generic_dir_item(
        rootpath,
        dirpath
        ):
    return dirpath.relative_to(rootpath)

def _generic_file_item(
        rootpath,
        dirpath,
        filename):
    return (dirpath / filename).relative_to(rootpath)

def walk(root, ignore_file=None):
    """
    26.09.2022 J.Ebert
    """
    files = []
    dir_func = _generic_dir_item
    file_func = _generic_file_item
    rootPath = Path(root)
    # Pattern-Dictionray laden...
    patterns = _load_patterns(ignore_file)
    # Exclude-/Include-Liste der Verzeichnis- und Dateinamen initialisieren...
    # Hinweis
    #   Exclude-/Include-Listen mit den exakten/"absoluten" Pattern initialisieren.
    exc_dirnames = _glob_files(root, patterns.get('xaDir',[]))
    exc_filenames = _glob_files(root, patterns.get('xaFiles',[]))
    inc_dirnames = _glob_files(root, patterns.get('iaDir',[]))
    inc_filenames = _glob_files(root, patterns.get('iaFiles',[]))
    # letztes Verzeichnis initialisieren
    lst_dirname = ""
    for dirname, subdirnames, filenames in os.walk(root):
        # Exclude-/Include-Listen mit einfachen/relativen Pattern ergänzen, wenn
        # sich das aktuelle Verzeichnis geändert hat/nicht identisch mit dem letzten ist
        if dirname != lst_dirname:
            dirpath = Path(dirname)
            exc_dirnames += _glob_files(dirname, patterns.get('xrDir',[]))
            exc_filenames += _glob_files(dirname, patterns.get('xrFiles',[]))
            inc_dirnames += _glob_files(dirname, patterns.get('irDir',[]))
            inc_filenames += _glob_files(dirname, patterns.get('irFiles',[]))
            lst_dirname = dirname
        # Filnames für das akt. Verzeichnis filtern...
        if (dirname in inc_dirnames) or (dirname not in exc_dirnames):
            # Wenn das akt. Verzeichnis NICHT ausgeschlossen ist,
            # dann Filenamen filtern,
            #   für die ein Include-Pattern/eine Ausnahme definiert ist oder
            #   die NICHT ausgeschlossen sind
            filtered_filenames = [filename for filename in filenames if
                (str(dirpath / filename) in inc_filenames) or
                (str(dirpath / filename) not in exc_filenames)
                ]
            # Wenn das akt. Verzeichnis NICHT ausgeschlossen ist,
            # dann immer Dir-Function ausführen...
            files.append(dir_func(rootPath, dirpath))
        else:
            # Wenn das akt, Verzeichnis ausgeschlossen ist,
            # dann Filenamen filtern, für die ein Include-Pattern/eine Ausnahme definiert ist
            filtered_filenames = [filename for filename in filenames if
                (str(dirpath / filename) in inc_filenames)
                ]
            # Wenn das akt, Verzeichnis ausgeschlossen ist,
            # dann Dir-Function nur ausführen, wenn...
            if filtered_filenames:
                files.append(dir_func(rootPath, dirpath))

        # gefilterte Filenamen sequntiell durchlaufen...
        for filename in filtered_filenames:
            files.append(file_func(rootPath, dirpath, filename))
    print(f"""
exclude dirs...
{exc_dirnames}

exclude files...
{exc_filenames}
    """)
    return files

def main():
    pass

if __name__ == '__main__':
    xf_gqgis = r"C:\Data\GeODinQGIS\repos\gQGIS_3\.gitignore"
    main()
