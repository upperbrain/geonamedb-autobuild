#/usr/bin/env python
# _*_ coding: utf-8 _*_

#This is a script that create geoinfomation_cms databased based on geonameId.
#$ python wikiinfoupdate.py '{"geonameId":"6694389","newWikiUrl":"http://en.wikipedia.org/wiki/Alton_Towers_Resort"}'
#$ python wikiinfoupdate.py '{"geonameId":"6615354","newWikiUrl":"http://en.wikipedia.org/wiki/Legoland_Windsor_Resort"}'

import sys
import re
import codecs
import requests
import json
import datetime
import os
import time
import pymysql

start_time = time.time()
URLPT = r'((?:File\:|Image\:)+[\'\"\s\w\d.,-]+\.(?:JPG|PNG|SVG|GIF))'
DESCR = r'Description\=([\s\w]+)'
URL = r'website[\s]+\=[\s]\[(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
TITLE = r'/+([a-zA-Z0-9_,%2C-]+)$'
IMGR = r'photo[\s]+\=[\s]+([a-zA-Z0-9-_ ]+\.(?:JPG|PNG|SVG|GIF))'
ROOT = [ 'wikivoyage', 'wikipedia' ]
DEBUG = False

def parse(conn,valDic):
    #get list of geonameid, name, countryCode
    global cur
    cur = conn.cursor()
    
    geonameid = valDic['geonameId']
    newWikiUrl = valDic['newWikiUrl']
    newWikiTitle = os.path.basename(valDic['newWikiUrl']).replace("_"," ") #this will be like Alton_Towers_Resort
        
    sql = """SELECT a.*, w.* \
             FROM geonames_cms.all_countries a \
             LEFT JOIN geoinformation_cms.wikiinfo w ON w.geonameId=a.geonameId \
             WHERE a.geonameId='%s'""" % geonameid
    
    
    data = cur.execute(sql)
    results = cur.fetchall()
        
    for row in results:
        name = row[1].encode('utf-8')
        countryCode = row[9].encode('utf-8')
        requestGEO(geonameid, name, countryCode, newWikiUrl, newWikiTitle, row)
    cur.close()
    


def requestGEO(geonameid, name, countryCode, newWikiUrl, newWikiTitle, row):
    try:
        global cur
        
        ########################################################
        ##Fist, get wikipedia and wikivoyage infos and save to db
        ########################################################
        db_geonameId = geonameid
        db_wikicat = ''
        db_rank = 0
        db_thumbnailImg = ''
        db_descriptionwikipedia = ''
        db_wikipediaLink = newWikiUrl
        db_geonamewikisearchurl = ''
        db_descriptionwikivoyage = ''
        db_website = ''
        
        #Get location description from wikivoyage
        rd = requests.get('http://en.wikivoyage.org/w/api.php?action=query&prop=extracts&exchars=1000&exsectionformat=plain&format=json&titles='+newWikiTitle)
        if rd.status_code is 200:
            rdStrObj = rd.json()['query']['pages']
            for rdEle in rdStrObj:
                rdStr = rdStrObj[rdEle]
                if rdStr.get('extract','NO_SUM') is not 'NO_SUM':
                    db_descriptionwikivoyage = rdStr['extract'].encode('utf8')
        
        #Get location description from wikivoyage
        rp = requests.get('http://en.wikipedia.org/w/api.php?action=query&prop=extracts&exchars=1000&exsectionformat=plain&format=json&titles='+newWikiTitle)
        if rp.status_code is 200:
            rpStrObj = rp.json()['query']['pages']
            for rpEle in rpStrObj:
                rpStr = rpStrObj[rpEle]
                if rpStr.get('extract','NO_SUM') is not 'NO_SUM':
                    db_descriptionwikipedia = conn.escape_string(unicode(rpStr['extract']))
                    
        ri = requests.get('http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&rvsection=0&titles='+newWikiTitle)
        #Get location homepage url if there is any
        if ri.status_code is 200:
            riStrObj = ri.json()['query']['pages']
            if(riStrObj.get('-1','NO_DATA') is 'NO_DATA'):
                for riEle in riStrObj:
                    if unicode(riEle) is not '-1':
                        cu = re.findall(URL, unicode(riStrObj[riEle]['revisions'][0]['*']), flags=re.IGNORECASE)
                        if cu:
                            db_website = cu[0]
        
        #if there is already record, then just update it.
        sqlSelect = """SELECT geonameId FROM geoinformation_cms.wikiinfo WHERE geonameId=%s""" % db_geonameId
        cur.execute(sqlSelect)
        
        if cur.execute(sqlSelect) is not 0:
            #print "just update"
            sqlUpdate = """UPDATE geoinformation_cms.wikiinfo
                            SET geonameId='%s', geonamewikisearchurl='%s', wikipediaLink='%s', wikicat='%s', rank='%s', descriptionwikivoyage='%s', descriptionwikipedia='%s', thumbnailImg='%s', website='%s'
                            WHERE geonameId='%s'
                            """ % (db_geonameId, db_geonamewikisearchurl, db_wikipediaLink, db_wikicat, db_rank, db_descriptionwikivoyage.decode('utf8'), db_descriptionwikipedia, db_thumbnailImg, db_website ,db_geonameId)
            cur.execute(sqlUpdate)
        else:
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            sqlInsert = """INSERT INTO geoinformation_cms.wikiinfo
                        (geonameId, geonamewikisearchurl, wikipediaLink, wikicat, rank, descriptionwikivoyage, descriptionwikipedia, thumbnailImg, website, creation_date) VALUES 
                        ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')""" % \
                        (db_geonameId, db_geonamewikisearchurl, db_wikipediaLink, db_wikicat, db_rank, db_descriptionwikivoyage.decode('utf8'), db_descriptionwikipedia.decode('utf8'), db_thumbnailImg, db_website, now)
            cur.execute(sqlInsert)
            
        
        ########################################################
        #Second, get image info from wikipedia and wikivoyage
        ########################################################
        db_imgDownLoadUrl = ""
        db_imgurl = ""
        db_imgdesc = ""
        db_imgname = ""
        
        for rootUrl in ROOT:
            r = requests.get('http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles='+newWikiTitle)
            #Get location images
            if r.status_code is 200:
                strObj = r.json()['query']['pages']
                for ele in strObj:
                    urlList = re.findall(URLPT, unicode(strObj[ele]), flags=re.IGNORECASE)
                    
                    if re.findall(IMGR, unicode(strObj[ele]), flags=re.IGNORECASE):
                        infoboxImgTmp = re.findall(IMGR, unicode(strObj[ele]), flags=re.IGNORECASE)
                        infoboxImg = 'File:%s' % infoboxImgTmp[0]
                        urlList.append(infoboxImg) #to add str, use append instead of extend
                        
                        #From this point, we need to drop previous images
                        sqlDrop = """DELETE FROM geoinformation_cms.pictures WHERE geonameId='%s' """ % db_geonameId
                        cur.execute(sqlDrop)
                        
                    for imgurlst in urlList:
                        imgurl = imgurlst.replace(' ','_').replace('..','.').replace("'","%27")
                        db_imgurl = imgurl
                        ri = requests.get('http://en.wikipedia.org/w/api.php?action=query&titles='+imgurl+'&prop=imageinfo&iiprop=url|comment&format=json')
                        if ri.status_code is 200:
                            imgStrObj = ri.json()['query']['pages']
                            
                            #then lets startd saving images in db
                            for elei in imgStrObj:
                                #some times, the imageinfo is missing from query
                                if len(imgStrObj[elei]) is 5:
                                    imgstr = imgStrObj[elei]['imageinfo']
                                    db_imgDownLoadUrl = imgstr[0]['url']
                                    db_imgname = os.path.basename(db_imgDownLoadUrl)
                                    imgDescriptionUrl = imgstr[0]['descriptionurl']
                                    imgdesc = re.findall(DESCR, unicode(imgstr), flags=re.IGNORECASE)
                                    if imgdesc:
                                        db_imgdesc = imgdesc[0]
                                    else:
                                        cp = re.findall(r'([^:]+[\s\w]+)\.(?:JPG|PNG|SVG|GIF)', imgurlst, flags=re.IGNORECASE)
                                        db_imgdesc = cp[0].replace("'","%27")
                                    
                                    #if there is already image, then just update
                                    sqlImgSelect = """SELECT geonameId, picname FROM geoinformation_cms.pictures WHERE geonameId='%s' and picname='%s'""" % (db_geonameId,db_imgname)
                                    cur.execute(sqlImgSelect)
                                    
                                    if cur.execute(sqlImgSelect) is not 0:
                                        #just update
                                        sqlImgUpdate = """UPDATE geoinformation_cms.pictures 
                                                            SET geonameId='%s', picurl='%s', picname='%s', picdescription='%s' 
                                                            WHERE geonameId='%s' and picname='%s' and downloadpath is NULL""" % (db_geonameId, db_imgDownLoadUrl, db_imgname, db_imgdesc, db_geonameId, db_imgname)
                                        cur.execute(sqlImgUpdate)
                                    else:
                                        #insert as new
                                        sqlInsertImage = """INSERT INTO geoinformation_cms.pictures 
                                                    (geonameId, picurl, picname, picdescription) VALUES 
                                                    ('%s', '%s', '%s', '%s')""" % (db_geonameId, db_imgDownLoadUrl, db_imgname, db_imgdesc)
                                        cur.execute(sqlInsertImage)
                    
        # Commit your changes in the database
        conn.commit()
        
        print "ok" #lets print out ok, so php and ajax can notice its' success
        
    except:
        print "Unexpected error:", sys.exc_info()[0]
        
    
    
def get_mysql_connection():
    #fill host, user, passwd and db with your access info.
    conn = pymysql.connect(host="HOSTNAME", user="USERNAME", passwd="PASSWORD", db="DBNAME", use_unicode=True, charset='utf8')
    return conn


if __name__ == '__main__':
    #get the varaiables from php
    jsonVal = sys.argv[1]
    #jsonVal = {"geonameId":"4444","wikiTitleName":"wikiTitleNamefoo"}
    valDic = json.loads(jsonVal)
    conn = get_mysql_connection()
    parse(conn,valDic)
    conn.close()
