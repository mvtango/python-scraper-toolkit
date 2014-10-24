#! /bin/bash

DBC=/home/mvirtel/local/bin/sqlite3 


cat <<HERE  | $DBC data.db
select av.start,a.pid, a.name,ad.name,ad.nid,ad.depth, " -> ", bv.start,b.name,bd.name,bd.nid,bd.depth from pers as b, pers as a, dept as ad, dept as bd, versions as av, versions as bv  where a.pid=b.pid and not a.nid=b.nid and ad.nid=a.nid and bd.nid=b.nid and bv.oid=b.id and av.oid=a.id and av."table"="pers" and bv."table"="pers" order by bv.start desc;
HERE

