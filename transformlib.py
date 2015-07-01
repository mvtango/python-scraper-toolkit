from collections import OrderedDict
import copy,types,string,re,datetime
import logging
logger=logging.getLogger(__file__)

"""
A transformerFunc is a function that gets (key,value,dict) and returns
a dict that can be used to update the dict These functions can be bundled in
a transformer object.

Example:

	make all keys lower case

	b=Transformer()
	b.append(re.compile('.*'), lambda a,b,c: { a: DeleteThis, string.lower(a) : b})

	b({ 'Hallo' : 0 }) -> { 'hallo' : 0 }


"""

class DeleteThis :
	pass


def funcTransformer(f) :
	return lambda k,v,o : { k: f(v) }

def reTransformer(s,r) :
	return funcTransformer(lambda a : re.sub(s,r,a) )

def strptimeTransformer(f) :
	return funcTransformer(lambda a: datetime.datetime.strptime(a,f) )


def groups_or_none(s,v) :
	m=re.search(s,v)
	if not m :
		return {}
	else :
		return m.groupdict()

def resplitTransformer(f) :
	return funcTransformer(lambda a: groups_or_none(f,a))


class Transformer :

	def __init__(self,*args) :
		self.instructions=OrderedDict()
		if len(args)==1 :
			for pair in args[0] :
				self.append(pair[0],pair[1])



	def append(self,keys=None,func=None) :
		self.instructions[keys]=func


	def transform(self,o) :
		for (k,v) in o.items() :
			for (kt,tt) in self.instructions.items() :
				if isinstance(kt, (str,bytes)) :
					if k==kt :
						try :
							o.update(tt(k,v,o))
						except Exception as e:
							logger.exception("Exception transforming '%s'" % kt)

				elif hasattr(kt,"search") :
					if kt.match(k) :
						try :
							o.update(tt(k,v,o))
						except Exception as e:
							logger.exception("Exception transforming '%s'" % kt)

		td=[]
		for (k,v) in o.items() :
			if o[k] is DeleteThis :
				td.append(k)
		for f in td :
			del o[f]
		return o


	def __call__(self,o) :
		return self.transform(o)


if __name__=='__main__' :
	import re,datetime
	def js_to_timestamp(a) :
		return datetime.datetime.fromtimestamp(int(re.search(r"(?P<time>\d+)",a).groupdict()["time"])/1000)
	test_object={'End': '/Date(1370963382000+0000)/', 'dd' : '4/4/2010 4:20:20 am', 'Language': 'de', 'Title': u'Fussball L\xe4nderspiel der Frauen', 'IsCommenting': 1, 'LastModified': '/Date(1370963403180+0000)/', 'Discussion': {'Moderated': 0, 'Enabled': 0}, 'IsSyndicatable': 0, 'Websites': [{'Url': 'http://www.scribblelive.com/Event/Fussball_Landerspiel_der_Frauen', 'Id': 1, 'Name': 'ScribbleLive'}], 'Start': '/Date(1370962800000+0000)/', 'NumPosts': 5, 'IsLive': 0, 'NumComments': 3, 'IsSyndicated': 0, 'id': '120285', 'IsModerated': 1, 'Description': 'Deutschland gegen Schottland', 'title': 'Sorry, that live event was not found', 'Created': '/Date(1370873423000+0000)/', 'Id': 120285, 'Meta': {}, 'SyndicatedComments': 0, 'Pages': 1, 'IsDeleted': 1}
	t=Transformer(((  'time'                                    , lambda a,b,c:  { a: DeleteThis,  'stime' : datetime.datetime.strptime(b, "%m/%d/%Y %I:%M:%S %p") }),
                        (   'Time'                                    , lambda a,b,c:  { a: DeleteThis,  'mtime' : datetime.datetime.strptime(b, "%m/%d/%Y %I:%M:%S %p") }),
                        (   'Title'                                   , lambda a,b,c:  { a: DeleteThis,  'metatitle' : b }),
                        (   'ThreadId'                                , lambda a,b,c:  { a: DeleteThis,  'id' : b }),
                        (  re.compile('^End|Created|Start|LastModified$')
                                                                      , lambda a,b,c:  { a: DeleteThis, string.lower(a) : js_to_timestamp(b) }),
                        (   re.compile(".*")                          , lambda a,b,c:  { a: DeleteThis, string.lower(a) : b}),

                       ))
	print(t.transform(test_object))
	t1=Transformer()
	t1.append('Title', reTransformer("a","b"))
	t1.append('dd', strptimeTransformer("%m/%d/%Y %I:%M:%S %p"))
	t1.append(re.compile('^Start|End$'), resplitTransformer("(?P<dt>\d+)"))

	print(t1(test_object))
