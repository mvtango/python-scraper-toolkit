import scrapelib
import transformlib
import requests
import re

s=scrapelib.TreeScraper("http://www.wulfmansworld.com/Kino/Charts/Kino_Charts_der_Woche/")


liste=s.extract(".filmKCa",
                     pos='div.position:text',
                     pos_vorw=".vorwoche:text",
                     titel=".filmtitelbig:text",
                     titel2=".filmtitelhinweis:text",
                     titel3=".filmtitelsmall2:text",
                     darsteller=".darsteller:text",
                     regie=".regie:text",
                     produzent=".produzent:text",
                     genre=".genre:text",
                     kinotstart=".kinostart:text",
                     spielzeit=".spielzeit:text",
                     land=".land:text",
                     img='.poster img:@src',
                     besucher=".besucheraktuellewochekcw:text",
                     deltabesuchervorwoche=".vorwochepercchange:text",
                     besuchergesamt=".besuchergesbisjetzt:text",
                     fsk=".FSKkcw:text")


t=transformlib.Transformer()

from collections import defaultdict
dn=defaultdict(lambda : "")


t.append(re.compile(".*"),
         transformlib.reTransformer(r"[\r\n\t]+",""))
t.append(re.compile("^(besuch|pos).*"),
         transformlib.funcTransformer(lambda a: int(a.replace(".",""))))
t.append(re.compile("^delta.*"),
         transformlib.funcTransformer(lambda a: float(a.replace(",",".").replace("%",""))))
t.append("titel",
         lambda a,b,c : { a: "{titel} {titel2} {titel3}".format(**defaultdict(lambda : "",c))
                        })
t.append(re.compile("^titel[23]$"),
         lambda a,b,c : { a : transformlib.DeleteThis })
t.append("titel",
         transformlib.reTransformer(r"[\r\n\t]+",""))

from copy import deepcopy
eliste=deepcopy(liste)
for l in liste :
    t(l)

import pprint

for (i,a) in enumerate(eliste) :
    pprint.pprint([a,liste[i]])
