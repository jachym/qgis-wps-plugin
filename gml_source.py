owslib_exists = True
try:
    from owslib.wps import *
except:
    owslib_exists = False

from lxml import etree

class GmlSource(IComplexDataInput):
    def getXml(self):
        return etree.parse("/home/jencek/test2.gml").getroot()
