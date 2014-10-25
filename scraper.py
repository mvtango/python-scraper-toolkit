from slscraper import listevents,eventdata
from dumptruck import DumpTruck
import random   
import os,sys
import logging
from sqlite3 import OperationalError
import datetime
import copy,types,time

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
if "proxy" in sys.argv :
	proxy=True
else :
	proxy=None


mid=dt.execute("select max(id) as c from events")[0]["c"]
mid=795871 #794230 # 778540
err=0
lmid=mid
done={}
samestatus=0
lstatus=""
start=datetime.datetime.now()
last={ 
				'tc' : dt.execute("select count(*) as c from events")[0]["c"],
				'pc' : dt.execute("select count(*) as c from events where numposts>0")[0]["c"],
				'mid' : dt.execute("select max(id) as c from events")[0]["c"],
				'err' : err,
				'stamp' : datetime.datetime.now()
		}
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
			retry=0
			success=False
			while success==False and retry<3 :
				try :
					dt.upsert(eventdata(idt,proxy=proxy),"events")
					success=True
				except OperationalError :
					retry += 1
					time.sleep(1)
					logger.error("Retrying #%s" % retry)
				except KeyboardInterrupt :
					raise
				except Exception, e:
					logger.exception("ERROR %s " % (idt,))
					err+=1
			sc=sc+1
	if (sc % 100)==0 :
		nn=scrape_now()
		try :
			stats={ 
					'tc' : dt.execute("select count(*) as c from events")[0]["c"],
					'pc' : dt.execute("select count(*) as c from events where numposts>0")[0]["c"],
					'mid' : dt.execute("select max(id) as c from events")[0]["c"],
					'err' : err,
					'stamp' : datetime.datetime.now()
			}
			status="################ %(tc)s of %(mid)s scraped, %(pc)s with posts, %(err)s with errors" % stats
			if last :
				delta={}
				for k in stats.keys() :
					delta[k]=stats[k]-last[k]
				for k in delta.keys() :
					if type(delta[k]) in (types.IntType,types.LongType, types.StringType) :
						delta["speed_%s" % k]=float(delta[k])/(float(delta["stamp"].seconds)/60)
				delta["complete"]=100*(float(stats["tc"])/float(stats["mid"]))
				status += " +%(pc)s with posts (%(speed_pc).1f/min), +%(tc)s (%(speed_tc).1f/min) scraped; %(complete).2f %% complete" % delta
			last=copy.deepcopy(stats)
			logger.info(status)
			if status==lstatus :
					samestatus+=1
					if samestatus>999 : # or nn==0 
						break
			else :
				lstatus=status
				samestatus=0
		except KeyboardInterrupt : 
			raise
		except Exception,e :
			logger.exception("During stat")
logger.info("finished after %s seconds" %	(datetime.datetime.now()-start,))	
