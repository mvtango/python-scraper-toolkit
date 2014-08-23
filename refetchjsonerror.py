# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>
import os

_here=os.path.split("__file__")[0]

from dumptruck import DumpTruck
dt=DumpTruck(dbname=os.path.join(_here,"data/events.sqlite"))
from collections import defaultdict
from slscraper import eventdata 

d=True
c=1


while d: 
	r=dt.execute("select id from events where error like '%JSON%' order by random() limit 1")
	if len(r)>0 :
		rr=r[0]["id"]
		try :	
			dd=eventdata("%s" % rr)
			if 'error' not in dd :
				dd["error"]="--"
			dt.upsert(dd,"events")
			print "%(id)s %(title)s: %(error)s" % defaultdict(lambda : "-", dd)
			c+=1
			if (c % 10)==0 :
				r=dt.execute("select count(*) as c from events where error like '%JSON%'")
				if len(r)>0 :
					print "still %s to go" % r[0]["c"]
		except Exception, e:
			print "ERROR %s %s" % (rr,e)
	else :
		d=False
        

# <codecell>


