# coding: utf-8

from lxml import etree
from lxml.cssselect import CSSSelector, SelectorSyntaxError
import types
import requests
import re
import logging
import os

logger=logging.getLogger(os.path.split(__file__)[1])


class AddToEditorChainClass :


	def __init__(self) :
		self._debug=False


	def __add__(self,o) :
        	def a(*args,**kwargs) :
            		return self(o(*args,**kwargs))
        	return a


	def makestring(self,a) :
		if isinstance(a, ([],())) :
			a="".join([unicode(b) for b in a])
		return a


	def debug(self,state=None) :
		if state is not None :
			self._debug=state
		return self._debug


class TextEditor(AddToEditorChainClass):
	"""
	Takes List of Search / Replace Expressions
	d=TextEditor([("a","b"),("c","d")])

	d.process("maca") -> "mbdb"
	"""

	def __init__(self, ruleset) :
		AddToEditorChainClass.__init__(self)
		self.ruleset=[(re.compile(a[0]),a[1]) for a in ruleset]


	def edit(self,i) :
		i=self.makestring(i)
		if self.debug() :
			logger.debug("Start: %s" % repr(i))
		for r in self.ruleset :
			i=r[0].sub(r[1],i)
			if self.debug() :
				logger.debug("%s->%s : %s" % (r[0].pattern,r[1],repr(i)))

		return i

	def __call__(self,i) :
		return self.edit(i)




class TextParser(AddToEditorChainClass) :
	"""
	Takes List of Regexp. Will return groupdict() of first match

	"""


	def __init__(self, *ruleset) :
		AddToEditorChainClass.__init__(self)
		self.ruleset=[re.compile(a) for a in ruleset]


	def parse(self,i) :
		i=self.makestring(i)
		for r in self.ruleset :
			m=r.search(i)
			if m :
				return m.groupdict()
		return None


	def __call__(self,i) :
		return self.parse(i)



class ScrapedElement(etree.ElementBase) :
	""" Custom etree.Element

	added methods: text(parse-parameter) -> gives toString,
	               parse-parameter optionally applies r'(?P<regular>.*)' expression with named matches or function

				   select(css-or-xpath) -> returns list of children that match css or xpath expression

				   extract(**kwargs) -> returns dict with keys of kwargs, values of self.select(value)

	"""

	def text(self,parse=None,**kwargs) :
		t=etree.tostring(self,**kwargs)
		if isinstance(parse, (str,bytes)) :
			parse=TextParser(parse)
		if isinstance(parse, types.FunctionType) :
			t=parse(t)
		return t.decode("utf-8")

	def select(self,p) :
		""" p is either a CSS selector
		    or an xpath expression

			pseudo-class ":content" will take "text only"
		"""
		try :
			attr=False
			if p.find(":text")>0 :
				p=p.replace(":text","")
				textonly=True
			else :
				textonly=False
				if p.find(":@") > 0 :
					ps=re.search(":@([^ ]+)",p)
					attr=ps.group(1)
					p=re.sub(":@[^ ]+","",p)
			sel=CSSSelector(p)
			if textonly :
				return "".join([a.text(method="text",with_tail=False,encoding="utf-8") for a in sel(self)])
			else :
				if attr :
					return "".join([a.get(attr,"") for a in  sel(self)])
				else :
					return sel(self)
		except SelectorSyntaxError :
			try :
				return self.xpath(p)
			except Exception as e :
				raise SyntaxError(p)
		except AssertionError :
			return self.xpath(p)


	def extract(self, **args) :
		r={}
		for (k,v) in args.items() :
			vv=self.select(v)
			if vv :
				if len(vv)==1 :
					r[k]=vv[0]
				else :
					r[k]=vv
		return  r

	def __repr__(self) :
		t=self.text()
		if t is None :
			t="-"
		return t


def myparser() :
	parser_lookup = etree.ElementDefaultClassLookup(element=ScrapedElement)
	parser = etree.HTMLParser()
	parser.set_element_class_lookup(parser_lookup)
	return parser


class TreeScraper :
	""" Class that parses URL into lxml tree and extracts CSS / Xpath
	"""

	def __init__(self, ss,**kwargs) :
		if isinstance(ss, (str,bytes)) :
			if isinstance(ss,bytes) :
				ss=ss.decode("utf-8")
			if len(ss)>0 and ss[0:4].find("<")>-1 :
				self.tree=etree.fromstring(ss,myparser())
			else :
				if kwargs or ss[:4]=="http":
					r=requests.get(ss,**kwargs)
					r.raise_for_status()
					self.tree=etree.fromstring(r.content,myparser())
				else :
					self.tree=etree.parse(ss,myparser())
		else :
			self.tree=etree.parse(ss,myparser())



	def select(self,p) :
		try :
			sel=CSSSelector(p)
			return sel(self.tree)
		except SelectorSyntaxError :
			return self.tree.xpath(p)
		except AssertionError :
			return self.tree.xpath(p)

	def extract(self,*args,**kwargs) :
		""" with select expression as first arg: returns array of match dicts, without: returns match dicts"""
		r=[]
		if len(args) == 1 :
			for e in self.select(args[0]) :
				if hasattr(e,"extract") :
					e=e.extract(**kwargs)
				r.append(e)
			return r
		else :
			if len(args)==0 :
				r=self.tree
				if hasattr(r,"getroot") :
					r=r.getroot()
				if hasattr(r,"extract") :
					return r.extract(**kwargs)
				else :
					return {}
			else :
				raise(TypeError,"extract() takes 0 or 1 arguments + keyword arguments, got %s" % len(args))








if __name__=="__main__" :

	chinese=TextEditor([("r","l"),("a","m")])
	assert chinese.edit("roaring")=="lomling"

	firstlast=TextParser(r"(?P<first>\d+)(?P<last>.+)",r"(?P<last>\D+)(?P<first>\d+)")
	assert firstlast.parse("3a")=={ "first":"3", "last" : "a"}
	assert firstlast("a3")=={ "first":"3", "last" : "a"}

	t=TreeScraper("<html><h1>Headline</h1><p>Hallo <b>Welt</b>, Du bist so <b>sch&ouml;n</b></p><p>Nat&uuml;rlich <b>nicht immer</b></html>")

	assert t.select("//h1/text()")==['Headline']
	print("e=", t.extract("p",text='b'))
	notags=TextEditor([["<[^>]+>",""]])

	print (notags(u"blöd"))
	#print t.extract("h1",notags)
	#print t.extract("h1",chinese)
	#print t.extract("h1",chinese+notags)
