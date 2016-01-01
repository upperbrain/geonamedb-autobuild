#/usr/bin/env python
# _*_ coding: utf-8 _*_

#This is a script that create geoinfomation_cms databased based on errors from country2wiki.py.
#We need to pass geonameId list in command line. This is not done yet.
#$ python geonameId2wiki.py

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

ERRORLIST = [u'2856817', u'2862127', u'2862132', u'2862150', u'2862185', u'2862193', u'2862200', u'2862232', u'2862233', u'2862240', u'2862367', u'2862375', u'2862882', u'2862907', u'2862908', u'2863017', u'2863019', u'2863027', u'2863035', u'2863046', u'2863047', u'2863066', u'2863073', u'2863074', u'2863075', u'2863076', u'2863077', u'2863078', u'2863079', u'2863080', u'2863087', u'2863088', u'2863091', u'2863116', u'2863136', u'2863138', u'2863147', u'2863158', u'2863159', u'2863161', u'2863191', u'2863194', u'2863210', u'2863213', u'2863230', u'2863234', u'2863240', u'2863263', u'2863267', u'2863276', u'2863337', u'2863348', u'2863354', u'2863370', u'2863381', u'2863382', u'2865647', u'2865648', u'2865651', u'2865652', u'2865667', u'2865668', u'2865809', u'2865813', u'2865814', u'2865817', u'2865818', u'2865825', u'2865827', u'2865828', u'2865829', u'2865830', u'2865831', u'2865832', u'2865839', u'2865841', u'2865844', u'2865856', u'2865872', u'2865873', u'2865893', u'2865902', u'2865903', u'2865927', u'2865928', u'2865929', u'2865930', u'2865931', u'2865932', u'2865933', u'2865934', u'2865936', u'2865937', u'2865938', u'2865947', u'2865950', u'2865951', u'2865952', u'2865953', u'2865954', u'2865955', u'2865956', u'2865957', u'2865958', u'2865959', u'2865960', u'2865961', u'2865962', u'2865964', u'2865965', u'2865966', u'2865967', u'2865968', u'2865969', u'2865970', u'2865971', u'2865972', u'2865973', u'2865974', u'2865975', u'2865976', u'2865977', u'2865978', u'2865979', u'2865980', u'2865981', u'2865982', u'2865983', u'2865984', u'2865986', u'2865987', u'2865988', u'2865989', u'2865990', u'2865991', u'2865992', u'2865993', u'2865994', u'2865995', u'2865996', u'2865997', u'2865998', u'2865999', u'2866000', u'2866002', u'2866022', u'2866049', u'2866050', u'2866051', u'2866070', u'2866071', u'2866072', u'2866074', u'2866075', u'2866076', u'2866077', u'2866078', u'2866079', u'2866080', u'2866081', u'2866082', u'2866083', u'2866084', u'2866093', u'2866095', u'2866101', u'2866102', u'2866103', u'2866104', u'2866106', u'2866108', u'2866109', u'2866110', u'2866111', u'2866112', u'2866113', u'2866114', u'2866115', u'2866118', u'2866119', u'2866120', u'2866121', u'2866122', u'2866126', u'2866135', u'2866146', u'2866147', u'2866148', u'2866171', u'2866175', u'2866182', u'2866186', u'2866190', u'2866192', u'2866196', u'2866198', u'2866202', u'2866223', u'2866225', u'2866226', u'2866227', u'2866228', u'2866229', u'2866230', u'2866234', u'2866235', u'2866236', u'2866237', u'2866238', u'2866239', u'2866242', u'2866243', u'2866244', u'2866245', u'2866246', u'2866247', u'2866297', u'2866298']

def parse(conn):
    #get list of geonameid, name, countryCode
    global cur
    cur = conn.cursor()
    
    for num in ERRORLIST:
        geonameid = num.encode('utf-8')
        
        sql = """SELECT name, country_code FROM all_countries WHERE geonameId='%s'""" % geonameid
        
        data = cur.execute(sql)
        results = cur.fetchall()
        
        for row in results:
           name = row[0].encode('utf-8')
           countryCode = row[1].encode('utf-8')
           print("====")
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
                    #print rw.json()['geonames']
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
                    db_descriptionwikivoyage = conn.escape_string(rdStr['extract'].encode('utf8'))
                else:
                    db_descriptionwikivoyage = ''
                    
        ri = requests.get('http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&rvsection=0&titles='+wikititle)
        #Get location homepage url if there is any
        if ri.status_code is 200:
            riStrObj = ri.json()['query']['pages']
            if(riStrObj.get('-1','NO_DATA') is 'NO_DATA'):
                for riEle in riStrObj:
                    if unicode(riEle) is '-1':
                        db_website = ""
                    else:
                        cu = re.findall(URL, unicode(riStrObj[riEle]['revisions'][0]['*']), flags=re.IGNORECASE)
                        if cu:
                            db_website = cu[0]
                        else:
                            db_website = ""
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
