#/usr/bin/env python
# _*_ coding: utf-8 _*_

#This script creates geoinfomation_cms databased based on geonameId.
#$python addattraction.py '{"countrycode":"GB","newWikiUrl":"http://en.wikipedia.org/wiki/Adventure_Island_(amusement_park)","locationName":"Adventure Island"}'
#$python addattraction.py '{"countrycode":"GB","newWikiUrl":"http://en.wikipedia.org/wiki/Adventure_Wonderland","locationName":"Adventure Wonderland"}'
#$python addattraction.py '{"newWikiUrl":"http://en.wikipedia.org/wiki/Chessington World of Adventures Resort","countrycode":"GB","locationName":"Chessington World of Adventures"}'

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

def parse(conn,valDic):
    #get list of geonameid, name, countryCode
    global cur
    cur = conn.cursor()
    requestGEO(valDic)
    #print("--- %s seconds ---" % str(datetime.timedelta(seconds=round(time.time() - start_time))))
    
def requestGEO(valDic):
    try:
        global cur
        
        ########################################################
        ##Fist, get wikipedia and wikivoyage infos and save to db
        ########################################################
        
        newWikiTitle = os.path.basename(valDic['newWikiUrl']).replace("_"," ").replace("&#39;","'")
        #this goes to st_countries table
        name = valDic['locationName'].replace("&#39;","'")
        countryCode = valDic['countrycode']
        db_alternatename = valDic['locationName'].replace("&#39;","'")
        db_asciiname = ''
        db_latitude = ''
        db_longitude = ''
        db_featureclass = ''
        db_featurecode = '' 
        db_cc2 = ''
        db_admin1code = ''
        db_admin2code = ''
        db_admin3code = ''
        db_admin4code = ''
        db_population = ''
        db_elevation = ''
        db_dem = ''
        db_timezone = ''
        
        #this goes to st_wikiinfo table
        db_attractionid = ''
        db_wikipediaLink = valDic['newWikiUrl'].replace("_"," ").replace("&#39;","'")
        db_wikicat = ''
        db_descriptionwikivoyage = '' #this goes to st_wikiinfo table
        db_descriptionwikipedia = '' #this goes to st_wikiinfo table
        db_website = ''
        #For the rank, we seem need to have own calculation logic, since this seems not supported from wiki.
        #This is how geonames do it (http://www.geonames.org/export/wikipedia-webservice.html)
        db_rank = 0 #this goes to st_wikiinfo table
        
        #Get long,lat,type,country, region and dim from coordinate api
        rCoordinate = requests.get("http://en.wikipedia.org/w/api.php?action=query&prop=coordinates&coprop=type|name|dim|country|region&format=json&titles="+newWikiTitle)
        if rCoordinate.status_code is 200:
            rCStrObj = rCoordinate.json()['query']['pages']
            for rCEle in rCStrObj:
                rCStr = rCStrObj[rCEle]
                if rCStr.get('coordinates','NO_DATA') is not 'NO_DATA':
                    if rCStr['coordinates'][0].get('lat','NO_DATA') is not 'NO_DATA':
                        db_latitude = rCStr['coordinates'][0]['lat']
                        db_longitude = rCStr['coordinates'][0]['lon']
                    if rCStr['coordinates'][0].get('type','NO_DATA') is not 'NO_DATA':
                        db_wikicat = rCStr['coordinates'][0]['type']
                        
        #Get location description from wikivoyage
        rd = requests.get("http://en.wikivoyage.org/w/api.php?action=query&prop=extracts&exchars=1000&exsectionformat=plain&format=json&titles="+newWikiTitle)
        if rd.status_code is 200:
            rdStrObj = rd.json()['query']['pages']
            for rdEle in rdStrObj:
                rdStr = rdStrObj[rdEle]
                if rdStr.get('extract','NO_SUM') is not 'NO_SUM':
                    db_descriptionwikivoyage = conn.escape_string(rdStr['extract'].encode('utf8'))
                    
        #Get location description from wikipedia
        rp = requests.get("http://en.wikipedia.org/w/api.php?action=query&prop=extracts&exchars=1000&exsectionformat=plain&format=json&titles="+newWikiTitle)
        if rp.status_code is 200:
            rpStrObj = rp.json()['query']['pages']
            for rpEle in rpStrObj:
                rpStr = rpStrObj[rpEle]
                if rpStr.get('extract','NO_SUM') is not 'NO_SUM':
                    db_descriptionwikipedia = conn.escape_string(rpStr['extract'].encode('utf8'))
                    
        #Get location homepage url if there is any            
        ri = requests.get("http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&rvsection=0&titles="+newWikiTitle)
        if ri.status_code is 200:
            riStrObj = ri.json()['query']['pages']
            if(riStrObj.get('-1','NO_DATA') is 'NO_DATA'):
                for riEle in riStrObj:
                    if unicode(riEle) is not '-1':
                        cu = re.findall(URL, unicode(riStrObj[riEle]['revisions'][0]['*']), flags=re.IGNORECASE)
                        if cu:
                            db_website = cu[0]
                            
        #print "if there is already record, then just update it."
        sqlSelect = """SELECT * FROM geoinformation_cms.st_countries WHERE name="%s" and country_code="%s" """ % (name,countryCode)
        
        if cur.execute(sqlSelect) is not 0:
            sqlCountriesUpdate = """UPDATE geoinformation_cms.st_countries
                        SET name="%s", alternatename="%s", latitude="%s", longitude="%s"
                        WHERE name="%s" and country_code="%s" """ % \
                        (name, db_alternatename, db_latitude, db_longitude, name, countryCode)
            cur.execute(sqlCountriesUpdate)
            
            sqlSelectAfterUpdate = """SELECT * FROM geoinformation_cms.st_countries WHERE name="%s" and country_code='%s' """ % (name,countryCode)
            cur.execute(sqlSelectAfterUpdate)
            for row in cur.fetchall():
                db_attractionid = row[0]
                create_wiki_record(db_wikipediaLink, db_descriptionwikivoyage, db_descriptionwikipedia, db_wikicat, db_website, db_attractionid)
                create_img_record(newWikiTitle, db_attractionid)
        else:
            #print "insert as new"
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            sqlCountriesInsert = """INSERT INTO geoinformation_cms.st_countries
                        (name, asciiname, alternatename, latitude, longitude, feature_class, feature_code, country_code,\
                        cc2, admin1_code, admin2_code, admin3_code, admin4_code, population, elevation, dem, timezone, modification_date) VALUES 
                        ("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")""" % \
                        (name, db_asciiname, db_alternatename, db_latitude, db_longitude, db_featureclass, db_featurecode, countryCode,\
                        db_cc2, db_admin1code, db_admin2code, db_admin3code, db_admin4code, db_population, db_elevation, db_dem, db_timezone, now)
            cur.execute(sqlCountriesInsert)
            
            sqlSelectAfterInsert = """SELECT * FROM geoinformation_cms.st_countries WHERE name="%s" and country_code='%s' """ % (name,countryCode)
            cur.execute(sqlSelectAfterInsert)
            for row in cur.fetchall():
                db_attractionid = row[0]
                create_wiki_record(db_wikipediaLink, db_descriptionwikivoyage, db_descriptionwikipedia, db_wikicat, db_website, db_attractionid)
                create_img_record(newWikiTitle, db_attractionid)
        
        
        # Commit your changes in the database
        conn.commit()
        
        print "ok" #lets print out ok, so php and ajax can notice its' success
    
    except:
        print "Unexpected error:", sys.exc_info()[0]



def create_wiki_record(db_wikipediaLink, db_descriptionwikivoyage, db_descriptionwikipedia, db_wikicat, db_website, db_attractionid):    
    sqlWikiinfoSelect = """SELECT * FROM geoinformation_cms.st_wikiinfo WHERE attractionId='%s' """ % db_attractionid
    if cur.execute(sqlWikiinfoSelect) is not 0:
        sqlWikiinfoUpdate = """UPDATE geoinformation_cms.st_wikiinfo
                            SET wikipediaLink="%s",descriptionwikivoyage='%s',descriptionwikipedia='%s', wikicat='%s', website='%s'
                            WHERE attractionId='%s' """ % \
                            (db_wikipediaLink, db_descriptionwikivoyage, db_descriptionwikipedia, db_wikicat, db_website, db_attractionid)
        cur.execute(sqlWikiinfoUpdate)
    else:
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        sqlWikiinfoInsert = """INSERT INTO geoinformation_cms.st_wikiinfo
                                (attractionid, wikipediaLink, wikicat, descriptionwikivoyage, descriptionwikipedia, website, creation_date) VALUES 
                                ("%s", "%s", "%s", "%s", "%s", "%s", "%s")""" % \
                                (db_attractionid, db_wikipediaLink, db_wikicat, db_descriptionwikivoyage.decode('utf8'), db_descriptionwikipedia.decode('utf8'), db_website, now)
        cur.execute(sqlWikiinfoInsert)


def create_img_record(newWikiTitle, attractionId):
    
    ########################################################
    #Second, get image info from wikipedia and wikivoyage
    ########################################################
    db_imgDownLoadUrl = ""
    db_imgurl = ""
    db_imgdesc = ""
    db_imgname = ""
    
    for rootUrl in ROOT:
            r = requests.get("http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles="+newWikiTitle)
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
                                        cp = re.findall(r'([^:]+[\'\"\s\w\d.,-]+)\.(?:JPG|PNG|SVG|GIF)', imgurlst, flags=re.IGNORECASE)
                                        if cp:
                                            db_imgdesc = cp[0].replace("'","%27")
                                        else:
                                            db_imgdesc = '';
                                    
                                    #if there is already image, then just update
                                    sqlImgSelect = """SELECT * 
                                                        FROM geoinformation_cms.st_pictures 
                                                        WHERE attractionId='%s' and picname='%s'""" % (attractionId,db_imgname)
                                    cur.execute(sqlImgSelect)
                                    
                                    if cur.execute(sqlImgSelect) is not 0:
                                        #just update
                                        sqlImgUpdate = """UPDATE geoinformation_cms.st_pictures 
                                                            SET attractionId='%s', picurl='%s', picname='%s', picdescription='%s' 
                                                            WHERE attractionId='%s' and picname='%s' and downloadpath is NULL""" % \
                                                            (attractionId, db_imgDownLoadUrl, db_imgname, db_imgdesc, attractionId, db_imgname)
                                        cur.execute(sqlImgUpdate)
                                    else:
                                        #insert as new
                                        sqlInsertImage = """INSERT INTO geoinformation_cms.st_pictures 
                                                            (attractionId, picurl, picname, picdescription) VALUES 
                                                            ('%s', '%s', '%s', '%s')""" % \
                                                            (attractionId, db_imgDownLoadUrl, db_imgname, db_imgdesc)
                                        cur.execute(sqlInsertImage)


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
