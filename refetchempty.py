# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>
import os

_here=os.path.split("__file__")[0]

from dumptruck import DumpTruck
dt=DumpTruck(dbname=os.path.join(_here,"data/events.sqlite"))

from slscraper import eventdata 

d=True

while d: 
    r=dt.execute("select id from events where error like '%403 Client Error%' and title is null order by id desc limit 1")
    if len(r)>0 :
        rr=r[0]["id"]
        try :
            dd=eventdata("%s" % rr)
            if "url" not in dd :
                dd["url"]=dd["id"]
            if "metatitle" in dd :
				dd["title"]=dd["metatitle"]
            dt.upsert(dd,"events")
            tc=dt.execute("select count(id) as c from events where error like '%403 Client Error%' and title is null") 
            print "(%s) %s,%s" % (tc[0]["c"], rr,repr(dt.execute("select title,start,id from events where id=%s" % rr)))
        except Exception, e:
            print "ERROR %s %s" % (rr,e)
    else :
        d=False
        

# <codecell>


