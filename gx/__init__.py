""" GeODin Extension


06.03.2023 j.ebert
"""
__company__ = 'Fugro'
__product__ = 'FGIS'
__version__ = '0.1.1'
__author__ = 'j.ebert'
__license__ = 'GPL-2.0-or-later'
__author_email__ = 'j.ebert@fugro.com'
__maintainer_email__ = 'j.ebert@fugro.com'
__url__ = 'www.furgo.com'

test = "einfacher String"
from .client import GxCOMClient
from .geodin import GxSQL  # noqa: F401 - re-export

gApp = GxCOMClient()