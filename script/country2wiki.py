#/usr/bin/env python
# _*_ coding: utf-8 _*_

#This is a script that create geoinfomation_cms databased based on geonameId.
#$ python country2wiki.py

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
URL = r'website|homepage[\s]+\=[\s]\[(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
TITLE = r'/+([a-zA-Z0-9_,%2C-]+)$'
IMGR = r'photo[\s]+\=[\s]+([a-zA-Z0-9-_ ]+\.(?:JPG|PNG|SVG|GIF))'
ROOT = [ 'wikivoyage', 'wikipedia' ]
DEBUG = False

def parse(conn):
    #get list of geonameid, name, countryCode
    global cur
    cur = conn.cursor()
    
    #google place api is 1000 per day(non-premium)
    
    if DEBUG:
        sql = "SELECT geonameid, name, country_code FROM all_countries LIMIT 0, 1"
    else:
        #go through all countries
        #sql = "SELECT geonameid, name, country_code FROM all_countries LIMIT 0, 1000"
        
        #2000credit * 12hours = 24000credit(this will run for 12 hours)
        #sql = "SELECT geonameid, name, country_code FROM all_countries WHERE country_code='GB' LIMIT 2,1"
        
        #lets go all the GB - 51900 locations!
        #sql = "SELECT geonameid, name, country_code FROM all_countries WHERE country_code='GB'"
        #disconnected, so we start from 7297277
        #sql = "SELECT geonameid, name, country_code FROM all_countries WHERE country_code='GB' and geonameid >= '7297277' "
        
        #lets go all the FR - 137100 locations!
        #137100/30000(daily call limit) = 4.57, this will take about 5 days.
        #sql = "SELECT geonameid, name, country_code FROM all_countries WHERE country_code='FR' and geonameid > '6543975' " #disconnected, so we start from 6543975.
        
        #lets go all the DE!
        #sql = "SELECT geonameid, name, country_code FROM all_countries WHERE country_code='DE'"
        sql = "SELECT geonameid, name, country_code FROM all_countries WHERE country_code='US' AND admin1_code='CA' AND geonameid > '5398242' "
        
    data = cur.execute(sql)
    results = cur.fetchall()
    
    for row in results:
       geonameid = row[0]
       name = row[1].encode('utf-8')
       countryCode = row[2].encode('utf-8')
       if DEBUG:
           geonameid = "3038816"
           name = "Xixerella"
           countryCode = "AD"
       
       print "geonameid=%s,name=%s,countryCode=%s" % (geonameid, name, countryCode)
       requestGEO(geonameid, name, countryCode)
    cur.close()
    print("--- %s seconds ---" % str(datetime.timedelta(seconds=round(time.time() - start_time))))
    
    
def requestGEO(geonameid, name, countryCode):
    try:
        global cur
        
        ########################################################
        ##Fist, get wikipedia and wikivoyage infos and save to db
        ########################################################
        wikiUrl = 'http://api.geonames.org/wikipediaSearchJSON?maxRows=1&q='+name+'&country='+countryCode+'&username=chrisstaccato'
        rw = requests.get(wikiUrl)
        
        db_geonameId = geonameid
        db_wikicat = ""
        db_rank = 0 #rank is int, so it cant be empty str
        db_thumbnailImg = ""
        db_descriptionwikipedia = ""
        db_wikipediaLink = ""
        db_geonamewikisearchurl = wikiUrl.replace("'","%27").decode('utf-8')
        db_descriptionwikivoyage = ""
        db_website = ""
        
        #Get wikipedia info from Geonames
        if rw.status_code is 200:
            #lets check api limit at first
            #http://www.geonames.org/export/webservice-exception.html
            rObj = rw.json()
            if rObj.get('status','NO_ST') is not 'NO_ST':
                if unicode(rObj['status']['value']) == '18':
                    print('daily limit of credits exceeded')
                    #30'000 credits daily limit per application
                    os._exit(1)
                elif unicode(rObj['status']['value']) == '19':
                    print('hourly limit of credits exceeded')
                    #hourly limit is 2000 credits
                    #os._exit(1) instead kill process, lets sleep for an hour
                    time.sleep(1 * 3600)
                elif unicode(rObj['status']['value']) == '20':
                    print('weekly limit of credits exceeded')
                    os._exit(1)
                elif unicode(rObj['status']['value']) == '10':
                    wikiObj = None
                    wikititle = name
            
            if rw.json().get('geonames', 'NO_GEONAME') is not 'NO_GEONAME':
                if not rw.json()['geonames']:
                    #print "NO wiki data from Geonames"
                    wikiObj = None
                    wikititle = name
                else:
                    wikiObj = rw.json()['geonames'][0]
                    if not wikiObj:
                        print "No wikidata avaliable"
                    else:
                        if wikiObj.get('feature','NO_FEATURECODE') is not 'NO_FEATURECODE':
                            #print str(wikiObj.get('feature','NO_FEATURECODE'))
                            db_wikicat = str(wikiObj.get('feature','NO_FEATURECODE'))
                        else:
                            db_wikicat = ''
                            #print "No wiki category found"
                        
                        if wikiObj.get('rank','NO_RANK') is not 'NO_RANK':
                            #print str(wikiObj.get('rank','NO_RANK'))
                            db_rank = str(wikiObj.get('rank','NO_RANK'))
                            #print(db_rank)
                        else:
                            db_rank = 0
                            #print "No wiki category found"
                        
                        if wikiObj.get('thumbnailImg','NO_WIKI_IMAGE') is not 'NO_WIKI_IMAGE':
                            #print str(wikiObj.get('thumbnailImg','NO_WIKI_IMAGE'))
                            db_thumbnailImg = str(wikiObj.get('thumbnailImg','NO_WIKI_IMAGE'))
                            #print(db_thumbnailImg)
                        else:
                            db_thumbnailImg = ''
                            #print "No wiki thumbnail image found"
                        
                        if wikiObj.get('summary','NO_SUM') is not 'NO_SUM':
                            #print unicode(wikiObj.get('summary','NO_SUM'))
                            db_descriptionwikipedia = conn.escape_string(unicode(wikiObj.get('summary','NO_SUM')))
                            #print(db_descriptionwikipedia)
                        else:
                            db_descriptionwikipedia = ''
                            #print "NO wiki summary found"
                        
                        if wikiObj.get('wikipediaUrl','NO_WIKI_LINK') is not 'NO_WIKI_LINK':
                            #print str(wikiObj.get('wikipediaUrl','NO_WIKI_LINK'))
                            db_wikipediaLink = str(wikiObj.get('wikipediaUrl','NO_WIKI_LINK'))
                            #print(db_wikipediaLink)
                            wikititle = os.path.basename(db_wikipediaLink)
                            #print(wikititle)
                        else:
                            db_wikipediaLink = ''
                            #print "No wiki link found"
                
        #Get location description from wikivoyage
        rd = requests.get('http://en.wikivoyage.org/w/api.php?action=query&prop=extracts&exchars=1000&exsectionformat=plain&format=json&titles='+wikititle)
        if rd.status_code is 200:
            rdStrObj = rd.json()['query']['pages']
            for rdEle in rdStrObj:
                rdStr = rdStrObj[rdEle]
                if rdStr.get('extract','NO_SUM') is not 'NO_SUM':
                    db_descriptionwikivoyage = conn.escape_string(rdStr['extract'].encode('utf-8'))
                else:
                    db_descriptionwikivoyage = ''
                    print "No wikivoyage data found"
        
        ri = requests.get('http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&rvsection=0&titles='+wikititle)
        #Get location homepage url if there is any
        if ri.status_code is 200:
            riStrObj = ri.json()['query']['pages']
            if(riStrObj.get('-1','NO_DATA') is 'NO_DATA'):
                for riEle in riStrObj:
                    if unicode(riEle) is '-1':
                        db_website = ""
                        #print 'No website address found'
                    else:
                        cu = re.findall(URL, unicode(riStrObj[riEle]['revisions'][0]['*']), flags=re.IGNORECASE)
                        if cu:
                            db_website = cu[0]
                        else:
                            db_website = ""
                            #print 'No website address found'
            else:
                #print "CANT FIND ANY INFO"
                db_website = ""
        
        #if there is already record, then just update it.
        sqlSelect = """SELECT geonameId FROM geoinformation_cms.wikiinfo WHERE geonameId='%s' """ % db_geonameId
        cur.execute(sqlSelect)
        
        if cur.execute(sqlSelect) is not 0:
            #print "just update"
            sqlUpdate = """UPDATE geoinformation_cms.wikiinfo
                            SET geonameId='%s',geonamewikisearchurl='%s', wikipediaLink='%s', wikicat='%s', rank='%s', descriptionwikivoyage='%s', descriptionwikipedia='%s', thumbnailImg='%s', website='%s'
                            WHERE geonameId='%s'
                            """ % (db_geonameId, db_geonamewikisearchurl, db_wikipediaLink, db_wikicat, db_rank, db_descriptionwikivoyage.decode('utf8'), db_descriptionwikipedia, db_thumbnailImg, db_website ,db_geonameId)
            #Execute the SQL command
            cur.execute(sqlUpdate)
        else:
            #print "insert as new"
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            sqlInsert = """INSERT INTO geoinformation_cms.wikiinfo
                        (geonameId, geonamewikisearchurl, wikipediaLink, wikicat, rank, descriptionwikivoyage, descriptionwikipedia, thumbnailImg, website, creation_date) VALUES 
                        ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')""" % \
                        (db_geonameId, db_geonamewikisearchurl, db_wikipediaLink, db_wikicat, db_rank, db_descriptionwikivoyage.decode('utf8'), db_descriptionwikipedia, db_thumbnailImg, db_website, now)
            #Execute the SQL command
            cur.execute(sqlInsert)
            
        
        ########################################################
        #Second, get image info from wikipedia and wikivoyage
        ########################################################
        db_imgDownLoadUrl = ""
        db_imgurl = ""
        db_imgdesc = ""
        db_imgname = ""
        
        for rootUrl in ROOT:
            r = requests.get('http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles='+wikititle)
            #Get location images
            if r.status_code is 200:
                strObj = r.json()['query']['pages']
                for ele in strObj:
                    urlList = re.findall(URLPT, unicode(strObj[ele]), flags=re.IGNORECASE)
                    
                    if re.findall(IMGR, unicode(strObj[ele]), flags=re.IGNORECASE):
                        infoboxImgTmp = re.findall(IMGR, unicode(strObj[ele]), flags=re.IGNORECASE)
                        infoboxImg = 'File:%s' % infoboxImgTmp[0]
                        urlList.append(infoboxImg) #to add str, use append instead of extend
                        
                    for imgurlst in urlList:
                        imgurl = imgurlst.replace(' ','_').replace('..','.').replace("'","%27")
                        db_imgurl = imgurl
                        #http://en.wikipedia.org/w/api.php?action=query&titles=image:London%20Tower01.jpg&prop=imageinfo&iiprop=url|comment&format=json
                        ri = requests.get('http://en.wikipedia.org/w/api.php?action=query&titles='+imgurl+'&prop=imageinfo&iiprop=url|comment&format=json')
                        if ri.status_code is 200:
                            imgStrObj = ri.json()['query']['pages']
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
                                        cp = re.findall(r'([^:]+[\'\"\s\w\d.,-]+)\.(?:JPG|PNG|SVG|GIF)', imgurlst, flags=re.IGNORECASE)
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
        
    except:
        print "Unexpected error:", sys.exc_info()[0]
        

    
def get_mysql_connection():
    #fill host, user, passwd and db with your access info.
    conn = pymysql.connect(host="HOSTNAME", user="USERNAME", passwd="PASSWORD", db="DBNAME", use_unicode=True, charset='utf8')
    return conn



if __name__ == '__main__':
    conn = get_mysql_connection()
    parse(conn)
    conn.close()