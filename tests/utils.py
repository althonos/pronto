import os
import sys

try:
    from unittest import mock
except ImportError:
    import mock

# Import several available etrees
from xml.etree import ElementTree as xml_etree
try:
    from lxml import etree as lxml_etree
except ImportError:
    lxml_etree = None
try:
    from xml.etree import cElementTree as cxml_etree
except ImportError:
    cxml_etree = None



TESTDIR = os.path.dirname(os.path.abspath(__file__))
MAINDIR = os.path.dirname(TESTDIR)
DOCSDIR = os.path.join(MAINDIR, "docs")
DATADIR = os.path.join(TESTDIR, "resources")
RUNDIR = os.path.join(TESTDIR, "run")

# Force importing the local version of the module
sys.path.insert(0, MAINDIR)

# Launch a stub HTTP server to server local files
from .stubs import StubHTTPServer
StubHTTPServer(DATADIR).start()
