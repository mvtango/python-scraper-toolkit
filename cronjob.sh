!#/bin/bash

cd ~/projekte/eurowhoiswho/scraper

LOGDIR=logs

. ~/venv/bin/activate
python ./euscraper.py >$LOGDIR/`date +%Y%m%d%H%M%S`-euscraper.log 2>&1 


find $LOGDIR -mtime +30 -exec rm {} \; 

