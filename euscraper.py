import dataset
import sys, time
import logging,requests
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)s %(filename)s:%(lineno)s %(message)s')

from scrapelib import TreeScraper, TextParser
logger=logging.getLogger(__name__)
from insertversioned import update_if_different 
import random

DEBUG=0
LANG="en"

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

data='datatype=entity&datalang={LANG}&lang={LANG}&orderby=NOM&newSearch=true&institution=10&entity_name=&RES_MAX=90000&btnSearch=Suche'.format(**locals())
url='http://europa.eu/whoiswho/public/index.cfm?fuseaction=idea.search_entity'

parsedeplink=TextParser("nodeID=(?P<nid>\d+)")
parseperslink=TextParser("personID=(?P<pid>\d+)")

def depts() :
	t=TreeScraper()
	if DEBUG :
		t.debuglevel(1)
	for tries in xrange(0,5) :
		try :
			t.fetch(url,data=data,headers=headers)
		except Exception,e :
			logger.exception(e)
			logger.debug("Try #%s after 5 seconds" % tries)
			time.sleep(5)
		else :
			break
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
		dep.update(parsedeplink(dep["link"]))
		del dep["path"]
		del dep["link"]
	return filter(lambda a: a.get("nid",None),all)

def pers(depid) :
	t=TreeScraper()
	if DEBUG :
		t.debuglevel(1)
	try :
		t.fetch("http://europa.eu/whoiswho/public/index.cfm?fuseaction=idea.hierarchy&nodeID=%s" % depid, headers=headers)
		all=t.extract("table#mainContent li",link="./a[contains(@href,'personID')]/@href",
						     name="./a[contains(@href,'personID')]/text() ",
						     func="./text()")
	except requests.HTTPError,e :
		logger.exception(e)
		all=[]
	for per in all :
		if per :
			per["func"]=per["func"][1]
			per.update(parseperslink(per["link"]))
			per.update(parsedeplink(per["link"]))
			del per["link"]
	return filter(lambda a: a, all)


def runspider(db) :
	tables={ "dept" : db["dept"], "pers" : db["pers"] }
	depl=depts()
	update={ "dept" :[], "pers" : []}
	firstrun=True
	random.shuffle(depl)
	for d in depl :
		update["dept"].append(update_if_different(tables["dept"],d,["nid"],"versions"))
		for p in pers(d["nid"]) :
			update["pers"].append(update_if_different(tables["pers"],p,["pid","nid"],"versions"))
		if not firstrun :
			db.commit()
		else :
			firstrun=False
		db.begin()
		logger.info("{pers} persons, {pupdate} updated; {deps} depts, {dupdate} updated".format(pers=len(update["pers"]),pupdate=len(filter(lambda a: a, update["pers"])), deps=len(update["dept"]),dupdate=len(filter(lambda a: a, update["dept"]))))
	return update


if __name__=='__main__' :
	import sys
	logging.basicConfig(file=sys.stderr,level=logging.DEBUG)
	import pprint
	update={"dept": [], "pers" : []}
	try:
		db=dataset.connect("sqlite:///data.db")
		update=runspider(db)
	except Exception,e:
		logger.exception(e)	
	logger.info("{pers} persons, {pupdate} updated; {deps} depts, {dupdate} updated".format(pers=len(update["pers"]),pupdate=len(filter(lambda a: a, update["pers"])), deps=len(update["dept"]),dupdate=len(filter(lambda a: a, update["dept"]))))
