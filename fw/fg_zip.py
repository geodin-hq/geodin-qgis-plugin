#-------------------------------------------------------------------------------
# Name:        Modul1
# Purpose:
#
# Author:      j.ebert
#
# Created:     15.09.2022
# Copyright:   (c) j.ebert 2022
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# seealso
#   https://stackoverflow.com/questions/513788/delete-file-from-zipfile-with-the-zipfile-module
#-------------------------------------------------------------------------------
import json
import zipfile


config = {
    "int": 1234,
    "dbl": 1234.90840,
    "str": 'abcd',
    "featurecoll":  [
        [[1,2,3]
        ]
        ]}
row = [
    'das ist der erste test',
    21345,
    456.789]

def make_archive_annoying(path="test.zip"):
    # This does work but is annoying
    # Also note, this will write to the root of the archive, and when unzipped will not
    # unzip to a directory but rather into the same directory as the zip file
    with zipfile.ZipFile(path, "a") as z:
        with z.open("row.json", "w") as c:
            c.write(json.dumps(row, indent=4).encode("utf-8"))

##        with z.open("data.json", "w") as d:
##            for row in data(config):
##                d.write(json.dumps(row).encode("utf-8"))
##                d.write("\n".encode("utf-8"))

def load(path="test.zip"):
    with zipfile.ZipFile(path, "r") as z:
        with z.open("row.json", "r") as c:
##            c.write(json.dumps(row, indent=4).encode("utf-8"))
            o = json.loads( c.read())
    return o

def delete(in_name, out_name, item_name):
    with zipfile.ZipFile(in_name, "r") as zi, zipfile.ZipFile(out_name, "w") as zo:
        for item in zi.infolist():
            print(item)
            if item.filename != item_name:
                buffer = zi.read(item.filename)
                zo.writestr(item, buffer)

def update():
    """
    Args:
        ZIP-Filename
        Update-Liste    - list of tuple(name, object|None)
                            name    ~> JSON-Filename im ZIP-File
                            object  ~> löschen und object JSON speichern
                            None    ~> löschen
    Notes
        tuple(name, object|None) - sollte function einer Klasse sein
            untergeordente Klassen liefern das an übergeordente Klasse, damit
            kann ein strukturiertes Dictinary aufgebaut werden
            root klasse/obertse Klasse liefert an save funktion
    """
    # ZIP-Filename
    # BAK-Filename
    # BAK-File löschen, sofern es existiert
    # ZIP-File umbenennen in BAK-File
    # BAK- und ZIP-File öffnen und Inhalt kopieren, sofern nicht aktualisiert/gelöschet werden soll
    # zu aktualsierenden Inhalt hinzufügen

##zin = zipfile.ZipFile ('archive.zip', 'r')
##zout = zipfile.ZipFile ('archve_new.zip', 'w')
##for item in zin.infolist():
##    buffer = zin.read(item.filename)
##    if (item.filename[-4:] != '.exe'):
##        zout.writestr(item, buffer)
##zout.close()
##zin.close()

def main():
    pass

if __name__ == '__main__':
    main()
    fname = r"C:\Data\GeODinQGIS\temp\test.gxtn"
    oname = r"C:\Data\GeODinQGIS\temp\test_new.gxtn"
##    make_archive_annoying(fname)
##    unz_row = load(fname)
##    delete(fname, oname, "row.json")
    text = json.dumps(config, indent=4)

