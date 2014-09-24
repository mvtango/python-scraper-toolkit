import datetime


def changed(stored,maybenew) :
	for k in maybenew.keys() :
		if stored[k] != maybenew[k] :
			return True
	return False

def store_new_version(table,stored,object,versiontablename) :
	versiontable=table.database[versiontablename]
	stamp=datetime.datetime.now()
	if stored is not None :
		versiontable.update(dict(end=stamp,oid=stored["id"],table=table.table.name),["table","oid"])
	nid=table.insert(object)
	versiontable.insert(dict(end=None,start=stamp,oid=nid,table=table.table.name))
	return nid


def update_if_different(table,object,fields,versiontablename) :
	filterarg={}
	for f in fields :
		filterarg[f]=object[f]
	sql="select * from `{table}` where {filter} and id in (select oid from `{vtable}` where `table`='{table}' and end is null)".format(table=table.table.name,vtable=versiontablename, filter=" and ".join(["(`%s`='%s')" % (a[0],a[1]) for a in filterarg.items()]))
	try :
		stored=[a for a in table.database.query(sql)]
	except Exception, e:
		stored=False
	if stored :
		stored=stored[0]
		if not changed(stored,object) :
			return False # no new version
		else :
			return store_new_version(table,stored,object,versiontablename)
	else :
		return store_new_version(table,None,object,versiontablename)
		

	


if __name__=='__main__' :
	import dataset
	d=dataset.connect("sqlite:///:memory:")
	t=d["tble"]
	print "first=%s" % update_if_different(t,dict(a=1,t="eins"),["a"],"versions")
	print "same=%s" % update_if_different(t,dict(a=1,t="eins"),["a"],"versions")
	print "different=%s" % update_if_different(t,dict(a=1,t="mehralseins"),["a"],"versions")
	print "same=%s" % update_if_different(t,dict(a=1,t="mehralseins"),["a"],"versions")
	print "different=%s" % update_if_different(t,dict(a=1,t="eins"),["a"],"versions")
	print "\n".join([repr(a) for a in t.all()])
	print "\n".join([repr(a) for a in d["versions"].all()])

