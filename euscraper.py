import dataset
import sys
import logging
logging.basicConfig(level=logging.DEBUG)
from scrapelib import TreeScraper, TextParser
logger=logging.getLogger(__name__)
import httplib
httplib.HTTPConnection.debuglevel = 1


initial_curl="""curl 'http://europa.eu/whoiswho/public/index.cfm?fuseaction=idea.search_entity' -H 'Pragma: no-cache' -H 'Origin: http://europa.eu' -H 'Accept-Encoding: gzip,deflate' -H 'Accept-Language: en;q=0.8,en;q=0.6,es;q=0.4' -H 'User-Agent: Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36' -H 'Content-Type: application/x-www-form-urlencoded' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Referer: http://europa.eu/whoiswho/public/index.cfm?fuseaction=idea.entity' -H 'Cookie: CFID=121410243; CFTOKEN=65187697; JSESSIONID=38059ae293d871573d42' -H 'Connection: keep-alive' --data 'datatype=entity&datalang=de&lang=de&orderby=NOM&newSearch=true&institution=10&entity_name=&RES_MAX=90000&btnSearch=Suche' --compressed"""


headers=dict([a.split(": ",1) for a in [	'Pragma: no-cache',
				      	'Origin: http://europa.eu',
					'Accept-Encoding: gzip,deflate',
					'Accept-Language: en;q=0.8,en;q=0.6,es;q=0.4',
					'User-Agent: Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36',
					'Content-Type: application/x-www-form-urlencoded',
					'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
					'Cache-Control: no-cache',
					'Referer: http://europa.eu/whoiswho/public/index.cfm?fuseaction=idea.entity' ]])

data='datatype=entity&datalang=de&lang=de&orderby=NOM&newSearch=true&institution=10&entity_name=&RES_MAX=90000&btnSearch=Suche'
url='http://europa.eu/whoiswho/public/index.cfm?fuseaction=idea.search_entity'

parselink=TextParser("nodeID=(?P<id>\d+)")

def depts() :
	try :
		t=TreeScraper(url,data=data,headers=headers)
	except Exception, e:
		logger.exception(e)
	else :
		# return t.extract("table#mainContent a",link="a[@href]",text="a/text()")
		all=t.extract("#mainContent a",text="./text()",link="./@href")
		for dep in all :
			dep["path"]=dep.get("text","").split("; ")
			dep["depth"]=len(dep["path"])
			if len(dep["path"])>0 :
				dep["name"]=dep["path"][-1]
			else :
				dep["name"]=None
			if len(dep["path"])>1 :
				dep["parent"]=dep["path"][-2]
			else :
				dep["parent"]=None
			dep.update(parselink(dep["link"]))
			del dep["path"]
		return all


if __name__=='__main__' :
	import sys
	logging.basicConfig(file=sys.stderr,level=logging.DEBUG)
	import pprint
	pprint.pprint(depts())