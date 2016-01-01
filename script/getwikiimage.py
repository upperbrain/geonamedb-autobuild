#/usr/bin/env python
# _*_ coding: utf-8 _*_

#$python getwikiimage.py Peru

import sys
import re
import requests
import codecs
import json
import os
from datetime import datetime

URLPT = r'((?:File\:|Image\:)+[\'\"\s\w\d.,-]+\.(?:JPG|PNG|SVG|GIF))'
DESCR = r'Description\=([\s\w]+)'
URL = r'website[\s]+\=[\s]\[(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'

ROOT = [ 'wikivoyage', 'wikipedia' ]

def parse(wikiurl):
    locationName = wikiurl
    #locationName should not have any space in word
    if " " in locationName:
        print 'locationName has space'
        sys.exit()
    else:
        #htmlOut = codecs.open('out.html', 'w', 'utf-8')
        response = {} #Dictionary will be JSON Object
        requestAll(ROOT, locationName, response)
        #htmlOut.close()
    

def requestAll(ROOT, locationName, response):    
    try:
        rd = requests.get('http://en.wikivoyage.org/w/api.php?action=query&prop=extracts&exchars=1000&exsectionformat=plain&format=json&titles='+locationName)
        rwp = requests.get('http://en.wikipedia.org/w/api.php?action=query&prop=extracts&exchars=1000&exsectionformat=plain&format=json&titles='+locationName)
        ri = requests.get('http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&rvsection=0&titles='+locationName)
        
        #Get location description from wikivoyage
        if rd.status_code is 200:
            rdStrObj = rd.json()['query']['pages']
            for rdEle in rdStrObj:
                rdStr = rdStrObj[rdEle]
                
        #Get location description from wikipedia
        if rwp.status_code is 200:
            rwpStrObj = rwp.json()['query']['pages']
            for rwpEle in rwpStrObj:
                rwpStr = rwpStrObj[rwpEle]
        
        imgDic =[] #List will be JSON array
        for rootUrl in ROOT:
            r = requests.get('http://en.'+ rootUrl +'.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles='+locationName)
            #Get location images
            if r.status_code is 200:
                strObj = r.json()['query']['pages']
                for ele in strObj:
                    str = strObj[ele]
                    urlList = re.findall(URLPT, unicode(str), flags=re.IGNORECASE)
                    for imgurlst in urlList:
                        imgurl = imgurlst.replace(' ','_')
                        #http://en.wikipedia.org/w/api.php?action=query&titles=image:London%20Tower01.jpg&prop=imageinfo&iiprop=url|comment&format=json
                        ri = requests.get('http://en.wikipedia.org/w/api.php?action=query&titles='+imgurl+'&prop=imageinfo&iiprop=url|comment&format=json')
                        if ri.status_code is 200:
                            imgStrObj = ri.json()['query']['pages']
                            for elei in imgStrObj:
                                #some times, the imageinfo is missing from query
                                if len(imgStrObj[elei]) is 5:
                                    imgstr = imgStrObj[elei]['imageinfo']
                                    imgDownLoadUrl = imgstr[0]['url']
                                    imgDescriptionUrl = imgstr[0]['descriptionurl']
                                    #htmlOut.write('<img src="'+imgDownLoadUrl+'" width="200">')
                                    imgdesc = re.findall(DESCR, unicode(imgstr), flags=re.IGNORECASE)
                                    if imgdesc:
                                        #htmlOut.write('<p>' + imgdesc[0] + '</p>')
                                        imgdesc = imgdesc[0]
                                    else:
                                        cp = re.findall(r'([^:]+[\s\w]+)\.(?:JPG|PNG|SVG|GIF)', imgurlst, flags=re.IGNORECASE)
                                        #htmlOut.write('<p>' + imgurl + '</br>' + cp[0] + '</br>Just in case visit http://commons.wikimedia.org/wiki/' + imgurl + '</p>')
                                        imgdesc = cp[0]
                                    metaDict = {'imgDescriptionUrl':imgDescriptionUrl, 'imgName':imgurl, 'imgDownLoadUrl':imgDownLoadUrl, 'imgDescription':imgdesc}
                                    imgDic.append(metaDict)
        
        #if we cant find extract data from wikivoye
        if(rdStr.get('extract','NO_DATA') is 'NO_DATA'):
            rdStr['extract'] = ''
        #if we cant find extract data from wikipedia
        if(rwpStr.get('extract','NO_DATA') is 'NO_DATA'):
            rwpStr['extract'] = ''
        response = {'images':imgDic}
        print json.dumps(response, sort_keys=False)
        #with codecs.open(outPutFile, 'w', 'utf-8') as jsonFile:
            #jsonFile.write(json.dumps(response, jsonFile, sort_keys=False, indent=4, separators=(',', ': ')))
        
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise



if __name__ == '__main__':
    parse(sys.argv[1])