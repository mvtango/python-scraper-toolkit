from slscraper import listevents,eventdata
from dumptruck import DumpTruck
import random   
import os,sys
import logging
from sqlite3 import OperationalError
import datetime

logging.basicConfig(level=logging.DEBUG,file=sys.stdout,format='%(levelname)s %(asctime)-15s %(filename)s %(lineno)s %(message)s')
logger=logging.getLogger(os.path.split(__file__)[1])

_here=os.path.split(__file__)[0]

dt=DumpTruck(dbname=os.path.join(_here,"data/events.sqlite"))
try :
	dt.create_index(["id"],"events",unique=True)
	dt.create_index(["url"],"events",unique=True)
except OperationalError :
	pass

def scrape_now() :
	nn=0
	for l in listevents() :
		try :
			d=dt.execute("select count(*) as c from events where url='%(url)s'" % l)
		except OperationalError :
			d=[{ "c" : 0 }]
			pass
		if d[0]["c"]==0 :
			l.update(eventdata(l["url"]))
			logger.info("found new %s %s" % (l.get("id",l.get("threadid","")),l.get("title","")))
			if l["url"] is not None :
				dt.upsert(l,"events")
				nn+=1
		else :
			pass #	logger.debug("now - %(url)s already scraped" % l)
	return nn


sc=0

scrape_now()

mid=dt.execute("select max(id) as c from events")[0]["c"]
mid=778540
err=0
lmid=mid
done={}
samestatus=0
lstatus=""
start=datetime.datetime.now()

while True :
	idt="%s" % random.randrange(1,mid)
	if idt in done :
		sc=sc+1
	else :
		d=dt.execute("select count(*) as c from events where id='%s'" % idt)
		if d[0]["c"]==1 :
			# logger.debug("%s already scraped" % idt)
			sc=sc+1
			done[idt]=1
		else :
			try :
				dt.upsert(eventdata(idt),"events")
			except Exception, e:
				logger.exception("ERROR %s " % (idt,))
				err+=1
			sc=sc+1
	if (sc % 100)==0 :
		nn=scrape_now()
		tc=dt.execute("select count(*) as c from events")
		pc=dt.execute("select count(*) as c from events where numposts>0")
		mc=dt.execute("select max(id) as c from events")
		mid=mc[0]["c"]
		status="################ %s of %s scraped, %s with posts, %s with errors" % (tc[0]["c"],mid,pc[0]["c"],err)
		logger.info(status)
		if status==lstatus :
				samestatus+=1
				if samestatus>999 : # or nn==0 
					break
		else :
			lstatus=status
			samestatus=0
logger.info("finished after %s seconds" %	(datetime.datetime.now()-start,))	
