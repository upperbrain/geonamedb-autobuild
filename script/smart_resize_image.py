#!/usr/bin/python
# -*- coding: utf-8 -*-

#This script resizes pic of imgFile to imgFileOut.
#python smart_resize_image.py '{"imgFile":"../data/GB/pictures/london/Black_London_Cab.jpg","imgFileOut":"../data/GB/pictures/london_resize/","width":"300","height":"300"}'

from __future__ import division
import sys
import os
import json
import time
import datetime
import Image

def resize(valDic):
	
	try:
		imgfile = valDic['imgFile'].replace("&#39;","'")
		imgfileout = valDic['imgFileOut'].replace("&#39;","'")
		maxwidth = int(valDic['width'])
		maxheight = int(valDic['height'])
		
		im = Image.open(imgfile)
		imwidth = im.size[0]
		imheight = im.size[1]
		imformat = im.format
		
		if maxheight is 0:
		    ratio = maxwidth/imwidth
		elif maxwidth is 0:
		    ratio = maxheight/imheight
		else:
		    ratio = min(maxwidth/imwidth, maxheight/imheight)
		
		out = im.resize((int(imwidth*ratio), int(imheight*ratio)), Image.ANTIALIAS)
		
		outpath = imgfileout+os.path.basename(imgfile)
		#print outpath
		
		out.save(outpath, imformat, quality=95)
		print "ok"
		
	except IOError:
		print 'error'
		

if __name__ == "__main__":
	start_time = time.time()
	jsonVal = sys.argv[1]
	valDic = json.loads(jsonVal)
	print valDic
	resize(valDic)
	#print("--- %s seconds ---" % str(datetime.timedelta(seconds=round(time.time() - start_time))))