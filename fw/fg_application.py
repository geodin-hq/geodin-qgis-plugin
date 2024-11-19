#-------------------------------------------------------------------------------
# Name:        Modul1
# Purpose:
#
# Author:      j.ebert
#
# Created:     26.08.2022
# Copyright:   (c) j.ebert 2022
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os
from pathlib import Path

# global settings...
_company = 'Fugro'
_product = Path(__file__).parents[1].name

class EnvDict(dict):
    """ customiced Python dict class

    19.11.2021 j.ebert
    """
    __getattr__= dict.__getitem__
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__

class Env:
    """ environment class

    26.08.2022 J.Ebert
    """

    def __init__(self):
        self._LocalAppData = None
        self._TmpFolder = None

    @property
    def Company(self):
        """ company name (str)

        26.08.2022 J.Ebert
        """
        return _company

    @property
    def Product(self):
        """ produkt name (str)

        26.08.2022 J.Ebert
        """
        return _product

    @property
    def AppName(self):
        """ application name (str)

        26.08.2022 J.Ebert
        """
        return Path(__file__).parents[1].name

    @property
    def AppPath(self):
        """ application path/location (Path)

        26.08.2022 J.Ebert
        """
        return Path(__file__).parents[1]

    @property
    def LocalAppData(self):
        """ local application data folder (Path)

        26.08.2022 J.Ebert
        """
        if not self._LocalAppData:
            # Wenn die Systemvariable LOCALAPPDATA nicht existiert,
            # dann wird der Benutzerordner/das Benutzerverzeichnis auf dem Computer genutzt
            self._LocalAppData = Path(
                os.getenv('LOCALAPPDATA', Path.home()), self.Company, self.Product)
            self._LocalAppData.mkdir(parents=True, exist_ok=True)
        return self._LocalAppData

    @property
    def TmpFolder(self):
        """ local temp Folder (Path)

        26.08.2022 J.Ebert
        """
        if not self._TmpFolder:
            # Wenn die Systemvariable LOCALAPPDATA nicht existiert,
            # dann wird der Benutzerordner/das Benutzerverzeichnis auf dem Computer genutzt
            self._TmpFolder = Path(self.LocalAppData / 'tmp')
            self._TmpFolder.mkdir(parents=True, exist_ok=True)
        return self._TmpFolder



def main():
    env = Env()
    print(f"""
    env.Company             {env.Company}
    env.Product             {env.Product}

    env.AppName             {env.AppName}
    env.AppPath             {env.AppPath}

    env.LocalAppData        {env.LocalAppData}
    env.TmpFolder           {env.TmpFolder}

    """)

if __name__ == '__main__':
    main()
