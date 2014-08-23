import logging,sys,StringIO

b=StringIO.StringIO()

logging.basicConfig(file=b, level=logging.DEBUG)

from slscraper import eventdata

eventdata("184792",),b.getvalue()
