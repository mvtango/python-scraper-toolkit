from scrapelib import TreeScraper
from transformlib import Transformer
import re
import urlparse
import requests
import random   
import simplejson, pprint,string, datetime
from collections import OrderedDict
import types
import copy
import logging
logger=logging.getLogger(__name__)


# proxy  = { 'http':'127.0.0.1:8118' }
proxy={}
header = { "user-agent" : "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; chromeframe/12.0.742.112)" }
token = { 'sss@gmx.info' : "1fNpNSiw", 'spon' : "4BA1IOGz", "pool" : ['GukMuRA7', "4BA1IOGz", "1fNpNSiw" ], "sinfalta@mailinator.com" : 'GukMuRA7' } #cAISsODRE sinfalta@mailinator.com

# 

def eventdata_web(eid) :
    er={}
    if eid[0]>="0" and eid[0]<="9" :
        url="http://www.scribblelive.com/Event/Thread.aspx?Id=%s" % eid
        er["id"]=eid
    else :
        url=urlparse.urljoin("http://www.scribblelive.com/Event/",urlparse.urlsplit(eid)[2])
        er["id"]=None
    try :
        t=TreeScraper(url,proxies=proxy, headers=header)
    except Exception, e:
		er.update({"error" : repr(e) })
		return er
    e=t.extract(title="//h2/text()",
              description="//h3/text()",
              time="//span[contains(@class,'DisplayPostTime')][1]//text()[1]",
              who="//dl[contains(@id,'WhosBloggingSidebar')]//li//text()",
              meta="//head//script/text()",
              canonical="//head//link[contains(@rel,'canonical')]/@href"
              )
    if "meta" in e :
		for m in re.finditer(r"var (?P<name>[^ ]+) *= *\"?(?P<val>[^\r]+[^\"])\"?;",''.join(e["meta"])) :
			d=m.groupdict()
			if d["name"] in ("DiscussionsEnabled","PromotionalUrl","IsLive","Time","ThreadId") :
				e[d["name"]]=d["val"]
			else :
				# e["rest"]=e["rest"]+"\n%(name)s = %(val)s" % d
				pass
		del e["meta"]
    er.update(e)
    return er


def eventdata_api(eid) :
    a=requests.get("http://apiv1.scribblelive.com/event/%s/?Token=%s&callback=g" % (eid,token["sinfalta@mailinator.com"]),proxies=proxy,headers=header)
    if a.status_code==403 :
		return { "id" : eid, "error" : "API: 403 forbidden" }
    else :
		a.raise_for_status()
		try :
			return simplejson.loads(a.content[2:-1])
		except Exception, e :
			return { "id" : eid, "error" : "JSON: %s " % repr(e) }
    

def js_to_timestamp(a) :
	try :
		sinceepoch=int(re.search(r"(?P<time>\d+)",a).groupdict()["time"])/1000
		if sinceepoch==253402300799 :
			return None
		else :
			return datetime.datetime.fromtimestamp(sinceepoch)
	except Exception, e:
		logger.debug("%s -> %s timestamp conversion error: %s" % (a,sinceepoch,e))
		return None

    

 
translate = Transformer(((  'time'                                    , lambda a,b,c:  { a: None,  'stime' : datetime.datetime.strptime(b, "%m/%d/%Y %I:%M:%S %p") }),
                        (   'Time'                                    , lambda a,b,c:  { a: None,  'mtime' : datetime.datetime.strptime(b, "%m/%d/%Y %I:%M:%S %p") }),
                        (   'Title'                                   , lambda a,b,c:  { a: None,  'metatitle' : b }),
                        (   'ThreadId'                                , lambda a,b,c:  { a: None,  'id' : b }),
                        (  re.compile('^End|Created|Start|LastModified$')
                                                                      , lambda a,b,c:  { a: None, string.lower(a) : js_to_timestamp(b) }),
                        (   re.compile(".*")                          , lambda a,b,c:  { a: None, string.lower(a) : b}),
                        
                       ))

                 
def eventdata(eid,api=True,web=True) :
    if not web :
        m=eventdata_api(eid)
    else :
		m=eventdata_web(eid)
		if not ("error" in m and m["error"].find("404")>0) :
			tid=m.get("ThreadId","")
			if not tid :
				tid=m.get("id","")
			if api and re.search("^\d+$",tid) and not ("error" in m and m["error"].find("404")>0) :
				m.update(eventdata_api(tid))
				if not "who" in m or len(m["who"])==0 :
					try :
						rp=recentposts(tid).get("Posts",[])
					except Exception, e:
						rp=[]
					if len(rp)>0 :
						m["who"]=[ rp[0]["CreatorName"], ]
    if ('time' in m) and (type(m['time']) == type([])) :
        m['time']=m['time'][0]
    # logger.debug(pprint.pformat(m))
    m=translate(m)
    if "title" not in m and "metatitle" in m:
		m["title"]=m["metatitle"]
    return m
                
def recentposts(eid) :
    url=re.sub(r"([0-9])",r"/\1",eid)
    resp=requests.get("http://liveupdate1.scribblelive.com%s/recentposts.js?rand=%s" % (url,random.randint(1000000,9999999)))
    resp.raise_for_status()
    try :
		obj=simplejson.loads(resp.content[resp.content.find(",")+1:-1])
    except Exception, e:
		obj={ 'error' : repr(e), 'content' : resp.content }
    obj["id"]=eid
    return obj
    
    
               
               
def listevents() :
    t=TreeScraper("http://scribblelive.mobi",headers=header)
    return t.extract("ul#Threads li",url="./a/@href", title="./a/text()",description=".//span[contains(@class,'Description')]/text()",stamp=".//span[contains(@class,'DateTime')]/text()" )
    
# for l in listevents() :
#    l.update(eventdata(l["url"]))
#    print l :
if __name__=='__main__' :    
	print eventdata("202752")
	#print eventdata("173569",api=False),"\n\n",eventdata("120285"),"\n\n",eventdata("179163",api=False),"\n\n",eventdata("120285",web=False)
