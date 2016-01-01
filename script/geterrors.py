#!/usr/bin/python
#This script gets list of geonameId that had been failed any automation(mainly country2wiki.py).
#By getting list of geonameId, we need to pass the ids to geonameId2wiki.py and re-build database.
#Python geterrors.py logfile.log

import sys
import re
import codecs
import os
import time
import datetime

GEONAME = r"geonameid=([0-9]+)"
ERROR = r"Error"

def ocrParser(ocrTXT):
	
	global goeIdList
	
	ocrfile = codecs.open(ocrTXT, 'r', 'utf-8')
	lines = [line.rstrip('\n') for line in ocrfile]
	try:
		tempTXT = None
		t1 = ''
		t2 = ''
		t3 = ''
		for lin in lines:
			tempTXT = unicode(lin)
			if re.findall(GEONAME, unicode(tempTXT), flags=re.IGNORECASE):
				#print"got geonamid line"
				t1 = tempTXT
			elif re.findall(ERROR, unicode(tempTXT), flags=re.IGNORECASE):
				#print"got error line"
				t2 = tempTXT
				t3 = t1+t2
				if re.findall(GEONAME, unicode(t3), flags=re.IGNORECASE) and re.findall(ERROR, unicode(t3), flags=re.IGNORECASE):
					#print (t3)
					#print (re.findall(GEONAME, unicode(t3), flags=re.IGNORECASE)[0])
					goeIdList.append(re.findall(GEONAME, unicode(t3), flags=re.IGNORECASE)[0])
	except:
		print 'error'
		print "tempTXT=> " + tempTXT
		ocrfile.close()

	ocrfile.close()

if __name__ == "__main__":
	start_time = time.time()
	goeIdList = []
	ocrParser(sys.argv[1])
	print goeIdList
	
	#Here, we need to call the geonameId2wiki.py and pass the geoIdList.
	
	print("--- %s seconds ---" % str(datetime.timedelta(seconds=round(time.time() - start_time))))